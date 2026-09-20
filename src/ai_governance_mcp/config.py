"""Configuration management for AI Governance MCP Server.

Per specification v4: Configuration for hybrid retrieval (BM25 + semantic + reranking).
Logging must use stderr (stdout reserved for MCP JSON-RPC).
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml  # nosec B506 — safe_load only
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from .models import DomainConfig
from .path_resolution import safe_cwd


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


_ROOT_WARNING_EMITTED = False


def _warn_root_not_found_once(*, cwd_available: bool) -> None:
    """Warn that the data root could not be found — at most once per process.

    WHY ONCE. ``_find_project_root`` is called from the telemetry write path, so it
    runs twice per ``evaluate_governance`` call. When the working directory has
    been deleted the marker search fails every single time, and the unguarded
    version emitted two warnings per governance call for the life of the process.
    That is the alert-fatigue pattern ``_record_write_failure`` is careful to avoid,
    arriving from a sibling function — and this repo has already recorded noisy
    checks training people to reach for bypass flags.

    Repeating it would not even help: the advice ("set these env vars") is wrong
    for the dead-directory case, which is why that case is named explicitly.
    """
    global _ROOT_WARNING_EMITTED
    if _ROOT_WARNING_EMITTED:
        return
    _ROOT_WARNING_EMITTED = True
    detail = "" if cwd_available else " (the process working directory is unavailable)"
    logging.getLogger("ai_governance_mcp").warning(
        "Could not find ai-governance data directory%s. "
        "Set AI_GOVERNANCE_DOCUMENTS_PATH and AI_GOVERNANCE_INDEX_PATH "
        "environment variables, or run: python -m ai_governance_mcp.config_generator",
        detail,
    )


def _find_project_root() -> Path:
    """Find the ai-governance-mcp data root directory.

    Uses CWD-based search (walks up from current directory) looking for
    ai-governance markers: ``documents/constitution.md``, any
    ``documents/title-*-*.md``, or ``documents/domains.json``.

    Note: config_generator.py uses __file__-based root detection instead,
    since it's a CLI tool that needs to find templates relative to the
    package installation.

    An unavailable working directory (deleted out from under a running process —
    see ``safe_cwd``) skips the walk-up and falls through to the configured
    fallback. It does NOT raise: this function is reached from the telemetry
    write path on every governance call, and a raise there discarded a governance
    verdict that had already been computed.
    """
    cwd = safe_cwd()

    if cwd is not None:
        for path in [cwd] + list(cwd.parents):
            if _has_governance_marker(path):
                return path

    fallback = Path.home() / ".ai-governance"
    if not _has_governance_marker(fallback):
        _warn_root_not_found_once(cwd_available=cwd is not None)
    return fallback


def _user_data_root() -> Path:
    """Where THIS USER's governance data lives — never inside the corpus checkout.

    WHY THIS IS SEPARATE FROM ``_find_project_root()`` (session-268)
    ---------------------------------------------------------------
    ``documents/`` is the PRODUCT: it ships with the repo, every user gets the same
    thing, and it is read-only in normal use. The Reference Library is the opposite —
    it is written at runtime by ``capture_reference`` and accumulates lessons specific
    to one person across all of their projects. Storing both under the same root meant
    one directory doing two jobs, and the consequences were measured, not theorized:

      * A session working in an UNRELATED project wrote a capture into this repo's
        working tree (verified by file content and mtime), because the corpus root is
        pinned machine-wide. The checkout was therefore never clean, and per AGENTS.md
        a dirty primary blocks a sibling session's fast-forward merge.
      * A downloader who captures a reference writes into their clone of OUR git repo.
        Reproduced: their next ``git pull`` is refused outright with uncommitted index
        changes, or hits an unmergeable binary conflict on ``.npy`` once committed.

    So the default lives outside any checkout. The user decides where their own library
    goes via ``AI_GOVERNANCE_REFERENCE_LIBRARY_PATH``; the default just has to be
    somewhere that is theirs and is not a git working tree we also publish.

    ``~/.ai-governance`` is not a new invention here — ``enforcement.py`` already keeps
    ``enforcement-state.json`` there, and the sibling Context Engine keeps every
    per-project index under ``~/.context-engine``. This adopts the convention the rest
    of the stack already follows.

    ``logs_path`` JOINED THIS SET AT COMPLIANCE REVIEW #17 (session-270), and the
    omission was not cosmetic. It kept deriving from ``_find_project_root()`` — a CWD
    walk-up for a ``documents/`` marker that **every git worktree also carries** — so
    the telemetry fragmented once per checkout. Measured on one machine: four
    ``governance_audit.jsonl`` trees, three of them written the same day (1908 records
    in the main checkout, 487 under ``~/.ai-governance``, 7 in a sibling worktree).

    Why that is worse than untidy: ``scripts/analyze_feedback_loop.py`` computes M-001 /
    M-003 / M-004 and the ``dead_principles`` list from ONE directory, so a principle
    retrieved only from a worktree session reads as never-retrieved — the error runs in
    the direction that would justify DELETING governance content. And the fragmentation
    scales with concurrent worktrees, which AGENTS.md now names the default operating
    mode. The argument in this docstring always applied to logs verbatim; only the field
    was missed.
    """
    root = os.environ.get("AI_GOVERNANCE_USER_DATA_ROOT")
    return Path(root).expanduser() if root else Path.home() / ".ai-governance"


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
        default_factory=lambda: _user_data_root() / "index",
        description="Path to index files (JSON + embeddings) — a BUILD ARTIFACT",
    )
    logs_path: Path = Field(
        default_factory=lambda: _user_data_root() / "logs",
        description=(
            "Path to governance telemetry — audit, reasoning, query and feedback logs. "
            "USER DATA, like the Reference Library: written at runtime, accumulates "
            "across every project this server serves, never part of the published repo."
        ),
    )
    reference_library_path: Path = Field(
        default_factory=lambda: _user_data_root() / "reference-library",
        description="Path to the Reference Library (USER DATA — defaults outside the repo)",
    )

    private_reference_library_path: Path = Field(
        default_factory=lambda: _user_data_root() / "private-reference-library",
        description="Private (never-published) Reference Library entries",
    )

    @field_validator(
        "reference_library_path",
        "private_reference_library_path",
        "index_path",
        "documents_path",
        "logs_path",
    )
    @classmethod
    def _expand_and_absolutize(cls, v: Path) -> Path:
        """Expand `~` and absolutize — these paths steer filesystem reads AND writes.

        `_user_data_root()` expands its env var; the FIELD env vars did not, so
        `AI_GOVERNANCE_REFERENCE_LIBRARY_PATH=~/lib` created a literal `~` directory in
        the process CWD, and the private-library sibling (`path.parent / ...`) then
        resolved against the CWD too — landing in whatever project the MCP host happened
        to launch from. That is precisely the cross-project contamination this split was
        made to end, reintroduced through a different door. Found by code review.

        A RELATIVE path with no working directory to resolve it against is a hard
        error, and deliberately so — unlike the other cwd sites, which degrade.
        There is no safe substitute: guessing a base would silently point a WRITE
        path (logs, reference library) at a directory the operator never named.
        This runs at ``Settings`` construction, so it fails at startup with an
        actionable message rather than mid-call.

        A TRAVERSAL SEQUENCE IS ALSO REJECTED HERE, not only at write time.
        ``_validate_log_path`` has always refused ``..`` in a log path, but it runs
        per write — which is AFTER a governance verdict has been computed. So a
        misconfigured ``AI_GOVERNANCE_LOGS_PATH=/tmp/../tmp`` used to surface as a
        failed tool call rather than a failed startup, and the operator learned
        about their configuration error from a discarded assessment. Configuration
        and security invariants belong before the first verdict exists; durability
        is the only part that may degrade. (Both reviewers converged on this
        ordering independently.) The per-write check stays as defence in depth.
        """
        if ".." in str(v):
            raise ValueError(
                f"Path traversal sequence in configured path {v!r}. Provide a "
                "canonical absolute path via the AI_GOVERNANCE_*_PATH env var."
            )
        p = Path(v).expanduser()
        if p.is_absolute():
            return p
        base = safe_cwd()
        if base is None:
            raise ValueError(
                f"Cannot resolve relative path {v!r}: the process working directory is "
                "unavailable (deleted?). Set this path as an absolute path via its "
                "AI_GOVERNANCE_*_PATH environment variable."
            )
        return (base / p).resolve()

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

    # Keyword-only S-Series adjudication (BACKLOG #73, plan async-giggling-wren).
    # A CRITICAL keyword with no S-Series principle retrieved is a topic mention,
    # not a veto. A fresh-context judge (keyless Codex) adjudicates it benign-vs-
    # genuine, floored by the deterministic insecure-persistence net.
    keyword_judge_mode: Literal["off", "shadow", "active"] = Field(
        default="active",
        description="Keyword-only adjudication routing mode: "
        "'off' (skip the layer entirely — pre-#73 behavior), "
        "'shadow' (run the layer + record the verdict, but keep ESCALATE routing), "
        "'active' (route on the verdict: benign→REVIEW, genuine/floor/unavailable→ESCALATE "
        "— the default since Stage-2 flip, session-258). "
        "Change takes effect on server restart (settings are a cached singleton).",
    )
    keyword_judge_timeout: int = Field(
        default=25,
        description="Seconds before the keyword adjudicator gives up on the judge "
        "(→ unavailable → ESCALATE). Set from the Stage-1 measured latency "
        "(median 4.6s, max 11.9s over 24 calls, 2026-07-05); 25s is ~2x max "
        "headroom, and a clip fails safe to ESCALATE.",
    )
    keyword_judge_model: str | None = Field(
        default=None,
        description="Optional Codex model override for the keyword adjudicator "
        "(None = the CLI default).",
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

    # Make the MCP SDK's own loggers CONTROLLABLE (BACKLOG #205).
    #
    # BE PRECISE ABOUT WHAT THIS DOES — an earlier version of this comment claimed it
    # "breaks the silence" on SDK faults, and that was FALSE. `logging.lastResort` is a
    # `_StderrHandler(WARNING)` that fires whenever no handler is found anywhere in a
    # record's ancestor chain, so `mcp.*` records at WARNING+ were ALREADY reaching
    # stderr before this existed — unformatted, but not silent. Getting that wrong in a
    # bug that has already survived two wrong root causes is exactly how a third one
    # gets written down, so: this attaches a formatter and, crucially, makes the LEVEL
    # follow our own, which `lastResort` cannot do.
    #
    # THAT is the diagnostic win. The record that actually matters is emitted at DEBUG
    # by `mcp/server/lowlevel/server.py`:
    #
    #     logger.debug("Response for %s dropped - transport closed", ...)
    #
    # It sits below `lastResort`'s WARNING floor and is therefore invisible by default —
    # which is why a dropped response looked like a clean shutdown. With the level wired
    # to `level` here, `AI_GOVERNANCE_LOG_LEVEL=DEBUG` now surfaces it. Do that when
    # diagnosing a transport problem; the default stays quiet because DEBUG also emits a
    # per-request "Processing request of type ..." line with no operational value.
    sdk_logger = logging.getLogger("mcp")
    if not sdk_logger.handlers:
        # NOTSET-only so a caller who deliberately set a level before import keeps it.
        # `setup_logging()` runs at module import (retrieval.py, server/_app.py,
        # extractor.py), so an unconditional set would silently clobber exactly the
        # "raise it to DEBUG to diagnose" move this comment recommends.
        if sdk_logger.level == logging.NOTSET:
            sdk_logger.setLevel(getattr(logging, level.upper()))
        # stderr, never stdout: stdout carries ONLY MCP protocol messages.
        sdk_handler = logging.StreamHandler(stream=sys.stderr)
        sdk_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        sdk_logger.addHandler(sdk_handler)

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
