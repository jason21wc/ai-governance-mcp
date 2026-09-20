"""A process outlives its working directory — the governance gate must too.

THE INCIDENT THESE TESTS ENCODE
-------------------------------
A session ran ``ExitWorktree``, deleting the git worktree its own governance MCP
server process had been launched in. From that moment ``Path.cwd()`` raised
``FileNotFoundError`` for the life of the process, and every
``evaluate_governance`` call returned ``[Errno 2] No such file or directory``.
The enforcement gate this repo exists to provide was down for a whole session.

The chain was: the tool computed its assessment, then called
``log_governance_audit_async`` to record it, which validated the log path, which
re-derived the project root from the working directory, which raised. A fully
computed governance verdict was discarded because a log line could not be
appended.

WHY THE TESTS ARE AT THIS ALTITUDE — read this before adding to them
-------------------------------------------------------------------
The first fix proposed for this bug was a guard on
``path_resolution.is_within_allowed_scope``, with a unit test asserting that
function tolerates a dead cwd. That test would have PASSED while the incident
remained perfectly reproducible, because ``is_within_allowed_scope`` is not on
the ``evaluate_governance`` path at all. A test that goes green while the bug
lives is worse than no test — it retires the question.

So the load-bearing tests here (``TestTelemetryFailureDoesNotDiscardTheRecord``)
assert the property that actually matters: **the record survives and the caller
does not raise**. Unit tests on the individual guards follow, but they are
support, not the contract.
"""

import asyncio
import errno
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from ai_governance_mcp import config
from ai_governance_mcp.path_resolution import is_within_allowed_scope, safe_cwd


@pytest.fixture
def dead_cwd():
    """Run the test body with the process sitting in a deleted directory.

    ``monkeypatch.chdir`` cannot be used: its teardown restores the previous
    directory by path, and computing that path calls ``getcwd()``, which is the
    very thing that fails here. So the original directory is captured as an OPEN
    FILE DESCRIPTOR before the deletion and restored with ``os.fchdir``, which
    needs no path lookup and therefore still works.

    NOT PARALLEL-SAFE. It mutates process-global cwd, so these tests would flake
    *other* tests under in-process parallelism. There is no ``-n``/xdist in
    ``pyproject.toml`` today; if one is ever added, mark this module serial.
    """
    victim = tempfile.mkdtemp(prefix="dead-cwd-")
    # Opened AFTER mkdtemp so a failing mkdtemp cannot leak the descriptor.
    anchor_fd = os.open(".", os.O_RDONLY)
    try:
        os.chdir(victim)
        shutil.rmtree(victim)
        yield Path(victim)
    finally:
        # Restore before pytest formats any failure report: traceback rendering
        # calls Path.cwd(), and an unrestored cwd there risks an INTERNALERROR
        # rather than a readable test failure.
        os.fchdir(anchor_fd)
        os.close(anchor_fd)
        shutil.rmtree(victim, ignore_errors=True)


class TestTheFixtureActuallyReproducesTheFailure:
    """If these fail, every test below is vacuous.

    Per the repo rule for anything whose job is to detect: the acceptance test is
    not "does it pass" but "have I watched it fail on the real condition". These
    assert the real condition is present.
    """

    def test_raw_path_cwd_raises(self, dead_cwd):
        with pytest.raises(FileNotFoundError):
            Path.cwd()

    def test_raw_os_getcwd_raises(self, dead_cwd):
        with pytest.raises(FileNotFoundError):
            os.getcwd()


