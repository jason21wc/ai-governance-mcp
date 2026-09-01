"""Cross-consumer contract tests for worktree lifecycle journal v2.

The producer and three readers are intentionally independently installable. They
duplicate the small schema instead of importing a runtime helper; this test is
the shared fixture that prevents those copies from evolving separately.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts import repo_hygiene


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_KEYS = (
    "version",
    "host",
    "lifecycle_owner",
    "path",
    "branch",
    "base_sha",
    "default_ref",
    "owner_pid",
    "session_id",
    "task_key",
    "parallel_task",
    "state",
    "updated_at",
)
SHELL_CONSUMERS = (
    ROOT / "global-skills/start-worktree/prepare.sh",
    ROOT / "global-skills/start-worktree/cleanup.sh",
    ROOT / "global-skills/all-clear/allclear.sh",
)


def _shell_contract(path: Path) -> tuple[str, ...]:
    source = path.read_text(encoding="utf-8")
    match = re.search(r'^JOURNAL_V2_KEYS="([^"]+)"$', source, re.MULTILINE)
    assert match, f"{path} does not declare JOURNAL_V2_KEYS"
    return tuple(match.group(1).split())


def test_all_journal_consumers_declare_one_ordered_v2_schema():
    """Covers: FM-WORKTREE-JOURNAL-V2-STRICT"""
    for path in SHELL_CONSUMERS:
        assert _shell_contract(path) == EXPECTED_KEYS
    assert repo_hygiene.JOURNAL_V2_KEYS == EXPECTED_KEYS


def test_prepare_writer_emits_the_declared_schema_in_order():
    """Covers: FM-WORKTREE-JOURNAL-V2-STRICT"""
    source = SHELL_CONSUMERS[0].read_text(encoding="utf-8")
    body = source.split("write_state() {", 1)[1].split("\n}\n\nload_state()", 1)[0]
    emitted = tuple(re.findall(r"printf '([a-z_]+)=", body))
    assert emitted == EXPECTED_KEYS


def test_v2_lock_contract_is_named_v2_in_every_reader_and_writer():
    """Covers: FM-WORKTREE-JOURNAL-V2-STRICT"""
    for path in SHELL_CONSUMERS:
        source = path.read_text(encoding="utf-8")
        assert "ai-worktree-v2" in source
    source = (ROOT / "scripts/repo_hygiene.py").read_text(encoding="utf-8")
    assert "ai-worktree-v2" in source
