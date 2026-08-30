"""`.claude/hooks/session-start-boot.sh` — what a resuming session actually receives.

WHY THIS FILE EXISTS. The hook had NO test of any kind, while being the single
thing that decides what context every session starts with. It selected the
injected region by matching the literal heading `## RESUMPTION` and terminating on
the next `## ` or a `---` line — three string matches, none of them checked, all
of them silent on failure: rename the heading and every session boots from a
four-line fallback with no error anywhere.

That went from latent to live on 2026-08-15, when the stacked per-session
RESUMPTION block was deleted (it was the region concurrent sessions collided on).
The old rule then stopped at the first heading of the snapshot shape, so sessions
received Current Position and no Next Actions — mechanically fine, and useless.
Measured, not reasoned about: 30,517 characters before the change, 660 under the
old rule against the new file, 2,477 after.

The contract pinned here is *what gets injected*, not *that the hook exits 0*.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "session-start-boot.sh"

SNAPSHOT = """# Session State

**Memory Type:** Working (transient)

---

## Current Position

- **Phase:** FIXTURE-PHASE
- **Blocker:** None.

## Immediate Context

FIXTURE-CONTEXT sentence.

## Next Actions

FIXTURE-NEXT-ACTION line.

## Quick Reference

| Metric | Value |
|---|---|
| Version | FIXTURE-SHOULD-NOT-APPEAR |

## Links

