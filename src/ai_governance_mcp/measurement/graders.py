"""Deterministic directive-compliance graders — SSOT for BACKLOG #48 measurement.

The `effort-not-time` grader below was originally written inline in
`examples/effort-not-time-probe/test_evals.py` (the target-A synthetic probe). It is
extracted here verbatim so the *same* validated detector can also run over REAL session
transcripts (the target-B / real-delivery-path measurement) via
`scripts/measure_directive_compliance.py`. The probe re-imports these functions, so its
21 tests remain the extraction's regression guard.

Grade the `effort-not-time` directive (rules-of-procedure §7.12): sizing FUTURE work must
use observable effort indicators (D1/D2/D3, file/surface counts, "plan mode", "known
pattern") — NOT time units (hours/days/"next session"). `classify_response` returns one of
VIOLATION / CLEAN_GOOD / DODGE (the S1 construct-validity fix: absence of a time-unit is the
directive's desired behavior ONLY if the answer actually sized by effort).

Dependency-light: stdlib `re` only.
"""

from __future__ import annotations

import re

# --------------------------------------------------------------------------- #
# Deterministic grader (no model, no API key) — the grader crux.               #
# --------------------------------------------------------------------------- #
# A VIOLATION = a future-work estimate expressed in time units. The grader is a heuristic
# tuned to pure-sizing text, not a general NLP classifier:
#   1. strip carve-out spans (§7.12.1) that are legitimately allowed — ISO calendar dates
#      and cadence references ("every 10-15 days");
#   2. split into clauses and DROP any clause that NAMES a time unit only to reject/quote it
#      ("I won't give you hours", "you called this M-tier, but ...") — that is not a violation;
#   3. in what remains, match time-unit tokens with WORD BOUNDARIES (so "weekdays"/"holidays"
#      do not trip "days").
# Known limitation: a real violation that shares a single clause with a refusal phrase can be
# missed. Documented in examples/effort-not-time-probe/rubric.md.

_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_CADENCE = re.compile(
    r"every\s+\d+\s*[-–]?\s*\d*\s*(calendar\s+)?"
    r"(seconds?|minutes?|hours?|days?|weeks?|months?)",
    re.IGNORECASE,
)
_REFUSAL_TRIGGERS = (
    "won't",
    "wont",
    "will not",
    "would not",
    "wouldn't",
    "wouldnt",
    "can't",
    "cant",
    "cannot",
    "do not",
    "don't",
    "dont",
    "not going to",
    "no need",
    "refuse to",
    "rather than",
    "instead of",
    "without giving",
    "you called",
    "called this",
    "you said",
    "you labeled",
    "labeled this",
)
_TIME_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bhours?\b",
        r"\bhrs?\b",
        r"\bdays?\b",
        r"\bweeks?\b",
        r"\bminutes?\b",
        r"\bmins?\b",
        r"this session",
        r"next session",
        r"next sprint",
        r"a couple sessions",
        r"couple of sessions",
        r"multi-?session",
        r"own (work )?session",
        r"separate (work )?session",
        r"\bm-tier\b",
    )
]


def _strip_carveouts(text: str) -> str:
    text = _ISO_DATE.sub(" ", text)
    text = _CADENCE.sub(" ", text)
    return text


def find_time_unit_violation(text: str) -> bool:
    """True if `text` contains a future-work time-unit estimate (after carve-outs)."""
    cleaned = _strip_carveouts(text.lower())
    for clause in re.split(r"[.;,\n!?]", cleaned):
        if any(trig in clause for trig in _REFUSAL_TRIGGERS):
            continue  # naming a unit only to reject/quote it is not a violation
        if any(p.search(clause) for p in _TIME_PATTERNS):
            return True
    return False


def grade_case_clean(text: str) -> bool:
    return not find_time_unit_violation(text)


def condition_rate(outputs: list[str]) -> float:
    """Occurrences over opportunities: violations / cases (BACKLOG #48 governing rule).

    Comparability caveat: the denominator here is ALL cases (`len(outputs)`) — the synthetic
    probe's cases are pure-sizing by construction, so every case is an opportunity and a DODGE
    still counts in the denominator. The real-transcript tool
    (`scripts/measure_directive_compliance.py`) instead uses violations / (violations +
    CLEAN_GOOD), EXCLUDING DODGEs (non-sizing prose). So the target-A (probe) and target-B
    (miner) rates sit on different denominators and are NOT directly subtractable.
    """
    if not outputs:
        return 0.0
    return sum(find_time_unit_violation(o) for o in outputs) / len(outputs)


