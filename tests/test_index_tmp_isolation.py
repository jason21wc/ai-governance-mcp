"""Two concurrent rebuilds must not splice their outputs into one index.

THE HAZARD
----------
The index is three files — ``global_index.json``, ``content_embeddings.npy``,
``domain_embeddings.npy``. Each is written atomically (tmp + fsync + rename), and
``extract_all`` writes the ``.npy`` pair first and the JSON last, because
``retrieval.py:_check_index_freshness`` keys "the index is ready" on the JSON's
mtime.

Per-file atomicity says nothing about a SECOND writer. Before this module's fix
the temp paths were fixed strings — ``global_index.tmp`` and
``content_embeddings.npy.tmp`` — shared by every process on the machine. Two
concurrent ``python -m ai_governance_mcp.extractor`` runs therefore wrote the
same temp path. Two things follow, and both are silent:

1. **Interleaved bytes.** Two writers open the same temp file; the survivor is
   whatever the interleaving left, which may be truncated or spliced.
2. **Interleaved renames.** Run A can publish run B's embeddings under A's JSON,
   because the rename of file 1 and the rename of file 2 are separate events with
   no transaction around them.

WHY THIS IS NOT A THEORETICAL CONCERN IN THIS REPO
--------------------------------------------------
An index whose JSON and ``.npy`` rows disagree is the row-misattribution defect:
every semantic query scored against the wrong document for six days on ``main``
(1041/1041 rows; principle Recall@10 measured at 0.462) while every shape gate
and the entire suite stayed green. Both files were individually well-formed —
which is precisely why nothing caught it. Shape checks cannot see a pairing
error.

WHAT THE FIX IS, AND WHAT IT IS NOT
-----------------------------------
``_tmp_suffix()`` makes the temp path unique per process and thread, adopting the
pattern already proven at
``context_engine/storage/filesystem.py:_atomic_write_json`` rather than inventing
one. It is **not a lock**: two rebuilds still race, and the loser's work is
discarded. That is the correct trade — a whole stale index is fixed by rebuilding,
a spliced index is undetectable.

TEST DISCIPLINE (session-266 rule)
----------------------------------
For anything whose job is to prevent a failure, passing is not evidence. Each
test below that asserts the fix works has a paired test that reinstates the old
fixed-suffix behaviour and *watches the failure happen*. If the fix is reverted,
the first group fails; if these tests are ever weakened into tautologies, the
second group stops failing and says so.
"""

import os
import threading
from pathlib import Path

import numpy as np
import pytest

from ai_governance_mcp import extractor as extractor_mod
from ai_governance_mcp.extractor import _tmp_suffix

OLD_FIXED_SUFFIX = ".tmp"  # the pre-fix behaviour, reproduced deliberately


@pytest.fixture
def extractor(test_settings):
    from unittest.mock import patch

    with patch("sentence_transformers.SentenceTransformer"):
        from ai_governance_mcp.extractor import DocumentExtractor

        test_settings.index_path.mkdir(parents=True, exist_ok=True)
        yield DocumentExtractor(test_settings)


def _tmp_paths_used(monkeypatch) -> list[Path]:
    """Record every temp path handed to ``np.save``."""
    seen: list[Path] = []
    real_save = np.save

    def spy(path, arr):
        seen.append(Path(str(path)))
        real_save(path, arr)

    monkeypatch.setattr(extractor_mod.np, "save", spy)
    return seen


