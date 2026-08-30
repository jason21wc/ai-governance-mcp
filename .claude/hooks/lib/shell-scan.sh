#!/usr/bin/env bash
# Shared helper — strip QUOTED REGIONS from a shell command before pattern-matching it.
#
# THE ROOT CAUSE THIS FIXES (observed n=3 in one session, 2026-07-13):
#
# Both safety gates match dangerous tokens against the RAW command string. A token
# inside a quoted region — a commit message, an echo string, a grep pattern, a heredoc
# body — is not executable, but a token-anchored matcher cannot tell the difference:
#
#   1. pre-push-quality-gate:  git commit -m "...bandit -r src/ -f txt..."
#                              -> the ` -f ` in the MESSAGE tripped force-push detection.
#   2. pre-test-oom-gate:      git commit -m "...ran pytest tests/..."   (OPERATIONS T-143)
#                              -> `pytest` in the MESSAGE tripped the OOM gate.
#   3. pre-test-oom-gate:      echo "===== the pytest matcher ====="
#                              -> blocked a read-only `echo`. This one fired while its
#                                 author was trying to READ the hook to fix defect #2.
#
# The oom gate documents #2/#3 as an accepted false positive ("we'd rather block a
# harmless echo than miss a real invocation"). That trade was defensible at n=1. At n=3,
# with one shared cause, the structural fix is cheaper than the standing friction —
# and the friction has a real cost: a gate that cries wolf trains people to bypass it.
#
# WHAT THIS DOES: replaces the CONTENTS of quoted regions with a single space, leaving
# executable position intact.
#
#   pytest tests/ -m "not slow"          ->  pytest tests/ -m           (still matches)
#   git push --force origin main         ->  git push --force origin main  (still matches)
#   echo "run pytest tests/"             ->  echo                       (no longer matches)
#   git commit -m "use -f to force"      ->  git commit -m              (no longer matches)
#   git commit -F msg.txt <<'EOF' ... EOF->  git commit -F msg.txt      (body stripped)
#
# KNOWN RESIDUAL (accepted, stated honestly): a deliberately QUOTED command name would
# evade — `"pytest" tests/` and `'git' push --force` are valid shell and would no longer
# match. This is OUT OF THREAT MODEL: these gates exist to stop an AI from running a
# dangerous command *carelessly*, not to stop an adversary who is actively evading them.
# An AI with documented bypass env-vars (PYTEST_ALLOW_HEAVY, QUALITY_GATE_SKIP) has no
# incentive to smuggle a command past a gate it can simply ask to skip. If the threat
# model ever becomes adversarial, this helper is the wrong layer and a real shell parser
# is required.
#
# FAIL-SAFE: if python3 is unavailable, errors, OR RETURNS NOTHING, this echoes the
# ORIGINAL command unchanged. A gate then sees the raw string and behaves exactly as it
# did before this helper existed — over-blocking, never under-blocking. Degradation
# direction is deliberate: for a safety gate, a false positive is survivable and a false
# negative is not.
#
# The "OR RETURNS NOTHING" clause was missing until session-272 (BACKLOG #298) and the
# omission was invisible: the guarantee was written here, believed, and tested only on
# the nonzero-exit path. A python3 exiting 0 with empty output disabled all three
# consuming gates at once. See the implementation note in the function body.
#
# WHAT THIS HELPER STILL CANNOT DO. It is one preprocessing step; it cannot make its
# CALLERS fail closed. A Claude Code PreToolUse hook denies only by positively asserting
# it (exit 2, or JSON carrying permissionDecision=deny) — verified against the installed
# CLI 2.1.220 and the published hooks reference. Every other outcome, including exit 1,
# exit 127, a failed `source`, an unbound variable under `set -u`, a timeout, and
# malformed JSON, is ALLOWED. There is no harness-level fail-closed setting. So a gate
# that crashes before reaching its own `exit 2` is simply off, and no amount of care in
# this file changes that. Tracked as the class fix.

