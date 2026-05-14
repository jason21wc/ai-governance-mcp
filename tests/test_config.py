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
    discover_domains,
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
        """Should NOT match a directory with only a documents/ folder (no governance marker)."""
        (tmp_path / "documents").mkdir()

        monkeypatch.chdir(tmp_path)
        root = _find_project_root()

        assert root != tmp_path

    def test_matches_directory_with_constitution(self, tmp_path, monkeypatch):
        """Should match when documents/constitution.md exists (multi-marker)."""
        docs = tmp_path / "documents"
        docs.mkdir()
        (docs / "constitution.md").write_text(
            "---\ndomain: constitution\n---\n# Constitution"
        )

        monkeypatch.chdir(tmp_path)
        root = _find_project_root()

        assert root == tmp_path

    def test_matches_directory_with_title_file(self, tmp_path, monkeypatch):
        """Should match when documents/title-*-*.md exists (multi-marker)."""
        docs = tmp_path / "documents"
        docs.mkdir()
        (docs / "title-50-custom.md").write_text("---\ndomain: custom\n---\n# Custom")

        monkeypatch.chdir(tmp_path)
        root = _find_project_root()

        assert root == tmp_path

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

    def test_eight_default_domains(self):
        """Should have all 8 domains: constitution, ai-coding, multi-agent, storytelling, multimodal-rag, ui-ux, kmpd, accounting."""
        domains = _default_domains()
        assert len(domains) == 8
        names = [d.name for d in domains]
        assert "constitution" in names
        assert "ai-coding" in names
        assert "multi-agent" in names
        assert "storytelling" in names
        assert "multimodal-rag" in names
        assert "ui-ux" in names
        assert "kmpd" in names
        assert "accounting" in names

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
        """Load domains.json registry, return None if missing.

        Filters out underscore-prefixed keys (metadata like _note).
        """
        domains_path = Path(__file__).parent.parent / "documents" / "domains.json"
        if not domains_path.exists():
            return None
        with open(domains_path) as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith("_")}

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
        """Handler valid_domains should be derived from engine index dynamically.

        Sends an invalid domain to each handler and parses the accepted set from
        the error message format: "Valid: ai-coding, constitution, ..."
        Verifies the engine-derived set matches domains.json.
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
            mock_engine.index.domains = {name: None for name in registry_names}
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


class TestReadmePropagation:
    """CI assertion: README metrics must match actual state.

    Prevents the recurring "README stale" propagation gap. Promoted from
    BEST-EFFORT to ENFORCED per root cause analysis: advisory propagation
    checks failed in 4 consecutive sessions.
    """

    @pytest.mark.asyncio
    async def test_readme_governance_tool_count(self):
        """README governance tool count must match list_tools()."""
        import re

        from ai_governance_mcp.server import list_tools

        tools = await list_tools()
        actual_gov_count = len(tools)

        readme_path = Path(__file__).parent.parent / "README.md"
        if not readme_path.exists():
            pytest.skip("README.md not found")

        readme = readme_path.read_text()
        # Match "Governance Server (N tools)" pattern
        match = re.search(r"Governance Server\s*\((\d+)\s*tools?\)", readme)
        if not match:
            # Fallback: match "N MCP Tools" and subtract CE tools (4)
            total_match = re.search(r"(\d+)\s+MCP\s+Tools", readme)
            assert total_match, "README must contain tool count"
            readme_total = int(total_match.group(1))
            CE_TOOL_COUNT = (
                4  # query_project, index_project, project_status, list_projects
            )
            readme_gov_count = readme_total - CE_TOOL_COUNT
        else:
            readme_gov_count = int(match.group(1))

        assert readme_gov_count == actual_gov_count, (
            f"README governance tool count ({readme_gov_count}) doesn't match "
            f"list_tools() ({actual_gov_count}). Update README."
        )


class TestPrincipleCountCeiling:
    """CI assertion: no domain exceeds the principle count ceiling.

    Catches principle accretion structurally at CI time. If a domain exceeds
    the ceiling, a consolidation pass (Part 9.8.5) is needed before adding
    more principles. Uses the real pre-built index — no mocking.

    Closes Backlog #25 — structural enforcement over advisory checklist.
    """

    MAX_PRINCIPLES_PER_DOMAIN = 35
    WARNING_THRESHOLD = 30

    def test_no_domain_exceeds_ceiling(self):
        """Each domain's principle count must be <= MAX_PRINCIPLES_PER_DOMAIN."""
        index_path = Path(__file__).parent.parent / "index" / "global_index.json"
        if not index_path.exists():
            pytest.skip("Index not built — run extractor first")

        with open(index_path) as f:
            index_data = json.load(f)

        domains = index_data.get("domains", {})
        if not domains:
            pytest.skip("No domains in index")

        violations = []
        warnings = []

        for domain_name, domain_data in domains.items():
            count = len(domain_data.get("principles", []))
            if count > self.MAX_PRINCIPLES_PER_DOMAIN:
                violations.append(
                    f"{domain_name}: {count} principles "
                    f"(ceiling: {self.MAX_PRINCIPLES_PER_DOMAIN})"
                )
            elif count >= self.WARNING_THRESHOLD:
                warnings.append(
                    f"{domain_name}: {count} principles "
                    f"(approaching ceiling of {self.MAX_PRINCIPLES_PER_DOMAIN})"
                )

        if warnings:
            print(
                f"\n⚠️  Principle count warnings: {', '.join(warnings)}",
                file=sys.stderr,
            )

        assert not violations, (
            f"Domain(s) exceed principle count ceiling ({self.MAX_PRINCIPLES_PER_DOMAIN}). "
            f"Run consolidation pass (Part 9.8.5) before adding more:\n  "
            + "\n  ".join(violations)
        )


