"""Unit tests for scripts/check-volatile-pins.py — the volatile-pin WARN check.

Per BACKLOG #253. The script warns when a commit ADDS a hard-coded fact about
an external vendor's product (model generation, price, context size, model
count) — the class `rules-of-procedure.md` §10.1.4 governs.

**The acceptance bar here is not "does it pass."** For anything whose job is to
detect, the test that matters is *have I watched it fail on the real condition*
(session-266 through-line). So the true-positive cases below are drawn from the
actual text of the pins removed in session-267, and the false-positive cases are
drawn from the actual shape of the lines a de-pinning commit legitimately adds —
because a checker that fires on correct work is worse than no checker
(`ref-multi-agent-rtk-hook-compliance-patterns`: a gate that misfires trains its
own bypass).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "check-volatile-pins.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("check_volatile_pins", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_volatile_pins"] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _scan(path: str, added: str):
    """Scan a single added line as the diff parser would hand it over."""
    return mod.scan([(path, "+" + added)])


# --------------------------------------------------------------------------
# TRUE POSITIVES — verbatim from the pins session-267 actually removed.
# Each of these shipped in the corpus; the check must see every one.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line,expected_kind",
    [
        ('  "model": "claude-opus-5",', "Claude model ID"),
        (
            "| Frontier (Opus, GPT-4, Gemini Pro) | Safety guardrails only |",
            "OpenAI model generation",
        ),
        (
            "**Applies To:** Claude Sonnet 4.5+, GPT-4o+, and other advanced models.",
            "Claude model generation",
        ),
        (
            "- **Reasoning Models (o1/o3)**: Internal reasoning is not visible",
            "OpenAI reasoning model version",
        ),
        (
            "- Context window size for current AI tool (Claude: 200K, GPT-4: 128K)",
            "OpenAI model generation",
        ),
        (
            "AI assistants operate within token limits (typically 100K-200K tokens).",
            "context-window size",
        ),
        ("- Sub-agents get FRESH context window (200K tokens)", "context-window size"),
        ("| GPT-4o mini | $0.15 | $0.60 | openai |", "OpenAI model generation"),
        ("| Voyage-3-large | 69.2 | $0.12/M tokens | Enterprise |", "per-token price"),
        (
            "Vertex AI offers a curated set of 160+ models to fit needs",
            "vendor model count",
        ),
        ('`Appendix: "Opus 4.7 for D2+ in Claude Code."`', "Claude model generation"),
        (
            "Not recommended: Gemini 2.5 models have structured output issues.",
            "Gemini model generation",
        ),
        ("| Qwen 3.6 35B-A3B MoE (MLX 4-bit) | ~20 GB |", "open-model generation"),
    ],
)
def test_detects_real_pins(line: str, expected_kind: str) -> None:
    """Every one of these is a pin that really shipped. Red-before verified."""
    found = _scan("documents/rules-of-procedure.md", line)
    assert found, f"MISSED a real pin: {line!r}"
    assert found[0].kind == expected_kind


# --------------------------------------------------------------------------
# FALSE POSITIVES — the shapes a CORRECT de-pinning commit adds.
# These are the ones that decide whether the check is usable at all.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        # Version-history rows record what was true at a release.
        "| 3.46.0 | 2026-07-28 | MINOR: de-pinned Opus 4.6 and GPT-4o from §10.2.2. |",
        "| v2.11.1 | 2026-07-28 | PATCH: removed `Claude: 200K, GPT-4: 128K`. |",
        # Prose that frames the value as historical — the doctrine's own evidence.
        "This row previously read `200K-1M | 128K | 128K-200K | 1M-2M | 128K`.",
        "G said Opus 4.6 while Opus 5 shipped; all three have been de-pinned.",
        '`git log -S \'"model": "claude-opus-5"\'` returns 01822dc.',
        # Anchored form. The earlier fixture read "GPT-4o was retired; the
        # reference is historical and stays" and passed only because the bare
        # words "retired"/"historical" were exempt anywhere on a line — the
        # over-broad rule that blinded the check (see the blindness cases below).
        # Narrowing deliberately changed this: bare vocabulary no longer exempts.
        "This previously stated GPT-4o; the reference is historical and stays.",
        # Tier language — the form §10.1.4 now mandates.
        "| Complex reasoning | frontier / reasoning tier on any vendor |",
        "Sub-agents get a FRESH context window sized by the subagent's own model.",
        "the fast tier is the constrained one — confirm the input fits.",
        # Generation-stable aliases that Appendix I.1 explicitly ratifies.
        "| Large context | frontier tier on any vendor (Claude `opus`, Gemini Pro) |",
    ],
)
def test_does_not_fire_on_correct_work(line: str) -> None:
    """A checker that fires on de-pinning commits would be disabled within a day."""
    assert not _scan("documents/rules-of-procedure.md", line), (
        f"FALSE POSITIVE on legitimate text: {line!r}"
    )


def test_exempt_paths_are_skipped() -> None:
    """Archive and migration hold deliberately frozen history."""
    line = "Claude Opus 4.6 and GPT-4o are the current frontier models."
    assert _scan("documents/archive/old-methods.md", line) == []
    assert _scan("documents/migration/notes.md", line) == []
    assert _scan("documents/rules-of-procedure.md", line), (
        "control: should fire elsewhere"
    )


def test_advisory_by_default_strict_available() -> None:
    """V-004 arc: ships WARN, has a BLOCK mode ready for promotion."""
    src = SCRIPT_PATH.read_text()
    assert "return 2 if args.strict else 0" in src, "must be advisory unless --strict"
    assert '"--strict"' in src, "promotion path must exist"


def test_only_added_lines_are_considered(tmp_path, monkeypatch) -> None:
    """Diff-scoped is the design: existing rot is grandfathered, no allowlist.

    Exercises the SHIPPED parser. An earlier version of this test reimplemented
    the +/- loop inline and asserted against its own copy, so a regression in
    `added_lines` could not have turned it red (gate-2 review, session-267).
    """
    diff = (
        "+++ b/documents/rules-of-procedure.md\n"
        "-Old text naming Opus 4.6 as current\n"
        "+New text naming the frontier tier\n"
    )

    class _Result:
        stdout = diff

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _Result())
    pairs = mod.added_lines(None)
    assert pairs == [
        ("documents/rules-of-procedure.md", "+New text naming the frontier tier")
    ]
    assert mod.scan(pairs) == [], "a removal must never be reported as an addition"


# --------------------------------------------------------------------------
# EXEMPTION BLINDNESS — the hole gate-2 review found in the shipped guard.
# An exemption must describe the VALUE's status, not merely co-occur with it.
# Before the fix, all three of these were silently skipped because the line
# happened to contain "effective", "finding", or "no longer".
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        "The effective context window on Opus 4.6 is 200K tokens.",
        "A key finding: GPT-4o costs $2.50/1M tokens.",
        "This is no longer true: Gemini 2.5 has a 2M token window.",
        "Retired guidance aside, route heavy work to Opus 4.6 today.",
        "Historical note aside, GPT-4o is the current default.",
    ],
)
def test_exemption_words_do_not_blind_a_live_assertion(line: str) -> None:
    """A live pin must fire even when the line contains an exemption-ish word."""
    assert _scan("documents/rules-of-procedure.md", line), (
        f"BLINDED by an exemption word: {line!r}"
    )


@pytest.mark.parametrize(
    "line",
    [
        "This row previously read `200K-1M | 128K | 1M-2M`.",
        "G said Opus 4.6 while Opus 5 shipped; all three have been de-pinned.",
        "Research shows quality degrades around 32K tokens (Liu et al., 2023).",
        '`Appendix: "Opus 4.7 for D2+"` is an authoring exemplar that teaches the defect.',
    ],
)
def test_anchored_exemptions_still_hold(line: str) -> None:
    """Narrowing must not have removed the exemptions that earn their place."""
    assert not _scan("documents/rules-of-procedure.md", line), (
        f"FALSE POSITIVE after narrowing: {line!r}"
    )
