"""Tests for configuration management (T19).

Per specification v4: Validates settings and configuration loading.
"""

import json
from pathlib import Path
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_governance_mcp.config import (
    Settings,
    load_settings,
    load_domains_registry,
    setup_logging,
    ensure_directories,
    get_settings,
    _default_domains,
    _find_project_root,
)


class TestFindProjectRoot:
    """Tests for _find_project_root() data directory detection."""

    def test_finds_root_from_project_directory(self):
        """Should find root when CWD is the ai-governance project."""
        # Running tests from the project root, so this should work
        root = _find_project_root()
        assert (root / "documents" / "domains.json").exists()

    def test_does_not_match_generic_pyproject_toml(self, tmp_path, monkeypatch):
        """Should NOT match a directory with only pyproject.toml (no domains.json)."""
        # Create a generic Python project structure
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'other-project'\n")
        (tmp_path / "src").mkdir()

        monkeypatch.chdir(tmp_path)
        root = _find_project_root()

        # Should NOT return the tmp_path (generic project)
        assert root != tmp_path

    def test_does_not_match_generic_documents_dir(self, tmp_path, monkeypatch):
        """Should NOT match a directory with only a documents/ folder (no domains.json)."""
        (tmp_path / "documents").mkdir()

        monkeypatch.chdir(tmp_path)
        root = _find_project_root()

        assert root != tmp_path

    def test_matches_directory_with_domains_json(self, tmp_path, monkeypatch):
        """Should match when documents/domains.json exists."""
        docs = tmp_path / "documents"
        docs.mkdir()
        (docs / "domains.json").write_text("[]")

        monkeypatch.chdir(tmp_path)
        root = _find_project_root()

        assert root == tmp_path

    def test_walks_up_to_find_root(self, tmp_path, monkeypatch):
        """Should find root from a subdirectory."""
        docs = tmp_path / "documents"
        docs.mkdir()
        (docs / "domains.json").write_text("[]")
        subdir = tmp_path / "src" / "deep" / "nested"
        subdir.mkdir(parents=True)

        monkeypatch.chdir(subdir)
        root = _find_project_root()

        assert root == tmp_path

    def test_fallback_when_no_marker_found(self, tmp_path, monkeypatch):
        """Should fall back to ~/.ai-governance when no marker found."""
        monkeypatch.chdir(tmp_path)
        root = _find_project_root()

        assert root == Path.home() / ".ai-governance"

    def test_prefers_nearest_match(self, tmp_path, monkeypatch):
        """Should return the nearest ancestor with the marker, not a higher one."""
        # Outer project
        outer_docs = tmp_path / "documents"
        outer_docs.mkdir()
        (outer_docs / "domains.json").write_text("[]")

        # Inner project (nested)
        inner = tmp_path / "inner"
        inner_docs = inner / "documents"
        inner_docs.mkdir(parents=True)
        (inner_docs / "domains.json").write_text("[]")

        monkeypatch.chdir(inner)
        root = _find_project_root()

        assert root == inner


class TestSettings:
    """Test Settings class."""

    def test_default_values(self):
        """Should have sensible defaults."""
        settings = Settings()
        assert settings.log_level == "INFO"
        assert settings.embedding_model == "BAAI/bge-small-en-v1.5"
        assert settings.embedding_dimensions == 384
        assert settings.semantic_weight == 0.6
        assert settings.max_results == 10

    def test_embedding_settings(self):
        """Should have embedding configuration."""
        settings = Settings()
        assert "bge" in settings.embedding_model.lower()
        assert settings.embedding_dimensions == 384
        assert settings.rerank_model == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert settings.rerank_top_k == 20

    def test_retrieval_thresholds(self):
        """Should have retrieval thresholds."""
        settings = Settings()
        assert settings.min_score_threshold == 0.3
        assert settings.confidence_high_threshold == 0.7
        assert settings.confidence_medium_threshold == 0.4
        assert settings.domain_similarity_threshold == 0.25

    def test_performance_target(self):
        """Should have latency target."""
        settings = Settings()
        assert settings.latency_target_ms == 100.0

    def test_semantic_weight_constraints(self):
        """Semantic weight should be 0-1."""
        # Valid values
        settings = Settings(semantic_weight=0.0)
        assert settings.semantic_weight == 0.0

        settings = Settings(semantic_weight=1.0)
        assert settings.semantic_weight == 1.0

    def test_paths_are_path_objects(self):
        """Paths should be Path objects."""
        settings = Settings()
        assert isinstance(settings.documents_path, Path)
        assert isinstance(settings.index_path, Path)
        assert isinstance(settings.logs_path, Path)


