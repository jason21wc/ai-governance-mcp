"""Drift guard for the single-source-of-truth loader model (v2.63.0).

`AGENTS.md` is the shared BODY; `CLAUDE.md`/`GEMINI.md` are thin overlays that
IMPORT it (`@AGENTS.md` / `@./AGENTS.md`) with a prose "Also read AGENTS.md"
fallback. This test pins that shape on the repo-owned template constants, modelled
on tests/test_frame_ssot.py (an existing SSOT-across-two-files drift guard).

IMPORTANT — scope of this guard: it asserts the import literal is PRESENT and the
body carries the shared content. It CANNOT assert the import literal RESOLVES in a
real CLI (CI cannot run Claude Code / Gemini). Import *resolution* is a manual
live-run gate — see plan `floofy-noodling-rose` Verification step 3 and the flagship
probe. The prose "Also read AGENTS.md" fallback is the belt-and-suspenders that keeps
a wrong/unresolved import from degrading below today's proven behaviour.
"""

import re

from ai_governance_mcp.server import _constants as c

# Exact per-tool import literals (verified against vendor docs — Claude Code memory
# docs use `@AGENTS.md`; Gemini memport uses the relative `@./AGENTS.md`). Do NOT
# normalise them to one spelling: a wrong literal silently loads an almost-empty file.
CLAUDE_IMPORT = re.compile(r"^@AGENTS\.md\s*$", re.M)
GEMINI_IMPORT = re.compile(r"^@\./AGENTS\.md\s*$", re.M)

PROSE_FALLBACK = "Also read AGENTS.md"

MEMORY_POINTERS = (
    "_ai-context/SESSION-STATE.md",
    "_ai-context/PROJECT-MEMORY.md",
    "_ai-context/LEARNING-LOG.md",
)

# Codex merges the project AGENTS.md with a global ~/.codex/AGENTS.md under a
# ~32 KiB budget (project_doc_max_bytes). Keep the scaffold body lean: a conservative
# sample of a global floor plus the rendered body must stay well under the cap.
CODEX_DOC_MAX_BYTES = 32 * 1024
CODEX_GLOBAL_FLOOR_SAMPLE = 6 * 1024  # generous estimate of a real ~/.codex/AGENTS.md
BUDGET_CEILING = 24 * 1024


def test_claude_overlay_imports_the_body():
    assert CLAUDE_IMPORT.search(c.SCAFFOLD_CLAUDE_MD), (
        "CLAUDE.md must import the body via a bare `@AGENTS.md` line"
    )


def test_gemini_overlay_imports_the_body():
    assert GEMINI_IMPORT.search(c.SCAFFOLD_GEMINI_MD), (
        "GEMINI.md must import the body via a bare `@./AGENTS.md` line"
    )


def test_overlays_carry_the_prose_fallback():
    # Belt-and-suspenders: a failed/unresolved import degrades to today's proven
    # prose directive, never to a memory-less session.
    for name, tmpl in (
        ("CLAUDE.md", c.SCAFFOLD_CLAUDE_MD),
        ("GEMINI.md", c.SCAFFOLD_GEMINI_MD),
    ):
        assert PROSE_FALLBACK in tmpl, f"{name} missing the prose import fallback"


def test_body_carries_pointers_and_session_start():
    for p in MEMORY_POINTERS:
        assert p in c.SCAFFOLD_AGENTS_MD, f"AGENTS.md body missing pointer {p}"
    assert "## Session Start" in c.SCAFFOLD_AGENTS_MD


def test_overlays_do_not_reinline_the_body():
    # The one-copy invariant: overlays import the body, never duplicate it. Analogue
    # of frame_ssot's byte-equality check.
    for name, tmpl in (
        ("CLAUDE.md", c.SCAFFOLD_CLAUDE_MD),
        ("GEMINI.md", c.SCAFFOLD_GEMINI_MD),
    ):
        for p in MEMORY_POINTERS:
            assert p not in tmpl, (
                f"{name} re-inlines {p} — overlays import the body, never copy it"
            )


def test_body_respects_the_codex_doc_budget():
    rendered = c.SCAFFOLD_AGENTS_MD.format(project_name="x", date="2026-01-01")
    total = len(rendered.encode("utf-8")) + CODEX_GLOBAL_FLOOR_SAMPLE
    assert total < BUDGET_CEILING, (
        f"AGENTS.md body ({len(rendered.encode('utf-8'))} B) + a sample global floor "
        f"({CODEX_GLOBAL_FLOOR_SAMPLE} B) = {total} B exceeds the {BUDGET_CEILING} B "
        f"ceiling (Codex project_doc_max_bytes ~{CODEX_DOC_MAX_BYTES} B). Keep the body lean."
    )


def test_safety_boundary_enforcement_stays_in_claude_overlay():
    # Governance ENFORCEMENT (hook block) belongs in the CLAUDE.md overlay, never in
    # the imported AGENTS.md body (title-10 Appendix A / K.3). Cheap structural pin.
    assert "ENFORCED BY HOOK" in c.SCAFFOLD_CLAUDE_MD
    for token in ("BLOCKS", "ENFORCED BY HOOK", "S-Series"):
        assert token not in c.SCAFFOLD_AGENTS_MD, (
            f"enforcement language {token!r} leaked into the imported AGENTS.md body"
        )
