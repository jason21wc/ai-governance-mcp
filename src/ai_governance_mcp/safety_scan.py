"""Deterministic, dependency-light safety scanning.

Two roles, intentionally co-located in a torch-free top-level module so the
enforcement proxy (`enforcement.py`, stdlib-only) can import them without
dragging in the retrieval engine / sentence-transformers:

1. **S-Series TOPIC detection** (`_detect_safety_concerns`, the safety keyword
   sets) — answers "is this action *about* something sensitive?" Tuned on AI
   `planned_action` text; used by the governance server for ESCALATE routing.
   Re-exported from `server/_constants.py` + `server/__init__.py` for back-compat.

2. **Act-intrinsic VALUE/LOCUS detection** (`act_intrinsic_block`) — answers
   "does this action *carry* a secret value or *touch* a credential path?" These
   are deterministic value/path signatures (near-zero false positives on human
   prose), the opposite question from the topic keywords. Used by the proxy as a
   non-model-satisfiable gate: it reads the action's real arguments, so the model
   cannot dodge it by re-describing its plan to governance.

DEFENSE-IN-DEPTH, NOT A BOUNDARY: literal matching is defeated by deliberate
obfuscation (splitting a secret across fields, base64, homoglyphs). It blocks
naive/injected exfiltration, not an adversarial model.
"""

import re

# ---------------------------------------------------------------------------
# S-Series safety TOPIC keyword sets + demotion gates (moved from _constants.py
# / handlers/governance.py; behavior-preserving — guarded by FM-S-SERIES tests).
# ---------------------------------------------------------------------------

CRITICAL_SAFETY_KEYWORDS = {
    "credential",
    "password",
    "secret",
    "api key",
    "private key",
    "access token",
    "encryption key",
    "pii",
    "personal data",
    "irreversible",
    "destructive",
}

ADVISORY_SAFETY_KEYWORDS = {
    "delete",
    "remove",
    "drop",
    "destroy",
    "wipe",
    "purge",
    "erase",
    "truncate",
    "clear",
    "reset",
    "overwrite",
    "deploy",
    "token",
    "security",
    "authentication",
    "authorization",
    "permission",
    "external api",
    "production",
    "database",
    "user data",
    "sensitive",
    "confidential",
}

# Safe-context leaders demote a keyword match when EVERY sentence containing it
# also contains one of these. Negation forms (no/not/never/cannot + the n't
# contraction suffix) are first-class leaders — the precision report 2026-06-20
# showed "not a destructive operation" was forcing ESCALATE because only "no"
# was recognized. The trailing `n['’]t\b` alternative matches contraction
# suffixes (isn't/doesn't/won't); it sits OUTSIDE the `\b(...)\b` group because
# there is no word boundary before the `n` in "isn't" (`\bn't\b` would fail).
_SAFE_CONTEXT_LEADERS = re.compile(
    r"\b("
    r"no|not|without|never|cannot|purely|"
    r"describing|description\s+of|class\s+of|category\s+of|"
    r"example\s+of|meta-?description\s+of|kind\s+of|"
    r"documents?|catalogs?|tracks?|enumerates?|references?|notes?|records?|"
    r"prior|previous|historical|past|former|hypothetical|theoretical|"
    r"discussion\s+of|review\s+of|audit\s+of"
    r")\b"
    r"|(?<=\w)n['’]t\b",
    re.IGNORECASE,
)