class TestEnvironmentOverrides:
    """Test environment variable overrides."""

    def test_env_prefix(self):
        """Settings should use AI_GOVERNANCE_ prefix."""
        settings = Settings()
        assert settings.model_config.get("env_prefix") == "AI_GOVERNANCE_"


class TestDefaultDomains:
    """Test default domain configurations."""

    def test_six_default_domains(self):
        """Should have all 6 domains: constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux."""
        domains = _default_domains()
        assert len(domains) == 6
        names = [d.name for d in domains]
        assert "constitution" in names
        assert "ai-coding" in names
        assert "multi-agent" in names
        assert "storytelling" in names
        assert "multimodal-rag" in names
        assert "ui-ux" in names

    def test_constitution_highest_priority(self):
        """Constitution should have priority 0."""
        domains = _default_domains()
        constitution = next(d for d in domains if d.name == "constitution")
        assert constitution.priority == 0

    def test_domains_have_descriptions(self):
        """All domains should have descriptions for semantic routing."""
        domains = _default_domains()
        for domain in domains:
            assert domain.description != ""
            assert len(domain.description) > 50

    def test_domain_files_specified(self):
        """Each domain should have principles file."""
        domains = _default_domains()
        for domain in domains:
            assert domain.principles_file.endswith(".md")


class TestLogging:
    """Test logging configuration."""

    def test_setup_logging_returns_logger(self):
        """Should return a logger instance."""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == "ai_governance_mcp"

    def test_setup_logging_level(self):
        """Should set log level correctly."""
        import logging

        logger = setup_logging("DEBUG")
        assert logger.level == logging.DEBUG

        logger = setup_logging("WARNING")
        assert logger.level == logging.WARNING


class TestLoadSettings:
    """Test settings loading functions."""

    def test_load_settings(self):
        """Should load settings successfully."""
        settings = load_settings()
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_get_settings_caches(self):
        """get_settings should cache instance."""
        # Clear any cached instance
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2  # Same instance


class TestLoadDomainsRegistry:
    """Test domain registry loading."""

    def test_load_returns_list(self):
        """Should return list of DomainConfig."""
        settings = Settings()
        domains = load_domains_registry(settings)
        assert isinstance(domains, list)
        assert len(domains) >= 3  # Default domains


class TestEnsureDirectories:
    """Test directory creation."""

    def test_creates_directories(self, tmp_path):
        """Should create required directories."""
        settings = Settings()
        settings.documents_path = tmp_path / "docs"
        settings.index_path = tmp_path / "index"
        settings.logs_path = tmp_path / "logs"

        ensure_directories(settings)

        assert settings.documents_path.exists()
        assert settings.index_path.exists()
        assert settings.logs_path.exists()


