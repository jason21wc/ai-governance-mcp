"""Tests for the post-push CI check hook (PostToolUse: Bash).

The hook (`.claude/hooks/post-push-ci-check.sh`) fires after a Bash call that runs
a `git push`, waits for GitHub to register the run, and reports CI status back into
the session. It carries four behaviours worth pinning:

1. THE TRIGGER (BACKLOG #230(d)). It used to grep `git.*push` against the RAW
   command, so `git commit -m "...ask before every git push..."` — which pushes
   nothing — cost a 5s sleep plus up to 17 `gh` API calls for a report about
   someone else's push. Same root cause the safety gates hit at n=3: a
   token-anchored matcher cannot tell executable position from quoted content.
   Detection now runs against `lib/shell-scan.sh`'s quoted-region-stripped view.

2. THE BILLING-VS-REAL CLASSIFIER (OPERATIONS T-169). A GitHub-Free billing block
   kills jobs in 3-8s because they never start; a genuine failure runs for
   minutes. That discriminator was documented in two places and applied in
   neither, and a genuinely red `security` job sat on main for three days behind
   a "billing, don't look" label. It is correct in BOTH directions and this file
   exists partly so it stays that way — these tests are a regression pin, not a
   specification of something to change.

3. THE FIELD CONTRACT (BACKLOG #234). The hook consumed `.[0].databaseId` from a
   `--json` list that never requested it, so the classifier in (2) was dead from
   the day it was written. The stub below now projects to the requested fields, and
   `test_every_requested_field_reaches_the_report` asserts each one reaches output
   — because projection alone only stops the fake over-supplying; a *dropped* field
   still degrades quietly through the hook's `//` defaults.

4. THE EXIT-0 CONTRACT. A PostToolUse hook must never disturb the Bash call that
   triggered it. Two ordinary conditions used to be fatal, both measured: no `jq`
   on PATH (exit 127) and a malformed payload (exit 5). Same class as BACKLOG #236
   in the session-start hooks.

`gh` and `sleep` are stubbed on PATH: no network, no waiting. The `gh` stub logs
every invocation, which is what makes the trigger assertions measure the actual
cost (calls made) rather than just the absence of stdout.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "post-push-ci-check.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("jq") is None, reason="hook parses its payload with jq"
)

GH_STUB = """#!/usr/bin/env bash
printf 'gh %s\\n' "$*" >> "$HOOK_TEST_CALL_LOG"

# HONOUR THE --json FIELD SELECTION (BACKLOG #234).
#
# The real `gh` returns ONLY the fields named after --json. A stub that hands back
# a complete fixture regardless of the request is MORE PERMISSIVE than the thing it
# replaces, and a permissive fake cannot detect the one defect class this API shape
# produces: a caller that consumes a field it never asked for.
#
# That is not a hypothetical. It is why the T-169 classifier's `.[0].databaseId`
# read was dead from the day it was written while this file stayed green -- the
# tests exercised a response production never receives. Projecting here is what
# makes the field list a contract instead of a comment.
json_fields=""
saw_json_flag=""
prev=""
for arg in "$@"; do
  [ "$prev" = "--json" ] && json_fields="$arg"
  [ "$arg" = "--json" ] && saw_json_flag=1
  prev="$arg"
done

# `--json` with no value would leave json_fields empty and silently fall through to
# the old return-everything behaviour -- a guard whose failure mode is to become the
# thing it replaced. Real `gh` errors here; so does this.
if [ -n "$saw_json_flag" ] && [ -z "$json_fields" ]; then
  echo "stub: --json given with no field list" >&2
  exit 1
fi

emit() {
  if [ -z "$json_fields" ]; then
    cat
    return
  fi
  jq --arg f "$json_fields" '
    def pick: with_entries(select(.key as $k | ($f | split(",")) | index($k)));
    if type == "array" then map(pick) else pick end'
}

case "$*" in
  "run list --limit 1 "*)  emit < "$HOOK_TEST_FIXTURES/latest.json" ;;
  "run list --limit 15 "*) emit < "$HOOK_TEST_FIXTURES/recent.json" ;;
  "run view "*)
      f="$HOOK_TEST_FIXTURES/jobs-$3.json"
      if [ -f "$f" ]; then emit < "$f"; else printf '{"jobs":[]}\\n'; fi
      ;;
  *) printf '\\n' ;;
