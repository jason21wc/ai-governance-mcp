#!/usr/bin/env bash
# Shared cadence date helpers for the SessionStart surfacer hooks.
#
# REPO-CANONICAL: .claude/hooks/lib/cadence.sh. The user-level `lib/` directories
# under ~/.claude/hooks and ~/.codex/hooks are SYMLINKS to .claude/hooks/lib, so
# this file has no second copy — edit here and it is live for every project
# (BACKLOG #226). Guarded by scripts/check-installed-hooks.sh.
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

# date_field_from_operations <operations_file> <anchor> <field>
#   anchor e.g. 'C-078' or 'RW-313'; field e.g. 'Next due' or 'Counting since'.
#   Echoes the FIRST YYYY-MM-DD found in a line containing <field> inside that
#   item's section (from the '### <anchor>' heading up to the next '## '/'### '
#   heading or a '---' rule). Echoes '' if not found. For date ranges
#   (e.g. "~2026-06-01-2026-06-06") the earliest date is taken — surfaces the
#   reminder conservatively at the start of the window. Input read is line-capped
#   to guard against a pathological file.
#
#   The field is a PARAMETER rather than the hardcoded 'Next due' it used to be,
#   because OPERATIONS.md carries two kinds of item and only one of them has a due
#   date: date-based cadences (C-series) and count-based observation windows
#   (RW-series), which are anchored to the date counting STARTED. Hardcoding the
#   date-based field is why RW-313 could not be surfaced by the same reader.
date_field_from_operations() {
    python3 -c "
import re, sys
path, anchor, field = sys.argv[1], sys.argv[2], sys.argv[3]
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
            if field in line:
                m = date_re.search(line)
                if m:
                    print(m.group(1)); sys.exit(0)
except Exception:
    pass
print('')
" "${1:-}" "${2:-}" "${3:-}" 2>/dev/null || echo ''
}

# next_due_from_operations <operations_file> <anchor>
#   The date-based-cadence spelling of the above. Kept as the named entry point its
#   callers and tests already use; the parsing lives in ONE place
#   (meta-core-single-source-of-truth).
next_due_from_operations() {
    date_field_from_operations "${1:-}" "${2:-}" 'Next due'
}

# section_exists_in_operations <operations_file> <anchor>
#   True when the item's `### <anchor>` heading is present, using the SAME three
#   accepted forms as the parser above (`### X.`, `### X `, bare `### X`), with the
#   same leading-whitespace tolerance. It exists because a caller open-coded
#   `grep -qE "^### ${anchor}[. ]"` and the two disagreed on a bare heading: the
#   grep missed it, the parser would have found its date, and the caller took its
#   "section absent, stay silent" branch — reintroducing the silent-disable it was
#   written to prevent. Same defect class as the anchor being interpolated into an
#   ERE unescaped, which this also removes.
section_exists_in_operations() {
    python3 -c "
import sys
path, anchor = sys.argv[1], sys.argv[2]
try:
    with open(path, encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f):
            if i > 20000:
                break
            s = line.lstrip()
            if s.startswith('### ' + anchor + '.') or s.startswith('### ' + anchor + ' ') or s.rstrip() == '### ' + anchor:
                sys.exit(0)
except Exception:
    pass
sys.exit(1)
" "${1:-}" "${2:-}" 2>/dev/null
}

# last_git_date <repo_dir> <grep_pattern>
#   Echoes the committer short-date (YYYY-MM-DD) of the most recent commit (within
#   ~400 days) whose SUBJECT matches the case-insensitive extended regex, or '' if
#   none / not a repo. The --since bound caps the history walk; cadences are <=30d
#   so older matches never matter, and a missed ancient match yields the
#   conservative "no prior activity" surface. NOTE: any git error (corrupt repo,
#   git missing) also maps to '' -> fail-toward-surfacing.
#
#   SUBJECT-ONLY match (BACKLOG #167; sibling of the session-start-dream.sh fix). A bare
#   `git log --grep` searches the WHOLE message, so a commit that merely NAMES the cadence
#   token in its BODY (e.g. a later commit describing the cadence) gets mistaken for cadence
#   activity -> the cadence looks more recent than it is -> a due nudge gets suppressed on
#   this fallback path. Print "<date>\t<subject>" per commit and grep the line: the date
#   column has no letters, so a match can only land in the subject. `sed -n 1p` reads the
#   whole stream (no early close) to avoid a head/awk SIGPIPE under `pipefail`; the trailing
#   `|| echo ''` maps a git-error / no-match (grep exit 1 under pipefail) to the empty path.
last_git_date() {
    git -C "${1:-.}" log --since="400 days ago" --format='%cs%x09%s' 2>/dev/null \
        | grep -iE "${2:-}" | cut -f1 | sed -n '1p' || echo ''
}

# sessions_since <since> <transcript_dir>
#   Echoes the count of flat top-level *.jsonl transcripts in <transcript_dir> whose
#   mtime is newer than <since> — a local "YYYY-MM-DD HH:MM:SS" timestamp accepted by
#   `find -newermt` on both BSD (macOS) and GNU (CI). The current in-progress session's
#   transcript lives in this dir too and is counted — the CALLER subtracts it.
#
#   Dir missing/unreadable -> echoes the sentinel -1 (DISTINCT from a real 0 count).
#   Scope: -1 covers the dir-absent case only; a <since> that `find -newermt` cannot
#   parse would degrade to 0/silent (not -1) — but <since> is git --date=format-local
#   output (a fixed, controlled format), so that path is not reachable in practice.
#   This is a DELIBERATELY different failure direction than days_since: the dream
#   trigger is activity-only with no calendar floor, so the caller treats -1 as
#   "cannot assess" and stays SILENT rather than firing — an unbounded every-session
#   nag in a broken environment would be worse than silence (the dir essentially
#   always exists under Claude Code; -1 is the genuine-anomaly path).
sessions_since() {
    local since="${1:-}" dir="${2:-}" n
    [ -d "$dir" ] || { printf '%s\n' -1; return; }
    # `|| echo -1` is load-bearing under the callers' `set -euo pipefail`. GNU
    # find REJECTS a malformed `-newermt` argument (a typo'd date in a
    # hand-edited OPERATIONS.md is enough) and exits non-zero; `pipefail` then
    # propagates that through the assignment and `set -e` kills the calling hook
    # BEFORE it emits anything — in files whose headers promise "Exit 0 always".
    # Degrade to the unassessable sentinel instead, which every caller already
    # handles. BSD find (macOS) accepts the same malformed date and returns 0, so
    # this is invisible on the development platform and only bites on Linux —
    # verified both ways rather than assumed.
    n=$(find "$dir" -maxdepth 1 -type f -name '*.jsonl' -newermt "$since" 2>/dev/null | wc -l | tr -d ' ' || echo -1)
    [ -n "$n" ] || n=-1
    printf '%s\n' "$n"
}
