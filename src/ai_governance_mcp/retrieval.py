"""Retrieval engine for AI Governance documents.

Per specification v4: Hybrid retrieval with BM25 + semantic search + reranking.
"""

import json
import time
from typing import Optional

import numpy as np
from rank_bm25 import BM25Okapi

from .config import Settings, load_settings, setup_logging
from .models import (
    ConfidenceLevel,
    GlobalIndex,
    Method,
    Principle,
    RetrievalResult,
    ScoredMethod,
    ScoredPrinciple,
)

logger = setup_logging()


class RetrievalEngine:
    """Hybrid retrieval engine with BM25 + semantic search + reranking."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.index: Optional[GlobalIndex] = None
        self.content_embeddings: Optional[np.ndarray] = None
        self.domain_embeddings: Optional[np.ndarray] = None
        self.bm25_index: Optional[BM25Okapi] = None
        self.bm25_docs: list[tuple[str, str, int]] = []  # (domain, type, local_idx)
        self._embedder = None
        self._reranker = None
        self._feedback_ratings: dict[str, tuple[float, int]] = {}  # id -> (avg, count)
        self._load_index()
        self._load_feedback_ratings()

    @property
    def embedder(self):
        """Lazy-load embedding model for query encoding."""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.settings.embedding_model}")
            self._embedder = SentenceTransformer(self.settings.embedding_model)
        return self._embedder

    @property
    def reranker(self):
        """Lazy-load cross-encoder reranking model."""
        if self._reranker is None:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading reranking model: {self.settings.rerank_model}")
            self._reranker = CrossEncoder(self.settings.rerank_model)
        return self._reranker

    def _load_index(self) -> None:
        """Load global index and embeddings from disk."""
        index_path = self.settings.index_path / "global_index.json"
        content_emb_path = self.settings.index_path / "content_embeddings.npy"
        domain_emb_path = self.settings.index_path / "domain_embeddings.npy"

        if not index_path.exists():
            logger.warning(f"Index not found: {index_path}. Run extractor first.")
            return

        # Load index
        with open(index_path) as f:
            data = json.load(f)
            self.index = GlobalIndex(**data)
        logger.info(f"Loaded index with {len(self.index.domains)} domains")

        # Load embeddings
        if content_emb_path.exists():
            self.content_embeddings = np.load(content_emb_path, allow_pickle=False)
            logger.info(f"Loaded content embeddings: {self.content_embeddings.shape}")

        if domain_emb_path.exists():
            self.domain_embeddings = np.load(domain_emb_path, allow_pickle=False)
            logger.info(f"Loaded domain embeddings: {self.domain_embeddings.shape}")

        # Build BM25 index
        self._build_bm25_index()

    def _build_bm25_index(self) -> None:
        """Build BM25 index from loaded documents."""
        if not self.index:
            return

        corpus = []
        self.bm25_docs = []

        for domain_name, domain_index in self.index.domains.items():
            for i, principle in enumerate(domain_index.principles):
                # Tokenize for BM25
                text = self._get_bm25_text(principle)
                tokens = text.lower().split()
                corpus.append(tokens)
                self.bm25_docs.append((domain_name, "principle", i))

            for i, method in enumerate(domain_index.methods):
                text = self._get_method_bm25_text(method)
                tokens = text.lower().split()
                corpus.append(tokens)
                self.bm25_docs.append((domain_name, "method", i))

        if corpus:
            self.bm25_index = BM25Okapi(corpus)
            logger.info(f"Built BM25 index with {len(corpus)} documents")

    def _load_feedback_ratings(self) -> None:
        """Load feedback ratings from feedback.jsonl for adaptive retrieval.

        Per contrarian review: activates dormant feedback infrastructure.
        Calculates average rating per principle for score boosting.
        """
        if not self.settings.enable_feedback_adaptation:
            logger.debug("Feedback adaptation disabled")
            return

        feedback_path = self.settings.logs_path / "feedback.jsonl"
        if not feedback_path.exists():
            logger.debug("No feedback file found - adaptive retrieval inactive")
            return

        # Collect ratings per principle
        ratings_by_id: dict[str, list[int]] = {}

        try:
            with open(feedback_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        principle_id = entry.get("principle_id", "")
                        rating = entry.get("rating", 0)
                        if principle_id and 1 <= rating <= 5:
                            if principle_id not in ratings_by_id:
                                ratings_by_id[principle_id] = []
                            ratings_by_id[principle_id].append(rating)
                            # Cap per-principle ratings to prevent feedback poisoning
                            if len(ratings_by_id[principle_id]) > 100:
                                ratings_by_id[principle_id] = ratings_by_id[
                                    principle_id
                                ][-100:]
                    except json.JSONDecodeError:
                        continue  # Skip malformed entries

            # Calculate averages
            for principle_id, ratings in ratings_by_id.items():
                avg = sum(ratings) / len(ratings)
                self._feedback_ratings[principle_id] = (avg, len(ratings))

            if self._feedback_ratings:
                logger.info(
                    f"Loaded feedback for {len(self._feedback_ratings)} principles"
                )
        except Exception as e:
            logger.warning(f"Failed to load feedback: {e}")

    def reload_feedback_ratings(self) -> None:
        """Reload feedback ratings from disk.

        Call this to pick up new feedback without restarting the server.
        """
        self._feedback_ratings = {}
        self._load_feedback_ratings()

    def get_feedback_adjustment(self, principle_id: str) -> float:
        """Get score adjustment for a principle based on feedback.

        Returns:
            Positive value for boost, negative for penalty, 0 for no adjustment.
        """
        if not self.settings.enable_feedback_adaptation:
            return 0.0

        if principle_id not in self._feedback_ratings:
            return 0.0

        avg_rating, count = self._feedback_ratings[principle_id]

        # Require minimum ratings for confidence
        if count < self.settings.feedback_min_ratings:
            return 0.0

        if avg_rating >= self.settings.feedback_boost_threshold:
            return self.settings.feedback_boost_amount
        elif avg_rating <= self.settings.feedback_penalty_threshold:
            return -self.settings.feedback_penalty_amount

        return 0.0

    def _get_bm25_text(self, principle: Principle) -> str:
        """Create text for BM25 indexing."""
        parts = [
            principle.title,
            principle.content[:1000],
            " ".join(principle.metadata.keywords),
            " ".join(principle.metadata.synonyms),
            " ".join(principle.metadata.trigger_phrases),
            " ".join(principle.metadata.failure_indicators),
        ]
        return " ".join(parts)

    def _get_method_bm25_text(self, method: Method) -> str:
        """Create text for BM25 indexing from a method.

        Includes metadata fields for improved keyword matching.
        """
        parts = [
            method.title,
            method.content[:1500],  # Increased from 500
            " ".join(method.keywords),  # Legacy keywords
        ]

        # Add metadata fields for richer keyword matching
        meta = method.metadata
        if meta.keywords:
            parts.append(" ".join(meta.keywords))
        if meta.trigger_phrases:
            parts.append(" ".join(meta.trigger_phrases))
        if meta.purpose_keywords:
            parts.append(" ".join(meta.purpose_keywords))
        if meta.applies_to:
            parts.append(" ".join(meta.applies_to))
        if meta.guideline_keywords:
            parts.append(" ".join(meta.guideline_keywords))

        return " ".join(parts)

    # =========================================================================
    # T6: Domain Router
    # =========================================================================

    def route_domains(self, query: str) -> dict[str, float]:
        """Route query to relevant domains using semantic similarity.

        Returns dict of domain_name -> similarity_score.
        """
        if self.domain_embeddings is None or not self.index:
            return {}

        # Encode query
        query_embedding = self.embedder.encode([query])[0]

        # Calculate similarity with each domain
        scores = {}
        for i, domain_config in enumerate(self.index.domain_configs):
            if i < len(self.domain_embeddings):
                similarity = self._cosine_similarity(
                    query_embedding, self.domain_embeddings[i]
                )
                if similarity >= self.settings.domain_similarity_threshold:
                    scores[domain_config.name] = float(similarity)

        # Sort by score and limit
        sorted_scores = dict(
            sorted(scores.items(), key=lambda x: -x[1])[: self.settings.max_domains]
        )

        return sorted_scores

    # =========================================================================
    # T7: BM25 Search
    # =========================================================================

    def bm25_search(
        self, query: str, domains: list[str] | None = None, top_k: int = 50
    ) -> list[tuple[str, str, int, float]]:
        """BM25 keyword search.

        Returns list of (domain, type, local_idx, score).
        """
        if not self.bm25_index:
            return []

        tokens = query.lower().split()
        scores = self.bm25_index.get_scores(tokens)

        # Filter by domains if specified
        results = []
        for idx, score in enumerate(scores):
            if score > 0:
                domain, item_type, local_idx = self.bm25_docs[idx]
                if domains is None or domain in domains:
                    results.append((domain, item_type, local_idx, float(score)))

        # Sort and limit
        results.sort(key=lambda x: -x[3])
        return results[:top_k]

    # =========================================================================
    # T8: Semantic Search
    # =========================================================================

    def semantic_search(
        self, query: str, domains: list[str] | None = None, top_k: int = 50
    ) -> list[tuple[str, str, int, float]]:
        """Semantic search using embeddings.

        Returns list of (domain, type, local_idx, score).
        """
        if self.content_embeddings is None or not self.index:
            return []

        # Encode query
        query_embedding = self.embedder.encode([query])[0]

        # Calculate similarities
        results = []
        for idx in range(len(self.content_embeddings)):
            if idx >= len(self.bm25_docs):
                break

            domain, item_type, local_idx = self.bm25_docs[idx]
            if domains is None or domain in domains:
                similarity = self._cosine_similarity(
                    query_embedding, self.content_embeddings[idx]
                )
                if similarity > 0:
                    results.append((domain, item_type, local_idx, float(similarity)))

        # Sort and limit
        results.sort(key=lambda x: -x[3])
        return results[:top_k]

    # =========================================================================
    # T9: Score Fusion
    # =========================================================================

    def fuse_scores(
        self,
        bm25_results: list[tuple[str, str, int, float]],
        semantic_results: list[tuple[str, str, int, float]],
    ) -> dict[tuple[str, str, int], tuple[float, float, float]]:
        """Fuse BM25 and semantic scores.

        Returns dict of (domain, type, local_idx) -> (bm25_norm, semantic_score, combined).
        """
        # Normalize BM25 scores to 0-1
        max_bm25 = max((r[3] for r in bm25_results), default=1.0)
        bm25_norm = {
            (r[0], r[1], r[2]): r[3] / max_bm25 if max_bm25 > 0 else 0
            for r in bm25_results
        }

        # Semantic scores are already 0-1
        semantic_scores = {(r[0], r[1], r[2]): r[3] for r in semantic_results}

        # Get all keys
        all_keys = set(bm25_norm.keys()) | set(semantic_scores.keys())

        # Fuse with configurable weights
        fused = {}
        for key in all_keys:
            bm25_score = bm25_norm.get(key, 0.0)
            sem_score = semantic_scores.get(key, 0.0)

            combined = (
                self.settings.semantic_weight * sem_score
                + (1 - self.settings.semantic_weight) * bm25_score
            )

            fused[key] = (bm25_score, sem_score, combined)

        return fused

    # =========================================================================
    # T10: Cross-Encoder Reranking
    # =========================================================================

    def rerank(
        self, query: str, candidates: list[tuple[str, str, int, float]]
    ) -> list[tuple[str, str, int, float]]:
        """Rerank candidates using cross-encoder.

        Takes top candidates by combined score and reranks with cross-encoder.
        """
        if not candidates or not self.index:
            return candidates

        # Limit to top-k for reranking
        top_candidates = candidates[: self.settings.rerank_top_k]

        # Prepare pairs for cross-encoder
        pairs = []
        for domain, item_type, local_idx, _ in top_candidates:
            text = self._get_candidate_text(domain, item_type, local_idx)
            pairs.append((query, text))

        # Score with cross-encoder
        if pairs:
            rerank_scores = self.reranker.predict(pairs)

            # Combine with new scores
            reranked = []
            for i, (domain, item_type, local_idx, _) in enumerate(top_candidates):
                # Normalize cross-encoder score to 0-1 (sigmoid-like)
                score = float(1 / (1 + np.exp(-rerank_scores[i])))
                reranked.append((domain, item_type, local_idx, score))

            # Sort by rerank score
            reranked.sort(key=lambda x: -x[3])
            return reranked

        return top_candidates

    def _get_candidate_text(self, domain: str, item_type: str, local_idx: int) -> str:
        """Get text for a candidate for reranking."""
        if not self.index or domain not in self.index.domains:
            return ""

        domain_index = self.index.domains[domain]

        if item_type == "principle" and local_idx < len(domain_index.principles):
            p = domain_index.principles[local_idx]
            return f"{p.title}\n{p.content[:500]}"
        elif item_type == "method" and local_idx < len(domain_index.methods):
            m = domain_index.methods[local_idx]
            return f"{m.title}\n{m.content[:500]}"

        return ""

    # =========================================================================
    # T11: Hierarchy Filter
    # =========================================================================

    def apply_hierarchy(
        self, principles: list[ScoredPrinciple]
    ) -> list[ScoredPrinciple]:
        """Apply governance hierarchy ordering.

        S-Series > Constitution > Domain principles.
        Within same level, sort by score.
        """
        hierarchy_order = {
            "S": 0,  # Safety - highest priority
            "C": 1,  # Core
            "Q": 2,  # Quality
            "O": 3,  # Operational
            "MA": 4,  # Meta-awareness
            "G": 5,  # Growth
            "P": 6,  # Process (domain)
            "A": 7,  # Architecture (multi-agent)
            "T": 8,  # Trust
            "D": 9,  # Delegation
        }

        def sort_key(sp: ScoredPrinciple) -> tuple:
            series = sp.principle.series_code
            hierarchy = hierarchy_order.get(series, 99)
            return (hierarchy, -sp.combined_score, sp.principle.number or 0)

        return sorted(principles, key=sort_key)

    # =========================================================================
    # Main Retrieval Pipeline
    # =========================================================================

    def retrieve(
        self,
        query: str,
        domain: str | None = None,
        include_constitution: bool = True,
        include_methods: bool = True,
        max_results: int | None = None,
    ) -> RetrievalResult:
        """Full hybrid retrieval pipeline.

        1. Route to domains (or use explicit domain)
        2. BM25 keyword search
        3. Semantic search
        4. Score fusion
        5. Reranking
        6. Hierarchy filtering
        """
        start_time = time.time()
        max_results = max_results or self.settings.max_results

        if not self.index:
            return RetrievalResult(
                query=query,
                domains_detected=[],
                domain_scores={},
                constitution_principles=[],
                domain_principles=[],
                methods=[],
                s_series_triggered=False,
                retrieval_time_ms=0,
            )

        # Step 1: Route to domains
        if domain:
            # Forced domain - include it in search
            domain_scores = {domain: 1.0} if domain in self.index.domains else {}
            detected_domains = []
            search_domains = [domain] if domain in self.index.domains else []
            if include_constitution and "constitution" not in search_domains:
                search_domains.append("constitution")
        else:
            domain_scores = self.route_domains(query)
            detected_domains = list(domain_scores.keys())
            if detected_domains:
                # Search detected domains plus constitution
                search_domains = list(set(detected_domains + ["constitution"]))
            else:
                # No confident domain match - search ALL domains
                search_domains = list(self.index.domains.keys())

        # Step 2-3: Hybrid search
        bm25_results = self.bm25_search(query, search_domains)
        semantic_results = self.semantic_search(query, search_domains)

        # Step 4: Fuse scores
        fused = self.fuse_scores(bm25_results, semantic_results)

        # Step 5: Prepare candidates for reranking
        candidates = [
            (key[0], key[1], key[2], scores[2])  # domain, type, idx, combined
            for key, scores in fused.items()
            if scores[2] >= self.settings.min_score_threshold
        ]
        candidates.sort(key=lambda x: -x[3])

        # Step 6: Rerank top candidates
        reranked = self.rerank(query, candidates)

        # Step 7: Build scored principles/methods
        constitution_principles: list[ScoredPrinciple] = []
        domain_principles: list[ScoredPrinciple] = []
        methods: list[ScoredMethod] = []
        s_series_triggered = False

        for domain_name, item_type, local_idx, rerank_score in reranked:
            domain_index = self.index.domains.get(domain_name)
            if not domain_index:
                continue

            # Get original scores
            key = (domain_name, item_type, local_idx)
            bm25_norm, sem_score, combined = fused.get(key, (0, 0, rerank_score))

            if item_type == "principle" and local_idx < len(domain_index.principles):
                principle = domain_index.principles[local_idx]

                # Check S-Series
                if principle.series_code == "S":
                    s_series_triggered = True

                # Apply feedback-based score adjustment
                # Per contrarian review: adaptive retrieval based on user feedback
                # S-Series exemption: NEVER penalize safety principles (per second contrarian review)
                feedback_adj = self.get_feedback_adjustment(principle.id)
                if principle.series_code == "S" and feedback_adj < 0:
                    feedback_adj = 0.0  # S-Series exempt from penalties
                adjusted_combined = min(1.0, max(0.0, combined + feedback_adj))
                adjusted_rerank = min(1.0, max(0.0, rerank_score + feedback_adj))

                # Add feedback boost to match reasons if applied
                match_reasons = self._get_match_reasons(bm25_norm, sem_score)
                if feedback_adj > 0:
                    match_reasons.append("feedback boost")
                elif feedback_adj < 0:
                    match_reasons.append("feedback penalty")

                scored = ScoredPrinciple(
                    principle=principle,
                    semantic_score=sem_score,
                    keyword_score=bm25_norm,
                    combined_score=adjusted_combined,
                    rerank_score=adjusted_rerank,
                    confidence=self._get_confidence(adjusted_rerank),
                    match_reasons=match_reasons,
                )

                if domain_name == "constitution":
                    if include_constitution:
                        constitution_principles.append(scored)
                else:
                    domain_principles.append(scored)

            elif item_type == "method" and include_methods:
                if local_idx < len(domain_index.methods):
                    method = domain_index.methods[local_idx]
                    scored_method = ScoredMethod(
                        method=method,
                        semantic_score=sem_score,
                        keyword_score=bm25_norm,
                        combined_score=combined,
                        confidence=self._get_confidence(combined),
                    )
                    methods.append(scored_method)

        # Step 8: Apply hierarchy and limit
        constitution_principles = self.apply_hierarchy(constitution_principles)[
            :max_results
        ]
        domain_principles = self.apply_hierarchy(domain_principles)[:max_results]

        retrieval_time = (time.time() - start_time) * 1000

        return RetrievalResult(
            query=query,
            domains_detected=detected_domains,
            domain_scores=domain_scores,
            constitution_principles=constitution_principles,
            domain_principles=domain_principles,
            methods=methods[:max_results] if include_methods else [],
            s_series_triggered=s_series_triggered,
            retrieval_time_ms=retrieval_time,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _get_confidence(self, score: float) -> ConfidenceLevel:
        """Determine confidence level from score."""
        if score >= self.settings.confidence_high_threshold:
            return ConfidenceLevel.HIGH
        elif score >= self.settings.confidence_medium_threshold:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _get_match_reasons(self, bm25_score: float, semantic_score: float) -> list[str]:
        """Generate human-readable match reasons."""
        reasons = []
        if bm25_score > 0.5:
            reasons.append("strong keyword match")
        elif bm25_score > 0.2:
            reasons.append("keyword match")
        if semantic_score > 0.7:
            reasons.append("strong semantic similarity")
        elif semantic_score > 0.4:
            reasons.append("semantic similarity")
        return reasons

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_principle_by_id(self, principle_id: str) -> Principle | None:
        """Get a specific principle by its ID."""
        if not self.index:
            return None

        parts = principle_id.split("-")
        if len(parts) < 2:
            return None

        prefix = parts[0]
        prefix_to_domain = {
            "meta": "constitution",
            "coding": "ai-coding",
            "multi": "multi-agent",
            "stor": "storytelling",
            "mult": "multimodal-rag",
        }

        domain_name = prefix_to_domain.get(prefix)
        if not domain_name or domain_name not in self.index.domains:
            return None

        for principle in self.index.domains[domain_name].principles:
            if principle.id == principle_id:
                return principle

        return None

    def get_method_by_id(self, method_id: str) -> Method | None:
        """Get a specific method by its ID."""
        if not self.index:
            return None

        parts = method_id.split("-")
        if len(parts) < 2:
            return None

        prefix = parts[0]
        prefix_to_domain = {
            "meta": "constitution",
            "coding": "ai-coding",
            "multi": "multi-agent",
            "stor": "storytelling",
            "mult": "multimodal-rag",
        }

        domain_name = prefix_to_domain.get(prefix)
        if not domain_name or domain_name not in self.index.domains:
            return None

        for method in self.index.domains[domain_name].methods:
            if method.id == method_id:
                return method

        return None

    def list_domains(self) -> list[dict]:
        """List all available domains with stats."""
        if not self.index:
            return []

        result = []
        for domain_config in self.index.domain_configs:
            domain_index = self.index.domains.get(domain_config.name)
            result.append(
                {
                    "name": domain_config.name,
                    "display_name": domain_config.display_name,
                    "description": domain_config.description[:100] + "...",
                    "principles_count": len(domain_index.principles)
                    if domain_index
                    else 0,
                    "methods_count": len(domain_index.methods) if domain_index else 0,
                    "priority": domain_config.priority,
                }
            )
        return result

    def get_domain_summary(self, domain_name: str) -> dict | None:
        """Get detailed summary of a domain."""
        if not self.index or domain_name not in self.index.domains:
            return None

        domain_index = self.index.domains[domain_name]
        config = next(
            (c for c in self.index.domain_configs if c.name == domain_name), None
        )

        if not config:
            return None

        return {
            "name": domain_name,
            "display_name": config.display_name,
            "description": config.description,
            "principles": [
                {"id": p.id, "title": p.title, "series": p.series_code}
                for p in domain_index.principles
            ],
            "methods": [{"id": m.id, "title": m.title} for m in domain_index.methods],
            "last_extracted": domain_index.last_extracted,
        }


def main():
    """Test retrieval engine."""
    import sys

    settings = load_settings()
    engine = RetrievalEngine(settings)

    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "how do I handle incomplete specifications"
    )

    print(f"Query: {query}", file=sys.stderr)
    print("\nDomain routing:", file=sys.stderr)
    for domain, score in engine.route_domains(query).items():
        print(f"  {domain}: {score:.3f}", file=sys.stderr)

    result = engine.retrieve(query)

    print(f"\nRetrieval time: {result.retrieval_time_ms:.1f}ms", file=sys.stderr)
    print(f"S-Series triggered: {result.s_series_triggered}", file=sys.stderr)

    print(f"\nConstitution ({len(result.constitution_principles)}):", file=sys.stderr)
    for sp in result.constitution_principles[:3]:
        print(
            f"  [{sp.confidence.value}] {sp.principle.id}: {sp.principle.title}",
            file=sys.stderr,
        )
        print(
            f"    Scores: BM25={sp.keyword_score:.2f}, Semantic={sp.semantic_score:.2f}, "
            f"Combined={sp.combined_score:.2f}",
            file=sys.stderr,
        )

    print(f"\nDomain ({len(result.domain_principles)}):", file=sys.stderr)
    for sp in result.domain_principles[:5]:
        print(
            f"  [{sp.confidence.value}] {sp.principle.id}: {sp.principle.title}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
