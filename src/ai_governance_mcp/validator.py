"""Cross-reference validator for governance documents.

Validates that all "Derives from" references in domain principles
point to existing constitution (meta) principles.

Usage:
    python -m ai_governance_mcp.validator
"""

import json
import re
import sys
from collections import defaultdict

from .config import get_settings


def extract_constitution_principles(content: str) -> set[str]:
    """Extract principle names from constitution document.

    Looks for ### headings that define principles.
    """
    principles = set()

    # Match ### headers (principle definitions)
    # Exclude headers that are clearly not principles
    exclude_patterns = [
        "Framework Overview",
        "Design Philosophy",
        "Version History",
        "Document Governance",
        "Preamble",
        "How",
        "Why",
        "When",
        "Common Pitfalls",
        "Operational",
        "Net Impact",
        "Definition",
    ]

    for match in re.finditer(r"^### ([^\n]+)", content, re.MULTILINE):
        title = match.group(1).strip()
        # Skip excluded patterns
        if any(exc in title for exc in exclude_patterns):
            continue
        # Clean up the title (remove any trailing content after specific markers)
        title = re.split(r"\s*\(", title)[0].strip()
        if title:
            principles.add(title)

    return principles


def extract_derives_from_references(content: str, filename: str) -> list[dict]:
    """Extract all 'Derives from' references with context.

    Returns list of {reference, line_number, context}
    """
    references = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Match "Derives from **[Name]:**" or "Derives from **[Name]**"
        # The name may contain colons internally, so capture up to :** or **
        matches = re.findall(r"Derives from \*\*([^*]+?)(?::\*\*|\*\*)", line)
        for ref in matches:
            references.append(
                {
                    "reference": ref.strip(),
                    "line_number": i,
                    "file": filename,
                    "context": line.strip()[:100],
                }
            )

    return references


def normalize_principle_name(name: str) -> str:
    """Normalize principle name for matching.

    Handles variations like:
    - "Context Engineering" vs "Meta-Principle Context Engineering"
    - Extra whitespace
    - Case differences
    """
    # Remove common prefixes
    name = re.sub(r"^Meta-Principle\s+", "", name, flags=re.IGNORECASE)
    # Normalize whitespace
    name = " ".join(name.split())
    return name.lower()


def build_principle_index(principles: set[str]) -> dict[str, str]:
    """Build index mapping normalized names to original names."""
    index = {}
    for p in principles:
        normalized = normalize_principle_name(p)
        index[normalized] = p
    return index


def is_template_placeholder(ref: str) -> bool:
    """Check if reference is a template placeholder."""
    return ref.startswith("[") and ref.endswith("]")


def find_fuzzy_match(normalized: str, principle_index: dict[str, str]) -> str | None:
    """Try to find a fuzzy match for shortened principle names.

    Returns the matched principle name or None.
    """
    # Common abbreviation mappings (reference -> constitution name pattern)
    # These are intentional shortened names used in domain principles
    abbreviation_map = {
        "atomic decomposition": "atomic task decomposition",
        "fail-fast detection": "fail-fast validation",
        "iterative design": "iterative planning and delivery",
        "explicit intent": "explicit over implicit",
        "role segregation": "role specialization & topology",
        "handoff protocols": "standardized collaboration protocols",
        "constraint awareness": "constraint-based prompting",
        "testing": "verifiable outputs",
        "context optimization": "minimal relevant context",
    }

    # Check abbreviation map first
    if normalized in abbreviation_map:
        target = abbreviation_map[normalized]
        if target in principle_index:
            return principle_index[target]

    # Try prefix matching (e.g., "verification mechanisms" matches
    # "verification mechanisms before action")
    for norm_name, original in principle_index.items():
        if norm_name.startswith(normalized) or normalized.startswith(norm_name):
            return original
        # Also try if reference is a significant substring
        if len(normalized) >= 8 and normalized in norm_name:
            return original
        # Try word overlap for near-misses
        ref_words = set(normalized.split())
        principle_words = set(norm_name.split())
        # If 2+ words match and it's a majority of the reference words
        common = ref_words & principle_words
        if len(common) >= 2 and len(common) >= len(ref_words) * 0.6:
            return original

    return None