class TestTelemetryFailureDoesNotDiscardTheRecord:
    """THE CONTRACT. A failed durable write must not fail the governed call."""

    def test_audit_write_survives_dead_cwd(
        self, reset_server_state, test_settings, dead_cwd
    ):
        """The exact call that broke: governance.py:500 on a dead cwd.

        Asserts three things at once, because the bug needed all three to be
        wrong: it does not raise, the in-memory audit trail still receives the
        entry, and the failure is COUNTED rather than silently swallowed.

        Covers: FM-VERDICT-DISCARDED-BY-FAILED-SIDE-EFFECT
        """
        from ai_governance_mcp.models import GovernanceAuditLog
        from ai_governance_mcp.server import _logging, _state

        _state._settings = test_settings
        # Point the durable write at the dead directory — this is what a session
        # whose worktree was deleted actually had in its loaded settings.
        test_settings.logs_path = dead_cwd / "logs"
        _logging._telemetry_failures.clear()

        entry = GovernanceAuditLog(
            audit_id="gov-deadcwd-test",
            timestamp="2026-07-29T00:00:00+00:00",
            action="probe",
            assessment="PROCEED",
            confidence="high",
        )

        asyncio.run(_logging.log_governance_audit_async(entry))

        assert any(
            e.audit_id == "gov-deadcwd-test" for e in _logging.get_audit_log()
        ), (
            "the in-memory audit trail lost the record — a governance verdict was "
            "discarded because its log line could not be written"
        )
        assert _logging.get_telemetry_failures().get("governance_audit") == 1, (
            "the durable write failed but was not accounted for; a silent swallow "
            "trades a loud availability failure for a quiet integrity failure"
        )

    def test_reasoning_write_survives_dead_cwd(
        self, reset_server_state, test_settings, dead_cwd
    ):
        """governance.py:534 — the same call one line down, same contract."""
        from ai_governance_mcp.models import GovernanceReasoningLog
        from ai_governance_mcp.server import _logging, _state

        _state._settings = test_settings
        test_settings.logs_path = dead_cwd / "logs"
        _logging._telemetry_failures.clear()

        asyncio.run(
            _logging.log_reasoning_async(
                GovernanceReasoningLog(
                    audit_id="gov-deadcwd-test",
                    reasoning_entries=[],
                    final_decision="PROCEED",
                )
            )
        )

        assert any(
            e.audit_id == "gov-deadcwd-test" for e in _logging.get_reasoning_log()
        )
        assert _logging.get_telemetry_failures().get("governance_reasoning") == 1

    def test_log_dir_outside_home_survives_dead_cwd(
        self, reset_server_state, test_settings, dead_cwd, tmp_path_factory
    ):
        """REGRESSION for the bug my own machine was hiding.

        The first version of the guard caught ``OSError`` only. But on a dead cwd
        the permitted-roots list loses TWO entries — the cwd, and the real project
        root, because ``_find_project_root()`` stops finding its marker and returns
        the ``~/.ai-governance`` fallback. A log directory outside ``$HOME`` then
        fails with ``LogPathOutOfScope``, which is a ``ValueError``, sails past an
        OSError-only guard, and reproduces the original incident.

        It did not reproduce locally because this checkout lives under ``$HOME``.
        Found by review; this test is what makes the environment irrelevant.
        """
        from ai_governance_mcp.models import GovernanceAuditLog
        from ai_governance_mcp.server import _logging, _state

        # A directory that is NOT under $HOME (which conftest points at a tmp dir),
        # NOT under tempdir, and NOT under the project root — i.e. the Docker /app
        # or /workspace/repo shape.
        outside = Path("/private/etc/ai-governance-nonexistent/logs")

        _state._settings = test_settings
        test_settings.logs_path = outside
        _logging._telemetry_failures.clear()

        entry = GovernanceAuditLog(
            audit_id="gov-outside-home",
            timestamp="2026-07-29T00:00:00+00:00",
            action="probe",
            assessment="PROCEED",
            confidence="high",
        )
        # Must NOT raise. Pre-fix this raised LogPathOutOfScope -> TOOL_ERROR.
        asyncio.run(_logging.log_governance_audit_async(entry))

        assert any(e.audit_id == "gov-outside-home" for e in _logging.get_audit_log())
        assert _logging.get_telemetry_failures().get("governance_audit") == 1

    def test_path_traversal_is_still_fatal(self, reset_server_state, test_settings):
        """The guard absorbs environment failures — never the M1 attack signal.

        ``LogPathTraversal`` and ``LogPathOutOfScope`` are both ``ValueError``
        subclasses and both decline the write, so neither is a security
        relaxation. Only the traversal one is an active-manipulation signal, and
        only it stays fatal. If the guard widened to bare ``except ValueError``
        this test fails, which is the point.
        """
        from ai_governance_mcp.server import _logging

        with pytest.raises(_logging.LogPathTraversal):
            _logging._guarded_write(Path("/tmp/../etc/evil.jsonl"), "{}\n", "probe")

    def test_out_of_scope_is_absorbed_not_fatal(self, reset_server_state):
        """The sibling exception, pinned in the opposite direction."""
        from ai_governance_mcp.server import _logging

        _logging._telemetry_failures.clear()
        # No raise expected — declined write, counted.
        _logging._guarded_write(Path("/private/etc/nope/evil.jsonl"), "{}\n", "probe")
        assert _logging.get_telemetry_failures().get("probe") == 1

    def test_failure_is_logged_once_per_kind_not_once_per_call(
        self, reset_server_state, test_settings, dead_cwd, caplog
    ):
        """A dead cwd lasts the process lifetime; the warning must not.

        Without this, a long session emits one warning per governance call
        forever — the alert-fatigue pattern this repo has already recorded
        driving people to bypass flags.
        """
        from ai_governance_mcp.server import _logging, _state

        _state._settings = test_settings
        test_settings.logs_path = dead_cwd / "logs"
        _logging._telemetry_failures.clear()

        with caplog.at_level("WARNING"):
            for _ in range(5):
                _logging._guarded_write(dead_cwd / "logs" / "x.jsonl", "{}\n", "probe")

        assert _logging.get_telemetry_failures()["probe"] == 5, "all 5 must be counted"

        # THE PROPERTY: warning volume must not scale with call count. Five failed
        # writes must not produce five warnings.
        #
        # ASSERTED PER-CAUSE, NOT AS A TOTAL — and that distinction is the whole
        # history of this assertion. Three versions:
        #
        #   v1: filtered for "Durable probe log write failed" and asserted 1. Blind
        #       to _find_project_root emitting its own warning twice per call from
        #       the same code path — a storm from a sibling function.
        #   v2: asserted the TOTAL was exactly 2 (one per distinct cause). Caught
        #       that storm, and caught a real test-isolation bug (before conftest
        #       cleared _ROOT_WARNING_EMITTED this passed only when an earlier test
        #       had already latched it — i.e. it passed on test ORDER). But it then
        #       failed in the full suite and passed alone, because the two causes log
        #       to DIFFERENT loggers and other tests mutate global logging
        #       configuration (propagation), so the captured total shifts.
        #   v3 (this): assert each cause is latched exactly once, using the signal
        #       each cause actually owns — caplog for the write warning (this
        #       module's own logger), and the module latch itself for the config
        #       warning. Order-independent, and it still fails if either latch is
        #       removed.
        #
        # A test that passes or fails on ORDER is not measuring what it claims
        # (FM-TEST-ECHO-CHAMBER). Asserting on global logging state was the defect.
        write_warnings = [
            r for r in caplog.records if "Durable probe log write failed" in r.message
        ]
        assert len(write_warnings) == 1, (
            f"expected exactly 1 durable-write WARNING for 5 failed calls, got "
            f"{len(write_warnings)}: {[r.message for r in write_warnings]}"
        )
        assert config._ROOT_WARNING_EMITTED is True, (
            "the data-root warning should have latched exactly once; the latch is "
            "asserted directly rather than counted through caplog because that "
            "warning uses a different logger whose propagation other tests mutate"
        )


