#!/usr/bin/env bash
# Shared project-genesis detection helpers for the SessionStart genesis hook.
#
# REPO-CANONICAL: .claude/hooks/lib/genesis.sh. The user-level `lib/` directories
# under ~/.claude/hooks and ~/.codex/hooks are SYMLINKS to .claude/hooks/lib, so
# this file has no second copy — edit here and it is live for every project
# (BACKLOG #226). Guarded by scripts/check-installed-hooks.sh.
#
# Design: STATELESS. No stamp files. The "is this a fresh project?" signal is read
# live from the filesystem every session start (presence of governance memory
# files), so the nudge self-clears the instant the project is onboarded. Avoids
# the new-write-path / passive-trigger-calcification risk (C-109).
#
# Each helper echoes a token ("yes"/"no", or the project type) so it is directly
# unit-testable and composes in the hook via `[ "$(fn dir)" = "yes" ]`.

# is_project_dir <dir>
#   "yes" if the dir looks like a real project — a .git directory, OR at least one
#   source / project-marker / document file in the top two levels (depth 0-1,
#   skipping vendor dirs).
#   "no" for an empty/near-empty scratch dir. Errors -> "no" (fail-toward-SILENCE:
#   the opposite of the date hooks — a wrong "new project!" in a random folder is
#   the annoying case this hook minimizes; a missed nudge is cheap and recovers
#   next session).
is_project_dir() {
    python3 -c "
import os, sys
d = sys.argv[1]
SRC = {'.py','.js','.ts','.tsx','.jsx','.go','.rs','.java','.rb','.c','.cc','.cpp',
       '.h','.hpp','.cs','.php','.swift','.kt','.scala','.sh','.md','.txt','.rst',
       '.adoc','.tex'}
MARK = {'package.json','pyproject.toml','setup.py','Cargo.toml','go.mod','pom.xml',
        'build.gradle','Gemfile','requirements.txt','Makefile'}
SKIP = {'.git','node_modules','.venv','venv','__pycache__','dist','build','.mypy_cache'}
try:
    if os.path.isdir(os.path.join(d, '.git')):
        print('yes'); sys.exit(0)
    for root, dirs, files in os.walk(d):
        if root[len(d):].count(os.sep) >= 2:
            dirs[:] = []
            continue
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            if f in MARK or os.path.splitext(f)[1].lower() in SRC:
                print('yes'); sys.exit(0)
    print('no')
except Exception:
    print('no')
" "${1:-}" 2>/dev/null || echo 'no'
}

# memory_files_present <dir>
#   "yes" if governance memory exists — root (grandfathered pre-v2.62.0 layout)
#   or _ai-context/ (unified layout). This is the self-clearing signal.
memory_files_present() {
    local d="${1:-}"
    if [ -f "$d/SESSION-STATE.md" ] || [ -f "$d/_ai-context/SESSION-STATE.md" ]; then
        echo yes
    else
        echo no
    fi
}

# has_code_signal <dir>
#   "yes" if the dir carries a genuine CODE signature: a project manifest, a
#   true-code source file (prose extensions .md/.txt/.rst/.adoc/.tex deliberately
#   EXCLUDED — a research folder full of .md files is not code), or src/ + tests/
#   dirs. Depth <= 2, vendor dirs skipped, errors -> "no" (fail-toward-no).
#   Distinct from is_project_dir, which answers "is this a project at all?" and
#   correctly counts prose files.
has_code_signal() {
    python3 -c "
import os, sys
d = sys.argv[1]
CODE = {'.py','.js','.ts','.tsx','.jsx','.go','.rs','.java','.rb','.c','.cc','.cpp',
        '.h','.hpp','.cs','.php','.swift','.kt','.scala','.sh'}
MARK = {'package.json','pyproject.toml','setup.py','Cargo.toml','go.mod','pom.xml',
        'build.gradle','Gemfile','requirements.txt','Makefile'}
SKIP = {'.git','node_modules','.venv','venv','__pycache__','dist','build','.mypy_cache'}
try:
    if os.path.isdir(os.path.join(d, 'src')) or os.path.isdir(os.path.join(d, 'tests')):
        print('yes'); sys.exit(0)
    for root, dirs, files in os.walk(d):
        if root[len(d):].count(os.sep) >= 2:
            dirs[:] = []
            continue
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            if f in MARK or os.path.splitext(f)[1].lower() in CODE:
                print('yes'); sys.exit(0)
    print('no')
except Exception:
    print('no')
" "${1:-}" 2>/dev/null || echo 'no'
}

# detect_project_type <dir>
#   "code" or "document". Tailors the nudge + the scaffold_project project_type.
#   Order matters (unified layout v2.62.0 — code projects ALSO carry _ai-context/,
#   so its presence alone no longer implies document):
#     1. Root loader (AGENTS.md/CLAUDE.md) -> code. Under the unified layout the
#        loader-at-root IS the code signature; a document project's loader is
#        _ai-context/README.md, never a root AGENTS.md/CLAUDE.md.
#     2. Code signal (manifest / true-code sources / src|tests dirs) -> code.
#        Catches pre-scaffold code repos — the case the nudge exists for.
#        Prose extensions are excluded so a .md-heavy research folder cannot
#        misclassify as code (contrarian abd7249bc39fc8171).
#     3. _ai-context/ present (and no code signal) -> document.
#     4. Default -> code (greenfield default unchanged).
detect_project_type() {
    local d="${1:-}"
    if [ -f "$d/AGENTS.md" ] || [ -f "$d/CLAUDE.md" ]; then
        echo code
    elif [ "$(has_code_signal "$d")" = "yes" ]; then
        echo code
    elif [ -d "$d/_ai-context" ]; then
        echo document
    else
        echo code
    fi
}

# is_dismissed <dir>
#   "yes" if the user opted out — a `.start-project-dismissed` marker in the dir
#   (durable, gitignore-able) OR START_PROJECT_NUDGE_DISMISS=1 in the env.
is_dismissed() {
    local d="${1:-}"
    if [ "${START_PROJECT_NUDGE_DISMISS:-}" = "1" ] || [ -f "$d/.start-project-dismissed" ]; then
        echo yes
    else
        echo no
    fi
}
