"""Tests for shared path resolution utilities.

Tests is_within_allowed_scope(), looks_like_project(), and PROJECT_MARKERS
from the shared module used by both governance server and Context Engine.
"""

import tempfile
from pathlib import Path

from ai_governance_mcp.path_resolution import (
    PROJECT_MARKERS,
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
