#!/usr/bin/env python3
"""Warn on NEW volatile-value pins per `rules-of-procedure.md` §10.1.4.

A *volatile pin* is a hard-coded fact about an external vendor's product that
rots on that vendor's release cadence and nobody here can audit: a model version
name, a per-token price, a context-window size, a model count.

WHY THIS IS DIFF-SCOPED, NOT CORPUS-SCOPED
------------------------------------------
The corpus already carries ~30 such pins (BACKLOG #253) plus a large, *correct*
population of historical ones — the de-pinning doctrine cites rotted pins AS
EVIDENCE, and version-history rows record what was true at a release. A
corpus-wide scan would be false-positive-dominated on day one
(`ref-ai-coding-measure-first-detector-fp-domination`) and would need an
allowlist as large as the violation set.

Scanning only ADDED lines dissolves that: existing rot is grandfathered by
construction, no allowlist is needed, and the check answers the only question
that prevents regression — *are we adding a new one right now?*

WHY IT WARNS AND DOES NOT BLOCK
-------------------------------
Per the V-004 advisory→structural arc. The false positives that remain are
concentrated in exactly the commits doing the RIGHT thing: a de-pinning commit
adds a version-history row quoting the pin it just removed. A gate that fires
hardest on correct work trains its own bypass — a hazard this repo has already
recorded. Ship advisory, measure the fire rate on real commits, promote to BLOCK
only if the signal earns it.

ORIGIN
------
Session-267. Commit `01822dc`, subject "de-pin Appendix G.1 from model
versions", introduced two fresh `"model": "claude-opus-5"` pins four screens
below the rule it was writing. That is the case this check exists for: not a
careless author, but a careful one, mid-sweep, in the file being swept.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass

# Volatile-value patterns. Deliberately narrow: each must name a vendor product
# generation or a vendor-controlled quantity. Generic words ("model", "tokens")
# are not enough — the whole point is precision over recall at the WARN stage.
PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:Opus|Sonnet|Haiku|Fable)\s+\d+(?:\.\d+)*\b", "Claude model generation"),
    (r"\bclaude-(?:opus|sonnet|haiku|fable)-[\w.-]*\d", "Claude model ID"),
    (r"\bGPT-\d[\w.-]*\b", "OpenAI model generation"),
    (r"(?<![\w-])o[13](?:-\w+)?(?![\w])", "OpenAI reasoning model version"),
    (r"\bGemini\s+\d+(?:\.\d+)*\b", "Gemini model generation"),
    (r"\b(?:Llama|Mistral|Qwen)\s*\d+(?:\.\d+)*\b", "open-model generation"),
    (r"\$\d+(?:\.\d+)?\s*/\s*1?M\b", "per-token price"),
    (r"\b\d{2,4}K\s*(?:token|context)", "context-window size"),
    (r"\b\d+M\s*(?:token|context)", "context-window size"),
    (r"\b\d{2,4}\+\s*models\b", "vendor model count"),
)

# Contexts where naming a version is CORRECT and must not be flagged.
EXEMPT_LINE = (
    # Version-history / changelog rows: records of what was true at a release.
    re.compile(r"^\+\s*\|\s*v?\d+\.\d+\.\d+\s*\|"),
    # Prose that explicitly frames the value as PAST. Anchored phrases only —
    # an earlier version listed bare words ("no longer", "historical", "retired")
    # that match anywhere on a line, which blinded the check on live assertions
    # that merely contained one. Gate-2 review, session-267: three real pins
    # sailed through. An exemption must describe the VALUE's status, not merely
    # co-occur with it.
    re.compile(
        r"previously (?:read|stated|said)|used to (?:say|read)|this row previously"
        r"|de-pinned|was \*\*wrong\*\*|`git log",
        re.IGNORECASE,
    ),
    # Prose QUOTING a pin in order to name it as a defect. Measured on the first
    # live run as the largest false-positive class — it fires on the text that
    # documents this very rule. Narrowed for the same reason as above.
    re.compile(
        r"teaches the defect|authoring exemplar|worst instance"
        r"|the defect (?:this|it|that)|instance of the",
        re.IGNORECASE,
    ),
    # A CITED RESEARCH CONSTANT is not a vendor pin — it is the opposite claim.
    # "Quality degrades around 32K" is a measured finding that does not move when
    # a vendor ships, and flagging it would push authors to delete durable
    # evidence. Requires a CITATION SHAPE, not the bare word "research" or
    # "finding": those exempted live assertions that happened to use them.
    re.compile(
        r"\b(?:et al\.|\(20\d\d\)|20\d\d\)|Lost in the Middle)"
        r"|research (?:shows|demonstrates|from)|stud(?:y|ies) (?:show|found)",
        re.IGNORECASE,
    ),
    # This checker's own source and docs.
    re.compile(r"check-volatile-pins"),
)

EXEMPT_PATH = (
    # Generated artifacts: the index is built FROM the corpus, so a pin there is
    # a duplicate report of one already flagged (or already exempt) at source.
    "index/",
    "logs/",
    "documents/archive/",
    "documents/migration/",
    "scripts/check-volatile-pins.py",
    "tests/test_volatile_pins.py",
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: str
    kind: str
    match: str


def added_lines(ref: str | None) -> list[tuple[str, str]]:
    """Return (path, added_line) pairs from the diff. Staged if ref is None."""
    cmd = ["git", "diff", "-U0", "--no-color"]
    cmd += [ref] if ref else ["--cached"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    pairs: list[tuple[str, str]] = []
    path = ""
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            pairs.append((path, line))
    return pairs


def scan(pairs: list[tuple[str, str]]) -> list[Finding]:
    findings: list[Finding] = []
    for path, line in pairs:
        if any(path.startswith(p) or path == p for p in EXEMPT_PATH):
            continue
        if any(rx.search(line) for rx in EXEMPT_LINE):
            continue
        for rx, kind in PATTERNS:
            m = re.search(rx, line)
            if m:
                findings.append(Finding(path, line[1:].strip(), kind, m.group(0)))
                break
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", help="Diff against this ref instead of the index.")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on findings. Reserved for a future V-004 promotion; "
        "the default is advisory because the residual false positives land on "
        "correct de-pinning work.",
    )
    args = ap.parse_args()

    findings = scan(added_lines(args.ref))
    if not findings:
        return 0

    print(
        f"NOTE: {len(findings)} newly-added volatile value(s) — §10.1.4 says name "
        f"the tier and resolve the value from a live source, not from prose."
    )
    for f in findings:
        excerpt = f.line if len(f.line) <= 110 else f.line[:107] + "..."
        print(f"NOTE:   {f.path}: {f.kind} `{f.match}`")
        print(f"NOTE:     {excerpt}")
    print(
        "NOTE: If the value is genuinely historical, say so in the line "
        "(e.g. 'previously read', 'de-pinned') and this check will pass it."
    )
    return 2 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