# Danger-action verbs come in TWO tiers with DIFFERENT scoping (BACKLOG #129
# precision arc, 2026-06-20). Both block safe-context demotion (the bypass-vector
# defense — a negation cannot talk the gate out of a real action), but:
#
#   _IMPERATIVE_ACTION_VERBS (MUTATION / destruction) — checked FIELD-WIDE.
#     A destroy/mutate verb ANYWHERE in a field blocks demotion of any CRITICAL
#     keyword in that field. Conservative on purpose: catches
#     "Delete the production database; the credentials are not affected"
#     (the dangerous clause has no critical keyword of its own).
#
#   _EGRESS_VERBS (DISCLOSURE / exfiltration) — checked SENTENCE-SCOPED (see
#     `_is_keyword_in_safe_context`). An egress verb blocks demotion only when it
#     sits in the SAME sentence as the keyword. This closes "not destructive,
#     just send the credential" (egress + secret co-located → escalate) WITHOUT
#     re-flagging "Publish the release notes. No credentials." (egress in a
#     keyword-free clause → still demotes). Sentence-scoping is what lets the
#     egress set be generous without re-introducing the false positives this arc
#     removes. Origin: security-auditor HIGH finding — adding negation leaders
#     widened a credential-egress FN that the prior mutation-only gate missed.
#
# Residual (the lexical limit): an exotic egress verb nobody enumerated, or a
# cross-sentence pronoun ("export IT"), still slips. The real fix is semantic —
# tracked under BACKLOG #73. Per the FM-S-SERIES co-evolution rule, widening the
# leader list requires auditing BOTH verb tiers.
_IMPERATIVE_ACTION_VERBS = re.compile(
    r"\b("
    r"ship|deploy|delete|drop|truncate|wipe|rm|erase|purge|"
    r"execute|run|apply|merge|push|force|force-push|"
    r"override|bypass|disable|kill|"
    r"nuke|format|chmod|chown|sudo|flush|revoke|terminate|expire|unset|mv|"
    r"rotate|replace|migrate|modify|restart|restore|clone|copy|move"
    r")\b",
    re.IGNORECASE,
)

# Deliberately EXCLUDES low-signal verbs that read benignly even when co-located
# with a negated secret (e.g. "put"/"emit": "we put no secrets in the repo") —
# they would re-introduce the false ESCALATEs this arc removes. The kept set is
# high-signal-for-exfiltration; the residual (an exotic egress verb) is the
# accepted lexical limit (BACKLOG #73).
_EGRESS_VERBS = re.compile(
    r"\b("
    r"send|post|email|mail|publish|upload|share|forward|transmit|"
    r"exfiltrate|disclose|expose|leak|dump|export|print|"
    r"curl|scp|sftp|base64|tee"
    r")\b",
    re.IGNORECASE,
)

_SENTENCE_BOUNDARY = re.compile(r"[.!?;\n]+|\s[—–]\s")

# Layer-0 insecure-persistence floor (BACKLOG #73, plan async-giggling-wren).
# Deliberately NARROW strong-signal membership: a floor hit forces a
# deterministic ESCALATE *under* the keyword-adjudication judge, so a floor
# false-positive merely reproduces pre-judge behavior — but it also denies the
# judge the chance to clear a benign mention, so noun-collision verbs this
# project's own vocabulary uses constantly (commit/log/write/embed/cache) are
# EXCLUDED and left to the judge. Membership is tuned against the live FP
# specimens + the 16-string FN corpus (see tests + the Stage-1 eval).
_PERSISTENCE_VERBS = re.compile(
    r"\b("
    r"hardcode[sd]?|hardcoding|"
    r"store[sd]?|storing|"
    r"save[sd]?|saving|"
    r"persist(?:s|ed|ing)?"
    r")\b",
    re.IGNORECASE,
)

# 'plaintext'/'cleartext' co-located with a CRITICAL keyword is itself the
# insecure-persistence signal — no verb needed ("the password ends up in
# plaintext on disk").
_PLAINTEXT_SIGNALS = re.compile(r"\b(plain\s?text|cleartext)\b", re.IGNORECASE)


