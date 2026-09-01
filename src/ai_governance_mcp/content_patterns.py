"""Content-security patterns and normalization. STDLIB ONLY, deliberately.

WHY THIS IS ITS OWN MODULE
--------------------------
These definitions lived in ``extractor.py``, which imports ``numpy`` and ``yaml`` at
module level. That was invisible until ``scripts/check_content_security.py`` started
importing them: the gate acquired a hard dependency on numpy, and on an interpreter
without it the import failed, the gate returned exit 3 (could-not-run), and
``check.sh`` reports could-not-run as SKIP while the pre-push gate blocks only on
``fail > 0``. Measured on this machine: 2 of the 3 ``python3`` on PATH lack numpy,
and ``check.sh`` invokes bare ``python3``.

So a missing scientific-computing dependency silently disabled a prompt-injection
scan — which is precisely the "scanned nothing and reported clean" shape the whole
BACKLOG #324 arc exists to close, arriving through a new door.

A detection ruleset has no reason to sit behind numpy. It sits here instead, with no
imports beyond ``re`` and ``unicodedata``, so every consumer — the extractor, the
scaffold handler, and the check.sh gate — can load it anywhere Python runs.

``extractor.py`` re-exports these names, so existing imports keep working and there
is still exactly one definition.

SCOPE, STATED PLAINLY: this is a heuristic and NOT a trust boundary. It does not
defeat homoglyphs (see ``normalize_text_for_security``), and
``tests/test_injection_corpus.py`` measures its still-partial efficacy. Treat a clean
result as "nothing obvious", never as "safe".
"""

from __future__ import annotations

import re
import unicodedata

# Invisible Unicode characters that should be stripped for security scanning.
# These can be used to hide malicious content from visual inspection.
_INVISIBLE_CATEGORIES = frozenset(
    {
        "Cf",  # Format characters (zero-width joiners, etc.)
        "Cc",  # Control characters (except newlines/tabs)
    }
)

# Specific invisible codepoints to strip
_INVISIBLE_CODEPOINTS = frozenset(
    {
        0x200B,  # Zero-width space
        0x200C,  # Zero-width non-joiner
        0x200D,  # Zero-width joiner
        0x200E,  # Left-to-right mark
        0x200F,  # Right-to-left mark
        0x2060,  # Word joiner
        0x2061,  # Function application
        0x2062,  # Invisible times
        0x2063,  # Invisible separator
        0x2064,  # Invisible plus
        0xFEFF,  # Byte order mark / zero-width no-break space
    }
)


def _is_invisible_char(char: str) -> bool:
    """Check if a character is invisible and should be stripped for security."""
    cp = ord(char)
    # Keep newlines and tabs for pattern matching context
    if char in "\n\r\t":
        return False
    if cp in _INVISIBLE_CODEPOINTS:
        return True
    return unicodedata.category(char) in _INVISIBLE_CATEGORIES


def normalize_text_for_security(text: str) -> str:
    """Normalize text for security pattern matching.

    Applies NFKC normalization (compatibility decomposition + canonical composition)
    and strips invisible characters.

    ⚠️ IT DOES **NOT** DEFEAT HOMOGLYPHS, and this docstring once claimed it did. NFKC
    maps compatibility equivalents (ligatures, fullwidth forms, superscripts); Cyrillic
    'о' (U+043E) and Latin 'o' (U+006F) are DIFFERENT characters, not compatibility
    variants, so NFKC leaves them alone. Verified by probe: ``Ignоre previous
    instructions`` with one Cyrillic 'о' produces **no finding**, while the pure-ASCII
    line matches. The test named ``test_normalize_text_handles_homoglyphs``
    acknowledged the limitation in a comment and then asserted only idempotence on
    ASCII — a name that validated more than its assertions. Found by a cross-vendor
    review after three same-model reviews missed it.

    What this DOES buy: invisible-character stripping (zero-width joiners and friends
    used to break up a pattern) and compatibility folding. That is real and worth
    keeping.

    ⚠️ NORMALIZING IS NOT MONOTONE FOR MATCHING, so a caller must scan the raw text as
    WELL as the normalized text, never instead of it. Two measured ways this removes a
    match that the raw string had: U+001F is stripped as ``Cc`` but ``\\s`` matches it,
    so ``ignore\\x1fprevious`` satisfies ``ignore\\s+previous`` raw and not normalized;
    and U+FE65/U+FF1E normalize to a literal ``>``, which terminates a ``[^>]*``
    negated class and ends a match that raw text does not end. ``check_content_security``
    scans both views for this reason.

    Closing the homoglyph gap needs actual confusable mapping — Unicode TR39 skeletons
    or the ``confusable_homoglyphs`` package — which is not installed. Until then treat
    this scanner as a heuristic, NOT the corpus trust boundary (BACKLOG #332 is about
    exactly that mis-framing).
    """
    normalized = unicodedata.normalize("NFKC", text)
    return "".join(c for c in normalized if not _is_invisible_char(c))