class TestSafeCwd:
    def test_returns_none_instead_of_raising(self, dead_cwd):
        """The accessor absorbs the unlinked-directory failure.

        Covers: FM-UNGUARDED-CWD-READ
        """
        assert safe_cwd() is None


class TestScopeCheckGetsStricterNotWider:
    """An unavailable cwd must never widen the allowed set.

    A scope check that silently fell back to ``/`` or ``Path.home()`` when it
    could not read cwd would be a security regression, so the direction of the
    degradation is the property under test — not merely that it doesn't crash.
    """

    def test_does_not_raise_on_dead_cwd(self, dead_cwd):
        # Asserted against the permitted list directly rather than a path that
        # happens to sit under BOTH home and tempdir: conftest's isolate_home
        # points $HOME inside pytest's basetemp, so the obvious assertion passed
        # via the tempdir entry and would have survived deleting the home entry.
        assert is_within_allowed_scope(Path.home() / "anything") is True
        assert is_within_allowed_scope(Path(tempfile.gettempdir()) / "x") is True

    def test_still_rejects_out_of_scope_paths_on_dead_cwd(self, dead_cwd):
        # /etc is outside home, temp and (now absent) cwd. It must stay rejected;
        # if a fallback had widened the allowed set to "/", this returns True.
        assert is_within_allowed_scope(Path("/etc")) is False

    def test_root_is_rejected_on_dead_cwd(self, dead_cwd):
        assert is_within_allowed_scope(Path("/")) is False


