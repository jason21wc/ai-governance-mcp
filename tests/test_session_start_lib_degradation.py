"""The SessionStart hooks' "Exit 0 always" contract (BACKLOG #236).

Both global SessionStart hooks state `Exit 0 always — never blocks startup` in
their own headers, and both broke it. Each guarded exactly one library
(`repo-root.sh`) with a careful validated load and a graceful fallback, while
sourcing the other two bare directly above it. Under `set -euo pipefail` a
missing file in a bare `source` exits 1 — before the careful guard ever runs, so
the guard's failure path was unreachable in the case that actually matters.
Measured before the fix: exit 1 from a lib-less copy of either hook.

WHY THIS IS NOT AN EXOTIC EDGE CASE. `lib/` is a single symlink into this
checkout (BACKLOG #226), so moving or renaming the repo removes every library at
once, for all three global hooks, in every project they run in. The
all-libs-missing state is the ordinary consequence of moving a directory.

The hook list is DERIVED from the directory, never hardcoded. The fix is ONE shared
`load_lib` mechanism, so a per-hook test would let a future hook reintroduce the
bare `source` without anything noticing — the same "guard one member, not the
class" mistake that produced the defect.

NOTE ON SCOPE: whether a nonzero SessionStart hook actually blocks startup on
this host is NOT established here (unlike UserPromptSubmit exit 2, which does).
The contract is the hooks' own stated one; these tests hold them to it rather
than to an assumption about the host.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOKS = REPO / ".claude" / "hooks"
LIB = HOOKS / "lib"

PAYLOAD = '{"source":"startup","cwd":"/tmp"}'

# A bare `source` of a lib, in every spelling. The first version of this guard
# matched only `source "$HOOK_DIR/lib/..."`, which misses the POSIX dot form and
# the braced `${HOOK_DIR}` — and `session-start-hygiene.sh` already used the dot
# form, so the "structural" assertion was evaded in-repo on the day it shipped.
BARE_SOURCE = re.compile(
    r"""^\s*(?:source|\.)\s+["']?\$\{?HOOK_DIR\}?/lib/""", re.MULTILINE
)

# Libs a hook actually LOADS. Read from the `load_lib` loop and from any direct
# source lines — not from prose. The first attempt at this matched `lib/<name>.sh`
# anywhere in the file, which picked up comment text and missed hooks whose loader
# loop names libs without the `lib/` prefix. Deriving from the wrong token is its
# own version of hardcoding.
LOADER_LOOP = re.compile(r"""for\s+_lib\s+in\s+([^\n;]+?)\s*;\s*do""")
DIRECT_SOURCE = re.compile(
    r"""^\s*(?:source|\.)\s+["']?\$\{?HOOK_DIR\}?/lib/([A-Za-z0-9_-]+\.sh)""",
    re.MULTILINE,
)

# `set -e` is the causal condition. Without it, a failing `source` does not kill
# the hook, so a guarded direct source is equally safe — `session-start-hygiene.sh`
# uses exactly that shape deliberately. Testing the spelling instead of the cause
# would flag a correct hook and train a bypass.
USES_ERREXIT = re.compile(r"""^\s*set\s+-[a-z]*e[a-z]*(\s|$)""", re.MULTILINE)

# Each hook names its own debug variable; derive it rather than mapping names.
DEBUG_VAR = re.compile(r"""\$\{([A-Z][A-Z0-9_]*_DEBUG):-""")


def discover_session_start_hooks():
    """Every SessionStart hook that loads libraries — DERIVED, not listed.

    The first version of this file hardcoded a two-entry dict and its docstring
    claimed the tests were "parametrized over both hooks deliberately... so a
    future hook cannot reintroduce the bare source without anything noticing."
    That claim was false: a hand-maintained dict IS the per-hook test it warned
    about, and a third hook carrying the identical defect
    (`session-start-cadence.sh`) was sitting in the same directory, unlisted and
    unfixed, while the suite stayed green.

    Deriving from the filesystem is the whole point — a hook added tomorrow is
    covered the moment it exists. This mirrors the rule
    `scripts/check-installed-hooks.sh` states in its own header: the authority is
    reality, not a list maintained by hand.
    """
    hooks = {}
    for path in sorted(HOOKS.glob("session-start-*.sh")):
        text = path.read_text()
        libs = []
        for match in LOADER_LOOP.findall(text):
            libs.extend(match.split())
        libs.extend(DIRECT_SOURCE.findall(text))
        libs = [lib for i, lib in enumerate(libs) if lib not in libs[:i]]
        hooks[path.name] = [lib for lib in libs if (LIB / lib).exists()]
    return hooks


HOOK_LIBS = discover_session_start_hooks()


def run_copy(hook_dir, hook_name):
    return subprocess.run(
        ["bash", str(hook_dir / hook_name)],
        input=PAYLOAD,
        capture_output=True,
        text=True,
        timeout=30,
    )


def stage(tmp_path, hook_name, libs):
    """Copy the hook plus the named libs into a scratch dir.

    Never mutate the real tree: `~/.claude/hooks` and `~/.codex/hooks` are
    symlinks into this checkout, so editing a hook here changes live behaviour
    for every project on this machine.
    """
    hook_dir = tmp_path / "hooks"
    (hook_dir / "lib").mkdir(parents=True)
    shutil.copy(HOOKS / hook_name, hook_dir / hook_name)
    for lib in libs:
        shutil.copy(LIB / lib, hook_dir / "lib" / lib)
    return hook_dir