- FIXTURE-LINK-SHOULD-NOT-APPEAR
"""


def _project(tmp_path: Path, body: str | None = SNAPSHOT) -> Path:
    d = tmp_path / "proj"
    (d / "_ai-context").mkdir(parents=True)
    if body is not None:
        (d / "_ai-context" / "SESSION-STATE.md").write_text(body, encoding="utf-8")
    return d


def _run(project_dir: Path, source: str = "startup") -> str:
    """Return the injected additionalContext, or '' when the hook stays silent."""
    payload = json.dumps({"source": source, "cwd": str(project_dir)})
    env = os.environ.copy()
    for k in list(env):
        if k.startswith("BOOT_") or k == "CLAUDE_PROJECT_DIR":
            env.pop(k)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    r = subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    assert r.returncode == 0, f"a SessionStart hook must never block; {r.stderr}"
    out = r.stdout.strip()
    if not out:
        return ""
    # strict=False: the injected markdown legitimately carries control characters.
    payload_out = json.loads(out, strict=False)
    hso = payload_out["hookSpecificOutput"]
    assert hso["hookEventName"] == "SessionStart"
    return hso.get("additionalContext", "")


def test_injects_the_whole_orienting_span_not_just_the_first_section(tmp_path):
    """The regression that prompted this file: stopping at the next `## ` gave a
    resuming session its position and none of its next actions."""
    ctx = _run(_project(tmp_path))
    assert "FIXTURE-PHASE" in ctx
    assert "FIXTURE-CONTEXT" in ctx, "Immediate Context must survive the stop rule"
    assert "FIXTURE-NEXT-ACTION" in ctx, "Next Actions is the point of the injection"


def test_stops_before_the_reference_tables(tmp_path):
    """Quick Reference is generated tables and Links is boilerplate — injecting
    them costs every session tokens for content it can read on demand."""
    ctx = _run(_project(tmp_path))
    assert "FIXTURE-SHOULD-NOT-APPEAR" not in ctx
    assert "FIXTURE-LINK-SHOULD-NOT-APPEAR" not in ctx


def test_a_horizontal_rule_does_not_truncate(tmp_path):
    """`---` used to terminate extraction, because it bounded the old per-session
    stack. In the snapshot shape it is ordinary formatting, and a stray rule
    silently cutting the boot context is exactly the failure class this hook keeps
    producing."""
    body = SNAPSHOT.replace(
        "## Next Actions", "---\n\n## Next Actions"
    )  # rule INSIDE the injected span
    ctx = _run(_project(tmp_path, body))
    assert "FIXTURE-NEXT-ACTION" in ctx, "a horizontal rule must not end the span"


def test_grandfathered_resumption_heading_still_works(tmp_path):
    """Other projects (and older checkouts) still use `## RESUMPTION`."""
    body = SNAPSHOT.replace("## Current Position", "## RESUMPTION")
    ctx = _run(_project(tmp_path, body))
    assert "FIXTURE-PHASE" in ctx


def test_no_session_state_still_emits_the_protocol(tmp_path):
    """Absent memory file is not an error — but the protocol line must still land,
    or the session gets no instruction at all."""
    ctx = _run(_project(tmp_path, body=None))
    assert "SESSION-START PROTOCOL" in ctx
    assert "FIXTURE" not in ctx


def test_protocol_line_teaches_routing_not_a_line_count(tmp_path):
    """The `>300 lines` instruction was removed on 2026-08-15. It measured the
    wrong unit — the file sat AT 300 lines while carrying 61,258 characters,
    because it is written one paragraph per line — and it told sessions to prune
    rather than to route, which is how the content ended up misfiled."""
    ctx = _run(_project(tmp_path))
    assert "300 lines" not in ctx
    assert "route decisions to PROJECT-MEMORY" in ctx


@pytest.mark.parametrize(
    "template_name",
    ["SCAFFOLD_SESSION_STATE", "SCAFFOLD_SESSION_STATE_DOC"],
)
def test_works_against_the_templates_this_server_actually_ships(
    tmp_path, template_name
):
    """The fixture above is hand-written and therefore only ever proves the hook
    works on THIS repo's file. That is exactly how the v2 defect shipped:

    `SCAFFOLD_SESSION_STATE` orders `## Quick Reference` BEFORE `## Next Actions`,
    so a stop-at-a-reference-heading rule cut the injection off at 456 characters
    with no next actions — the very regression it was written to fix — and
    `SCAFFOLD_SESSION_STATE_DOC` leads with `## Current Focus`, matching no start
    token, injecting nothing at all. Both were invisible because the fixture
    copied this repo's section order rather than the shipped template.

    So this test reads the real constants. If a scaffold's headings or their order
    change, this fails rather than the projects created from it silently booting
    blind.
    """
    from ai_governance_mcp.server import _constants

    body = getattr(_constants, template_name)
    body = body.replace("{project_name}", "demo").replace("{date}", "2026-08-15")

    proj = tmp_path / "proj"
    (proj / "_ai-context").mkdir(parents=True)
    (proj / "_ai-context" / "SESSION-STATE.md").write_text(body, encoding="utf-8")
    ctx = _run(proj)

    assert ctx, f"{template_name} produced no resumption context at all"
    # The orienting sections must survive regardless of where they sit.
    assert ("Current Position" in ctx) or ("Current Focus" in ctx)
    assert ("Next Actions" in ctx) or ("Next Steps" in ctx), (
        "next actions must be injected no matter what order the template puts "
        "them in — this is the assertion the hand-written fixture could not make"
    )
    # And the reference tables must not be, wherever they sit.
    assert "| Metric | Value |" not in ctx


def test_injection_is_hard_capped_regardless_of_headings(tmp_path):
    """The cap must not be defeatable by editing markdown. A file whose wanted
    section simply never ends used to inject to EOF — 17,891 characters measured."""
    body = (
        "# Session State\n\n## Current Position\n- Phase: X\n\n## Immediate Context\n"
        + "\n".join(f"filler line {i}" for i in range(2000))
        + "\n"
    )
    proj = tmp_path / "proj"
    (proj / "_ai-context").mkdir(parents=True)
    (proj / "_ai-context" / "SESSION-STATE.md").write_text(body, encoding="utf-8")
    ctx = _run(proj)
    assert "truncated" in ctx, "an unbounded section must be capped, not injected"
    assert len(ctx) < 12000, f"cap did not hold: {len(ctx)} chars"


def test_unknown_sections_are_skipped_not_traversed(tmp_path):
    """Selection is by section NAME, so a section nobody anticipated is simply not
    injected — it cannot leak in by sitting between two wanted headings, which is
    how a CFR-contemplated session log would have been swept in wholesale."""
    body = SNAPSHOT.replace(
        "## Quick Reference",
        "## Session Log\n\nFIXTURE-UNANTICIPATED-SECTION\n\n## Quick Reference",
    )
    ctx = _run(_project(tmp_path, body))
    assert "FIXTURE-UNANTICIPATED-SECTION" not in ctx
    assert "FIXTURE-NEXT-ACTION" in ctx, "wanted sections after it must still appear"


@pytest.mark.parametrize("source", ["startup", "resume", "clear"])
def test_fires_on_boundary_sources(tmp_path, source):
    assert "FIXTURE-PHASE" in _run(_project(tmp_path), source=source)


def test_compact_is_silent(tmp_path):
    """compact is mid-session, not a session boundary."""
    assert _run(_project(tmp_path), source="compact") == ""
