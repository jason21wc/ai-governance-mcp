"""Tests for cross-reference validator + failure-mode-registry lint."""

import ast
import re
from pathlib import Path

import pytest
import yaml

from ai_governance_mcp.validator import (
    extract_constitution_principles,
    extract_derives_from_references,
    find_fuzzy_match,
    is_template_placeholder,
    normalize_principle_name,
    build_principle_index,
)


class TestExtractConstitutionPrinciples:
    """Tests for extracting principle names from constitution."""

    def test_extracts_h3_headings(self):
        content = """
### Context Engineering
**Definition**
Some content here.

### Single Source of Truth
**Definition**
More content.
"""
        principles = extract_constitution_principles(content)
        assert "Context Engineering" in principles
        assert "Single Source of Truth" in principles

    def test_excludes_non_principle_headings(self):
        content = """
### Framework Overview
Not a principle.

### Context Engineering
**Definition**
A real principle.

### How the AI Applies This
Content.
"""
        principles = extract_constitution_principles(content)
        assert "Context Engineering" in principles
        assert "Framework Overview" not in principles
        assert "How the AI Applies This" not in principles


class TestExtractDerivesFromReferences:
    """Tests for extracting 'Derives from' references."""

    def test_extracts_references_with_colon(self):
        content = "- Derives from **Context Engineering:** Some description"
        refs = extract_derives_from_references(content, "test.md")
        assert len(refs) == 1
        assert refs[0]["reference"] == "Context Engineering"
        assert refs[0]["file"] == "test.md"

    def test_extracts_multiple_references(self):
        content = """
- Derives from **Context Engineering:** Description 1
- Derives from **Single Source of Truth:** Description 2
"""
        refs = extract_derives_from_references(content, "test.md")
        assert len(refs) == 2

    def test_captures_line_numbers(self):
        content = "line 1\n- Derives from **Test:** desc\nline 3"
        refs = extract_derives_from_references(content, "test.md")
        assert refs[0]["line_number"] == 2


class TestIsTemplatePlaceholder:
    """Tests for template placeholder detection."""

    def test_detects_placeholder(self):
        assert is_template_placeholder("[Meta-Principle Full Name]")
        assert is_template_placeholder("[Something]")

    def test_rejects_non_placeholder(self):
        assert not is_template_placeholder("Context Engineering")
        assert not is_template_placeholder("[partial")
        assert not is_template_placeholder("partial]")


class TestNormalizePrincipleName:
    """Tests for principle name normalization."""

    def test_removes_meta_principle_prefix(self):
        assert (
            normalize_principle_name("Meta-Principle Context Engineering")
            == "context engineering"
        )

    def test_lowercases(self):
        assert normalize_principle_name("Context Engineering") == "context engineering"

    def test_normalizes_whitespace(self):
        assert (
            normalize_principle_name("Context   Engineering") == "context engineering"
        )


class TestFuzzyMatching:
    """Tests for fuzzy matching of principle references."""

    def test_exact_match(self):
        index = build_principle_index({"Context Engineering"})
        match = find_fuzzy_match("context engineering", index)
        assert match == "Context Engineering"

    def test_prefix_match(self):
        index = build_principle_index({"Verification Mechanisms Before Action"})
        match = find_fuzzy_match("verification mechanisms", index)
        assert match == "Verification Mechanisms Before Action"

    def test_abbreviation_map_match(self):
        index = build_principle_index({"Atomic Task Decomposition"})
        match = find_fuzzy_match("atomic decomposition", index)
        assert match == "Atomic Task Decomposition"

    def test_no_match_returns_none(self):
        index = build_principle_index({"Context Engineering"})
        match = find_fuzzy_match("completely different", index)
        assert match is None


class TestBuildPrincipleIndex:
    """Tests for principle index building."""

    def test_builds_normalized_index(self):
        principles = {"Context Engineering", "Single Source of Truth"}
        index = build_principle_index(principles)
        assert "context engineering" in index
        assert index["context engineering"] == "Context Engineering"


# ---------------------------------------------------------------------------
# Failure-mode registry lint (TestFailureModeCoverage)
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "documents" / "failure-mode-registry.md"
TESTS_DIR = PROJECT_ROOT / "tests"
_COVERS_RE = re.compile(r"Covers:\s*([A-Z][A-Z0-9_\-, ]+)", re.MULTILINE)


