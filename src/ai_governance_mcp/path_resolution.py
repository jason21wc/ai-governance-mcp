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


def safe_cwd() -> Path | None:
    """The process working directory, or ``None`` when it is unavailable.

    THE ONLY PLACE THIS PACKAGE IS ALLOWED TO READ THE WORKING DIRECTORY.
    ``tests/test_no_unguarded_cwd.py`` asserts that, so the guard cannot
    quietly regrow copies the way the last two fixes for this class did.

    WHY A FUNCTION AND NOT A TRY/EXCEPT AT EACH SITE
    -----------------------------------------------
    A process outlives its working directory. Delete the directory a running
    process sits in — ``git worktree remove``, ``ExitWorktree``, ``rm -rf`` in
    another shell — and ``Path.cwd()`` raises ``FileNotFoundError`` from then on,
    for the life of the process. This is not hypothetical: a session deleted the
    worktree its own governance MCP server was launched in, and every
    ``evaluate_governance`` call for the rest of that session returned
    ``[Errno 2] No such file or directory``. The enforcement gate this repo
    exists to provide was down, and the tool that reports gate health could not
    report it, because the reporter reads the same cwd.

    The 2026-04-10 LEARNING-LOG entry for the previous occurrence already named
    the structural fix — "shared module + a check, you can't have divergent
    implementations if there's only one." The shared *module* got built (this
    file). The single shared *accessor* did not, so the unguarded call simply
    moved inside the shared module and kept its blast radius. This is that
    accessor.

    RETURNS ``None`` RATHER THAN RAISING OR SUBSTITUTING A DEFAULT.
    Callers must decide what an unknown cwd means for them, and the two honest
    answers differ: a *scope* check drops cwd from its allowed set (strictly
    fewer paths permitted — fail safe), while a *resolver* looking for a project
    root falls through to its explicit-configuration path. Substituting ``/`` or
    ``Path.home()`` here would silently answer that question wrong for both, and
    a scope check that quietly widened to ``/`` is a security regression.
    """
    try:
        return Path.cwd()
    except OSError:
        # FileNotFoundError (cwd unlinked) and PermissionError (parent lost +x)
        # both land here. Deliberately NOT logged: this is called on hot paths,
        # and a dead cwd would emit a warning per call for the process lifetime.
        return None


def is_within_allowed_scope(p: Path) -> bool:
    """Check if a resolved path is within allowed scope (home, CWD, or temp dirs).

    An unavailable cwd removes cwd from the allowed set instead of raising, so
    the check gets STRICTER, never wider — see ``safe_cwd``. Nothing legitimate
    is lost: if ``getcwd()`` fails because the directory is gone, no path can be
    inside it anyway.
    """
    p = p.resolve()
    home = Path.home().resolve()
    tmp = Path(tempfile.gettempdir()).resolve()
    allowed = [home, tmp]
    cwd = safe_cwd()
    if cwd is not None:
        allowed.append(cwd.resolve())
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