class TestDiscoverDomains:
    """Tests for filesystem-based domain discovery."""

    def _write_domain_file(self, docs: Path, filename: str, frontmatter: dict) -> None:
        """Helper to write a domain file with YAML frontmatter."""
        import yaml

        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n# {frontmatter.get('display_name', 'Domain')}\n\nContent here.\n"
        (docs / filename).write_text(content)

    def test_discovers_from_frontmatter(self, tmp_path):
        """Should discover domains from title-*-*.md files with frontmatter."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "constitution.md",
            {
                "domain": "constitution",
                "prefix": "meta",
                "display_name": "Constitution",
                "description": "Universal rules",
                "priority": 0,
            },
        )
        self._write_domain_file(
            docs,
            "title-10-coding.md",
            {
                "domain": "coding",
                "prefix": "cod",
                "display_name": "Coding",
                "description": "Software development",
                "priority": 10,
            },
        )

        domains = discover_domains(docs)

        assert len(domains) == 2
        assert domains[0].name == "constitution"
        assert domains[0].prefix == "meta"
        assert domains[0].priority == 0
        assert domains[1].name == "coding"
        assert domains[1].prefix == "cod"

    def test_sorts_by_priority(self, tmp_path):
        """Discovered domains should be sorted by priority."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-50-last.md",
            {
                "domain": "last",
                "priority": 50,
            },
        )
        self._write_domain_file(
            docs,
            "title-10-first.md",
            {
                "domain": "first",
                "priority": 10,
            },
        )
        self._write_domain_file(
            docs,
            "title-30-middle.md",
            {
                "domain": "middle",
                "priority": 30,
            },
        )

        domains = discover_domains(docs)
        names = [d.name for d in domains]
        assert names == ["first", "middle", "last"]

    def test_skips_files_without_frontmatter(self, tmp_path):
        """Should skip .md files that lack domain frontmatter."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-10-good.md",
            {
                "domain": "good",
                "priority": 10,
            },
        )
        (docs / "title-20-bad.md").write_text("# No frontmatter\n\nJust content.\n")

        domains = discover_domains(docs)
        assert len(domains) == 1
        assert domains[0].name == "good"

    def test_skips_cfr_files(self, tmp_path):
        """Should not discover CFR files as domains."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-10-coding.md",
            {
                "domain": "coding",
                "priority": 10,
            },
        )
        self._write_domain_file(
            docs,
            "title-10-coding-cfr.md",
            {
                "domain": "coding-methods",
                "priority": 10,
            },
        )

        domains = discover_domains(docs)
        assert len(domains) == 1
        assert domains[0].name == "coding"

    def test_discovers_methods_file_by_convention(self, tmp_path):
        """Should find matching CFR file when it exists."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-10-coding.md",
            {
                "domain": "coding",
                "priority": 10,
            },
        )
        (docs / "title-10-coding-cfr.md").write_text("# Methods\n")

        domains = discover_domains(docs)
        assert domains[0].methods_file == "title-10-coding-cfr.md"

    def test_methods_file_none_when_missing(self, tmp_path):
        """Should set methods_file to None when no CFR file exists."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-10-coding.md",
            {
                "domain": "coding",
                "priority": 10,
            },
        )

        domains = discover_domains(docs)
        assert domains[0].methods_file is None

    def test_returns_empty_for_empty_directory(self, tmp_path):
        """Should return empty list when no domain files found."""
        docs = tmp_path / "documents"
        docs.mkdir()

        domains = discover_domains(docs)
        assert domains == []

    def test_skips_malformed_yaml_frontmatter(self, tmp_path):
        """Should skip files with invalid YAML in frontmatter."""
        docs = tmp_path / "documents"
        docs.mkdir()

        (docs / "title-10-bad.md").write_text("---\ndomain: [unclosed\n---\n# Bad\n")
        self._write_domain_file(
            docs,
            "title-20-good.md",
            {
                "domain": "good",
                "priority": 20,
            },
        )

        domains = discover_domains(docs)
        assert len(domains) == 1
        assert domains[0].name == "good"

    def test_skips_non_dict_yaml_frontmatter(self, tmp_path):
        """Should skip files where frontmatter is a bare string, not a dict."""
        docs = tmp_path / "documents"
        docs.mkdir()

        (docs / "title-10-bad.md").write_text("---\njust a string\n---\n# Bad\n")
        self._write_domain_file(
            docs,
            "title-20-good.md",
            {
                "domain": "good",
                "priority": 20,
            },
        )

        domains = discover_domains(docs)
        assert len(domains) == 1
        assert domains[0].name == "good"

    def test_default_display_name_from_domain(self, tmp_path):
        """Should derive display_name from domain name when not specified."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-10-my-domain.md",
            {
                "domain": "my-domain",
                "priority": 10,
            },
        )

        domains = discover_domains(docs)
        assert domains[0].display_name == "My Domain"

    def test_constitution_discovers_rules_of_procedure(self, tmp_path):
        """Constitution should find rules-of-procedure.md as its methods file."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "constitution.md",
            {
                "domain": "constitution",
                "prefix": "meta",
                "priority": 0,
            },
        )
        (docs / "rules-of-procedure.md").write_text("# Rules\n")

        domains = discover_domains(docs)
        assert domains[0].methods_file == "rules-of-procedure.md"


