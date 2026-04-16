"""Tests for the Context Engine platform service installer.

Covers:
- Platform detection
- macOS plist generation (watcher + measurement)
- Linux systemd unit generation
- Executable discovery
- CLI argument parsing
- Phase 0 changes: --projects + --max-uptime-hours threading, path validation,
  measurement plist generation, env var string-type assertion.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_governance_mcp.context_engine.service import (
    DEFAULT_MAX_UPTIME_HOURS,
    LINUX_SERVICE_NAME,
    MACOS_LABEL,
    MACOS_MEASURE_LABEL,
    WINDOWS_TASK_NAME,
    _detect_platform,
    _find_watcher_executable,
    _generate_linux_unit,
    _generate_macos_measurement_plist,
    _generate_macos_plist,
    _generate_windows_task_action,
    _linux_unit_path,
    _macos_measure_plist_path,
    _macos_plist_path,
    _validate_project_paths,
)


# =============================================================================
# Platform Detection Tests
# =============================================================================


class TestPlatformDetection:
    """Test platform auto-detection."""

    def test_macos(self):
        with patch.object(sys, "platform", "darwin"):
            assert _detect_platform() == "macos"

    def test_linux(self):
        with patch.object(sys, "platform", "linux"):
            assert _detect_platform() == "linux"

    def test_windows(self):
        with patch.object(sys, "platform", "win32"):
            assert _detect_platform() == "windows"

    def test_unknown_defaults_linux(self):
        with patch.object(sys, "platform", "freebsd12"):
            assert _detect_platform() == "linux"


# =============================================================================
# macOS Plist Generation Tests (Phase 0)
# =============================================================================


class TestMacOSPlistDefaults:
    """Tests for default plist generation (no --projects).

    Phase 0 contract: default install does NOT use --all. Daemon runs
    realtime-filtered (watcher_daemon.py:187 default). Explicit --projects
    in plist is the preferred usage; default-no-flag is the fallback.
    """

    def test_plist_contains_label(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert MACOS_LABEL in plist

    def test_plist_contains_executable(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "/usr/local/bin/context-engine-watcher" in plist

    def test_plist_does_not_contain_all_flag_by_default(self):
        """Phase 0 Finding 4: --all is NOT in plist unless explicitly asked."""
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "--all" not in plist

    def test_plist_run_at_load(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "<key>RunAtLoad</key>" in plist
        assert "<true/>" in plist

    def test_plist_keep_alive(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "<key>KeepAlive</key>" in plist

    def test_plist_log_paths(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "watcher.out.log" in plist
        assert "watcher.err.log" in plist

    def test_plist_throttle_interval(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "<key>ThrottleInterval</key>" in plist
        assert "<integer>30</integer>" in plist

    def test_plist_environment_vars_index_mode(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "AI_CONTEXT_ENGINE_INDEX_MODE" in plist
        assert "realtime" in plist

    def test_plist_environment_vars_max_uptime_default(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS" in plist
        # Phase 0 default is 12; must be written as string value
        assert f"<string>{DEFAULT_MAX_UPTIME_HOURS}</string>" in plist

    def test_plist_max_uptime_is_string_not_integer(self):
        """Contrarian Finding 10: launchd env vars must be strings."""
        plist = _generate_macos_plist(
            "/usr/local/bin/context-engine-watcher", max_uptime_hours=8
        )
        # Assert the value is wrapped in <string> not <integer>
        assert "<string>8</string>" in plist
        # Negative: integer wrapping would be wrong
        assert (
            "<key>AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS</key>\n                <integer>"
            not in plist
        )

    def test_plist_valid_xml_default(self):
        import xml.etree.ElementTree as ET

        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        ET.fromstring(plist)

    def test_plist_module_invocation(self):
        """Module-style executable should split into separate args."""
        plist = _generate_macos_plist(
            "/usr/bin/python -m ai_governance_mcp.context_engine.watcher_daemon"
        )
        assert "/usr/bin/python" in plist
        assert "-m" in plist
        assert "ai_governance_mcp.context_engine.watcher_daemon" in plist

    def test_plist_path(self):
        path = _macos_plist_path()
        assert path.name == f"{MACOS_LABEL}.plist"
        assert "LaunchAgents" in str(path)


class TestMacOSPlistWithProjects:
    """Tests for plist generation WITH explicit --projects (preferred path)."""

    def test_plist_with_single_project(self):
        plist = _generate_macos_plist(
            "/usr/local/bin/context-engine-watcher",
            projects=[Path("/Users/jc/dev/myproject")],
        )
        assert "<string>--projects</string>" in plist
        assert "<string>/Users/jc/dev/myproject</string>" in plist
        assert "--all" not in plist

    def test_plist_with_multiple_projects(self):
        plist = _generate_macos_plist(
            "/usr/local/bin/context-engine-watcher",
            projects=[Path("/a/b"), Path("/c/d")],
        )
        assert "<string>--projects</string>" in plist
        assert "<string>/a/b</string>" in plist
        assert "<string>/c/d</string>" in plist

    def test_plist_with_projects_valid_xml(self):
        import xml.etree.ElementTree as ET

        plist = _generate_macos_plist(
            "/usr/local/bin/context-engine-watcher",
            projects=[Path("/a"), Path("/b")],
        )
        ET.fromstring(plist)

    def test_plist_empty_projects_list_omits_flag(self):
        """Empty list should be equivalent to None: no --projects flag."""
        plist = _generate_macos_plist(
            "/usr/local/bin/context-engine-watcher", projects=[]
        )
        assert "<string>--projects</string>" not in plist
        assert "--all" not in plist

    def test_plist_custom_max_uptime_hours(self):
        plist = _generate_macos_plist(
            "/usr/local/bin/context-engine-watcher", max_uptime_hours=6
        )
        assert "<string>6</string>" in plist


class TestMacOSMeasurementPlist:
    """Tests for the second launchd plist — measurement automation sidecar."""

    def test_measurement_plist_contains_label(self):
        plist = _generate_macos_measurement_plist(
            Path("/Users/jc/dev/repo/scripts/measure-watcher-footprint.sh")
        )
        assert MACOS_MEASURE_LABEL in plist
        assert MACOS_LABEL != MACOS_MEASURE_LABEL

    def test_measurement_plist_contains_script_path(self):
        plist = _generate_macos_measurement_plist(
            Path("/Users/jc/dev/repo/scripts/measure-watcher-footprint.sh")
        )
        assert "/Users/jc/dev/repo/scripts/measure-watcher-footprint.sh" in plist

    def test_measurement_plist_not_keep_alive(self):
        """Measurement is a one-shot job, not a daemon."""
        plist = _generate_macos_measurement_plist(Path("/tmp/script.sh"))
        assert "<key>KeepAlive</key>" in plist
        # The value after KeepAlive should be <false/>, not <true/>
        ka_section = plist[plist.index("<key>KeepAlive</key>") :]
        assert "<false/>" in ka_section[:100]

    def test_measurement_plist_start_calendar_interval(self):
        plist = _generate_macos_measurement_plist(Path("/tmp/script.sh"))
        assert "<key>StartCalendarInterval</key>" in plist
        assert "<key>Hour</key>" in plist
        assert "<integer>4</integer>" in plist
        assert "<key>Minute</key>" in plist
        assert "<integer>0</integer>" in plist

    def test_measurement_plist_not_run_at_load(self):
        plist = _generate_macos_measurement_plist(Path("/tmp/script.sh"))
        ral_section = plist[plist.index("<key>RunAtLoad</key>") :]
        assert "<false/>" in ral_section[:100]

    def test_measurement_plist_valid_xml(self):
        import xml.etree.ElementTree as ET

        plist = _generate_macos_measurement_plist(
            Path("/Users/jc/dev/repo/scripts/measure-watcher-footprint.sh")
        )
        ET.fromstring(plist)

    def test_measurement_plist_path(self):
        path = _macos_measure_plist_path()
        assert path.name == f"{MACOS_MEASURE_LABEL}.plist"
        assert "LaunchAgents" in str(path)


# =============================================================================
# Linux systemd Unit Generation Tests (Phase 0)
# =============================================================================


class TestLinuxUnit:
    """Test Linux systemd user service unit generation."""

    def test_unit_default_exec_start_has_no_all_flag(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "ExecStart=/usr/local/bin/context-engine-watcher" in unit
        assert "--all" not in unit

    def test_unit_with_projects(self):
        unit = _generate_linux_unit(
            "/usr/local/bin/context-engine-watcher",
            projects=[Path("/a/b"), Path("/c/d")],
        )
        assert (
            'ExecStart=/usr/local/bin/context-engine-watcher --projects "/a/b" "/c/d"'
            in unit
        )

    def test_unit_with_empty_projects_list(self):
        unit = _generate_linux_unit(
            "/usr/local/bin/context-engine-watcher", projects=[]
        )
        assert "--projects" not in unit
        assert "--all" not in unit

    def test_unit_restart_on_failure(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "Restart=on-failure" in unit

    def test_unit_restart_delay(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "RestartSec=30" in unit

    def test_unit_memory_limit(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "MemoryMax=512M" in unit

    def test_unit_cpu_limit(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "CPUQuota=25%" in unit

    def test_unit_environment_index_mode(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "Environment=AI_CONTEXT_ENGINE_INDEX_MODE=realtime" in unit

    def test_unit_environment_max_uptime(self):
        unit = _generate_linux_unit(
            "/usr/local/bin/context-engine-watcher", max_uptime_hours=6
        )
        assert "Environment=AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS=6" in unit

    def test_unit_environment_max_uptime_default(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert (
            f"Environment=AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS={DEFAULT_MAX_UPTIME_HOURS}"
            in unit
        )

    def test_unit_install_section(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "[Install]" in unit
        assert "WantedBy=default.target" in unit

    def test_unit_path(self):
        path = _linux_unit_path()
        assert path.name == f"{LINUX_SERVICE_NAME}.service"
        assert "systemd/user" in str(path)


# =============================================================================
# Windows Task Action Generation Tests (Phase 0)
# =============================================================================


class TestWindowsTaskAction:
    """Test the /tr argument builder for schtasks."""

    def test_default_has_no_all_flag(self):
        action = _generate_windows_task_action("C:\\bin\\context-engine-watcher.exe")
        assert "--all" not in action
        assert '"C:\\bin\\context-engine-watcher.exe"' in action

    def test_with_projects(self):
        action = _generate_windows_task_action(
            "C:\\bin\\watcher.exe",
            projects=[Path("C:\\dev\\project1"), Path("C:\\dev\\project2")],
        )
        assert "--projects" in action
        assert "C:\\dev\\project1" in action
        assert "C:\\dev\\project2" in action


# =============================================================================
# Path Validation Tests (Phase 0)
# =============================================================================


class TestValidateProjectPaths:
    """Test _validate_project_paths helper used at install time."""

    def test_none_returns_empty_list(self):
        assert _validate_project_paths(None) == []

    def test_empty_list_returns_empty(self):
        assert _validate_project_paths([]) == []

    def test_valid_path_returns_resolved_absolute(self, tmp_path):
        result = _validate_project_paths([tmp_path])
        assert len(result) == 1
        assert result[0] == tmp_path.resolve()
        assert result[0].is_absolute()

    def test_multiple_valid_paths(self, tmp_path):
        d1 = tmp_path / "a"
        d2 = tmp_path / "b"
        d1.mkdir()
        d2.mkdir()
        result = _validate_project_paths([d1, d2])
        assert len(result) == 2
        assert result[0] == d1.resolve()
        assert result[1] == d2.resolve()

    def test_missing_path_raises_value_error(self, tmp_path):
        nonexistent = tmp_path / "does-not-exist"
        with pytest.raises(ValueError, match="does not exist"):
            _validate_project_paths([nonexistent])

    def test_file_instead_of_directory_raises(self, tmp_path):
        file_path = tmp_path / "file.txt"
        file_path.write_text("hello")
        with pytest.raises(ValueError, match="not a directory"):
            _validate_project_paths([file_path])

    def test_first_missing_path_fails_loud(self, tmp_path):
        valid = tmp_path
        missing = tmp_path / "missing"
        with pytest.raises(ValueError):
            _validate_project_paths([valid, missing])


# =============================================================================
# Executable Discovery Tests
# =============================================================================


class TestExecutableDiscovery:
    """Test finding the watcher executable."""

    def test_finds_on_path(self):
        with patch(
            "shutil.which", return_value="/usr/local/bin/context-engine-watcher"
        ):
            result = _find_watcher_executable()
            assert result == "/usr/local/bin/context-engine-watcher"

    def test_fallback_to_module(self):
        with patch("shutil.which", return_value=None):
            result = _find_watcher_executable()
            assert "-m" in result
            assert "watcher_daemon" in result


# =============================================================================
# CLI Tests (Phase 0)
# =============================================================================


class TestCLI:
    """Test CLI argument parsing — install subcommand gains --projects + --max-uptime-hours."""

    def test_install_command_bare(self):
        parser = _build_test_parser()
        args = parser.parse_args(["install"])
        assert args.command == "install"
        assert args.projects is None
        assert args.max_uptime_hours == DEFAULT_MAX_UPTIME_HOURS

    def test_install_with_single_project(self):
        parser = _build_test_parser()
        args = parser.parse_args(["install", "--projects", "/a/b"])
        assert args.command == "install"
        assert args.projects == ["/a/b"]

    def test_install_with_multiple_projects(self):
        parser = _build_test_parser()
        args = parser.parse_args(["install", "--projects", "/a/b", "/c/d", "/e/f"])
        assert args.projects == ["/a/b", "/c/d", "/e/f"]

    def test_install_with_max_uptime_hours(self):
        parser = _build_test_parser()
        args = parser.parse_args(["install", "--max-uptime-hours", "8"])
        assert args.max_uptime_hours == 8

    def test_install_combined_flags(self):
        parser = _build_test_parser()
        args = parser.parse_args(
            ["install", "--projects", "/a", "--max-uptime-hours", "6"]
        )
        assert args.projects == ["/a"]
        assert args.max_uptime_hours == 6

    def test_uninstall_command(self):
        parser = _build_test_parser()
        args = parser.parse_args(["uninstall"])
        assert args.command == "uninstall"

    def test_status_command(self):
        parser = _build_test_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_logs_command(self):
        parser = _build_test_parser()
        args = parser.parse_args(["logs"])
        assert args.command == "logs"


def _build_test_parser():
    """Build the same parser as main() for testing — mirrors service.main()."""
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("--projects", nargs="+", metavar="PATH")
    install_parser.add_argument(
        "--max-uptime-hours",
        type=int,
        default=DEFAULT_MAX_UPTIME_HOURS,
        metavar="N",
    )
    subparsers.add_parser("uninstall")
    subparsers.add_parser("status")
    subparsers.add_parser("logs")
    return parser


# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Verify service identifier constants."""

    def test_macos_label_format(self):
        assert MACOS_LABEL.startswith("com.")
        assert "context-engine" in MACOS_LABEL

    def test_macos_measure_label_format(self):
        assert MACOS_MEASURE_LABEL.startswith("com.")
        assert "context-engine" in MACOS_MEASURE_LABEL
        assert MACOS_MEASURE_LABEL != MACOS_LABEL

    def test_linux_service_name(self):
        assert LINUX_SERVICE_NAME == "context-engine-watcher"

    def test_windows_task_name(self):
        assert WINDOWS_TASK_NAME == "ContextEngineWatcher"

    def test_default_max_uptime_hours(self):
        assert DEFAULT_MAX_UPTIME_HOURS == 12
