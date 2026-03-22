"""Tests for the standalone watcher daemon.

Covers:
- Project discovery from index storage
- Heartbeat and PID file management
- CLI argument parsing
- Daemon status reading from server
"""

import json
import os
from pathlib import Path
from unittest.mock import patch


from ai_governance_mcp.context_engine.watcher_daemon import (
    _discover_projects,
    _get_base_path,
    _remove_heartbeat,
    _remove_pid_file,
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
