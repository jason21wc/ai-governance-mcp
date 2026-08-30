"""What do the safety gates decide when their own tools are broken?

WHY THIS FILE EXISTS
--------------------
Every gate in `.claude/hooks/` is tested against inputs. None was tested against
a degraded ENVIRONMENT — a missing `jq`, a `python3` that exits 0 printing
nothing, an unset `$HOME`, a `lib/` file that did not get copied. That gap is
not incidental. It is the reason BACKLOG #298 existed for months without being
visible: the fail-safe guarantee was written in a comment, believed, and
exercised only on the path that already worked.

THE CONTRACT THIS FILE ENCODES (verified, not assumed)
------------------------------------------------------
For a Claude Code PreToolUse hook, DENY is a POSITIVE ASSERTION — exit 2, or
exit 0 with JSON carrying `hookSpecificOutput.permissionDecision = "deny"`.
Confirmed against the published hooks reference and the installed CLI 2.1.220.
**Everything else is ALLOWED**: exit 1, exit 127, a failed `source`, an unbound
variable under `set -u`, a timeout, malformed JSON. There is no harness-level
fail-closed setting.

Bash's entire failure vocabulary — abort on `set -e`, abort on `set -u`, a
missing binary, a dead subprocess — produces exactly that "everything else".
So these hooks are written in a language whose every failure mode is a synonym
for "allow", and each gate must construct fail-closed behaviour for itself.

TWO PROPERTIES, AND THE SECOND IS NOT OPTIONAL
----------------------------------------------
1. A degraded environment must not turn a DENY into an ALLOW.
2. A degraded environment must not turn an ALLOW into a DENY either. A gate that
   blocks everything when a tool is missing does not fail safe — it bricks the
   session, and the only escape is a bypass env var that in this repo also
   disables the secret scanner. Both directions are asserted below.

SCOPE, STATED PLAINLY. This file pins `strip_quoted_regions` (the BACKLOG #298
fix), the observable decision of the gates that consume it, and — in
`TestEveryDegradationAgainstEveryGate` at the bottom — a real GATES × DEGRADATIONS
cross-product over the three Bash gates, both directions.

That cross-product replaced two hand-written lists, and the replacement was not
tidying. An independent audit found the two worst holes in this repo's safety
layer living exactly where those lists did not overlap: a broken `grep` was
never probed against the push gate, and `jq` was never probed against any gate
but the push gate. Both were live full bypasses. A list records what someone
thought of; a cross-product forces the cells.

CROSS-PLATFORM, and this was measured rather than assumed. An earlier version of
this docstring said the `grep` vs `[[ =~ ]]` equivalence relied on by the builtin
fallbacks was unverified against GNU grep + glibc. It has since been checked in a
Linux container (GNU bash 5.2.37, GNU grep 3.11, glibc): all 8 patterns actually
routed through `_match_regex` compared against 15 haystacks including multiline
ones — 120 comparisons, ZERO divergences. The three Bash gates were also run
directly there and returned identical verdicts to macOS in both directions. CI
runs `ubuntu-latest`, so this is the platform that matters and it now agrees.

STILL NOT COVERED, so nobody reads the above as more than it is: the governance
gate and the exit-plan gate are exercised by the earlier per-axis classes but are
not in the cross-product (their payloads are not Bash-shaped). Locale
degradation, a read-only `HOME`, concurrent invocation, `sed` degradation, and
disk-full on the deny logs are untested.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.hook_fixtures import (
    STUB_BROKEN,
    STUB_SILENT,
    daemon_home,
    gate_tree,
    run_gate,
    stub_tool,
)

REPO = Path(__file__).resolve().parent.parent
HOOKS = REPO / ".claude" / "hooks"
LIB = HOOKS / "lib" / "shell-scan.sh"

# A command that MUST be denied by the OOM gate, and one that must not be.
MUST_DENY_PYTEST = "pytest tests/"
MUST_ALLOW = "ls -la"


def _stub_dir(tmp_path: Path, name: str, script: str) -> Path:
    """A PATH directory whose `name` behaves as `script` says."""
    d = tmp_path / f"stub-{name}"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text(script)
    p.chmod(0o755)
    return d


def _strip(command: str, *, path_prefix: Path | None = None) -> tuple[str, int]:
    """Call the real bash helper. Returns (stdout, returncode)."""
    env = {**os.environ}
    if path_prefix is not None:
        env["PATH"] = f"{path_prefix}:{env['PATH']}"
    r = subprocess.run(
        ["bash", "-c", f'source "{LIB}"; strip_quoted_regions "$1"', "_", command],
        capture_output=True,
        text=True,
        env=env,
        timeout=20,
    )
    return r.stdout, r.returncode


class TestStripperNeverReturnsNothing:
    """BACKLOG #298. Emptiness is a failure, not a result.

    For a match-to-deny gate, "produced nothing" and "found nothing dangerous"
    are the same observable — so a preprocessing step that can return empty can
    silently disable every gate downstream of it.
    """

    def test_healthy_python3_strips_normally(self):
        out, rc = _strip('git push --force "origin" main')
        assert rc == 0
        assert "--force" in out, "control: the real stripper must still work"

    def test_python3_exiting_zero_with_no_output_falls_back_to_raw(self, tmp_path):
        """THE #298 CASE. Watched failing before the fix; pinned here after."""
        stub = _stub_dir(tmp_path, "python3", "#!/bin/sh\nexit 0\n")
        out, rc = _strip("git push --force origin main", path_prefix=stub)
        assert out != "", "empty output must never be returned as a result"
        assert out == "git push --force origin main", (
            "a silent python3 must degrade to the RAW command, so the gate "
            "over-blocks rather than going blind"
        )

    def test_python3_exiting_nonzero_falls_back_to_raw(self, tmp_path):
        stub = _stub_dir(tmp_path, "python3", "#!/bin/sh\nexit 3\n")
        out, _ = _strip("git push --force origin main", path_prefix=stub)
        assert out == "git push --force origin main"

    def test_python3_printing_partial_output_then_failing_falls_back(self, tmp_path):
        stub = _stub_dir(tmp_path, "python3", "#!/bin/sh\nprintf 'PARTIAL'\nexit 3\n")
        out, _ = _strip("git push --force origin main", path_prefix=stub)
        assert "PARTIAL" not in out or out == "git push --force origin main", (
            "a truncated strip must not be handed to a matcher as if complete"
        )

    def test_missing_python3_falls_back_to_raw(self, tmp_path):
        """PATH with no python3 at all — the pre-existing guarded path."""
        env_dir = tmp_path / "empty-path"
        env_dir.mkdir()
        for tool in ("bash", "sh"):
            src = shutil.which(tool)
            if src:
                (env_dir / tool).symlink_to(src)
        r = subprocess.run(
            [
                "bash",
                "-c",
                f'source "{LIB}"; strip_quoted_regions "$1"',
                "_",
                "cmd --force",
            ],
            capture_output=True,
            text=True,
            env={"PATH": str(env_dir), "HOME": str(tmp_path)},
            timeout=20,
        )
        assert r.stdout == "cmd --force"

    def test_empty_input_still_yields_empty_output(self):
        """The fallback must not manufacture content from nothing."""
        out, _ = _strip("")
        assert out == ""

    def test_trailing_newlines_survive(self):
        """The fix captures via $(), which eats trailing newlines unless guarded.

        Not cosmetic: it means the returned value is byte-identical to what the
        old pipe emitted, so no consumer's matching can shift as a side effect
        of a fail-safe change.
        """
        out, _ = _strip("echo hi\n\n")
        assert out.endswith("\n\n"), f"trailing newlines lost: {out!r}"


