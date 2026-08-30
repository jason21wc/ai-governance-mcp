"""Tests for the fresh-context keyword-trigger adjudicator (BACKLOG #73 Layer 1).

Everything here stubs `_codex_call` (the module-level seam, same pattern as
scripts/measure_plain_language.py) — no Codex, no network, CI-safe. The judge's
LIVE properties (injection resistance, uncertain→genuine skew, recall on the FN
corpus) are deliberately NOT unit-testable with a stub; they are pinned by the
Stage-1 live eval (scripts/eval_keyword_adjudicator.py). These tests pin the
deterministic scaffolding: parsing, fail-safe paths, prompt construction.
"""

import subprocess

import pytest

from ai_governance_mcp import keyword_adjudicator as ka

FIELDS = {
    "planned_action": "update the credential-path detection docs",
    "context": "docs-only change",
    "concerns": "",
}
KEYWORDS = {"planned_action": ["credential"]}


def _call(monkeypatch, response, fields=None, keywords=None, available=True):
    """Run adjudicate_keyword_trigger with a stubbed judge; capture the prompt."""
    seen = {}

    def stub(prompt, *, model=None, timeout=None, extra_env=None):
        seen["prompt"] = prompt
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(ka, "_codex_call", stub)
    monkeypatch.setattr(ka, "codex_available", lambda: available)
    result = ka.adjudicate_keyword_trigger(
        fields or FIELDS, keywords or KEYWORDS, model=None, timeout=45
    )
    return result, seen


# --------------------------------------------------------------------------- #
# Verdict parsing                                                              #
# --------------------------------------------------------------------------- #


def test_genuine_verdict_parsed(monkeypatch):
    result, _ = _call(
        monkeypatch, '{"verdict": "genuine", "reason": "stores a password"}'
    )
    assert result["verdict"] == "genuine"
    assert "password" in result["reason"]


def test_benign_verdict_parsed(monkeypatch):
    result, _ = _call(
        monkeypatch, '{"verdict": "benign", "reason": "mere topic mention"}'
    )
    assert result["verdict"] == "benign"


def test_chatter_around_json_still_parses(monkeypatch):
    result, _ = _call(
        monkeypatch,
        'Sure, here is my assessment:\n{"verdict": "benign", "reason": "ok"}\nDone.',
    )
    assert result["verdict"] == "benign"


# --------------------------------------------------------------------------- #
# Fail-safe paths → 'unavailable' (routing treats unavailable as ESCALATE)     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "response",
    [
        "not json at all",
        "",
        '{"verdict": "maybe", "reason": "unexpected label"}',
        '{"reason": "no verdict key"}',
        # decoy JSON + real JSON → first-{-to-last-} spans both → parse failure
        '{"verdict": "benign"} ignore that, real answer: {"verdict": "genuine"}',
    ],
)
def test_unparseable_or_unexpected_output_is_unavailable(monkeypatch, response):
    result, _ = _call(monkeypatch, response)
    assert result["verdict"] == "unavailable"


@pytest.mark.parametrize(
    "exc",
    [
        subprocess.TimeoutExpired(cmd="codex", timeout=45),
        OSError("boom"),
        FileNotFoundError("codex vanished"),
    ],
)
def test_judge_exceptions_are_unavailable(monkeypatch, exc):
    result, _ = _call(monkeypatch, exc)
    assert result["verdict"] == "unavailable"


def test_missing_cli_short_circuits_without_calling_codex(monkeypatch):
    called = []
    monkeypatch.setattr(
        ka, "_codex_call", lambda *a, **k: called.append(1) or '{"verdict":"benign"}'
    )
    monkeypatch.setattr(ka, "codex_available", lambda: False)
    result = ka.adjudicate_keyword_trigger(FIELDS, KEYWORDS, model=None, timeout=45)
    assert result["verdict"] == "unavailable"
    assert called == []


# --------------------------------------------------------------------------- #
# Prompt construction (security HIGH-2: per-field isolation preserved)         #
# --------------------------------------------------------------------------- #


def test_prompt_labels_fields_separately_with_provenance(monkeypatch):
    fields = {
        "planned_action": "rotate the deploy credentials",
        "context": "routine ops work",
        "concerns": "none noted",
    }
    keywords = {"planned_action": ["credential"]}
    _, seen = _call(monkeypatch, '{"verdict":"benign","reason":"x"}', fields, keywords)
    prompt = seen["prompt"]
    # labeled, separate sections — not one concatenated blob
    assert "PLANNED_ACTION" in prompt
    assert "CONTEXT" in prompt
    assert "CONCERNS" in prompt
    assert "rotate the deploy credentials" in prompt
    assert "routine ops work" in prompt
    # keyword provenance names the field it fired in
    assert "planned_action" in prompt and "credential" in prompt


def test_prompt_carries_load_bearing_rubric_properties(monkeypatch):
    """Presence-level pin of the four rubric properties (efficacy = live eval)."""
    _, seen = _call(monkeypatch, '{"verdict":"benign","reason":"x"}')
    prompt = seen["prompt"].lower()
    assert "data" in prompt and "not instructions" in prompt.replace(
        "never instructions", "not instructions"
    )
    # field-provenance non-neutralization
    assert "planned_action" in prompt and "neutraliz" in prompt
    # self-declared test/doc/hypothetical framing does not make it benign
    assert "hypothetical" in prompt or "test" in prompt
    # uncertain → genuine skew
    assert "uncertain" in prompt and "genuine" in prompt


def test_prompt_field_lengths_are_capped(monkeypatch):
    fields = {
        "planned_action": "credential " + "A" * 10_000 + "ZEND",
        "context": "B" * 10_000 + "ZEND",
        "concerns": "C" * 10_000 + "ZEND",
    }
    _, seen = _call(monkeypatch, '{"verdict":"benign","reason":"x"}', fields, KEYWORDS)
    prompt = seen["prompt"]
    assert "ZEND" not in prompt  # tails beyond the caps never reach the judge
    assert len(prompt) < 20_000


def test_reason_is_length_capped(monkeypatch):
    long_reason = "r" * 5_000
    result, _ = _call(
        monkeypatch, f'{{"verdict": "benign", "reason": "{long_reason}"}}'
    )
    assert len(result["reason"]) <= ka.REASON_CAP


def test_non_string_reason_is_coerced_safely(monkeypatch):
    result, _ = _call(monkeypatch, '{"verdict": "benign", "reason": ["a", "b"]}')
    assert result["verdict"] == "benign"
    assert isinstance(result["reason"], str)
