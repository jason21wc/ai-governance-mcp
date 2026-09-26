"""One import-time source observation, not loaded-bytecode attestation.

Import this before server state/handlers. Never recapture from a metrics request:
editable installs can change underneath a process that still holds old modules.
"""

import copy
import hashlib
import os
from pathlib import Path
import re
import stat

# Fixed, read-only Git argv below; no shell or caller-supplied arguments.
import subprocess  # nosec B404
from datetime import datetime, timezone

from .. import __version__

_MAX_FILES = 512
_MAX_ENTRIES = 4096
_MAX_BYTES = 16 * 1024 * 1024
_GIT_TIMEOUT = 1


def _source_snapshot(package: Path) -> dict:
    """Hash names and bytes of regular .py files, refusing partial observations."""
    digest = hashlib.sha256()
    count = total = entries = 0
    try:
        if not package.is_dir():
            return {"status": "unavailable", "reason": "source_directory_missing"}
        for directory, dirs, files in os.walk(
            package, followlinks=False, onerror=_raise
        ):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            entries += len(dirs) + len(files)
            if entries > _MAX_ENTRIES:
                return {"status": "unavailable", "reason": "source_limit_exceeded"}
            if any((Path(directory) / d).is_symlink() for d in dirs):
                return {"status": "unavailable", "reason": "source_symlink"}
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                path = Path(directory) / name
                if path.is_symlink():
                    return {"status": "unavailable", "reason": "source_not_regular"}
                count += 1
                if count > _MAX_FILES:
                    return {"status": "unavailable", "reason": "source_limit_exceeded"}
                flags = (
                    os.O_RDONLY
                    | getattr(os, "O_NONBLOCK", 0)
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_BINARY", 0)
                )
                with os.fdopen(os.open(path, flags), "rb") as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        return {"status": "unavailable", "reason": "source_not_regular"}
                    data = stream.read(_MAX_BYTES - total + 1)
                total += len(data)
                if total > _MAX_BYTES:
                    return {"status": "unavailable", "reason": "source_limit_exceeded"}
                digest.update(path.relative_to(package).as_posix().encode("utf-8"))
                digest.update(b"\0")
                digest.update(len(data).to_bytes(8, "big"))
                digest.update(data)
        if not count:
            return {"status": "unavailable", "reason": "no_python_sources"}
    except (OSError, UnicodeError):
        return {"status": "unavailable", "reason": "source_read_failed"}
    return {
        "status": "available",
        "scope": "package_python_sources",
        "source_sha256_at_import": digest.hexdigest(),
        "file_count": count,
    }


def _raise(error: OSError) -> None:
    raise error


def _git_snapshot(package: Path) -> dict:
    """Optional context for the tracked src layout, never an enclosing app's Git."""
    root = package.parent.parent
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")

    def git(*args: str) -> str:
        result = subprocess.run(  # nosec B603 B607
            ["git", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT,
            check=True,
            env=env,
        )
        return result.stdout.strip()

    try:
        if package.parent.name != "src" or not (root / ".git").exists():
            return {"status": "unavailable", "reason": "not_source_checkout"}
        if Path(git("rev-parse", "--show-toplevel")).resolve() != root:
            return {"status": "unavailable", "reason": "not_package_repository"}
        relative = package.relative_to(root).as_posix()
        git("ls-files", "--error-unmatch", "--", relative + "/__init__.py")
        revision = git("rev-parse", "--verify", "HEAD")
        dirty = bool(
            git("status", "--porcelain", "--untracked-files=normal", "--", relative)
        )
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
            return {"status": "unavailable", "reason": "invalid_revision"}
        if git("rev-parse", "--verify", "HEAD") != revision:
            return {
                "status": "unavailable",
                "reason": "revision_changed_during_capture",
            }
    except subprocess.TimeoutExpired:
        return {"status": "unavailable", "reason": "git_timeout"}
    except (OSError, UnicodeError, subprocess.CalledProcessError):
        return {"status": "unavailable", "reason": "git_observation_failed"}
    return {
        "status": "available",
        "revision_at_import": revision,
        "package_dirty_at_import": dirty,
        "dirty_scope": relative,
    }


def _capture_identity() -> dict:
    try:
        package = Path(__file__).resolve().parent.parent
    except OSError:
        package = None
    return {
        "package_version": __version__,
        "pid": os.getpid(),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "capture_phase": "server_package_import",
        "package_path": str(package) if package is not None else None,
        "source": _source_snapshot(package)
        if package is not None
        else {"status": "unavailable", "reason": "source_path_unavailable"},
        "git": _git_snapshot(package)
        if package is not None
        else {"status": "unavailable", "reason": "source_path_unavailable"},
        "limitations": (
            "Source observed at import, not loaded-bytecode attestation. Concurrent "
            "edits, later lazy imports and manual reloads can differ. Excludes "
            "dependencies and index/corpus data. Reconnect MCP after code changes."
        ),
    }


_IDENTITY = _capture_identity()


def get_runtime_identity() -> dict:
    """Return a detached copy; metric resets and later edits do not change identity."""
    return copy.deepcopy(_IDENTITY)
