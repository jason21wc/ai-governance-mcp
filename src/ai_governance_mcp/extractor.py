"""Document extractor for AI Governance documents.

Per specification v4: Build-time extraction creates index and embeddings
for hybrid retrieval (BM25 + semantic search).
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from .config import Settings, load_settings, load_domains_registry, setup_logging, ensure_directories
from .models import DomainConfig, DomainIndex, GlobalIndex, Method, Principle, PrincipleMetadata

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

        # Pattern for principle headers
        # Constitution: ### C1. Context Engineering
        # Domain: #### C1. Specification Completeness (The Requirements Act)
        header_pattern = re.compile(
            r"^#{2,4}\s+([A-Z]+)(\d+)\.\s+(.+?)(?:\s+\(The .+?\))?$"
        )

        current_principle = None

        for i, line in enumerate(lines, 1):
            match = header_pattern.match(line)
            if match:
                # Save previous principle
                if current_principle:
                    current_principle["end_line"] = i - 1
                    current_principle["content"] = "\n".join(
                        lines[current_principle["start_line"] - 1 : i - 1]
                    )
                    principles.append(self._build_principle(current_principle, domain_prefix))

                # Start new principle
                series_code = match.group(1)
                number = int(match.group(2))
                title = match.group(3).strip()

                current_principle = {
                    "series_code": series_code,
                    "number": number,
                    "title": title,
                    "domain": domain_config.name,
                    "start_line": i,
                    "end_line": None,
                    "content": "",
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
        principle_id = f"{domain_prefix}-{data['series_code']}{data['number']}"

        metadata = self._generate_metadata(
            principle_id, data["series_code"], data["title"], data["content"]
        )

        return Principle(
            id=principle_id,
            domain=data["domain"],
            series_code=data["series_code"],
            number=data["number"],
            title=data["title"],
            content=data["content"],
            line_range=(data["start_line"], data["end_line"]),
            metadata=metadata,
            embedding_id=None,  # Set later after embedding
        )

    def _generate_metadata(
        self, principle_id: str, series_code: str, title: str, content: str
    ) -> PrincipleMetadata:
        """Generate metadata for BM25 keyword search."""
        # Extract keywords from title
        title_words = [w.lower() for w in title.split() if len(w) > 3]

        # Extract key phrases from content
        trigger_phrases = self._extract_phrases(content)

        # Extract failure indicators
        failure_indicators = self._extract_failure_indicators(content)

        return PrincipleMetadata(
            keywords=title_words,
            synonyms=[],  # Could be expanded with synonym database
            trigger_phrases=trigger_phrases,
            failure_indicators=failure_indicators,
            aliases=[principle_id.split("-")[-1]],  # e.g., "C1"
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
                if w not in ("this", "that", "with", "from", "have", "been", "will", "when")
            ]
            indicators.extend(words[:5])

        return indicators

    def _extract_methods(self, domain_config: DomainConfig) -> list[Method]:
        """Extract methods from a domain's methods file."""
        file_path = self.settings.documents_path / domain_config.methods_file
        if not file_path.exists():
            logger.warning(f"Methods file not found: {file_path}")
            return []

        content = file_path.read_text()
        lines = content.split("\n")

        methods = []
        domain_prefix = self._get_domain_prefix(domain_config.name)

        # Pattern for method headers (## or ### with numbered sections)
        header_pattern = re.compile(r"^#{2,3}\s+(\d+(?:\.\d+)?)\s+(.+)$")

        current_method = None
        method_count = 0

        for i, line in enumerate(lines, 1):
            match = header_pattern.match(line)
            if match:
                if current_method:
                    current_method["end_line"] = i - 1
                    current_method["content"] = "\n".join(
                        lines[current_method["start_line"] - 1 : i - 1]
                    )
                    methods.append(self._build_method(current_method, domain_prefix, method_count))
                    method_count += 1

                section_num = match.group(1)
                title = match.group(2).strip()

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
            methods.append(self._build_method(current_method, domain_prefix, method_count))

        logger.info(f"Extracted {len(methods)} methods from {domain_config.name}")
        return methods

    def _build_method(self, data: dict, domain_prefix: str, index: int) -> Method:
        """Build a Method object."""
        method_id = f"{domain_prefix}-M{index + 1}"
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
        logger.info(f"Saved embeddings to {embeddings_file} (shape: {embeddings.shape})")


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
    print(f"\nExtraction complete:", file=sys.stderr)
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