# ---------------------------------------------------------------------------
# shell_arg_segments <command-string>
#   Splits the command at UNQUOTED shell separators (&& || ; | newline) and
#   echoes one segment per line, with quote CHARACTERS removed and their
#   CONTENTS PRESERVED.
#
# WHY THIS EXISTS — the third view, and the defect that forced it.
# -----------------------------------------------------------------------
# strip_quoted_regions answers a DETECTION question ("is this command in
# executable position?") by deleting quoted contents. A gate also has to answer
# an ARGUMENT question ("what arguments did that command get?"), and the two
# need opposite treatment of quotes: `-m "not slow"` is a legitimately quoted
# ARGUMENT, so the detection view erases it.
#
# The oom gate resolved that by running argument analysis against the RAW
# command — and that is a measured under-block, because the raw string contains
# every OTHER command on the line too:
#
#   git commit -m "fix tests/test_server.py" && pytest tests/
#
# The path lives in a commit message, but "is this run targeted?" asked of the
# whole line finds it and calls the bare full-suite run targeted. Measured
# session-272: DENY before, ALLOW after the terminator class was widened to
# accept a closing quote. The widening was correct; asking the question of the
# wrong subject was the defect, and it was latent before the widening exposed it.
#
# So the question has to be scoped to ONE command's own segment:
#
#   git commit -m "fix tests/test_server.py" && pytest tests/
#     -> segment 1:  git commit -m fix tests/test_server.py
#     -> segment 2:  pytest tests/           (no test path -> NOT targeted -> deny)
#
#   pytest "tests/test_server.py" -q
#     -> segment 1:  pytest tests/test_server.py -q   (targeted -> allow)
#
# DEGRADED PATH: a bash-native splitter, not "return nothing".
#
# The first version of this helper emitted nothing when python3 failed, on the
# reasoning that its only consumer gates `pytest`, which cannot run without
# python3 anyway. That reasoning is WRONG and the cross-product matrix caught it:
# a console script's shebang is an ABSOLUTE interpreter path, so shadowing
# `python3` on PATH does not stop `pytest` from running. Measured: `pytest
# tests/test_a.py` and `pytest -m "not slow"` — both ordinary targeted runs —
# were DENIED with python3 shadowed. That is a false positive on everyday work,
# and the escape is a bypass env var, which is the shape that trains routine
# bypass use.
#
# So the fallback re-implements the split with bash parameter expansion only.
# It is coarser: quote characters are removed before splitting, so a separator
# INSIDE a quoted argument (`-k "a || b"`) splits where it should not. The
# direction of that error is safe — an over-split segment loses its safe-subset
# marker and the run is denied, never silently allowed.
#
# FAIL-SAFE DIRECTION IS DELIBERATE AND OPPOSITE TO strip_quoted_regions.
# That helper returns the RAW command on failure, because its consumers match
# to DENY and a raw string over-blocks. This helper's consumers match to ALLOW
# (a matched safe-subset pattern EXEMPTS a run), so handing back the whole raw
# command would over-ALLOW — it would reintroduce the very defect this helper
# exists to fix. Segment structure has to be preserved or approximated, never
# discarded wholesale.
_shell_arg_segments_bash() {
    local _s="$1"
    # Drop quote characters, keep their contents.
    _s=${_s//\"/}
    _s=${_s//\'/}
    # Longest separators first, so && does not become two & breaks.
    _s=${_s//&&/$'\n'}
    _s=${_s//||/$'\n'}
    _s=${_s//;/$'\n'}
    _s=${_s//|/$'\n'}
    _s=${_s//&/$'\n'}
    # Trim each line; drop empties.
    local _line _acc=""
    while IFS= read -r _line; do
        _line="${_line#"${_line%%[![:space:]]*}"}"
        _line="${_line%"${_line##*[![:space:]]}"}"
        [ -n "$_line" ] || continue
        if [ -z "$_acc" ]; then _acc="$_line"; else _acc="$_acc
$_line"; fi
    done <<EOF
$_s
EOF
    printf '%s' "$_acc"
}

shell_arg_segments() {
    local _cmd="$1"

    if ! command -v python3 >/dev/null 2>&1; then
        _shell_arg_segments_bash "$_cmd"
        return 0
    fi

    local _out _rc
    _out=$(
        printf '%s' "$_cmd" | python3 -c '
import sys

src = sys.stdin.read()
segs = []
cur = []
i = 0
n = len(src)

def flush():
    s = "".join(cur).strip()
    if s:
        segs.append(s)
    del cur[:]

while i < n:
    ch = src[i]

    # Backslash escape outside quotes — keep both characters.
    if ch == "\\" and i + 1 < n:
        cur.append(ch)
        cur.append(src[i + 1])
        i += 2
        continue

    # Single quotes: literal. Drop the quote chars, keep the contents.
    if ch == "\x27":
        i += 1
        while i < n and src[i] != "\x27":
            cur.append(src[i])
            i += 1
        i += 1 if i < n else 0
        continue

    # Double quotes: honour backslash escapes. Drop quotes, keep contents.
    if ch == "\"":
        i += 1
        while i < n:
            if src[i] == "\\" and i + 1 < n:
                cur.append(src[i + 1])
                i += 2
                continue
            if src[i] == "\"":
                break
            cur.append(src[i])
            i += 1
        i += 1 if i < n else 0
        continue

    # Unquoted separators end a segment.
    if src.startswith("&&", i) or src.startswith("||", i):
        flush()
        i += 2
        continue
    if ch in ";|\n&":
        flush()
        i += 1
        continue

    cur.append(ch)
    i += 1

flush()
sys.stdout.write("\n".join(segs))
' 2>/dev/null
        _rc=$?
        printf '\001%s' "$_rc"
    )
    _rc=${_out##*$'\001'}
    _out=${_out%$'\001'*}

    # Any failure — nonzero exit, or empty output for a non-empty command —
    # falls back to the bash splitter. "Produced nothing" is not "succeeded"
    # (BACKLOG #298), and here it would silently disable safe-subset detection
    # and deny every targeted run.
    if [ "${_rc:-1}" != "0" ] || { [ -z "$_out" ] && [ -n "$_cmd" ]; }; then
        _shell_arg_segments_bash "$_cmd"
        return 0
    fi

    printf '%s' "$_out"
}

# strip_quoted_regions <command-string>
#   Echoes the command with quoted-region CONTENTS replaced by a single space.
strip_quoted_regions() {
    local _cmd="$1"

    if ! command -v python3 >/dev/null 2>&1; then
        printf '%s' "$_cmd"
        return 0
    fi

    # WHY THE OUTPUT IS CAPTURED AND CHECKED RATHER THAN PIPED STRAIGHT OUT
    # --------------------------------------------------------------------
    # The fallback below used to be `... || printf '%s' "$_cmd"`, which fires
    # only on a NONZERO exit. A python3 that exits 0 and prints nothing —
    # a wrapper, a shim, a broken venv — therefore returned the EMPTY STRING,
    # and an empty string matches no pattern, so every gate using this helper
    # silently ALLOWED. Measured session-272 with a stub: all three consuming
    # gates went from deny to allow with no error and no log line.
    #
    # For a match-to-deny gate, "produced nothing" and "found nothing dangerous"
    # are the same observable. Emptiness must therefore be treated as failure,
    # not as a result. BACKLOG #298.
    #
    # The \x01 sentinel keeps `$()` from eating trailing newlines, so the
    # returned string matches what the pipe used to emit exactly, rather than
    # merely equivalent-for-grep. It is split off again immediately below.
    local _out _rc
    _out=$(
        printf '%s' "$_cmd" | python3 -c '
import sys

src = sys.stdin.read()
out = []
i = 0
n = len(src)

# Pending heredoc delimiters found on the current logical line.
pending_heredocs = []

while i < n:
    ch = src[i]

    # --- Backslash escape (outside quotes) -----------------------------------
    if ch == "\\" and i + 1 < n:
        out.append(ch)
        out.append(src[i + 1])
        i += 2
        continue

    # --- Heredoc introducer:  <<EOF   <<-EOF   <<"EOF"   <<\x27EOF\x27 --------
    if ch == "<" and src.startswith("<<", i):
        j = i + 2
        if j < n and src[j] == "-":
            j += 1
        while j < n and src[j] in " \t":
            j += 1
        q = ""
        if j < n and src[j] in "\x27\"":
            q = src[j]
            j += 1
        start = j
        while j < n and (src[j].isalnum() or src[j] == "_"):
            j += 1
        delim = src[start:j]
        if q and j < n and src[j] == q:
            j += 1
        if delim:
            pending_heredocs.append(delim)
            out.append(" ")   # the introducer itself is not executable content
            i = j
            continue
        out.append(ch)
        i += 1
        continue

    # --- Newline: consume any heredoc bodies opened on this line --------------
    if ch == "\n":
        out.append("\n")
        i += 1
        while pending_heredocs:
            delim = pending_heredocs.pop(0)
            # Skip lines until the delimiter line (or EOF).
            while i < n:
                eol = src.find("\n", i)
                if eol == -1:
                    line = src[i:]
                    i = n
                else:
                    line = src[i:eol]
                    i = eol + 1
                if line.strip() == delim:
                    break
        continue

    # --- Single quotes: literal, no escapes ----------------------------------
    if ch == "\x27":
        i += 1
        while i < n and src[i] != "\x27":
            i += 1
        i += 1 if i < n else 0
        out.append(" ")
        continue

    # --- Double quotes: honour backslash escapes -----------------------------
    if ch == "\"":
        i += 1
        while i < n:
            if src[i] == "\\" and i + 1 < n:
                i += 2
                continue
            if src[i] == "\"":
                break
            i += 1
        i += 1 if i < n else 0
        out.append(" ")
        continue

    out.append(ch)
    i += 1

sys.stdout.write("".join(out))
' 2>/dev/null
        _rc=$?
        printf '\001%s' "$_rc"
    )
    # Split the sentinel-appended exit code back off.
    _rc=${_out##*$'\001'}
    _out=${_out%$'\001'*}

    # THREE WAYS THIS HELPER CAN FAIL, AND ALL THREE MUST LAND IN THE SAME PLACE.
    #   nonzero exit      — the original guard caught this one
    #   empty output      — BACKLOG #298; a python3 that exits 0 saying nothing
    #   truncated output  — partial write then a crash, which is WORSE than empty
    #                       because a half-stripped string looks like a result
    # Any of them means the helper did not do its job, so hand back the RAW
    # command. The gate then sees the unstripped string and behaves exactly as
    # it did before this helper existed — over-blocking, never under-blocking.
    if [ "${_rc:-1}" != "0" ] || { [ -z "$_out" ] && [ -n "$_cmd" ]; }; then
        _out="$_cmd"
    fi

    printf '%s' "$_out"
}