class TestDegradedEnvironmentDoesNotOpenTheOomGate:
    """The observable that actually matters: the gate's DECISION.

    Testing the helper proves the helper. These tests prove the gate, which is
    the thing a stale `python3` would really have disabled.
    """

    HOOK = HOOKS / "pre-test-oom-gate.sh"

    def _decide(self, command: str, tmp_path: Path, path_prefix: Path | None = None):
        env = {**os.environ, "HOME": str(daemon_home(tmp_path))}
        # Same scrub as run_gate, and for the same reason: an inherited
        # PYTEST_ALLOW_HEAVY makes this class's must-deny assertions fail and its
        # must-allow assertions vacuously true. Measured — the documented heavy-run
        # invocation produced failures a clean run did not have.
        for _bypass in ("PYTEST_ALLOW_HEAVY", "PYTEST_SKIP_OOM_GATE"):
            env.pop(_bypass, None)
        if path_prefix is not None:
            env["PATH"] = f"{path_prefix}:{env['PATH']}"
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
        r = subprocess.run(
            ["bash", str(self.HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        denied = r.returncode == 2 or '"permissionDecision": "deny"' in r.stdout
        return denied, r.returncode

    def test_baseline_denies(self, tmp_path):
        denied, _ = self._decide(MUST_DENY_PYTEST, tmp_path)
        assert denied, "precondition: a bare full-suite pytest must be denied"

    def test_baseline_allows_a_benign_command(self, tmp_path):
        denied, _ = self._decide(MUST_ALLOW, tmp_path)
        assert not denied, "precondition: an ordinary command must be allowed"

    def test_silent_python3_does_not_open_the_gate(self, tmp_path):
        """Before #298 this flipped the gate from deny to allow.

        A stub that returns empty for the STRIPPER while leaving the rest of the
        hook working is not constructible with a whole-python3 stub — the hook
        needs python3 for other steps too. So this asserts the weaker but still
        decisive property: whatever else breaks, the answer is never ALLOW.
        """
        stub = _stub_dir(tmp_path, "python3", "#!/bin/sh\nexit 0\n")
        denied, rc = self._decide(MUST_DENY_PYTEST, tmp_path, stub)
        assert denied, (
            f"a python3 that succeeds silently turned a DENY into an ALLOW "
            f"(rc={rc}) — this is BACKLOG #298 and it must never regress"
        )

    def test_a_degraded_environment_does_not_brick_benign_commands(self, tmp_path):
        """The other direction, and it is not optional.

        A gate that denies everything when a tool is missing does not fail safe.
        It forces the bypass env var, which in this repo also disables the
        secret scanner — a bypass used routinely is a bypass.
        """
        stub = _stub_dir(tmp_path, "python3", "#!/bin/sh\nexit 0\n")
        denied, rc = self._decide(MUST_ALLOW, tmp_path, stub)
        assert not denied, (
            f"a benign command was blocked by a degraded environment (rc={rc}); "
            "failing closed on everything is a different bug, not a fix"
        )


# ---------------------------------------------------------------------------
# The matrix (BACKLOG #299 Stage A) — five gates × the measured degradations
# ---------------------------------------------------------------------------
# Every case below was RED before the Stage A fixes. Each must-deny case has a
# must-allow partner, because a gate that denies everything when a tool is
# missing has not failed safe — it has bricked the session, and the only escape
# is a bypass flag that in this repo also disables the secret scanner.

GATES = [
    "pre-tool-content-security.sh",
    "pre-test-oom-gate.sh",
    "pre-push-quality-gate.sh",
    "pre-tool-governance-check.sh",
    "pre-exit-plan-mode-gate.sh",
]

# PER-GATE PROBES, and the reason this is not one shared constant.
#
# The first version of this file used a single `BENIGN = "ls -la"` everywhere.
# An adversarial pass measured that `ls -la` and `git status` are BOTH on the
# governance gate's read-only allowlist, so those parametrizations exited at
# line 181 without reaching any of the logic under test — and the push gate
# exits at its push-detector before touching `$HOME`. Two of five cases proved
# nothing while reading as coverage. One constant cannot be non-trivial for five
# gates with five different early-exit paths.
#
# `deny` is a command the gate MUST refuse; `allow` is one it must not. Both are
# chosen to survive that gate's short-circuits.
CRED = "cat " + chr(126) + "/.ssh/id_rsa"  # built to keep it off any command line
GATE_PROBES = {
    "pre-tool-content-security.sh": {"deny": CRED, "allow": "echo hi"},
    "pre-test-oom-gate.sh": {"deny": "pytest tests/", "allow": "echo hi"},
    "pre-push-quality-gate.sh": {
        "deny": "git push --force origin main",
        "allow": "echo hi",
    },
    # The governance gate needs a transcript with no governance calls, and a
    # command that is NOT on its read-only allowlist. `echo hi` clears both.
    "pre-tool-governance-check.sh": {"deny": "echo hi", "allow": None},
    # Matcher is ExitPlanMode; it never receives a Bash payload. Driven by
    # `_exit_plan_payload` below rather than a command string.
    "pre-exit-plan-mode-gate.sh": {"deny": None, "allow": None},
}

BENIGN = "echo hi"  # the one command that reaches real logic in every Bash gate


def _no_governance_transcript(tmp_path):
    """A transcript with no evaluate_governance / query_project calls."""
    p = Path(tmp_path) / "t.jsonl"
    p.write_text(
        json.dumps({"message": {"role": "user", "content": "do a thing"}}) + "\n"
    )
    return str(p)


class TestUnsetHomeDoesNotDisableAGate:
    """`HOME` unset → unbound variable under `set -u` → rc 1 → ALLOW.

    Measured on three of five gates. `trap 'exit 2' ERR` does NOT fire on an
    unbound-variable abort, so the gates carrying it are not protected either.

    The root cause is worth stating: `HOME` is needed only for a DENY LOG, and a
    logging path leaked into the decision path. So the assertion is `rc != 1`,
    not `denied` — a gate is free to allow a benign command; it is not free to
    die before deciding.
    """

    @pytest.mark.parametrize("hook_name", GATES)
    def test_unset_home_does_not_abort_the_gate(self, hook_name):
        """The FLOOR. Necessary, and measured NOT sufficient — see below."""
        _, rc, _ = run_gate(HOOKS / hook_name, BENIGN, env={"HOME": None})
        assert rc != 1, (
            f"{hook_name} aborted (rc=1) with HOME unset — the harness reads "
            "that as ALLOW, so the gate is silently off"
        )

    @pytest.mark.parametrize(
        "hook_name", [g for g, p in GATE_PROBES.items() if p["deny"] and "gov" not in g]
    )
    def test_unset_home_preserves_the_deny(self, hook_name):
        """THE ASSERTION THAT ACTUALLY MATTERS.

        `rc != 1` above is blind to a gate that exits 0 having silently decided
        nothing — which is not hypothetical: the governance gate does exactly
        that (next test). A fix as lazy as `[ -z "${HOME:-}" ] && exit 0` greens
        every `rc != 1` case with the gate switched off. Only a preserved
        DECISION proves the gate still works.
        """
        if "oom" in hook_name:
            # DOCUMENTED EXCLUSION, and the reason is a property of the gate.
            #
            # The OOM gate does not deny because of the COMMAND; it denies
            # because the command is dangerous on a LOADED machine. Its two risk
            # signals are a watcher-daemon heartbeat (read from `$HOME`) and
            # ps-detectable torch processes. With HOME unset the first is
            # unreadable BY CONSTRUCTION, and the second cannot be created
            # portably by a test. So "still denies with HOME unset" is not a
            # property this gate can have on a quiet machine — asserting it tests
            # whether the developer's laptop happens to be busy.
            #
            # That is not hypothetical: this assertion passed for weeks on a Mac
            # running 13 torch-holding MCP processes and failed the first time it
            # ran on a clean CI runner. The luck also masked a real fail-open in
            # the gate's heartbeat parsing for five review rounds.
            #
            # The property that IS meaningful here — the gate does not ABORT with
            # HOME unset, which was the actual #299 defect — is asserted for all
            # five gates by `test_unset_home_does_not_abort_the_gate` above.
            # Deny-preservation under degradation is covered for this gate, with
            # the precondition properly established, by the missing-lib, silent-
            # emitter and GATES × DEGRADATIONS tests.
            pytest.skip(
                "OOM gate's deny needs a risk signal that HOME-unset removes by "
                "construction; abort-freedom is asserted separately"
            )
        denied, rc, _ = run_gate(
            HOOKS / hook_name, GATE_PROBES[hook_name]["deny"], env={"HOME": None}
        )
        assert denied, f"{hook_name} lost its deny with HOME unset (rc={rc})"

    def test_unset_home_degrades_the_governance_gate_LOUDLY_not_silently(
        self, tmp_path
    ):
        """This test asserted the wrong thing at first — corrected, and why.

        `pre-tool-governance-check.sh:248` probes `${HOME:-}/.claude.json`. With
        HOME unset that is `/.claude.json`, which does not exist, so
        `mcp_configured` returns false and both gates auto-degrade to soft. The
        first version of this test called that a deny→allow regression and
        demanded a deny.

        That was wrong, and checking the gate settled it. The auto-degrade is
        DELIBERATE and documented: a session that cannot call the gated MCP
        tools cannot satisfy a fail-closed gate, so denying would deadlock a
        cloud clone or a fresh checkout with no escape the model can reach.
        LEARNING-LOG 2026-06-10 prescribes exactly this — where a legitimate
        context structurally cannot satisfy a gate, degrade LOUDLY, do not block.

        So the property worth pinning is the LOUDNESS, not a deny. Measured: the
        gate emits `additionalContext` telling the model governance was not
        detected and must be called. It is not silent, and this asserts that.

        KNOWN RESIDUAL, recorded rather than asserted: with HOME unset the
        `audit_bypass` line recording the auto-degrade cannot be written, so the
        degrade happens loudly to the MODEL and invisibly to the AUDIT TRAIL.
        That is a real gap and it belongs to the allow-path work (Stage B), not
        here.
        """
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
            "transcript_path": _no_governance_transcript(tmp_path),
        }
        denied, rc, out = run_gate(
            HOOKS / "pre-tool-governance-check.sh",
            "",
            env={"HOME": None, "MCP_DETECT_SKIP": None},
            payload=payload,
        )
        assert rc != 1, f"the gate aborted rather than degrading (rc={rc})"
        assert not denied, (
            "a deny here would deadlock any context that cannot reach the MCP "
            "server — the documented reason this degrade exists"
        )
        assert "GOVERNANCE NOT DETECTED" in out or "additionalContext" in out, (
            "the degrade was SILENT — a degrade the model cannot see is "
            "indistinguishable from a gate that never ran"
        )

    def test_empty_home_is_a_distinct_condition_from_unset(self):
        """HOME="" does not trip `set -u`, and is a live false positive today.

        `pre-tool-content-security.sh:79` is unguarded, so an empty HOME yields
        an empty `HOME_ESCAPED` and the pattern `${HOME_ESCAPED}/.npmrc` becomes
        the bare substring `/.npmrc` — denying any absolute path containing it.
        Unset and empty are two conditions, not one, and the file must say which.
        """
        denied, rc, _ = run_gate(
            HOOKS / "pre-tool-content-security.sh",
            "cat /srv/app/.npmrc",
            env={"HOME": ""},
        )
        assert not denied, (
            f"an unrelated path was denied with HOME empty (rc={rc}) — the "
            "empty-pattern false positive"
        )

    def test_unset_home_still_denies_a_credential_read(self):
        denied, rc, _ = run_gate(
            HOOKS / "pre-tool-content-security.sh",
            "cat ~/.ssh/id_rsa",
            env={"HOME": None},
        )
        assert denied, f"credential read ALLOWED with HOME unset (rc={rc})"

    def test_unset_home_does_not_deny_an_unrelated_path(self):
        """The anti-false-positive pin for the `${HOME:-}` trap.

        A bare `${HOME:-}` empties `HOME_ESCAPED`, turning the pattern
        `${HOME_ESCAPED}/.npmrc` into the bare substring `/.npmrc` — which then
        denies any absolute path containing it. Measured. That is why the fix is
        an explicit deny-on-empty-HOME rather than a default-value guard.
        """
        denied, rc, _ = run_gate(
            HOOKS / "pre-tool-content-security.sh",
            "cat /srv/app/.npmrc",
            env={"HOME": None},
        )
        assert not denied, (
            f"an unrelated path was denied with HOME unset (rc={rc}) — the "
            "empty-pattern false-positive class was introduced"
        )


class TestABrokenGrepDoesNotBlindTheMatcher:
    """`grep` IS the matcher in two gates, and a broken one is a total bypass.

    Both gates call `grep` inside an `if` condition, so exit 127 reads as
    "condition false" = "found nothing dangerous". No ERR trap fires, nothing is
    printed, the hook exits 0. Measured: a credential read and a bare full-suite
    pytest both ALLOWED with `grep` stubbed to 127.

    This is a cleaner instance of the #298 class than #298 itself — "the matcher
    could not run" and "the matcher found nothing" are the same observable — and
    the first version of this file did not probe it at all, stubbing only
    `python3` and `jq`. It is ranked first among the misses for that reason.
    """

    @staticmethod
    def _daemon_home(tmp_path):
        """A HOME with a FRESH watcher heartbeat.

        The OOM gate's deny is conditional on machine state, not on the command
        alone: `pytest tests/` is only dangerous when the daemon is holding
        torch. Without this the autouse `isolate_home` fixture gives an empty
        HOME, the gate correctly finds no risk, and it ALLOWS — so a test that
        omitted this was asserting a deny the gate had no reason to make. That
        is the probe-never-reaches-the-surface defect one level up: the
        environment, not the input, was the missing precondition.
        """
        import json as _json
        from datetime import datetime, timedelta, timezone

        home = tmp_path / "daemon_home"
        (home / ".context-engine").mkdir(parents=True, exist_ok=True)
        alive = datetime.now(timezone.utc) - timedelta(seconds=30)
        (home / ".context-engine" / "watcher-heartbeat.json").write_text(
            _json.dumps({"pid": 99999, "alive_at": alive.isoformat()})
        )
        return str(home)

    @pytest.mark.parametrize(
        "hook_name",
        ["pre-tool-content-security.sh", "pre-test-oom-gate.sh"],
    )
    @pytest.mark.parametrize("body", [STUB_BROKEN, STUB_SILENT], ids=["127", "silent"])
    def test_a_broken_grep_does_not_lose_the_deny(self, hook_name, body, tmp_path):
        stub = stub_tool(tmp_path, "grep", body)
        env = {"HOME": self._daemon_home(tmp_path)} if "oom" in hook_name else None
        denied, rc, _ = run_gate(
            HOOKS / hook_name,
            GATE_PROBES[hook_name]["deny"],
            path_prefix=stub,
            env=env,
        )
        assert denied, (
            f"{hook_name} ALLOWED its must-deny command with grep degraded "
            f"(rc={rc}) — the matcher cannot run, so the gate is blind"
        )

    @pytest.mark.parametrize(
        "hook_name",
        ["pre-tool-content-security.sh", "pre-test-oom-gate.sh"],
    )
    def test_a_broken_grep_does_not_brick_ordinary_work(self, hook_name, tmp_path):
        stub = stub_tool(tmp_path, "grep", STUB_BROKEN)
        denied, rc, _ = run_gate(
            HOOKS / hook_name, GATE_PROBES[hook_name]["allow"], path_prefix=stub
        )
        assert not denied, (
            f"{hook_name} denied ordinary work with grep degraded (rc={rc})"
        )


class TestPushGateSurvivesADeadToolchain:
    """The push gate has THREE independent full-bypass conditions.

    Measured: with `jq` OR `python3` degraded, `git push --force origin main`
    returns rc=0 with 0 bytes — an ALLOW. That is the force-push block AND the
    diff secret scanner, both off.

    The trap worth naming: the git-push DETECTOR is itself python3, so "add a
    python3 fallback to the jq parse" fixes nothing for a broken python3. A
    contrarian caught that before it shipped.
    """

    HOOK = HOOKS / "pre-push-quality-gate.sh"
    FORCE_PUSH = "git push --force origin main"

    @pytest.mark.parametrize(
        "tool,body",
        [
            ("jq", STUB_BROKEN),
            ("jq", STUB_SILENT),
            ("python3", STUB_BROKEN),
            ("python3", STUB_SILENT),
        ],
        ids=["jq-127", "jq-silent", "python3-127", "python3-silent"],
    )
    def test_force_push_is_not_allowed_by_a_dead_tool(self, tool, body, tmp_path):
        stub = stub_tool(tmp_path, tool, body)
        denied, rc, out = run_gate(self.HOOK, self.FORCE_PUSH, path_prefix=stub)
        assert denied, (
            f"force-push ALLOWED with {tool} degraded (rc={rc}, {len(out)} bytes)"
            " — the force-push block and the diff secret scanner are both off"
        )

    @pytest.mark.parametrize(
        "tool,body",
        [("jq", STUB_BROKEN), ("python3", STUB_BROKEN), ("python3", STUB_SILENT)],
        ids=["jq-127", "python3-127", "python3-silent"],
    )
    # THE ANTI-BRICK SET, widened deliberately. `ls -la` / `echo hi` /
    # `git status` were too thin: an adversarial pass built the obvious lazy fix
    # ("toolchain degraded -> deny anything matching /push/"), and it greened
    # every force-push case while denying `git commit -m "fix the push gate"` —
    # resurrecting the exact T-143 false-positive class this repo already paid
    # to close. These commands are the ones that catch that fix.
    @pytest.mark.parametrize(
        "command",
        [
            "echo hi",
            "ls -la",
            'git commit -m "fix the push gate"',
            'git commit -m "use -f to force"',
            'echo "do not push yet"',
            "grep -rn push .claude/hooks",
            "make push",
            "npm run push-docs",
            "git log --oneline -5",
            "python3 -c 'print(1)'",
        ],
    )
    def test_ordinary_commands_are_untouched_by_a_dead_tool(
        self, tool, body, command, tmp_path
    ):
        """THE ANTI-BRICK PIN. This gate matches every Bash call, so a
        degraded-mode deny not narrowly scoped to real pushes stops all work.
        """
        stub = stub_tool(tmp_path, tool, body)
        denied, rc, _ = run_gate(self.HOOK, command, path_prefix=stub)
        assert not denied, (
            f"'{command}' was DENIED with {tool} degraded (rc={rc}) — a degraded"
            " push gate must not block ordinary commands"
        )


class TestAMissingLibDoesNotDisableAGate:
    """A missing `lib/*.sh` → failed `source` → rc 1 → ALLOW.

    `trap ... ERR` does not cover a failed `source` (measured, bash 3.2), and in
    several gates the source sits ABOVE the trap anyway. `lib/` is a single
    symlink into this checkout, so moving the repo removes every library at
    once — the ordinary consequence of moving a directory, not an exotic case.
    """

    @pytest.mark.parametrize("hook_name", GATES)
    @pytest.mark.parametrize("lib", ["audit-bypass.sh", "shell-scan.sh"])
    def test_missing_lib_does_not_abort_the_gate(self, hook_name, lib, tmp_path):
        hook = gate_tree(tmp_path / lib.replace(".", "_"), hook_name, drop_libs=(lib,))
        _, rc, _ = run_gate(hook, BENIGN)
        assert rc != 1, (
            f"{hook_name} aborted (rc=1) with lib/{lib} missing — reads as ALLOW"
        )

    def test_missing_lib_still_denies_a_credential_read(self, tmp_path):
        hook = gate_tree(
            tmp_path, "pre-tool-content-security.sh", drop_libs=("audit-bypass.sh",)
        )
        denied, rc, _ = run_gate(hook, "cat ~/.ssh/id_rsa")
        assert denied, f"credential read allowed with a lib missing (rc={rc})"

    def test_missing_lib_still_allows_a_benign_command(self, tmp_path):
        hook = gate_tree(
            tmp_path, "pre-tool-content-security.sh", drop_libs=("audit-bypass.sh",)
        )
        denied, _, _ = run_gate(hook, BENIGN)
        assert not denied, "a missing lib must not brick ordinary commands"


class TestASilentEmitterDoesNotDiscardADeny:
    """Ten deny sites emit through `python3 ... || true` then `exit 0`.

    `|| true` fires only on a NONZERO exit, so a python3 that exits 0 printing
    nothing emits no JSON, skips the fallback, and falls through to `exit 0` —
    discarding a deny the gate had ALREADY DECIDED.
    """

    def test_content_security_deny_survives_a_silent_emitter(self, tmp_path):
        stub = stub_tool(tmp_path, "python3", STUB_SILENT)
        denied, rc, _ = run_gate(
            HOOKS / "pre-tool-content-security.sh",
            "cat ~/.ssh/id_rsa",
            path_prefix=stub,
        )
        assert denied, f"a decided deny was discarded by a silent emitter (rc={rc})"

    def test_oom_deny_survives_a_silent_emitter(self, tmp_path):
        stub = stub_tool(tmp_path, "python3", STUB_SILENT)
        denied, rc, _ = run_gate(
            HOOKS / "pre-test-oom-gate.sh",
            MUST_DENY_PYTEST,
            path_prefix=stub,
            env={"HOME": str(daemon_home(tmp_path))},
        )
        assert denied, f"a decided deny was discarded by a silent emitter (rc={rc})"

    # WHY pre-exit-plan-mode-gate IS EXCLUDED HERE AND INCLUDED ELSEWHERE.
    # An adversarial pass called this exclusion inconsistent — the same fake
    # Bash payload is fed to that gate in the HOME and missing-lib tests, where
    # it happens to pass. The challenge was fair and the answer is a real
    # distinction, so it is written down rather than left to look motivated:
    #
    #   The HOME/missing-lib cases assert the gate does not ABORT. That abort
    #   happens at `DENY_LOG="${HOME}/..."` and at the `source` lines — BEFORE
    #   the payload is ever parsed. A Bash payload is therefore a valid probe
    #   for them; the payload shape is irrelevant to what is being measured.
    #
    #   This case asserts the gate ALLOWS. That is a decision, and a decision on
    #   a payload the gate's matcher (`ExitPlanMode`) guarantees it never sees.
    #   Fed one it fails closed, which for this gate is correct — an
    #   unrecognised payload means it cannot verify the contrarian ran.
    #   Demanding "allow" would weaken a control to make a test pass.
    #
    # OWED, and named rather than quietly skipped: a realistic ExitPlanMode
    # payload + prior-plan transcript would give this gate genuine deny-side
    # coverage under every degradation. Measured by that same pass to hold up
    # (it survives silent/broken python3, jq, and an absent scanner). Not built
    # here to keep this diff to the one root cause.
    @pytest.mark.parametrize("hook_name", [g for g in GATES if "exit-plan" not in g])
    def test_a_silent_emitter_does_not_deny_a_benign_command(self, hook_name, tmp_path):
        """Anti-brick partner, for every gate that actually matches Bash."""
        stub = stub_tool(tmp_path, "python3", STUB_SILENT)
        denied, rc, _ = run_gate(HOOKS / hook_name, BENIGN, path_prefix=stub)
        assert not denied, (
            f"{hook_name} denied '{BENIGN}' with a silent python3 (rc={rc})"
        )


@pytest.mark.parametrize(
    "hook_name", [g for g, p in GATE_PROBES.items() if p["deny"] and "gov" not in g]
)
@pytest.mark.parametrize("lib", ["audit-bypass.sh", "shell-scan.sh"])
def test_a_missing_lib_preserves_the_deny(hook_name, lib, tmp_path):
    """The OBSERVABLE, replacing a text grep that could not work.

    The first version of this asserted "no gate sources a lib unguarded" by
    grepping for `source .../lib/`. Two defects, both measured: it flagged
    sources that ARE correctly wrapped in `if [ -r ... ]` (so correct code could
    not satisfy it), and its only satisfiable form — assigning the path to a
    variable first — evades the grep while remaining exactly as unguarded.
    A check that correct code fails and that one refactor blinds forever is
    worse than none.

    Assert the thing that actually matters instead: with a lib missing, does the
    gate still reach and preserve its decision? That is unfoolable by spelling.
    """
    hook = gate_tree(tmp_path, hook_name, drop_libs=(lib,))
    # The OOM gate's deny is conditional on machine state; establish it.
    env = {"HOME": str(daemon_home(tmp_path))} if "oom" in hook_name else None
    denied, rc, _ = run_gate(hook, GATE_PROBES[hook_name]["deny"], env=env)
    assert denied, (
        f"{hook_name} lost its deny with lib/{lib} missing (rc={rc}) — a failed "
        "`source` exits 1, which the harness reads as ALLOW"
    )


@pytest.mark.parametrize(
    "hook_name",
    GATES,
)
def test_gates_that_claim_fail_closed_carry_an_err_trap(hook_name):
    """A recorded rule, checked rather than trusted — now across ALL five gates.

    LEARNING-LOG 2026-04-16 binds every security-relevant hook to
    `trap 'exit 2' ERR`. Two gates never applied it, and an earlier version of
    this test excluded them on the grounds that adding a trap changes failure
    behaviour and is "a decision, not a cleanup". That docstring then
    contradicted its own parametrize, which already listed all five.

    Resolved in favour of all five, deliberately: the decision was taken in the
    approved BACKLOG #299 Stage A plan (Task A6), and an adversarial pass built
    the trap-added mutant and probed 16 ordinary commands without producing a
    single brick. A rule two of five files ignore is not a rule.

    KNOWN INSUFFICIENT, measured session-272: `trap ... ERR` does NOT fire on a
    failed `source` or on an unbound variable under `set -u` — both exit 1,
    which the harness treats as ALLOW. The trap is necessary, not sufficient,
    which is why the decision-preserving tests above carry the real weight.
    """
    text = (HOOKS / hook_name).read_text()
    assert "trap 'exit 2' ERR" in text or 'trap "exit 2" ERR' in text, (
        f"{hook_name} claims fail-closed behaviour but has no ERR trap"
    )


# ---------------------------------------------------------------------------
# THE CROSS-PRODUCT. This replaces coverage-by-anecdote.
# ---------------------------------------------------------------------------

BASH_GATES = [
    "pre-tool-content-security.sh",
    "pre-test-oom-gate.sh",
    "pre-push-quality-gate.sh",
    # ADDED session-272 after this exclusion cost three defects.
    #
    # The governance gate was left out because its payload needs a transcript
    # rather than just a command — a shape difference, not a reason. It is the
    # HIGHEST-FIRING gate in the repo (every Bash, Edit and Write), and while it
    # sat outside this matrix it accumulated three separate instances of one
    # class: a deny emitter that discarded a computed verdict, and a DETECTOR
    # whose empty output read as "nothing missing" and allowed a non-compliant
    # call outright. A code-reviewer flagged the exclusion; CI found the cost.
    #
    # A cross-product that omits the busiest member is not a cross-product.
    "pre-tool-governance-check.sh",
]

# Every degradation, applied to every Bash gate, asserted in BOTH directions.
DEGRADATIONS = {
    "jq_broken": ("jq", STUB_BROKEN),
    "jq_silent": ("jq", STUB_SILENT),
    "grep_broken": ("grep", STUB_BROKEN),
    "grep_silent_nomatch": ("grep", "#!/bin/sh\nexit 1\n"),
    # Accepts plain -q but rejects -E/-F. The shape a `-q`-only health probe
    # passes while every real matcher silently returns no-match.
    "grep_no_ere_or_fixed": (
        "grep",
        '#!/bin/sh\nfor a in "$@"; do\n'
        '  case "$a" in -*E*|-*F*) exit 2 ;; esac\ndone\n'
        'exec /usr/bin/grep "$@"\n',
    ),
    "python3_broken": ("python3", STUB_BROKEN),
    # THE CORRELATED FAULT. Every other cell breaks ONE tool, but the written
    # justification for the unparseable-input deny is that jq and python3 resolve
    # to the same conda prefix here, so ONE broken environment takes out BOTH.
    # That cell did not exist, and its must-allow half is exactly what would have
    # caught the unescapable deny-everything: the new deny sat ABOVE the bypass
    # its own message told you to use. The axis chosen was "which tool"; the
    # code's own threat model says "which environment".
    "both_parsers_broken": (("jq", "python3"), STUB_BROKEN),
    "python3_silent": ("python3", STUB_SILENT),
}

# Must-deny and must-allow probes per gate. The allow list is the anti-brick
# pin: a degraded gate that blocks ordinary work is a different failure, not a
# safer one, because its only escape also disables the secret scanner.
CROSS_PROBES = {
    "pre-tool-content-security.sh": {
        "deny": [CRED, "cp " + chr(126) + "/.aws/credentials /tmp/x"],
        "allow": ["echo hi", "ls -la", "git status", "cat /srv/app/.npmrc"],
    },
    "pre-test-oom-gate.sh": {
        "deny": [
            "pytest tests/",
            'git commit -m "fix tests/test_a.py" && pytest tests/',
        ],
        "allow": [
            "echo hi",
            "git status",
            "pytest tests/test_a.py",
            'pytest -m "not slow"',
            # THE MIRROR of the deny probe above, and the partner whose absence
            # let a regression through. A quoted MENTION of pytest in a
            # NEIGHBOURING command must not make a targeted run look unsafe.
            # Without these three the segment detector regressed to a substring
            # match and denied all of them — the T-143 false-positive class,
            # reintroduced one layer down. Every deny probe here had an allow
            # partner at the GATE level; this one needed it at the PATTERN level.
            'git commit -m "ran pytest tests/ before this" && pytest tests/test_a.py',
            'grep -rn "pytest tests/" .claude/hooks && pytest tests/test_hooks.py',
            'echo "remember to run pytest tests/" && pytest tests/test_a.py',
        ],
    },
    # The governance gate denies a NON-COMPLIANT call and allows a compliant or
    # read-only one. Its probes are driven by the transcript fixture below, not
    # by the command text, so the command here is only a carrier.
    "pre-tool-governance-check.sh": {
        "deny": ["echo hi"],
        "allow": ["git status", "ls -la"],
    },
    "pre-push-quality-gate.sh": {
        "deny": ["git push --force origin main", "git push -f origin main"],
        "allow": [
            "echo hi",
            "git status",
            "git help push",
            'git commit -m "fix the push gate"',
            "git config --get remote.origin.pushurl",
        ],
    },
}


def _stub_tools(tmp_path, tool, body):
    """Stub one tool, or SEVERAL INTO ONE PATH DIR — the correlated-fault case.

    `stub_tool` puts each binary in its own `stub-<name>` directory and only one
    directory can be prepended, so calling it twice and keeping the last return
    value stubs only the LAST tool. The first version of this helper did exactly
    that, and the `both_parsers_broken` cell silently degraded to
    `python3_broken` — a test that reported coverage it did not have, which is
    the same defect this whole file exists to catch. Both binaries go in ONE dir.
    """
    names = (tool,) if isinstance(tool, str) else tuple(tool)
    d = Path(tmp_path) / ("stub-" + "-".join(names))
    d.mkdir(parents=True, exist_ok=True)
    for n in names:
        f = d / n
        f.write_text(body)
        f.chmod(0o755)
    return d


def _cross_payload(hook_name, command, tmp_path, *, compliant):
    """Payload for a cross-product probe.

    The governance gate reads `transcript_path`; the others read only the
    command. Returning None means "use run_gate's default Bash shape".
    """
    if "governance" not in hook_name:
        return None
    entries = [{"message": {"role": "user", "content": "do a thing"}}]
    if compliant:
        for tool in (
            "mcp__ai-governance__evaluate_governance",
            "mcp__context-engine__query_project",
        ):
            entries.append(
                {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "id": "x", "name": tool, "input": {}}
                        ],
                    }
                }
            )
    tp = Path(tmp_path) / f"transcript-{'ok' if compliant else 'bad'}.jsonl"
    tp.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": "/tmp/x.txt", "content": "x"},
        "transcript_path": str(tp),
    }


