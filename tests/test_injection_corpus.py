"""#360 efficacy contract — measured, not asserted.

WHAT THIS REPLACES. BACKLOG #360 and SESSION-STATE both carried the claim that the
content-security gate catches "roughly 2 of 30 realistic injections." That number
lived in prose and nowhere else: no corpus, no script, no test. It could not be
reproduced, improved against, or falsified. Measured against a real corpus for the
first time on 2026-08-30, the baseline was **5/30 blocking, 7/30 including advisory
patterns**. Covering the two authority-assertion classes then raised that to
**14/30 blocking, 16/30 including advisory**, without increasing measured false
positives — explicit before/after evidence, not a replacement assertion.

THE SHAPE MATTERS MORE THAN THE TOTAL, and only a per-class breakdown shows it:

    imperative-override    4/4    <- the one class the lexicon was written for
    tool-coercion          2/3
    hidden-channel         1/5
    unanchored             0/3
    declarative-authority  6/6
    persona                0/3
    exfiltration           0/3
    self-authorising       3/3

The original detector was not uniformly weak: it was a **single-class detector** at
100% on imperative override and ~0% elsewhere. The authority rule closes the two
classes that share a second explicit structure: retrieved text asserting authority
it cannot possess. Persona, exfiltration, unanchored, and most hidden-channel cases
remain outside this heuristic; a clean result still does not establish trust.

WHY THIS IS NOT A PRECISION PROBLEM — the correction this file exists to pin.
#360 has recorded, as its top-ranked approach, "add a precision second stage" citing
`ref-ai-coding-two-stage-detection-precision-over-recall`. That precedent does not
apply here, and the measurement is what shows it. That entry addresses a **high-recall
trigger with false-positive domination**; its stated mechanism is a second stage that
"only runs on what the trigger fired" and "only ever DOWNGRADES." Bolting that onto
this detector would adjudicate the 7 it already catches, could only lower that number,
and would never see the 23 it misses. Measured FP here is 1/8 — there is no
false-positive problem to solve.

The precedent's own first instruction is "KEEP the high-recall trigger." This detector
has no high-recall trigger to keep. **Stage 1 is the bottleneck**, and a precision
stage 2 becomes relevant only after a recall-adequate stage 1 exists and starts
producing the false positives that stage 2 is for. Sequencing them the other way
builds the second half of a cascade whose first half is missing.

WHAT THIS FILE DOES. It pins per-case behaviour so any change to the ruleset shows up
as an explicit diff rather than a silently moved number, and it enforces a recall
floor so recall can only go up. It deliberately does **not** fail on the current low
recall: a test that cannot pass gets disabled, and then nobody reads it (the same
argument `all-clear` makes for "it must be possible to go green").
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_governance_mcp.content_patterns import (  # noqa: E402
    CRITICAL_PATTERNS,
    SUSPICIOUS_PATTERNS,
    matches_any,
)
from injection_corpus import BENIGN, CORPUS, MALICIOUS  # noqa: E402

# Measured 2026-08-30. Each id maps to the pattern names that fire on it.
# An empty tuple means the corpus entry is a known MISS. Changing the ruleset
# changes this table; that is the point — the diff is the review surface.
BASELINE: dict[str, tuple[str, ...]] = {
    "inj-01": ("prompt_injection",),
    "inj-02": ("prompt_injection",),
    "inj-03": ("prompt_injection",),
    "inj-04": ("prompt_injection",),
    "inj-05": (),
    "inj-06": (),
    "inj-07": (),
    "inj-08": ("authority_assertion",),
    "inj-09": ("authority_assertion",),
    "inj-10": ("authority_assertion",),
    "inj-11": ("authority_assertion",),
    "inj-12": ("authority_assertion",),
    "inj-13": ("authority_assertion",),
    "inj-14": (),
    "inj-15": (),
    "inj-16": (),
    "inj-17": (),
    "inj-18": (),
    "inj-19": ("hidden_instruction",),
    "inj-20": (),
    "inj-21": (),
    "inj-22": (),
    "inj-23": (),
    "inj-24": (),
    "inj-25": ("shell_command",),
    "inj-26": ("shell_command",),
    "inj-27": (),
    "inj-28": ("authority_assertion",),
    "inj-29": ("authority_assertion",),
    "inj-30": ("authority_assertion",),
    # Benign. ben-04 is a REAL false positive: `shell_command` fires on any
    # backticked command, so ordinary documentation showing a pytest invocation
    # trips it. Recorded rather than excused — it is 1 of only 8 benign strings.
    "ben-01": (),
    "ben-02": (),
    "ben-03": (),
    "ben-04": ("shell_command",),
    "ben-05": (),
    "ben-06": (),
    "ben-07": (),
    "ben-08": (),
}

# Floors, not targets. Recall may rise freely; it may not fall.
MIN_BLOCKING_RECALL = 14  # of 30, CRITICAL_PATTERNS only — these actually block
MIN_ANY_RECALL = 16  # of 30, including advisory patterns
MAX_FALSE_POSITIVES = 1  # of 8


def _hits(text: str) -> tuple[str, ...]:
    return tuple(
        sorted(n for n, p in SUSPICIOUS_PATTERNS.items() if matches_any(p, text))
    )


def _blocking(text: str) -> tuple[str, ...]:
    return tuple(n for n in _hits(text) if n in CRITICAL_PATTERNS)


def test_corpus_is_well_formed() -> None:
    """A corpus with duplicate ids or unlabelled cases measures nothing."""
    ids = [c.id for c in CORPUS]
    assert len(ids) == len(set(ids)), "duplicate corpus ids"
    assert len(MALICIOUS) == 30, f"expected 30 malicious cases, got {len(MALICIOUS)}"
    assert BENIGN, (
        "a recall number without a false-positive number is half a measurement"
    )
    assert set(ids) == set(BASELINE), "BASELINE and CORPUS have drifted apart"


@pytest.mark.parametrize("case", CORPUS, ids=lambda c: c.id)
def test_detection_matches_the_recorded_baseline(case) -> None:
    """Pin per-case behaviour so a ruleset change is an explicit diff.

    If this fails after you changed the patterns, that is expected — read the
    diff, confirm the direction is the one you intended, and update BASELINE.
    """
    assert _hits(case.text) == BASELINE[case.id], (
        f"{case.id} [{case.class_}] detection changed; update BASELINE deliberately"
    )


def test_blocking_recall_does_not_regress() -> None:
    caught = sum(1 for c in MALICIOUS if _blocking(c.text))
    assert caught >= MIN_BLOCKING_RECALL, (
        f"blocking recall fell to {caught}/30 (floor {MIN_BLOCKING_RECALL})"
    )


def test_any_recall_does_not_regress() -> None:
    caught = sum(1 for c in MALICIOUS if _hits(c.text))
    assert caught >= MIN_ANY_RECALL, (
        f"recall fell to {caught}/30 (floor {MIN_ANY_RECALL})"
    )


def test_false_positives_do_not_grow() -> None:
    """Recall gains bought with false positives are not gains.

    The failure mode this guards is the one `.pre-commit-config.yaml`'s V-004 note
    describes: a gate that fires on correct work trains its own bypass.
    """
    fp = sum(1 for c in BENIGN if _hits(c.text))
    assert fp <= MAX_FALSE_POSITIVES, (
        f"false positives rose to {fp}/{len(BENIGN)} (ceiling {MAX_FALSE_POSITIVES})"
    )


def test_covered_and_remaining_class_shape() -> None:
    """Pin which mechanism classes this deliberately narrow rule now covers."""
    per_class: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for c in MALICIOUS:
        per_class[c.class_][1] += 1
        if _hits(c.text):
            per_class[c.class_][0] += 1

    got, tot = per_class["imperative-override"]
    assert got == tot, "the class the lexicon was built for is no longer fully covered"
    for class_ in ("declarative-authority", "self-authorising"):
        got, tot = per_class[class_]
        assert got == tot, f"the authority assertion rule regressed on {class_}"

    zero_classes = [k for k, (g, _) in per_class.items() if g == 0]
    assert zero_classes, (
        "no class is at zero any more — this heuristic's stated limitations and "
        "the next detector decision need re-measuring"
    )
