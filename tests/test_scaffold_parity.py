"""Parity tests for scaffold_project output vs framework's own published kit.

Closes F-C-03 (Cohort 5 Session 5-2, v5.0.6).

Source of truth: `documents/title-10-ai-coding-cfr.md` §1.5.2 Standard Kit
enumeration — the CFR's published list of required files for Standard-tier
projects. NOT adopter CLAUDE.md (which is tool-specific overlay per §1.5.5).

Design:
- Parse §1.5.2 Standard Kit table at test runtime (auto-updates when CFR
  changes; no hardcoded file list to drift)
- Compare against `SCAFFOLD_STANDARD_EXTRAS["code"]` output
- Bidirectional assertion: scaffold standard-extras = §1.5.2 kit exactly
  (v2.63.0: the tool overlays CLAUDE.md/GEMINI.md moved to the core kit, so
  no overlay carve-out remains in the standard tier — _OVERLAY_FILES is empty)

Re-evaluation trigger: if CFR §1.5.2 changes format (e.g., moves from a
markdown table to prose), this test's parser will fail loudly — update the
parser, do not silently pin to a hardcoded list.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from ai_governance_mcp.server import (
    SCAFFOLD_SAAS_OPS_EXTRAS,
    SCAFFOLD_STANDARD_EXTRAS,
)
from tests.memory_policy_helpers import (
    assert_declared_type,
    assert_header_line_claims,
    assert_lifecycle,
    canonical_line_triggers,
    canonical_types,
    declared_field,
)

# As of v2.63.0 the tool-overlay loaders (CLAUDE.md, GEMINI.md) live in the CORE
# kit, not standard extras, so SCAFFOLD_STANDARD_EXTRAS["code"] equals the §1.5.2
# Standard Kit exactly — no overlay carve-out remains in the standard-tier parity.
_OVERLAY_FILES = frozenset()


def _cfr_path() -> Path:
    """Locate the AI Coding CFR document."""
    return (
        Path(__file__).resolve().parent.parent
        / "documents"
        / "title-10-ai-coding-cfr.md"
    )


def _parse_standard_kit_files() -> list[str]:
    """Parse CFR §1.5.2 Standard Kit table, returning the file list.

    Returns the `Additional File` column values from the markdown table under
    the §1.5.2 heading, preserving order. If the CFR structure changes such
    that the parser can't locate the section or table, raises explicitly —
    silent failure would hide drift.
    """
    content = _cfr_path().read_text()
    section_match = re.search(
        r"^### 1\.5\.2 Standard Kit.*?(?=^### 1\.5\.3)",
        content,
        re.DOTALL | re.MULTILINE,
    )
    if not section_match:
        raise RuntimeError(
            "Could not locate §1.5.2 Standard Kit section in CFR. "
            "Parser expects heading `### 1.5.2 Standard Kit` followed by "
            "content up to `### 1.5.3`. Update parser if CFR structure changed."
        )
    section = section_match.group(0)
    files: list[str] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        first = cells[0]
        if first and not first.startswith("-") and first != "Additional File":
            files.append(first)
    if not files:
        raise RuntimeError(
            "Parsed §1.5.2 Standard Kit section but found zero file entries. "
            "Table structure may have changed; update parser."
        )
    return files


def _scaffold_code_files() -> list[str]:
    """Return the filenames SCAFFOLD_STANDARD_EXTRAS produces for code projects."""
    return [name for (name, _content) in SCAFFOLD_STANDARD_EXTRAS["code"]]


class TestScaffoldParityWithCFR152:
    """F-C-03: scaffold_project output must match CFR §1.5.2 Standard Kit."""

    def test_cfr_152_parser_finds_files(self) -> None:
        """Parser successfully extracts file list from CFR §1.5.2."""
        files = _parse_standard_kit_files()
        assert files, "CFR §1.5.2 Standard Kit parse returned empty list"
        # Sanity check: Standard Kit currently has 5 files (per §1.5.2 text
        # "Total: 9 files = 4 core + 5 standard additions"). Failing here means
        # either the CFR changed intentionally (update expected count or
        # remove this assertion) or the parser drifted.
        assert len(files) == 5, (
            f"Expected 5 files in §1.5.2 Standard Kit table, got {len(files)}: {files}"
        )

    def test_scaffold_covers_cfr_152_kit(self) -> None:
        """Every file in CFR §1.5.2 Standard Kit is produced by scaffold (superset)."""
        cfr_kit = set(_parse_standard_kit_files())
        scaffold = set(_scaffold_code_files())
        missing = cfr_kit - scaffold
        assert not missing, (
            f"Scaffold is missing files from CFR §1.5.2 Standard Kit: {missing}. "
            f"Scaffold emits: {sorted(scaffold)}. "
            f"CFR §1.5.2 requires: {sorted(cfr_kit)}."
        )

    def test_scaffold_has_no_extra_files_beyond_overlay(self) -> None:
        """Scaffold emits nothing beyond §1.5.2 + approved overlays (subset)."""
        cfr_kit = set(_parse_standard_kit_files())
        scaffold = set(_scaffold_code_files())
        extras = scaffold - cfr_kit - _OVERLAY_FILES
        assert not extras, (
            f"Scaffold emits files not in CFR §1.5.2 and not an approved "
            f"overlay: {extras}. Either add the file to §1.5.2 (if it "
            f"should be kit-standard) or to _OVERLAY_FILES in this test "
            f"(if it's a documented §1.5.5 tool overlay). As of v2.63.0 the tool "
            f"overlays CLAUDE.md/GEMINI.md are core-kit loaders, so _OVERLAY_FILES "
            f"is empty and standard-extras equal §1.5.2 exactly."
        )

    def test_scaffold_parity_is_bidirectional(self) -> None:
        """Bidirectional assertion: scaffold = §1.5.2 kit + approved overlays.

        Equivalent to test_scaffold_covers_cfr_152_kit +
        test_scaffold_has_no_extra_files_beyond_overlay combined. Kept as a
        distinct test so a single assertion documents the full invariant.

        Covers: FM-TEST-ECHO-CHAMBER
        """
        cfr_kit = set(_parse_standard_kit_files())
        scaffold = set(_scaffold_code_files())
        expected = cfr_kit | _OVERLAY_FILES
        assert scaffold == expected, (
            f"Scaffold/CFR §1.5.2 parity violated.\n"
            f"  Scaffold output:  {sorted(scaffold)}\n"
            f"  Expected (CFR §1.5.2 + overlays): {sorted(expected)}\n"
            f"  Missing from scaffold: {expected - scaffold}\n"
            f"  Extra in scaffold:     {scaffold - expected}"
        )


class TestSaasOpsTierIsSeparateKitKey:
    """BACKLOG #71 Phase C2: the saas-ops tier must be a SEPARATE kit key.

    Per the bidirectional parity invariant above, SCAFFOLD_STANDARD_EXTRAS is
    pinned to CFR §1.5.2 (Standard Kit) exactly (the tool overlays CLAUDE.md/
    GEMINI.md moved to the core kit in v2.63.0). The per-app
    SaaS-ops SOP is saas-ops-specific, NOT a universal standard-kit file, so it
    lives in its own constant (SCAFFOLD_SAAS_OPS_EXTRAS) — never folded into
    standard. Same constraint as sibling BACKLOG #65 (evals tier).
    """

    _SOP_FILE = "SAAS-OPS-SOP.md"

    def test_sop_in_saas_ops_extras(self) -> None:
        """The SOP file is emitted by the saas-ops kit key (code projects)."""
        names = [name for (name, _content) in SCAFFOLD_SAAS_OPS_EXTRAS["code"]]
        assert self._SOP_FILE in names, (
            f"{self._SOP_FILE} not in SCAFFOLD_SAAS_OPS_EXTRAS['code']: {names}"
        )

    def test_sop_not_in_standard_extras(self) -> None:
        """The SOP file must NOT leak into the standard kit (separate-key invariant)."""
        standard = [name for (name, _content) in SCAFFOLD_STANDARD_EXTRAS["code"]]
        assert self._SOP_FILE not in standard, (
            f"{self._SOP_FILE} leaked into SCAFFOLD_STANDARD_EXTRAS — this breaks the "
            f"§1.5.2 parity invariant. Keep it in SCAFFOLD_SAAS_OPS_EXTRAS only. "
            f"Standard emits: {standard}"
        )

    def test_saas_ops_document_has_no_extras(self) -> None:
        """saas-ops is code-only — the SOP key stays empty for document projects.

        (Document projects DO have standard extras since session-243 — BACKLOG.md —
        but those live in SCAFFOLD_STANDARD_EXTRAS, not this key.)"""
        assert SCAFFOLD_SAAS_OPS_EXTRAS["document"] == []


class TestDocumentTierExtras:
    """Document-tier standard extras pin (session-243 neutral-kit design).

    Unlike the code tier (live-parsed from the §1.5.2 table above), the document
    tier is pinned by a hardcoded list: the CFR states it as a PROSE sentence
    immediately after the §1.5.2 table ("For document projects, standard adds
    `_ai-context/BACKLOG.md` and `_ai-context/OPERATIONS.md`"), because any
    `|`-prefixed line in that
    section would be slurped by _parse_standard_kit_files as a code-kit row.
    If you change this list, update that §1.5.2 prose sentence (and vice
    versa) — the CFR sentence carries a matching cross-link comment.
    """

    def test_document_standard_extras_pinned(self) -> None:
        names = [name for (name, _content) in SCAFFOLD_STANDARD_EXTRAS["document"]]
        assert names == ["_ai-context/BACKLOG.md", "_ai-context/OPERATIONS.md"], (
            f"Document standard extras drifted from the §1.5.2 prose pin: {names}. "
            "Update documents/title-10-ai-coding-cfr.md §1.5.2 document-tier "
            "sentence in the same change."
        )


class TestLoaderNamesEveryMemoryFileTheKitCreates:
    """A memory file the loader never names is a file the AI never opens.

    This is not hypothetical. `SCAFFOLD_AGENTS_MD` listed only the three CORE
    memory files, while `_ai-context/BACKLOG.md` has been a STANDARD extra the
    whole time — so every standard-kit project got a prospective-memory file that
    nothing instructed the AI to read. It went unnoticed because the two lists
    live in different constants and no test compared them.

    The repo's own precedent decides the shape (see the header of
    tests/test_memory_enumerations.py): keep the template LITERAL and let a test
    scan and fail loudly, rather than deriving the list at runtime. A template is
    prose an adopter edits by hand; deriving it would fight that.
    """

    def _memory_files_for(self, project_type: str) -> list[str]:
        from ai_governance_mcp.server._constants import (
            SCAFFOLD_CORE_FILES,
            SCAFFOLD_STANDARD_EXTRAS,
        )

        names = [n for (n, _c) in SCAFFOLD_CORE_FILES[project_type]]
        names += [n for (n, _c) in SCAFFOLD_STANDARD_EXTRAS[project_type]]
        return [n for n in names if n.startswith("_ai-context/") and n.endswith(".md")]

    def test_agents_md_names_every_code_memory_file(self) -> None:
        from ai_governance_mcp.server._constants import SCAFFOLD_AGENTS_MD

        missing = [
            f
            for f in self._memory_files_for("code")
            if f.rsplit("/", 1)[-1] not in SCAFFOLD_AGENTS_MD
        ]
        assert not missing, (
            f"AGENTS.md never names {missing}. A scaffolded project would create "
            "those files and no instruction would tell the AI to read them."
        )

    def test_ai_context_readme_names_every_document_memory_file(self) -> None:
        from ai_governance_mcp.server._constants import SCAFFOLD_AI_CONTEXT_README

        missing = [
            f
            for f in self._memory_files_for("document")
            if f.rsplit("/", 1)[-1] not in SCAFFOLD_AI_CONTEXT_README
            and f != "_ai-context/README.md"
        ]
        assert not missing, (
            f"The _ai-context README never names {missing}. For a document project "
            "that README is the only loader there is."
        )


def test_every_scaffolded_memory_template_declares_a_canonical_type() -> None:
    """A scaffolded memory file must say what it is, in the file itself.

    The three CORE templates carried `**Memory Type:**` from the start; the
    standard-tier ones (BACKLOG, and OPERATIONS when it was added) did not. Same
    tier-boundary blind spot as the loader omission above — whatever was true of
    the core kit was assumed to be true of the whole kit.

    This header is the portability surface. It is plain markdown at the top of the
    file, so an agent in Codex, ChatGPT, Gemini, or a bare editor learns the file's
    cognitive type and lifecycle from the file itself, with no MCP server, no
    loader, and no framework tooling. Every other mechanism here is Claude-shaped;
    this one is not, which is exactly why it must not be optional.

    Ground truth is CFR §7.0.2's table, parsed live — not a second hardcoded list.
    """
    # Keep private-source assertions in this existing public-deselected node;
    # pure policy/parser fixtures below still execute in the public build.
    policy = _cfr_path().read_text()
    canonical = canonical_types(policy)
    triggers = canonical_line_triggers(policy)
    for label, stem, content in _memory_templates():
        assert_declared_type(stem + ".md", content, canonical)
        assert_header_line_claims(stem + ".md", content, triggers)


def _memory_templates() -> list[tuple[str, str, str]]:
    """(label, filename-stem, content) for every scaffolded memory template."""
    from ai_governance_mcp.server._constants import (
        SCAFFOLD_CORE_FILES,
        SCAFFOLD_STANDARD_EXTRAS,
    )

    out = []
    for project_type in ("code", "document"):
        pairs = list(SCAFFOLD_CORE_FILES[project_type]) + list(
            SCAFFOLD_STANDARD_EXTRAS[project_type]
        )
        for name, content in pairs:
            if not name.startswith("_ai-context/") or name.endswith("README.md"):
                continue
            stem = name.rsplit("/", 1)[-1][: -len(".md")]
            out.append((f"{project_type}:{stem}", stem, content))
    return out


def test_scaffolded_memory_templates_meet_the_header_contract() -> None:
    """CFR Appendix B.0, applied to what ADOPTERS actually receive.

    The repo's own memory files satisfied all three fields while the templates
    that create other people's did not — this repo had learned something its
    scaffold never received. Both PROJECT-MEMORY templates stated what they hold
    and never what they do not, which to a cold agent reads as "put anything
    uncertain here": exactly how a semantic file becomes a dumping ground.

    Header region is the first 40 lines, per Appendix B.0 — not "before the first
    `---`", which would fail BACKLOG.md, a compliant file.
    """
    # Derived, not hand-typed, and scoped PER PROJECT TYPE (Codex round 2): a
    # document project must not satisfy routing by naming a file only the code kit
    # creates. ARCHITECTURE was in the hand-typed version and is NOT memory
    # (EXECUTION-FRAMEWORK §6.4 classes it as reference) — that is what let a header
    # routing only to ARCHITECTURE.md pass a memory-sibling contract.
    by_type: dict[str, set[str]] = {}
    for label, stem, _c in _memory_templates():
        by_type.setdefault(label.split(":", 1)[0], set()).add(stem)
    offenders = []
    for label, stem, content in _memory_templates():
        # Table rows excluded here too (Codex round 2): the repo-side guard was
        # passing on incidental words inside a decisions table, and the template
        # side would drift into the same false pass. Routing is prose, not a cell.
        header = "\n".join(
            ln for ln in content.splitlines()[:40] if not ln.lstrip().startswith("|")
        )
        siblings = by_type[label.split(":", 1)[0]]
        assert_lifecycle(stem + ".md", content)
        if not [s for s in siblings if s != stem and re.search(rf"\b{s}\b", header)]:
            offenders.append(f"{label}: header names no other memory file (no routing)")
    assert not offenders, (
        "scaffolded memory templates violate CFR Appendix B.0:\n  "
        + "\n  ".join(offenders)
    )


def test_advertised_kit_counts_match_the_assembled_kit() -> None:
    """Every prose count of kit files must equal what the scaffold actually writes.

    Codex found three surfaces still advertising the pre-OPERATIONS numbers
    (10/5/11) after the kit gained a file: `API.md`, the `scaffold_project` MCP
    schema, and the handler's own suggestion text. Each was written by hand and
    each drifted independently — which is the point of deriving them here rather
    than maintaining a fourth copy of the same arithmetic.

    Counts come from the same tier-composition the handler uses, so a future kit
    change fails this test instead of silently outdating the docs.
    """
    import re

    from ai_governance_mcp.server._constants import (
        SCAFFOLD_CORE_FILES,
        SCAFFOLD_SAAS_OPS_EXTRAS,
        SCAFFOLD_STANDARD_EXTRAS,
    )

    def kit(project_type: str, tier: str) -> int:
        n = len(SCAFFOLD_CORE_FILES[project_type])
        if tier in ("standard", "saas-ops"):
            n += len(SCAFFOLD_STANDARD_EXTRAS[project_type])
        if tier == "saas-ops":
            n += len(SCAFFOLD_SAAS_OPS_EXTRAS[project_type])
        return n

    expected = {
        "code-core": kit("code", "core"),
        "code-standard": kit("code", "standard"),
        "code-saas": kit("code", "saas-ops"),
        "doc-core": kit("document", "core"),
        "doc-standard": kit("document", "standard"),
    }

    repo = Path(__file__).resolve().parent.parent
    api = (repo / "API.md").read_text()
    app = (repo / "src/ai_governance_mcp/server/_app.py").read_text()

    offenders = []
    for text, name in ((api, "API.md"), (app, "_app.py")):
        m = re.search(r"code: (\d+) files.*?document: (\d+) files", text, re.S)
        if m and int(m.group(1)) != expected["code-core"]:
            offenders.append(
                f"{name}: core code={m.group(1)}, kit={expected['code-core']}"
            )
        for label, pat in (
            ("code-standard", r"code: (\d+) files; (?:core \+ )?adds?"),
            ("code-saas", r'"saas-ops"[^)]*?\((\d+) files'),
        ):
            mm = re.search(pat, text)
            if mm and int(mm.group(1)) != expected[label]:
                offenders.append(
                    f"{name}: {label}={mm.group(1)}, kit={expected[label]}"
                )
    assert not offenders, (
        "advertised kit counts disagree with the assembled kit:\n  "
        + "\n  ".join(offenders)
    )


def test_start_protocols_tell_the_agent_to_check_operations() -> None:
    """Naming a memory file is not the same as instructing anyone to read it.

    `TestLoaderNamesEveryMemoryFileTheKitCreates` above checks the loader NAMES
    every kit file, and both loaders passed it while their Session Start / Session
    Protocol sections omitted OPERATIONS entirely. So a scaffolded project carried
    cadences and tripwires that nothing ever told the agent to open — and a cadence
    that is never checked is worse than an absent one, because it reads as covered.

    Codex caught this and asked for a test scoped to the start-protocol SECTION
    rather than the whole file, which is the correct shape: the earlier guard's
    file-wide search is exactly what let the omission pass.
    """
    import re

    from ai_governance_mcp.server._constants import (
        SCAFFOLD_AGENTS_MD,
        SCAFFOLD_AI_CONTEXT_README,
    )

    offenders = []
    for name, template in (
        ("AGENTS.md", SCAFFOLD_AGENTS_MD),
        ("_ai-context/README.md", SCAFFOLD_AI_CONTEXT_README),
    ):
        m = re.search(r"## Session (?:Start|Protocol)(.*?)(?:\n## |\Z)", template, re.S)
        if not m:
            offenders.append(f"{name}: no Session Start/Protocol section found")
            continue
        if "OPERATIONS" not in m.group(1):
            offenders.append(f"{name}: start protocol never mentions OPERATIONS.md")
    assert not offenders, (
        "generated start protocols omit OPERATIONS:\n  " + "\n  ".join(offenders)
    )


def test_generated_code_loader_defines_worktree_concurrency_contract() -> None:
    """A scaffolded project must receive the isolation contract, not only this repo."""
    from ai_governance_mcp.server._constants import SCAFFOLD_AGENTS_MD

    section = SCAFFOLD_AGENTS_MD.split("## Concurrency", 1)[1]
    for required in (
        "Each mutating session owns one checkout and one topic branch",
        "explicit live `origin/<default>`",
        "optimistic fast-forward",
        "recovery metadata atomically",
        "records native ownership",
        "cleanup refreshes remote refs",
        "deletion guard, not a session mutex",
        "ports, databases",
    ):
        assert required in section


def test_generated_completion_is_refresh_first_and_retryable() -> None:
    """Close-out must not write shared memory on a stale base or force a lost race."""
    from ai_governance_mcp.server._constants import SCAFFOLD_COMPLETION_CHECKLIST

    checklist = SCAFFOLD_COMPLETION_CHECKLIST
    assert "explicit live `origin/<default>`" in checklist
    assert checklist.index("Fetch and merge") < checklist.index(
        "overwrite _ai-context/SESSION-STATE.md"
    )
    assert "repeat refresh → tests → memory → commit → publish" in checklist
    assert "never force-push" in checklist


def test_architecture_alone_cannot_satisfy_the_memory_sibling_contract() -> None:
    """NEGATIVE CONTROL (Codex round 2) — the specific false pass, pinned.

    `ARCHITECTURE.md` is a framework **reference** doc, not memory:
    `EXECUTION-FRAMEWORK.md` §6.4 — "ARCHITECTURE.md, README.md, and
    reference-library/ are framework reference / charter docs — also 'ours,' but
    classified as reference, not memory."

    `_ai-context/PROJECT-MEMORY.md` routed only there and passed the routing check
    anyway, because ARCHITECTURE sat in a hand-typed sibling allowlist. Deriving the
    list fixes today's instance; this test pins the RULE, so no future edit can
    reintroduce a reference doc as a valid memory-routing destination without a
    failure naming exactly why.
    """
    import re

    header = (
        "# Project Memory\n"
        "**Memory Type:** Semantic (accumulates)\n"
        "**Lifecycle:** Accumulates; condense periodically.\n"
        "> For structural details → ARCHITECTURE.md\n"
    )
    siblings = {stem for _label, stem, _c in _memory_templates()}
    assert "ARCHITECTURE" not in siblings, (
        "ARCHITECTURE is in the derived memory-sibling set. It is a reference doc "
        "per EXECUTION-FRAMEWORK §6.4, and admitting it re-opens the false pass "
        "where a header routing only to ARCHITECTURE.md satisfies the contract."
    )
    routed = [
        s for s in siblings if s != "PROJECT-MEMORY" and re.search(rf"\b{s}\b", header)
    ]
    assert not routed, (
        f"a header routing only to ARCHITECTURE.md was accepted as routing to {routed} "
        "— the memory-sibling contract must reject it."
    )


# Public builds omit the private CFR. These counterexamples carry their own policy
# fixture, so parser/declaration coverage must not be skipped with corpus checks.
POLICY_FIXTURE = """### 7.0.2 Cognitive Memory Types
| Cognitive Type | File | Purpose | Lifecycle |
|---|---|---|---|
| **Working Memory** | `SESSION-STATE.md` | Current | Overwrite |
| **Semantic Memory** | `PROJECT-MEMORY.md` | Decisions | Preserve |
| **Episodic Memory** | `LEARNING-LOG.md` | Lessons | Graduate |
| **Procedural Memory** | Methods documents | Procedures | Evolve |
| **Prospective Memory** | `BACKLOG.md`, `OPERATIONS.md` | Intentions | Retire |
| **Reference Memory** | Context Engine index | Content | Rebuild |
### 7.0.3 Memory Loading Strategy
### 7.0.4 Memory Lifecycle Principles
**Distillation Triggers:**
| Memory File | Trigger | Action |
|---|---|---|
| SESSION-STATE.md | > 300 lines | Review |
| PROJECT-MEMORY.md | > 800 lines | Review |
| LEARNING-LOG.md | Entry > 6 months | Review |
| LEARNING-LOG.md | > 200 lines | Review |
| BACKLOG.md | > 600 lines | Review |
**Memory Health Check:**
"""


def test_wrong_but_canonical_learning_log_type_is_rejected(monkeypatch, tmp_path):
    from ai_governance_mcp.server import _constants

    policy = tmp_path / "policy.md"
    policy.write_text(POLICY_FIXTURE)
    monkeypatch.setattr(sys.modules[__name__], "_cfr_path", lambda: policy)
    templates = {
        kind: [
            (
                name,
                content.replace(
                    "**Memory Type:** Episodic", "**Memory Type:** Semantic"
                ),
            )
            for name, content in pairs
        ]
        for kind, pairs in _constants.SCAFFOLD_CORE_FILES.items()
    }
    monkeypatch.setattr(_constants, "SCAFFOLD_CORE_FILES", templates)
    with pytest.raises(AssertionError, match="LEARNING-LOG"):
        test_every_scaffolded_memory_template_declares_a_canonical_type()


def test_destructive_learning_log_lifecycle_is_rejected(monkeypatch):
    monkeypatch.setattr(
        sys.modules[__name__],
        "_memory_templates",
        lambda: [
            (
                "code:LEARNING-LOG",
                "LEARNING-LOG",
                "**Memory Type:** Episodic\n"
                "**Lifecycle:** Delete every lesson after one session.\n"
                "> Route decisions to PROJECT-MEMORY.md",
            ),
            (
                "code:PROJECT-MEMORY",
                "PROJECT-MEMORY",
                "**Memory Type:** Semantic\n"
                "**Lifecycle:** Grows with project.\n> Route lessons to LEARNING-LOG.md",
            ),
        ],
    )
    with pytest.raises(AssertionError, match="LEARNING-LOG"):
        test_scaffolded_memory_templates_meet_the_header_contract()


VALID_LIFECYCLES = {
    "SESSION-STATE.md": "Overwrite the current snapshot every session; keep no session-history stack.",
    "PROJECT-MEMORY.md": "Preserve decisions; condense supporting detail. Mark superseded decisions with a date and replacement link.",
    "LEARNING-LOG.md": "Graduate lessons into procedures when patterns emerge. Remove obsolete lessons per §7.3.4; never prune for size alone.",
    "BACKLOG.md": "Remove items when completed, closed, migrated, or abandoned.",
    "OPERATIONS.md": "Retire recurring commitments with a documented reason; completion alone is not retirement.",
}


@pytest.mark.parametrize("name,prose", VALID_LIFECYCLES.items())
def test_lifecycle_supported_declarations_and_wrapped_continuations(name, prose):
    assert_lifecycle(name, "**Lifecycle:** " + prose)
    assert_lifecycle(name, "**Lifecycle:** " + prose.replace("; ", ";\n  "))


@pytest.mark.parametrize(
    "name,prose",
    [
        (
            "SESSION-STATE.md",
            "Replaced at the start of each session; this is a snapshot, not a log.",
        ),
        (
            "PROJECT-MEMORY.md",
            "Retain all decisions. Summarize supporting material; superseded decisions carry the date and a link to the replacement.",
        ),
        (
            "LEARNING-LOG.md",
            "Distill recurring lessons into standing guidance. Removal follows §7.3.4; no size-only pruning.",
        ),
        (
            "BACKLOG.md",
            "Items are removed when implemented or abandoned. Git history holds closed work.",
        ),
        (
            "OPERATIONS.md",
            'Items persist indefinitely unless retired with documented rationale; these are never "done."',
        ),
    ],
)
def test_lifecycle_accepts_meaningful_tailored_variants(name, prose):
    assert_lifecycle(name, "**Lifecycle:** " + prose)


@pytest.mark.parametrize(
    "name,old,new",
    [
        (
            "SESSION-STATE.md",
            "Overwrite the current snapshot every session",
            "Append the latest session",
        ),
        (
            "SESSION-STATE.md",
            "keep no session-history stack",
            "route decisions elsewhere",
        ),
        ("PROJECT-MEMORY.md", "Preserve decisions; ", ""),
        ("PROJECT-MEMORY.md", "condense supporting detail. ", ""),
        ("PROJECT-MEMORY.md", "a date and ", ""),
        ("PROJECT-MEMORY.md", " and replacement link", ""),
        (
            "LEARNING-LOG.md",
            "Graduate lessons into procedures when patterns emerge. ",
            "",
        ),
        ("LEARNING-LOG.md", " when patterns emerge", ""),
        ("LEARNING-LOG.md", "Remove obsolete lessons per §7.3.4; ", ""),
        ("LEARNING-LOG.md", "; never prune for size alone", ""),
        ("BACKLOG.md", "completed, closed, migrated, or ", ""),
        ("BACKLOG.md", ", or abandoned", ""),
        ("OPERATIONS.md", "with a documented reason", "as convenient"),
        ("OPERATIONS.md", "; completion alone is not retirement", ""),
    ],
)
def test_lifecycle_rejects_missing_obligations(name, old, new):
    with pytest.raises(AssertionError, match=name):
        assert_lifecycle(
            name, "**Lifecycle:** " + VALID_LIFECYCLES[name].replace(old, new)
        )


@pytest.mark.parametrize(
    "name,conflict",
    [
        ("SESSION-STATE.md", "Keep a session-history stack."),
        ("PROJECT-MEMORY.md", "Delete superseded decisions."),
        ("LEARNING-LOG.md", "Delete every lesson after one session."),
        ("BACKLOG.md", "Keep completed work forever."),
        ("OPERATIONS.md", "Delete when done."),
    ],
)
def test_lifecycle_rejects_explicit_conflict_after_correct_clause(name, conflict):
    with pytest.raises(AssertionError, match="conflicting"):
        assert_lifecycle(
            name, "**Lifecycle:** " + VALID_LIFECYCLES[name] + " " + conflict
        )


def test_lifecycle_cannot_borrow_obligations_from_other_fields_or_body():
    valid = VALID_LIFECYCLES["PROJECT-MEMORY.md"]
    for suffix in ("\n\n" + valid, "\n> " + valid, "\n**Routing:** " + valid):
        with pytest.raises(AssertionError):
            assert_lifecycle("PROJECT-MEMORY.md", "**Lifecycle:** Grows." + suffix)


@pytest.mark.parametrize("field", ["Memory Type", "Lifecycle"])
def test_header_fields_must_be_unique_nonempty_and_in_first_forty_lines(field):
    line = f"**{field}:** Working"
    for text in (
        "",
        f"**{field}:**",
        line + "\n" + line,
        "\n" * 40 + line,
        f"| {line} | unrelated table cell |",
    ):
        with pytest.raises(AssertionError):
            declared_field(text, field)
    assert declared_field(line + "\n\n" + "\n" * 40 + line, field) == "Working"


def test_canonical_mapping_includes_both_prospective_files_and_exact_assignments():
    expected = {
        "SESSION-STATE.md": "Working",
        "PROJECT-MEMORY.md": "Semantic",
        "LEARNING-LOG.md": "Episodic",
        "BACKLOG.md": "Prospective",
        "OPERATIONS.md": "Prospective",
    }
    assert canonical_types(POLICY_FIXTURE) == expected
    for name, kind in expected.items():
        assert_declared_type(
            name, f"**Memory Type:** {kind} (tailored purpose)", expected
        )
        with pytest.raises(AssertionError, match=name):
            assert_declared_type(name, "**Memory Type:** Reference", expected)


@pytest.mark.parametrize(
    "old,new",
    [
        ("### 7.0.2", "### 7.9.2"),
        (
            "| Cognitive Type | File | Purpose | Lifecycle |",
            "| Type | File | Purpose | Lifecycle |",
        ),
        ("`BACKLOG.md`, `OPERATIONS.md`", "`BACKLOG.md`"),
        ("`BACKLOG.md`, `OPERATIONS.md`", "`BACKLOG.md`, OPERATIONS.md"),
        (
            "`BACKLOG.md`, `OPERATIONS.md`",
            "`BACKLOG.md`, `OPERATIONS.md`, `LEARNING-LOG.md`",
        ),
        (
            "`PROJECT-MEMORY.md` | Decisions",
            "`PROJECT-MEMORY.md`, LEARNING-LOG.md | Decisions",
        ),
        ("**Prospective Memory**", "**Semantic Memory**"),
        ("**Prospective Memory**", "Prospective"),
    ],
)
def test_canonical_mapping_fails_closed_on_missing_or_ambiguous_source(old, new):
    with pytest.raises(AssertionError, match="7.0.2"):
        canonical_types(POLICY_FIXTURE.replace(old, new))


def test_policy_parser_uses_canonical_section_not_earlier_copy_or_prose():
    fake = (
        POLICY_FIXTURE.split("### 7.0.3")[0]
        .replace("### 7.0.2", "### 1.0.2")
        .replace("**Episodic Memory**", "**Wrong Memory**")
    )
    assert (
        canonical_types(fake + "\n" + POLICY_FIXTURE)["LEARNING-LOG.md"] == "Episodic"
    )
    with pytest.raises(AssertionError):
        canonical_types(
            POLICY_FIXTURE.replace("`BACKLOG.md`, `OPERATIONS.md`", "`BACKLOG.md`")
            + "\nOPERATIONS.md is Prospective"
        )


def test_canonical_trigger_parser_selects_line_rows_not_age_or_source_documents():
    assert canonical_line_triggers(POLICY_FIXTURE) == {
        "SESSION-STATE.md": 300,
        "PROJECT-MEMORY.md": 800,
        "LEARNING-LOG.md": 200,
        "BACKLOG.md": 600,
    }
    assert (
        canonical_line_triggers(POLICY_FIXTURE.replace("> 200 lines", "> 201 lines"))[
            "LEARNING-LOG.md"
        ]
        == 201
    )


@pytest.mark.parametrize(
    "old,new",
    [
        ("**Distillation Triggers:**", "Triggers:"),
        ("| Memory File | Trigger | Action |", "| File | Trigger | Action |"),
        ("| LEARNING-LOG.md | > 200 lines | Review |\n", ""),
        ("> 200 lines", "about 200 lines"),
        (
            "| LEARNING-LOG.md | > 200 lines | Review |",
            "| LEARNING-LOG.md | > 200 lines | Review |\n| LEARNING-LOG.md | > 300 lines | Review |",
        ),
    ],
)
def test_canonical_trigger_parser_fails_closed(old, new):
    with pytest.raises(AssertionError, match="7.0.4"):
        canonical_line_triggers(POLICY_FIXTURE.replace(old, new))


def test_current_header_threshold_claims_checked_without_rewriting_history():
    triggers = canonical_line_triggers(POLICY_FIXTURE)
    name = "LEARNING-LOG.md"
    assert_header_line_claims(
        name, "**Lifecycle:** Review trigger: >200 lines.", triggers
    )
    assert_header_line_claims(
        name,
        "**Lifecycle:** Entry rules ≤5 lines.\n> Previously quoted >300 lines.\n| 1.0 | >300 lines |",
        triggers,
    )
    for claim in (
        "**Lifecycle:** Review trigger: >300 lines.",
        "**Review trigger:** >300 lines",
        "Target: 300 lines",
        "> Review trigger: >300 lines",
    ):
        with pytest.raises(AssertionError, match="7.0.4"):
            assert_header_line_claims(name, claim, triggers)


def test_decision_preservation_is_not_mistaken_for_an_explicit_conflict():
    assert_lifecycle(
        "PROJECT-MEMORY.md",
        "**Lifecycle:** Never delete superseded decisions; "
        "condense supporting detail. Mark superseded decisions with date and replacement link.",
    )


def test_wrong_source_assignment_disagrees_with_real_header_even_if_type_is_canonical():
    swapped = POLICY_FIXTURE.replace(
        "`LEARNING-LOG.md` | Lessons", "`PROJECT-MEMORY.md` | Lessons"
    ).replace("`PROJECT-MEMORY.md` | Decisions", "`LEARNING-LOG.md` | Decisions")
    with pytest.raises(AssertionError, match="LEARNING-LOG"):
        assert_declared_type(
            "LEARNING-LOG.md", "**Memory Type:** Episodic", canonical_types(swapped)
        )
