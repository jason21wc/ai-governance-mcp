"""Configuration management for AI Governance MCP Server.

Per specification v4: Configuration for hybrid retrieval (BM25 + semantic + reranking).
Logging must use stderr (stdout reserved for MCP JSON-RPC).
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from .models import DomainConfig


# M2 FIX: JSON formatter for structured logging
class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging.

    M2 FIX: Enables machine-parseable log output.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def _find_project_root() -> Path:
    """Find project root by looking for pyproject.toml or documents folder."""
    cwd = Path.cwd()

    for path in [cwd] + list(cwd.parents):
        if (path / "pyproject.toml").exists() or (path / "documents").exists():
            return path

    return Path.home() / ".ai-governance"


class Settings(BaseSettings):
    """Server configuration via environment variables.

    Uses pydantic-settings for automatic env var loading.
    Prefix: AI_GOVERNANCE_
    """

    # Paths
    documents_path: Path = Field(
        default_factory=lambda: _find_project_root() / "documents",
        description="Path to governance documents directory",
    )
    index_path: Path = Field(
        default_factory=lambda: _find_project_root() / "index",
        description="Path to index files (JSON + embeddings)",
    )
    logs_path: Path = Field(
        default_factory=lambda: _find_project_root() / "logs",
        description="Path to feedback and query logs",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Embedding model
    # BGE-small-en-v1.5: 512 token max (vs 256 for MiniLM), better quality
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="Sentence-transformers model for embeddings",
    )
    embedding_dimensions: int = Field(
        default=384,
        description="Embedding vector dimensions (must match model)",
    )

    # Reranking model
    rerank_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model for reranking",
    )
    rerank_top_k: int = Field(
        default=20,
        description="Number of candidates to rerank",
    )

    # Hybrid retrieval weights
    semantic_weight: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Weight for semantic similarity (1 - this = BM25 weight)",
    )

    # Thresholds
    min_score_threshold: float = Field(
        default=0.3,
        description="Minimum combined score for inclusion",
    )
    max_results: int = Field(
        default=10,
        description="Maximum principles returned per query",
    )
    confidence_high_threshold: float = Field(
        default=0.7,
        description="Score threshold for HIGH confidence",
    )
    confidence_medium_threshold: float = Field(
        default=0.4,
        description="Score threshold for MEDIUM confidence",
    )

    # Domain routing
    domain_similarity_threshold: float = Field(
        default=0.25,
        description="Minimum similarity for domain to be included",
    )
    max_domains: int = Field(
        default=3,
        description="Maximum domains to search per query",
    )

    # Performance
    latency_target_ms: float = Field(
        default=100.0,
        description="Target retrieval latency in milliseconds",
    )

    # Adaptive retrieval (feedback-based score adjustment)
    enable_feedback_adaptation: bool = Field(
        default=True,
        description="Enable feedback-driven score adjustment for principles",
    )
    feedback_min_ratings: int = Field(
        default=5,
        description="Minimum ratings required before applying score adjustment (per contrarian review: 3 too low)",
    )
    feedback_boost_threshold: float = Field(
        default=4.0,
        description="Average rating threshold for positive boost (≥ this gets boosted)",
    )
    feedback_penalty_threshold: float = Field(
        default=2.0,
        description="Average rating threshold for negative penalty (≤ this gets penalized)",
    )
    feedback_boost_amount: float = Field(
        default=0.1,
        description="Score boost for high-rated principles (added to combined score)",
    )
    feedback_penalty_amount: float = Field(
        default=0.05,
        description="Score penalty for low-rated principles (subtracted from combined score)",
    )

    # M2 FIX: Logging format (json or text)
    log_format: str = Field(
        default="text",
        description="Log format: 'json' for structured logging, 'text' for human-readable",
    )

    # M3 FIX: Log rotation settings
    log_max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        description="Maximum log file size in bytes before rotation",
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep",
    )

    model_config = {
        "env_prefix": "AI_GOVERNANCE_",
        "env_file": ".env",
        "extra": "ignore",
    }


def setup_logging(
    level: str = "INFO",
    log_format: str = "text",
    log_file: Path | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure logging to stderr (stdout reserved for MCP JSON-RPC).

    Per LEARNING-LOG.md: MCP protocol uses stdout for JSON-RPC messages.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: 'json' for structured logging, 'text' for human-readable.
        log_file: Optional path for file-based logging with rotation.
        max_bytes: Maximum log file size before rotation (M3 FIX).
        backup_count: Number of backup files to keep (M3 FIX).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("ai_governance_mcp")
    logger.setLevel(getattr(logging, level.upper()))

    if not logger.handlers:
        # M2 FIX: Choose formatter based on log_format setting
        if log_format.lower() == "json":
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        # stderr handler (always present for MCP compatibility)
        stderr_handler = logging.StreamHandler(stream=sys.stderr)
        stderr_handler.setFormatter(formatter)
        logger.addHandler(stderr_handler)

        # M3 FIX: Optional rotating file handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def load_settings() -> Settings:
    """Load settings from environment and .env file."""
    return Settings()


def load_domains_registry(settings: Settings) -> list[DomainConfig]:
    """Load domain configurations from domains.json.

    Per specification v4: Domain registry enables adding new domains
    without code changes. Descriptions enable semantic routing.
    """
    registry_path = settings.documents_path / "domains.json"

    if not registry_path.exists():
        return _default_domains()

    with open(registry_path) as f:
        data = json.load(f)

    # Handle both list and dict formats
    if isinstance(data, list):
        return [DomainConfig(**domain_data) for domain_data in data]
    else:
        return [DomainConfig(**domain_data) for domain_data in data.values()]


def _default_domains() -> list[DomainConfig]:
    """Default domain configurations per specification v4.

    Descriptions are used for semantic domain routing.
    """
    return [
        DomainConfig(
            name="constitution",
            display_name="Constitution",
            principles_file="ai-interaction-principles.md",
            methods_file=None,
            description=(
                "Universal behavioral rules for AI interaction. Safety principles, "
                "core behavioral guidelines, quality standards, operational rules, "
                "growth mindset, and meta-awareness. Applies to all AI interactions."
            ),
            priority=0,  # Highest priority - always included
        ),
        DomainConfig(
            name="ai-coding",
            display_name="AI Coding",
            principles_file="ai-coding-domain-principles.md",
            methods_file="ai-coding-methods.md",
            description=(
                "Software development with AI assistance. Code generation, debugging, "
                "testing, refactoring, code review, pull requests, git workflows, "
                "CI/CD, API design, and software architecture."
            ),
            priority=10,
        ),
        DomainConfig(
            name="multi-agent",
            display_name="Multi-Agent",
            principles_file="multi-agent-domain-principles.md",
            methods_file="multi-agent-methods.md",
            description=(
                "Multi-agent AI systems and orchestration. Agent coordination, "
                "task delegation, handoffs, swarm intelligence, ensemble methods, "
                "pipeline design, and agent communication protocols."
            ),
            priority=20,
        ),
    ]


def ensure_directories(settings: Settings) -> None:
    """Ensure all required directories exist."""
    settings.documents_path.mkdir(parents=True, exist_ok=True)
    settings.index_path.mkdir(parents=True, exist_ok=True)
    settings.logs_path.mkdir(parents=True, exist_ok=True)


# Convenience function for quick access
def get_settings() -> Settings:
    """Get cached settings instance."""
    if not hasattr(get_settings, "_instance"):
        get_settings._instance = load_settings()
    return get_settings._instance
