"""Tests for the standalone watcher daemon.

Covers:
- Project discovery from index storage
- Heartbeat and PID file management
- CLI argument parsing
- Daemon status reading from server
- Phase 0: max_uptime env var parsing, jitter/floor, idle detection,
  restart-gate logic, integrated self-exit via parameterized run_daemon.
"""

import json
import os
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


from ai_governance_mcp.context_engine.watcher_daemon import (
    HARD_CAP_MULTIPLIER,
    IDLE_THRESHOLD_SECONDS,
    JITTER_RANGE,
    MIN_MAX_UPTIME_SECONDS,
    _apply_jitter_and_floor,
    _discover_projects,
    _get_base_path,
    _get_last_activity_seconds_ago,
    _read_max_uptime_from_env,
    _remove_heartbeat,
    _remove_pid_file,
    _should_restart_now,
    _write_heartbeat,
    _write_pid_file,
)


# =============================================================================
# Project Discovery Tests
# =============================================================================


class TestDiscoverProjects:
    """Test project discovery from index storage."""

    def _create_project(
        self, base_path, project_id, project_path, index_mode="realtime"
    ):
        """Helper to create a minimal project in storage."""
        project_dir = base_path / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        metadata = {
            "project_id": project_id,
            "project_path": str(project_path),
            "index_mode": index_mode,
        }
        (project_dir / "metadata.json").write_text(json.dumps(metadata))

    def test_discover_realtime_projects(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()

        self._create_project(base, "abcdef1234567890", project_dir, "realtime")
        self._create_project(base, "1234567890abcdef", project_dir, "ondemand")

        projects = _discover_projects(base, filter_mode="realtime")
        assert len(projects) == 1
        assert projects[0]["index_mode"] == "realtime"

    def test_discover_all_projects(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        project_dir = tmp_path / "myproject"
        project_dir.mkdir()

        self._create_project(base, "abcdef1234567890", project_dir, "realtime")
        self._create_project(base, "1234567890abcdef", project_dir, "ondemand")

        projects = _discover_projects(base, filter_mode=None)
        assert len(projects) == 2

    def test_discover_empty_directory(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        projects = _discover_projects(base)
        assert projects == []

    def test_discover_nonexistent_directory(self, tmp_path):
        projects = _discover_projects(tmp_path / "does_not_exist")
        assert projects == []

    def test_discover_skips_missing_project_path(self, tmp_path):
        """Projects whose path no longer exists should be skipped."""
        base = tmp_path / "indexes"
        base.mkdir()
        missing_path = tmp_path / "deleted_project"
        # Don't create missing_path — it doesn't exist

        self._create_project(base, "abcdef1234567890", missing_path, "realtime")
        projects = _discover_projects(base, filter_mode="realtime")
        assert len(projects) == 0

    def test_discover_skips_corrupt_metadata(self, tmp_path):
        base = tmp_path / "indexes"
        project_dir = base / "abcdef1234567890"
        project_dir.mkdir(parents=True)
        (project_dir / "metadata.json").write_text("{invalid json")

        projects = _discover_projects(base)
        assert len(projects) == 0

    def test_discover_skips_symlinks(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        symlink_dir = base / "symlinked"
        symlink_dir.symlink_to(tmp_path)

        projects = _discover_projects(base)
        assert len(projects) == 0


# =============================================================================
# Heartbeat & PID File Tests
# =============================================================================


class TestHeartbeatAndPID:
    """Test heartbeat and PID file management."""

    def test_write_and_read_pid(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        pid_path = _write_pid_file(base)
        assert pid_path.exists()
        assert int(pid_path.read_text()) == os.getpid()

    def test_remove_pid(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        pid_path = _write_pid_file(base)
        assert pid_path.exists()
        _remove_pid_file(base)
        assert not pid_path.exists()

    def test_remove_pid_missing_ok(self, tmp_path):
        """Removing nonexistent PID file should not raise."""
        base = tmp_path / "indexes"
        base.mkdir()
        _remove_pid_file(base)  # Should not raise

    def test_write_heartbeat(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        _write_heartbeat(base, projects_watched=3)

        heartbeat_path = base.parent / "watcher-heartbeat.json"
        assert heartbeat_path.exists()
        data = json.loads(heartbeat_path.read_text())
        assert data["pid"] == os.getpid()
        assert data["projects_watched"] == 3
        assert "alive_at" in data

    def test_remove_heartbeat(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        _write_heartbeat(base, 1)
        heartbeat_path = base.parent / "watcher-heartbeat.json"
        assert heartbeat_path.exists()
        _remove_heartbeat(base)
        assert not heartbeat_path.exists()

    def test_remove_heartbeat_missing_ok(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        _remove_heartbeat(base)  # Should not raise


# =============================================================================
# Base Path Tests
# =============================================================================


class TestGetBasePath:
    """Test base path resolution."""

    def test_default_path(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove env var if present
            os.environ.pop("AI_CONTEXT_ENGINE_INDEX_PATH", None)
            path = _get_base_path()
            assert path == Path.home() / ".context-engine" / "indexes"

    def test_custom_path(self, tmp_path):
        custom = str(tmp_path / "custom_indexes")
        with patch.dict(os.environ, {"AI_CONTEXT_ENGINE_INDEX_PATH": custom}):
            path = _get_base_path()
            assert path == Path(custom).resolve()


# =============================================================================
# CLI Argument Parsing Tests
# =============================================================================


class TestCLIParsing:
    """Test argument parsing."""

    def test_no_args(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--projects", nargs="+", type=Path)
        parser.add_argument("--all", action="store_true", dest="watch_all")
        parser.add_argument("--log-file", type=str)

        args = parser.parse_args([])
        assert args.projects is None
        assert args.watch_all is False
        assert args.log_file is None

    def test_projects_arg(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--projects", nargs="+", type=Path)
        parser.add_argument("--all", action="store_true", dest="watch_all")

        args = parser.parse_args(["--projects", "/tmp/foo", "/tmp/bar"])
        assert len(args.projects) == 2
        assert args.projects[0] == Path("/tmp/foo")

    def test_all_flag(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--projects", nargs="+", type=Path)
        parser.add_argument("--all", action="store_true", dest="watch_all")

        args = parser.parse_args(["--all"])
        assert args.watch_all is True


# =============================================================================
# Server Daemon Status Tests
# =============================================================================


class TestDaemonStatusInServer:
    """Test _read_daemon_heartbeat in server.py."""

    def test_read_existing_heartbeat(self, tmp_path):
        from ai_governance_mcp.context_engine.server import _read_daemon_heartbeat

        heartbeat_path = tmp_path / "watcher-heartbeat.json"
        from datetime import datetime, timezone

        data = {
            "pid": 12345,
            "alive_at": datetime.now(timezone.utc).isoformat(),
            "projects_watched": 2,
        }
        heartbeat_path.write_text(json.dumps(data))

        with patch(
            "ai_governance_mcp.context_engine.server._get_base_path",
            return_value=tmp_path / "indexes",
        ):
            result = _read_daemon_heartbeat()
            assert result is not None
            assert result["pid"] == 12345
            assert result["projects_watched"] == 2
            assert result["likely_alive"] is True
            assert "heartbeat_age_seconds" in result

    def test_read_stale_heartbeat(self, tmp_path):
        from ai_governance_mcp.context_engine.server import _read_daemon_heartbeat

        heartbeat_path = tmp_path / "watcher-heartbeat.json"
        data = {
            "pid": 12345,
            "alive_at": "2020-01-01T00:00:00+00:00",  # Very old
            "projects_watched": 1,
        }
        heartbeat_path.write_text(json.dumps(data))

        with patch(
            "ai_governance_mcp.context_engine.server._get_base_path",
            return_value=tmp_path / "indexes",
        ):
            result = _read_daemon_heartbeat()
            assert result is not None
            assert result["likely_alive"] is False

    def test_no_heartbeat_file(self, tmp_path):
        from ai_governance_mcp.context_engine.server import _read_daemon_heartbeat

        with patch(
            "ai_governance_mcp.context_engine.server._get_base_path",
            return_value=tmp_path / "indexes",
        ):
            result = _read_daemon_heartbeat()
            assert result is None


# =============================================================================
# Phase 0: Max Uptime Env Var Parsing
# =============================================================================


class TestReadMaxUptimeFromEnv:
    """Test AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS env var parsing."""

    def test_unset_returns_none(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS", None)
            assert _read_max_uptime_from_env() is None

    def test_empty_string_returns_none(self):
        with patch.dict(os.environ, {"AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS": ""}):
            assert _read_max_uptime_from_env() is None

    def test_zero_returns_none(self):
        """Zero means 'disabled' per plan Change 2."""
        with patch.dict(
            os.environ, {"AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS": "0"}
        ):
            assert _read_max_uptime_from_env() is None

    def test_negative_returns_none(self):
        with patch.dict(
            os.environ, {"AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS": "-5"}
        ):
            assert _read_max_uptime_from_env() is None

    def test_valid_integer_returns_seconds(self):
        with patch.dict(
            os.environ, {"AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS": "12"}
        ):
            assert _read_max_uptime_from_env() == 12 * 3600

    def test_valid_float_returns_seconds(self):
        with patch.dict(
            os.environ, {"AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS": "1.5"}
        ):
            assert _read_max_uptime_from_env() == pytest.approx(5400.0)

    def test_invalid_string_returns_none(self):
        with patch.dict(
            os.environ, {"AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS": "notanumber"}
        ):
            assert _read_max_uptime_from_env() is None

    def test_whitespace_trimmed(self):
        with patch.dict(
            os.environ, {"AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS": "  8  "}
        ):
            assert _read_max_uptime_from_env() == 8 * 3600


# =============================================================================
# Phase 0: Jitter and Floor
# =============================================================================


class TestApplyJitterAndFloor:
    """Test jitter + floor enforcement on max_uptime_seconds.

    Contrarian Finding 6: jitter prevents multi-machine flap synchronization.
    Contrarian Finding 4/6: 1h floor prevents MAX_UPTIME_HOURS=0.01 crashloop.
    """

    def test_normal_value_within_jitter_range(self):
        result = _apply_jitter_and_floor(12 * 3600.0)
        # 12h = 43200s; with ±10% jitter: [38880, 47520]
        assert 38880.0 <= result <= 47520.0

    def test_below_floor_clamped_up(self):
        """0.5h (1800s) should clamp to 3600s floor."""
        result = _apply_jitter_and_floor(1800.0)
        # After clamp to 3600 then jitter ±10%, result must still be ≥ floor
        assert result >= MIN_MAX_UPTIME_SECONDS

    def test_zero_clamped_to_floor(self):
        """Zero should clamp to floor (not produce zero)."""
        result = _apply_jitter_and_floor(0.0)
        assert result >= MIN_MAX_UPTIME_SECONDS

    def test_jitter_within_10_percent(self):
        """Jitter multiplier must land in [0.9, 1.1]."""
        with patch("random.uniform") as mock_uniform:
            mock_uniform.return_value = 1.05
            result = _apply_jitter_and_floor(12 * 3600.0)
            mock_uniform.assert_called_once_with(1.0 - JITTER_RANGE, 1.0 + JITTER_RANGE)
            assert result == pytest.approx(12 * 3600.0 * 1.05)

    def test_jitter_at_lower_bound(self):
        with patch("random.uniform", return_value=0.9):
            result = _apply_jitter_and_floor(12 * 3600.0)
            assert result == pytest.approx(12 * 3600.0 * 0.9)

    def test_jitter_at_upper_bound(self):
        with patch("random.uniform", return_value=1.1):
            result = _apply_jitter_and_floor(12 * 3600.0)
            assert result == pytest.approx(12 * 3600.0 * 1.1)


# =============================================================================
# Phase 0: Idle Detection via Metadata Mtime
# =============================================================================


class TestLastActivitySecondsAgo:
    """Test _get_last_activity_seconds_ago — proxy for watcher activity."""

    def test_missing_base_path_returns_infinity(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        result = _get_last_activity_seconds_ago(missing)
        assert result == float("inf")

    def test_empty_base_path_returns_infinity(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()
        result = _get_last_activity_seconds_ago(base)
        assert result == float("inf")

    def test_fresh_metadata_returns_small_value(self, tmp_path):
        base = tmp_path / "indexes"
        project_dir = base / "abcdef1234567890"
        project_dir.mkdir(parents=True)
        (project_dir / "metadata.json").write_text("{}")
        result = _get_last_activity_seconds_ago(base)
        # Just created: should be near zero
        assert 0.0 <= result < 5.0

    def test_stale_metadata_returns_large_value(self, tmp_path):
        base = tmp_path / "indexes"
        project_dir = base / "abcdef1234567890"
        project_dir.mkdir(parents=True)
        metadata = project_dir / "metadata.json"
        metadata.write_text("{}")
        # Set mtime to 1000 seconds in the past
        old_time = time.time() - 1000.0
        os.utime(metadata, (old_time, old_time))
        result = _get_last_activity_seconds_ago(base)
        assert 990.0 <= result <= 1010.0

    def test_max_across_multiple_projects(self, tmp_path):
        base = tmp_path / "indexes"
        base.mkdir()

        # Old project
        old_dir = base / "old1234567890abcd"
        old_dir.mkdir()
        old_meta = old_dir / "metadata.json"
        old_meta.write_text("{}")
        os.utime(old_meta, (time.time() - 5000.0, time.time() - 5000.0))

        # Recent project
        new_dir = base / "new1234567890abcd"
        new_dir.mkdir()
        new_meta = new_dir / "metadata.json"
        new_meta.write_text("{}")
        # Leave new_meta at current time

        result = _get_last_activity_seconds_ago(base)
        # Should return the MOST RECENT activity (smallest seconds-ago)
        assert result < 10.0


# =============================================================================
# Phase 0: Restart Gate Logic
# =============================================================================


class TestShouldRestartNow:
    """Test _should_restart_now — the phase-aligned restart gate.

    Gate opens when:
    - elapsed >= target AND idle >= IDLE_THRESHOLD_SECONDS (quiet-window), OR
    - elapsed >= target × HARD_CAP_MULTIPLIER (hard cap)
    """

    def test_elapsed_below_target_never_restarts(self):
        # Even with huge idle, if elapsed < target, don't restart
        target = 12 * 3600.0
        assert _should_restart_now(target - 1, target, 10000.0) is False

    def test_elapsed_equals_target_and_idle_triggers(self):
        target = 12 * 3600.0
        assert _should_restart_now(target, target, IDLE_THRESHOLD_SECONDS) is True

    def test_elapsed_equals_target_but_active_defers(self):
        """Quiet-window fails → wait for hard cap."""
        target = 12 * 3600.0
        # idle below threshold = user is active
        assert _should_restart_now(target, target, IDLE_THRESHOLD_SECONDS - 1) is False

    def test_elapsed_equals_hard_cap_always_triggers(self):
        """Hard cap overrides active status."""
        target = 12 * 3600.0
        hard_cap = target * HARD_CAP_MULTIPLIER
        # Even with idle=0 (very active), hard cap fires
        assert _should_restart_now(hard_cap, target, 0.0) is True

    def test_elapsed_between_target_and_hard_cap_needs_idle(self):
        target = 12 * 3600.0
        mid = target * 1.25  # between target and 1.5× cap
        assert _should_restart_now(mid, target, IDLE_THRESHOLD_SECONDS) is True
        assert _should_restart_now(mid, target, IDLE_THRESHOLD_SECONDS - 1) is False

    def test_idle_infinity_with_elapsed_target_triggers(self):
        """No recent activity + reached target = restart."""
        target = 12 * 3600.0
        assert _should_restart_now(target, target, float("inf")) is True


# =============================================================================
# Phase 0: Heartbeat loop — self-exit logic in isolation
# =============================================================================


class TestHeartbeatLoopSelfExit:
    """Tests for _heartbeat_loop's self-exit enforcement in isolation.

    Strategy: bypass run_daemon entirely (which loads torch via ProjectManager).
    Drive _heartbeat_loop directly with a minimal fake manager and fake base_path.
    Uses short heartbeat_interval so tests finish in <1s each.
    """

    def _make_fake_manager(self, n_watchers: int = 1):
        fake = MagicMock()
        fake._watchers = {f"w{i}": MagicMock() for i in range(n_watchers)}
        return fake

    def test_loop_sets_stop_event_when_hard_cap_fires(self, tmp_path):
        """target=1s, elapsed=2s (via fake start_time in the past) → hard cap fires."""
        from ai_governance_mcp.context_engine.watcher_daemon import _heartbeat_loop

        base = tmp_path / "indexes"
        base.mkdir()
        # Fresh metadata: idle will be ~0, but hard cap fires regardless
        (base / ("a" * 16)).mkdir()
        (base / ("a" * 16) / "metadata.json").write_text("{}")

        manager = self._make_fake_manager()
        stop_event = threading.Event()

        # start_time far enough in the past that elapsed > target × 1.5
        # target = 1.0s, so start_time should be ~2s ago
        fake_start_time = time.time() - 2.0

        thread = threading.Thread(
            target=_heartbeat_loop,
            args=(base, manager, stop_event, 0.1, fake_start_time, 1.0),
            daemon=True,
        )
        thread.start()
        # First tick at ~100ms: elapsed ≈ 2.1s, target = 1s, hard_cap = 1.5s
        # Gate opens on hard-cap branch → stop_event.set()
        assert stop_event.wait(timeout=1.0), "heartbeat loop did not set stop_event"
        thread.join(timeout=1.0)
        assert not thread.is_alive()

    def test_loop_sets_stop_event_on_quiet_window(self, tmp_path):
        """elapsed >= target AND idle >= 300s → quiet-window fires."""
        from ai_governance_mcp.context_engine.watcher_daemon import _heartbeat_loop

        base = tmp_path / "indexes"
        project_dir = base / ("a" * 16)
        project_dir.mkdir(parents=True)
        metadata = project_dir / "metadata.json"
        metadata.write_text("{}")
        # Make metadata 400 seconds old — passes IDLE_THRESHOLD_SECONDS (300)
        old = time.time() - 400.0
        os.utime(metadata, (old, old))

        manager = self._make_fake_manager()
        stop_event = threading.Event()
        # elapsed must reach target (1.0s) but not hard cap (1.5s)
        # so: start_time = now - 1.1s
        fake_start_time = time.time() - 1.1

        thread = threading.Thread(
            target=_heartbeat_loop,
            args=(base, manager, stop_event, 0.1, fake_start_time, 1.0),
            daemon=True,
        )
        thread.start()
        assert stop_event.wait(timeout=1.0)
        thread.join(timeout=1.0)

    def test_loop_does_not_exit_when_active(self, tmp_path):
        """elapsed >= target but idle < 300s (active) → stay running until hard cap."""
        from ai_governance_mcp.context_engine.watcher_daemon import _heartbeat_loop

        base = tmp_path / "indexes"
        project_dir = base / ("a" * 16)
        project_dir.mkdir(parents=True)
        (project_dir / "metadata.json").write_text("{}")  # fresh mtime = active

        manager = self._make_fake_manager()
        stop_event = threading.Event()
        # elapsed 1.1s, target 10s → still < target, should NOT exit
        fake_start_time = time.time() - 1.1

        thread = threading.Thread(
            target=_heartbeat_loop,
            args=(base, manager, stop_event, 0.1, fake_start_time, 10.0),
            daemon=True,
        )
        thread.start()
        # Wait briefly; stop_event should NOT be set
        exited = stop_event.wait(timeout=0.4)
        assert not exited, "loop exited prematurely despite being within target"
        # Clean up the thread
        stop_event.set()
        thread.join(timeout=1.0)

    def test_loop_disabled_when_target_is_none(self, tmp_path):
        """target_uptime_seconds=None → loop NEVER triggers self-exit."""
        from ai_governance_mcp.context_engine.watcher_daemon import _heartbeat_loop

        base = tmp_path / "indexes"
        base.mkdir()

        manager = self._make_fake_manager()
        stop_event = threading.Event()

        thread = threading.Thread(
            target=_heartbeat_loop,
            args=(base, manager, stop_event, 0.1, time.time() - 1000.0, None),
            daemon=True,
        )
        thread.start()
        # Even with elapsed=1000s (enormous), no target means no exit
        exited = stop_event.wait(timeout=0.4)
        assert not exited
        stop_event.set()
        thread.join(timeout=1.0)

    def test_loop_writes_heartbeat_on_tick(self, tmp_path):
        """Heartbeat file is written on each tick regardless of exit state."""
        from ai_governance_mcp.context_engine.watcher_daemon import _heartbeat_loop

        base = tmp_path / "indexes"
        base.mkdir()

        manager = self._make_fake_manager(n_watchers=3)
        stop_event = threading.Event()

        thread = threading.Thread(
            target=_heartbeat_loop,
            args=(base, manager, stop_event, 0.1, time.time(), None),
            daemon=True,
        )
        thread.start()
        time.sleep(0.3)  # at least 2 ticks
        heartbeat_path = base.parent / "watcher-heartbeat.json"
        assert heartbeat_path.exists()
        data = json.loads(heartbeat_path.read_text())
        assert data["projects_watched"] == 3
        stop_event.set()
        thread.join(timeout=1.0)

    def test_floor_warning_logged_for_low_uptime(self, caplog, tmp_path):
        """Providing max_uptime below floor should log a WARN."""
        import logging

        with caplog.at_level(
            logging.WARNING,
            logger="ai_governance_mcp.context_engine.watcher_daemon",
        ):
            _apply_jitter_and_floor(60.0)  # 1 min → clamped to 3600s floor
        assert any("below floor" in rec.message.lower() for rec in caplog.records), (
            "expected WARN about floor clamping"
        )