def detect_insecure_persistence(action: str) -> list[str]:
    """Sentence-scoped insecure-persistence floor: verb/plaintext + CRITICAL keyword.

    Returns hit messages (one per signal×keyword pair) when a persistence
    signal and a CRITICAL safety keyword co-locate in the same sentence AND
    that sentence carries no safe-context leader. A leader in the co-located
    sentence suppresses the floor (the judge still sees the trigger); a leader
    elsewhere cannot talk the floor out of a real hit. Consumed by the
    governance handler's routing (a floor hit escalates deterministically,
    judge never consulted) — this function does NOT alter
    `_detect_safety_concerns` demotion semantics.
    """
    if not action:
        return []
    hits: list[str] = []
    for sentence in _SENTENCE_BOUNDARY.split(action.lower()):
        if not sentence:
            continue
        keywords = [kw for kw in CRITICAL_SAFETY_KEYWORDS if kw in sentence]
        if not keywords:
            continue
        if _SAFE_CONTEXT_LEADERS.search(sentence):
            continue
        verb_match = _PERSISTENCE_VERBS.search(sentence)
        plaintext_match = _PLAINTEXT_SIGNALS.search(sentence)
        signal = verb_match or plaintext_match
        if not signal:
            continue
        for keyword in sorted(keywords):
            hits.append(
                f"Insecure-persistence signal: '{signal.group(0)}' "
                f"co-located with '{keyword}'"
            )
    return list(dict.fromkeys(hits))


def _is_keyword_in_safe_context(action_lower: str, keyword: str) -> bool:
    """True iff EVERY sentence with `keyword` has a leader AND no EGRESS verb.

    Sentence-level granularity (vs. position-span envelope-coverage) handles
    multi-word keywords natively and is robust to leader-before-keyword OR
    leader-after-keyword phrasings. Default-deny: a sentence holding the keyword
    that lacks a safe-context leader — OR that contains a disclosure/egress verb
    (`_EGRESS_VERBS`, e.g. send/email/exfiltrate co-located with the secret) —
    makes the action unsafe. The egress check is sentence-scoped on purpose: an
    egress verb in a keyword-free clause does not block demotion (no FP), while
    one co-located with the secret does (closes the exfiltration FN). The
    field-wide MUTATION tier is applied separately by the caller.

    Note: case-insensitive substring match for the keyword (mirrors the existing
    CRITICAL/ADVISORY scan semantics — does NOT add word boundaries, since the
    existing scan accepts plurals like "credentials" matching "credential").
    """
    sentences = _SENTENCE_BOUNDARY.split(action_lower)
    keyword_lower = keyword.lower()
    saw_keyword_anywhere = False
    for sentence in sentences:
        if keyword_lower in sentence:
            saw_keyword_anywhere = True
            if not _SAFE_CONTEXT_LEADERS.search(sentence):
                return False  # Keyword in a sentence with no leader → unsafe
            if _EGRESS_VERBS.search(sentence):
                return False  # Egress verb co-located with the keyword → unsafe
    return saw_keyword_anywhere


def detect_critical_keywords(action: str) -> list[str]:
    """CRITICAL safety keywords present in `action` and NOT demoted to safe context.

    The single source of truth for "which CRITICAL keywords force escalation for
    this text" — shared by `_detect_safety_concerns` (message construction) and the
    governance handler (per-field keyword provenance for the #73 adjudicator), so
    the two never drift and the keyword is never parsed back out of a message.
    """
    action_lower = action.lower()
    imperative_present = bool(_IMPERATIVE_ACTION_VERBS.search(action_lower))
    return [
        keyword
        for keyword in CRITICAL_SAFETY_KEYWORDS
        if keyword in action_lower
        and not (
            not imperative_present
            and _is_keyword_in_safe_context(action_lower, keyword)
        )
    ]


