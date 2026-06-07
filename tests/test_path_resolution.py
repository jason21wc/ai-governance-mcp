"""Tests for shared path resolution utilities.

Tests is_within_allowed_scope(), looks_like_project(), and PROJECT_MARKERS
from the shared module used by both governance server and Context Engine.
"""

import tempfile
from pathlib import Path

from ai_governance_mcp.path_resolution import (
    PROJECT_MARKERS,
    _git_common_dir,
    is_within_allowed_scope,
    looks_like_project,
)


class TestProjectMarkers:
    """Verify PROJECT_MARKERS is a complete frozenset."""

    def test_is_frozenset(self):
        assert isinstance(PROJECT_MARKERS, frozenset)

    def test_contains_expected_markers(self):
        expected = {
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
        assert PROJECT_MARKERS == expected

    def test_has_14_markers(self):
        assert len(PROJECT_MARKERS) == 14


class TestLooksLikeProject:
    """Test looks_like_project() project marker detection."""

    def test_with_git_dir(self, tmp_path):
        (tmp_path / ".git").mkdir()
        assert looks_like_project(tmp_path) is True

    def test_with_pyproject_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        assert looks_like_project(tmp_path) is True

    def test_with_package_json(self, tmp_path):
        (tmp_path / "package.json").touch()
        assert looks_like_project(tmp_path) is True

    def test_with_contextignore(self, tmp_path):
        (tmp_path / ".contextignore").touch()
        assert looks_like_project(tmp_path) is True

    def test_with_cargo_toml(self, tmp_path):
        (tmp_path / "Cargo.toml").touch()
        assert looks_like_project(tmp_path) is True

    def test_with_go_mod(self, tmp_path):
        (tmp_path / "go.mod").touch()
        assert looks_like_project(tmp_path) is True

    def test_empty_dir_not_project(self, tmp_path):
        assert looks_like_project(tmp_path) is False

    def test_dir_with_random_files_not_project(self, tmp_path):
        (tmp_path / "weakpass_edit").touch()
        (tmp_path / "readme.txt").touch()
        assert looks_like_project(tmp_path) is False

    def test_nonexistent_dir_returns_false(self, tmp_path):
        nonexistent = tmp_path / "nonexistent"
        assert looks_like_project(nonexistent) is False

    def test_multiple_markers(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / "pyproject.toml").touch()
        assert looks_like_project(tmp_path) is True


class TestIsWithinAllowedScope:
    """Test is_within_allowed_scope() path containment check."""

    def test_home_subdir_allowed(self):
        subdir = Path.home() / "some_project"
        assert is_within_allowed_scope(subdir) is True

    def test_temp_dir_allowed(self):
        tmp = Path(tempfile.gettempdir()).resolve()
        test_path = tmp / "test_project"
        assert is_within_allowed_scope(test_path) is True

    def test_system_tmp_allowed(self):
        test_path = Path("/tmp").resolve() / "test_project"
        assert is_within_allowed_scope(test_path) is True

    def test_cwd_subdir_allowed(self):
        cwd = Path.cwd().resolve()
        subdir = cwd / "subproject"
        assert is_within_allowed_scope(subdir) is True

    def test_outside_all_scopes_rejected(self):
        bogus = Path("/nonexistent/rogue/path")
        assert is_within_allowed_scope(bogus) is False

    def test_root_path_rejected(self):
        assert is_within_allowed_scope(Path("/")) is False


class TestGitCommonDir:
    """Test _git_common_dir() — resolves a path's git common dir for identity checks.

    Used by capture_reference (BACKLOG #49) to validate that a target_root is a
    worktree/checkout of the SAME repo as the configured corpus (identity), not
    merely a directory that looks corpus-shaped. Pure stdlib — no git subprocess.
    """

    def test_normal_repo_returns_dot_git(self, tmp_path):
        """A normal checkout (.git is a directory) returns the .git dir."""
        (tmp_path / ".git").mkdir()
        assert _git_common_dir(tmp_path) == (tmp_path / ".git").resolve()

    def test_non_repo_returns_none(self, tmp_path):
        """A directory with no .git returns None."""
        assert _git_common_dir(tmp_path) is None

    def test_worktree_matches_main_via_commondir(self, tmp_path):
        """A worktree (.git is a pointer file) resolves to the SAME common dir
        as its main checkout, via the gitdir 'commondir' file."""
        main = tmp_path / "main"
        main_git = main / ".git"
        (main_git / "worktrees" / "wt").mkdir(parents=True)
        # git writes a 'commondir' file inside the worktree's gitdir, pointing back
        (main_git / "worktrees" / "wt" / "commondir").write_text("../..\n")

        wt = tmp_path / "wt"
        wt.mkdir()
        (wt / ".git").write_text(f"gitdir: {main_git / 'worktrees' / 'wt'}\n")

        assert _git_common_dir(wt) == _git_common_dir(main) == main_git.resolve()

    def test_worktree_no_commondir_strips_worktrees_suffix(self, tmp_path):
        """If no commondir file is present, strip '/worktrees/<name>' to recover
        the common dir."""
        main = tmp_path / "main"
        main_git = main / ".git"
        (main_git / "worktrees" / "wt").mkdir(parents=True)

        wt = tmp_path / "wt"
        wt.mkdir()
        (wt / ".git").write_text(f"gitdir: {main_git / 'worktrees' / 'wt'}\n")

        assert _git_common_dir(wt) == main_git.resolve()

    def test_garbage_dot_git_file_returns_none(self, tmp_path):
        """A .git file that is not a 'gitdir:' pointer returns None."""
        (tmp_path / ".git").write_text("not a gitdir pointer\n")
        assert _git_common_dir(tmp_path) is None

    def test_submodule_gitdir_distinct_from_superproject(self, tmp_path):
        """A submodule (.git file → .git/modules/<name>, no commondir, parent is
        'modules' not 'worktrees') resolves to its own modules gitdir and does NOT
        match the superproject's common dir — so a submodule is never mistaken for
        the same repo as its parent."""
        super_git = tmp_path / ".git"
        (super_git / "modules" / "sub").mkdir(parents=True)

        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / ".git").write_text(f"gitdir: {super_git / 'modules' / 'sub'}\n")

        assert _git_common_dir(sub) == (super_git / "modules" / "sub").resolve()
        assert _git_common_dir(sub) != _git_common_dir(tmp_path)