def _cross_env(hook_name, tmp_path):
    """Establish each gate's decision PRECONDITIONS. Nothing ambient.

    Two gates read machine state before they will deny, and neither reads the
    command to decide it:

      * the OOM gate needs a live watcher heartbeat (or torch processes, which a
        test cannot portably create);
      * the governance gate needs the ai-governance MCP server to appear in some
        config surface, or it correctly auto-degrades to advisory.

    The governance case was hidden behind an xfail and, when the xfail came off,
    the cells failed — not because the gate was broken but because `gate_tree`
    copies the hook to a temp tree with no config in it, so detection legitimately
    found nothing. That is the same defect as testing the OOM gate on a busy
    laptop, inverted: there the machine supplied a signal the test never
    established; here the machine WITHHELD one. Both mean the cell was measuring
    the environment.

    So the config surface is WRITTEN HERE, hermetically, and pointed at with the
    hook's documented `GOVERNANCE_PROJECT_ROOT` override — rather than relying on
    the developer's `~/.claude.json`, which is what made these cells pass locally
    and fail in a copied tree.
    """
    if "governance" in hook_name:
        root = Path(tmp_path) / "mcp-root"
        root.mkdir(parents=True, exist_ok=True)
        (root / ".mcp.json").write_text(
            json.dumps({"mcpServers": {"ai-governance": {}, "context-engine": {}}})
        )
        return {"GOVERNANCE_PROJECT_ROOT": str(root)}
    if "oom" not in hook_name:
        return None
    import json as _json
    from datetime import datetime, timedelta, timezone

    home = tmp_path / "xhome"
    (home / ".context-engine").mkdir(parents=True, exist_ok=True)
    alive = datetime.now(timezone.utc) - timedelta(seconds=30)
    (home / ".context-engine" / "watcher-heartbeat.json").write_text(
        _json.dumps({"alive_at": alive.isoformat()})
    )
    return {"HOME": str(home)}


