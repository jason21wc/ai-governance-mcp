"""Platform service installer for the Context Engine watcher daemon.

Generates and manages platform-specific service configurations to run
the watcher daemon as a persistent background service.

Supported platforms:
- macOS: launchd (LaunchAgent plist)
- Linux: systemd (user service unit)
- Windows: Task Scheduler (schtasks)

Usage:
    context-engine-service install     # Auto-detect platform, install service
    context-engine-service uninstall   # Remove service
    context-engine-service status      # Check service status
    context-engine-service logs        # Tail service logs
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

logger = logging.getLogger("ai_governance_mcp.context_engine.service")

# Service identifiers
MACOS_LABEL = "com.ai-governance.context-engine-watcher"
LINUX_SERVICE_NAME = "context-engine-watcher"
WINDOWS_TASK_NAME = "ContextEngineWatcher"

# Log directory
LOG_DIR = Path.home() / ".context-engine" / "logs"


def _detect_platform() -> str:
    """Detect the current platform.

    Returns: 'macos', 'linux', or 'windows'.
    """
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        return "linux"  # Best guess for unknown Unix-like


def _find_watcher_executable() -> str:
    """Find the context-engine-watcher executable path."""
    path = shutil.which("context-engine-watcher")
    if path:
        return path
    # Fallback: try Python module invocation
    python = sys.executable
    return f"{python} -m ai_governance_mcp.context_engine.watcher_daemon"


def _ensure_log_dir() -> Path:
    """Create log directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


# =============================================================================
# macOS: launchd
# =============================================================================


def _macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{MACOS_LABEL}.plist"