class TestProjectRootResolution:
    def test_find_project_root_falls_back_instead_of_raising(self, dead_cwd):
        """config.py:75 — reached from the telemetry write path on every call."""
        root = config._find_project_root()
        assert isinstance(root, Path)
        assert root.is_absolute()

    def test_relative_path_setting_fails_loudly_on_dead_cwd(self, dead_cwd):
        """The one cwd site that must NOT degrade quietly.

        A relative write path with no cwd to anchor it has no safe default:
        guessing would point logs or the reference library at a directory the
        operator never named. It raises at Settings construction with an
        actionable message instead.
        """
        from ai_governance_mcp.config import Settings

        with pytest.raises(ValueError, match="working directory is unavailable"):
            Settings(logs_path=Path("relative/logs"))


class TestLogPathValidation:
    def test_validate_log_path_tolerates_dead_cwd(self, dead_cwd):
        """_logging.py:44-45 — where the incident actually raised."""
        from ai_governance_mcp.server._logging import _validate_log_path

        # Home is still a permitted root, so a home-relative log path validates
        # even with no working directory. This is the post-session-270 layout
        # (~/.ai-governance/logs), which is why the pair of fixes compose.
        _validate_log_path(Path.home() / ".ai-governance" / "logs" / "audit.jsonl")

    def test_validate_log_path_still_rejects_out_of_scope_on_dead_cwd(self, dead_cwd):
        from ai_governance_mcp.server._logging import _validate_log_path

        with pytest.raises(ValueError, match="must be within"):
            _validate_log_path(Path("/etc/evil.jsonl"))


class TestTheGapIsVisibleNotJustSurvivable:
    """A degraded audit trail must be reportable, or the fix is merely quiet.

    ``verify_governance_compliance`` answers from the IN-MEMORY deque, so it keeps
    saying COMPLIANT while ``logs/*.jsonl`` develops holes. Those logs are what
    ``/compliance-review`` and ``scripts/analyze_compliance.py`` read, and in a
    log-derived metric a missing record is indistinguishable from "this never
    happened". Without this annotation the two answers diverge silently.
    """

    def test_verify_reports_durable_telemetry_gaps(
        self, reset_server_state, test_settings, dead_cwd
    ):
        import json as _json

        from ai_governance_mcp.models import GovernanceAuditLog
        from ai_governance_mcp.server import _logging, _state
        from ai_governance_mcp.server.handlers.governance import (
            _handle_verify_governance,
        )

        _state._settings = test_settings
        test_settings.logs_path = dead_cwd / "logs"
        _logging._telemetry_failures.clear()

        asyncio.run(
            _logging.log_governance_audit_async(
                GovernanceAuditLog(
                    audit_id="gov-visible",
                    timestamp="2026-07-29T00:00:00+00:00",
                    action="refactor the payment handler",
                    assessment="PROCEED",
                    confidence="high",
                )
            )
        )

        result = asyncio.run(
            _handle_verify_governance(
                {"action_description": "refactor the payment handler"}
            )
        )
        payload = _json.loads(result[0].text)

        assert payload["durable_telemetry_gaps"] == {"governance_audit": 1}
        assert "undercount" in payload["finding"], (
            "the reply must SAY the log-derived metrics are incomplete, not just "
            "carry a field a reader has to notice"
        )

    def test_healthy_process_carries_no_gap_field(
        self, reset_server_state, test_settings
    ):
        """No noise on the happy path — the field appears only when it means something."""
        import json as _json

        from ai_governance_mcp.server import _logging, _state
        from ai_governance_mcp.server.handlers.governance import (
            _handle_verify_governance,
        )

        _state._settings = test_settings
        _logging._telemetry_failures.clear()

        result = asyncio.run(
            _handle_verify_governance({"action_description": "anything at all"})
        )
        payload = _json.loads(result[0].text)
        assert "durable_telemetry_gaps" not in payload