@pytest.mark.parametrize("hook_name", sorted(HOOK_LIBS))
def test_no_libs_at_all_exits_zero(tmp_path, hook_name):
    """The moved-checkout case: `lib/` is one symlink, so all libs vanish."""
    hook_dir = stage(tmp_path, hook_name, [])
    r = run_copy(hook_dir, hook_name)
    assert r.returncode == 0, f"stderr={r.stderr}"


@pytest.mark.parametrize("hook_name,libs", sorted(HOOK_LIBS.items()))
def test_each_missing_lib_individually_exits_zero(tmp_path, hook_name, libs):
    """Every library, one at a time — not just the one that was guarded.

    Guarding a single member of the class is the defect; this asserts the class.
    """
    for omitted in libs:
        present = [lib for lib in libs if lib != omitted]
        hook_dir = stage(tmp_path / omitted.replace(".", "_"), hook_name, present)
        r = run_copy(hook_dir, hook_name)
        assert r.returncode == 0, f"missing {omitted}: stderr={r.stderr}"


@pytest.mark.parametrize("hook_name,libs", sorted(HOOK_LIBS.items()))
def test_each_truncated_lib_exits_zero(tmp_path, hook_name, libs):
    """Presence is not enough — a truncated lib parses partially.

    Appending an unterminated block is a cheap, deterministic way to make the
    file syntactically invalid without depending on where a real truncation
    would land.
    """
    for broken in libs:
        hook_dir = stage(tmp_path / ("t_" + broken.replace(".", "_")), hook_name, libs)
        with open(hook_dir / "lib" / broken, "a") as fh:
            fh.write("\nif [ 1 = 1 ]; then\n")
        r = run_copy(hook_dir, hook_name)
        assert r.returncode == 0, f"truncated {broken}: stderr={r.stderr}"


@pytest.mark.parametrize("hook_name,libs", sorted(HOOK_LIBS.items()))
def test_healthy_load_still_runs_the_hook(tmp_path, hook_name, libs):
    """A degradation fix must not silently disable the feature.

    Exit 0 is what a fully-degraded hook returns too, so exit code alone cannot
    distinguish "working" from "quietly dead". With every lib present the hook
    must reach its own logic, which the debug channel proves.
    """
    debug_vars = DEBUG_VAR.findall((HOOKS / hook_name).read_text())
    if not debug_vars:
        pytest.skip(f"{hook_name} exposes no *_DEBUG channel to observe")
    hook_dir = stage(tmp_path, hook_name, libs)
    env_var = debug_vars[0]
    r = subprocess.run(
        ["bash", str(hook_dir / hook_name)],
        input=PAYLOAD,
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", env_var: "true"},
    )
    assert r.returncode == 0
    assert "session root=" in r.stderr, (
        f"hook exited 0 without reaching its own logic — degraded, not working. "
        f"stderr={r.stderr}"
    )


@pytest.mark.parametrize("hook_name", sorted(HOOK_LIBS))
def test_no_bare_source_remains(hook_name):
    """Structural: the next hook must not reintroduce the bare `source`.

    The defect was not a missing check, it was a check applied per-library. This
    asserts the shape rather than the symptom, so a future edit that sources a
    lib directly fails here even if every runtime path above still passes.

    Matches the dot form and `${HOOK_DIR}` too — the first version matched only
    `source "$HOOK_DIR/lib/`, and a hook in this very directory already used the
    dot form, so the guard was evadable by the two most ordinary spellings.

    Scoped to hooks using `set -e`, which is the causal condition: without it a
    failing source does not kill the hook, so a presence-guarded direct source is
    equally safe. `session-start-hygiene.sh` uses that shape on purpose. Asserting
    the spelling rather than the cause would flag a correct hook, and a guard with
    a known false positive trains its own bypass.
    """
    text = (HOOKS / hook_name).read_text()
    if not USES_ERREXIT.search(text):
        pytest.skip(
            f"{hook_name} does not use `set -e`; a failing source is survivable"
        )
    offenders = BARE_SOURCE.findall(text)
    assert offenders == [], (
        f"bare lib source in {hook_name} — load every lib through the guarded "
        f"loader so a missing lib degrades instead of exiting non-zero: {offenders}"
    )


def test_the_hook_list_is_derived_not_hardcoded():
    """The guard against this file repeating the defect it tests for.

    If discovery silently returned nothing, every parametrized test above would
    vanish and the suite would go green with zero coverage — the exact
    failure shape (`could not run` reported as a pass) this session spent four
    fixes on. Assert discovery found the hooks that actually exist.
    """
    on_disk = {p.name for p in HOOKS.glob("session-start-*.sh")}
    assert on_disk, "no session-start hooks found — discovery is broken"

    # NOT `set(HOOK_LIBS) == on_disk`. That was the first version and it was a
    # TAUTOLOGY: discovery is built from this same glob and assigns an entry for
    # every match, so the two sets are equal by construction. It is the identical
    # shape as the `sorted(x, key=x.index)` check deleted from
    # test_journal_reminder_hook.py earlier in this session — written, in the very
    # test named "derived not hardcoded", by the author who had just deleted the
    # other one. Caught by a fresh-context sweep, not by re-reading.
    #
    # The check has to come from an INDEPENDENT signal. A raw grep for lib
    # references is a different derivation path than the loader-loop parser, so
    # disagreement between them is real information: if a hook names lib files but
    # discovery found none, the parser broke.
    for name in sorted(on_disk):
        text = (HOOKS / name).read_text()
        mentioned = {
            lib
            for lib in re.findall(r"lib/([A-Za-z0-9_-]+\.sh)", text)
            if (LIB / lib).exists()
        }
        if not mentioned:
            continue
        assert HOOK_LIBS.get(name), (
            f"{name} references {sorted(mentioned)} but discovery found no libs "
            "for it — the loader-loop parser is out of step with the hook"
        )