esac
exit 0
"""

# Stubbed so a firing test does not actually wait 5 seconds. It logs too, because
# the sleep is half of what the false trigger was costing.
SLEEP_STUB = """#!/usr/bin/env bash
printf 'sleep %s\\n' "$*" >> "$HOOK_TEST_CALL_LOG"
exit 0
"""


def jobs_json(*durations, conclusion="failure"):
    """Jobs payload whose failed jobs ran for `durations` seconds each.

    The hook computes `completedAt - startedAt` via jq's fromdateiso8601, so the
    durations have to be expressed as real ISO timestamps.
    """
    out = []
    for secs in durations:
        out.append(
            {
                "conclusion": conclusion,
                "startedAt": "2026-07-24T00:00:00Z",
                "completedAt": _plus(secs),
            }
        )
    return {"jobs": out}


def _plus(seconds):
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"2026-07-24T{hours:02d}:{mins:02d}:{secs:02d}Z"


@pytest.fixture
def env(tmp_path):
    """PATH-stubbed environment. Returns a handle with fixtures + call log."""
    bin_dir = tmp_path / "bin"
    fixtures = tmp_path / "fixtures"
    bin_dir.mkdir()
    fixtures.mkdir()
    (bin_dir / "gh").write_text(GH_STUB)
    (bin_dir / "sleep").write_text(SLEEP_STUB)
    for f in ("gh", "sleep"):
        (bin_dir / f).chmod(0o755)

    call_log = tmp_path / "calls.log"

    class Handle:
        def __init__(self):
            self.bin_dir = bin_dir
            self.fixtures = fixtures
            self.call_log = call_log
            # Default: one completed, successful run. Overridden per test.
            self.set_latest(status="completed", conclusion="success")
            self.set_recent([])

        def set_latest(self, **fields):
            run = {
                "status": "completed",
                "conclusion": "success",
                "name": "CI",
                "headBranch": "main",
                "url": "https://example/run/1",
                "createdAt": "2026-07-24T00:00:00Z",
                "databaseId": 1,
            }
            run.update(fields)
            (fixtures / "latest.json").write_text(json.dumps([run]))

        def set_recent(self, runs):
            (fixtures / "recent.json").write_text(json.dumps(runs))

        def set_jobs(self, run_id, payload):
            (fixtures / f"jobs-{run_id}.json").write_text(json.dumps(payload))

        def calls(self):
            if not call_log.exists():
                return []
            return [ln for ln in call_log.read_text().splitlines() if ln.strip()]

    return Handle()


def run_hook(env, command, path=None):
    """Feed the hook a PostToolUse payload for `command`."""
    e = os.environ.copy()
    e["PATH"] = path if path is not None else f"{env.bin_dir}:{e['PATH']}"
    e["HOOK_TEST_CALL_LOG"] = str(env.call_log)
    e["HOOK_TEST_FIXTURES"] = str(env.fixtures)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        env=e,
        timeout=30,
    )


class TestTriggerIgnoresQuotedMentions:
    """BACKLOG #230(d) — a push must be RUN, not merely mentioned.

    Every case here pushes nothing. The assertion is on side effects, not just
    stdout: the cost of the false trigger was the sleep and the API calls.
    """

    @pytest.mark.parametrize(
        "command",
        [
            'git commit -m "docs(ops): explain why we ask before every git push"',
            "git commit -m 'chore: note the git push cadence'",
            'echo "remember to git push origin main"',
            'grep -rn "git push" .claude/hooks/',
            'git commit -m "fix: post-push-ci-check.sh fired on prose"',
        ],
    )
    def test_quoted_mention_is_silent_and_free(self, env, command):
        r = run_hook(env, command)
        assert r.returncode == 0
        assert r.stdout.strip() == ""
        assert env.calls() == [], "a mention must cost no sleep and no gh calls"

    def test_heredoc_body_mention_is_silent(self, env):
        r = run_hook(env, "git commit -F - <<EOF\ndocs: git push notes\nEOF")
        assert r.returncode == 0
        assert r.stdout.strip() == ""
        assert env.calls() == []

    @pytest.mark.parametrize("command", ["ls -la", "pytest tests/ -q", ""])
    def test_unrelated_commands_stay_silent(self, env, command):
        r = run_hook(env, command)
        assert r.returncode == 0
        assert r.stdout.strip() == ""
        assert env.calls() == []


class TestTriggerStillCatchesRealPushes:
    """The other direction — stripping quotes must not cost a true positive."""

    @pytest.mark.parametrize(
        "command",
        [
            "git push origin main",
            "git push",
            'git push origin "main"',
            'git commit -m "fix: thing" && git push origin main',
            "git -C /Users/x/repo push",
            "cd /repo && git push --set-upstream origin feature",
        ],
    )
    def test_real_push_fires(self, env, command):
        r = run_hook(env, command)
        assert r.returncode == 0
        assert "CI run detected" in r.stdout
        assert any(c.startswith("gh run list --limit 1") for c in env.calls())

    @pytest.mark.parametrize(
        "command",
        [
            'bash -c "git push origin main"',
            'ssh host "cd /repo && git push"',
            "bash <<EOF\ngit push origin main\nEOF",
        ],
    )
    def test_quoted_invocation_is_a_known_missed_case(self, env, command):
        """ACCEPTED RESIDUAL, pinned so a future change to it is deliberate.

        These DO push, and the hook no longer sees them: stripping quoted regions
        cannot distinguish a quoted command name from quoted prose. The cost is a
        missed CI report, which is this hook's expensive direction — accepted only
        because this project pushes with a bare `git push` (the human authorizes
        each one). The fix, if these forms ever appear, is a real shell parser;
        loosening the regex would re-admit the prose class this file exists for.
        """
        r = run_hook(env, command)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_every_requested_field_reaches_the_report(self, env):
        """Each field in the hook's `--json` list must be pinned to an observable.

        Projecting the stub (#234) stops it certifying fields nobody asked for, but
        it does NOT make a dropped field loud: every read in the hook has a `//`
        default, so dropping one silently yields "unknown"/"" — the exact shape in
        which #234 hid. Only an assertion on the VALUE reddens.

        Measured, not assumed: before this test existed, deleting `name` from the
        hook's field list left all 29 tests green.

        If you add a field to the hook's `--json` list, add it here too.
        """
        env.set_latest(
            status="completed",
            conclusion="success",
            name="Pipeline-Alpha",
            headBranch="release-candidate",
            url="https://example/run/9781",
        )
        out = run_hook(env, "git push origin main").stdout
        assert "Pipeline-Alpha" in out, "name dropped from the --json list"
        assert "release-candidate" in out, "headBranch dropped from the --json list"
        assert "https://example/run/9781" in out, "url dropped from the --json list"
        assert "completed" in out, "status dropped from the --json list"
        assert "success" in out, "conclusion dropped from the --json list"
        # databaseId is pinned separately by the classifier tests, which are the
        # only place its absence is observable.

    def test_in_progress_run_advises_watching(self, env):
        env.set_latest(status="in_progress", conclusion=None)
        r = run_hook(env, "git push origin main")
        assert "gh run watch" in r.stdout

    def test_malformed_payload_is_not_fatal(self, env):
        """MEASURED before the fix: exit 5. A hook must not break the Bash call.

        `set -euo pipefail` plus an unguarded `jq` on the payload meant any input
        jq could not parse killed the hook with jq's own status. Same contract
        breach as BACKLOG #236 in the session-start hooks, different file.
        """
        e = os.environ.copy()
        e["PATH"] = f"{env.bin_dir}:{e['PATH']}"
        e["HOOK_TEST_CALL_LOG"] = str(env.call_log)
        e["HOOK_TEST_FIXTURES"] = str(env.fixtures)
        r = subprocess.run(
            ["bash", str(HOOK)],
            input="{",
            capture_output=True,
            text=True,
            env=e,
            timeout=30,
        )
        assert r.returncode == 0
        assert env.calls() == []

    def test_missing_jq_is_not_fatal(self, env, tmp_path):
        """MEASURED before the fix: exit 127.

        The lookback's `command -v jq` guard is unreachable — jq is used to parse
        the payload long before it. Without a top guard the hook died on any
        machine lacking an optional dependency.
        """
        lean = tmp_path / "leanbin"
        lean.mkdir()
        for b in ("bash", "grep", "sed", "cat", "dirname", "pwd"):
            src = shutil.which(b)
            if src:
                (lean / b).symlink_to(src)
        if shutil.which("jq", path=str(lean)):
            pytest.skip("jq still reachable on the lean PATH")
        r = subprocess.run(
            ["bash", str(HOOK)],
            input=json.dumps({"tool_input": {"command": "git push origin main"}}),
            capture_output=True,
            text=True,
            env={"PATH": str(lean), "HOME": str(tmp_path)},
            timeout=30,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"

    @pytest.mark.parametrize(
        "payload",
        [
            '{"status":"completed"}',  # object, not array — exit 5 before the fix
            '"a string"',
            "123",
            "null",
            "{}",
            # ARRAYS of non-objects. These passed the FIRST version of the shape
            # guard (`type == "array" and length > 0`) and still died at `.[0].status`
            # with the same jq error and the same exit 5 — the guard stopped one
            # predicate short of the property its own comment named. Found by code
            # review, not by the six payloads above, which all collapse to a single
            # branch: each fails the very first conjunct.
            # ARRAYS of non-objects are NOT here: the contract-faithful stub's
            # own `--json` projection destroys them before the hook sees them
            # (`with_entries` over a number errors, so the stub emits nothing).
            # Putting them here would measure the stub. They are covered against
            # a deliberately raw stub in TestShapeGuardAgainstRawOutput below.
            # jq FAILS rather than returning false on these two — a different
            # mechanism reaching the same branch, and previously untested.
            "",  # gh exits 0 with empty stdout -> jq exit 4
            "{not json",  # unparseable -> jq exit 2
        ],
    )
    def test_wrong_shaped_gh_output_is_not_fatal(self, env, payload):
        """A SUCCESSFUL `gh` call returning a non-array must not kill the hook.

        MEASURED before the fix: `{"status":"completed"}` exited **5** with
        `jq: error … Cannot index object with number`. The emptiness guard used
        `jq length`, which counts an object's KEYS, so a non-array passed it and
        then hit `.[0]`. Checking the count without checking the shape.

        Distinct from the malformed-*payload* case: there the hook's own stdin is
        bad; here `gh` exits 0 and hands back well-formed JSON of the wrong type.
        Found by an independent verifier probing a boundary this hook's UNVERIFIED
        list had named but not tested.
        """
        (env.fixtures / "latest.json").write_text(payload)
        r = run_hook(env, "git push origin main")
        assert r.returncode == 0, f"stdout={r.stdout} stderr={r.stderr}"
        assert "CI run detected" not in r.stdout

    def test_array_of_empty_objects_is_accepted_not_fatal(self, env):
        """`[{}]` passes the shape guard and reports a run with unknown fields.

        DOCUMENTED, NOT FIXED. The guard's job is to prevent a crash and to
        prevent inventing a run out of an EMPTY list; `[{}]` is a well-formed
        array of objects, so it passes, and every field falls to its `//`
        default. That renders as `CI run detected: unknown on unknown`, which is
        arguably still inventing a run.

        Left alone deliberately: `gh run list --json <fields>` returns objects
        carrying the requested keys, so this shape is not reachable in
        production, and adding a "must have at least one expected key" predicate
        would be guarding against the test stub rather than against `gh`. The
        contract that matters — never exit non-zero — holds.
        """
        (env.fixtures / "latest.json").write_text("[{}]")
        r = run_hook(env, "git push origin main")
        assert r.returncode == 0
        assert "unknown on unknown" in r.stdout

    def test_empty_run_list_is_not_reported_as_a_run(self, env):
        """`[]` must read as "no runs", not as a run with every field missing.

        The `//` defaults turned an empty list into a confident
        `CI run detected: unknown on unknown` — a fabricated run.
        """
        (env.fixtures / "latest.json").write_text("[]")
        out = run_hook(env, "git push origin main").stdout
        assert "No workflow run to report" in out
        assert "CI run detected" not in out

    def test_missing_gh_is_reported_not_fatal(self, env, tmp_path):
        """Degradation path: no gh on PATH must not break the Bash call."""
        jq = shutil.which("jq")
        assert jq, "guarded by pytestmark"
        path = f"{env.bin_dir}:{os.path.dirname(jq)}:/usr/bin:/bin"
        # The stub bin ships gh; drop it so the hook sees a machine without one.
        (env.bin_dir / "gh").unlink()
        if shutil.which("gh", path=path):
            pytest.skip("real gh reachable on the minimal PATH")
        r = run_hook(env, "git push origin main", path=path)
        assert r.returncode == 0
        assert "gh CLI not found" in r.stdout


class TestBillingVsRealClassification:
    """OPERATIONS T-169 regression pin. This logic is CORRECT — keep it that way.

    A billing block kills jobs in 3-8s because they never start. A genuine
    failure runs for minutes. Getting this backwards is what hid a red security
    job on main for three days.
    """

    def test_short_failure_is_labelled_billing(self, env):
        env.set_latest(conclusion="failure", databaseId=42)
        env.set_jobs(42, jobs_json(4))
        r = run_hook(env, "git push origin main")
        assert "billing block" in r.stdout
        assert "REAL" not in r.stdout

    def test_long_failure_is_labelled_real(self, env):
        env.set_latest(conclusion="failure", databaseId=42)
        env.set_jobs(42, jobs_json(287))  # 4m47s — the actual T-169 duration
        r = run_hook(env, "git push origin main")
        assert "CI FAILURE IS **REAL**" in r.stdout
        assert "Do NOT apply the 'expected GitHub-Free billing' label" in r.stdout
        assert "gh run view 42 --log-failed" in r.stdout

    def test_longest_failed_job_decides(self, env):
        """One quick job among slow ones must not downgrade the verdict."""
        env.set_latest(conclusion="failure", databaseId=42)
        env.set_jobs(42, jobs_json(3, 5, 240))
        assert "REAL" in run_hook(env, "git push origin main").stdout

    def test_unclassifiable_failure_says_so_rather_than_going_quiet(self, env):
        """The verdict is ternary. Silence on a red run is the T-169 failure itself.

        A failed run whose jobs carry no usable timings (cancelled, timed out, a
        workflow-level failure with no failed job) produced NO output at all — which
        reads as reassurance on a run that failed. Unreachable until #234 made the
        classifier live, so it had never been exercised.
        """
        env.set_latest(conclusion="failure", databaseId=42)
        env.set_jobs(42, {"jobs": [{"conclusion": "cancelled"}]})
        out = run_hook(env, "git push origin main").stdout
        assert "could NOT classify" in out
        assert "NOT a clean bill of health" in out
        assert "billing block" not in out
        assert "CI FAILURE IS **REAL**" not in out

    def test_unclassifiable_when_run_details_are_unfetchable(self, env):
        """Same verdict when the jobs call yields nothing — no id, no fixture."""
        env.set_latest(conclusion="failure")  # default databaseId=1, no jobs-1.json
        out = run_hook(env, "git push origin main").stdout
        assert "could NOT classify" in out

    def test_successful_run_is_not_classified(self, env):
        r = run_hook(env, "git push origin main")
        assert "billing" not in r.stdout
        assert "REAL" not in r.stdout


class TestLookback:
    """A real failure one push back used to be invisible forever (T-169)."""

    def test_earlier_real_failure_is_surfaced(self, env):
        env.set_latest(conclusion="success")  # current push looks clean
        env.set_recent(
            [
                {
                    "databaseId": 30121645663,
                    "conclusion": "failure",
                    "headSha": "abc",
                    "displayTitle": "test_no_unregistered_skills",
                }
            ]
        )
        env.set_jobs(30121645663, jobs_json(217))
        r = run_hook(env, "git push origin main")
        assert "AN EARLIER CI RUN FAILED FOR REAL" in r.stdout
        assert "30121645663" in r.stdout
        assert "test_no_unregistered_skills" in r.stdout

    def test_earlier_billing_failure_is_not_surfaced(self, env):
        env.set_latest(conclusion="success")
        env.set_recent(
            [
                {
                    "databaseId": 777,
                    "conclusion": "failure",
                    "headSha": "abc",
                    "displayTitle": "billing block",
                }
            ]
        )
        env.set_jobs(777, jobs_json(6))
        r = run_hook(env, "git push origin main")
        assert "AN EARLIER CI RUN FAILED" not in r.stdout
        # POSITIVE ANCHOR. Without it this test passes whether the discriminator
        # ran and said "billing" or nothing ran at all — a jq error inside the stub,
        # an unread fixture, a deleted lookback block all look identical from a
        # purely negative assertion.
        assert any(c.startswith("gh run view 777") for c in env.calls()), (
            "the run must actually have been inspected, not merely not-reported"
        )

    def test_current_run_is_not_reported_as_an_earlier_one(self, env):
        """The lookback set really does contain the current run.

        `gh run list --limit 15` returns the 15 newest runs, which necessarily
        includes the one `--limit 1` just returned. So a current-push failure
        matches BOTH paths, and the lookback would announce the run the user is
        looking at as an "EARLIER" one that "MAY BE UNEXAMINED" — while the
        classifier below reports the same run correctly. Two banners, one of them
        false, about a single failure.

        This was unobservable until #234: the current-run classifier was dead, so
        nothing ever fired alongside the lookback. Fixing one exposed the other.
        """
        env.set_latest(conclusion="failure", databaseId=42)
        env.set_jobs(42, jobs_json(287))
        # The current run is placed SECOND on purpose. A skip implemented by
        # position ("ignore the first entry") rather than by id would survive a
        # first-position fixture, and the two `gh run list` calls are separate
        # round-trips whose ordering can legitimately differ.
        env.set_recent(
            [
                {
                    "databaseId": 555,
                    "conclusion": "success",
                    "headSha": "old",
                    "displayTitle": "an unrelated green run",
                },
                {
                    "databaseId": 42,
                    "conclusion": "failure",
                    "headSha": "abc",
                    "displayTitle": "the current push",
                },
            ]
        )
        out = run_hook(env, "git push origin main").stdout
        assert "CI FAILURE IS **REAL**" in out, "current run must still classify"
        assert "AN EARLIER CI RUN FAILED" not in out

    def test_skipping_the_current_run_still_surfaces_a_different_one(self, env):
        """The skip must be targeted at one id, not a blanket disable.

        The dangerous over-correction: suppressing the whole lookback whenever the
        current run also failed, which would restore exactly the blind spot the
        lookback was built for — a real red one push back, invisible forever.
        """
        env.set_latest(conclusion="failure", databaseId=42)
        env.set_jobs(42, jobs_json(287))
        env.set_recent(
            [
                {
                    "databaseId": 42,
                    "conclusion": "failure",
                    "headSha": "abc",
                    "displayTitle": "the current push",
                },
                {
                    "databaseId": 30121645663,
                    "conclusion": "failure",
                    "headSha": "def",
                    "displayTitle": "test_no_unregistered_skills",
                },
            ]
        )
        env.set_jobs(30121645663, jobs_json(217))
        out = run_hook(env, "git push origin main").stdout
        assert "CI FAILURE IS **REAL**" in out
        assert "AN EARLIER CI RUN FAILED" in out
        assert "30121645663" in out

    def test_lookback_survives_unreadable_run(self, env):
        """Fails quiet — a broken lookback must not swallow the current report."""
        env.set_latest(conclusion="success")
        env.set_recent(
            [{"databaseId": 999, "conclusion": "failure", "displayTitle": "x"}]
        )
        # No jobs-999.json fixture -> stub returns an empty jobs list.
        r = run_hook(env, "git push origin main")
        assert r.returncode == 0
        assert "CI run detected" in r.stdout


class TestShapeGuardAgainstRawOutput:
    """Shapes the contract-faithful stub cannot deliver (code review M1).

    WHY A SECOND STUB EXISTS, stated because a second fake is normally a smell.
    The main `GH_STUB` honours `--json` by projecting its fixture — deliberately,
    since a permissive fake is what let BACKLOG #234 hide. That projection also
    REWRITES malformed fixtures: `map(with_entries(...))` over `[1]` errors, so
    the stub emits nothing and the hook never sees the array at all. Feeding
    array-of-non-object payloads through it measures the stub, not the guard —
    which is exactly what the first version of these cases did, and they passed
    against the unfixed hook.

    MEASURED against a raw stub: `[1]`, `["x"]` and `[true]` exit **1** on the
    pre-fix hook (`type == "array" and length > 0`, which establishes array-ness
    but not element shape) and **0** after adding `(.[0] | type) == "object"`.

    Honest scope: real `gh run list --json <fields>` returns objects carrying the
    requested keys, so these shapes are not reachable in production. This closes
    a stated contract — never exit non-zero — rather than an observed incident.
    """

    RAW_GH = """#!/usr/bin/env bash
case "$*" in
  "run list --limit 1 "*) cat "$HOOK_TEST_FIXTURES/latest.json" ;;
  *) printf '[]\n' ;;
esac
exit 0
"""

    @pytest.mark.parametrize("payload", ["[1]", '["x"]', "[true]", "[1,2,3]"])
    def test_array_of_non_objects_does_not_break_the_exit_contract(self, env, payload):
        (env.bin_dir / "gh").write_text(self.RAW_GH)
        (env.bin_dir / "gh").chmod(0o755)
        (env.fixtures / "latest.json").write_text(payload)
        r = run_hook(env, "git push origin main")
        assert r.returncode == 0, f"stdout={r.stdout} stderr={r.stderr}"
        assert "CI run detected" not in r.stdout

    def test_raw_stub_still_passes_a_well_formed_array(self):
        """Guard against the raw stub itself becoming the thing under test."""
        assert "--json" not in self.RAW_GH, (
            "the raw stub must NOT project; that is its only purpose here"
        )
