"""Document extractor for AI Governance documents.

Per specification v4: Build-time extraction creates index and embeddings
for hybrid retrieval (BM25 + semantic search).
"""

import json
import re
import sys
import unicodedata
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
from .models import (
    DomainConfig,
    DomainIndex,
    GlobalIndex,
    Method,
    MethodMetadata,
    Principle,
    PrincipleMetadata,
)

logger = setup_logging()


class EmbeddingGenerator:
    """Generates embeddings using sentence-transformers.

    Lazy-loads the model to avoid import overhead when not needed.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        if not texts:
            return np.array([])
        return self.model.encode(texts, show_progress_bar=len(texts) > 10)

    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.model.encode([text])[0]

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.model.get_sentence_embedding_dimension()


class ExtractorConfigError(Exception):
    """Raised when extractor configuration is invalid (e.g., missing files)."""

    pass


class ContentSecurityError(Exception):
    """Raised when critical security patterns are detected in governance documents.

    Critical patterns include prompt injection phrases and hidden instructions
    that could compromise AI agents consuming governance content.
    """

    pass


# Patterns classified by severity
# CRITICAL: Hard-fail extraction - these are clear attack indicators
# ADVISORY: Warn only - may have legitimate uses in documentation
CRITICAL_PATTERNS = {"prompt_injection", "hidden_instruction"}
ADVISORY_PATTERNS = {"shell_command", "base64_payload", "data_exfiltration"}


class ContentSecurityWarning:
    """Warning about suspicious content in governance documents."""

    def __init__(self, file: str, line: int, pattern_type: str, content: str):
        self.file = file
        self.line = line
        self.pattern_type = pattern_type
        self.content = content[:100]  # Truncate for logging

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.pattern_type}]: {self.content}"


# Invisible Unicode characters that should be stripped for security scanning
# These can be used to hide malicious content from visual inspection
_INVISIBLE_CATEGORIES = frozenset(
    {
        "Cf",  # Format characters (zero-width joiners, etc.)
        "Cc",  # Control characters (except newlines/tabs)
    }
)

# Specific invisible codepoints to strip
_INVISIBLE_CODEPOINTS = frozenset(
    {
        0x200B,  # Zero-width space
        0x200C,  # Zero-width non-joiner
        0x200D,  # Zero-width joiner
        0x200E,  # Left-to-right mark
        0x200F,  # Right-to-left mark
        0x2060,  # Word joiner
        0x2061,  # Function application
        0x2062,  # Invisible times
        0x2063,  # Invisible separator
        0x2064,  # Invisible plus
        0xFEFF,  # Byte order mark / zero-width no-break space
    }
)


def _is_invisible_char(char: str) -> bool:
    """Check if a character is invisible and should be stripped for security."""
    cp = ord(char)
    # Keep newlines and tabs for pattern matching context
    if char in "\n\r\t":
        return False
    # Check specific codepoints
    if cp in _INVISIBLE_CODEPOINTS:
        return True
    # Check Unicode category
    category = unicodedata.category(char)
    return category in _INVISIBLE_CATEGORIES


def normalize_text_for_security(text: str) -> str:
    """Normalize text for security pattern matching.

    Applies NFKC normalization (compatibility decomposition + canonical composition)
    and strips invisible characters. This prevents homoglyph attacks where
    Cyrillic 'а' (U+0430) is used instead of Latin 'a' (U+0061).

    Per OWASP recommendations for input validation.

    Args:
        text: Raw text to normalize

    Returns:
        Normalized text safe for pattern matching
    """
    # NFKC normalization: handles homoglyphs, ligatures, compatibility chars
    normalized = unicodedata.normalize("NFKC", text)
    # Strip invisible characters that could hide malicious content
    return "".join(c for c in normalized if not _is_invisible_char(c))


# Suspicious patterns that may indicate prompt injection or malicious content
SUSPICIOUS_PATTERNS = {
    "shell_command": re.compile(
        r"(?<!`)`[^`]+`(?!`)|"  # Backtick commands (not in code blocks)
        r"\$\([^)]+\)|"  # $() subshells
        r"(?:^|\s)(?:curl|wget|bash|sh|eval|exec)\s+[^\s]",
        re.MULTILINE,
    ),
    "prompt_injection": re.compile(
        # These patterns must appear at start of sentence or after punctuation
        # to avoid matching documentation that discusses these concepts
        r"(?:^|[.!?]\s+)ignore\s+(?:previous|prior|above)\s+instructions|"
        r"(?:^|[.!?]\s+)you\s+are\s+now\s+|"
        r"(?:^|[.!?]\s+)disregard\s+(?:all|previous)|"
        r"(?:^|[.!?]\s+)forget\s+(?:everything|all|previous)|"
        # "new instructions:" is directive - scan only at line start or after bullet
        r"(?:^|\*\s+)new\s+instructions:",
        re.IGNORECASE | re.MULTILINE,
    ),
    "hidden_instruction": re.compile(
        r"<!--[^>]*(?:instruction|execute|ignore|override)[^>]*-->",
        re.IGNORECASE,
    ),
    "base64_payload": re.compile(
        r"base64\s+(?:-d|--decode)|"
        r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{100,}={0,2}(?![A-Za-z0-9+/])",
    ),
    "data_exfiltration": re.compile(
        r"(?:cat|type)\s+[~\/].*(?:\.ssh|\.env|\.aws|credentials|secret)|"
        r"(?:curl|wget|nc|netcat).*(?:-d|--data|POST)",
        re.IGNORECASE,
    ),
}


class DocumentExtractor:
    """Extracts principles and methods from governance markdown documents.

    Creates a GlobalIndex with embeddings for hybrid retrieval.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.domains = load_domains_registry(settings)
        self.embedder = EmbeddingGenerator(settings.embedding_model)

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
                f"Check documents/domains.json and ensure file versions match."
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
            CRITICAL patterns (prompt_injection, hidden_instruction) cause hard failure.
            ADVISORY patterns (shell_command, base64_payload, data_exfiltration) warn only.
        """
        warnings: list[ContentSecurityWarning] = []
        critical_findings: list[ContentSecurityWarning] = []

        for domain_config in self.domains:
            # Check principles file
            principles_path = (
                self.settings.documents_path / domain_config.principles_file
            )
            if principles_path.exists():
                file_warnings = self._scan_file_for_suspicious_content(principles_path)
                for w in file_warnings:
                    if w.pattern_type in CRITICAL_PATTERNS:
                        critical_findings.append(w)
                    else:
                        warnings.append(w)

            # Check methods file
            if domain_config.methods_file:
                methods_path = self.settings.documents_path / domain_config.methods_file
                if methods_path.exists():
                    file_warnings = self._scan_file_for_suspicious_content(methods_path)
                    for w in file_warnings:
                        if w.pattern_type in CRITICAL_PATTERNS:
                            critical_findings.append(w)
                        else:
                            warnings.append(w)

        # Check agent templates
        agents_path = self.settings.documents_path / "agents"
        if agents_path.exists():
            for agent_file in agents_path.glob("*.md"):
                file_warnings = self._scan_file_for_suspicious_content(agent_file)
                for w in file_warnings:
                    if w.pattern_type in CRITICAL_PATTERNS:
                        critical_findings.append(w)
                    else:
                        warnings.append(w)

        # Hard-fail on critical patterns
        if critical_findings:
            findings_list = "\n".join(f"  - {f}" for f in critical_findings)
            raise ContentSecurityError(
                f"CRITICAL: Prompt injection or hidden instructions detected!\n\n"
                f"The following patterns were found in governance documents:\n"
                f"{findings_list}\n\n"
                f"This is a potential supply chain attack. Extraction blocked.\n"
                f"If this is legitimate documentation, wrap in a code block (```)."
            )

        return warnings

    def _scan_file_for_suspicious_content(
        self, file_path: Path
    ) -> list[ContentSecurityWarning]:
        """Scan a single file for suspicious patterns."""
        warnings: list[ContentSecurityWarning] = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Track if we're inside a code block (where patterns may be examples)
        in_code_block = False

        for line_num, line in enumerate(lines, 1):
            # Track code block state
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip patterns inside code blocks (likely examples)
            if in_code_block:
                continue

            # Normalize text for security scanning (NFKC + strip invisibles)
            # This prevents homoglyph attacks (Cyrillic 'а' → Latin 'a')
            normalized_line = normalize_text_for_security(line)

            # Check each pattern against normalized text
            for pattern_type, pattern in SUSPICIOUS_PATTERNS.items():
                matches = pattern.findall(normalized_line)
                if matches:
                    line_lower = normalized_line.lower()

                    # For CRITICAL patterns: NEVER skip, even in "example" context
                    # Per security hardening: prompt_injection and hidden_instruction
                    # should never appear in governance docs, not even as examples.
                    # Legitimate attack documentation should use code blocks (```)
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

                    # For ADVISORY patterns: skip if in example/documentation context
                    # These legitimately appear in documentation (shell commands, etc.)
                    if any(
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

        return warnings

    def validate_version_consistency(self) -> None:
        """Validate that filename versions match header versions.

        Checks both principles and methods files for version consistency.
        Extracts version from filename pattern (e.g., 'file-v2.5.0.md')
        and compares to header version (e.g., '**Version:** 2.5.0').

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

        if version_mismatches:
            mismatches_list = "\n".join(version_mismatches)
            raise ExtractorConfigError(
                f"Version mismatches found (filename vs header):\n{mismatches_list}\n\n"
                f"Update filename to match header version, or vice versa."
            )

    def _check_file_version(
        self,
        filename: str,
        domain_name: str,
        file_type: str,
        mismatches: list[str],
    ) -> None:
        """Check version consistency for a single file."""
        # Extract version from filename (e.g., 'ai-coding-methods-v2.5.0.md' -> '2.5.0')
        filename_match = re.search(r"-v(\d+\.\d+\.\d+)\.md$", filename)
        if not filename_match:
            return  # No version in filename, skip check

        filename_version = filename_match.group(1)

        # Read file and extract header version
        file_path = self.settings.documents_path / filename
        if not file_path.exists():
            return  # File doesn't exist, will be caught by validate_domain_files

        content = file_path.read_text(encoding="utf-8")

        # Look for version in header (e.g., '**Version:** 2.5.0' or 'Version: 2.5.0')
        header_match = re.search(
            r"\*?\*?Version:?\*?\*?\s*(\d+\.\d+\.\d+)", content[:2000]
        )
        if not header_match:
            return  # No version in header, skip check

        header_version = header_match.group(1)

        if filename_version != header_version:
            mismatches.append(
                f"  - {domain_name} {file_type}: '{filename}'\n"
                f"    Filename version: {filename_version}\n"
                f"    Header version:   {header_version}"
            )

    def validate_domain_descriptions(self) -> list[ContentSecurityWarning]:
        """Scan domain descriptions in domains.json for suspicious patterns.

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
            # Normalize the description for security scanning
            normalized_desc = normalize_text_for_security(domain_config.description)

            for pattern_type, pattern in SUSPICIOUS_PATTERNS.items():
                matches = pattern.findall(normalized_desc)
                if matches:
                    warning = ContentSecurityWarning(
                        file="domains.json",
                        line=0,  # No line number for JSON
                        pattern_type=pattern_type,
                        content=f"[{domain_config.name}]: {domain_config.description[:80]}",
                    )

                    if pattern_type in CRITICAL_PATTERNS:
                        critical_findings.append(warning)
                    else:
                        # For ADVISORY patterns in descriptions, still warn
                        # (no "example" context to skip in descriptions)
                        warnings.append(warning)

        if critical_findings:
            findings_list = "\n".join(f"  - {f}" for f in critical_findings)
            raise ContentSecurityError(
                f"CRITICAL: Suspicious patterns in domain descriptions!\n\n"
                f"The following patterns were found in domains.json:\n"
                f"{findings_list}\n\n"
                f"Domain descriptions are used for AI routing. This is a potential attack vector."
            )

        return warnings

    def extract_all(self) -> GlobalIndex:
        """Extract all domains and build global index with embeddings."""
        # Pre-flight validation: fail fast if files are missing or inconsistent
        self.validate_domain_files()
        self.validate_version_consistency()

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

        # Generate embeddings for all content
        logger.info(f"Generating embeddings for {len(all_texts)} items...")
        embeddings = self.embedder.embed(all_texts)

        # Assign embedding IDs back to items
        for idx, (domain_name, item_type, local_idx) in enumerate(text_mapping):
            if item_type == "principle":
                domain_indexes[domain_name].principles[local_idx].embedding_id = idx
            else:
                domain_indexes[domain_name].methods[local_idx].embedding_id = idx

        # Generate domain description embeddings
        logger.info("Generating domain embeddings for routing...")
        domain_descriptions = [d.description for d in self.domains]
        domain_embeddings = self.embedder.embed(domain_descriptions)

        for i, domain_config in enumerate(self.domains):
            domain_config.embedding_id = i

        # Build global index
        global_index = GlobalIndex(
            domains=domain_indexes,
            domain_configs=self.domains,
            created_at=datetime.now(timezone.utc).isoformat(),
            version="1.0",
            embedding_model=self.settings.embedding_model,
            embedding_dimensions=self.embedder.dimensions,
        )

        # Save everything
        self._save_index(global_index)
        self._save_embeddings(embeddings, "content_embeddings.npy")
        self._save_embeddings(domain_embeddings, "domain_embeddings.npy")

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

    def _extract_domain(self, domain_config: DomainConfig) -> DomainIndex:
        """Extract a single domain."""
        principles = self._extract_principles(domain_config)
        methods = []
        if domain_config.methods_file:
            methods = self._extract_methods(domain_config)

        return DomainIndex(
            domain=domain_config.name,
            principles=principles,
            methods=methods,
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
        """
        category_mapping = {
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
            "r-series": "reliability",
            "reliability principle": "reliability",
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
        section_lower = section_title.lower()
        for keyword, category in category_mapping.items():
            if keyword in section_lower:
                return category
        return "general"

    def _extract_principles(self, domain_config: DomainConfig) -> list[Principle]:
        """Extract principles from a domain's principles file."""
        file_path = self.settings.documents_path / domain_config.principles_file
        if not file_path.exists():
            logger.warning(f"Principles file not found: {file_path}")
            return []

        content = file_path.read_text()
        lines = content.split("\n")

        principles = []
        domain_prefix = self._get_domain_prefix(domain_config.name)

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
        principle_count = 0

        for i, line in enumerate(lines, 1):
            # Check for section headers
            # Allow ## headers always, and ### headers if they're series markers
            section_match = section_pattern.match(line)
            if section_match:
                section_text = section_match.group(1).lower()
                is_series_header = any(
                    s in section_text
                    for s in [
                        "c-series",
                        "p-series",
                        "q-series",
                        "a-series",
                        "r-series",
                    ]
                )
                if "###" not in line or is_series_header:
                    current_section = self._get_category_from_section(
                        section_match.group(1)
                    )
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
                        self._build_principle(current_principle, domain_prefix)
                    )
                    principle_count += 1

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
                }
                continue

            # Check for new-format principle headers
            new_match = new_header_pattern.match(line)
            if new_match:
                title = new_match.group(1).strip()

                # Skip non-principle headers (like "When to Apply" etc.)
                skip_keywords = [
                    # Navigation and reference sections
                    "when to",
                    "how to",
                    "quick reference",
                    "decision tree",
                    "pre-action",
                    "operational",
                    "framework",
                    "immediate",
                    # Document structure sections
                    "domain implementation",
                    "extending",
                    "universal",
                    "template structure",
                    "the twelve",
                    "the three series",
                    "version history",
                    "evidence base",
                    "glossary",
                    "scope and non-goals",
                    "design philosophy",
                    "peer domain",
                    "meta ↔ domain",
                    "appendix",
                    # Series headers (these are section intros, not principles)
                    "c-series:",
                    "p-series:",
                    "q-series:",
                    "a-series:",
                    "r-series:",
                    "context principles",
                    "process principles",
                    "quality principles",
                    "architecture principles",
                    "reliability principles",
                ]
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
                        self._build_principle(current_principle, domain_prefix)
                    )
                    principle_count += 1

                # Start new principle (new format)
                current_principle = {
                    "category": current_section,
                    "title": title,
                    "domain": domain_config.name,
                    "start_line": i,
                    "end_line": None,
                    "content": "",
                    "series_code": None,
                }

        # Save last principle
        if current_principle:
            current_principle["end_line"] = len(lines)
            current_principle["content"] = "\n".join(
                lines[current_principle["start_line"] - 1 :]
            )
            principles.append(self._build_principle(current_principle, domain_prefix))

        logger.info(f"Extracted {len(principles)} principles from {domain_config.name}")
        return principles

    def _build_principle(self, data: dict, domain_prefix: str) -> Principle:
        """Build a Principle object with metadata."""
        # Generate slug-based ID: {domain}-{category}-{title-slug}
        category = data.get("category", "general")
        title_slug = self._slugify(data["title"])
        principle_id = f"{domain_prefix}-{category}-{title_slug}"

        # For backwards compatibility, extract series_code and number if present
        series_code = data.get("series_code")
        number = None
        if series_code:
            # Old format had series_code, try to get number from old-style matching
            number = data.get("number", 0)

        metadata = self._generate_metadata(
            principle_id, category, data["title"], data["content"]
        )

        return Principle(
            id=principle_id,
            domain=data["domain"],
            series_code=series_code,
            number=number,
            title=data["title"],
            content=data["content"],
            line_range=(data["start_line"], data["end_line"]),
            metadata=metadata,
            embedding_id=None,  # Set later after embedding
        )

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

        return phrases[:10]  # Limit to 10 phrases

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
        domain_prefix = self._get_domain_prefix(domain_config.name)

        # Pattern for method headers (##, ###, or #### with numbered sections like 1.2.3)
        # Includes #### to extract subsections (e.g., 2.1.5) as separate methods
        header_pattern = re.compile(r"^#{2,4}\s+(\d+(?:\.\d+)*)\s+(.+)$")

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

        for i, line in enumerate(lines, 1):
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
                    methods.append(
                        self._build_method(current_method, domain_prefix, method_count)
                    )
                    method_count += 1

                current_method = {
                    "section": section_num,
                    "title": title,
                    "domain": domain_config.name,
                    "start_line": i,
                    "end_line": None,
                    "content": "",
                }

        if current_method:
            current_method["end_line"] = len(lines)
            current_method["content"] = "\n".join(
                lines[current_method["start_line"] - 1 :]
            )
            methods.append(
                self._build_method(current_method, domain_prefix, method_count)
            )

        logger.info(f"Extracted {len(methods)} methods from {domain_config.name}")
        return methods

    def _build_method(self, data: dict, domain_prefix: str, index: int) -> Method:
        """Build a Method object with slug-based ID and rich metadata."""
        # Generate slug-based ID: {domain}-method-{title-slug}
        title_slug = self._slugify(data["title"])
        method_id = f"{domain_prefix}-method-{title_slug}"

        keywords = [w.lower() for w in data["title"].split() if len(w) > 3]

        # Generate rich metadata for better search
        metadata = self._generate_method_metadata(data["title"], data["content"])

        return Method(
            id=method_id,
            domain=data["domain"],
            title=data["title"],
            content=data["content"],
            line_range=(data["start_line"], data["end_line"]),
            keywords=keywords,
            metadata=metadata,
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

    def _get_domain_prefix(self, domain_name: str) -> str:
        """Get the prefix for principle IDs based on domain."""
        prefixes = {
            "constitution": "meta",
            "ai-coding": "coding",
            "multi-agent": "multi",
        }
        return prefixes.get(domain_name, domain_name[:4])

    def _save_index(self, index: GlobalIndex) -> None:
        """Save global index to JSON file."""
        index_file = self.settings.index_path / "global_index.json"

        with open(index_file, "w") as f:
            json.dump(index.model_dump(), f, indent=2)

        logger.info(f"Saved index to {index_file}")

    def _save_embeddings(self, embeddings: np.ndarray, filename: str) -> None:
        """Save embeddings to NumPy file."""
        embeddings_file = self.settings.index_path / filename
        np.save(embeddings_file, embeddings)
        logger.info(
            f"Saved embeddings to {embeddings_file} (shape: {embeddings.shape})"
        )


def main():
    """CLI entry point for extraction."""
    settings = load_settings()

    # Override documents path if provided
    if len(sys.argv) > 1:
        settings.documents_path = Path(sys.argv[1])

    logger.info(f"Extracting documents from: {settings.documents_path}")
    logger.info(f"Using embedding model: {settings.embedding_model}")

    extractor = DocumentExtractor(settings)
    index = extractor.extract_all()

    # Print summary
    print("\nExtraction complete:", file=sys.stderr)
    for domain_name, domain_index in index.domains.items():
        print(
            f"  {domain_name}: {len(domain_index.principles)} principles, "
            f"{len(domain_index.methods)} methods",
            file=sys.stderr,
        )
    print(f"\nEmbedding model: {index.embedding_model}", file=sys.stderr)
    print(f"Embedding dimensions: {index.embedding_dimensions}", file=sys.stderr)


if __name__ == "__main__":
    main()
