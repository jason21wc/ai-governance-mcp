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

import yaml  # nosec B506 — safe_load only
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


def _has_governance_marker(path: Path) -> bool:
    """Check if a directory contains ai-governance document markers."""
    docs = path / "documents"
    if not docs.is_dir():
        return False
    if (docs / "constitution.md").exists():
        return True
    if any(docs.glob("title-*-*.md")):
        return True
    if (docs / "domains.json").exists():
        return True
    return False


def _find_project_root() -> Path:
    """Find the ai-governance-mcp data root directory.

    Uses CWD-based search (walks up from current directory) looking for
    ai-governance markers: ``documents/constitution.md``, any
    ``documents/title-*-*.md``, or ``documents/domains.json``.

    Note: config_generator.py uses __file__-based root detection instead,
    since it's a CLI tool that needs to find templates relative to the
    package installation.
    """
    cwd = Path.cwd()

    for path in [cwd] + list(cwd.parents):
        if _has_governance_marker(path):
            return path

    fallback = Path.home() / ".ai-governance"
    if not _has_governance_marker(fallback):
        logging.getLogger("ai_governance_mcp").warning(
            "Could not find ai-governance data directory. "
            "Set AI_GOVERNANCE_DOCUMENTS_PATH and AI_GOVERNANCE_INDEX_PATH "
            "environment variables, or run: python -m ai_governance_mcp.config_generator"
        )
    return fallback


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
    review_score_threshold: float = Field(
        default=0.5,
        description="Minimum best-principle score to return REVIEW assessment. "
        "Below this, assessment is PROCEED even when principles are surfaced.",
    )
    s_series_score_threshold: float = Field(
        default=0.5,
        description="Minimum score for S-Series semantic promotion to ESCALATE. "
        "Below this, S-Series principles appear in results but don't trigger veto. "
        "Keyword detection is unaffected by this threshold.",
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


def _parse_frontmatter(file_path: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        result = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    if not isinstance(result, dict):
        return None
    return result


def _methods_file_for(principles_path: Path) -> str | None:
    """Derive methods filename from a principles file by convention."""
    name = principles_path.stem
    if name == "constitution":
        candidate = principles_path.parent / "rules-of-procedure.md"
    else:
        candidate = principles_path.parent / f"{name}-cfr.md"
    return candidate.name if candidate.exists() else None


def discover_domains(documents_path: Path) -> list[DomainConfig]:
    """Discover domains from filesystem by scanning document frontmatter.

    Looks for constitution.md and title-*-*.md files with YAML frontmatter
    containing domain metadata (domain, prefix, display_name, description,
    priority). Domains are sorted by priority.
    """
    _logger = logging.getLogger("ai_governance_mcp")
    domains: list[DomainConfig] = []

    candidates: list[Path] = []
    constitution = documents_path / "constitution.md"
    if constitution.exists():
        candidates.append(constitution)
    candidates.extend(
        f
        for f in sorted(documents_path.glob("title-*-*.md"))
        if not f.stem.endswith("-cfr")
    )

    for file_path in candidates:
        fm = _parse_frontmatter(file_path)
        if fm is None or "domain" not in fm:
            _logger.warning("Skipping %s — no domain frontmatter", file_path.name)
            continue

        domain = DomainConfig(
            name=fm["domain"],
            display_name=fm.get("display_name", fm["domain"].replace("-", " ").title()),
            principles_file=file_path.name,
            methods_file=_methods_file_for(file_path),
            description=fm.get("description", ""),
            priority=fm.get("priority", 100),
            prefix=fm.get("prefix"),
        )
        domains.append(domain)

    if domains:
        domains.sort(key=lambda d: d.priority)
        _logger.info(
            "Discovered %d domain(s): %s",
            len(domains),
            ", ".join(d.name for d in domains),
        )
    return domains


def load_domains_registry(settings: Settings) -> list[DomainConfig]:
    """Load domain configurations via filesystem discovery with optional overrides.

    Priority order:
    1. Filesystem discovery (frontmatter in constitution.md / title-*-*.md)
    2. domains.json overrides (merges fields over discovered defaults)
    3. Hardcoded fallback (only if both discovery and domains.json fail)
    """
    discovered = discover_domains(settings.documents_path)

    registry_path = settings.documents_path / "domains.json"
    if registry_path.exists():
        try:
            with open(registry_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            _logger = logging.getLogger("ai_governance_mcp")
            _logger.warning("Failed to parse %s — skipping overrides", registry_path)
            data = None

        overrides: dict[str, dict] = {}
        if data is None:
            pass
        elif isinstance(data, list):
            for entry in data:
                if "name" in entry:
                    overrides[entry["name"]] = entry
        else:
            overrides = {
                k: v
                for k, v in data.items()
                if not k.startswith("_") and isinstance(v, dict)
            }

        if discovered:
            for domain in discovered:
                if domain.name in overrides:
                    override = overrides[domain.name]
                    for field in ("display_name", "description", "priority", "prefix"):
                        if field in override:
                            setattr(domain, field, override[field])
        elif overrides:
            return [DomainConfig(**v) for v in overrides.values()]

    if not discovered:
        return [
            DomainConfig(
                name="constitution",
                display_name="Constitution",
                principles_file="constitution.md",
                methods_file="rules-of-procedure.md",
                description="Universal behavioral rules for AI interaction.",
                priority=0,
            )
        ]

    return discovered


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
