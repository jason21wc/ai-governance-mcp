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


def _git_common_dir(path: Path) -> Path | None:
    """Resolve a path's git common directory, or None if it is not a git checkout.

    Two checkouts of the same repository (e.g. the main working tree and a
    ``git worktree``) share one common dir. Comparing common dirs is therefore an
    *identity* test ("same repository, possibly different working tree") — stronger
    than a structural-shape check, which every clone/fork/worktree would pass alike.

    Pure stdlib — reads the ``.git`` directory-or-pointer; never shells out to git.

    - ``.git`` is a directory  → that directory (normal checkout / bare-ish layout).
    - ``.git`` is a file       → a worktree pointer ``gitdir: <path>``; the common
      dir is read from the ``commondir`` file inside that gitdir when present,
      else recovered by stripping a trailing ``worktrees/<name>`` segment.
    - no ``.git``              → None (cannot establish repo identity).
    """
    git = path / ".git"
    try:
        if git.is_dir():
            return git.resolve()
        if git.is_file():
            content = git.read_text(encoding="utf-8", errors="replace").strip()
            if not content.startswith("gitdir:"):
                return None
            raw = content[len("gitdir:") :].strip()
            gitdir = Path(raw)
            if not gitdir.is_absolute():
                gitdir = path / gitdir
            gitdir = gitdir.resolve()
            commondir_file = gitdir / "commondir"
            if commondir_file.is_file():
                cd = commondir_file.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                return (gitdir / cd).resolve()
            if gitdir.parent.name == "worktrees":
                return gitdir.parent.parent.resolve()
            # commondir absent and not a worktree layout — e.g. a submodule gitdir
            # at .git/modules/<name>. Return the gitdir itself (already resolved at
            # the assignment above): two checkouts of the same submodule share it,
            # while a submodule and its superproject correctly do NOT match.
            return gitdir
    except OSError:
        return None
    return None