class TestEveryDegradationAgainstEveryGate:
    """GATES x DEGRADATIONS, both directions. Not two hand-picked lists.

    WHY THIS CLASS EXISTS, stated plainly because the lesson is the point.

    The first version of this file tested a broken `grep` against two gates it
    happened to think of, and `jq`/`python3` against one. An independent audit
    then found the two holes those omissions left, and both were live:

      * the push gate's degraded detector was written in `grep` — the very tool
        whose failure routes execution there — so a shadowed `grep` allowed
        13/15 force-pushes;
      * a broken `jq` was a total silent bypass of the credential gate and the
        OOM gate, a class the push gate had already NAMED in a comment and fixed
        for itself alone.

    Neither hole needed a new idea to find. Both needed the cross-product that
    was not being taken. The recurring structure across this whole arc is a
    check repaired at the site where it was noticed, in the tool being repaired,
    and verified by a list someone wrote from memory. A cross-product is the
    cheapest structural answer: adding a gate or a degradation forces the cells.
    """

    @pytest.mark.parametrize("hook_name", BASH_GATES)
    @pytest.mark.parametrize("degradation", sorted(DEGRADATIONS))
    def test_a_degraded_tool_never_opens_a_gate(self, hook_name, degradation, tmp_path):
        """MUST-DENY. A gate that cannot run its matcher must not say yes."""
        tool, body = DEGRADATIONS[degradation]
        # The governance gate was xfail'd here as BACKLOG #299 Stage B debt.
        # REMOVED 2026-08-03: measurement shows all four gates now hold under
        # every degradation in DEGRADATIONS, so the cells run for real.
        #
        # AND THE MECHANISM WAS BROKEN, which is the part worth keeping. The
        # marker was an IMPERATIVE `pytest.xfail(...)` call, which flags the test
        # and HALTS it — the body never executes, so it can never report XPASS.
        # It was introduced with the explicit claim that "when Stage B lands these
        # turn XPASS and FAIL the suite, forcing the marker off". That was a
        # promise the construct cannot keep: only the DECORATOR form,
        # `@pytest.mark.xfail(strict=True)`, runs the body and fails on an
        # unexpected pass. Proven here — the gates were fixed and the suite still
        # reported 8 xfailed, 0 xpassed. A forcing function that cannot fire is
        # indistinguishable from a comment.
        tree = gate_tree(tmp_path, hook_name)
        stub = _stub_tools(tmp_path, tool, body)
        env = _cross_env(hook_name, tmp_path)
        for command in CROSS_PROBES[hook_name]["deny"]:
            payload = _cross_payload(hook_name, command, tmp_path, compliant=False)
            denied, rc, _ = run_gate(
                tree, command, env=env, path_prefix=stub, payload=payload
            )
            assert denied, (
                f"{hook_name}: {command!r} was ALLOWED with {tool} degraded "
                f"({degradation}, rc={rc}) — the gate is off, silently"
            )

    @pytest.mark.parametrize("hook_name", BASH_GATES)
    @pytest.mark.parametrize("degradation", sorted(DEGRADATIONS))
    def test_a_degraded_tool_never_blocks_ordinary_work(
        self, hook_name, degradation, tmp_path
    ):
        """MUST-ALLOW. The anti-brick partner, in the same run as its deny."""
        tool, body = DEGRADATIONS[degradation]
        tree = gate_tree(tmp_path, hook_name)
        stub = _stub_tools(tmp_path, tool, body)
        env = _cross_env(hook_name, tmp_path)
        for command in CROSS_PROBES[hook_name]["allow"]:
            payload = _cross_payload(hook_name, command, tmp_path, compliant=True)
            # DOCUMENTED EXCEPTION, and the only one in this matrix.
            #
            # With BOTH parsers broken the OOM gate cannot parse the payload, so
            # it cannot tell whose argument a `tests/test_x.py` substring is —
            # `git commit -m "fix tests/test_a.py" && pytest tests/` contains a
            # targeted shape and IS a full-suite run. That attribution is what
            # needs a parser, so a blind gate treats every pytest-shaped payload
            # as full-suite and over-blocks. Deliberate: an over-block costs one
            # explained deny with a reachable bypass; an under-block costs the
            # OOM the gate exists to prevent.
            #
            # The anti-brick property still holds and is still asserted — every
            # NON-pytest command must be allowed. That is what "does not brick
            # the session" means; it was never "allows literally everything".
            if (
                degradation == "both_parsers_broken"
                and "oom" in hook_name
                and "pytest" in command
            ):
                continue
            denied, rc, _ = run_gate(
                tree, command, env=env, path_prefix=stub, payload=payload
            )
            assert not denied, (
                f"{hook_name}: {command!r} was DENIED with {tool} degraded "
                f"({degradation}, rc={rc}) — a degraded gate that blocks "
                "ordinary work trains the bypass that disables all of it"
            )

    @pytest.mark.parametrize("hook_name", BASH_GATES)
    def test_a_home_with_regex_metacharacters_still_denies(self, hook_name, tmp_path):
        """A username containing a dot is ordinary input, not a degradation.

        `HOME` was regex-escaped and then used as a FIXED-STRING needle, so
        `/Users/jane.doe` became `/Users/jane\\.doe` and all seven expanded-path
        credential patterns stopped matching. `first.last` is a standard
        corporate username; `+` and `(` are legal in a path too.
        """
        if "governance" in hook_name:
            pytest.skip(
                "credential-path probe; this gate does not read credential paths"
            )
        tree = gate_tree(tmp_path, hook_name)
        for home_name in ("plain", "jane.doe", "a+b"):
            home = tmp_path / home_name
            (home / ".context-engine").mkdir(parents=True, exist_ok=True)
            if "oom" in hook_name:
                import json as _json
                from datetime import datetime, timedelta, timezone

                alive = datetime.now(timezone.utc) - timedelta(seconds=30)
                (home / ".context-engine" / "watcher-heartbeat.json").write_text(
                    _json.dumps({"alive_at": alive.isoformat()})
                )
            for command in CROSS_PROBES[hook_name]["deny"]:
                # Rewrite ~ to the literal home so the EXPANDED-path patterns
                # are what gets exercised, not the symbolic ~ ones.
                literal = command.replace(chr(126) + "/", str(home) + "/")
                denied, rc, _ = run_gate(tree, literal, env={"HOME": str(home)})
                assert denied, (
                    f"{hook_name}: {literal!r} was ALLOWED with HOME={home} (rc={rc})"
                )


