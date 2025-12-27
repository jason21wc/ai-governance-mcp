"""Retrieval engine for AI Governance documents.

Implements scoring, domain detection, and principle retrieval per specification v3 §3.2.
"""

import json
import re
from pathlib import Path

from .config import ServerConfig, load_config, load_domains_registry, setup_logging
from .models import (
    DomainConfig,
    DomainIndex,
    Method,
    Principle,
    RetrievalResult,
    ScoredPrinciple,
)

logger = setup_logging()


class RetrievalEngine:
    """Core retrieval engine for governance documents."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.domains = load_domains_registry(config)
        self.indexes: dict[str, DomainIndex] = {}
        self._load_indexes()

    def _load_indexes(self) -> None:
        """Load all domain indexes from disk."""
        for domain_name in self.domains:
            index_path = self.config.index_path / f"{domain_name}-index.json"
            if index_path.exists():
                with open(index_path) as f:
                    data = json.load(f)
                    self.indexes[domain_name] = DomainIndex(**data)
                logger.debug(f"Loaded index for {domain_name}")
            else:
                logger.warning(f"Index not found for {domain_name}: {index_path}")

    def detect_domains(self, query: str) -> list[str]:
        """Detect which domains are relevant to a query.

        Per specification v3 §3.1: Returns list of matching domains.
        Multi-domain queries return multiple domains.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        domain_scores: dict[str, float] = {}

        for domain_name, domain_config in self.domains.items():
            if domain_name == "constitution":
                # Constitution is always included, not detected
                continue

            score = 0.0

            # Phrase matching (priority - weight 2.0)
            for phrase in domain_config.trigger_phrases:
                if phrase.lower() in query_lower:
                    score += 2.0

            # Keyword matching (weight 1.0)
            for keyword in domain_config.trigger_keywords:
                if self._word_match(keyword.lower(), query_words):
                    score += 1.0

            if score > 0:
                domain_scores[domain_name] = score

        # Return all domains with score > 0, sorted by score (then priority)
        if not domain_scores:
            return []

        # Sort by score descending, then by priority ascending
        sorted_domains = sorted(
            domain_scores.keys(),
            key=lambda d: (-domain_scores[d], self.domains[d].priority),
        )

        return sorted_domains

    def retrieve(
        self,
        query: str,
        domain: str | None = None,
        include_constitution: bool = True,
        include_methods: bool = False,
        max_results: int | None = None,
    ) -> RetrievalResult:
        """Retrieve relevant principles for a query.

        Per specification v3 §3.2: Main retrieval algorithm.

        Args:
            query: The user's query
            domain: Specific domain to search (auto-detected if None)
            include_constitution: Include constitution principles in output
            include_methods: Include methods in response
            max_results: Maximum principles per domain

        Returns:
            RetrievalResult with scored principles
        """
        max_results = max_results or self.config.max_principles_per_domain

        # Step 1: Detect domains (or use explicit domain)
        if domain:
            # Explicit domain - use it but don't set as "detected"
            search_domains = [domain] if domain in self.domains else []
            detected_domains = []  # Empty because domain was explicit, not detected
        else:
            detected_domains = self.detect_domains(query)
            search_domains = detected_domains

        # Step 2: ALWAYS search constitution internally (S-Series check)
        constitution_results = []
        s_series_triggered = False

        if "constitution" in self.indexes:
            constitution_scored = self._score_principles(
                query, self.indexes["constitution"].principles
            )
            constitution_results = constitution_scored[:max_results]

            # Check for S-Series triggers
            s_series_triggered = any(
                sp.principle.series_code == "S" and sp.score > 0
                for sp in constitution_scored
            )

        # Step 3: Search domains (detected or explicit)
        domain_results: list[ScoredPrinciple] = []
        for domain_name in search_domains:
            if domain_name not in self.indexes:
                continue

            domain_scored = self._score_principles(
                query, self.indexes[domain_name].principles
            )
            domain_results.extend(domain_scored[:max_results])

        # Step 4: Get methods if requested
        methods: list[Method] = []
        if include_methods:
            for domain_name in search_domains:
                if domain_name in self.indexes:
                    methods.extend(self.indexes[domain_name].methods)

        # Step 5: Sort all results by score and hierarchy
        domain_results = self._sort_by_hierarchy(domain_results)

        # Step 6: Build result
        return RetrievalResult(
            query=query,
            domains_detected=detected_domains,
            constitution_principles=constitution_results if include_constitution else [],
            domain_principles=domain_results,
            methods=methods,
            s_series_triggered=s_series_triggered,
        )

    def _score_principles(
        self, query: str, principles: list[Principle]
    ) -> list[ScoredPrinciple]:
        """Score principles against a query.

        Per specification v3 §3.2.3: Scoring algorithm.
        """
        scored: list[ScoredPrinciple] = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for principle in principles:
            score = 0.0
            match_reasons: list[str] = []

            # 1. Keyword matching (weight: 1.0)
            for keyword in principle.metadata.keywords:
                if self._word_match(keyword.lower(), query_words):
                    score += self.config.keyword_weight
                    match_reasons.append(f"keyword:{keyword}")

            # 2. Synonym matching (weight: 0.8)
            for synonym in principle.metadata.synonyms:
                if self._word_match(synonym.lower(), query_words):
                    score += self.config.synonym_weight
                    match_reasons.append(f"synonym:{synonym}")

            # 3. Phrase matching (weight: 2.0)
            for phrase in principle.metadata.trigger_phrases:
                if phrase.lower() in query_lower:
                    score += self.config.phrase_weight
                    match_reasons.append(f"phrase:{phrase}")

            # 4. Failure indicator matching (weight: 1.5)
            for indicator in principle.metadata.failure_indicators:
                if self._word_match(indicator.lower(), query_words):
                    score += self.config.failure_indicator_weight
                    match_reasons.append(f"failure:{indicator}")

            # 5. S-Series priority boost
            if principle.series_code == "S":
                # Check for S-Series specific triggers
                s_triggers = [
                    "security",
                    "privacy",
                    "harm",
                    "safety",
                    "ethical",
                    "vulnerability",
                    "breach",
                    "leak",
                    "malicious",
                    "injection",
                ]
                for trigger in s_triggers:
                    if trigger in query_lower:
                        score *= self.config.s_series_multiplier
                        match_reasons.append(f"s-series-trigger:{trigger}")
                        break

            if score >= self.config.min_score_threshold:
                scored.append(
                    ScoredPrinciple(
                        principle=principle,
                        score=score,
                        match_reasons=match_reasons,
                    )
                )

        # Sort by score descending
        scored.sort(key=lambda sp: -sp.score)
        return scored

    def _sort_by_hierarchy(
        self, principles: list[ScoredPrinciple]
    ) -> list[ScoredPrinciple]:
        """Sort principles by governance hierarchy.

        Per specification v3 §3.2.4: S-Series > Constitution > Domain.
        Within same level, sort by score.
        """
        # Define hierarchy order
        hierarchy_order = {
            "S": 0,  # Safety - highest priority
            "C": 1,  # Core
            "Q": 2,  # Quality
            "O": 3,  # Operational
            "MA": 4,  # Multi-Agent
            "G": 5,  # Governance
            "P": 6,  # Process (domain)
            "A": 7,  # Architecture (multi-agent domain)
            "T": 8,  # Trust (multi-agent domain)
            "D": 9,  # Delegation (multi-agent domain)
        }

        def sort_key(sp: ScoredPrinciple) -> tuple:
            series = sp.principle.series_code
            hierarchy = hierarchy_order.get(series, 99)
            # Negative score for descending order
            return (hierarchy, -sp.score, sp.principle.number)

        return sorted(principles, key=sort_key)

    def _word_match(self, word: str, query_words: set[str]) -> bool:
        """Check if word matches any query word (whole-word, case-insensitive).

        Per specification v3 §3.2.2: Whole-word matching to prevent false positives.
        """
        return word in query_words

    def get_principle_by_id(self, principle_id: str) -> Principle | None:
        """Get a specific principle by its ID."""
        # Parse the ID to find the domain
        parts = principle_id.split("-")
        if len(parts) < 2:
            return None

        prefix = parts[0]
        prefix_to_domain = {
            "meta": "constitution",
            "coding": "ai-coding",
            "multi": "multi-agent",
        }

        domain_name = prefix_to_domain.get(prefix)
        if not domain_name or domain_name not in self.indexes:
            return None

        for principle in self.indexes[domain_name].principles:
            if principle.id == principle_id:
                return principle

        return None

    def list_domains(self) -> list[dict]:
        """List all available domains with stats."""
        result = []
        for domain_name, domain_config in self.domains.items():
            index = self.indexes.get(domain_name)
            result.append(
                {
                    "name": domain_name,
                    "display_name": domain_config.display_name,
                    "principles_count": len(index.principles) if index else 0,
                    "methods_count": len(index.methods) if index else 0,
                    "trigger_keywords": domain_config.trigger_keywords[:5],  # Sample
                }
            )
        return result

    def list_principles(self, domain: str | None = None) -> list[dict]:
        """List all principles, optionally filtered by domain."""
        result = []
        domains_to_check = [domain] if domain else list(self.indexes.keys())

        for domain_name in domains_to_check:
            if domain_name not in self.indexes:
                continue

            for principle in self.indexes[domain_name].principles:
                result.append(
                    {
                        "id": principle.id,
                        "domain": principle.domain,
                        "series": principle.series_code,
                        "number": principle.number,
                        "title": principle.title,
                    }
                )

        return result

    def get_principle_content(self, principle_id: str) -> str | None:
        """Get the full content of a principle from cache."""
        cache_path = self.config.cache_path / f"{principle_id}.md"
        if cache_path.exists():
            return cache_path.read_text()
        return None


def main():
    """Test retrieval engine."""
    import sys

    config = load_config()
    engine = RetrievalEngine(config)

    # Test query
    query = sys.argv[1] if len(sys.argv) > 1 else "specification seems incomplete"

    print(f"Query: {query}", file=sys.stderr)
    print(f"Detected domains: {engine.detect_domains(query)}", file=sys.stderr)

    result = engine.retrieve(query)

    print(f"\nS-Series triggered: {result.s_series_triggered}", file=sys.stderr)
    print(f"\nConstitution principles ({len(result.constitution_principles)}):", file=sys.stderr)
    for sp in result.constitution_principles[:3]:
        print(f"  [{sp.score:.1f}] {sp.principle.id}: {sp.principle.title}", file=sys.stderr)
        print(f"       Reasons: {sp.match_reasons[:3]}", file=sys.stderr)

    print(f"\nDomain principles ({len(result.domain_principles)}):", file=sys.stderr)
    for sp in result.domain_principles[:5]:
        print(f"  [{sp.score:.1f}] {sp.principle.id}: {sp.principle.title}", file=sys.stderr)


if __name__ == "__main__":
    main()
