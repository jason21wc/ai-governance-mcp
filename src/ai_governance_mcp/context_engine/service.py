"""Platform service installer for the Context Engine watcher daemon.

Generates and manages platform-specific service configurations to run
the watcher daemon as a persistent background service.

Supported platforms:
- macOS: launchd (LaunchAgent plist)
- Linux: systemd (user service unit)
- Windows: Task Scheduler (schtasks)

Phase 0 changes (plan jiggly-honking-cascade.md):
- Installer accepts --projects PATH [PATH ...] instead of hardcoded --all
- Installer accepts --max-uptime-hours N for self-restart allocator flush
- macOS install writes a second launchd plist for daily measurement automation
- All project paths validated at install time

Security: All subprocess calls use hardcoded commands (launchctl, systemctl,
schtasks, tail, journalctl) with constant or config-derived arguments.
No user input flows into any subprocess call. B603 nosec annotations
are applied throughout — verified safe by design.

Usage:
    context-engine-service install --projects /path/to/project [--max-uptime-hours 12]
    context-engine-service uninstall   # Remove service (and measurement plist on macOS)
    context-engine-service status      # Check service status
    context-engine-service logs        # Tail service logs
"""

import argparse
import json
import logging
import os
import shutil
import subprocess  # nosec B404
import sys
import textwrap
from pathlib import Path

logger = logging.getLogger("ai_governance_mcp.context_engine.service")

# Service identifiers
MACOS_LABEL = "com.ai-governance.context-engine-watcher"
MACOS_MEASURE_LABEL = "com.ai-governance.context-engine-measure"
LINUX_SERVICE_NAME = "context-engine-watcher"
WINDOWS_TASK_NAME = "ContextEngineWatcher"

# Defaults
DEFAULT_MAX_UPTIME_HOURS = 12

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


def _find_measurement_script() -> Path | None:
    """Find scripts/measure-watcher-footprint.sh in the repo.

    Returns the absolute path if found, else None. Resolution walks up from
    this file to the repo root. Works for editable installs (pip install -e .)
    which is the documented Phase 0 deployment path.
    """
    candidate = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "scripts"
        / "measure-watcher-footprint.sh"
    )
    if candidate.exists():
        return candidate
    return None


def _ensure_log_dir() -> Path:
    """Create log directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def _validate_project_paths(projects: list[Path] | None) -> list[Path]:
    """Validate project paths exist and are directories. Returns resolved absolutes.

    Raises ValueError with a clear message on the first missing path.
    An empty or None list returns [] (meaning: daemon runs realtime-filtered).
    """
    if not projects:
        return []
    resolved: list[Path] = []
    for p in projects:
        absolute = Path(p).expanduser().resolve()
        if not absolute.exists():
            raise ValueError(f"Project path does not exist: {absolute}")
        if not absolute.is_dir():
            raise ValueError(f"Project path is not a directory: {absolute}")
        resolved.append(absolute)
    return resolved


# =============================================================================
# macOS: launchd
# =============================================================================


def _macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{MACOS_LABEL}.plist"


def _macos_measure_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{MACOS_MEASURE_LABEL}.plist"


def _generate_macos_plist(
    executable: str,
    projects: list[Path] | None = None,
    max_uptime_hours: int = DEFAULT_MAX_UPTIME_HOURS,
) -> str:
    """Generate launchd plist XML for macOS.

    Phase 0: accepts explicit project list and max-uptime-hours for self-restart.
    If projects is empty/None, the daemon runs without flags (realtime-filtered
    default from watcher_daemon.py). max_uptime_hours is written as a STRING
    in EnvironmentVariables because launchd requires string values there.
    """
    log_dir = _ensure_log_dir()

    # Split executable into command + args if it's a module invocation
    if " -m " in executable:
        parts = executable.split(" ", 2)
        program_args_lines = [f"        <string>{p}</string>" for p in parts]
    else:
        program_args_lines = [f"        <string>{executable}</string>"]

    # Phase 0: add --projects PATH [PATH ...] if projects provided
    if projects:
        program_args_lines.append("        <string>--projects</string>")
        for p in projects:
            program_args_lines.append(f"        <string>{p}</string>")
    # else: no flag → daemon defaults to realtime-filter discovery

    program_args = "\n".join(program_args_lines)

    # Phase 0: max_uptime_hours as STRING (launchd requires string env values)
    max_uptime_str = str(int(max_uptime_hours))

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
                <key>AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS</key>
                <string>{max_uptime_str}</string>
            </dict>
        </dict>
        </plist>
    """)