class TestThePushGateNeverDiscardsAComputedDeny:
    """A deny that was correctly computed must reach the harness.

    THE CONTRACT, not the implementation: a PreToolUse hook denies only by
    POSITIVE ASSERTION — exit 2, or exit 0 with JSON carrying
    permissionDecision=deny. So a gate that decides "deny", fails to serialise
    it, and exits 0 with empty stdout has ALLOWED. `|| true` does not help: it
    catches a NONZERO exit, and the dangerous shape is a python3 that exits 0
    having printed nothing.

    This was live in the push gate for the whole of Stage A and the audit round.
    Both other gates got capture-and-check; this one — which holds the ONLY diff
    secret scanner — did not, and two rounds of testing did not notice because
    every probe used a healthy python3. An independent code-reviewer with no
    Bash tool found it by reading control flow.

    The `_PY_OK` health probe does not close this. It proves python3 worked ONCE,
    EARLIER. A python3 killed later — OOM under the memory pressure these gates
    exist for, a resource limit, a broken json module — passes the probe and then
    drops the verdict.
    """

    HOOK = "pre-push-quality-gate.sh"

    # A python3 that works for everything EXCEPT serialising the verdict. This is
    # the shape a health probe cannot catch, which is the entire point.
    PY_FAILS_ONLY_ON_EMIT = (
        "#!/bin/sh\n"
        'case "$*" in *"import json, sys"*) exit 0 ;; esac\n'
        'exec /usr/bin/python3 "$@"\n'
    )

    @pytest.mark.parametrize(
        "command",
        ["git push --force origin main", "git push -f origin main"],
    )
    def test_a_verdict_that_cannot_be_serialised_still_denies(self, command, tmp_path):
        """The force-push block must survive an emitter that prints nothing."""
        tree = gate_tree(tmp_path, self.HOOK)
        stub = stub_tool(tmp_path, "python3", self.PY_FAILS_ONLY_ON_EMIT)
        denied, rc, out = run_gate(tree, command, path_prefix=stub)
        assert denied, (
            f"{command!r} was ALLOWED (rc={rc}, {len(out)} bytes) — the gate "
            "decided to deny and then threw the decision away. Empty stdout "
            "with exit 0 is an ALLOW under the harness contract."
        )

    def test_the_structural_fallback_is_exit_2_not_a_silent_exit_0(self, tmp_path):
        """When the reason cannot be encoded, deny STRUCTURALLY.

        exit 2 is a deny regardless of stdout, so it is the only correct
        fallback when the rich JSON reason is unavailable. A terse deny beats a
        lost one.
        """
        tree = gate_tree(tmp_path, self.HOOK)
        stub = stub_tool(tmp_path, "python3", self.PY_FAILS_ONLY_ON_EMIT)
        _, rc, _ = run_gate(tree, "git push --force origin main", path_prefix=stub)
        assert rc == 2, f"expected structural deny (exit 2), got rc={rc}"

    def test_every_deny_in_this_gate_goes_through_the_checked_emitter(self):
        """Anti-drift, and deliberately an OUTCOME-shaped structural test.

        A previous structural test in this file grepped for a `source` guard
        SHAPE, flagged already-correct code, and was evadable by one refactor.
        This one asserts something narrower and non-evadable-by-rephrasing: the
        raw `python3 ... || true` deny-emitter idiom must not reappear. The
        helper itself is the single permitted construction site.
        """
        text = (HOOKS / self.HOOK).read_text()
        emitters = text.count("'permissionDecision': 'deny'")
        assert emitters == 1, (
            f"{self.HOOK} builds a deny payload in {emitters} places; there must "
            "be exactly one (inside emit_deny). Every other site must call "
            "emit_deny so the capture-and-check cannot be forgotten at a new one."
        )
        assert "|| true\n    exit 0" not in text, (
            "a raw `|| true` followed by `exit 0` discards a computed deny"
        )


