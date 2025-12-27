"""Document extractor for AI Governance documents.

Parses governance markdown documents and extracts principles with expanded metadata.
Per specification v3 §4: Extraction enables ~5% miss rate via expanded keywords.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import ServerConfig, load_config, load_domains_registry, setup_logging
from .models import DomainConfig, DomainIndex, Method, Principle, PrincipleMetadata

logger = setup_logging()


# Expanded keyword mappings per specification v3 §3.2.1
EXPANDED_METADATA = {
    # Constitution series
    "C": {  # Core Architecture
        "keywords": ["context", "information", "knowledge", "data", "state"],
        "synonyms": ["context", "info", "knowledge-base", "background"],
        "phrases": ["need context", "load context", "missing information"],
        "failure_indicators": ["hallucinating", "made up", "invented", "assumed"],
    },
    "Q": {  # Quality
        "keywords": ["quality", "verification", "validation", "testing", "evidence"],
        "synonyms": ["verify", "validate", "test", "check", "confirm"],
        "phrases": ["ensure quality", "run tests", "validate output"],
        "failure_indicators": ["untested", "unverified", "no evidence", "broke"],
    },
    "O": {  # Operational
        "keywords": ["efficiency", "performance", "optimization", "resources"],
        "synonyms": ["optimize", "efficient", "performant", "fast"],
        "phrases": ["improve performance", "optimize code"],
        "failure_indicators": ["slow", "inefficient", "resource-heavy"],
    },
    "MA": {  # Multi-Agent / Collaborative
        "keywords": ["agent", "collaboration", "handoff", "coordination", "role"],
        "synonyms": ["agents", "collaborate", "coordinate", "delegate"],
        "phrases": ["multiple agents", "agent handoff", "agent communication"],
        "failure_indicators": ["agent conflict", "coordination failure", "lost handoff"],
    },
    "G": {  # Governance
        "keywords": ["documentation", "governance", "feedback", "evolution"],
        "synonyms": ["document", "record", "log", "track"],
        "phrases": ["document decision", "maintain records"],
        "failure_indicators": ["undocumented", "no record", "lost history"],
    },
    "S": {  # Safety (Bill of Rights)
        "keywords": ["safety", "security", "privacy", "ethics", "harm"],
        "synonyms": ["safe", "secure", "private", "ethical"],
        "phrases": [
            "prevent harm",
            "protect privacy",
            "security concern",
            "ethical issue",
            "safety violation",
        ],
        "failure_indicators": [
            "vulnerability",
            "breach",
            "leak",
            "exposed",
            "harmful",
            "malicious",
            "injection",
        ],
    },
    # Domain-specific series (AI Coding)
    "P": {  # Process
        "keywords": ["process", "workflow", "phase", "gate", "validation"],
        "synonyms": ["workflow", "pipeline", "procedure", "step"],
        "phrases": ["validation gate", "phase complete", "process flow"],
        "failure_indicators": ["skipped validation", "bypassed gate", "out of order"],
    },
    # Multi-Agent domain series
    "A": {  # Architecture (multi-agent)
        "keywords": ["architecture", "design", "structure", "pattern"],
        "synonyms": ["design", "structure", "layout", "framework"],
        "phrases": ["agent architecture", "system design"],
        "failure_indicators": ["bad architecture", "poor design", "structural issue"],
    },
    "T": {  # Trust
        "keywords": ["trust", "verification", "authentication", "authorization"],
        "synonyms": ["verify", "authenticate", "authorize", "validate"],
        "phrases": ["verify agent", "trust boundary", "authenticate request"],
        "failure_indicators": ["untrusted", "unauthorized", "unauthenticated"],
    },
    "D": {  # Delegation
        "keywords": ["delegation", "assignment", "task", "responsibility"],
        "synonyms": ["delegate", "assign", "distribute", "allocate"],
        "phrases": ["delegate task", "assign work", "distribute responsibility"],
        "failure_indicators": ["unclear delegation", "overlapping responsibility"],
    },
}


# Principle-specific keyword overrides
PRINCIPLE_KEYWORDS = {
    # Constitution
    "meta-C1": {
        "keywords": ["context", "information", "requirements", "specifications"],
        "synonyms": ["specs", "reqs", "background", "prior knowledge"],
        "phrases": ["need context", "load context", "missing requirements"],
        "failure_indicators": ["hallucinating", "making things up", "no context"],
    },
    "meta-S1": {
        "keywords": ["harm", "safety", "damage", "risk"],
        "synonyms": ["harmful", "dangerous", "risky", "unsafe"],
        "phrases": ["prevent harm", "safety concern", "risk assessment"],
        "failure_indicators": ["causing harm", "unsafe", "dangerous"],
    },
    "meta-S2": {
        "keywords": ["privacy", "data", "personal", "confidential"],
        "synonyms": ["private", "sensitive", "pii", "secret"],
        "phrases": ["protect privacy", "handle data", "sensitive information"],
        "failure_indicators": ["privacy breach", "data leak", "exposed pii"],
    },
    "meta-S3": {
        "keywords": ["deception", "honesty", "truth", "transparency"],
        "synonyms": ["honest", "truthful", "transparent", "candid"],
        "phrases": ["be honest", "tell truth", "transparent about"],
        "failure_indicators": ["deceiving", "lying", "misleading", "hiding"],
    },
    # AI Coding Domain
    "coding-C1": {
        "keywords": ["specification", "requirements", "specs", "complete"],
        "synonyms": ["reqs", "requirements doc", "spec doc", "acceptance criteria"],
        "phrases": [
            "specs incomplete",
            "missing requirements",
            "need specifications",
            "undefined behavior",
        ],
        "failure_indicators": [
            "hallucination",
            "guessing",
            "assuming",
            "invented requirement",
        ],
    },
    "coding-C2": {
        "keywords": ["context", "window", "tokens", "overflow"],
        "synonyms": ["token limit", "context limit", "memory", "conversation length"],
        "phrases": ["context too long", "running out of context", "token overflow"],
        "failure_indicators": ["context overflow", "forgot earlier", "lost context"],
    },
    "coding-C3": {
        "keywords": ["session", "state", "continuity", "persistence"],
        "synonyms": ["memory", "remember", "previous session", "state file"],
        "phrases": ["between sessions", "remember context", "persist state"],
        "failure_indicators": ["forgot", "lost state", "no memory", "starting fresh"],
    },
    "coding-P1": {
        "keywords": ["phase", "sequence", "order", "dependencies"],
        "synonyms": ["workflow", "phases", "steps", "stages"],
        "phrases": ["phase order", "complete before", "prerequisite phase"],
        "failure_indicators": ["skipped phase", "out of order", "jumped ahead"],
    },
    "coding-P2": {
        "keywords": ["validation", "gate", "checkpoint", "approval"],
        "synonyms": ["verify", "check", "review", "approve"],
        "phrases": ["validation gate", "pass gate", "gate check"],
        "failure_indicators": ["skipped validation", "bypassed gate", "no review"],
    },
    "coding-P3": {
        "keywords": ["atomic", "task", "decomposition", "small"],
        "synonyms": ["chunk", "piece", "unit", "module"],
        "phrases": ["break down", "smaller tasks", "atomic unit"],
        "failure_indicators": ["too large", "hard to review", "complex task"],
    },
    "coding-P4": {
        "keywords": ["human", "collaboration", "decision", "oversight"],
        "synonyms": ["product owner", "user", "stakeholder", "reviewer"],
        "phrases": ["human decision", "product decision", "need approval"],
        "failure_indicators": ["ai decided", "no human input", "automation bias"],
    },
    "coding-Q1": {
        "keywords": ["production", "ready", "deployable", "complete"],
        "synonyms": ["prod-ready", "ship", "deploy", "release"],
        "phrases": ["production ready", "ready to deploy", "complete implementation"],
        "failure_indicators": ["not production ready", "incomplete", "technical debt"],
    },
    "coding-Q2": {
        "keywords": ["security", "vulnerability", "secure", "safe"],
        "synonyms": ["sec", "vuln", "exploit", "attack"],
        "phrases": ["security check", "vulnerability scan", "secure code"],
        "failure_indicators": ["vulnerability", "insecure", "exploit", "injection"],
    },
    "coding-Q3": {
        "keywords": ["testing", "tests", "coverage", "unit"],
        "synonyms": ["test", "unit test", "integration test", "coverage"],
        "phrases": ["run tests", "test coverage", "write tests"],
        "failure_indicators": ["no tests", "untested", "failing tests", "low coverage"],
    },
    "coding-Q4": {
        "keywords": ["dependency", "package", "supply chain", "verify"],
        "synonyms": ["dep", "lib", "library", "npm", "pypi"],
        "phrases": ["verify package", "check dependency", "supply chain"],
        "failure_indicators": ["hallucinated package", "fake dependency", "malicious package"],
    },
    "coding-Q5": {
        "keywords": ["workflow", "integrity", "injection", "adversarial"],
        "synonyms": ["prompt injection", "manipulation", "attack"],
        "phrases": ["prompt injection", "workflow attack", "adversarial input"],
        "failure_indicators": ["injected", "manipulated", "adversarial", "compromised"],
    },
}


class DocumentExtractor:
    """Extracts principles and methods from governance markdown documents."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.domains = load_domains_registry(config)

    def extract_all(self) -> dict[str, DomainIndex]:
        """Extract all domains and return indexes."""
        indexes: dict[str, DomainIndex] = {}

        for domain_name, domain_config in self.domains.items():
            logger.info(f"Extracting domain: {domain_name}")
            index = self._extract_domain(domain_config)
            indexes[domain_name] = index

            # Save index to file
            self._save_index(domain_name, index)

        return indexes

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
        )

    def _extract_principles(self, domain_config: DomainConfig) -> list[Principle]:
        """Extract principles from a domain's principles file."""
        file_path = self.config.documents_path / domain_config.principles_file
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
        start_line = 0

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
                start_line = i

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
        """Build a Principle object with expanded metadata."""
        principle_id = f"{domain_prefix}-{data['series_code']}{data['number']}"

        # Get metadata from principle-specific overrides or series defaults
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
        )

    def _generate_metadata(
        self, principle_id: str, series_code: str, title: str, content: str
    ) -> PrincipleMetadata:
        """Generate expanded metadata for a principle."""
        # Start with principle-specific overrides if available
        if principle_id in PRINCIPLE_KEYWORDS:
            specific = PRINCIPLE_KEYWORDS[principle_id]
            return PrincipleMetadata(
                keywords=specific.get("keywords", []),
                synonyms=specific.get("synonyms", []),
                trigger_phrases=specific.get("phrases", []),
                failure_indicators=specific.get("failure_indicators", []),
                aliases=[principle_id.split("-")[-1]],  # e.g., "C1"
            )

        # Fall back to series-based defaults
        series_meta = EXPANDED_METADATA.get(series_code, {})

        # Extract keywords from title
        title_words = [w.lower() for w in title.split() if len(w) > 3]

        # Extract failure indicators from content (look for "Failure Mode" sections)
        failure_indicators = series_meta.get("failure_indicators", [])[:]
        failure_match = re.search(
            r"\*\*(?:Failure Mode|Common Pitfalls)[^*]*\*\*[:\s]*(.+?)(?:\n\n|\*\*)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if failure_match:
            # Extract key phrases from failure mode text
            failure_text = failure_match.group(1)
            failure_words = [
                w.lower()
                for w in re.findall(r"\b[a-z]{4,}\b", failure_text.lower())
                if w not in ("this", "that", "with", "from", "have", "been", "will")
            ]
            failure_indicators.extend(failure_words[:5])

        return PrincipleMetadata(
            keywords=list(set(series_meta.get("keywords", []) + title_words)),
            synonyms=series_meta.get("synonyms", []),
            trigger_phrases=series_meta.get("phrases", []),
            failure_indicators=list(set(failure_indicators)),
            aliases=[f"{series_code}{principle_id.split(series_code)[-1]}"],
        )

    def _extract_methods(self, domain_config: DomainConfig) -> list[Method]:
        """Extract methods from a domain's methods file."""
        file_path = self.config.documents_path / domain_config.methods_file
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
                # Save previous method
                if current_method:
                    current_method["end_line"] = i - 1
                    current_method["content"] = "\n".join(
                        lines[current_method["start_line"] - 1 : i - 1]
                    )
                    methods.append(self._build_method(current_method, domain_prefix, method_count))
                    method_count += 1

                # Start new method
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

        # Save last method
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

        # Extract keywords from title
        keywords = [w.lower() for w in data["title"].split() if len(w) > 3]

        return Method(
            id=method_id,
            domain=data["domain"],
            title=data["title"],
            content=data["content"],
            line_range=(data["start_line"], data["end_line"]),
            keywords=keywords,
        )

    def _get_domain_prefix(self, domain_name: str) -> str:
        """Get the prefix for principle IDs based on domain."""
        prefixes = {
            "constitution": "meta",
            "ai-coding": "coding",
            "multi-agent": "multi",
        }
        return prefixes.get(domain_name, domain_name[:4])

    def _save_index(self, domain_name: str, index: DomainIndex) -> None:
        """Save domain index to JSON file."""
        self.config.index_path.mkdir(parents=True, exist_ok=True)
        index_file = self.config.index_path / f"{domain_name}-index.json"

        with open(index_file, "w") as f:
            json.dump(index.model_dump(), f, indent=2)

        logger.info(f"Saved index to {index_file}")

        # Also save individual principle caches
        self._save_principle_caches(domain_name, index.principles)

    def _save_principle_caches(self, domain_name: str, principles: list[Principle]) -> None:
        """Save individual principle content to cache files."""
        self.config.cache_path.mkdir(parents=True, exist_ok=True)

        for principle in principles:
            cache_file = self.config.cache_path / f"{principle.id}.md"
            cache_file.write_text(principle.content)


def main():
    """CLI entry point for extraction."""
    config = load_config()

    # Override documents path if provided
    if len(sys.argv) > 1:
        config.documents_path = Path(sys.argv[1])

    logger.info(f"Extracting documents from: {config.documents_path}")

    extractor = DocumentExtractor(config)
    indexes = extractor.extract_all()

    # Print summary
    print(f"\nExtraction complete:", file=sys.stderr)
    for domain_name, index in indexes.items():
        print(
            f"  {domain_name}: {len(index.principles)} principles, {len(index.methods)} methods",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