class TestCustomDomainDiscovery:
    """Tests for adding custom domains to the framework."""

    def _write_domain_file(self, docs: Path, filename: str, frontmatter: dict) -> None:
        import yaml

        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n# {frontmatter.get('display_name', 'Domain')}\n\nContent here.\n"
        (docs / filename).write_text(content)

    def test_custom_domain_alongside_existing(self, tmp_path):
        """Custom domain file should be discovered alongside built-in domains."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "constitution.md",
            {
                "domain": "constitution",
                "prefix": "meta",
                "priority": 0,
            },
        )
        self._write_domain_file(
            docs,
            "title-10-coding.md",
            {
                "domain": "coding",
                "prefix": "cod",
                "priority": 10,
            },
        )
        self._write_domain_file(
            docs,
            "title-50-custom.md",
            {
                "domain": "custom",
                "prefix": "cust",
                "display_name": "Custom Domain",
                "description": "My custom governance domain",
                "priority": 50,
            },
        )

        domains = discover_domains(docs)
        names = [d.name for d in domains]

        assert "custom" in names
        assert len(domains) == 3

        custom = next(d for d in domains if d.name == "custom")
        assert custom.prefix == "cust"
        assert custom.display_name == "Custom Domain"
        assert custom.priority == 50

    def test_domain_removal_reduces_count(self, tmp_path):
        """Removing a domain file should reduce discovered domains."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-10-a.md",
            {
                "domain": "a",
                "priority": 10,
            },
        )
        self._write_domain_file(
            docs,
            "title-20-b.md",
            {
                "domain": "b",
                "priority": 20,
            },
        )
        self._write_domain_file(
            docs,
            "title-30-c.md",
            {
                "domain": "c",
                "priority": 30,
            },
        )

        assert len(discover_domains(docs)) == 3

        (docs / "title-20-b.md").unlink()

        domains = discover_domains(docs)
        assert len(domains) == 2
        assert {d.name for d in domains} == {"a", "c"}

    def test_domains_json_overrides_frontmatter(self, tmp_path):
        """domains.json should override frontmatter fields when present."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-10-coding.md",
            {
                "domain": "coding",
                "display_name": "Coding",
                "description": "Original description",
                "priority": 10,
            },
        )

        overrides = {
            "coding": {
                "name": "coding",
                "display_name": "AI Coding",
                "description": "Overridden description",
            }
        }
        (docs / "domains.json").write_text(json.dumps(overrides))

        settings = Settings()
        settings.documents_path = docs
        domains = load_domains_registry(settings)

        coding = next(d for d in domains if d.name == "coding")
        assert coding.display_name == "AI Coding"
        assert coding.description == "Overridden description"

    def test_works_without_domains_json(self, tmp_path):
        """System should work with no domains.json — pure filesystem discovery."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "constitution.md",
            {
                "domain": "constitution",
                "prefix": "meta",
                "priority": 0,
            },
        )
        self._write_domain_file(
            docs,
            "title-10-coding.md",
            {
                "domain": "coding",
                "prefix": "cod",
                "priority": 10,
            },
        )

        settings = Settings()
        settings.documents_path = docs
        domains = load_domains_registry(settings)

        assert len(domains) == 2
        assert domains[0].name == "constitution"
        assert domains[1].name == "coding"

    def test_malformed_domains_json_falls_through(self, tmp_path):
        """Malformed domains.json should be skipped, falling back to discovery."""
        docs = tmp_path / "documents"
        docs.mkdir()

        self._write_domain_file(
            docs,
            "title-10-coding.md",
            {
                "domain": "coding",
                "prefix": "cod",
                "priority": 10,
            },
        )
        (docs / "domains.json").write_text("{invalid json")

        settings = Settings()
        settings.documents_path = docs
        domains = load_domains_registry(settings)

        assert len(domains) == 1
        assert domains[0].name == "coding"