def security_views(text: str) -> tuple[str, ...]:
    """The strings a scanner must match against: RAW and normalized, never one.

    THE INVARIANT LIVES HERE, IN CODE, because it spent one commit living in the
    docstring above and two of the three callers did not obey it. `normalize` is
    not monotone with respect to matching — it can delete a character a pattern
    needs and manufacture one that ends a match — so scanning only the normalized
    text silently loses detections the raw text had:

      `ignore\\x1fprevious instructions` — U+001F is category Cc so it is stripped,
          yielding `ignoreprevious`; but `\\s` MATCHES it, so the RAW string
          satisfies `ignore\\s+previous` and the normalized one does not.
      `<!-- ﹥ instruction: … -->` (U+FE65), `<!-- ＞ … -->` (U+FF1E) — both NFKC to
          a literal `>`, terminating the `[^>]*` class in `hidden_instruction`.

    Returns one element when normalization is the identity, which is every
    printable-ASCII line, so the common path costs one extra comparison.
    """
    probe = normalize_text_for_security(text)
    return (text,) if probe == text else (text, probe)


def matches_any(pattern, text: str) -> bool:
    """True if `pattern` matches the raw OR the normalized view of `text`."""
    return any(pattern.search(v) for v in security_views(text))


_MARKDOWN_PREFIX_RE = re.compile(
    r"^[ \t]*(?:(?:[-*+]|>)\s+)*(?:#{1,6}\s+)?(?:\*{1,2}|_{1,2})?"
)
_FENCE_PREFIX_RE = re.compile(r"^[ \t]*(?:```|~~~)")
_CONTINUATION_PATTERNS = frozenset({"authority_assertion"})


def matches_security_pattern(
    name: str, pattern, line: str, continuation: str = ""
) -> bool:
    """Match one scanner line, including bounded production-shaped variants.

    Production consumers scan line-by-line to preserve source locations and fence
    state. Authority claims, however, are commonly prefixed by Markdown or wrapped
    onto the immediately following line. The corpus originally scored whole plain
    strings, so it reported those cases covered while all three consumers missed
    them. This shared seam keeps their behavior aligned:

    - every pattern still sees raw + normalized forms of the current line;
    - authority assertions also see common Markdown prefixes removed;
    - authority assertions may span one nonblank, non-fence continuation line;
    - a cross-line match must START on the current line, avoiding duplicate or
      off-by-one findings for an attack that begins on the next line.
    """
    first_views = list(security_views(line))
    if name == "authority_assertion":
        first_views.extend(
            stripped
            for view in tuple(first_views)
            if (stripped := _MARKDOWN_PREFIX_RE.sub("", view)) != view
        )
    if any(pattern.search(view) for view in first_views):
        return True

    if (
        name not in _CONTINUATION_PATTERNS
        or not continuation.strip()
        or _FENCE_PREFIX_RE.match(continuation)
    ):
        return False

    second_views = list(security_views(continuation))
    second_views.extend(
        stripped
        for view in tuple(second_views)
        if (stripped := _MARKDOWN_PREFIX_RE.sub("", view)) != view
    )
    # If the next line is independently a complete finding, let the next scanner
    # iteration report it at its own line. Otherwise a delimiter at the end of the
    # current line can begin the regex match and produce a duplicate finding whose
    # displayed content is harmless context.
    if any(pattern.search(view) for view in second_views):
        return False
    for first in first_views:
        for second in second_views:
            match = pattern.search(first + "\n" + second)
            if match and match.start() <= len(first):
                return True
    return False


# Patterns classified by severity.
# CRITICAL: hard-fail extraction — these are clear attack indicators.
# ADVISORY: warn only — may have legitimate uses in documentation.
#
# Lives here beside the patterns it classifies, so a consumer gets the ruleset and
# the severity policy from ONE place. It was briefly re-derived by hand in
# `check_content_security.py`, which would have recreated in a day the divergence
# BACKLOG #360 exists to remove.
CRITICAL_PATTERNS = {
    "prompt_injection",
    "hidden_instruction",
    "authority_assertion",
}