def _load_registry_entries() -> dict[str, dict]:
    """Parse YAML frontmatter from the failure-mode registry; return {id: entry}."""
    text = REGISTRY_PATH.read_text()
    assert text.startswith("---\n"), "registry missing YAML frontmatter"
    end = text.find("\n---\n", 4)
    assert end != -1, "registry YAML frontmatter unterminated"
    meta = yaml.safe_load(text[4:end]) or {}
    entries = meta.get("entries") or []
    return {e["id"]: e for e in entries if e.get("id")}


def _parse_covers(docstring: str | None) -> list[str]:
    """Extract FM-* IDs from a docstring's Covers: line(s)."""
    if not docstring:
        return []
    ids: list[str] = []
    for match in _COVERS_RE.finditer(docstring):
        for raw in match.group(1).split(","):
            ident = raw.strip().rstrip(".\"' \t")
            if ident and ident.startswith("FM-"):
                ids.append(ident)
    return ids


def _collect_annotations() -> list[tuple[str, str, list[str]]]:
    """Return list of (relative_file, test_qualname, [covered_ids]).

    Iterates top-level nodes only (mirrors scripts/generate-test-failure-map.py
    collect_annotations). Nested classes are NOT traversed — if the codebase
    grows to use `class TestA: class WhenB:` patterns, extend both this and
    the generator to avoid drift between lint and derived map.
    """
    annotations: list[tuple[str, str, list[str]]] = []
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        for top in tree.body:
            if isinstance(top, ast.ClassDef):
                for method in top.body:
                    if isinstance(
                        method, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ) and method.name.startswith("test_"):
                        ids = _parse_covers(ast.get_docstring(method))
                        if ids:
                            annotations.append((rel, f"{top.name}::{method.name}", ids))
            elif isinstance(
                top, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and top.name.startswith("test_"):
                ids = _parse_covers(ast.get_docstring(top))
                if ids:
                    annotations.append((rel, top.name, ids))
    return annotations


class TestFailureModeCoverage:
    """Failure-mode registry lint — ensures `Covers:` annotations stay honest.

    Prevents the class of bug where `Covers:` annotations turn into theatre:
    typos coin new "IDs" that lint-pattern-match but aren't in the registry,
    refactors rename IDs without updating annotations, must_cover entries drift
    into zero-coverage state without anyone noticing.

    Three checks:
    1. Every `Covers:` ID across tests/ must exist in the registry (unknown = fail).
    2. Every registry entry with must_cover: true must have ≥1 annotation (fail).
    3. Annotations citing retired entries emit a warning (not a failure — gives
       migration window).
    """

    @pytest.fixture(scope="class")
    def registry(self) -> dict[str, dict]:
        return _load_registry_entries()

    @pytest.fixture(scope="class")
    def annotations(self) -> list[tuple[str, str, list[str]]]:
        return _collect_annotations()

    def test_every_covers_id_exists_in_registry(self, registry, annotations):
        """Covers: IDs must resolve to a registry entry — no typos, no ghosts.

        Covers: FM-REGISTRY-UNKNOWN-ID-REJECTED
        """
        unknown: list[str] = []
        for rel, qualname, ids in annotations:
            for eid in ids:
                if eid not in registry:
                    unknown.append(f"{rel}::{qualname} cites unknown id {eid}")
        assert not unknown, (
            "tests cite failure-mode IDs that are not in "
            "documents/failure-mode-registry.md:\n  " + "\n  ".join(unknown)
        )

    def test_every_must_cover_entry_has_annotation(self, registry, annotations):
        """Every must_cover: true registry entry must have ≥1 annotated test.

        Covers: FM-REGISTRY-MUST-COVER-HAS-ANNOTATION
        """
        annotated_ids: set[str] = set()
        for _, _, ids in annotations:
            annotated_ids.update(ids)
        missing: list[str] = []
        for eid, entry in registry.items():
            if entry.get("must_cover") and not entry.get("retired"):
                if eid not in annotated_ids:
                    missing.append(f"{eid} — {entry.get('description', '')}")
        assert not missing, (
            "registry entries with must_cover: true have no annotated tests. "
            "Either add a test annotated with `Covers: <id>` in its docstring, "
            "or flip the entry to must_cover: false if coverage isn't required:\n  "
            + "\n  ".join(missing)
        )

    def test_retired_ids_emit_warning_only(self, registry, annotations, recwarn):
        """Annotations citing retired IDs produce deprecation warnings, not failures.

        Counts actual retired-id citations and asserts a matching number of
        DeprecationWarnings got raised. Without this assertion the test was
        a log statement, not a test (per 2nd-pass code-reviewer MEDIUM-3,
        session-123).
        """
        retired = {eid for eid, e in registry.items() if e.get("retired")}
        if not retired:
            pytest.skip("no retired registry entries yet — nothing to test")
        expected_citations = 0
        import warnings

        for rel, qualname, ids in annotations:
            for eid in ids:
                if eid in retired:
                    expected_citations += 1
                    warnings.warn(
                        f"{rel}::{qualname} cites retired id {eid} "
                        f"(retired {registry[eid].get('retired')})",
                        DeprecationWarning,
                        stacklevel=1,
                    )
        raised = [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)]
        assert len(raised) == expected_citations, (
            f"expected {expected_citations} DeprecationWarnings for retired-id "
            f"citations; got {len(raised)}"
        )

    def test_registry_yaml_parses(self, registry):
        """Registry YAML frontmatter must be valid and contain entries.

        Schema enforced:
        - id (implicit via key), description, must_cover, scope, introduced
        - must_cover is a real bool (not string "true")
        - scope is a string in {"framework", "project"}
        """
        assert registry, "registry has zero entries — check YAML frontmatter"
        valid_scopes = {"framework", "project"}
        for eid, entry in registry.items():
            assert entry.get("description"), f"{eid} missing description"
            assert "must_cover" in entry, f"{eid} missing must_cover field"
            # Must be a real bool — YAML `"true"` (string) is truthy but silently
            # wrong; explicit isinstance catches schema drift. (Per contrarian
            # MEDIUM-5, session-123.)
            assert isinstance(entry["must_cover"], bool), (
                f"{eid} must_cover must be bool, got {type(entry['must_cover']).__name__}"
            )
            # scope positions registry for scaffold-safe seeding (BACKLOG #125).
            assert "scope" in entry, f"{eid} missing scope field"
            assert isinstance(entry["scope"], str), (
                f"{eid} scope must be string, got {type(entry['scope']).__name__}"
            )
            assert entry["scope"] in valid_scopes, (
                f"{eid} scope must be one of {valid_scopes}, got {entry['scope']!r}"
            )
            assert entry.get("introduced"), f"{eid} missing introduced date"