class TestEndToEndThroughTheToolHandler:
    """The contract at the altitude the incident actually occurred.

    Every test above calls ``log_governance_audit_async`` directly. That is one
    layer below where the damage was visible: the session saw
    ``evaluate_governance`` return ``TOOL_ERROR``. Cross-vendor review pointed out
    that asserting on the logging function alone leaves the claim "the tool still
    answers" untested — so this drives the real handler and asserts on its payload.
    """

    @pytest.mark.parametrize(
        "failure",
        [
            FileNotFoundError(2, "No such file or directory"),
            PermissionError(13, "Permission denied"),
            OSError(errno.ENOSPC, "No space left on device"),
            OSError(errno.EROFS, "Read-only file system"),
        ],
        ids=["deleted-cwd", "permissions", "disk-full", "read-only-fs"],
    )
    def test_verdict_survives_any_durable_write_failure(
        self, reset_server_state, test_settings, monkeypatch, failure
    ):
        """Four different filesystem failures, one required outcome: a verdict.

        Parameterised deliberately. The incident was ENOENT, but nothing about the
        fix is specific to it — a full disk or a read-only volume discards a
        governance verdict by exactly the same mechanism, and those need no
        deleted directory to occur.
        """
        import json as _json

        from ai_governance_mcp.server import _logging, _state

        _state._settings = test_settings

        def _boom(*_args, **_kwargs):
            raise failure

        monkeypatch.setattr(_logging, "_write_log_sync", _boom)

        from ai_governance_mcp.models import GovernanceAuditLog

        asyncio.run(
            _logging.log_governance_audit_async(
                GovernanceAuditLog(
                    audit_id="gov-e2e",
                    timestamp="2026-07-29T00:00:00+00:00",
                    action="deploy the billing migration",
                    assessment="PROCEED",
                    confidence="high",
                )
            )
        )

        from ai_governance_mcp.server.handlers.governance import (
            _handle_verify_governance,
        )

        result = asyncio.run(
            _handle_verify_governance(
                {"action_description": "deploy the billing migration"}
            )
        )
        payload = _json.loads(result[0].text)

        assert payload["status"] == "COMPLIANT", (
            f"{type(failure).__name__} discarded the verdict: {payload}"
        )
        assert payload["matching_audit_id"] == "gov-e2e"
        assert payload["durable_telemetry_gaps"] == {"governance_audit": 1}


class TestConfigurationFailsBeforeAnyVerdictExists:
    """Invariants belong at startup; only durability may degrade mid-call.

    The ordering rule both reviewers arrived at independently: compute and commit
    the authoritative verdict plus in-memory enforcement state, THEN do best-effort
    persistence — and let configuration and security invariants fail before the
    first verdict is ever computed.
    """

    def test_traversal_in_configured_path_fails_at_construction(self):
        from ai_governance_mcp.config import Settings

        with pytest.raises(ValueError, match="traversal"):
            Settings(logs_path=Path("/tmp/../tmp/logs"))

    def test_canonical_absolute_path_is_accepted(self):
        from ai_governance_mcp.config import Settings

        s = Settings(logs_path=Path("/tmp/governance-logs"))
        assert s.logs_path == Path("/tmp/governance-logs")


class TestProxyIdentityResolution:
    """enforcement.py's project tag — the exemption that was hiding a crash."""

    def test_env_var_wins_and_cwd_is_not_touched(self, monkeypatch, dead_cwd):
        """The original bug: os.getcwd() was an eagerly-evaluated default.

        So it ran even when GOVERNANCE_PROJECT_PATH was set, and a proxy that
        inherited a deleted directory died at startup regardless of configuration.
        """
        from ai_governance_mcp.enforcement import _resolve_project_identity

        monkeypatch.setenv("GOVERNANCE_PROJECT_PATH", "/explicit/project")
        assert _resolve_project_identity() == "/explicit/project"

    def test_unavailable_cwd_yields_a_never_matching_sentinel(
        self, monkeypatch, dead_cwd
    ):
        """Fail CLOSED, not open.

        ``_state_is_fresh`` reads ``if self.project_path and ...``, so a falsy
        value SKIPS the cross-project rejection — reopening the state leakage
        session-259 fixed. The sentinel must be truthy and must never equal a real
        stored path.
        """
        from ai_governance_mcp.enforcement import _resolve_project_identity

        monkeypatch.delenv("GOVERNANCE_PROJECT_PATH", raising=False)
        identity = _resolve_project_identity()
        assert identity, "a falsy identity would skip the cross-project check"
        assert identity not in ("/", "/tmp", str(Path.home()))
        assert not Path(identity).exists()