# Suspicious patterns that may indicate prompt injection or malicious content
SUSPICIOUS_PATTERNS = {
    "shell_command": re.compile(
        r"(?<!`)`[^`]+`(?!`)|"  # Backtick commands (not in code blocks)
        r"\$\([^)]+\)|"  # $() subshells
        r"(?:^|\s)(?:curl|wget|bash|sh|eval|exec)\s+[^\s]",
        re.MULTILINE,
    ),
    "prompt_injection": re.compile(
        # These patterns must appear at start of sentence or after punctuation
        # to avoid matching documentation that discusses these concepts.
        # That positional anchoring is deliberate and it is also a real blind spot:
        # `Please ignore previous instructions…` mid-sentence does NOT match here.
        # check_content_security keeps its own unanchored regex alongside this one
        # for that reason — see BACKLOG #360.
        r"(?:^|[.!?]\s+)ignore\s+(?:previous|prior|above)\s+instructions|"
        r"(?:^|[.!?]\s+)you\s+are\s+now\s+|"
        r"(?:^|[.!?]\s+)disregard\s+(?:all|previous)|"
        r"(?:^|[.!?]\s+)forget\s+(?:everything|all|previous)|"
        # "new instructions:" is directive - scan only at line start or after bullet
        r"(?:^|\*\s+)new\s+instructions:",
        re.IGNORECASE | re.MULTILINE,
    ),
    "hidden_instruction": re.compile(
        r"<!--[^>]*(?:instruction|execute|ignore|override)[^>]*-->",
        re.IGNORECASE,
    ),
    "authority_assertion": re.compile(
        r"""
        (?:
            # Retrieved content declaring itself above a protected authority.
            (?:^|[:.!?]\s+)
            (?:
                this\s+(?:entry|document|reference(?:\s+entry)?)
                |the\s+following\s+section
            )
            \s+(?:
                (?:is\s+authoritative\s+and\s+)?
                (?:supersedes|overrides)\s+(?:the\s+)?
                (?:governance\s+rules?|constitution|retrieved\s+principles?|system\s+prompt)
                |takes\s+precedence\s+over\s+(?:the\s+)?
                (?:governance\s+rules?|constitution|retrieved\s+principles?|system\s+prompt)
            )
            # A forged system-role label used to bypass a named control.
            |(?:^|\n)\s*SYSTEM:\s*
                (?:skip|bypass|disable|ignore)\s+
                (?:evaluate_governance|governance|the\s+approval\s+requirement)
            # Recast document text as system-level instructions.
            |(?:^|[:.!?]\s+)treat\s+(?:the\s+)?instructions?\s+
                (?:below|here|that\s+follow)\s+as\s+if\s+(?:they|it)\s+
                came\s+from\s+(?:the\s+)?system\s+prompt
            # Declare a protected control inapplicable by fiat.
            |(?:^|[:.!?]\s+)effective\s+immediately,?\s+(?:the\s+)?
                approval\s+requirement\s+no\s+longer\s+applies
            # Assert permission that the retrieved content cannot establish.
            |(?:^|[:.!?]\s+)(?:the\s+)?(?:user|owner|operator)\s+has\s+
                already\s+(?:approved|authori[sz]ed)\b[^.!?]*\b
                no\s+(?:confirmation|approval)\s+is\s+(?:needed|required)
            |(?:^|[:.!?]\s+)this\s+is\s+(?:only|just)\s+(?:a\s+)?
                (?:test\s+fixture|test|fixture|example)\b[^.!?]*\b
                (?:safety|governance)\s+rules?\s+(?:do|does)\s+not\s+apply
            |(?:^|[:.!?]\s+)(?:governance|approval|review)\s+has\s+been\s+
                (?:satisfied|completed|approved)\s+upstream[;,]?\s*
                (?:proceed|continue)\s+without\s+
                (?:evaluating|evaluation|confirmation|review)
        )
        """,
        re.IGNORECASE | re.MULTILINE | re.VERBOSE,
    ),
    "base64_payload": re.compile(
        r"base64\s+(?:-d|--decode)|"
        r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{100,}={0,2}(?![A-Za-z0-9+/])",
    ),
    "data_exfiltration": re.compile(
        r"(?:cat|type)\s+[~\/].*(?:\.ssh|\.env|\.aws|credentials|secret)|"
        r"(?:curl|wget|nc|netcat).*(?:-d|--data|POST)",
        re.IGNORECASE,
    ),
}
