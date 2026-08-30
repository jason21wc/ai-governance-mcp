#!/usr/bin/env bash
# Shared secret redaction for hook diagnostic logs.
#
# Source from any hook that writes a command string to a log:
#   source "$HOOK_DIR/lib/redact.sh"
#   printf '%s' "$COMMAND" | redact_secrets
#
# WHY THIS IS SHARED AND NOT COPIED
# ---------------------------------
# This function lived inline in `pre-test-oom-gate.sh`. When the content-security
# hook gained its own deny log it needed the same redaction, and copying it would
# have produced two independently-maintained redactors — one of them guarding a
# SECURITY log. A pattern added to one copy and not the other is a silent leak in
# whichever copy was forgotten, and this repo has repeatedly recorded that a
# duplicated value drifts the moment either copy moves. One definition, two
# consumers.
#
# Layered patterns:
#   1. Specific token prefixes (OpenAI sk-, GitHub ghp_, AWS AKIA)
#   2. Bearer tokens
#   3. CLI flags (--api-key, --token, --secret, --password, --credential)
#   4. Generic KEY=VALUE environment variable patterns
#
# Trade-off: may redact legitimate args like --token-file=/path. Acceptable for a
# diagnostic log, where over-redaction is strictly better than a leaked secret.
#
# NOT a boundary. This reduces the chance a diagnostic log captures a credential
# that was pasted onto a command line; it does not make these logs safe to
# publish. Treat them as local diagnostics.

redact_secrets() {
    sed -E \
        -e 's/(sk-[a-zA-Z0-9]{3})[a-zA-Z0-9_-]*/\1<redacted>/g' \
        -e 's/(ghp_[a-zA-Z0-9]{4})[a-zA-Z0-9]*/\1<redacted>/g' \
        -e 's/AKIA[A-Z0-9]{12,}/AKIA<redacted>/g' \
        -e 's/(Bearer )[^ ]*/\1<redacted>/gI' \
        -e 's/(--(api[_-]?key|token|secret|password|credential)[= ])[^ ]*/\1<redacted>/gI' \
        -e 's/([A-Z_]*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)=)[^ ]*/\1<redacted>/g'
}