class TestDomainConsistency:
    """Automated domain consistency checks across all code surfaces.

    Uses domains.json as the single source of truth — no domain names
    hardcoded in tests. Catches incomplete domain propagation at CI time.
    """

    @staticmethod
    def _load_registry() -> dict | None:
        """Load domains.json registry, return None if missing."""
        domains_path = Path(__file__).parent.parent / "documents" / "domains.json"
        if not domains_path.exists():
            return None
        with open(domains_path) as f:
            return json.load(f)

    def test_registry_matches_default_domains_names(self):
        """domains.json keys should match _default_domains() names bidirectionally."""
        registry = self._load_registry()
        if registry is None:
            pytest.skip("domains.json not found")

        registry_names = set(registry.keys())
        default_names = {d.name for d in _default_domains()}

        assert registry_names == default_names, (
            f"Mismatch between domains.json and _default_domains().\n"
            f"  In registry only: {registry_names - default_names}\n"
            f"  In defaults only: {default_names - registry_names}"
        )

    async def test_registry_matches_server_enums(self):
        """Both tool schema enum lists should contain all domains.json keys."""
        registry = self._load_registry()
        if registry is None:
            pytest.skip("domains.json not found")

        registry_names = set(registry.keys())

        from ai_governance_mcp.server import list_tools

        tools = await list_tools()

        enum_sets = {}
        for tool in tools:
            if tool.name in ("query_governance", "get_domain_summary"):
                schema = tool.inputSchema
                props = schema.get("properties", {})
                domain_prop = props.get("domain", {})
                enum_list = domain_prop.get("enum", [])
                if enum_list:
                    enum_sets[tool.name] = set(enum_list)

        assert "query_governance" in enum_sets, "query_governance missing domain enum"
        assert "get_domain_summary" in enum_sets, (
            "get_domain_summary missing domain enum"
        )

        for tool_name, enum_set in enum_sets.items():
            assert enum_set == registry_names, (
                f"{tool_name} enum mismatch with domains.json.\n"
                f"  In enum only: {enum_set - registry_names}\n"
                f"  In registry only: {registry_names - enum_set}"
            )

    async def test_registry_matches_handler_valid_domains(self):
        """Handler valid_domains sets should match domains.json (behavioral test).

        Sends an invalid domain to each handler and parses the accepted set from
        the error message format: "Valid: ai-coding, constitution, ..."
        """
        registry = self._load_registry()
        if registry is None:
            pytest.skip("domains.json not found")

        registry_names = set(registry.keys())

        from ai_governance_mcp.server import (
            _handle_query_governance,
            _handle_get_domain_summary,
        )

        async def _extract_valid_set(handler, args):
            mock_engine = Mock()
            result = await handler(mock_engine, args)
            text = result[0].text
            if "Valid:" in text:
                valid_str = text.split("Valid:")[1].strip()
                return {name.strip(".,; ") for name in valid_str.split(", ")}
            return None

        # query_governance handler
        qg_set = await _extract_valid_set(
            _handle_query_governance,
            {"query": "test", "domain": "__invalid__"},
        )
        assert qg_set is not None, (
            "Could not extract valid_domains from query_governance"
        )
        assert qg_set == registry_names, (
            f"query_governance handler valid_domains mismatch.\n"
            f"  In handler only: {qg_set - registry_names}\n"
            f"  In registry only: {registry_names - qg_set}"
        )

        # get_domain_summary handler
        gds_set = await _extract_valid_set(
            _handle_get_domain_summary,
            {"domain": "__invalid__"},
        )
        assert gds_set is not None, (
            "Could not extract valid_domains from get_domain_summary"
        )
        assert gds_set == registry_names, (
            f"get_domain_summary handler valid_domains mismatch.\n"
            f"  In handler only: {gds_set - registry_names}\n"
            f"  In registry only: {registry_names - gds_set}"
        )

    def test_registry_matches_extractor_prefix_keys(self):
        """DOMAIN_PREFIXES keys should match domains.json keys exactly."""
        registry = self._load_registry()
        if registry is None:
            pytest.skip("domains.json not found")

        registry_names = set(registry.keys())

        # Mock is for import-time SentenceTransformer side effect, not DOMAIN_PREFIXES
        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            prefix_keys = set(DocumentExtractor.DOMAIN_PREFIXES.keys())

        assert prefix_keys == registry_names, (
            f"DOMAIN_PREFIXES keys mismatch with domains.json.\n"
            f"  In prefixes only: {prefix_keys - registry_names}\n"
            f"  In registry only: {registry_names - prefix_keys}"
        )

    def test_domain_files_exist_on_disk(self):
        """All principles_file and methods_file from domains.json should exist."""
        registry = self._load_registry()
        if registry is None:
            pytest.skip("domains.json not found")

        documents_dir = Path(__file__).parent.parent / "documents"
        missing = []

        for domain_name, domain_data in registry.items():
            for file_key in ("principles_file", "methods_file"):
                filename = domain_data.get(file_key)
                if filename and not (documents_dir / filename).exists():
                    missing.append(f"{domain_name}.{file_key}: {filename}")

        assert not missing, "Domain files missing from documents/:\n  " + "\n  ".join(
            missing
        )

    def test_default_domains_files_match_registry(self):
        """_default_domains() file paths should match domains.json exactly."""
        registry = self._load_registry()
        if registry is None:
            pytest.skip("domains.json not found")

        defaults = {d.name: d for d in _default_domains()}
        mismatches = []

        for domain_name, reg_data in registry.items():
            if domain_name not in defaults:
                continue  # Caught by test_registry_matches_default_domains_names
            default = defaults[domain_name]
            if default.principles_file != reg_data.get("principles_file"):
                mismatches.append(
                    f"{domain_name} principles_file: "
                    f"default={default.principles_file!r} vs "
                    f"registry={reg_data.get('principles_file')!r}"
                )
            if hasattr(
                default, "methods_file"
            ) and default.methods_file != reg_data.get("methods_file"):
                mismatches.append(
                    f"{domain_name} methods_file: "
                    f"default={default.methods_file!r} vs "
                    f"registry={reg_data.get('methods_file')!r}"
                )

        assert not mismatches, (
            "File path mismatches between _default_domains() and domains.json:\n  "
            + "\n  ".join(mismatches)
        )