def _detect_safety_concerns(action: str) -> tuple[list[str], list[str]]:
    """Detect potential safety concerns with two confidence levels.

    Returns (critical_concerns, advisory_concerns):
    - critical_concerns: keywords that ALWAYS force escalation
    - advisory_concerns: keywords that produce warnings only (escalate
      only when semantic retrieval also finds S-Series principles)

    Negation handling: this function DOES NOT parse negation directly
    ("not delete" still flags), because negation parsing creates bypass
    vectors. Instead, a closed allowlist of safe-context leader phrases
    (negation forms not/never/cannot/n't, meta-description, governance-prose
    idioms, temporal distancing) governs two demotions under ONE shared
    predicate:
      - a CRITICAL keyword is demoted to ADVISORY, and
      - an ADVISORY keyword's warning is SUPPRESSED,
    when BOTH hold:
      (a) every sentence containing the keyword also contains a leader, AND
      (b) NO danger verb threatens the keyword, across TWO tiers (above): a
          MUTATION verb (`_IMPERATIVE_ACTION_VERBS`) anywhere in the action
          blocks demotion FIELD-WIDE; an EGRESS verb (`_EGRESS_VERBS`) blocks
          only when co-located in the keyword's sentence (enforced inside
          `_is_keyword_in_safe_context`). So "not destructive, send the
          credential" escalates (egress + secret co-located) while "publish the
          notes; no credentials" demotes (egress in a keyword-free clause).
    Critical demotion preserves the audit trail via the resulting advisory
    message; advisory suppression removes pure noise (advisory never vetoes
    alone, so suppression has zero veto impact). See
    FM-S-SERIES-KEYWORD-FALSE-POSITIVE (re-registered 2026-05-01 / BACKLOG #129;
    negation leaders + two-tier danger gate + advisory suppression added
    2026-06-20 per the precision report).
    """
    action_lower = action.lower()
    critical: list[str] = []
    advisory: list[str] = []

    # MUTATION-verb gate (field-wide): a destroy/mutate verb anywhere blocks
    # demotion. The EGRESS tier is sentence-scoped and applied inside
    # `_is_keyword_in_safe_context`. Computed once; shared by the critical
    # demotion and advisory suppression so the predicate is identical.
    imperative_present = bool(_IMPERATIVE_ACTION_VERBS.search(action_lower))

    def _in_safe_context(keyword: str) -> bool:
        return not imperative_present and _is_keyword_in_safe_context(
            action_lower, keyword
        )

    # CRITICAL: demote to ADVISORY in safe context, else escalate. Which keywords
    # land critical is decided by the shared `detect_critical_keywords` SSOT; the
    # keyword variable is in scope at message-construction time, so it is never
    # parsed back out of a message (apostrophe-safety holds structurally — per
    # BACKLOG #129 post-arc contrarian audit a8e2e0926f756db45 HIGH #2).
    critical_keywords = set(detect_critical_keywords(action))
    for keyword in CRITICAL_SAFETY_KEYWORDS:
        if keyword in action_lower:
            if keyword in critical_keywords:
                critical.append(f"Action mentions '{keyword}' - requires safety review")
            else:
                advisory.append(
                    f"Action mentions '{keyword}' in safe context - advisory only"
                )

    # ADVISORY: warn unless the same safe-context condition suppresses the noise.
    # (Suppression applies only to native-advisory keywords; demoted-from-critical
    # advisory messages above are kept — the audit trail of the demotion.)
    for keyword in ADVISORY_SAFETY_KEYWORDS:
        if keyword in action_lower and not _in_safe_context(keyword):
            advisory.append(f"Action mentions '{keyword}' - may require safety review")

    return critical, advisory


# ---------------------------------------------------------------------------
# Act-intrinsic VALUE / LOCUS detection (for the enforcement proxy).
#
# These match an actual secret VALUE or a credential file PATH, not a topic
# word — near-zero false positives on human prose. High-confidence patterns
# reused from global-skills/security-scan/procedure.md + the credential-path
# set from .claude/hooks/pre-tool-content-security.sh. NOT subject to the
# safe-context demotion above (a secret value / credential path is a value, not
# a topic that can be "described safely"). Same deterministic class as the path
# regex — NOT a semantic classifier (the session-196 rejection stands).
# ---------------------------------------------------------------------------

