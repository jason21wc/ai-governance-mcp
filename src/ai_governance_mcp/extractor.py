"""Document extractor for AI Governance documents.

Per specification v4: Build-time extraction creates index and embeddings
for hybrid retrieval (BM25 + semantic search).
"""

import json
import re
import sys
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
    Principle,
    PrincipleMetadata,
)

logger = setup_logging()


class EmbeddingGenerator:
    """Generates embeddings using sentence-transformers.

    Lazy-loads the model to avoid import overhead when not needed.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
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


class DocumentExtractor:
    """Extracts principles and methods from governance markdown documents.

    Creates a GlobalIndex with embeddings for hybrid retrieval.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.domains = load_domains_registry(settings)
        self.embedder = EmbeddingGenerator(settings.embedding_model)

    def extract_all(self) -> GlobalIndex:
        """Extract all domains and build global index with embeddings."""
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
                text = f"{method.title}\n{method.content[:500]}"
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
        """
        parts = [
            principle.title,
            principle.content[:1000],  # First 1000 chars of content
        ]

        # Add metadata keywords for richer embedding
        meta = principle.metadata
        if meta.keywords:
            parts.append(" ".join(meta.keywords[:5]))
        if meta.trigger_phrases:
            parts.append(" ".join(meta.trigger_phrases[:3]))

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
                is_series_header = any(s in section_text for s in [
                    "c-series", "p-series", "q-series", "a-series", "r-series"
                ])
                if "###" not in line or is_series_header:
                    current_section = self._get_category_from_section(section_match.group(1))
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
                    "when to", "how to", "quick reference", "decision tree",
                    "pre-action", "operational", "framework", "immediate",
                    # Document structure sections
                    "domain implementation", "extending", "universal",
                    "template structure", "the twelve", "the three series",
                    "version history", "evidence base", "glossary",
                    "scope and non-goals", "design philosophy",
                    "peer domain", "meta ↔ domain", "appendix",
                    # Series headers (these are section intros, not principles)
                    "c-series:", "p-series:", "q-series:",
                    "a-series:", "r-series:",
                    "context principles", "process principles", "quality principles",
                    "architecture principles", "reliability principles",
                ]
                if any(kw in title.lower() for kw in skip_keywords):
                    continue

                # Must have a principle-defining section following
                # Constitution uses **Definition**, Domain docs use **Failure Mode** or **Why This Principle Matters**
                next_lines = "\n".join(lines[i:i+10])
                principle_indicators = [
                    "**Definition**",
                    "**Failure Mode",
                    "**Why This Principle Matters**",
                    "**Domain Application",
                    "**Constitutional Basis**"
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

        # Pattern for method headers (## or ### with numbered sections like 1.2.3)
        header_pattern = re.compile(r"^#{2,3}\s+(\d+(?:\.\d+)*)\s+(.+)$")

        # Document structure sections to skip (not actual methods)
        skip_method_titles = [
            # Document metadata sections
            "scope", "applicability", "relationship to other",
            # Glossary/terminology sections
            "terms", "glossary", "definitions",
            # Overview sections that aren't procedures
            "purpose", "overview", "introduction", "background",
            # Reference sections
            "legend", "index", "references", "appendix",
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
        """Build a Method object with slug-based ID."""
        # Generate slug-based ID: {domain}-method-{title-slug}
        title_slug = self._slugify(data["title"])
        method_id = f"{domain_prefix}-method-{title_slug}"

        keywords = [w.lower() for w in data["title"].split() if len(w) > 3]

        return Method(
            id=method_id,
            domain=data["domain"],
            title=data["title"],
            content=data["content"],
            line_range=(data["start_line"], data["end_line"]),
            keywords=keywords,
            embedding_id=None,  # Set later
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