class TestPrincipleIdStability:
    """Verify that existing principle IDs are unchanged after modular migration.

    Compares IDs in the pre-built index against what discover_domains produces
    to ensure the migration didn't alter any principle IDs for existing domains.
    """

    def test_existing_domain_prefixes_unchanged(self):
        """Frontmatter prefix values must match DOMAIN_PREFIXES for all 8 domains."""
        docs_path = Path(__file__).parent.parent / "documents"

        from ai_governance_mcp.config import _parse_frontmatter

        with patch("sentence_transformers.SentenceTransformer"):
            from ai_governance_mcp.extractor import DocumentExtractor

            expected_prefixes = DocumentExtractor.DOMAIN_PREFIXES

        for domain_name, expected_prefix in expected_prefixes.items():
            if domain_name == "constitution":
                fm = _parse_frontmatter(docs_path / "constitution.md")
            else:
                candidates = list(docs_path.glob("title-*-*.md"))
                fm = None
                for c in candidates:
                    if c.stem.endswith("-cfr"):
                        continue
                    parsed = _parse_frontmatter(c)
                    if parsed and parsed.get("domain") == domain_name:
                        fm = parsed
                        break

            assert fm is not None, f"No frontmatter found for domain {domain_name}"
            assert fm.get("prefix") == expected_prefix, (
                f"Prefix mismatch for {domain_name}: "
                f"frontmatter={fm.get('prefix')!r}, DOMAIN_PREFIXES={expected_prefix!r}"
            )