# (label, compiled-pattern). Case-sensitive on purpose (AKIA upper, sk- lower).
# This is the BLOCK set — it must be FP-averse (a match hard-denies an action),
# so only high-confidence value shapes. Distinct from the log-redaction
# `SECRET_PATTERNS` in `server/_constants.py`, which is deliberately FP-tolerant
# (over-redacting a log is harmless; over-blocking an action is not). Do NOT
# merge them. Modern provider formats matter: `sk-proj-`/`sk-svcacct-` keys
# break a bare `sk-[A-Za-z0-9]+` on the hyphen, so they need their own pattern.
_SECRET_VALUE_PATTERNS = [
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("OpenAI key", re.compile(r"\bsk-(?:proj|svcacct|admin)-[A-Za-z0-9_-]{20,}\b")),
    ("OpenAI key (legacy)", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("Stripe key", re.compile(r"\b[rs]k_(?:live|test)_[A-Za-z0-9]{20,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained PAT", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("PEM private key", re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")),
]

# Credential file paths (loci). Home-relative + literal /Users//home forms.
_HOME = r"(?:~|\$HOME|\$\{HOME\}|/Users/[^/\s]+|/home/[^/\s]+)"
_CREDENTIAL_PATH_PATTERNS = [
    re.compile(_HOME + r"/\.ssh/"),
    re.compile(_HOME + r"/\.aws/"),
    re.compile(_HOME + r"/\.gnupg/"),
    re.compile(_HOME + r"/\.netrc\b"),
    re.compile(_HOME + r"/\.docker/config\.json"),
    re.compile(_HOME + r"/\.kube/config\b"),
    re.compile(_HOME + r"/\.npmrc\b"),
    re.compile(r"/etc/ssl/private/"),
]

_MAX_SCAN_CHARS = (
    64 * 1024
)  # per-leaf cap so a base64 attachment can't blow up the regex
_MAX_LEAVES = 1024  # bound total work on a deeply-nested / many-field payload


def _iter_string_values(obj):
    """Yield string-valued LEAVES of a JSON-ish structure (never dict keys)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _iter_string_values(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            yield from _iter_string_values(value)


def scan_tool_values(arguments) -> str | None:
    """Scan a tool call's argument VALUES for a credential path or secret value.

    Returns a short reason string if a deterministic secret signature is found in
    any string-valued leaf, else None. Keys are never scanned, so a field literally
    named "password" with an empty value is not a match.
    """
    if not arguments:
        return None
    # Scan each string leaf INDEPENDENTLY (capped per-leaf), not a single joined
    # blob — otherwise a secret in a field ordered after a >64KB field would fall
    # past the cap (a padding evasion + accidental FN on large multi-field
    # payloads), and the full join would materialize a huge temp string.
    for i, leaf in enumerate(_iter_string_values(arguments)):
        if i >= _MAX_LEAVES:
            break
        chunk = leaf[:_MAX_SCAN_CHARS]
        for pattern in _CREDENTIAL_PATH_PATTERNS:
            if pattern.search(chunk):
                return "credential path"
        for label, pattern in _SECRET_VALUE_PATTERNS:
            if pattern.search(chunk):
                return f"secret value ({label})"
    return None


def act_intrinsic_block(arguments) -> str | None:
    """Deterministic act-intrinsic block decision for a tool call's arguments.

    Returns a deny message (hard block) when the action's own content carries a
    secret value or touches a credential path; returns None to allow. This is
    non-model-satisfiable for the matched signatures (it reads the action itself,
    not the model's description) but is defense-in-depth, not a boundary —
    deliberate obfuscation defeats literal matching.
    """
    reason = scan_tool_values(arguments)
    if reason is None:
        return None
    return (
        f"GOVERNANCE BLOCK: this action's content matched a {reason}. "
        "Exfiltration of credentials/secrets is blocked by the enforcement proxy "
        "(act-intrinsic safety gate). If this is a genuine false positive, a human "
        "must approve it explicitly via the host's tool-approval prompt."
    )