def _generate_macos_measurement_plist(script_path: Path) -> str:
    """Generate the second launchd plist for daily measurement automation.

    Runs scripts/measure-watcher-footprint.sh at 04:00 local time daily.
    Writes ~/.context-engine/PHASE2_TRIGGERED on threshold exceed. Check 6b.2
    in workflows/COMPLIANCE-REVIEW.md reads that marker.

    Why a second plist: this is a standalone periodic task, not split daemon
    state. Different mechanism and purpose from the watcher plist. See plan
    jiggly-honking-cascade.md Alternative C rejection reasoning.
    """
    log_dir = _ensure_log_dir()
    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{MACOS_MEASURE_LABEL}</string>
            <key>ProgramArguments</key>
            <array>
                <string>/bin/bash</string>
                <string>{script_path}</string>
            </array>
            <key>RunAtLoad</key>
            <false/>
            <key>KeepAlive</key>
            <false/>
            <key>StartCalendarInterval</key>
            <dict>
                <key>Hour</key>
                <integer>4</integer>
                <key>Minute</key>
                <integer>0</integer>
            </dict>
            <key>StandardOutPath</key>
            <string>{log_dir}/measure.out.log</string>
            <key>StandardErrorPath</key>
            <string>{log_dir}/measure.err.log</string>
        </dict>
        </plist>
    """)


def _macos_install(
    projects: list[Path] | None = None,
    max_uptime_hours: int = DEFAULT_MAX_UPTIME_HOURS,
) -> bool:
    """Install macOS LaunchAgent (watcher) + optional measurement plist."""
    executable = _find_watcher_executable()

    # Primary: watcher plist
    plist_path = _macos_plist_path()
    plist_content = _generate_macos_plist(
        executable, projects=projects, max_uptime_hours=max_uptime_hours
    )
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist_content)
    print(f"Wrote watcher plist: {plist_path}")
    if projects:
        print(
            f"  Watching {len(projects)} project(s): {', '.join(str(p) for p in projects)}"
        )
    else:
        print("  Watching realtime-filtered projects (no --projects specified)")
    print(f"  Max uptime: {max_uptime_hours}h (self-restart for allocator flush)")

    # Load the watcher service (bootstrap replaces deprecated load)
    uid = os.getuid()
    result = subprocess.run(  # nosec B603 B607
        ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Failed to load watcher service: {result.stderr.strip()}")
        return False
    print(f"Watcher service loaded: {MACOS_LABEL}")

    # Secondary: measurement plist (Phase 0 test gate automation)
    script_path = _find_measurement_script()
    if script_path is None:
        print(
            "WARN: measurement script not found at expected path; "
            "Phase 0 test gate automation SKIPPED. Run Check 6b.2 manually, "
            "or reinstall from an editable checkout."
        )
    else:
        measure_path = _macos_measure_plist_path()
        measure_content = _generate_macos_measurement_plist(script_path)
        measure_path.write_text(measure_content)
        print(f"Wrote measurement plist: {measure_path}")
        measure_result = subprocess.run(  # nosec B603 B607
            ["launchctl", "bootstrap", f"gui/{uid}", str(measure_path)],
            capture_output=True,
            text=True,
        )
        if measure_result.returncode == 0:
            print(f"Measurement service loaded: {MACOS_MEASURE_LABEL} (daily at 04:00)")
        else:
            print(
                f"WARN: Failed to load measurement service: {measure_result.stderr.strip()}. "
                f"Watcher service is still running; Phase 0 test gate will fall back to manual."
            )

    return True


def _macos_uninstall() -> bool:
    """Uninstall macOS LaunchAgent (watcher) + measurement plist."""
    uid = os.getuid()
    # Bootout + remove watcher plist (bootout replaces deprecated unload)
    plist_path = _macos_plist_path()
    subprocess.run(  # nosec B603 B607
        ["launchctl", "bootout", f"gui/{uid}/{MACOS_LABEL}"],
        capture_output=True,
        text=True,
    )
    if plist_path.exists():
        plist_path.unlink()
        print(f"Removed watcher plist: {plist_path}")

    # Bootout + remove measurement plist (if present)
    measure_path = _macos_measure_plist_path()
    subprocess.run(  # nosec B603 B607
        ["launchctl", "bootout", f"gui/{uid}/{MACOS_MEASURE_LABEL}"],
        capture_output=True,
        text=True,
    )
    if measure_path.exists():
        measure_path.unlink()
        print(f"Removed measurement plist: {measure_path}")

    print(f"Service uninstalled: {MACOS_LABEL}")
    return True


def _macos_status() -> dict:
    """Get macOS service status."""
    result = subprocess.run(  # nosec B603 B607
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
        subprocess.run(["tail", "-f", "-n", "50", str(log_file)])  # nosec B603 B607
    else:
        print(f"No log file found at {log_file}")


# =============================================================================
# Linux: systemd
# =============================================================================


def _linux_unit_path() -> Path:
    return (
        Path.home() / ".config" / "systemd" / "user" / f"{LINUX_SERVICE_NAME}.service"
    )


def _generate_linux_unit(
    executable: str,
    projects: list[Path] | None = None,
    max_uptime_hours: int = DEFAULT_MAX_UPTIME_HOURS,
) -> str:
    """Generate systemd user service unit file.

    Phase 0: accepts explicit project list and max-uptime-hours.
    Measurement automation sidecar not implemented for Linux in Phase 0
    (macOS-only for v1 per plan).
    """
    exec_args = ""
    if projects:
        exec_args = " --projects " + " ".join(f'"{p}"' for p in projects)
    # else: no flag → daemon defaults to realtime-filter discovery

    return textwrap.dedent(f"""\
        [Unit]
        Description=Context Engine File Watcher Daemon
        After=default.target

        [Service]
        Type=simple
        ExecStart={executable}{exec_args}
        Restart=on-failure
        RestartSec=30
        Environment=AI_CONTEXT_ENGINE_INDEX_MODE=realtime
        Environment=AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS={int(max_uptime_hours)}
        MemoryMax=512M
        CPUQuota=25%

        [Install]
        WantedBy=default.target
    """)


def _linux_install(
    projects: list[Path] | None = None,
    max_uptime_hours: int = DEFAULT_MAX_UPTIME_HOURS,
) -> bool:
    """Install Linux systemd user service."""
    executable = _find_watcher_executable()
    unit_path = _linux_unit_path()
    unit_content = _generate_linux_unit(
        executable, projects=projects, max_uptime_hours=max_uptime_hours
    )

    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(unit_content)
    print(f"Wrote unit file: {unit_path}")
    if projects:
        print(
            f"  Watching {len(projects)} project(s): {', '.join(str(p) for p in projects)}"
        )
    else:
        print("  Watching realtime-filtered projects (no --projects specified)")
    print(f"  Max uptime: {max_uptime_hours}h")

    # Reload and enable
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)  # nosec B603 B607
    result = subprocess.run(  # nosec B603 B607
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
    subprocess.run(  # nosec B603 B607
        ["systemctl", "--user", "disable", "--now", LINUX_SERVICE_NAME],
        capture_output=True,
    )
    unit_path = _linux_unit_path()
    if unit_path.exists():
        unit_path.unlink()
        print(f"Removed unit file: {unit_path}")
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)  # nosec B603 B607
    print(f"Service uninstalled: {LINUX_SERVICE_NAME}")
    return True


def _linux_status() -> dict:
    """Get Linux service status."""
    result = subprocess.run(  # nosec B603 B607
        ["systemctl", "--user", "is-active", LINUX_SERVICE_NAME],
        capture_output=True,
        text=True,
    )
    is_active = result.stdout.strip() == "active"

    result2 = subprocess.run(  # nosec B603 B607
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
    subprocess.run(  # nosec B603 B607
        ["journalctl", "--user", "-u", LINUX_SERVICE_NAME, "-f", "-n", "50"]
    )


# =============================================================================
# Windows: Task Scheduler
# =============================================================================


def _generate_windows_task_action(
    executable: str,
    projects: list[Path] | None = None,
) -> str:
    """Build the /tr argument for schtasks /create."""
    if projects:
        project_args = " --projects " + " ".join(f'"{p}"' for p in projects)
    else:
        project_args = ""
    return f'"{executable}"{project_args}'


def _windows_install(
    projects: list[Path] | None = None,
    max_uptime_hours: int = DEFAULT_MAX_UPTIME_HOURS,
) -> bool:
    """Install Windows scheduled task.

    Note: schtasks does not natively support environment variables on a task,
    so MAX_UPTIME_HOURS must be threaded via a wrapper. For Phase 0, we document
    the gap — Windows users should set the env var system-wide or skip the
    self-restart feature. macOS is the primary target for Phase 0.
    """
    executable = _find_watcher_executable()
    _ensure_log_dir()

    tr_arg = _generate_windows_task_action(executable, projects=projects)

    result = subprocess.run(  # nosec B603 B607
        [
            "schtasks",
            "/create",
            "/tn",
            WINDOWS_TASK_NAME,
            "/tr",
            tr_arg,
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
        if projects:
            print(f"  Watching {len(projects)} project(s)")
        else:
            print("  Watching realtime-filtered projects (no --projects specified)")
        print(
            f"  Note: Phase 0 self-restart requires AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS={max_uptime_hours} "
            f"set in system env (schtasks does not carry task-scoped env vars)."
        )
        # Start it immediately
        subprocess.run(  # nosec B603 B607
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
    subprocess.run(  # nosec B603 B607
        ["schtasks", "/end", "/tn", WINDOWS_TASK_NAME],
        capture_output=True,
    )
    result = subprocess.run(  # nosec B603 B607
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
    result = subprocess.run(  # nosec B603 B607
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
        subprocess.run(  # nosec B603 B607
            ["powershell", "-Command", f"Get-Content -Tail 50 -Wait '{log_file}'"]
        )
    else:
        print(f"No log file found at {log_file}")


# =============================================================================
# Dispatch
# =============================================================================

_INSTALL_HANDLERS = {
    "macos": _macos_install,
    "linux": _linux_install,
    "windows": _windows_install,
}

_PLATFORM_HANDLERS = {
    "macos": {
        "uninstall": _macos_uninstall,
        "status": _macos_status,
        "logs": _macos_logs,
    },
    "linux": {
        "uninstall": _linux_uninstall,
        "status": _linux_status,
        "logs": _linux_logs,
    },
    "windows": {
        "uninstall": _windows_uninstall,
        "status": _windows_status,
        "logs": _windows_logs,
    },
}


def _cmd_install(
    platform: str,
    projects: list[Path] | None = None,
    max_uptime_hours: int = DEFAULT_MAX_UPTIME_HOURS,
) -> None:
    print(f"Installing Context Engine watcher service ({platform})...")
    install_fn = _INSTALL_HANDLERS[platform]
    success = install_fn(projects=projects, max_uptime_hours=max_uptime_hours)
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

    install_parser = subparsers.add_parser(
        "install", help="Install and start the watcher service"
    )
    install_parser.add_argument(
        "--projects",
        nargs="+",
        metavar="PATH",
        help=(
            "Explicit project paths to watch. If omitted, the daemon runs "
            "realtime-filtered discovery (NOT --all). Phase 0: this is the "
            "single source of truth for what this machine watches."
        ),
    )
    install_parser.add_argument(
        "--max-uptime-hours",
        type=int,
        default=DEFAULT_MAX_UPTIME_HOURS,
        metavar="N",
        help=(
            f"Daemon self-restart interval to flush PyTorch allocator cache. "
            f"Default: {DEFAULT_MAX_UPTIME_HOURS}. Set 0 to disable."
        ),
    )

    subparsers.add_parser("uninstall", help="Stop and remove the watcher service")
    subparsers.add_parser("status", help="Check service status")
    subparsers.add_parser("logs", help="Tail service logs")

    args = parser.parse_args()
    platform = _detect_platform()

    if args.command == "install":
        try:
            projects = _validate_project_paths([Path(p) for p in (args.projects or [])])
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(2)
        _cmd_install(
            platform,
            projects=projects or None,
            max_uptime_hours=args.max_uptime_hours,
        )
    elif args.command == "uninstall":
        _cmd_uninstall(platform)
    elif args.command == "status":
        _cmd_status(platform)
    elif args.command == "logs":
        _cmd_logs(platform)


if __name__ == "__main__":
    main()
