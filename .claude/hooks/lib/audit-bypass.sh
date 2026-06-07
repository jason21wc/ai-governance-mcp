#!/usr/bin/env bash
# Shared audit-bypass logging for Claude Code hooks.
# Source from any hook script; call audit_bypass() when a bypass envvar fires.
#
# Usage:
#   source "$(dirname "${BASH_SOURCE[0]}")/lib/audit-bypass.sh"
#   audit_bypass "hook-name" "ENVVAR_NAME=value" "reason"

BYPASS_AUDIT_LOG="${BYPASS_AUDIT_LOG:-${HOME}/.claude/hook-bypass-audit.log}"

audit_bypass() {
    local hook_name="$1"
    local envvar="$2"
    local reason="${3:-}"
    mkdir -p "$(dirname "$BYPASS_AUDIT_LOG")" 2>/dev/null || return 0
    # Cap at 100KB — rotate by tailing last 500 lines.
    # Uses wc -c (POSIX) not stat (macOS/Linux divergence). See pre-exit-plan-mode-gate.sh.
    if [ -f "$BYPASS_AUDIT_LOG" ]; then
        local size
        size=$(wc -c < "$BYPASS_AUDIT_LOG" 2>/dev/null | tr -d ' ' || echo 0)
        if [ "${size:-0}" -gt 102400 ]; then
            tail -n 500 "$BYPASS_AUDIT_LOG" > "$BYPASS_AUDIT_LOG.tmp" 2>/dev/null && mv "$BYPASS_AUDIT_LOG.tmp" "$BYPASS_AUDIT_LOG" 2>/dev/null || true
        fi
    fi
    printf '%s %s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$hook_name" "$envvar" "$reason" >> "$BYPASS_AUDIT_LOG" 2>/dev/null || true
}