def test_the_harness_leaves_nothing_behind_in_the_hooks_directory():
    """No test may create files inside the live `.claude/hooks/` tree.

    THE DEFECT THIS PINS. The ambient-signal neutralizer first wrote its stub
    `ps` to `Path(hook_path).parent / "_neutral-env"`. Sixteen call sites pass
    the LIVE hooks directory, so the harness created `.claude/hooks/_neutral-env/
    ps` in the real repo — and it was committed. A fake `ps` shipping inside the
    safety-hooks directory is a stray executable in the one tree that must stay
    trustworthy.

    Every test passed with the stub present and with it absent, because it only
    ever altered the harness's own PATH. So the suite could not see it; the
    completion checklist's `git diff --name-only` did. This test closes that gap
    by asserting the OBSERVABLE — is the tree clean? — rather than any particular
    spelling of the mistake, so a differently-named stray still fails it.
    """
    allowed_suffixes = {".sh", ".py", ".md"}
    strays = []
    for entry in HOOKS.iterdir():
        if entry.name in {"lib", "__pycache__"} or entry.name.startswith("."):
            continue
        if entry.is_dir():
            strays.append(f"{entry.name}/ (unexpected directory)")
        elif entry.suffix not in allowed_suffixes:
            strays.append(entry.name)
    assert not strays, (
        "unexpected entries in .claude/hooks/ — a test almost certainly wrote "
        f"them into the live tree: {strays}"
    )


