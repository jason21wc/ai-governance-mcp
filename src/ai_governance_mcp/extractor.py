"""Document extractor for AI Governance documents.

Build-time extraction creates index and embeddings
for hybrid retrieval (BM25 + semantic search).
"""

import hashlib
import json
import os
import re
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .config import (
    Settings,
    load_settings,
    load_domains_registry,
    setup_logging,
    ensure_directories,
)

# safe_load only, never yaml.load
import yaml  # nosec B506

from .models import (
    DomainConfig,
    DomainIndex,
    EmbeddingCanary,
    GlobalIndex,
    Method,
    MethodMetadata,
    Principle,
    PrincipleMetadata,
    ReferenceEntry,
)

logger = setup_logging()

# A rebuild may not replace an index with one holding less than this fraction of
# the previous entry count in ANY category, unless --force. Set at 0.9 rather than
# 1.0 so ordinary churn (a retired method, a renamed principle) does not nag —
# the target is the catastrophic case, where a path problem silently drops most of
# a category. Measured instance: 80 reference entries -> 3. See
# DocumentExtractor._refuse_silent_narrowing.
INDEX_SHRINK_TOLERANCE = 0.9


# Structural-boundary detection for unit extraction.
#
# WHY THIS EXISTS: before this, a principle or method ran until the next heading
# the *unit* pattern recognised — or to EOF. Every intervening section belonged to
# it. `## Historical Amendments` in constitution.md therefore lived inside
# `meta-safety-transparent-limitations`, giving it a 74,441-char body (real text:
# ~41 lines). 48 principles and 166 methods over-absorbed this way. The damage is
# not cosmetic: _generate_metadata mines trigger_phrases/failure_indicators from
# the body and retrieval.py appends those to the BM25 text UNCAPPED, so a
# document's changelog was contributing search tokens to a safety principle.
#
# A unit now ends at the next ATX heading of equal-or-shallower level.
#
# MIND THE DEPTH BUDGET when editing the corpus. The deepest units are at `####`
# (16 principles in title-10-ai-coding.md, 181 methods across the -cfr files), and
# `<=` means a `####` heading closes a `####` unit. So a `####` unit admits NO
# heading sub-structure — use bold labels (`**How AI Applies This Principle:**`,
# which is what the corpus actually uses) rather than a heading. Adding a heading
# under a `####` unit truncates its body with no count change, no failing test and
# no warning.
_FENCE_RE = re.compile(r"^[ \t]*(?:```|~~~)")
_HEADING_RE = re.compile(r"^(#{1,6})\s")


def _heading_level(line: str) -> int | None:
    """ATX heading level, or None when the line is not a heading.

    The trailing ``\\s`` in _HEADING_RE is load-bearing: ``#hashtag`` is not a
    heading, and ``#!/usr/bin/env`` inside prose must not close a unit.
    """
    m = _HEADING_RE.match(line)
    return len(m.group(1)) if m else None


def _tmp_suffix() -> str:
    """A temp-file suffix unique to the writing process and thread.

    WHY THIS IS NOT JUST ``.tmp``
    -----------------------------
    The three index files are each written atomically (tmp + fsync + rename),
    but they are NOT written as a unit — ``extract_all`` saves the two ``.npy``
    files first and ``global_index.json`` last, and ``retrieval.py`` keys its
    freshness check on that ordering. Atomicity per file therefore buys nothing
    against a SECOND extractor process: with a fixed ``.tmp`` name, two
    concurrent rebuilds write the same temp path (interleaved bytes), and their
    renames can interleave to leave ``global_index.json`` from run A paired with
    ``content_embeddings.npy`` from run B.

    That mismatch is not hypothetical here. A pairing defect of exactly this
    shape misattributed all 1041 index rows for six days while every shape gate
    and the whole suite stayed green (LEARNING-LOG, row-misattribution, #218) —
    the failure is silent because both files are individually well-formed.

    Per-process temp names make concurrent rebuilds independent: each writes its
    own temp file, and the last rename wins with a COMPLETE, self-consistent set
    rather than a spliced one. This is the pattern already proven in this repo at
    ``context_engine/storage/filesystem.py:_atomic_write_json``, adopted here
    rather than reinvented.

    NOT a lock. Two rebuilds still race; this makes the loser's work discarded
    instead of blended. That is the correct trade — a whole stale index is
    recoverable by rebuilding, a spliced one is undetectable.
    """
    return f".{os.getpid()}.{threading.get_ident()}.tmp"


