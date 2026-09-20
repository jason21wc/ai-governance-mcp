"""The retired copy model must not come back in prose (BACKLOG #237).

`7de7225` replaced the user-level hook COPIES with symlinks into this checkout.
The mechanism changed; eight descriptions of the mechanism did not. The result
was `journal-reminder.sh` telling its reader to "edit HERE, then copy to
~/.claude/hooks/" fourteen lines above a comment saying the installs are
symlinks — a file contradicting itself.

WHY THIS IS A TEST AND NOT JUST AN EDIT. Stale prose that merely *describes* is
a nuisance. Stale prose that *instructs* is a live regression path: the
compliance-review procedure is executed, and following its `diff -q` step would
have recreated the second-copy architecture the migration removed. Code changes
had guards here; the prose describing them had none, which is the whole reason a
retired model survived its own removal.

SCOPE, deliberately narrow. "byte-identical" is a perfectly good phrase in this
repo for things that ARE byte-identical — AGENTS.md loader overlays, subagent
fork semantics, hook deny-shape comparisons. This checks only the hook-install
subject, two ways:

  * inside `.claude/hooks/`, where every file describes only itself; and
  * in docs, only on lines that name a global hook AND use copy vocabulary.

Version-history rows are exempt by design. They record what was true at a past
version, and rewriting history to match the present is a different and worse
failure than the one this guards (the same call session-264 made when it kept a
superseded PROJECT-MEMORY row for provenance).
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOKS = REPO / ".claude" / "hooks"

# Vocabulary of the retired model. Each of these appeared in the stale headers.
RETIRED = re.compile(
    r"byte-mirrored|byte-identical|MIRRORED COPY|copy is unavoidable"
    r"|then mirror|then copy to|keep them byte|must stay byte",
    re.IGNORECASE,
)

GLOBAL_HOOKS = (
    "journal-reminder.sh",
    "session-start-dream.sh",
    "session-start-genesis.sh",
)

# Directories swept for docs that describe how the global hooks are installed.
#
# THE FIRST VERSION OF THIS LISTED THREE FILES BY HAND — the same three the
# session had already corrected. A guard scoped to what you have already fixed
# confirms your own work and nothing else, which is precisely the
# hand-maintained-list defect BACKLOG #235 was about, reproduced here one level
# up while the file's own docstring claimed to be structural. It could not see
# `_ai-context/OPERATIONS.md`, which was holding three stale claims including an
# *instruction* to mirror manually — the live regression path this guard exists
# to prevent. Found by a fresh-context coherence audit, not by re-reading.
#
# Sweeping directories instead means a doc written tomorrow is covered the day
# it lands.
DOC_ROOTS = [
    REPO,  # top-level: EXECUTION-FRAMEWORK.md, README.md, AGENTS.md, CLAUDE.md
    REPO / "documents",
    REPO / "_ai-context",
    REPO / ".claude" / "skills",
    REPO / "tests",
]

# The reference library records what was true for a past project at capture time
# and is explicitly append-only history; global-skills ship to other machines and
# do not describe this repo's install.
EXCLUDED_DIRS = {"reference-library", "global-skills", "node_modules", ".git"}

# Files exempt by nature, each for a stated reason rather than convenience:
#
#   BACKLOG.md / PROJECT-MEMORY.md — append-only records carrying dated STATUS and
#     "Evolved <date>" clauses. Rewriting them to match the present is the failure
#     this guard's history-row exemption already avoids, one file up.
#   this file — it QUOTES the retired instruction in order to explain it. A matcher
#     that cannot tell a quotation from an instruction is the n=3 failure named in
#     the deleted-check comment below; excluding the one file that quotes on purpose
#     is cheaper and more honest than trying to parse intent.
#
# RESIDUAL, stated rather than hidden: a genuinely NEW instruction added to one of
# these files would not be caught here. They are records, not procedures, so the
# exposure is low — but it is nonzero, and this is where it lives.
EXCLUDED_FILES = {
    REPO / "_ai-context" / "BACKLOG.md",
    REPO / "_ai-context" / "PROJECT-MEMORY.md",
    Path(__file__).resolve(),
}


def doc_surfaces():
    """Every markdown/py/sh doc surface that could describe the hook install."""
    seen, out = set(), []
    for root in DOC_ROOTS:
        if not root.exists():
            continue
        pattern = "*.md" if root == REPO else "**/*"
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or path.suffix not in {".md", ".py", ".sh"}:
                continue
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            if path.resolve() in EXCLUDED_FILES or path in seen:
                continue
            seen.add(path)
            out.append(path)
    return out


def is_history_row(line):
    """A markdown table row — version history or a past review log.

    Exempt: these record what was true at a past version or on a past review
    date. Rewriting them to match the present is a different and worse failure
    than the one this guards. Instructions in these docs are prose, not table
    rows, so the exemption does not create a hole in what is being checked.
    """
    return line.strip().startswith("|")


def hook_files():
    return sorted(HOOKS.rglob("*.sh"))


@pytest.mark.parametrize("path", hook_files(), ids=lambda p: p.name)
def test_hook_files_do_not_describe_a_copy_model(path):
    """Inside .claude/hooks/, every file describes only its own install."""
    offenders = [
        f"{path.relative_to(REPO)}:{i}: {line.strip()}"
        for i, line in enumerate(path.read_text().splitlines(), 1)
        if RETIRED.search(line)
    ]
    assert offenders == [], (
        "retired copy-model vocabulary in a hook file — the installs are "
        "symlinks (BACKLOG #226/#237):\n" + "\n".join(offenders)
    )


def test_docs_do_not_instruct_mirroring_a_global_hook():
    """Only lines that name a global hook AND use copy vocabulary.

    Swept across whole directories rather than a hand-listed set of files — see
    DOC_ROOTS for why. One test over the sweep, not one per file, so a new
    document cannot be missed by forgetting to add a parametrize entry.
    """
    surfaces = doc_surfaces()
    assert surfaces, "doc sweep found nothing — discovery is broken"
    offenders = []
    for doc in surfaces:
        try:
            text = doc.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        # Same-line co-occurrence for GENERAL docs. A file-level subject test was
        # tried and reverted: it flagged legitimate "byte-identical" prose about
        # AGENTS.md loader overlays in files that merely mention a hook elsewhere.
        # Widening the subject to the whole file cannot tell WHICH thing the
        # sentence is about — the same can't-tell-subject failure this file's
        # deleted-check comment records.
        #
        # Files whose subject IS a global hook are handled by the strict rule
        # below instead, which is where the same-line predicate's real miss lived.
        for i, line in enumerate(text.splitlines(), 1):
            if (
                any(h in line for h in GLOBAL_HOOKS)
                and RETIRED.search(line)
                and not is_history_row(line)
            ):
                offenders.append(f"{doc.relative_to(REPO)}:{i}: {line.strip()[:160]}")
    assert offenders == [], (
        "doc describes the retired hook-copy model; following it recreates the "
        "second copy 7de7225 removed:\n" + "\n".join(offenders)
    )


# DELIBERATELY NOT TESTED: "the procedure must not tell the reviewer to `diff`
# the installs."
#
# That check was written, and it failed on two lines that are both correct: the
# sentence saying "Do NOT `diff` the installs", and a historical review-log row
# recording a diff performed back when there was something to diff. A
# token-anchored matcher cannot tell an instruction from a prohibition or from a
# record of the past — which is the identical failure `lib/shell-scan.sh`
# documents at n=3 in this repo, and the reason the post-push hook fired on prose.
#
# Writing a cleverer regex would be walking into it a fourth time, so the
# vocabulary checks above plus the guard-is-named check below are the coverage.
# The `diff` instruction itself is removed; what is not claimed is that a future
# one would be caught automatically. Stated rather than papered over.


def test_the_guard_script_is_the_named_verification():
    """Replacing a bad instruction with none would leave the check unowned.

    Names `check-installed-hooks.sh` only as a STRING; it never runs it. The
    script is private (absent from `documents/.public-allowlist`) and so is the
    procedure that names it, so this skips in the public tree rather than being
    staged for removal — the file's other tests cover published surfaces and
    should keep running there.
    """
    proc = REPO / ".claude" / "skills" / "compliance-review" / "procedure.md"
    if not proc.exists():
        pytest.skip("compliance procedure is private; absent in the public tree")
    assert "check-installed-hooks.sh" in proc.read_text(), (
        "the compliance procedure must name the structural install guard — "
        "removing the diff step without naming its replacement drops the check"
    )


def dedicated_hook_test_files():
    """Test files whose SUBJECT is a single global hook, by filename.

    `.claude/hooks/*.sh` already gets a strict whole-file rule because each file
    describes only itself. A test file named after one hook is in exactly the
    same position, and it was not covered: the docs predicate needs the hook name
    and the retired vocabulary on the SAME line, so three stale claims in
    `tests/test_journal_reminder_hook.py` survived — including one that is the
    stated RATIONALE for a test ("~/.claude, ~/.codex ship a COPY of this hook"),
    describing a premise that no longer exists.
    """
    out = []
    for path in sorted((REPO / "tests").glob("test_*.py")):
        stem = path.stem.replace("test_", "").replace("_hook", "").replace("_", "-")
        if any(h.replace(".sh", "") in stem for h in GLOBAL_HOOKS):
            out.append(path)
    return out


@pytest.mark.parametrize("path", dedicated_hook_test_files(), ids=lambda p: p.name)
def test_dedicated_hook_tests_do_not_describe_a_copy_model(path):
    """Strict: a file about one hook must not carry the retired vocabulary."""
    offenders = [
        f"{path.relative_to(REPO)}:{i}: {line.strip()[:160]}"
        for i, line in enumerate(path.read_text().splitlines(), 1)
        if RETIRED.search(line) and not is_history_row(line)
    ]
    assert offenders == [], (
        "a test file named after a global hook still describes the retired copy "
        "model; its premises are what future readers trust:\n" + "\n".join(offenders)
    )


def test_the_dedicated_file_sweep_finds_something():
    """Discovery guard — an empty parametrize would pass vacuously."""
    assert dedicated_hook_test_files(), (
        "no dedicated hook test files discovered; the filename mapping broke"
    )