# ---------------------------------------------------------------------------
# Demotion rationale gate (TestDemotionRationale) — BACKLOG #124
# ---------------------------------------------------------------------------

import subprocess  # noqa: E402

_RATIONALE_RE = re.compile(
    r"[Dd]emotion rationale:|BACKLOG\s*#\d+|[Rr]etired|[Ss]upersedes"
)
# Number of commits we know have touched the registry as of shipping date.
# Used by shallow-clone guard — if git log returns fewer than this, history
# is truncated and the gate would silently pass. Update when registry
# history grows significantly; under-count is safe (raises unnecessarily),
# over-count is unsafe (hides truncation).
_EXPECTED_MIN_HISTORY = 2


def _git_log_registry(format_spec: str = "%H") -> list[str]:
    """Run `git log --format=<spec> -- <registry>`. Return [] on any error."""
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                f"--format={format_spec}",
                "--",
                str(REGISTRY_PATH.relative_to(PROJECT_ROOT)),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _git_show_diff(commit_sha: str) -> str:
    """Run `git show -p <sha> -- <registry>`. Return '' on error."""
    try:
        result = subprocess.run(
            [
                "git",
                "show",
                "-p",
                commit_sha,
                "--",
                str(REGISTRY_PATH.relative_to(PROJECT_ROOT)),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""


def _commit_message(commit_sha: str) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%B", commit_sha],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""


class TestDemotionRationale:
    """Gate: must_cover: true → false demotion requires rationale in commit msg.

    Walks git history of documents/failure-mode-registry.md, detects each
    commit that flipped an entry from must_cover: true to must_cover: false,
    and requires the commit message to contain rationale regex:
        Demotion rationale: | BACKLOG #\\d+ | [Rr]etired | [Ss]upersedes

    Per BACKLOG #124 + session-123 2nd-pass contrarian HIGH: without this
    gate, the path of least resistance when `TestFailureModeCoverage::
    test_every_must_cover_entry_has_annotation` reddens is to flip the flag.
    One character, test passes. Registry signal decays.

    Shallow-clone guard (per contrarian a51939a6fa61a7dad BLOCKER): CI
    default checkout is depth=1; git log on shallow history returns
    truncated results → gate silently passes. Test RAISES (not skips) if
    history is below _EXPECTED_MIN_HISTORY commits; see `.github/workflows/
    ci.yml` for the matching `fetch-depth: 0` configuration.

    Legitimate skips (distinct from shallow-clone BLOCKER):
      - Registry file doesn't exist (pre-v1.0.0 checkpoint or fresh scaffold)
      - Not in a git repo (adopter test context outside git)
    """

    def _require_git_and_registry(self) -> None:
        if not REGISTRY_PATH.exists():
            pytest.skip("registry file does not exist — pre-v1.0.0 checkpoint?")
        # Detect "not in a git repo" by probing git status
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("git not available in this environment")
        if result.returncode != 0 or result.stdout.strip() != "true":
            pytest.skip("not in a git repo — adopter context outside VCS")

    def test_registry_history_fully_available(self):
        """Shallow-clone guard — raise (not skip) on ANY shallow repo.

        Uses `git rev-parse --is-shallow-repository` to detect shallow clones
        at ANY depth, not just depth<2. Per post-edit contrarian 2nd-pass
        a2e12e533e8038e09 (session-123): earlier _EXPECTED_MIN_HISTORY=2
        guard caught depth=1 but a depth=10 clone would return 10 commits
        (passing the min-2 assertion) while still truncating the demotion
        walk below — guarding presence, not completeness.

        Covers: FM-REGISTRY-MUST-COVER-HAS-ANNOTATION
        """
        self._require_git_and_registry()
        # Completeness check: fail on ANY shallow clone.
        try:
            is_shallow = subprocess.run(
                ["git", "rev-parse", "--is-shallow-repository"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("git rev-parse unavailable; repo probe failed")
        if is_shallow.returncode == 0 and is_shallow.stdout.strip() == "true":
            raise AssertionError(
                "Repository is a shallow clone — git log will truncate the "
                "demotion walk below this test and let demotions slip past. "
                "For CI: set `fetch-depth: 0` on actions/checkout. For local "
                "dev: run `git fetch --unshallow`. See .github/workflows/ci.yml."
            )
        # Belt-and-suspenders: also assert presence of at least N commits in
        # case `--is-shallow-repository` reports false on a truncated history
        # (unusual, but shallow detection varies by git version).
        commits = _git_log_registry()
        assert len(commits) >= _EXPECTED_MIN_HISTORY, (
            f"Registry git history has {len(commits)} commits; expected at "
            f"least {_EXPECTED_MIN_HISTORY}. Both shallow-detection and "
            f"min-count checks disagree with current state — investigate."
        )

    def test_demotions_cite_rationale(self):
        """Every must_cover: true→false flip in history must cite rationale.

        Rationale regex: Demotion rationale: | BACKLOG #N | Retired | Supersedes
        """
        self._require_git_and_registry()
        commits = _git_log_registry()
        if len(commits) < _EXPECTED_MIN_HISTORY:
            # Defense-in-depth — prior test asserts, but if that test is
            # somehow skipped, also skip here rather than report a false OK.
            pytest.skip("registry history truncated; shallow-clone guard asserts first")

        violations: list[str] = []
        for sha in commits:
            diff = _git_show_diff(sha)
            if not diff:
                continue
            # Detect `must_cover: true` → `must_cover: false` flip in this commit.
            # Pattern in unified diff: `-    must_cover: true` followed soon by
            # `+    must_cover: false` for the same entry. Simplest heuristic:
            # presence of both removal + addition lines.
            has_removed_true = "-    must_cover: true" in diff
            has_added_false = "+    must_cover: false" in diff
            if not (has_removed_true and has_added_false):
                continue
            # Flip detected — require rationale in commit message.
            msg = _commit_message(sha)
            if not _RATIONALE_RE.search(msg):
                violations.append(
                    f"{sha[:7]}: flips must_cover: true→false but commit "
                    f"message lacks rationale (regex: "
                    f"'Demotion rationale:|BACKLOG #N|Retired|Supersedes')"
                )

        assert not violations, (
            "Must-cover demotion(s) lack rationale. Per registry demotion-"
            "discipline rule: every `must_cover: true → false` flip must "
            "include rationale in the commit message or a BACKLOG pointer. "
            "Amend commits to add rationale, or reconsider the demotion:\n  "
            + "\n  ".join(violations)
        )