def _load_local_embedder(model_name: str):
    """Load the SentenceTransformer, with a legible failure and a cached-model retry.

    TWO AMBIENT DEPENDENCIES MADE THE CANONICAL REBUILD PATH FRAGILE, and both
    produced errors that named neither cause. `AGENTS.md` documents the rebuild as
    `python -m ai_governance_mcp.extractor`, and on this machine `python` resolves
    to `/opt/anaconda3/bin/python3`, which happens to carry sentence-transformers.
    The project's own `.venv/bin/python` does NOT — so the documented command works
    by accident of PATH ordering, and fails with a bare ModuleNotFoundError that
    says nothing about which interpreter ran or how to fix it.

    Same shape as the reason `content_patterns.py` exists: a missing
    scientific-computing dependency silently disabling a security scan. The fix
    there and here is the same — make the failure name itself.

    NETWORK: sentence-transformers contacts Hugging Face for repo metadata even
    when every weight is already cached, so a transient 403/timeout fails a build
    that needs nothing from the network. If the first load fails for any reason and
    a cached copy exists, this retries with `local_files_only=True`. Deliberately a
    RETRY and not the default: forcing local-only would break a first-time user who
    genuinely has to download the model.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised via unit test
        raise ModuleNotFoundError(
            f"{exc}\n\n"
            f"The interpreter running this build is: {sys.executable}\n"
            "sentence-transformers is required to build the index and is not "
            "importable there.\n\n"
            "This usually means the canonical command "
            "`python -m ai_governance_mcp.extractor` resolved to an interpreter "
            "other than the one holding the project's dependencies. Install the "
            "extra into THIS interpreter, or invoke the one that has it:\n"
            f"    {sys.executable} -m pip install 'sentence-transformers'\n"
        ) from exc

    logger.info("Loading embedding model locally: %s", model_name)
    try:
        return SentenceTransformer(
            model_name,
            trust_remote_code=False,
            model_kwargs={"use_safetensors": True},
        )
    except Exception as exc:
        logger.warning(
            "Model load failed (%s); retrying against the local cache only. "
            "A cached model needs no network, and metadata lookups should not "
            "fail an otherwise-offline build.",
            exc,
        )
        return SentenceTransformer(
            model_name,
            trust_remote_code=False,
            local_files_only=True,
            model_kwargs={"use_safetensors": True},
        )


class EmbeddingGenerator:
    """Generates embeddings using sentence-transformers.

    Lazy-loads the model to avoid import overhead when not needed.
    """

    def __init__(
        self, model_name: str = "BAAI/bge-small-en-v1.5", force_local: bool = False
    ):
        from .retrieval import ALLOWED_EMBEDDING_MODELS

        if model_name not in ALLOWED_EMBEDDING_MODELS:
            raise ValueError(
                f"Embedding model '{model_name}' not in allowlist. "
                f"Allowed: {sorted(ALLOWED_EMBEDDING_MODELS)}"
            )
        self.model_name = model_name
        # force_local=True bypasses the IPC daemon entirely and loads the
        # canonical local SentenceTransformer. The index build sets this so the
        # committed index is always in the canonical embedding space — the
        # daemon could be serving a direction-divergent model, and a one-shot
        # batch build that exits gains no memory benefit from the daemon anyway
        # (BACKLOG #58). See retrieval._load_index canary gate for the load-side
        # verification that build-space == query-space.
        self._force_local = force_local
        self._model = None

    @property
    def model(self):
        """Lazy load the embedding model.

        Phase 2: tries EmbeddingClient (daemon socket) first. Falls back to
        local SentenceTransformer when socket doesn't exist (Docker/CI/tests).
        When force_local=True the IPC branch is skipped entirely (BACKLOG #58).
        """
        if self._model is None:
            import os

            if (
                not self._force_local
                and os.environ.get("AI_CONTEXT_ENGINE_EMBED_SOCKET", "").strip().lower()
                != "none"
            ):
                try:
                    from .embedding_ipc import DEFAULT_SOCKET_PATH, EmbeddingClient

                    sock_path = os.environ.get(
                        "AI_CONTEXT_ENGINE_EMBED_SOCKET", ""
                    ).strip()
                    check_path = sock_path if sock_path else str(DEFAULT_SOCKET_PATH)
                    if os.path.exists(check_path) and EmbeddingClient.available():
                        self._model = EmbeddingClient()
                        logger.info("Using embedding server (IPC) for extractor")
                        return self._model
                except Exception as e:
                    logger.debug("Extractor IPC client not available: %s", e)

            self._model = _load_local_embedder(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for a list of texts.

        normalize_embeddings=True is explicit (contract clarity): bge already
        L2-normalizes via its Normalize module, so this is idempotent there, but
        stating it removes the implicit dependency (BACKLOG #58 Fix D).
        """
        if not texts:
            return np.array([])
        return self.model.encode(
            texts, normalize_embeddings=True, show_progress_bar=len(texts) > 10
        )

    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        normalize_embeddings=True for parity with embed() — the index's vectors
        are normalized, so any single-text embedding compared against them must
        be too (BACKLOG #58 Fix D).
        """
        return self.model.encode([text], normalize_embeddings=True)[0]

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.model.get_sentence_embedding_dimension()


class ExtractorConfigError(Exception):
    """Raised when extractor configuration is invalid (e.g., missing files)."""

    pass


# --- Body version-surface validation (session-244 validator blind-spot fix) ---------
#
# Shapes replicate real corpus conventions; each check fires ONLY when its surface is
# present, so absence stays legal. Regex anchoring per the plan-stage contrarian:
# H1 = single '#' with the version TRAILING (changelog '### vX.Y.Z' headers can never
# match); Version/Effective-Date lines scan the whole (fence-stripped) body but are
# line-anchored with a digits-then-EOL requirement, so prose ('**Version bump
# rationale**'), placeholders ('**Version:** [Pinned...]'), and transition examples
# ('**Version:** v1.0 → v1.1') can't trip them — whole-body is required because real
# headers put an H2 subtitle before the Version line (Codex close-out catch); the
# changelog current-row check is presence-based, not position-based (order-
# independent), and table-row recognition requires the version+ISO-date shape so data
# tables ('| 0.868 | ...') are never mistaken for changelogs. Constitution-style
# history rows ('#### **vX.Y.Z (Month Year) - ...') are recognized via their own
# pattern.

_FENCED_BLOCK_RE = re.compile(
    r"^[ \t]*```.*?^[ \t]*```[ \t]*$", re.DOTALL | re.MULTILINE
)
_FRONTMATTER_BLOCK_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_H1_TRAILING_VERSION_RE = re.compile(r"^# .*\bv(\d+\.\d+(?:\.\d+)*)\s*$", re.MULTILINE)
_HEADER_VERSION_LINE_RE = re.compile(
    r"^\*\*Version:\*\*\s*v?(\d+\.\d+(?:\.\d+)*)\s*$", re.MULTILINE
)
_HEADER_EFFECTIVE_DATE_RE = re.compile(
    r"^\*\*Effective Date:\*\*\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE
)
_FOOTER_VERSION_RE = re.compile(
    r"^\*Version\s+(\d+\.\d+(?:\.\d+)*)\*\s*$", re.MULTILINE
)
_CHANGELOG_CURRENT_MARKER_RE = re.compile(
    r"^###\s*v?(\d+\.\d+(?:\.\d+)*)\s*\(Current\)", re.MULTILINE
)
_CHANGELOG_H3_ROW_RE = re.compile(r"^###\s*v?(\d+\.\d+(?:\.\d+)*)\b", re.MULTILINE)
_CHANGELOG_H4_BOLD_ROW_RE = re.compile(
    r"^####\s*\*\*v(\d+\.\d+(?:\.\d+)*)\b", re.MULTILINE
)
_CHANGELOG_TABLE_ROW_RE = re.compile(
    r"^\|\s*v?(\d+\.\d+(?:\.\d+)*)\s*\|\s*\d{4}-\d{2}-\d{2}\s*\|", re.MULTILINE
)


def _body_version_surface_problems(
    content: str, fm_version: str, fm_effective_date: str | None
) -> list[str]:
    """Compare every body version/date surface against the frontmatter values.

    Returns human-readable problem strings (empty list = consistent). ``content``
    is the full file text including frontmatter (universal-newline text — callers
    read via ``read_text``); fenced code blocks are stripped before scanning so
    embedded template/example changelogs cannot false-positive. An UNCLOSED fence
    is left in place (its content gets scanned) — fails toward flagging, never
    toward a silent miss.
    """
    body = _FRONTMATTER_BLOCK_RE.sub("", content)
    body = _FENCED_BLOCK_RE.sub("", body)
    problems: list[str] = []

    for h1_version in _H1_TRAILING_VERSION_RE.findall(body):
        if h1_version != fm_version:
            problems.append(
                f"H1 title version: v{h1_version} != frontmatter {fm_version}"
            )

    for line_version in _HEADER_VERSION_LINE_RE.findall(body):
        if line_version != fm_version:
            problems.append(
                f"Body **Version:** line: {line_version} != frontmatter {fm_version}"
            )

    if fm_effective_date:
        for line_date in _HEADER_EFFECTIVE_DATE_RE.findall(body):
            if line_date != fm_effective_date:
                problems.append(
                    f"Body **Effective Date:** line: {line_date} != "
                    f"frontmatter {fm_effective_date}"
                )

    for footer_version in _FOOTER_VERSION_RE.findall(body):
        if footer_version != fm_version:
            problems.append(
                f"Footer *Version* line: {footer_version} != frontmatter {fm_version}"
            )

    current_markers = _CHANGELOG_CURRENT_MARKER_RE.findall(body)
    for marker_version in current_markers:
        if marker_version != fm_version:
            problems.append(
                f"Changelog (Current) marker: v{marker_version} != "
                f"frontmatter {fm_version}"
            )

    changelog_rows = (
        set(_CHANGELOG_H3_ROW_RE.findall(body))
        | set(_CHANGELOG_H4_BOLD_ROW_RE.findall(body))
        | set(_CHANGELOG_TABLE_ROW_RE.findall(body))
    )
    if changelog_rows and fm_version not in changelog_rows:
        problems.append(
            f"changelog has no row for frontmatter version {fm_version} "
            f"(silent-bump shape; rows found: {sorted(changelog_rows)[-3:]})"
        )

    return problems


class EmbeddingSpaceError(Exception):
    """Raised when the index build does not run in the canonical local
    embedding space — e.g. force_local failed to take effect and the IPC daemon
    answered the build. Refusing to write a potentially-divergent index loudly
    at build time is better than shipping one that silently degrades to BM25
    (BACKLOG #58)."""

    pass


class ContentSecurityError(Exception):
    """Raised when critical security patterns are detected in governance documents.

    Critical patterns include prompt injection phrases and hidden instructions
    that could compromise AI agents consuming governance content.
    """

    pass


# Severity policy now lives beside the patterns it classifies, in the stdlib-only
# leaf module, so a consumer gets both from one place. Re-exported here.
from .content_patterns import CRITICAL_PATTERNS  # noqa: F401,E402

# `unterminated_code_fence` is a SCANNER-COVERAGE finding, not a content pattern, and it
# is ADVISORY. It was first shipped as CRITICAL; that was wrong for a reason worth keeping
# written down. Fences no longer exempt CRITICAL patterns at all, so an unclosed fence can
# only lose advisory coverage — and a critical severity would have blocked every index
# rebuild off a single malformed reference-library entry, which `capture_reference` can
# write without human review. `documents/` is gated hard on fence parity by the
# repo-hygiene test instead, where the content is version-controlled. BACKLOG #332.
ADVISORY_PATTERNS = {
    "shell_command",
    "base64_payload",
    "data_exfiltration",
    "unterminated_code_fence",
}
_COVERAGE_PATTERNS = {"unterminated_code_fence"}


class ContentSecurityWarning:
    """Warning about suspicious content in governance documents."""

    def __init__(self, file: str, line: int, pattern_type: str, content: str):
        self.file = file
        self.line = line
        self.pattern_type = pattern_type
        self.content = content[:100]  # Truncate for logging

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.pattern_type}]: {self.content}"


# Content-security patterns and normalization now live in a STDLIB-ONLY leaf module
# so consumers can load them without importing this file's numpy/yaml dependencies.
# `scripts/check_content_security.py` importing them from here gave a prompt-injection
# gate a hard numpy dependency, and a missing numpy silently turned it into a
# could-not-run that nothing blocks on. Re-exported so existing imports keep working
# and there is still exactly one definition. See content_patterns.py for the full
# reasoning, and BACKLOG #360 for the ruleset's measured efficacy.
from .content_patterns import (  # noqa: F401,E402
    _INVISIBLE_CATEGORIES,
    _INVISIBLE_CODEPOINTS,
    _is_invisible_char,
    SUSPICIOUS_PATTERNS,
    matches_security_pattern,
    normalize_text_for_security,
    security_views,
)


class DocumentExtractor:
    """Extracts principles and methods from governance markdown documents.

    Creates a GlobalIndex with embeddings for hybrid retrieval.
    """

    # Strip "Section N:" or "Amendment N:" prefixes from principle headers.
    # Anchored to colon delimiter to prevent over-matching on titles starting
    # with Roman numeral characters (I, V, X, L, C). See contrarian review F2
    # and TestConstitutionalTitleStripping for regression tests.
    CONSTITUTIONAL_PREFIX_RE = re.compile(
        r"^(?:Section\s+\d+|Amendment\s+(?:[IVXLC]+(?=\s*:)|\d+(?=\s*:)))\s*:\s*"
    )

    # Detect Article headers to track constitutional context during extraction.
    # Matches: "Article I: ...", "Article II: ...", etc.
    ARTICLE_HEADER_RE = re.compile(
        r"^Article\s+([IVXLC]+)",
        re.IGNORECASE,
    )

    # Roman numeral ↔ integer for constitutional citation generation
    _ROMAN_TO_INT = {
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4,
        "V": 5,
        "VI": 6,
        "VII": 7,
        "VIII": 8,
        "IX": 9,
        "X": 10,
    }
    _INT_TO_ROMAN = {v: k for k, v in _ROMAN_TO_INT.items()}

    def __init__(self, settings: Settings):
        self.settings = settings
        self.domains = load_domains_registry(settings)
        # force_local: the index build must run in the canonical embedding
        # space, never the (possibly divergent) IPC daemon (BACKLOG #58).
        self.embedder = EmbeddingGenerator(settings.embedding_model, force_local=True)

    def validate_domain_files(self) -> None:
        """Pre-flight validation: ensure all configured files exist.

        Raises:
            ExtractorConfigError: If any configured files are missing.
                Lists ALL missing files, not just the first one found.
        """
        missing_files: list[str] = []

        for domain_config in self.domains:
            # Check principles file (required)
            principles_path = (
                self.settings.documents_path / domain_config.principles_file
            )
            if not principles_path.exists():
                missing_files.append(
                    f"  - {domain_config.name}: principles file '{domain_config.principles_file}'"
                )

            # Check methods file (optional, but if configured must exist)
            if domain_config.methods_file:
                methods_path = self.settings.documents_path / domain_config.methods_file
                if not methods_path.exists():
                    missing_files.append(
                        f"  - {domain_config.name}: methods file '{domain_config.methods_file}'"
                    )

        if missing_files:
            files_list = "\n".join(missing_files)
            raise ExtractorConfigError(
                f"Domain configuration references missing files:\n{files_list}\n\n"
                f"Check document frontmatter and ensure domain files exist."
            )

    def validate_content_security(self) -> list[ContentSecurityWarning]:
        """Scan governance documents for suspicious patterns.

        Checks for prompt injection, shell commands, and other potentially
        malicious content that could compromise AI agents consuming this content.

        Returns:
            List of advisory warnings found (non-critical patterns).

        Raises:
            ContentSecurityError: If CRITICAL patterns are detected (prompt injection,
                hidden instructions). These hard-fail extraction because they are
                clear indicators of supply chain attacks.

        Note:
            CRITICAL patterns (prompt_injection, hidden_instruction) cause hard failure
            everywhere. ADVISORY patterns warn only. `unterminated_code_fence` is advisory
            in the reference library and FATAL in `documents/` — see below.

        SEVERITY IS SOURCE-SENSITIVE, and that asymmetry is the whole design:

        - **`documents/` and agent templates** are version-controlled product content, and
          an unclosed fence there does not merely under-scan — it CORRUPTS EXTRACTION.
          `_extract_*` skips its whole loop body while `in_fence`, so after an unbalanced
          fence no further unit is opened and the last open unit swallows the rest of the
          file: **silent unit loss**, in the extractor's own words. Refusing to build a
          corrupt index is the right answer, and the pre-existing claim that this is
          "enforced upstream by the fence-parity check in tests/" is only true if someone
          runs pytest — `python -m ai_governance_mcp.extractor` does not.
        - **The reference library** is user data outside the checkout, written by
          `capture_reference` from a caller's artifact with no human gate. A fatal severity
          there hands any caller a corpus-wide denial of rebuild off one malformed code
          snippet. Advisory, and the malformed entry is the only thing degraded.

        A uniform severity was wrong in one direction or the other whichever value it took;
        a cross-vendor review caught the version that was wrong for `documents/`.
        """
        warnings: list[ContentSecurityWarning] = []
        critical_findings: list[ContentSecurityWarning] = []
        # Coverage findings from VERSIONED trees only. Fatal — see the docstring.
        versioned_coverage: list[ContentSecurityWarning] = []

        def _classify(found: list[ContentSecurityWarning], *, versioned: bool) -> None:
            """Route one file's findings by pattern class and by source trust level."""
            for w in found:
                if w.pattern_type in CRITICAL_PATTERNS:
                    critical_findings.append(w)
                elif w.pattern_type in _COVERAGE_PATTERNS and versioned:
                    versioned_coverage.append(w)
                else:
                    warnings.append(w)

        for domain_config in self.domains:
            # Check principles file
            principles_path = (
                self.settings.documents_path / domain_config.principles_file
            )
            if principles_path.exists():
                _classify(
                    self._scan_file_for_suspicious_content(principles_path),
                    versioned=True,
                )

            # Check methods file
            if domain_config.methods_file:
                methods_path = self.settings.documents_path / domain_config.methods_file
                if methods_path.exists():
                    _classify(
                        self._scan_file_for_suspicious_content(methods_path),
                        versioned=True,
                    )

        # Check agent templates
        agents_path = self.settings.documents_path / "agents"
        if agents_path.exists():
            for agent_file in agents_path.glob("*.md"):
                _classify(
                    self._scan_file_for_suspicious_content(agent_file),
                    versioned=True,
                )

        # Scan reference library files. Same root as the indexing pass above — if these
        # two ever disagree, entries get indexed without being security-scanned.
        lib = self.settings.reference_library_path
        for domain_config in self.domains:
            for ref_dir in [
                lib / domain_config.name,
                self.settings.private_reference_library_path / domain_config.name,
            ]:
                if ref_dir.exists() and not ref_dir.is_symlink():
                    for md_file in ref_dir.glob("*.md"):
                        if md_file.is_symlink():
                            continue
                        _classify(
                            self._scan_file_for_suspicious_content(md_file),
                            versioned=False,
                        )

        # `unterminated_code_fence` is advisory now, so it must not appear here. Enforced
        # with a real branch rather than `assert`: bandit B101 flagged the assert and is
        # right that `python -O` strips it, and an invariant guarding a build-availability
        # decision must not evaporate in an optimised interpreter.
        #
        # It DEMOTES rather than raises, deliberately. Raising is exactly the corpus-wide
        # rebuild denial this severity change exists to prevent, so the safe direction here
        # is to log loudly and carry on. Read the ADVISORY_PATTERNS note before changing it.
        # A coverage failure in a VERSIONED tree is fatal, because there it means silent
        # unit loss and a corrupt index — not merely reduced advisory scanning.
        if versioned_coverage:
            findings_list = "\n".join(f"  - {f}" for f in versioned_coverage)
            raise ContentSecurityError(
                f"CRITICAL: unclosed code fence in version-controlled governance "
                f"content.\n\n{findings_list}\n\n"
                f"This is not only a scanning gap. The unit extractor skips its whole loop "
                f"body while inside a fence, so after an unbalanced fence NO further "
                f"principle or method is opened and the last one absorbs the rest of the "
                f"file — silent unit LOSS, producing an index that looks complete and is "
                f"missing content.\n"
                f"Fix: close the fence. (The same finding in the reference library is only "
                f"advisory, because a caller-written entry must not be able to block every "
                f"rebuild — the asymmetry is deliberate.)"
            )

        misrouted = [
            f for f in critical_findings if f.pattern_type in _COVERAGE_PATTERNS
        ]
        if misrouted:
            logger.error(
                "Coverage findings reached the critical path and were demoted to advisory: "
                "%s. Something re-promoted a coverage pattern to CRITICAL — see the "
                "ADVISORY_PATTERNS comment on why that blocks every index rebuild.",
                [f.pattern_type for f in misrouted],
            )
            critical_findings = [
                f for f in critical_findings if f.pattern_type not in _COVERAGE_PATTERNS
            ]
            warnings.extend(misrouted)

        if critical_findings:
            findings_list = "\n".join(f"  - {f}" for f in critical_findings)
            raise ContentSecurityError(
                f"CRITICAL: Prompt injection or hidden instructions detected!\n\n"
                f"The following patterns were found in governance documents:\n"
                f"{findings_list}\n\n"
                f"This is a potential supply chain attack. Extraction blocked.\n"
                f"\n"
                f"DO NOT wrap this in a code fence to silence it. Fences no longer exempt\n"
                f"critical patterns, and the previous version of this message advised\n"
                f"exactly that — which made the remedy it printed the same action that\n"
                f"hid the finding and left it indexed. If this content genuinely must\n"
                f"exist in the corpus, that is a human decision about the corpus, not a\n"
                f"formatting change."
            )

        return warnings

    def _scan_file_for_suspicious_content(
        self, file_path: Path
    ) -> list[ContentSecurityWarning]:
        """Scan a single file for suspicious patterns.

        CRITICAL PATTERNS ARE NEVER FENCE-EXEMPT. This is the important property, and it
        was not true until the fence exemption was removed for them. The exemption existed
        so that legitimate attack documentation could be wrapped in ``` — but a *deliberate
        exemption* inside the only blocking content gate is an attacker's target, and it was
        reachable two independent ways:

        1. **The two fence recognizers disagreed.** This function used
           ``line.strip().startswith("```")`` while the unit extractor and the repo-hygiene
           parity gate use ``_FENCE_RE`` (``^[ \\t]*(?:```|~~~)``). ``str.strip()`` removes
           ALL Unicode whitespace; ``[ \\t]*`` does not. So a fence indented with U+00A0 was
           a fence *for the scanner* (content skipped) and NOT a fence for the extractor
           (content indexed as a first-class principle). Measured: injection inside such a
           block produced zero findings and still became a retrievable unit. ``~~~`` diverged
           the opposite way. Fixed by using ``_FENCE_RE`` here too — one recognizer, three
           consumers.
        2. **The remediation laundered the attack.** The critical error message used to say
           "if this is legitimate documentation, wrap in a code block (```)" — i.e. the fix
           it printed for a real injection finding was the thing that made it invisible.

        Cost of removing the exemption, measured before doing it: **0 critical hits across
        133 live files** (``documents/`` + the reference library). The escape hatch was not
        load-bearing. ``scaffold.py``'s ingress scanner already used this stricter policy —
        this aligns the blocking scanner with the one that was already right.

        Fences still suppress ADVISORY patterns, which is what they are actually for: shell
        commands and base64 in examples are noise, and there are ~2,575 of them.
        """
        warnings: list[ContentSecurityWarning] = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Track fenced regions to suppress ADVISORY patterns only.
        in_code_block = False
        fence_opened_at = 0

        for line_num, line in enumerate(lines, 1):
            # ONE fence recognizer, shared with the unit extractor and the parity gate.
            if _FENCE_RE.match(line):
                in_code_block = not in_code_block
                if in_code_block:
                    fence_opened_at = line_num
                continue

            # RAW *AND* NORMALIZED. Normalizing alone LOSES detections, because
            # normalization is not monotone for matching: it strips the U+001F that
            # `\s` matches, and folds U+FE65/U+FF1E into the `>` that terminates
            # `[^>]*` in `hidden_instruction`. This BLOCKING scan matched only the
            # normalized view for one commit while `check_content_security` was
            # fixed — the invariant was written in a docstring and two of its three
            # callers did not obey it. See `content_patterns.security_views`.
            normalized_line = normalize_text_for_security(line)

            continuation = lines[line_num] if line_num < len(lines) else ""

            # Check each pattern against both views and, for authority assertions,
            # one bounded continuation line. The shared matcher preserves parity
            # with capture ingress and the repository gate.
            for pattern_type, pattern in SUSPICIOUS_PATTERNS.items():
                if matches_security_pattern(pattern_type, pattern, line, continuation):
                    line_lower = normalized_line.lower()

                    # CRITICAL patterns: NEVER skipped. Not for "example" context, and — as
                    # of the fence-exemption removal — not inside a code fence either.
                    # Critical authority attacks have no legitimate place in indexed
                    # governance content, and a wrapper that suppresses them is a
                    # laundering path rather than a documentation convenience.
                    if pattern_type in CRITICAL_PATTERNS:
                        warnings.append(
                            ContentSecurityWarning(
                                file=str(file_path.name),
                                line=line_num,
                                pattern_type=pattern_type,
                                content=line.strip(),
                            )
                        )
                        continue

                    # ADVISORY patterns: suppressed inside a fence and in example prose.
                    # These legitimately appear in documentation (shell commands, base64
                    # samples) in volume — ~2,575 of them — so the fence exemption still
                    # earns its place HERE, where a false positive costs attention and a
                    # miss costs nothing that blocks.
                    if in_code_block or any(
                        skip in line_lower
                        for skip in ["example", "e.g.", "for instance", "such as"]
                    ):
                        continue

                    warnings.append(
                        ContentSecurityWarning(
                            file=str(file_path.name),
                            line=line_num,
                            pattern_type=pattern_type,
                            content=line.strip(),
                        )
                    )

        # An unterminated fence still under-covers, but only for ADVISORY patterns now, so
        # this is ADVISORY — deliberately downgraded from the CRITICAL it was first shipped
        # as, and the downgrade is a consequence of the fix above rather than a softening.
        #
        # Why it must NOT be critical: `extract_all` calls `validate_content_security`
        # before extracting anything, so a critical finding blocks EVERY index rebuild. The
        # scanned set includes the reference library — user data, outside the checkout,
        # written by `capture_reference`, which is not human-gated and copies a caller's
        # 10,000-char `artifact` verbatim. A code snippet with an unbalanced fence is the
        # single likeliest artifact shape, so a critical severity here hands any caller a
        # corpus-wide denial of rebuild. Measured live: an entry ending in an unclosed
        # ```python fence raised and blocked the build.
        #
        # With critical patterns no longer fence-exempt, an unclosed fence can no longer
        # hide an injection — it can only lose shell-command and base64 advisories, which
        # do not block. Advisory is the honest severity for that.
        #
        # `documents/` keeps a HARD gate on this separately: the repo-hygiene parity test
        # fails the suite on an odd fence count there, where the content is product,
        # version-controlled and reviewed. Different trust levels, different severities.
        if in_code_block:
            # `split("\n")` leaves a trailing "" for any file ending in a newline, which
            # made the reported range one line too long — a wrong number inside a security
            # finding.
            last_line = len(lines) - 1 if lines and lines[-1] == "" else len(lines)
            warnings.append(
                ContentSecurityWarning(
                    file=str(file_path.name),
                    line=fence_opened_at,
                    pattern_type="unterminated_code_fence",
                    # Kept under 100 chars on purpose: `ContentSecurityWarning.__init__`
                    # truncates `content` for logging, so anything past that is lost. The
                    # "critical still scanned" clause is the load-bearing half — without it
                    # a reader assumes the whole file went unscanned — so it goes early.
                    content=(
                        f"unclosed fence at line {fence_opened_at}: advisory patterns to "
                        f"line {last_line} unscanned; critical patterns still scanned"
                    ),
                )
            )

        return warnings

    @staticmethod
    def _parse_frontmatter(content: str) -> dict | None:
        """Parse YAML frontmatter from document content.

        Returns the frontmatter dict if valid, None otherwise.
        Uses yaml.safe_load() exclusively for security.
        Normalizes date values to ISO strings (per CE lesson on YAML date coercion).
        """
        fm_match = re.match(r"^---\n(.*?\n)---\n", content, re.DOTALL)
        if not fm_match:
            return None
        try:
            frontmatter = yaml.safe_load(fm_match.group(1))
        except yaml.YAMLError:
            return None
        if not isinstance(frontmatter, dict):
            return None
        # Normalize date/datetime to strings (yaml.safe_load auto-parses dates)
        return DocumentExtractor._normalize_frontmatter_values(frontmatter)

    @staticmethod
    def _normalize_frontmatter_values(obj):
        """Normalize YAML-parsed values to JSON-serializable types."""
        from datetime import date as date_type
        from datetime import datetime as datetime_type

        if isinstance(obj, dict):
            return {
                k: DocumentExtractor._normalize_frontmatter_values(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [DocumentExtractor._normalize_frontmatter_values(v) for v in obj]
        if isinstance(obj, datetime_type):
            return obj.isoformat()
        if isinstance(obj, date_type):
            return obj.isoformat()
        return obj

    # Normative documents that carry version frontmatter but are not domain
    # principles/methods files — they ride the same validation (session-244:
    # the loader's own pin-discipline history shows this class drifts too).
    EXTRA_VERSION_CHECK_FILES = ("ai-instructions.md", "failure-mode-registry.md")

    def validate_domain_description_lengths(self) -> None:
        """Fail the build if a routing description would be SILENTLY TRUNCATED.

        `route_domains` embeds each domain's whole `description` and scores a query
        against it. The embedding model has a hard token limit (512 for bge-small);
        anything past it is **discarded without error**. The vocabulary is still in
        the file, still reviewed, still believed to work — and contributes nothing.

        This was live and undetected. `ai-coding`'s description was **624 tokens: 112
        silently dropped (18%)**. The lost tail held Terraform, Pulumi, IaC governance,
        rollback semantics, OWASP agentic, and credential scoping — and, measured,
        `"terraform governance"` and `"agent rollback semantics"` did **not** route to
        `ai-coding` despite appearing verbatim in its description. Meanwhile
        `visual-communication` sat at 510/512, two tokens from the same cliff.

        **Why this RAISES instead of warning.** The tokenizer *already* printed
        `Token indices sequence length is longer than the specified maximum (624 > 512)`
        on every single index build, and it was ignored every single time. A louder
        warning is the fix that already failed (cf. the CI-billing label, OPERATIONS
        T-169). The build must stop.

        Raises:
            ExtractorConfigError: listing every over-limit description with its token
                count and the exact overage, so the fix is mechanical.
        """
        model_name = self.settings.embedding_model
        try:
            from transformers import AutoTokenizer

            # nosec B615 — HuggingFace download without an explicit revision pin.
            # Honest justification, not a dismissal: (a) `model_name` is NOT free-form —
            # it is validated against ALLOWED_EMBEDDING_MODELS before any load, so this
            # cannot be pointed at an arbitrary repo; (b) the SAME model is already
            # fetched unpinned by `SentenceTransformer(...)` at four call sites
            # (extractor, retrieval, semantic_rank, context_engine.indexer) — bandit's
            # B615 simply only pattern-matches `from_pretrained`. Pinning a revision on
            # THIS call alone would reduce zero real exposure while reading as if it had
            # hardened something. Repo-wide revision pinning is the real control and is
            # filed as BACKLOG #198.
            tokenizer = AutoTokenizer.from_pretrained(model_name)  # nosec B615
        except Exception as e:  # pragma: no cover - offline/unavailable tokenizer
            # Fail SOFT here only: an unavailable tokenizer is an environment problem,
            # not a corpus defect, and must not block an offline build.
            logger.warning(
                "Could not load tokenizer for %s (%s) — skipping description-length "
                "validation. Routing descriptions are NOT verified against the token "
                "limit in this build.",
                model_name,
                e,
            )
            return

        limit = int(getattr(tokenizer, "model_max_length", 512) or 512)
        # Guard against tokenizers that report a sentinel "very large" max length.
        if limit > 100_000:
            limit = 512

        offenders: list[str] = []
        for domain_config in self.domains:
            description = (domain_config.description or "").strip()
            if not description:
                continue
            n_tokens = len(tokenizer.encode(description, add_special_tokens=True))
            if n_tokens > limit:
                offenders.append(
                    f"  - {domain_config.name}: {n_tokens} tokens "
                    f"({n_tokens - limit} OVER the {limit}-token limit — that text is "
                    f"embedded as nothing and cannot be routed to)"
                )

        if offenders:
            raise ExtractorConfigError(
                "Domain routing description(s) exceed the embedding model's token "
                f"limit and would be SILENTLY TRUNCATED by {model_name}:\n"
                + "\n".join(offenders)
                + "\n\nThe overflowing text is discarded at embed time: it stays in "
                "domains.json, reads as if it works, and contributes nothing to "
                "routing. Shorten the description(s) to fit.\n"
                "Note routing descriptions are ZERO-SUM (BACKLOG #197) — after editing, "
                "re-run the FULL matrix: pytest tests/test_domain_routing_evals.py"
            )

    def validate_version_consistency(self) -> None:
        """Validate document versions via YAML frontmatter.

        Primary: reads version from YAML frontmatter, then cross-checks every BODY
        version surface against it — H1 trailing version, header-region
        ``**Version:**`` / ``**Effective Date:**`` lines, footer ``*Version X*``,
        and the changelog current row (fenced code blocks stripped first). Each
        body check fires only when that surface is present.
        Cross-check: if filename has version suffix, verifies it matches frontmatter.
        Fallback: if no frontmatter, checks filename vs inline header (transition support).

        History: before session-244 the frontmatter-present path returned without
        reading the body at all, so 8 corpus files drifted (H1s/footers/dates lagging
        frontmatter) invisibly — the 2026-02-21 "Version Validator Has Blind Spots"
        LEARNING-LOG lesson, structurally closed here.

        Raises:
            ExtractorConfigError: If any version mismatches are found.
        """
        version_mismatches: list[str] = []

        for domain_config in self.domains:
            # Check principles file
            self._check_file_version(
                domain_config.principles_file,
                domain_config.name,
                "principles",
                version_mismatches,
            )

            # Check methods file
            if domain_config.methods_file:
                self._check_file_version(
                    domain_config.methods_file,
                    domain_config.name,
                    "methods",
                    version_mismatches,
                )

        for extra_file in self.EXTRA_VERSION_CHECK_FILES:
            # Fail-soft on absence: adopter corpora legitimately lack these files
            # (they are this repo's loader/registry, not domain content), but a
            # silent skip would recreate the coverage blind spot if one is renamed
            # here — so absence is logged loudly, never silently ignored.
            if not (self.settings.documents_path / extra_file).exists():
                logger.warning(
                    "version-consistency: extra normative file %r not found — "
                    "skipping its body-surface checks (expected in adopter "
                    "corpora; unexpected in the canonical repo)",
                    extra_file,
                )
                continue
            self._check_file_version(
                extra_file, "meta", "normative", version_mismatches
            )

        if version_mismatches:
            mismatches_list = "\n".join(version_mismatches)
            raise ExtractorConfigError(
                f"Version mismatches found:\n{mismatches_list}\n\n"
                f"Update frontmatter version to match, or fix the inconsistency."
            )

    def _check_file_version(
        self,
        filename: str,
        domain_name: str,
        file_type: str,
        mismatches: list[str],
    ) -> None:
        """Check version consistency for a single file.

        Priority: frontmatter > filename > inline header.
        If frontmatter exists with version, it is the source of truth.
        If filename has a version suffix, cross-check against frontmatter.
        If no frontmatter, fall back to filename vs inline header (transition).
        """
        file_path = self.settings.documents_path / filename
        if not file_path.exists():
            return  # File doesn't exist, will be caught by validate_domain_files

        content = file_path.read_text(encoding="utf-8")
        frontmatter = self._parse_frontmatter(content)

        # Extract version from filename if present
        filename_match = re.search(r"-v(\d+\.\d+(?:\.\d+)*)\.md$", filename)
        filename_version = filename_match.group(1) if filename_match else None

        # Primary path: frontmatter version
        if frontmatter and "version" in frontmatter:
            fm_version = str(frontmatter["version"])

            # Cross-check: if filename also has version, they must match
            if filename_version and filename_version != fm_version:
                mismatches.append(
                    f"  - {domain_name} {file_type}: '{filename}'\n"
                    f"    Filename version: {filename_version}\n"
                    f"    Frontmatter version: {fm_version}"
                )

            # Body surfaces must agree with frontmatter (session-244 blind-spot
            # fix — previously this path returned without reading the body).
            fm_date = frontmatter.get("effective_date")
            for problem in _body_version_surface_problems(
                content, fm_version, str(fm_date) if fm_date is not None else None
            ):
                mismatches.append(
                    f"  - {domain_name} {file_type}: '{filename}'\n    {problem}"
                )
            return

        # Fallback: filename vs inline header (transition support)
        if not filename_version:
            return  # No version source available, skip

        header_match = re.search(
            r"\*?\*?Version:?\*?\*?\s*(\d+\.\d+\.\d+)", content[:2000]
        )
        if not header_match:
            return  # No header version to compare

        header_version = header_match.group(1)
        if filename_version != header_version:
            mismatches.append(
                f"  - {domain_name} {file_type}: '{filename}'\n"
                f"    Filename version: {filename_version}\n"
                f"    Header version:   {header_version}"
            )

    def validate_domain_descriptions(self) -> list[ContentSecurityWarning]:
        """Scan domain descriptions for suspicious patterns.

        Domain descriptions are used for semantic routing and are embedded
        for similarity matching. They could be a vector for prompt injection
        if an attacker adds malicious content to a description.

        Returns:
            List of advisory warnings found.

        Raises:
            ContentSecurityError: If CRITICAL patterns are detected.
        """
        warnings: list[ContentSecurityWarning] = []
        critical_findings: list[ContentSecurityWarning] = []

        for domain_config in self.domains:
            # Raw AND normalized — see `content_patterns.security_views`.
            desc_views = security_views(domain_config.description)

            for pattern_type, pattern in SUSPICIOUS_PATTERNS.items():
                matches = [m for v in desc_views for m in pattern.findall(v)]
                if matches:
                    warning = ContentSecurityWarning(
                        file=f"domain:{domain_config.name}",
                        line=0,
                        pattern_type=pattern_type,
                        content=f"[{domain_config.name}]: {domain_config.description[:80]}",
                    )

                    if pattern_type in CRITICAL_PATTERNS:
                        critical_findings.append(warning)
                    else:
                        warnings.append(warning)

        if critical_findings:
            findings_list = "\n".join(f"  - {f}" for f in critical_findings)
            raise ContentSecurityError(
                f"CRITICAL: Suspicious patterns in domain descriptions!\n\n"
                f"The following patterns were found in domain descriptions:\n"
                f"{findings_list}\n\n"
                f"Domain descriptions are used for AI routing. This is a potential attack vector."
            )

        return warnings

    def extract_all(self, force: bool = False) -> GlobalIndex:
        """Extract all domains and build global index with embeddings."""
        # Pre-flight validation: fail fast if files are missing or inconsistent
        self.validate_domain_files()
        self.validate_version_consistency()
        # A description past the model's token limit is embedded as nothing — the
        # routing vocabulary reads as if it works and does not. Build stops.
        self.validate_domain_description_lengths()

        # Security scan: critical patterns raise, advisory patterns warn
        # Note: validate_content_security raises ContentSecurityError for critical patterns
        security_warnings = self.validate_content_security()

        # Also scan domain descriptions (used for semantic routing)
        domain_warnings = self.validate_domain_descriptions()
        security_warnings.extend(domain_warnings)

        if security_warnings:
            logger.warning(
                f"Content security scan found {len(security_warnings)} advisory pattern(s):"
            )
            for warning in security_warnings:
                logger.warning(f"  {warning}")
            logger.warning(
                "These are ADVISORY warnings (shell commands, base64, etc.). "
                "Critical patterns (prompt injection) would have blocked extraction."
            )

        ensure_directories(self.settings)

        domain_indexes: dict[str, DomainIndex] = {}
        all_texts: list[str] = []
        text_mapping: list[tuple[str, str, int]] = []  # (domain, type, local_idx)

        # First pass: extract all documents
        for domain_config in self.domains:
            logger.info(f"Extracting domain: {domain_config.name}")
            index = self._extract_domain(domain_config)
            domain_indexes[domain_config.name] = index

            # Collect texts for embedding
            for i, principle in enumerate(index.principles):
                text = self._get_embedding_text(principle)
                all_texts.append(text)
                text_mapping.append((domain_config.name, "principle", i))

            for i, method in enumerate(index.methods):
                text = self._get_method_embedding_text(method)
                all_texts.append(text)
                text_mapping.append((domain_config.name, "method", i))

            for i, ref in enumerate(index.references):
                text = self._get_reference_embedding_text(ref)
                all_texts.append(text)
                text_mapping.append((domain_config.name, "reference", i))

        # Generate embeddings for all content
        logger.info(f"Generating embeddings for {len(all_texts)} items...")
        embeddings = self.embedder.embed(all_texts)

        # BACKLOG #58 Fix C: assert the build ran in the canonical LOCAL space,
        # not the IPC daemon (force_local must have taken effect). Refusing
        # loudly at build time beats shipping a divergent index that silently
        # degrades semantic search to BM25-only.
        from .embedding_ipc import EmbeddingClient

        if isinstance(self.embedder.model, EmbeddingClient):
            raise EmbeddingSpaceError(
                "Index build resolved to the IPC embedding daemon despite "
                "force_local=True; refusing to write a potentially divergent "
                "index (BACKLOG #58)."
            )

        # Assign embedding IDs back to items
        for idx, (domain_name, item_type, local_idx) in enumerate(text_mapping):
            if item_type == "principle":
                domain_indexes[domain_name].principles[local_idx].embedding_id = idx
            elif item_type == "method":
                domain_indexes[domain_name].methods[local_idx].embedding_id = idx
            elif item_type == "reference":
                domain_indexes[domain_name].references[local_idx].embedding_id = idx

        # Generate domain description embeddings
        logger.info("Generating domain embeddings for routing...")
        domain_descriptions = [d.description for d in self.domains]
        domain_embeddings = self.embedder.embed(domain_descriptions)

        for i, domain_config in enumerate(self.domains):
            domain_config.embedding_id = i

        # BACKLOG #58 Fix A: store canonical (text, vector) canaries so the
        # loader can verify build-space == query-space behaviorally. Vectors
        # reuse the just-built force-local normalized content embeddings. A few
        # spread-out probes suffice — a directional flip is a property of the
        # space, not of which texts probe it.
        canary_indices = (
            sorted({0, len(all_texts) // 2, len(all_texts) - 1}) if all_texts else []
        )
        embedding_canaries = [
            EmbeddingCanary(
                text=all_texts[i],
                vector=np.asarray(embeddings[i], dtype=np.float32).tolist(),
            )
            for i in canary_indices
        ]

        # Build global index
        global_index = GlobalIndex(
            domains=domain_indexes,
            domain_configs=self.domains,
            created_at=datetime.now(timezone.utc).isoformat(),
            version="1.0",
            embedding_model=self.settings.embedding_model,
            embedding_dimensions=self.embedder.dimensions,
            embedding_canaries=embedding_canaries,
        )

        # GATE BEFORE THE FIRST WRITE. A configuration invariant must fail before
        # ANY artifact is touched — the ordering rule this codebase already states
        # in `config.py::_expand_and_absolutize`: "Configuration and security
        # invariants belong before the first verdict exists; durability is the only
        # part that may degrade."
        #
        # The first version of this guard lived only in `_save_index`, i.e. AFTER
        # both `.npy` writes. A refusal therefore left a 980-row matrix beside a
        # 1057-entry JSON. `retrieval.py` does detect that mismatch and discards the
        # embeddings rather than mis-scoring rows — but "discards" means a
        # cold-started server silently drops to BM25 keyword-only retrieval until
        # the next successful rebuild, which is the session-205→209
        # dead-semantic-search class. Measured on the live index, not theorised.
        # Found by an independent review pass; I had shipped the guard one call too
        # late and written a test that asserted the leftover matrix was "inert".
        self._refuse_silent_narrowing(global_index, force)

        # Save everything — embeddings first, JSON last.
        # JSON mtime change acts as "commit" signal for auto-reload
        # (see retrieval.py _check_index_freshness).
        self._save_embeddings(embeddings, "content_embeddings.npy")
        self._save_embeddings(domain_embeddings, "domain_embeddings.npy")

        content_f32 = np.asarray(embeddings, dtype=np.float32)
        domain_f32 = np.asarray(domain_embeddings, dtype=np.float32)
        global_index.build_id = uuid.uuid4().hex
        global_index.matrix_digests = {
            "content_embeddings": hashlib.sha256(content_f32.tobytes()).hexdigest(),
            "domain_embeddings": hashlib.sha256(domain_f32.tobytes()).hexdigest(),
        }

        # Re-checked inside _save_index as defence in depth for any other caller.
        # On this path it re-reads the same unchanged JSON, so it is a no-op.
        self._save_index(global_index, force=force)

        return global_index

    def _get_embedding_text(self, principle: Principle) -> str:
        """Create text for embedding from a principle.

        Combines title, content, and metadata for rich semantic representation.
        Uses 1500 chars to fit in BGE model's 512 token limit (~375 tokens).
        """
        parts = [
            principle.title,
            principle.content[:1500],  # Increased from 1000 to use new token budget
        ]

        # Add metadata keywords for richer embedding
        meta = principle.metadata
        if meta.keywords:
            parts.append(" ".join(meta.keywords[:5]))
        if meta.trigger_phrases:
            parts.append(" ".join(meta.trigger_phrases[:3]))

        return "\n".join(parts)

    def _get_method_embedding_text(self, method: Method) -> str:
        """Create text for embedding from a method.

        Combines title, content, and metadata for rich semantic representation.
        Uses 1500 chars to fit in BGE model's 512 token limit.
        """
        parts = [
            method.title,
            method.content[:1500],  # Increased from 500 to use new token budget
        ]

        # Add metadata keywords for richer embedding
        meta = method.metadata
        if meta.keywords:
            parts.append(" ".join(meta.keywords[:5]))
        if meta.trigger_phrases:
            parts.append(" ".join(meta.trigger_phrases[:3]))
        if meta.purpose_keywords:
            parts.append(" ".join(meta.purpose_keywords[:5]))
        if meta.applies_to:
            parts.append(" ".join(meta.applies_to[:3]))

        return "\n".join(parts)

    def _get_reference_embedding_text(self, ref: ReferenceEntry) -> str:
        """Create text for embedding from a reference entry.

        Combines title, summary, tags, and content for semantic representation.
        """
        parts = [ref.title]
        if ref.summary:
            parts.append(ref.summary)
        if ref.tags:
            parts.append(" ".join(ref.tags))
        parts.append(ref.content[:1500])

        meta = ref.metadata
        if meta.purpose_keywords:
            parts.append(" ".join(meta.purpose_keywords[:5]))

        return "\n".join(parts)

    def _extract_references(self, domain_config: DomainConfig) -> list[ReferenceEntry]:
        """Extract reference library entries from reference-library/{domain}/ directory.

        Parses YAML frontmatter from individual markdown files.
        Skips staging/ subdirectory and _criteria.yaml.
        """
        entries: list[ReferenceEntry] = []
        # NAME THE TREE ONCE (session-268). This used to derive the library from
        # `documents_path.parent`, which welded USER DATA to the PRODUCT checkout: a
        # capture from any project landed in this repo's working tree, and a downloader's
        # captures landed in their clone of our repo. `reference_library_path` is now its
        # own setting with a default outside any checkout. The private sibling stays
        # paired with it rather than with `documents/`.
        lib = self.settings.reference_library_path

        for ref_dir in [
            lib / domain_config.name,
            self.settings.private_reference_library_path / domain_config.name,
        ]:
            if not ref_dir.exists() or ref_dir.is_symlink():
                continue
            for md_file in sorted(ref_dir.glob("*.md")):
                entry = self._parse_reference_file(md_file, domain_config.name)
                if entry:
                    entries.append(entry)

        if entries:
            logger.info(
                f"Extracted {len(entries)} reference entries for {domain_config.name}"
            )
        return entries

    def _parse_reference_file(
        self, file_path: Path, domain_name: str
    ) -> ReferenceEntry | None:
        """Parse a single reference library markdown file with YAML frontmatter.

        Returns None if the file is invalid or missing required fields.
        Uses yaml.safe_load() exclusively — never yaml.load().
        """
        # Security: skip symlinks and oversized files
        if file_path.is_symlink():
            logger.warning(f"Skipping symlink reference file: {file_path}")
            return None
        MAX_REFERENCE_FILE_SIZE = 512 * 1024  # 512 KB
        try:
            if file_path.stat().st_size > MAX_REFERENCE_FILE_SIZE:
                logger.warning(f"Reference file too large, skipping: {file_path}")
                return None
        except OSError:
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Cannot read reference file {file_path}: {e}")
            return None

        # Parse YAML frontmatter (between --- delimiters)
        fm_match = re.match(r"^---\n(.*?\n)---\n(.*)", content, re.DOTALL)
        if not fm_match:
            logger.warning(f"Invalid frontmatter format in {file_path}")
            return None
        yaml_text = fm_match.group(1)
        body = fm_match.group(2).strip()

        try:
            frontmatter = yaml.safe_load(yaml_text)
        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML in {file_path}: {e}")
            return None

        if not isinstance(frontmatter, dict):
            logger.warning(f"Frontmatter is not a dict in {file_path}")
            return None

        # Validate required fields
        required = {"id", "title", "domain", "tags", "status", "entry_type"}
        missing = required - set(frontmatter.keys())
        if missing:
            logger.warning(f"Missing required fields in {file_path}: {missing}")
            return None

        # Build metadata for search
        metadata = self._generate_method_metadata(frontmatter["title"], body)
        # Enrich with tags. sorted() (not list()) because set iteration order
        # varies by PYTHONHASHSEED — this list is serialized into the index, so
        # an unsorted set churned the committed index across processes (#187).
        # (Non-string tags fail loudly at ReferenceEntry model validation below,
        # which is the guard for malformed frontmatter — not this line's job.)
        metadata.purpose_keywords = sorted(
            set(metadata.purpose_keywords + frontmatter.get("tags", []))
        )

        # YAML parses dates as datetime.date — convert to strings
        created = frontmatter.get("created")
        if created and not isinstance(created, str):
            created = str(created)
        last_verified = frontmatter.get("last_verified")
        if last_verified and not isinstance(last_verified, str):
            last_verified = str(last_verified)

        # Optional stack/platform applicability (BACKLOG #46). Normalize to
        # lowercase strings; tolerate a scalar or a missing field. Unlike the
        # capture_reference write path, no length/char cap is applied here:
        # this trusts hand-authored frontmatter, where a long applies_to is a
        # deliberate authoring choice rather than untrusted tool input.
        applies_raw = frontmatter.get("applies_to", [])
        if isinstance(applies_raw, str):
            applies_raw = [applies_raw]
        applies_to = [str(t).strip().lower() for t in applies_raw if str(t).strip()]

        return ReferenceEntry(
            id=frontmatter["id"],
            domain=frontmatter.get("domain", domain_name),
            title=frontmatter["title"],
            summary=frontmatter.get("summary", ""),
            content=body,
            tags=frontmatter.get("tags", []),
            applies_to=applies_to,
            status=frontmatter.get("status", "current"),
            maturity=frontmatter.get("maturity", "seedling"),
            entry_type=frontmatter.get("entry_type", "direct"),
            decay_class=frontmatter.get("decay_class", "framework"),
            created=created,
            last_verified=last_verified,
            source=frontmatter.get("source"),
            supersedes=frontmatter.get("supersedes", []),
            superseded_by=frontmatter.get("superseded_by"),
            related=frontmatter.get("related", []),
            source_path=self._reference_source_path(file_path),
            metadata=metadata,
        )

    def _reference_source_path(self, file_path: Path) -> str:
        """Display path for a reference entry, relative to whichever root holds it.

        This was the FOURTH derivation site (session-268), and the one that a reading
        pass missed and an actual run caught: it computed
        `file_path.relative_to(documents_path.parent)`, which silently assumed the
        library lives under the corpus checkout. Once the library moved out, every
        entry raised `ValueError: not in the subpath of` and the whole index build died
        — loudly, which is the right failure, but only because it was exercised.

        Tries the library root first, then the corpus root (a library still living
        in-repo is a supported layout), and finally falls back to the absolute path
        rather than raising: a provenance/display string is not worth failing a build
        over.
        """
        # Roots tried in order. The private library is its OWN setting (#257), so its
        # parent is used to render `private-reference-library/<domain>/<file>.md` rather
        # than assuming it sits beside the public one.
        for root in (
            self.settings.reference_library_path,
            self.settings.private_reference_library_path.parent,
            self.settings.documents_path.parent,
        ):
            try:
                return str(file_path.relative_to(root))
            except ValueError:
                continue
        return str(file_path)

    def _extract_domain(self, domain_config: DomainConfig) -> DomainIndex:
        """Extract a single domain."""
        principles = self._extract_principles(domain_config)
        methods = []
        if domain_config.methods_file:
            methods = self._extract_methods(domain_config)
        references = self._extract_references(domain_config)

        return DomainIndex(
            domain=domain_config.name,
            principles=principles,
            methods=methods,
            references=references,
            last_extracted=datetime.now(timezone.utc).isoformat(),
            version="1.0",
        )

    def _slugify(self, text: str) -> str:
        """Convert text to a URL-friendly slug."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        # Limit length to prevent overly long slugs
        if len(slug) > 50:
            slug = slug[:50].rsplit("-", 1)[0]
        return slug

    def _get_category_from_section(self, section_title: str) -> str:
        """Extract category from section header.

        Maps section headers to semantic categories for ID generation.
        Supports both descriptive headers ("Core Architecture") and
        series headers ("C-Series: Context Principles").

        Delegates to CATEGORY_MAPPING — promoted to a class constant so the
        substring-ordering invariant is directly testable (see
        TestCategoryMappingOrdering). Order is load-bearing: the scan returns the
        FIRST key that is a substring of the title.
        """
        section_lower = section_title.lower()
        for keyword, category in self.CATEGORY_MAPPING.items():
            if keyword in section_lower:
                return category
        return "general"

    # Section-header keyword → category, scanned IN ORDER by substring match.
    #
    # ORDER IS LOAD-BEARING AND SILENT WHEN WRONG. A key that is a substring of a
    # later key must come FIRST, or the shorter key steals the match and the
    # principle lands in another domain's category — which then misses
    # CATEGORY_SERIES_MAP, yielding series_code=None (sorts lowest in retrieval,
    # warning-only). Example caught in session-247: "gr-series" CONTAINS
    # "r-series", so GR principles silently became multi-agent's "reliability".
    # TestCategoryMappingOrdering enforces the invariant structurally — add new
    # series keys anywhere and let the test tell you where they belong.
    CATEGORY_MAPPING: dict[str, str] = {
        # Visual-Communication series mapping (title-35)
        # IMPORTANT: "gr-series" MUST precede "r-series" (multi-agent
        # reliability) — "gr-series" CONTAINS "r-series", so a later
        # position would silently categorize GR principles as "reliability".
        # Same substring hazard the multimodal-rag block below documents.
        "sg-series": "signal-structure",
        "ps-series": "presentation-design",
        "rpt-series": "report-layout",
        "wbk-series": "workbook-structure",
        "gr-series": "data-display",
        # Multimodal-RAG series mapping
        # IMPORTANT: Longer series names MUST come before shorter ones
        # to prevent substring collisions (e.g., "v-series" in "ev-series",
        # "c-series" in "sec-series")
        "ag-series": "agentic-retrieval",
        "agentic retrieval principle": "agentic-retrieval",
        "ev-series": "evaluation",
        "evaluation principle": "evaluation",
        "sec-series": "security",
        "security principle": "security",
        "ct-series": "citation",
        "citation principle": "citation",
        "dg-series": "data-governance",
        "data governance principle": "data-governance",
        "v-series": "verification",
        "verification principle": "verification",
        # IMPORTANT: ao-series MUST come before o-series (substring collision)
        "ao-series": "autonomous",
        "autonomous operation principle": "autonomous",
        "o-series": "operations",
        "operations principle": "operations",
        "f-series": "fallback",
        "fallback principle": "fallback",
        # UI/UX series mapping
        # IMPORTANT: Longer series names MUST come before shorter ones
        # (e.g., "acc-series" before "c-series", "ix-series" before "x-series")
        "vh-series": "visual-hierarchy",
        "visual hierarchy principle": "visual-hierarchy",
        "ds-series": "design-system",
        "design system principle": "design-system",
        "acc-series": "accessibility",
        "accessibility principle": "accessibility",
        "rd-series": "responsive",
        "responsive design principle": "responsive",
        "ix-series": "interaction",
        "interaction principle": "interaction",
        "pl-series": "platform",
        "platform principle": "platform",
        # Multimodal-RAG P-Series = "Presentation" (must precede ai-coding "p-series" = "process")
        # Note: section_pattern regex strips trailing "Principles?" so text is "P-Series: Presentation"
        "presentation": "presentation",
        # KM&PD series mapping
        # IMPORTANT: ka-series MUST come before a-series (substring collision)
        # IMPORTANT: qa-series MUST come before a-series AND q-series
        "ka-series": "knowledge-architecture",
        "knowledge architecture principle": "knowledge-architecture",
        "tl-series": "training",
        "training & learning principle": "training",
        "training principle": "training",
        "pd-series": "people-development",
        "people development principle": "people-development",
        "qa-series": "quality-assurance",
        "quality assurance principle": "quality-assurance",
        # Accounting series mapping
        # IMPORTANT: le-series MUST come before e-series (substring collision)
        # IMPORTANT: ec-series, tc-series, rc-series MUST come before c-series
        # IMPORTANT: rc-series MUST come before r-series
        "le-series": "ledger-integrity",
        "ledger integrity principle": "ledger-integrity",
        "ec-series": "entity-classification",
        "entity & classification principle": "entity-classification",
        "entity classification principle": "entity-classification",
        "tc-series": "temporal-compliance",
        "temporal & compliance principle": "temporal-compliance",
        "temporal compliance principle": "temporal-compliance",
        "rc-series": "reconciliation-controls",
        "reconciliation & controls principle": "reconciliation-controls",
        "reconciliation controls principle": "reconciliation-controls",
        # Series-based mapping (ai-coding domain)
        "c-series": "context",
        "context principle": "context",
        "p-series": "process",
        "process principle": "process",
        "q-series": "quality",
        "quality principle": "quality",
        # Architecture-series mapping (multi-agent domain)
        "a-series": "architecture",
        "architecture principle": "architecture",
        # Multimodal-RAG R-Series = "Reference" (must precede "r-series" = "reliability")
        "reference": "reference",
        "r-series": "reliability",
        "reliability principle": "reliability",
        # Storytelling-series mapping
        "st-series": "structure",
        "structure principle": "structure",
        "m-series": "medium",
        "medium principle": "medium",
        "e-series": "safety",
        "ethics principle": "safety",
        "audience principle": "architecture",
        # Constitutional structural sections (no principles — defensive mapping)
        "declaration": "declaration",
        "preamble": "preamble",
        "framework structure": "framework-structure",
        # Constitutional Article/Amendment mappings (Phase 2 — dual-mode)
        # IMPORTANT: Longer Article names MUST come before shorter ones
        # to prevent substring collisions ("article i" ⊂ "article ii/iii/iv")
        "article iv": "governance",
        "article iii": "quality",
        "article ii": "operational",
        "article i": "core",
        "bill of rights": "safety",
        # "historical amendments" must precede "amendment" (substring collision)
        "historical amendments": "general",
        "amendment": "safety",
        # Descriptive mapping (constitution and general)
        "core": "core",
        "architecture": "core",
        "quality": "quality",
        "reliability": "quality",
        "operational": "operational",
        "efficiency": "operational",
        "collaborative": "multi",
        "multi-agent": "multi",
        "governance": "governance",
        "evolution": "governance",
        "safety": "safety",
        "ethics": "safety",
    }

    def _extract_principles(self, domain_config: DomainConfig) -> list[Principle]:
        """Extract principles from a domain's principles file."""
        file_path = self.settings.documents_path / domain_config.principles_file
        if not file_path.exists():
            logger.warning(f"Principles file not found: {file_path}")
            return []

        content = file_path.read_text()
        lines = content.split("\n")

        principles = []
        domain_prefix = self._get_domain_prefix(domain_config.name, domain_config)

        # Pre-scan for series headers to build dynamic detection lists
        dynamic_series_map = self._extract_series_headers(content, domain_config.name)
        dynamic_header_tokens, dynamic_skip_entries = (
            self._build_dynamic_series_patterns(dynamic_series_map)
        )

        # Pattern for section headers (## or ### Section Name)
        # Matches both "## Core Architecture Principles" and "### C-Series: Context Principles"
        section_pattern = re.compile(r"^#{2,3}\s+(.+?)\s*(?:Principles?)?\s*$")

        # Pattern for principle headers - supports both old and new formats:
        # Old format: ### C1. Context Engineering
        # New format: ### Context Engineering
        # Also supports: ### Title (Legal Analogy) or #### Title (Legal Analogy)
        old_header_pattern = re.compile(
            r"^#{2,4}\s+([A-Z]+)(\d+)\.\s+(.+?)(?:\s+\(The .+?\))?$"
        )
        new_header_pattern = re.compile(
            r"^#{3,4}\s+([A-Z][^#\n]+?)(?:\s+\([^)]+\))?\s*$"
        )

        current_principle = None
        current_section = "general"
        in_fence = False

        # Constitutional context tracking (Phase 2 — dual-mode)
        # Tracks the current Article and section counter for constitutional_ref generation.
        # When parsing old-format docs, these stay None and principles get no ref.
        current_article_roman: str | None = None  # e.g., "I", "II", "III", "IV"
        current_section_num = 0  # Reset per Article, incremented per ### Section
        current_amendment_num = 0  # Incremented per ### Amendment
        in_bill_of_rights = False

        for i, line in enumerate(lines, 1):
            # Structural boundary: close the open principle at the next
            # equal-or-shallower heading. Deliberately ADDITIVE — it must not
            # `continue`, because this same line may itself open the next
            # principle, which the branches below still need to see.
            #
            # The fence guard skips the WHOLE loop body, so header detection is
            # fence-aware too. That is deliberate: the `[:.]?` in the widened
            # method pattern below matches numbered headings inside ```markdown
            # templates, so a boundary-only guard would have ADDED phantom units.
            # Guarding header detection instead removed the 10 phantoms that were
            # already shipping (stor-method-characters, kmpd-method-branch-scenario,
            # +8 — all fenced Story Bible / KMPD template headings, no consumers).
            if _FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            if current_principle is not None:
                lvl = _heading_level(line)
                if lvl is not None and lvl <= current_principle["level"]:
                    current_principle["end_line"] = i - 1
                    current_principle["content"] = "\n".join(
                        lines[current_principle["start_line"] - 1 : i - 1]
                    )
                    principles.append(
                        self._build_principle(
                            current_principle, domain_prefix, dynamic_series_map
                        )
                    )
                    current_principle = None

            # Check for section headers
            # Allow ## headers always, and ### headers if they're series markers
            section_match = section_pattern.match(line)
            if section_match:
                section_text = section_match.group(1).lower()
                # Hardcoded series tokens (fallback for known domains)
                _static_series = [
                    "c-series",
                    "p-series",
                    "q-series",
                    "a-series",
                    "ao-series",
                    "r-series",
                    "st-series",
                    "m-series",
                    "e-series",
                    "v-series",
                    "ev-series",
                    "ct-series",
                    "sec-series",
                    "dg-series",
                    "o-series",
                    "ag-series",
                    "f-series",
                    "vh-series",
                    "ds-series",
                    "acc-series",
                    "rd-series",
                    "ix-series",
                    "pl-series",
                    "ka-series",
                    "tl-series",
                    "pd-series",
                    "qa-series",
                    "le-series",
                    "ec-series",
                    "tc-series",
                    "rc-series",
                    "sg-series",
                    "ps-series",
                    "rpt-series",
                    "wbk-series",
                    "gr-series",
                ]
                all_series_tokens = set(_static_series) | set(dynamic_header_tokens)
                is_series_header = any(s in section_text for s in all_series_tokens)
                if "###" not in line or is_series_header:
                    current_section = self._get_category_from_section(
                        section_match.group(1)
                    )
                    # Track constitutional context for ref generation (Phase 2)
                    article_match = self.ARTICLE_HEADER_RE.match(section_match.group(1))
                    if article_match:
                        current_article_roman = article_match.group(1).upper()
                        current_section_num = 0  # Reset per Article
                        in_bill_of_rights = False
                    elif "bill of rights" in section_text:
                        in_bill_of_rights = True
                        current_article_roman = None
                        current_amendment_num = 0
                    else:
                        # Not a tracked constitutional section (e.g., Historical
                        # Amendments, Framework Overview) — reset context to
                        # prevent stale state from producing wrong refs.
                        in_bill_of_rights = False
                        current_article_roman = None

                    if is_series_header:
                        continue  # Skip series headers from principle extraction

            # Check for old-format principle headers first
            old_match = old_header_pattern.match(line)
            if old_match:
                # Save previous principle
                if current_principle:
                    current_principle["end_line"] = i - 1
                    current_principle["content"] = "\n".join(
                        lines[current_principle["start_line"] - 1 : i - 1]
                    )
                    principles.append(
                        self._build_principle(
                            current_principle, domain_prefix, dynamic_series_map
                        )
                    )

                # Start new principle (old format)
                series_code = old_match.group(1)
                title = old_match.group(3).strip()

                current_principle = {
                    "category": current_section,
                    "title": title,
                    "domain": domain_config.name,
                    "start_line": i,
                    "end_line": None,
                    "content": "",
                    "series_code": series_code,  # Keep for backwards compat
                    "level": _heading_level(line),
                }
                continue

            # Check for new-format principle headers
            new_match = new_header_pattern.match(line)
            if new_match:
                raw_title = new_match.group(1).strip()

                # Strip Constitutional prefixes (Phase 2 — dual-mode).
                # "Section 1: Context Engineering" → "Context Engineering"
                # "Amendment I: Non-Maleficence, Privacy & Security" → "Non-Maleficence, Privacy & Security"
                # Old-format titles pass through unchanged (no prefix to strip).
                title = self.CONSTITUTIONAL_PREFIX_RE.sub("", raw_title)
                has_constitutional_prefix = raw_title != title

                # Skip non-principle headers (like "When to Apply" etc.)
                # Domain-agnostic structural keywords
                _static_skip = [
                    "when to",
                    "how to",
                    "quick reference",
                    "decision tree",
                    "pre-action",
                    "framework overview",
                    "immediate",
                    "domain implementation",
                    "extending",
                    "universal",
                    "template structure",
                    "the twelve",
                    "the three series",
                    "the four series",
                    "the five series",
                    "the six series",
                    "version history",
                    "evidence base",
                    "glossary",
                    "scope and non-goals",
                    "design philosophy",
                    "peer domain",
                    "meta ↔ domain",
                    "appendix",
                    # Hardcoded series skip entries (fallback for known domains)
                    "c-series:",
                    "p-series:",
                    "q-series:",
                    "a-series:",
                    "r-series:",
                    # visual-communication (title-35) — parity with every other
                    # domain's series entries below; H2 series headers already
                    # short-circuit before this list is consulted, so these are
                    # defensive against a future heading-level change, not load-bearing.
                    "sg-series:",
                    "ps-series:",
                    "rpt-series:",
                    "wbk-series:",
                    "gr-series:",
                    "context principles",
                    "process principles",
                    "quality principles",
                    "architecture principles",
                    "reliability principles",
                    "st-series:",
                    "m-series:",
                    "e-series:",
                    "structure principles",
                    "craft principles",
                    "medium principles",
                    "ethics principles",
                    "audience principles",
                    "f-series:",
                    "fallback principles",
                    "v-series:",
                    "ev-series:",
                    "ct-series:",
                    "sec-series:",
                    "dg-series:",
                    "o-series:",
                    "ag-series:",
                    "verification principles",
                    "evaluation principles",
                    "citation principles",
                    "security principles",
                    "data governance principles",
                    "operations principles",
                    "agentic retrieval principles",
                    "vh-series:",
                    "ds-series:",
                    "acc-series:",
                    "rd-series:",
                    "ix-series:",
                    "pl-series:",
                    "visual hierarchy principles",
                    "design system principles",
                    "accessibility principles",
                    "responsive design principles",
                    "interaction principles",
                    "platform principles",
                    "ka-series:",
                    "tl-series:",
                    "pd-series:",
                    "qa-series:",
                    "knowledge architecture principles",
                    "training & learning principles",
                    "people development principles",
                    "quality assurance principles",
                    "le-series:",
                    "ec-series:",
                    "tc-series:",
                    "rc-series:",
                    "ledger integrity principles",
                    "entity & classification principles",
                    "temporal & compliance principles",
                    "reconciliation & controls principles",
                ]
                skip_keywords = list(set(_static_skip) | set(dynamic_skip_entries))
                if any(kw in title.lower() for kw in skip_keywords):
                    continue

                # Must have a principle-defining section following
                # Constitution uses **Definition**, Domain docs use **Failure Mode** or **Why This Principle Matters**
                next_lines = "\n".join(lines[i : i + 10])
                principle_indicators = [
                    "**Definition**",
                    "**Failure Mode",
                    "**Why This Principle Matters**",
                    "**Domain Application",
                    "**Constitutional Basis**",
                ]
                if not any(ind in next_lines for ind in principle_indicators):
                    continue

                # Save previous principle
                if current_principle:
                    current_principle["end_line"] = i - 1
                    current_principle["content"] = "\n".join(
                        lines[current_principle["start_line"] - 1 : i - 1]
                    )
                    principles.append(
                        self._build_principle(
                            current_principle, domain_prefix, dynamic_series_map
                        )
                    )

                # Compute constitutional_ref if we're in a tracked Article or Bill of Rights.
                # Note: Amendment numbering uses a sequential counter rather than
                # parsing the Roman numeral from the header. This assumes amendments
                # are numbered sequentially in the document. If amendments are ever
                # reordered or non-sequential, switch to parsing from raw_title.
                constitutional_ref = None
                if has_constitutional_prefix:
                    if in_bill_of_rights:
                        current_amendment_num += 1
                        roman = self._INT_TO_ROMAN.get(
                            current_amendment_num, str(current_amendment_num)
                        )
                        constitutional_ref = f"Amend. {roman}"
                    elif current_article_roman:
                        current_section_num += 1
                        constitutional_ref = (
                            f"Art. {current_article_roman}, § {current_section_num}"
                        )

                # Start new principle (new format)
                current_principle = {
                    "category": current_section,
                    "title": title,
                    "domain": domain_config.name,
                    "start_line": i,
                    "end_line": None,
                    "content": "",
                    "series_code": None,
                    "constitutional_ref": constitutional_ref,
                    "level": _heading_level(line),
                }

        # Save last principle
        if current_principle:
            current_principle["end_line"] = len(lines)
            current_principle["content"] = "\n".join(
                lines[current_principle["start_line"] - 1 :]
            )
            principles.append(
                self._build_principle(
                    current_principle, domain_prefix, dynamic_series_map
                )
            )

        if in_fence:
            # This does NOT degrade to pre-fix behavior — it is worse, and saying
            # so is the point. `if in_fence: continue` skips the whole loop body,
            # so after an unbalanced fence NO further unit is opened at all and the
            # last open unit swallows the rest of the file. Pre-fix behavior was
            # over-absorption with every unit still present; this is silent unit
            # LOSS, the exact class this fix exists to remove.
            # Enforced upstream by the fence-parity check in tests/test_repo_hygiene.py
            # so it cannot reach a rebuild; this warning is the second line.
            logger.warning(
                "unclosed code fence in %s — no further units were extracted from "
                "this file and the last open unit absorbed the remainder",
                domain_config.principles_file,
            )

        logger.info(f"Extracted {len(principles)} principles from {domain_config.name}")
        return principles

    # Domain name → principle ID prefix mapping.
    # Used by _get_domain_prefix() to generate stable principle IDs.
    # Promoted from local dict for direct testability (TestDomainConsistency).
    DOMAIN_PREFIXES: dict[str, str] = {
        "constitution": "meta",
        "ai-coding": "coding",
        "multi-agent": "multi",
        "storytelling": "stor",
        "multimodal-rag": "mrag",
        "ui-ux": "uiux",
        "kmpd": "kmpd",
        "accounting": "acct",
        "saas-ops": "so",
        "visual-communication": "viscom",
    }

    # Category → series code mapping, keyed by (domain, category).
    # Critical: only ("constitution", "safety") → "S" triggers S-Series veto.
    # Restores apply_hierarchy() sorting and series_code == "S" detection
    # that broke when v1.5 removed numeric series headers (### S1. → ### Title).
    CATEGORY_SERIES_MAP: dict[tuple[str, str], str] = {
        # Constitution — S/C/Q/O/G (MA-Series dissolved in v3.0.0)
        ("constitution", "safety"): "S",
        ("constitution", "core"): "C",
        ("constitution", "quality"): "Q",
        ("constitution", "operational"): "O",
        ("constitution", "governance"): "G",
        # AI-Coding — C/P/Q series
        ("ai-coding", "context"): "C",
        ("ai-coding", "process"): "P",
        ("ai-coding", "quality"): "Q",
        # Multi-Agent — A/R/Q/AO series (J-series maps to "general", no code)
        ("multi-agent", "architecture"): "A",
        ("multi-agent", "autonomous"): "AO",
        ("multi-agent", "reliability"): "R",
        ("multi-agent", "quality"): "Q",
        # Storytelling — A/ST/C/M/E series
        ("storytelling", "architecture"): "A",
        ("storytelling", "structure"): "ST",
        ("storytelling", "context"): "C",
        ("storytelling", "medium"): "M",
        ("storytelling", "safety"): "E",
        # Multimodal-RAG — P/R/A/F/V/EV/CT/SEC/DG/O/AG series
        ("multimodal-rag", "presentation"): "P",
        ("multimodal-rag", "reference"): "R",
        ("multimodal-rag", "architecture"): "A",
        ("multimodal-rag", "fallback"): "F",
        ("multimodal-rag", "verification"): "V",
        ("multimodal-rag", "evaluation"): "EV",
        ("multimodal-rag", "citation"): "CT",
        ("multimodal-rag", "security"): "SEC",
        ("multimodal-rag", "data-governance"): "DG",
        ("multimodal-rag", "operations"): "O",
        ("multimodal-rag", "agentic-retrieval"): "AG",
        # UI/UX — VH/DS/ACC/RD/IX/PL series
        ("ui-ux", "visual-hierarchy"): "VH",
        ("ui-ux", "design-system"): "DS",
        ("ui-ux", "accessibility"): "ACC",
        ("ui-ux", "responsive"): "RD",
        ("ui-ux", "interaction"): "IX",
        ("ui-ux", "platform"): "PL",
        # KM&PD series mapping
        ("kmpd", "knowledge-architecture"): "KA",
        ("kmpd", "knowledge"): "KA",
        ("kmpd", "training"): "TL",
        ("kmpd", "learning"): "TL",
        ("kmpd", "people-development"): "PD",
        ("kmpd", "people"): "PD",
        ("kmpd", "quality-assurance"): "QA",
        ("kmpd", "quality"): "QA",
        # Accounting — LE/EC/TC/RC series
        ("accounting", "ledger-integrity"): "LE",
        ("accounting", "entity-classification"): "EC",
        ("accounting", "temporal-compliance"): "TC",
        ("accounting", "reconciliation-controls"): "RC",
        # Visual-Communication — SG/PS/RPT/WBK/GR series
        ("visual-communication", "signal-structure"): "SG",
        ("visual-communication", "presentation-design"): "PS",
        ("visual-communication", "report-layout"): "RPT",
        ("visual-communication", "workbook-structure"): "WBK",
        ("visual-communication", "data-display"): "GR",
    }

    _SERIES_HEADER_RE = re.compile(
        r"^###\s+([A-Z]+)-Series:\s*(.+?)(?:\s+Principles?)?\s*$", re.MULTILINE
    )

    @staticmethod
    def _extract_series_headers(content: str, domain: str) -> dict[str, str]:
        """Extract series code → category mappings from document headers.

        Scans for ``### X-Series: Category Name`` patterns. Returns
        ``{series_code: category_slug}`` for the given domain. Constitution
        uses Article-based headers and returns empty (handled by fallback).
        """
        result: dict[str, str] = {}
        for m in DocumentExtractor._SERIES_HEADER_RE.finditer(content):
            code = m.group(1)
            name = m.group(2).strip()
            slug = name.lower().replace(" & ", "-").replace(" ", "-")
            result[code] = slug
        return result

    @staticmethod
    def _build_dynamic_series_patterns(
        series_map: dict[str, str],
    ) -> tuple[list[str], list[str]]:
        """Build is_series_header entries and skip_keywords from a dynamic series map.

        Returns (series_header_tokens, skip_keyword_entries).
        """
        headers: list[str] = []
        skips: list[str] = []
        for code, slug in series_map.items():
            token = f"{code.lower()}-series"
            headers.append(token)
            skips.append(f"{token}:")
            name_words = slug.replace("-", " ")
            skips.append(f"{name_words} principles")
        return headers, skips

    def _build_principle(
        self,
        data: dict,
        domain_prefix: str,
        dynamic_series_map: dict[str, str] | None = None,
    ) -> Principle:
        """Build a Principle object with metadata."""
        # Generate slug-based ID: {domain}-{category}-{title-slug}
        category = data.get("category", "general")
        title_slug = self._slugify(data["title"])
        principle_id = f"{domain_prefix}-{category}-{title_slug}"

        # Resolve series_code: old format sets it directly, new format infers from category
        series_code = data.get("series_code")
        number = None
        if series_code:
            # Old format had series_code, try to get number from old-style matching
            number = data.get("number", 0)
        else:
            domain = data.get("domain", "")
            # Try dynamic series map first (parsed from document headers)
            if dynamic_series_map:
                for code, slug in dynamic_series_map.items():
                    if slug == category:
                        series_code = code
                        break
            # Fall back to hardcoded map
            if not series_code:
                series_code = self.CATEGORY_SERIES_MAP.get((domain, category))
            if not series_code and category != "general":
                logger.warning(
                    "No series code mapping for (%s, %s) — principle will sort at lowest priority",
                    domain,
                    category,
                )

        # S-Series safety invariant: only constitution may produce series_code "S"
        if series_code == "S" and data.get("domain") != "constitution":
            logger.error(
                "S-Series veto code rejected for non-constitution domain %s — "
                "only constitution safety principles may trigger S-Series veto",
                data.get("domain"),
            )
            series_code = None

        metadata = self._generate_metadata(
            principle_id, category, data["title"], data["content"]
        )

        principle_aliases = self._parse_aliases(data["content"])

        return Principle(
            id=principle_id,
            domain=data["domain"],
            series_code=series_code,
            number=number,
            title=data["title"],
            content=data["content"],
            line_range=(data["start_line"], data["end_line"]),
            metadata=metadata,
            constitutional_ref=data.get("constitutional_ref"),
            aliases=principle_aliases,
            embedding_id=None,  # Set later after embedding
        )

    def _parse_aliases(self, content: str) -> list[str]:
        """Parse `**Aliases:**` lines from an item's body to populate
        Principle.aliases / Method.aliases for backwards-compatible ID retrieval
        after a rename.

        Recognized markdown forms (case-insensitive on `Aliases:`):
            **Aliases:** former ID `meta-old-id` (renamed in v5.0.0; ...).
            **Aliases:** `meta-old-1`, `meta-old-2`

        Extracts every backticked code-span identifier on an Aliases line —
        backticks are REQUIRED; a bare, unquoted ID is not matched. Handles
        lowercase kebab slugs and uppercase legacy short-form IDs (`coding-M125`).
        If no `**Aliases:**` line is found, returns []. Multiple Aliases lines are
        all consumed (concatenated). Per the v5.0.0 rename plan
        (~/.claude/plans/this-is-back-and-tidy-crescent.md §5).
        """
        aliases: list[str] = []
        # Match lines starting with **Aliases:** (case-insensitive on the label)
        alias_line_re = re.compile(
            r"^\s*\*\*Aliases:\*\*\s*(.+?)\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        # Identifier shapes used by this framework: kebab-case slugs starting
        # with a domain prefix (meta-quality-..., coding-process-...,
        # multi-general-...), plus legacy short-form IDs that carry an uppercase
        # series letter (e.g. `coding-M125`) — the method IDs #181 exists to
        # resolve. Uppercase is allowed for that reason; the scan is confined to
        # curated **Aliases:** lines, so it cannot pick up prose code-spans.
        ident_re = re.compile(r"`([a-zA-Z][a-zA-Z0-9-]+-[a-zA-Z0-9-]+)`")

        for match in alias_line_re.finditer(content):
            line_body = match.group(1)
            for ident_match in ident_re.finditer(line_body):
                ident = ident_match.group(1)
                if ident not in aliases:
                    aliases.append(ident)
        return aliases

    def _generate_metadata(
        self, principle_id: str, category: str, title: str, content: str
    ) -> PrincipleMetadata:
        """Generate metadata for BM25 keyword search."""
        # Extract keywords from title
        title_words = [w.lower() for w in title.split() if len(w) > 3]

        # Add category as keyword for better search
        if category and category not in title_words:
            title_words.append(category)

        # Extract key phrases from content
        trigger_phrases = self._extract_phrases(content)

        # Extract failure indicators
        failure_indicators = self._extract_failure_indicators(content)

        # Create aliases from the title slug parts
        slug_parts = self._slugify(title).split("-")
        aliases = [p for p in slug_parts if len(p) > 3][:3]

        return PrincipleMetadata(
            keywords=title_words,
            synonyms=[],  # Could be expanded with synonym database
            trigger_phrases=trigger_phrases,
            failure_indicators=failure_indicators,
            aliases=aliases,
        )

    def _extract_phrases(self, content: str) -> list[str]:
        """Extract trigger phrases from content."""
        phrases = []

        # Look for quoted phrases
        quoted = re.findall(r'"([^"]+)"', content)
        phrases.extend([q.lower() for q in quoted if len(q.split()) <= 4])

        # Look for bold phrases
        bold = re.findall(r"\*\*([^*]+)\*\*", content)
        phrases.extend([b.lower() for b in bold if len(b.split()) <= 4])

        return phrases[:20]

    def _extract_failure_indicators(self, content: str) -> list[str]:
        """Extract failure indicators from content."""
        indicators = []

        # Look for "Failure Mode" or similar sections
        failure_match = re.search(
            r"\*\*(?:Failure Mode|Common Pitfalls|Anti-pattern)[^*]*\*\*[:\s]*(.+?)(?:\n\n|\*\*|$)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if failure_match:
            failure_text = failure_match.group(1)
            words = [
                w.lower()
                for w in re.findall(r"\b[a-z]{4,}\b", failure_text.lower())
                if w
                not in ("this", "that", "with", "from", "have", "been", "will", "when")
            ]
            indicators.extend(words[:5])

        return indicators

    def _extract_methods(self, domain_config: DomainConfig) -> list[Method]:
        """Extract methods from a domain's methods file.

        Filters out document structure sections (glossary, scope, etc.)
        to only include actual procedural methods.
        """
        file_path = self.settings.documents_path / domain_config.methods_file
        if not file_path.exists():
            logger.warning(f"Methods file not found: {file_path}")
            return []

        content = file_path.read_text()
        lines = content.split("\n")

        methods = []
        domain_prefix = self._get_domain_prefix(domain_config.name, domain_config)

        # Pattern for method headers (##, ###, or #### with numbered sections like 1.2.3)
        # Includes #### to extract subsections (e.g., 2.1.5) as separate methods
        #
        # The optional ``Part `` prefix and ``[:.]`` separator are load-bearing, not
        # tidiness. Without them ``## Part 7.8: Progressive Application`` is not a
        # unit, so its text was only ever delivered as the tail of whatever method
        # preceded it. Once units close at structural boundaries (see _FENCE_RE
        # above) that tail is no longer attached to anything, and the section would
        # become reachable through no tool at all — including sections this repo's
        # own always-loaded files cite as binding (README §7.8, CLAUDE.md §15.4).
        # rules-of-procedure.md has 86 such headings; title-10-ai-coding-cfr.md 63.
        # NOT widened to lettered appendix subsections (`### G.5 ...`, `### A.1 ...`):
        # measured, that recovers ~146K orphan chars but raises duplicate method ids
        # from 32 to 49, making get_principle(id) ambiguous for 17 more ids. The
        # appendices are model-specific reference material that was already
        # unsearchable (buried past the 1,500-char BM25 cap of the unit that
        # absorbed them), so the trade is bad. Filed separately — resolving the
        # id collisions is the real prerequisite.
        header_pattern = re.compile(
            r"^#{2,4}\s+(?:Part\s+)?(\d+(?:\.\d+)*)[:.]?\s+(.+)$"
        )

        # Document structure sections to skip (not actual methods)
        skip_method_titles = [
            # Document metadata sections
            "scope",
            "applicability",
            "relationship to other",
            # Glossary/terminology sections
            "terms",
            "glossary",
            "definitions",
            # Overview sections that aren't procedures
            "purpose",
            "overview",
            "introduction",
            "background",
            # Reference sections
            "legend",
            "index",
            "references",
            "appendix",
        ]

        current_method = None
        method_count = 0
        in_fence = False

        for i, line in enumerate(lines, 1):
            # Structural boundary — see the matching block in _extract_principles.
            # Additive: must not `continue`, since this line may open the next
            # method. This also closes the open method before the skip-title
            # `continue` below, which previously glued a skipped section's body
            # onto the preceding method.
            if _FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            if current_method is not None:
                lvl = _heading_level(line)
                if lvl is not None and lvl <= current_method["level"]:
                    current_method["end_line"] = i - 1
                    current_method["content"] = "\n".join(
                        lines[current_method["start_line"] - 1 : i - 1]
                    )
                    methods.append(self._build_method(current_method, domain_prefix))
                    method_count += 1
                    current_method = None

            match = header_pattern.match(line)
            if match:
                section_num = match.group(1)
                title = match.group(2).strip()

                # Skip document structure sections
                title_lower = title.lower()
                if any(skip in title_lower for skip in skip_method_titles):
                    continue

                if current_method:
                    current_method["end_line"] = i - 1
                    current_method["content"] = "\n".join(
                        lines[current_method["start_line"] - 1 : i - 1]
                    )
                    methods.append(self._build_method(current_method, domain_prefix))
                    method_count += 1

                current_method = {
                    "section": section_num,
                    "title": title,
                    "domain": domain_config.name,
                    "start_line": i,
                    "end_line": None,
                    "content": "",
                    "level": _heading_level(line),
                }

        if current_method:
            current_method["end_line"] = len(lines)
            current_method["content"] = "\n".join(
                lines[current_method["start_line"] - 1 :]
            )
            methods.append(self._build_method(current_method, domain_prefix))

        if in_fence:
            # See the matching block in _extract_principles: this is silent unit
            # LOSS, not a degradation to pre-fix behavior. Enforced upstream by the
            # fence-parity check in tests/test_repo_hygiene.py.
            logger.warning(
                "unclosed code fence in %s — no further units were extracted from "
                "this file and the last open unit absorbed the remainder",
                domain_config.methods_file,
            )

        logger.info(f"Extracted {len(methods)} methods from {domain_config.name}")
        return methods

    def _build_method(self, data: dict, domain_prefix: str) -> Method:
        """Build a Method object with slug-based ID and rich metadata."""
        # Generate slug-based ID: {domain}-method-{title-slug}
        title_slug = self._slugify(data["title"])
        method_id = f"{domain_prefix}-method-{title_slug}"

        keywords = [w.lower() for w in data["title"].split() if len(w) > 3]

        # Generate rich metadata for better search
        metadata = self._generate_method_metadata(data["title"], data["content"])

        method_aliases = self._parse_aliases(data["content"])

        return Method(
            id=method_id,
            domain=data["domain"],
            title=data["title"],
            content=data["content"],
            line_range=(data["start_line"], data["end_line"]),
            keywords=keywords,
            metadata=metadata,
            aliases=method_aliases,
            embedding_id=None,  # Set later
        )

    def _generate_method_metadata(self, title: str, content: str) -> MethodMetadata:
        """Generate metadata for method matching.

        Extracts keywords from:
        - Title words
        - **Purpose:** section
        - **Applies To:** section
        - Bold text and headers
        - Guideline headers
        """
        # Extract keywords from title
        title_words = [w.lower() for w in title.split() if len(w) > 3]

        # Extract purpose keywords
        purpose_keywords = []
        purpose_match = re.search(
            r"\*\*Purpose[:\*]*\*\*[:\s]*(.+?)(?:\n\n|\*\*|$)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if purpose_match:
            purpose_text = purpose_match.group(1)
            purpose_keywords = [
                w.lower()
                for w in re.findall(r"\b[a-z]{4,}\b", purpose_text.lower())
                if w
                not in (
                    "this",
                    "that",
                    "with",
                    "from",
                    "have",
                    "been",
                    "will",
                    "when",
                    "used",
                    "using",
                    "provides",
                )
            ][:10]

        # Extract applies_to keywords
        applies_to = []
        applies_match = re.search(
            r"\*\*(?:Applies To|When to Use|Use When)[:\*]*\*\*[:\s]*(.+?)(?:\n\n|\*\*|$)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if applies_match:
            applies_text = applies_match.group(1)
            applies_to = [
                w.lower()
                for w in re.findall(r"\b[a-z]{4,}\b", applies_text.lower())
                if w not in ("this", "that", "with", "from")
            ][:10]

        # Extract trigger phrases from bold text
        trigger_phrases = []
        bold = re.findall(r"\*\*([^*]+)\*\*", content)
        for b in bold[:15]:
            if len(b.split()) <= 4 and len(b) > 5:
                # Skip common section headers
                if b.lower() not in (
                    "purpose",
                    "applies to",
                    "when to use",
                    "note",
                    "example",
                ):
                    trigger_phrases.append(b.lower())

        # Extract guideline keywords from subheaders (#### Guidelines, etc.)
        guideline_keywords = []
        guideline_matches = re.findall(r"^#{3,4}\s+(.+)$", content, re.MULTILINE)
        for g in guideline_matches[:10]:
            words = [w.lower() for w in g.split() if len(w) > 3]
            guideline_keywords.extend(words[:3])

        return MethodMetadata(
            keywords=title_words,
            trigger_phrases=trigger_phrases[:10],
            purpose_keywords=purpose_keywords,
            applies_to=applies_to,
            guideline_keywords=guideline_keywords[:15],
        )

    def _get_domain_prefix(
        self, domain_name: str, domain_config: DomainConfig | None = None
    ) -> str:
        """Get the prefix for principle IDs based on domain."""
        prefix = getattr(domain_config, "prefix", None) if domain_config else None
        if prefix:
            return prefix
        return self.DOMAIN_PREFIXES.get(domain_name, domain_name[:4])

    KINDS = ("principles", "methods", "references")

    @classmethod
    def _composition_from_json(cls, index_json: object) -> dict[tuple[str, str], int]:
        """Entry counts keyed by ``(domain, kind)`` read from an on-disk index.

        PER-DOMAIN, NOT PER-KIND. ``_extract_references`` resolves
        ``reference_library_path / domain`` **once per domain**, so per-domain loss
        is the natural failure unit and an aggregate hides it. Measured: with 80
        reference entries and a 0.9 tolerance the guard fires only below 72, so
        losing two whole small domains (kmpd 4 + multi-agent 3 = 73) passed
        silently — the original incident at one-tenth scale, with the guard
        installed. Found by review, not by the suite.

        Returns ``{}`` for anything that is not a dict-shaped index. A valid-JSON
        non-dict (``null``, ``[]``, ``123``) used to raise ``AttributeError`` here,
        which escaped the caller's ``except`` and made a corrupt index wedge the one
        tool able to replace it — defeating the fail-open the caller documents.
        """
        if not isinstance(index_json, dict):
            return {}
        doms = index_json.get("domains") or {}
        items = doms.items() if isinstance(doms, dict) else enumerate(doms)
        out: dict[tuple[str, str], int] = {}
        for name, body in items:
            if isinstance(body, dict):
                for kind in cls.KINDS:
                    out[(str(name), kind)] = len(body.get(kind) or [])
        return out

    @classmethod
    def _composition_from_index(cls, index: GlobalIndex) -> dict[tuple[str, str], int]:
        """Same shape, read straight off the model.

        Deliberately NOT ``model_dump()`` — that deep-copies every entry including
        full content bodies, and the guard needs only lengths. It also removed a
        shape-fragility: a field rename would have silently produced an all-zero
        composition rather than a type error.
        """
        return {
            (name, kind): len(getattr(body, kind, None) or [])
            for name, body in index.domains.items()
            for kind in cls.KINDS
        }

    def _refuse_silent_narrowing(self, index: GlobalIndex, force: bool) -> None:
        """Refuse to replace an index with a materially smaller one.

        WHY THIS EXISTS — a measured incident, not a hypothetical (session-271).
        A rebuild run exactly as three framework docs document it
        (``python -m ai_governance_mcp.extractor``, no environment setup) replaced
        the live index's **80** reference entries with the **3** test-fixture stubs
        that happen to sit in the default location. ``search_references`` was
        crippled for every session on the machine. The command exited 0, the
        summary printed only principles and methods, and nothing announced the
        narrowing. It was caught by arithmetic (976 + 80 = 1056), which is not a
        control.

        WHY THE GUARD IS HERE AND NOT IN THE DOCS. The proximate cause was a
        misconfigured path, and the tempting fix is to write the three env vars
        into the documented command. That puts the same value in two places and
        re-arms the drift the moment either moves (`ref-ai-coding-depin-volatile-
        values`). There are many ways to point this tool at the wrong tree — a
        missing env var, a relocated library, a typo, a shell that did not export
        what you thought — and exactly ONE place where the consequence becomes
        visible: the moment a smaller index is about to overwrite a larger one.
        Guarding the consequence covers every cause, including the ones nobody
        has thought of yet.

        TWO RULES, because proportional loss and total loss are different failures:
        a ``(domain, kind)`` going nonzero → **zero** always fires, regardless of
        tolerance — an entire category disappearing is never ordinary churn. Any
        other shrink fires below ``INDEX_SHRINK_TOLERANCE``.

        IT LOGS ON EVERY PATH, including the ones that pass. Without that, drift in
        the on-disk shape would zero out ``previous``, the comparison would find
        nothing to complain about, and the guard would become a permanent no-op with
        no run output revealing it — a silent failure in the code whose whole job is
        preventing silent failure.

        Implements ``mrag-operations-o1-index-version-management`` — specifically
        its "Overwrite Deploy" and "Untested Rebuild" pitfalls. A legitimate
        shrink (retiring content) passes with ``--force``; the point is that it
        must be *stated*, not assumed.
        """
        index_file = self.settings.index_path / "global_index.json"
        incoming = self._composition_from_index(index)

        if force:
            # Still say what was waved through. A bypass that prints nothing is a
            # bypass nobody can audit, and AGENTS.md already records this hazard
            # for QUALITY_GATE_SKIP ("a bypass used routinely is a bypass").
            logger.warning(
                "Index shrink guard BYPASSED via --force — writing %d entries. "
                "Resolved paths: documents=%s index=%s reference_library=%s "
                "private_reference_library=%s",
                sum(incoming.values()),
                self.settings.documents_path,
                self.settings.index_path,
                self.settings.reference_library_path,
                self.settings.private_reference_library_path,
            )
            return

        if not index_file.is_file():
            logger.info(
                "Index shrink guard: no existing index at %s — first build, %d entries.",
                index_file,
                sum(incoming.values()),
            )
            return
        try:
            previous = self._composition_from_json(json.loads(index_file.read_text()))
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            logger.warning(
                "Index shrink guard SKIPPED: existing index at %s is unreadable (%s). "
                "Failing open so a corrupt index cannot wedge the tool that replaces it.",
                index_file,
                exc,
            )
            return
        if not previous:
            logger.warning(
                "Index shrink guard SKIPPED: existing index at %s yielded no countable "
                "entries. Either it is empty or its shape has drifted from what this "
                "guard reads — if the latter, the guard is inert and needs updating.",
                index_file,
            )
            return

        emptied = sorted(
            k for k, n in previous.items() if n > 0 and incoming.get(k, 0) == 0
        )
        shrunk = sorted(
            k
            for k, n in previous.items()
            if n > 0 and 0 < incoming.get(k, 0) < n * INDEX_SHRINK_TOLERANCE
        )

        if not emptied and not shrunk:
            logger.info(
                "Index shrink guard PASSED: %d -> %d entries across %d (domain, kind) buckets.",
                sum(previous.values()),
                sum(incoming.values()),
                len(previous),
            )
            return

        width = max((len(f"{d}/{k}") for d, k in (*emptied, *shrunk)), default=0)

        def _rows(keys: list[tuple[str, str]]) -> str:
            return "\n".join(
                f"    {f'{dom}/{kind}':<{width}}  {previous[(dom, kind)]:5} ->"
                f" {incoming.get((dom, kind), 0):5}"
                for dom, kind in keys
            )

        detail = ""
        if emptied:
            detail += "  EMPTIED (a whole category vanished):\n" + _rows(emptied) + "\n"
        if shrunk:
            detail += (
                f"  SHRANK below {INDEX_SHRINK_TOLERANCE:.0%} of previous:\n"
                + _rows(shrunk)
                + "\n"
            )
        raise SystemExit(
            "REFUSING TO WRITE: this rebuild would shrink the index.\n\n"
            f"{detail}\n"
            "  This is almost always a PATH problem, not a content change. The\n"
            "  paths actually in effect for this run were:\n"
            f"    documents        : {self.settings.documents_path}\n"
            f"    index            : {self.settings.index_path}\n"
            f"    reference library: {self.settings.reference_library_path}\n"
            f"    private ref lib  : {self.settings.private_reference_library_path}\n\n"
            "  The MCP server reads these from the host config (e.g. ~/.claude.json),\n"
            "  which a shell does NOT inherit. Read the live values off the running\n"
            "  server and export them before rebuilding:\n"
            "    ps eww $(pgrep -f 'ai_governance_mcp.server' | head -1) | tr ' ' '\\n' | grep ^AI_GOVERNANCE\n\n"
            "  If the shrink is intended (content was genuinely retired), re-run with\n"
            "  --force."
        )

    def _save_index(self, index: GlobalIndex, force: bool = False) -> None:
        """Save global index to JSON file atomically (tmp + fsync + rename).

        Prevents corruption if the process crashes mid-write. Refuses outright
        when the incoming index is materially smaller than the one on disk —
        see ``_refuse_silent_narrowing``.
        """
        self._refuse_silent_narrowing(index, force)
        index_file = self.settings.index_path / "global_index.json"
        tmp_file = index_file.with_suffix(_tmp_suffix())

        with open(tmp_file, "w") as f:
            # sort_keys for deterministic dict-key order across processes (#187).
            json.dump(index.model_dump(), f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        tmp_file.replace(index_file)

        logger.info(f"Saved index to {index_file}")

    def _save_embeddings(self, embeddings: np.ndarray, filename: str) -> None:
        """Save embeddings to NumPy file atomically (tmp + rename).

        np.save auto-appends .npy, so we construct a tmp path that accounts
        for this: {name}.tmp → np.save creates {name}.tmp.npy → rename.

        Embeddings are cast to float32 — the canonical storage/transport dtype
        across the codebase (the IPC protocol in `embedding_ipc.py`, the retrieval
        load path, and the test fixtures all assume float32). This cast is the
        single chokepoint that keeps the on-disk index deterministically float32
        regardless of what dtype the embedding backend returns (some paths return
        float64). Without it the stored index can drift to float64 — double the
        size, and a silent float32→float64 upcast against the float32 query
        vectors at similarity time.
        """
        embeddings = np.asarray(embeddings, dtype=np.float32)
        embeddings_file = self.settings.index_path / filename
        # Explicit path construction: np.save("foo.tmp") creates "foo.tmp.npy".
        # The suffix is per-process/thread so two concurrent rebuilds cannot
        # write the same temp path and splice their outputs — see _tmp_suffix.
        tmp_base = Path(str(embeddings_file) + _tmp_suffix())
        np.save(tmp_base, embeddings)
        actual_tmp = Path(str(tmp_base) + ".npy")
        actual_tmp.replace(embeddings_file)
        logger.info(
            f"Saved embeddings to {embeddings_file} (shape: {embeddings.shape})"
        )


def main():
    """CLI entry point for extraction."""
    settings = load_settings()

    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv[1:]

    # Override documents path if provided
    if args:
        settings.documents_path = Path(args[0])

    # RESOLVED PATHS FIRST, ALWAYS. The operator's index is only as correct as the
    # paths this run actually used, and those come from the environment — which a
    # shell does not inherit from the MCP host config. Printing them up front is
    # what makes a misconfigured rebuild visible at a glance instead of arithmetic.
    print("Resolved paths for this build:", file=sys.stderr)
    print(f"  documents        : {settings.documents_path}", file=sys.stderr)
    print(f"  index            : {settings.index_path}", file=sys.stderr)
    print(f"  reference library: {settings.reference_library_path}", file=sys.stderr)
    print(
        f"  private ref lib  : {settings.private_reference_library_path}",
        file=sys.stderr,
    )

    logger.info(f"Extracting documents from: {settings.documents_path}")
    logger.info(f"Using embedding model: {settings.embedding_model}")

    extractor = DocumentExtractor(settings)
    index = extractor.extract_all(force=force)

    # Print summary. REFERENCES ARE INCLUDED — their omission is precisely why a
    # rebuild that dropped 77 of 80 reference entries looked like a clean run.
    print("\nExtraction complete:", file=sys.stderr)
    totals = {"principles": 0, "methods": 0, "references": 0}
    for domain_name, domain_index in index.domains.items():
        counts = {
            "principles": len(domain_index.principles),
            "methods": len(domain_index.methods),
            "references": len(getattr(domain_index, "references", []) or []),
        }
        for k, v in counts.items():
            totals[k] += v
        print(
            f"  {domain_name}: {counts['principles']} principles, "
            f"{counts['methods']} methods, {counts['references']} references",
            file=sys.stderr,
        )
    grand = sum(totals.values())
    print(
        f"\nTOTAL: {totals['principles']} principles + {totals['methods']} methods "
        f"+ {totals['references']} references = {grand} indexed entries",
        file=sys.stderr,
    )
    print(f"Embedding model: {index.embedding_model}", file=sys.stderr)
    print(f"Embedding dimensions: {index.embedding_dimensions}", file=sys.stderr)


if __name__ == "__main__":
    main()
