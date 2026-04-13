"""Shared path resolution utilities for MCP servers.

Both the governance server and Context Engine import from here.
Neither server should reimplement scope checking or project detection.
"""

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_MARKERS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "Makefile",
        "CMakeLists.txt",
        "pom.xml",
        "build.gradle",
        ".contextignore",
    }
)


def is_within_allowed_scope(p: Path) -> bool:
    """Check if a resolved path is within allowed scope (home, CWD, or temp dirs)."""
    p = p.resolve()
    home = Path.home().resolve()
    cwd = Path.cwd().resolve()
    tmp = Path(tempfile.gettempdir()).resolve()
    allowed = [home, cwd, tmp]
    # Also allow system /tmp explicitly (macOS symlinks it to /private/tmp,
    # which differs from tempfile.gettempdir() user-specific temp dir)
    system_tmp = Path("/tmp").resolve()  # nosec B108
    if system_tmp != tmp:
        allowed.append(system_tmp)
    return any(p.is_relative_to(base) for base in allowed)


def looks_like_project(path: Path) -> bool:
    """Check if a directory has common project markers.

    MCP servers run as separate processes — Path.cwd() resolves to the SERVER's
    working directory, not the calling client's project. This check prevents
    operating on arbitrary directories when CWD is used as fallback.
    """
    try:
        return any((path / marker).exists() for marker in PROJECT_MARKERS)
    except OSError:
        return False