def validate_references(
    constitution_principles: set[str], domain_files: list[tuple[str, str]]
) -> dict:
    """Validate all cross-references.

    Args:
        constitution_principles: Set of principle names from constitution
        domain_files: List of (filename, content) tuples for domain docs

    Returns:
        Validation report dict
    """
    principle_index = build_principle_index(constitution_principles)

    all_references = []
    for filename, content in domain_files:
        refs = extract_derives_from_references(content, filename)
        all_references.extend(refs)

    # Validate each reference
    exact_matches = []
    fuzzy_matches = []
    invalid_refs = []
    skipped_templates = []
    reference_counts = defaultdict(int)

    for ref in all_references:
        # Skip template placeholders
        if is_template_placeholder(ref["reference"]):
            skipped_templates.append(ref)
            continue

        normalized = normalize_principle_name(ref["reference"])

        # Try exact match first
        if normalized in principle_index:
            exact_matches.append({**ref, "matched_to": principle_index[normalized]})
            reference_counts[principle_index[normalized]] += 1
        else:
            # Try fuzzy matching
            fuzzy = find_fuzzy_match(normalized, principle_index)
            if fuzzy:
                fuzzy_matches.append(
                    {**ref, "matched_to": fuzzy, "match_type": "fuzzy"}
                )
                reference_counts[fuzzy] += 1
            else:
                # No match found - report as invalid
                suggestions = [
                    p
                    for p in constitution_principles
                    if normalized in normalize_principle_name(p)
                    or normalize_principle_name(p) in normalized
                ]
                invalid_refs.append({**ref, "suggestions": suggestions[:3]})

    # Find orphan principles (no incoming references)
    referenced_principles = set(reference_counts.keys())
    orphan_principles = constitution_principles - referenced_principles

    return {
        "total_references": len(all_references),
        "exact_matches": len(exact_matches),
        "fuzzy_matches": len(fuzzy_matches),
        "fuzzy_match_details": fuzzy_matches,
        "invalid_references": len(invalid_refs),
        "invalid_details": invalid_refs,
        "skipped_templates": len(skipped_templates),
        "orphan_principles": sorted(orphan_principles),
        "reference_counts": dict(
            sorted(reference_counts.items(), key=lambda x: x[1], reverse=True)
        ),
        "constitution_principle_count": len(constitution_principles),
    }


def run_validation() -> dict:
    """Run full validation on governance documents."""
    settings = get_settings()
    docs_path = settings.documents_path

    # Load domains.json to find files
    domains_file = docs_path / "domains.json"
    if not domains_file.exists():
        return {"error": f"domains.json not found at {domains_file}"}

    with open(domains_file) as f:
        domains = json.load(f)

    # Find constitution file
    constitution_config = domains.get("constitution", {})
    constitution_file = docs_path / constitution_config.get("principles_file", "")

    if not constitution_file.exists():
        return {"error": f"Constitution file not found: {constitution_file}"}

    # Extract constitution principles
    constitution_content = constitution_file.read_text()
    constitution_principles = extract_constitution_principles(constitution_content)

    # Load domain principle files
    domain_files = []
    for domain_name, config in domains.items():
        if domain_name == "constitution":
            continue
        principles_file = docs_path / config.get("principles_file", "")
        if principles_file.exists():
            domain_files.append(
                (config["principles_file"], principles_file.read_text())
            )

    # Run validation
    return validate_references(constitution_principles, domain_files)


def print_report(report: dict) -> None:
    """Print validation report to stderr."""
    if "error" in report:
        print(f"ERROR: {report['error']}", file=sys.stderr)
        return

    print("\n" + "=" * 60, file=sys.stderr)
    print("CROSS-REFERENCE VALIDATION REPORT", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    print(
        f"\nConstitution Principles: {report['constitution_principle_count']}",
        file=sys.stderr,
    )
    print(f"Total References Found: {report['total_references']}", file=sys.stderr)
    print(f"  Exact Matches: {report['exact_matches']}", file=sys.stderr)
    print(f"  Fuzzy Matches: {report['fuzzy_matches']}", file=sys.stderr)
    print(f"  Skipped (templates): {report['skipped_templates']}", file=sys.stderr)
    print(f"  Invalid: {report['invalid_references']}", file=sys.stderr)

    if report["invalid_details"]:
        print("\n" + "-" * 40, file=sys.stderr)
        print("INVALID REFERENCES (need attention):", file=sys.stderr)
        print("-" * 40, file=sys.stderr)
        for ref in report["invalid_details"]:
            print(f"\n  File: {ref['file']}:{ref['line_number']}", file=sys.stderr)
            print(f'  Reference: "{ref["reference"]}"', file=sys.stderr)
            if ref["suggestions"]:
                print(f"  Did you mean: {ref['suggestions']}", file=sys.stderr)

    if report["fuzzy_match_details"]:
        print("\n" + "-" * 40, file=sys.stderr)
        print("FUZZY MATCHES (shortened names accepted):", file=sys.stderr)
        print("-" * 40, file=sys.stderr)
        shown = set()
        for ref in report["fuzzy_match_details"]:
            key = (ref["reference"], ref["matched_to"])
            if key not in shown:
                print(
                    f'  "{ref["reference"]}" → "{ref["matched_to"]}"', file=sys.stderr
                )
                shown.add(key)

    if report["orphan_principles"]:
        print("\n" + "-" * 40, file=sys.stderr)
        print("ORPHAN PRINCIPLES (no incoming references):", file=sys.stderr)
        print("-" * 40, file=sys.stderr)
        for p in report["orphan_principles"]:
            print(f"  - {p}", file=sys.stderr)

    print("\n" + "-" * 40, file=sys.stderr)
    print("REFERENCE FREQUENCY (top 10):", file=sys.stderr)
    print("-" * 40, file=sys.stderr)
    for principle, count in list(report["reference_counts"].items())[:10]:
        print(f"  {count:3d}x  {principle}", file=sys.stderr)

    print("\n" + "=" * 60, file=sys.stderr)
    if report["invalid_references"] == 0:
        print("✓ All cross-references are valid!", file=sys.stderr)
    else:
        print(
            f"✗ {report['invalid_references']} invalid reference(s) found",
            file=sys.stderr,
        )
    print("=" * 60 + "\n", file=sys.stderr)


def main():
    """CLI entry point."""
    report = run_validation()
    print_report(report)

    # Return non-zero exit code if invalid references found
    if report.get("invalid_references", 0) > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
