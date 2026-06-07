#!/usr/bin/env bash
# Shared cadence date helpers for the SessionStart surfacer hooks.
#
# MIRRORED COPY. This file is byte-identical in two locations:
#   - .claude/hooks/lib/cadence.sh        (repo; canonical source)
#   - ~/.claude/hooks/lib/cadence.sh      (user-level; for the global dream hook)
# A user-level hook cannot source files from inside a project repo, so the copy
# is unavoidable. Keep them byte-identical — edit the repo copy, then mirror.
#
# Design: STATELESS. No stamp files. Dates are read live from the authoritative
# single source of truth on every session start (OPERATIONS.md "Next due:" for
# project cadences; `git log` for the dream cadence). Avoids the new-write-path /
# passive-trigger-calcification risk (C-109).
#
# Requires: python3 (date + regex parsing — portable, sidesteps BSD/GNU `date`
# divergence) and git >= 2.21 for `--format=%cs` (committer short-date). Both are
# present on macOS and Linux CI.

# days_until <YYYY-MM-DD>
#   Echoes integer days from today to the target date (>0 future, <=0 due/overdue).
#   On parse error echoes -99999 (FAIL-TOWARD-SURFACING: a broken date surfaces the
#   reminder rather than hiding an overdue cadence — a spurious nudge is cheap, a
#   missed review is not).
days_until() {
    python3 -c "
import sys
from datetime import date
try:
    y, m, d = (int(x) for x in sys.argv[1].split('-'))
    print((date(y, m, d) - date.today()).days)
except Exception:
    print(-99999)
" "${1:-}" 2>/dev/null || printf '%s\n' -99999
}

# days_since <YYYY-MM-DD>
#   Sign-safe inverse of days_until: integer days ELAPSED since the date
#   (>=0 for past dates). Keeps the sign convention in one place so callers don't
#   re-derive `-1 * days_until`. Parse error -> 99999 (fail-toward-surfacing).
days_since() {
    local du
    du=$(days_until "${1:-}")
    printf '%s\n' "$(( -1 * du ))"
}

# next_due_from_operations <operations_file> <anchor>
#   anchor e.g. 'C-078'. Echoes the FIRST YYYY-MM-DD found in a 'Next due:' line
#   inside that cadence's section (from the '### <anchor>' heading up to the next
#   '## '/'### ' heading or a '---' rule). Echoes '' if not found. For date ranges
#   (e.g. "~2026-06-01-2026-06-06") the earliest date is taken — surfaces the
#   reminder conservatively at the start of the window. Input read is line-capped
#   to guard against a pathological file.
next_due_from_operations() {
    python3 -c "
import re, sys
path, anchor = sys.argv[1], sys.argv[2]
date_re = re.compile(r'(\d{4}-\d{2}-\d{2})')
hdr_re = re.compile(r'^#{2,3}\s')
in_section = False
try:
    with open(path, encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f):
            if i > 20000:
                break
            s = line.lstrip()
            if not in_section:
                if s.startswith('### ' + anchor + '.') or s.startswith('### ' + anchor + ' ') or s.rstrip() == '### ' + anchor:
                    in_section = True
                continue
            if hdr_re.match(line) or line.strip() == '---':
                break
            if 'Next due' in line:
                m = date_re.search(line)
                if m:
                    print(m.group(1)); sys.exit(0)
except Exception:
    pass
print('')
" "${1:-}" "${2:-}" 2>/dev/null || echo ''
}

# last_git_date <repo_dir> <grep_pattern>
#   Echoes the committer short-date (YYYY-MM-DD) of the most recent commit (within
#   ~400 days) whose message matches the case-insensitive extended regex, or '' if
#   none / not a repo. The --since bound caps the history walk; cadences are <=30d
#   so older matches never matter, and a missed ancient match yields the
#   conservative "no prior activity" surface. NOTE: any git error (corrupt repo,
#   git missing) also maps to '' -> fail-toward-surfacing.
last_git_date() {
    git -C "${1:-.}" log -1 -i -E --since="400 days ago" --grep="${2:-}" --format=%cs 2>/dev/null || echo ''
}