def _generate_macos_plist(executable: str) -> str:
    """Generate launchd plist XML for macOS."""
    log_dir = _ensure_log_dir()

    # Split executable into command + args if it's a module invocation
    if " -m " in executable:
        parts = executable.split(" ", 2)
        program_args = "\n".join(f"        <string>{p}</string>" for p in parts)
    else:
        program_args = f"        <string>{executable}</string>"

    # Add --all flag to watch all projects
    program_args += "\n        <string>--all</string>"

    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{MACOS_LABEL}</string>
            <key>ProgramArguments</key>
            <array>
        {program_args}
            </array>
            <key>RunAtLoad</key>
            <true/>
            <key>KeepAlive</key>
            <true/>
            <key>ThrottleInterval</key>
            <integer>30</integer>
            <key>StandardOutPath</key>
            <string>{log_dir}/watcher.out.log</string>
            <key>StandardErrorPath</key>
            <string>{log_dir}/watcher.err.log</string>
            <key>EnvironmentVariables</key>
            <dict>
                <key>AI_CONTEXT_ENGINE_INDEX_MODE</key>
                <string>realtime</string>
            </dict>
        </dict>
        </plist>
    """)


def _macos_install() -> bool:
    """Install macOS LaunchAgent."""
    executable = _find_watcher_executable()
    plist_path = _macos_plist_path()
    plist_content = _generate_macos_plist(executable)

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist_content)
    print(f"Wrote plist: {plist_path}")

    # Load the service
    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"Service loaded: {MACOS_LABEL}")
        return True
    else:
        print(f"Failed to load service: {result.stderr.strip()}")
        return False


def _macos_uninstall() -> bool:
    """Uninstall macOS LaunchAgent."""
    plist_path = _macos_plist_path()

    # Unload first
    subprocess.run(
        ["launchctl", "unload", str(plist_path)],
        capture_output=True,
        text=True,
    )

    if plist_path.exists():
        plist_path.unlink()
        print(f"Removed plist: {plist_path}")

    print(f"Service uninstalled: {MACOS_LABEL}")
    return True


def _macos_status() -> dict:
    """Get macOS service status."""
    result = subprocess.run(
        ["launchctl", "list", MACOS_LABEL],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # Parse launchctl list output
        lines = result.stdout.strip().split("\n")
        status = {"installed": True, "platform": "macos", "label": MACOS_LABEL}
        for line in lines:
            if '"PID"' in line or "PID" in line:
                parts = line.strip().strip(";").split("=")
                if len(parts) == 2:
                    try:
                        status["pid"] = int(parts[1].strip().strip(";"))
                    except ValueError:
                        pass
        status["running"] = "pid" in status
        return status
    else:
        return {
            "installed": _macos_plist_path().exists(),
            "running": False,
            "platform": "macos",
            "label": MACOS_LABEL,
        }


def _macos_logs() -> None:
    """Tail macOS service logs."""
    log_file = LOG_DIR / "watcher.err.log"
    if log_file.exists():
        subprocess.run(["tail", "-f", "-n", "50", str(log_file)])
    else:
        print(f"No log file found at {log_file}")


# =============================================================================
# Linux: systemd
# =============================================================================


def _linux_unit_path() -> Path:
    return (
        Path.home() / ".config" / "systemd" / "user" / f"{LINUX_SERVICE_NAME}.service"
    )


def _generate_linux_unit(executable: str) -> str:
    """Generate systemd user service unit file."""
    return textwrap.dedent(f"""\
        [Unit]
        Description=Context Engine File Watcher Daemon
        After=default.target

        [Service]
        Type=simple
        ExecStart={executable} --all
        Restart=on-failure
        RestartSec=30
        Environment=AI_CONTEXT_ENGINE_INDEX_MODE=realtime
        MemoryMax=512M
        CPUQuota=25%

        [Install]
        WantedBy=default.target
    """)


def _linux_install() -> bool:
    """Install Linux systemd user service."""
    executable = _find_watcher_executable()
    unit_path = _linux_unit_path()
    unit_content = _generate_linux_unit(executable)

    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(unit_content)
    print(f"Wrote unit file: {unit_path}")

    # Reload and enable
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    result = subprocess.run(
        ["systemctl", "--user", "enable", "--now", LINUX_SERVICE_NAME],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"Service enabled and started: {LINUX_SERVICE_NAME}")
        print(
            "Note: Run 'sudo loginctl enable-linger $USER' to keep "
            "the service running after logout."
        )
        return True
    else:
        print(f"Failed to enable service: {result.stderr.strip()}")
        return False


def _linux_uninstall() -> bool:
    """Uninstall Linux systemd user service."""
    subprocess.run(
        ["systemctl", "--user", "disable", "--now", LINUX_SERVICE_NAME],
        capture_output=True,
    )
    unit_path = _linux_unit_path()
    if unit_path.exists():
        unit_path.unlink()
        print(f"Removed unit file: {unit_path}")
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    print(f"Service uninstalled: {LINUX_SERVICE_NAME}")
    return True


def _linux_status() -> dict:
    """Get Linux service status."""
    result = subprocess.run(
        ["systemctl", "--user", "is-active", LINUX_SERVICE_NAME],
        capture_output=True,
        text=True,
    )
    is_active = result.stdout.strip() == "active"

    result2 = subprocess.run(
        ["systemctl", "--user", "is-enabled", LINUX_SERVICE_NAME],
        capture_output=True,
        text=True,
    )
    is_enabled = result2.stdout.strip() == "enabled"

    return {
        "installed": _linux_unit_path().exists(),
        "running": is_active,
        "enabled": is_enabled,
        "platform": "linux",
        "service": LINUX_SERVICE_NAME,
    }


def _linux_logs() -> None:
    """Tail Linux service logs."""
    subprocess.run(["journalctl", "--user", "-u", LINUX_SERVICE_NAME, "-f", "-n", "50"])


# =============================================================================
# Windows: Task Scheduler
# =============================================================================


def _windows_install() -> bool:
    """Install Windows scheduled task."""
    executable = _find_watcher_executable()
    _ensure_log_dir()

    result = subprocess.run(
        [
            "schtasks",
            "/create",
            "/tn",
            WINDOWS_TASK_NAME,
            "/tr",
            f'"{executable}" --all',
            "/sc",
            "onlogon",
            "/rl",
            "limited",
            "/f",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"Task created: {WINDOWS_TASK_NAME}")
        # Start it immediately
        subprocess.run(
            ["schtasks", "/run", "/tn", WINDOWS_TASK_NAME],
            capture_output=True,
        )
        return True
    else:
        print(f"Failed to create task: {result.stderr.strip()}")
        return False


def _windows_uninstall() -> bool:
    """Uninstall Windows scheduled task."""
    # End the task first
    subprocess.run(
        ["schtasks", "/end", "/tn", WINDOWS_TASK_NAME],
        capture_output=True,
    )
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", WINDOWS_TASK_NAME, "/f"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"Task removed: {WINDOWS_TASK_NAME}")
        return True
    else:
        print(f"Failed to remove task: {result.stderr.strip()}")
        return False


def _windows_status() -> dict:
    """Get Windows task status."""
    result = subprocess.run(
        ["schtasks", "/query", "/tn", WINDOWS_TASK_NAME, "/fo", "csv", "/nh"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        parts = result.stdout.strip().split(",")
        status_text = parts[2].strip('"') if len(parts) > 2 else "Unknown"
        return {
            "installed": True,
            "running": status_text == "Running",
            "status_text": status_text,
            "platform": "windows",
            "task": WINDOWS_TASK_NAME,
        }
    return {
        "installed": False,
        "running": False,
        "platform": "windows",
        "task": WINDOWS_TASK_NAME,
    }


def _windows_logs() -> None:
    """Show Windows watcher logs."""
    log_file = LOG_DIR / "watcher.err.log"
    if log_file.exists():
        # Windows doesn't have tail -f, use PowerShell
        subprocess.run(
            ["powershell", "-Command", f"Get-Content -Tail 50 -Wait '{log_file}'"]
        )
    else:
        print(f"No log file found at {log_file}")


# =============================================================================
# Dispatch
# =============================================================================

_PLATFORM_HANDLERS = {
    "macos": {
        "install": _macos_install,
        "uninstall": _macos_uninstall,
        "status": _macos_status,
        "logs": _macos_logs,
    },
    "linux": {
        "install": _linux_install,
        "uninstall": _linux_uninstall,
        "status": _linux_status,
        "logs": _linux_logs,
    },
    "windows": {
        "install": _windows_install,
        "uninstall": _windows_uninstall,
        "status": _windows_status,
        "logs": _windows_logs,
    },
}


def _cmd_install(platform: str) -> None:
    handlers = _PLATFORM_HANDLERS[platform]
    print(f"Installing Context Engine watcher service ({platform})...")
    success = handlers["install"]()
    if success:
        print("\nService installed successfully.")
        print("The watcher daemon will start automatically on login.")
        print("Run 'context-engine-service status' to verify.")
    else:
        sys.exit(1)


def _cmd_uninstall(platform: str) -> None:
    handlers = _PLATFORM_HANDLERS[platform]
    print(f"Uninstalling Context Engine watcher service ({platform})...")
    handlers["uninstall"]()


def _cmd_status(platform: str) -> None:
    handlers = _PLATFORM_HANDLERS[platform]
    status = handlers["status"]()
    print(json.dumps(status, indent=2))

    # Also check heartbeat
    heartbeat_path = Path.home() / ".context-engine" / "watcher-heartbeat.json"
    if heartbeat_path.exists():
        try:
            data = json.loads(heartbeat_path.read_text())
            print(
                f"\nDaemon heartbeat: PID {data.get('pid')}, "
                f"watching {data.get('projects_watched')} projects, "
                f"last alive: {data.get('alive_at')}"
            )
        except (json.JSONDecodeError, OSError):
            pass


def _cmd_logs(platform: str) -> None:
    handlers = _PLATFORM_HANDLERS[platform]
    handlers["logs"]()


def main() -> None:
    """CLI entry point for context-engine-service."""
    parser = argparse.ArgumentParser(
        prog="context-engine-service",
        description="Manage the Context Engine watcher daemon as a system service.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("install", help="Install and start the watcher service")
    subparsers.add_parser("uninstall", help="Stop and remove the watcher service")
    subparsers.add_parser("status", help="Check service status")
    subparsers.add_parser("logs", help="Tail service logs")

    args = parser.parse_args()
    platform = _detect_platform()

    commands = {
        "install": _cmd_install,
        "uninstall": _cmd_uninstall,
        "status": _cmd_status,
        "logs": _cmd_logs,
    }
    commands[args.command](platform)


if __name__ == "__main__":
    main()
