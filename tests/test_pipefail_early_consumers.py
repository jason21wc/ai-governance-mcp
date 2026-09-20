"""Class guard for early-closing consumers under Bash pipefail."""

from pathlib import Path

import pytest

from scripts.check_pipefail_early_consumers import scan_text


@pytest.mark.parametrize(
    ("consumer", "command"),
    [
        ("grep -q thing", "grep"),
        ("grep -Eq thing", "grep"),
        ("grep --quiet thing", "grep"),
        ("head -3", "head"),
        ("sed -n '1q'", "sed"),
        ("sed -e '2,$q'", "sed"),
        ("awk '{if (NR == 2) exit}'", "awk"),
    ],
)
def test_rejects_early_consumers_after_a_pipe(consumer: str, command: str) -> None:
    """Covers: FM-HOOK-PIPEFAIL-EARLY-CONSUMER"""
    findings = scan_text(
        Path("hook.sh"), f"#!/bin/bash\nset -euo pipefail\nprintf x | {consumer}\n"
    )
    assert [finding.command for finding in findings] == [command]


def test_handles_multiline_pipeline_and_assignment_prefix() -> None:
    text = """#!/bin/bash
set -o pipefail
produce \\
  | LC_ALL=C grep -q \\
      'match'
"""
    assert [finding.command for finding in scan_text(Path("hook.sh"), text)] == ["grep"]


def test_quoted_empty_string_does_not_truncate_the_scan() -> None:
    text = """#!/bin/bash
set -euo pipefail
empty=""
printf x | grep -q x
"""
    assert [finding.command for finding in scan_text(Path("hook.sh"), text)] == ["grep"]


@pytest.mark.parametrize(
    "source",
    [
        "set -e\nprintf x | grep -q x\n",
        "set -euo pipefail\ngrep -q x <<< x\n",
        "set -euo pipefail\nprintf x | sed -n '1,3p'\n",
        "set -euo pipefail\nprintf x | awk 'NR <= 3 {print}'\n",
        "set -euo pipefail\nprintf x | cut -c1-3\n",
        "set -euo pipefail\nprintf x | grep -- '-q'\n",
        "set -euo pipefail\nprintf x | awk -v label=exit '{print}'\n",
        "set -euo pipefail\nprintf '%s' 'literal | head -1'\n",
        "set -euo pipefail\n# printf x | head -1\n",
    ],
)
def test_allows_non_pipefail_or_whole_stream_shapes(source: str) -> None:
    assert scan_text(Path("hook.sh"), source) == []


def test_repository_hook_corpus_is_clean() -> None:
    """Covers: FM-HOOK-PIPEFAIL-EARLY-CONSUMER"""
    repo = Path(__file__).resolve().parent.parent
    findings = []
    for hook in sorted((repo / ".claude" / "hooks").rglob("*.sh")):
        findings.extend(scan_text(hook.relative_to(repo), hook.read_text()))
    assert findings == []


def test_guard_is_wired_to_authoring_surface() -> None:
    repo = Path(__file__).resolve().parent.parent
    precommit = (repo / ".pre-commit-config.yaml").read_text()
    assert "pipefail-early-consumers" in precommit
    assert "check_pipefail_early_consumers.py" in precommit