class TestTheTempPathIsPrivateToItsWriter:
    def test_two_threads_do_not_share_a_temp_path(self, extractor, monkeypatch):
        seen = _tmp_paths_used(monkeypatch)
        barrier = threading.Barrier(2)

        def save(value: float):
            barrier.wait()  # force the two writers to overlap
            extractor._save_embeddings(
                np.full((4, 3), value, dtype=np.float32), "content_embeddings.npy"
            )

        threads = [threading.Thread(target=save, args=(v,)) for v in (1.0, 2.0)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(seen) == 2
        assert seen[0] != seen[1], (
            "two concurrent writers shared a temp path — they can splice"
        )

    def test_the_suffix_carries_the_writer_identity(self):
        suffix = _tmp_suffix()
        assert str(os.getpid()) in suffix
        assert str(threading.get_ident()) in suffix
        assert suffix.endswith(".tmp")

    def test_the_published_file_is_one_writers_data_not_a_mixture(
        self, extractor, monkeypatch
    ):
        """The point of the whole exercise: last-writer-wins, never a blend."""
        barrier = threading.Barrier(2)

        def save(value: float):
            barrier.wait()
            extractor._save_embeddings(
                np.full((8, 5), value, dtype=np.float32), "content_embeddings.npy"
            )

        threads = [threading.Thread(target=save, args=(v,)) for v in (1.0, 2.0)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        published = np.load(extractor.settings.index_path / "content_embeddings.npy")
        assert published.shape == (8, 5)
        # Every element came from the SAME writer — no interleaving.
        assert len(np.unique(published)) == 1, (
            f"published embeddings blended two writers: {np.unique(published)}"
        )
        assert published.flat[0] in (1.0, 2.0)

    def test_no_temp_files_survive_a_normal_save(self, extractor):
        extractor._save_embeddings(
            np.ones((3, 3), dtype=np.float32), "content_embeddings.npy"
        )
        leftovers = list(extractor.settings.index_path.glob("*.tmp*"))
        assert leftovers == [], f"orphaned temp files: {leftovers}"

    def test_the_json_temp_path_is_also_private(self, extractor, monkeypatch):
        """`_save_index` must use the same discipline as the embeddings path.

        Spies on ``json.dump``'s file handle rather than ``open`` — ``open`` is a
        builtin, not a module attribute, so patching it on the module is a no-op
        that would make this test silently vacuous.
        """
        written: list[Path] = []
        real_dump = extractor_mod.json.dump

        def spy(obj, fp, *a, **kw):
            written.append(Path(fp.name))
            return real_dump(obj, fp, *a, **kw)

        monkeypatch.setattr(extractor_mod.json, "dump", spy)
        monkeypatch.setattr(
            extractor, "_refuse_silent_narrowing", lambda *a, **kw: None
        )

        class _Index:
            def model_dump(self):
                return {"domains": {}}

        extractor._save_index(_Index())

        assert written, "no temp file was used — the atomic write was bypassed"
        tmp = written[0]
        assert tmp.name.endswith(".tmp"), f"not an atomic temp write: {tmp}"
        assert tmp.name != f"global_index{OLD_FIXED_SUFFIX}", (
            "global_index.json was written through the old fixed temp name"
        )
        assert str(os.getpid()) in tmp.name
        assert str(threading.get_ident()) in tmp.name
        # And the real file landed.
        assert (extractor.settings.index_path / "global_index.json").exists()


class TestTheOldBehaviourActuallyFailed:
    """Watch the failure the fix prevents. If these ever pass, the tests above
    have been weakened into tautologies and prove nothing."""

    def test_a_fixed_suffix_makes_two_writers_collide_on_one_temp_path(
        self, extractor, monkeypatch
    ):
        monkeypatch.setattr(extractor_mod, "_tmp_suffix", lambda: OLD_FIXED_SUFFIX)
        seen = _tmp_paths_used(monkeypatch)
        barrier = threading.Barrier(2)
        errors: list[BaseException] = []

        def save(value: float):
            barrier.wait()
            try:
                extractor._save_embeddings(
                    np.full((4, 3), value, dtype=np.float32), "content_embeddings.npy"
                )
            except BaseException as exc:  # the hazard itself — recorded, not raised
                errors.append(exc)

        threads = [threading.Thread(target=save, args=(v,)) for v in (1.0, 2.0)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(seen) == 2
        assert seen[0] == seen[1], (
            "expected the OLD fixed-suffix collision; if this fails the "
            "pre-fix hazard can no longer be reproduced and the tests above "
            "are no longer evidence of anything"
        )
        # THE SHARED PATH ABOVE IS THE DEFECT. What follows from it — whichever
        # writer renames second finding the path already gone — is a RACE
        # OUTCOME, and this assertion originally REQUIRED it:
        #
        #     assert any(isinstance(e, FileNotFoundError) for e in errors)
        #
        # That is asserting that a race was won on this run. CI proved it is not
        # reliable: identical code, `errors == []` on Python 3.11 and 3.12 while
        # 3.10 reproduced the ENOENT. Both threads simply completed. A negative
        # control that only sometimes reproduces is not a control — it is a
        # coin-flip that fails the build.
        #
        # So assert the deterministic half (both writers computed the SAME temp
        # path — already done above, and it is the hazard itself), and constrain
        # only the SHAPE of any corruption that did surface. When the race does
        # land it must land as ENOENT; a different exception would mean the
        # mechanism is not what this test claims.
        #
        # The splice consequence is proven deterministically by the next test,
        # which sequences the two writers explicitly instead of racing them —
        # that is where the "this actually corrupts data" evidence lives.
        assert all(isinstance(e, FileNotFoundError) for e in errors), (
            "the fixed-suffix collision must surface as ENOENT when it surfaces "
            f"at all; got {errors!r}"
        )

    def test_a_fixed_suffix_lets_one_run_publish_anothers_embeddings(
        self, extractor, monkeypatch
    ):
        """The splice, demonstrated deterministically.

        Run A writes its temp file and is paused before renaming. Run B writes
        the SAME temp path with different data and renames. A then renames — and
        publishes B's data under A's rebuild. With per-process temp names this
        interleaving is impossible, because A and B never touch the same path.
        """
        monkeypatch.setattr(extractor_mod, "_tmp_suffix", lambda: OLD_FIXED_SUFFIX)
        target = extractor.settings.index_path / "content_embeddings.npy"
        tmp = Path(str(target) + OLD_FIXED_SUFFIX + ".npy")

        # Run A writes its temp file (value 1.0) and stops short of the rename.
        np.save(Path(str(target) + OLD_FIXED_SUFFIX), np.full((4, 3), 1.0, np.float32))
        # Run B completes fully (value 2.0), overwriting the shared temp path.
        extractor._save_embeddings(np.full((4, 3), 2.0, np.float32), target.name)
        # Run A now renames what it believes is its own temp file.
        if tmp.exists():
            tmp.replace(target)

        published = np.load(target)
        assert published.flat[0] == 2.0, (
            "expected run A to publish run B's data — the splice this fix prevents"
        )
