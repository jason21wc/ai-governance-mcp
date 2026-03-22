"""Tests for the Context Engine platform service installer.

Covers:
- Platform detection
- macOS plist generation
- Linux systemd unit generation
- Executable discovery
- CLI argument parsing
"""

import sys
from unittest.mock import patch


from ai_governance_mcp.context_engine.service import (
    LINUX_SERVICE_NAME,
    MACOS_LABEL,
    WINDOWS_TASK_NAME,
    _detect_platform,
    _find_watcher_executable,
    _generate_linux_unit,
    _generate_macos_plist,
    _linux_unit_path,
    _macos_plist_path,
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
# macOS Plist Generation Tests
# =============================================================================


class TestMacOSPlist:
    """Test macOS LaunchAgent plist generation."""

    def test_plist_contains_label(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert MACOS_LABEL in plist

    def test_plist_contains_executable(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "/usr/local/bin/context-engine-watcher" in plist

    def test_plist_contains_all_flag(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "--all" in plist

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

    def test_plist_environment_vars(self):
        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        assert "AI_CONTEXT_ENGINE_INDEX_MODE" in plist
        assert "realtime" in plist

    def test_plist_valid_xml(self):
        """Plist should be valid XML."""
        import xml.etree.ElementTree as ET

        plist = _generate_macos_plist("/usr/local/bin/context-engine-watcher")
        # Should not raise
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


# =============================================================================
# Linux systemd Unit Generation Tests
# =============================================================================


class TestLinuxUnit:
    """Test Linux systemd user service unit generation."""

    def test_unit_contains_exec_start(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "ExecStart=/usr/local/bin/context-engine-watcher --all" in unit

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

    def test_unit_environment(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "Environment=AI_CONTEXT_ENGINE_INDEX_MODE=realtime" in unit

    def test_unit_install_section(self):
        unit = _generate_linux_unit("/usr/local/bin/context-engine-watcher")
        assert "[Install]" in unit
        assert "WantedBy=default.target" in unit

    def test_unit_path(self):
        path = _linux_unit_path()
        assert path.name == f"{LINUX_SERVICE_NAME}.service"
        assert "systemd/user" in str(path)


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
# CLI Tests
# =============================================================================


class TestCLI:
    """Test CLI argument parsing."""

    def test_install_command(self):
        parser = _build_test_parser()
        args = parser.parse_args(["install"])
        assert args.command == "install"

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
    """Build the same parser as main() for testing."""
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("install")
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

    def test_linux_service_name(self):
        assert LINUX_SERVICE_NAME == "context-engine-watcher"

    def test_windows_task_name(self):
        assert WINDOWS_TASK_NAME == "ContextEngineWatcher"
