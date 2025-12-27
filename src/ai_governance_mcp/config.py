"""Configuration management for AI Governance MCP Server.

Per specification v3: Configuration from environment and domains.json registry.
Logging must use stderr (stdout reserved for MCP JSON-RPC).
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .models import DomainConfig


def _find_project_root() -> Path:
    """Find project root by looking for pyproject.toml or documents folder."""
    # Start from current working directory
    cwd = Path.cwd()

    # Check current directory and parents for project markers
    for path in [cwd] + list(cwd.parents):
        if (path / "pyproject.toml").exists() or (path / "documents").exists():
            return path

    # Fall back to home directory location
    return Path.home() / ".ai-governance"


class ServerConfig(BaseModel):
    """Server-wide configuration."""

    documents_path: Path = Field(
        default_factory=lambda: _find_project_root() / "documents",
        description="Path to governance documents directory",
    )
    index_path: Path = Field(
        default_factory=lambda: _find_project_root() / "index",
        description="Path to extracted index files",
    )
    cache_path: Path = Field(
        default_factory=lambda: _find_project_root() / "cache",
        description="Path to cached principle content",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    audit_log_enabled: bool = Field(default=True, description="Enable audit logging")
    audit_log_path: Optional[Path] = Field(
        default_factory=lambda: _find_project_root() / "audit.log",
        description="Path to audit log file",
    )

    # Scoring weights per specification v3 §3.2.3
    keyword_weight: float = Field(default=1.0)
    synonym_weight: float = Field(default=0.8)
    phrase_weight: float = Field(default=2.0)
    failure_indicator_weight: float = Field(default=1.5)
    s_series_multiplier: float = Field(default=10.0)

    # Thresholds
    min_score_threshold: float = Field(default=0.5, description="Minimum score for inclusion")
    max_principles_per_domain: int = Field(default=10, description="Max principles returned per domain")


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure logging to stderr (stdout reserved for MCP JSON-RPC).

    Per LEARNING-LOG.md: MCP protocol uses stdout for JSON-RPC messages.
    """
    logger = logging.getLogger("ai_governance_mcp")
    logger.setLevel(getattr(logging, level.upper()))

    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

    return logger


def load_config() -> ServerConfig:
    """Load server configuration from environment variables."""
    config = ServerConfig()

    # Override from environment
    if docs_path := os.environ.get("AI_GOVERNANCE_DOCUMENTS_PATH"):
        config.documents_path = Path(docs_path)
    if index_path := os.environ.get("AI_GOVERNANCE_INDEX_PATH"):
        config.index_path = Path(index_path)
    if cache_path := os.environ.get("AI_GOVERNANCE_CACHE_PATH"):
        config.cache_path = Path(cache_path)
    if log_level := os.environ.get("AI_GOVERNANCE_LOG_LEVEL"):
        config.log_level = log_level
    if audit_enabled := os.environ.get("AI_GOVERNANCE_AUDIT_ENABLED"):
        config.audit_log_enabled = audit_enabled.lower() in ("true", "1", "yes")

    return config


def load_domains_registry(config: ServerConfig) -> dict[str, DomainConfig]:
    """Load domain configurations from domains.json.

    Per specification v3 §2.1: Domain registry enables adding new domains
    without code changes.
    """
    registry_path = config.documents_path / "domains.json"

    if not registry_path.exists():
        # Return default domains if registry doesn't exist
        return _default_domains()

    with open(registry_path) as f:
        data = json.load(f)

    return {name: DomainConfig(**domain_data) for name, domain_data in data.items()}


def _default_domains() -> dict[str, DomainConfig]:
    """Default domain configurations per specification v3."""
    return {
        "constitution": DomainConfig(
            name="constitution",
            display_name="Constitution",
            principles_file="ai-interaction-principles.md",
            methods_file=None,
            trigger_keywords=[],  # Always searched
            trigger_phrases=[],
            priority=0,  # Highest priority
        ),
        "ai-coding": DomainConfig(
            name="ai-coding",
            display_name="AI Coding",
            principles_file="ai-coding-domain-principles.md",
            methods_file="ai-coding-methods.md",
            trigger_keywords=[
                "code",
                "coding",
                "programming",
                "software",
                "development",
                "implementation",
                "debug",
                "debugging",
                "testing",
                "refactor",
                "refactoring",
                "api",
                "function",
                "class",
                "module",
                "bug",
                "error",
                "exception",
                "compile",
                "build",
                "deploy",
            ],
            trigger_phrases=[
                "write code",
                "fix bug",
                "code review",
                "pull request",
                "unit test",
                "integration test",
            ],
            priority=10,
        ),
        "multi-agent": DomainConfig(
            name="multi-agent",
            display_name="Multi-Agent",
            principles_file="multi-agent-domain-principles.md",
            methods_file="multi-agent-methods.md",
            trigger_keywords=[
                "agent",
                "agents",
                "multi-agent",
                "orchestration",
                "coordinator",
                "delegation",
                "handoff",
                "collaboration",
                "swarm",
                "ensemble",
                "pipeline",
            ],
            trigger_phrases=[
                "multiple agents",
                "agent communication",
                "agent coordination",
                "agent handoff",
            ],
            priority=20,
        ),
    }


def ensure_directories(config: ServerConfig) -> None:
    """Ensure all required directories exist."""
    config.documents_path.mkdir(parents=True, exist_ok=True)
    config.index_path.mkdir(parents=True, exist_ok=True)
    config.cache_path.mkdir(parents=True, exist_ok=True)
    if config.audit_log_path:
        config.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