class TestABrokenGrepCannotSilentlyDisarmTheGovernanceGate:
    """A failed detector must not read as "the thing is absent". BACKLOG #299.

    `pre-tool-governance-check.sh` auto-degrades from hard to advisory when the
    ai-governance MCP server is not configured in any session config surface.
    That degrade is CORRECT and must keep working: a session that genuinely
    cannot call the gated tools cannot satisfy a fail-closed gate, and forcing
    hard mode there is a deadlock the bypass cannot escape from inside.

    The detection was `if grep -q "name" file`, which collapses match(0),
    no-match(1) and ERROR(2+) into true/false. So a broken or shadowed `grep`
    read as "not configured" and silently turned the highest-firing gate in the
    repo — every Bash, Edit and Write — advisory. Measured: with grep stubbed to
    127, a non-compliant Write was ALLOWED and the debug log claimed the MCP
    server was not configured. Nothing about the config had changed; only the
    tool doing the looking had.

    Both directions are asserted here because the fix is dangerous in exactly one
    of them: over-returning "configured" keeps the gate hard, which at worst asks
    for a governance call that was already due. Under-returning turns the gate
    off. And if the legitimate degrade broke, every session without MCP
    configured would be bricked.
    """

    HOOK = "pre-tool-governance-check.sh"

    @staticmethod
    def _mcp_root(tmp_path):
        """A config surface naming the servers — established, never inherited.

        The autouse `isolate_home` fixture points $HOME at a throwaway dir, so
        `~/.claude.json` is absent in every test and the gate degrades LEGITIMATELY.
        The first version of this class did not account for that and was measuring
        the fixture rather than the gate — the same defect as testing the OOM gate
        on a busy laptop, and the fourth instance of it in one session.
        """
        root = Path(tmp_path) / "mcp-root"
        root.mkdir(parents=True, exist_ok=True)
        (root / ".mcp.json").write_text(
            json.dumps({"mcpServers": {"ai-governance": {}, "context-engine": {}}})
        )
        return root

    @staticmethod
    def _payload(tmp_path):
        t = Path(tmp_path) / "t.jsonl"
        t.write_text(json.dumps({"message": {"role": "user", "content": "x"}}) + "\n")
        return {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/x.txt", "content": "x"},
            "transcript_path": str(t),
        }

    def test_a_broken_grep_does_not_disarm_the_gate(self, tmp_path):
        """THE FAIL-OPEN. The detector failing is not evidence of absence."""
        stub = stub_tool(tmp_path, "grep", STUB_BROKEN)
        denied, rc, _ = run_gate(
            HOOKS / self.HOOK,
            "irrelevant",
            path_prefix=stub,
            env={"GOVERNANCE_PROJECT_ROOT": str(self._mcp_root(tmp_path))},
            payload=self._payload(tmp_path),
        )
        assert denied, (
            f"a broken grep turned the governance gate advisory (rc={rc}) — the "
            "config was never consulted, only the tool that reads it failed"
        )

    def test_the_legitimate_degrade_still_works(self, tmp_path):
        """THE ANTI-BRICK PARTNER, and the more dangerous direction to break.

        With no config surface naming the server, the degrade MUST still fire —
        otherwise every session that genuinely has no MCP configured is blocked
        with no in-band way out.
        """
        empty_home = Path(tmp_path) / "empty-home"
        empty_home.mkdir()
        denied, rc, _ = run_gate(
            HOOKS / self.HOOK,
            "irrelevant",
            env={"HOME": str(empty_home), "GOVERNANCE_PROJECT_ROOT": str(empty_home)},
            payload=self._payload(tmp_path),
        )
        assert not denied, (
            f"the MCP-absent auto-degrade stopped working (rc={rc}) — a session "
            "with no MCP configured is now bricked, which is worse than the "
            "fail-open this class was fixing"
        )
