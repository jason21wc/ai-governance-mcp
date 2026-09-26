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
from pathlib import Path

import pytest

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
    # Host enforcement belongs in the overlay, but a generated file is not proof
    # a hook was installed or executed. Preserve the safety rule without claiming
    # technical enforcement on an unverified adopter machine.
    assert "UNVERIFIED" in c.SCAFFOLD_CLAUDE_MD
    assert (
        "Safety stop rules still apply when no hook is running" in c.SCAFFOLD_CLAUDE_MD
    )
    assert "ENFORCED BY HOOK" not in c.SCAFFOLD_CLAUDE_MD
    assert "hook BLOCKS" not in c.SCAFFOLD_CLAUDE_MD
    for token in ("BLOCKS", "ENFORCED BY HOOK", "S-Series"):
        assert token not in c.SCAFFOLD_AGENTS_MD, (
            f"enforcement language {token!r} leaked into the imported AGENTS.md body"
        )


# --- the flagship dogfoods what it ships (BACKLOG #347) -----------------------
#
# Everything above pins the TEMPLATE constants. None of it looks at this
# repository's own root loaders, and that gap is exactly how #347 happened: the
# core kit has emitted CLAUDE.md AND GEMINI.md since v2.63.0 while this repo
# shipped only two of the three, so the framework prescribed a loader set it did
# not run itself. Nothing failed, because nothing was looking.
#
# Scope, stated so the next reader does not over-read it: this asserts the
# flagship HAS each loader and that each carries its own import literal plus the
# prose fallback. It cannot assert the import RESOLVES in a real CLI — same
# limit the module docstring records for the templates, and for the same reason.
# The flagship's overlays are deliberately FATTER than the scaffold templates
# (CLAUDE.md carries the hook contract), so this checks shape, not equality.

REPO_ROOT = Path(__file__).parent.parent

FLAGSHIP_LOADERS = (
    ("CLAUDE.md", CLAUDE_IMPORT, "@AGENTS.md"),
    ("GEMINI.md", GEMINI_IMPORT, "@./AGENTS.md"),
)


@pytest.mark.parametrize("name,pattern,literal", FLAGSHIP_LOADERS)
def test_flagship_ships_every_loader_the_core_kit_emits(name, pattern, literal):
    path = REPO_ROOT / name
    assert path.is_file(), (
        f"this repo scaffolds {name} into every core-tier project but does not "
        f"have one itself — the framework would be prescribing a loader set it "
        f"does not run (BACKLOG #347). Add the overlay, or if the exemption is "
        f"deliberate, record it in title-10 Appendix L.8.2 and delete this case."
    )
    text = path.read_text()
    assert pattern.search(text), (
        f"{name} must import the body via a bare `{literal}` line"
    )
    assert PROSE_FALLBACK in text, f"{name} missing the prose import fallback"


def test_flagship_body_is_the_one_copy():
    # The one-copy invariant, applied to the real files rather than the templates:
    # the shared body lives in AGENTS.md and the overlays import it. A memory
    # pointer appearing in an overlay means someone re-inlined the body.
    assert (REPO_ROOT / "AGENTS.md").is_file(), "AGENTS.md is the shared body"
    for name, _, _ in FLAGSHIP_LOADERS:
        path = REPO_ROOT / name
        if not path.is_file():
            continue  # the case above owns that failure; do not report it twice
        text = path.read_text()
        for p in MEMORY_POINTERS:
            assert p not in text, (
                f"{name} re-inlines {p} — overlays import the body, never copy it"
            )


def test_flagship_enforcement_language_stays_out_of_the_shared_body():
    # Safety-boundary binding (title-10 Appendix A / K.3) checked against the real
    # files: enforcement is a Claude Code property, so it belongs in an overlay.
    # GEMINI.md may — and here does — say enforcement is ABSENT under Gemini;
    # that is the boundary being respected, not violated, so only the body is
    # asserted against.
    body = (REPO_ROOT / "AGENTS.md").read_text()
    for token in ("ENFORCED BY HOOK", "BLOCKS"):
        assert token not in body, (
            f"enforcement language {token!r} leaked into the imported AGENTS.md body"
        )


def test_flagship_disposition_has_one_shared_copy():
    body = (REPO_ROOT / "AGENTS.md").read_text()
    for marker in (
        "## Disposition",
        "**Reasoning posture:**",
        "**Communication style:**",
    ):
        assert body.count(marker) == 1
        for name, _, _ in FLAGSHIP_LOADERS:
            assert marker not in (REPO_ROOT / name).read_text(), (
                f"{name} must inherit shared disposition through AGENTS.md"
            )


def test_flagship_claude_retains_its_planning_gate():
    overlay = (REPO_ROOT / "CLAUDE.md").read_text()
    assert (
        "`contrarian-reviewer` via Task subagent — required before `ExitPlanMode`"
        in overlay
    )
    assert "ENFORCED BY HOOK" in overlay