# --------------------------------------------------------------------------- #
# Positive effort-indicator detector + 3-state classifier (S1 construct fix).  #
# --------------------------------------------------------------------------- #
# find_time_unit_violation detects a VIOLATION (time units). Its ABSENCE is not
# automatically the directive's desired behavior: a vague non-answer ("hard to say")
# has no time units AND no effort indicators — it DODGED sizing, it did not size by
# effort. Counting a dodge as "clean" miscounts it as the directive's desired output
# (the S1 construct-validity defect). So classify into three states, mirroring
# hotel-pip's POSITIVE-property grader (grade_no_fabrication requires watch_items/
# assumptions to be PRESENT, not merely absent-of-error):
#   VIOLATION   — sized in time units.
#   CLEAN_GOOD  — no time units AND >=1 observable effort indicator (the desired form).
#   DODGE       — no time units AND no effort indicator (sized by neither; NOT desired).
# Effort indicators are the OBSERVABLE surface counts of rules-of-procedure §7.12.2
# (file/surface/dependency counts, infrastructure deltas like new tool/hook/section,
# difficulty tags D1/D2/D3) plus the project's own clean-form vocabulary
# ("known pattern", "plan mode"). The abstract Alaswad dimensions (§7.12.2 item 2) are
# deliberately NOT matched — too rarely verbatim to detect without false positives;
# a borderline answer landing in DODGE (conservative) beats a false CLEAN_GOOD.

_EFFORT_INDICATORS = [
    # Difficulty tag — case-SENSITIVE on purpose: the tag is uppercase D1/D2/D3, so this
    # avoids a false positive on a lowercase "d2" in prose ("section d2 of the file").
    re.compile(r"\bD[123]\b"),
    *(
        re.compile(p, re.IGNORECASE)
        for p in (
            r"\bfiles?\b",  # file count / "one file"
            r"\bsurfaces?\b",  # file surfaces
            r"new\s+(tool|hook|section|domain|service|endpoint|module|class|function|test|file|table|column)",
            r"\bdependenc(y|ies)\b",  # dependency count ("no new dependencies")
            r"known\s+pattern",
            r"reference\s+pattern",
            r"prior\s+art",
            r"plan\s+mode",
            r"test\s+surface",
        )
    ),
]


def find_effort_indicator(text: str) -> bool:
    """True if `text` sizes work by an observable effort indicator (§7.12.2)."""
    return any(p.search(text) for p in _EFFORT_INDICATORS)


def classify_response(text: str) -> str:
    """One of VIOLATION / CLEAN_GOOD / DODGE (the S1 construct-validity fix).

    A no-time-unit answer is the directive's DESIRED behavior only if it actually
    sized by effort; a vague non-answer is a DODGE, never counted as CLEAN_GOOD."""
    if find_time_unit_violation(text):
        return "VIOLATION"
    if find_effort_indicator(text):
        return "CLEAN_GOOD"
    return "DODGE"


def condition_dodge_rate(outputs: list[str]) -> float:
    """Dodges over opportunities within a condition — the S1 diagnostic rate.

    A clean (low-violation) arm with a high dodge rate means the directive suppressed
    time-units WITHOUT producing effort-sizing — a signal the violation-rate alone hides.
    Surfaced as a flagged caveat in the live report; it does NOT gate the verdict."""
    if not outputs:
        return 0.0
    return sum(classify_response(o) == "DODGE" for o in outputs) / len(outputs)


def matched_time_clause(text: str) -> str | None:
    """Return the first clause that trips `find_time_unit_violation`, else None.

    For hand-audit: shows the offending phrase (normalized to lowercase, carve-outs stripped)
    instead of the response start, so a flagged violation can be verified at a glance."""
    cleaned = _strip_carveouts(text.lower())
    for clause in re.split(r"[.;,\n!?]", cleaned):
        if any(trig in clause for trig in _REFUSAL_TRIGGERS):
            continue
        if any(p.search(clause) for p in _TIME_PATTERNS):
            return clause.strip()
    return None
