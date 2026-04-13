# Constitutional Framework Alignment — Implementation Plan

**Created:** 2026-04-10
**Last Updated:** 2026-04-12
**Status:** COMPLETE — All 7 phases done. Tagged `v2.0.0`. Released 2026-04-12.
**Reference docs:** `~/Downloads/AI_Governance_Detailed_Summary_v4.md`, `~/Downloads/US_Constitutional_Gap_Analysis.md`

## Context

The ai-governance framework already uses a US Constitutional analogy in prose and hierarchy tables, but the analogy is surface-level — numbered levels (1-5) mapped to legal concepts, with descriptive section names that don't reflect Constitutional structure. The goal is to move from analogy to genuine structural alignment: the document *is* a Constitution with Articles, Sections, and Amendments, not a principles list that *references* a Constitution.

Two reference documents guide this work:
- **AI_Governance_Detailed_Summary_v4.md** — Frames the framework evolution (prompt → context → intent engineering), maps Constitutional elements, includes well-written Declaration content
- **US_Constitutional_Gap_Analysis.md** — Identifies 8 missing Constitutional concepts with priority rankings

**Governance assessments:** PROCEED (`gov-bc32cdf42a50`, `gov-8f560416bc52`, `gov-53ac23d94eeb`). Key principles: `meta-core-structural-foundations`, `meta-method-breaking-changes-major`, `meta-core-systemic-thinking`, `meta-method-framework-hierarchy-reference`.

**Contrarian review 1 (HIGH confidence):** Initial plan was too conservative — "cosmetic labeling" rather than structural alignment. Rescoped to deliver genuine restructuring.

**Contrarian review 2 (HIGH confidence):** Five-purposes reframe validated. Cutting 5 of 8 Constitutional concepts is sound EXCEPT Full Faith and Credit — no cross-domain output recognition mechanism actually exists in the framework. Reinstated as 4th addition. Equal Protection and Impeachment covered by 1-sentence/1-paragraph additions to existing sections.

**Contrarian review 3 (HIGH confidence):** Framework Structure mapping should be a structural reference (describes the document's organization on its own terms), not an analogy mapping. Replaces existing Legal Analogy Interpretation Guide, doesn't add to it.

**Contrarian review 4 (HIGH confidence):** Preamble should be interpretive context, not operative governance. Purpose-alignment enforcement belongs in the Admission Test (Question 0), not in a vague operative Preamble that competes with the existing gate.

**Contrarian review 5 (HIGH confidence):** Applying storytelling principles to the Declaration is correct (its purpose IS communication). Scope boundary: storytelling applies to communication-purpose sections only (Declaration, README), not operative governance (Articles, Methods).

## Governing Principle: Pattern, Not Analogy

The US Constitution is not the source material — it's a proven *instance* of a governance framework pattern. ai-governance adopts the pattern (layered authority, separation of concerns, amendment process, supremacy clause) and expresses it for AI interaction governance. The same way every domain follows the ai-governance framework but expresses it in domain-appropriate terms, the framework itself follows the Constitutional governance pattern but with content authentic to its purpose.

This means: our Declaration serves the same *structural purpose* as the Declaration of Independence (stating why the system exists) but contains our own content (prompt → context → intent engineering). Our Articles serve the same structural purpose as Constitutional Articles (organizing governing principles by branch) but contain our principles. We follow the framework closely enough that the structural connection is visible to AI and humans, but never shoe-horn content to match a specific Constitutional provision.

**The US Constitution as provenance and pedagogical anchor:** The Declaration section tells the story of where this pattern comes from. The five root purposes are abstract — Authority, Process, Protection, Relations, Continuity. Abstractions are hard to grasp without a concrete anchor. The US Constitution is the most universally understood implementation of this pattern: its Bill of Rights handles Protection, its Articles handle Authority and Process, its Amendment process handles Continuity. Citing this gives readers an immediate "oh, I get it" moment before they see how ai-governance applies the same pattern to AI interactions. This is pedagogical (builds comprehension), not prescriptive (doesn't drive decisions). The v4 mapping table lives in the Declaration as provenance — "here's the proven example that inspired this structure." The Framework Structure section that follows stands on its own terms.

## Five Root Purposes

Any governance system must solve five fundamental problems. Rather than mapping individual Constitutional leaves (bicameralism, jury trials, commerce clause), the framework aligns at the branch level:

| Root Purpose | What It Solves | ai-governance Coverage |
|---|---|---|
| **Authority** | Who has power, how much, and what are its limits? | Supremacy clause, hierarchy, Human-AI Authority & Accountability, S-Series veto |
| **Process** | How do decisions get made, changed, and enforced? | Rules of Procedure (200+ methods), admission test, breaking changes, deprecation |
| **Protection** | What safeguards prevent misuse? | Bill of Rights (S-Series), subagent review battery, proportional application |
| **Relations** | How do the parts interact? | Cross-domain consistency, Full Faith and Credit (being added) |
| **Continuity** | How does the system persist and evolve? | Article IV: Governance (G-Series), continuity-auditor, handoff patterns |

These go in the Declaration section — they help readers understand the higher-level purpose structure before encountering the specific Articles and Amendments. Per `meta-core-systemic-thinking`: operate at the branch level, not the leaf level.

**User decisions (2026-04-10):**
1. Full structural alignment (not conservative approach)
2. Dual-layer ID system (slug IDs for machines + Constitutional citations for humans)
3. Title-based domain file naming (e.g., `title-10-ai-coding.md`)

---

## Key Design Decisions

### D1: Dual-Layer ID System
**Keep slug IDs for machines, add Constitutional citations for humans.**

The current slug system (`meta-core-context-engineering`) was designed to prevent AI hallucination — documented in v1.5 amendments. Replacing it would reintroduce those bugs. Instead, add a human-readable Constitutional citation layer:

| Layer | Purpose | Example | Where It Lives |
|-------|---------|---------|----------------|
| **Slug ID** (machine) | Index retrieval, code references, tool output | `meta-core-context-engineering` | Index, code, YAML `id:` field |
| **Constitutional citation** (human) | Document navigation, cross-references, conversation | `Art. I, § 1` | YAML `constitutional_ref:`, section headers |

Citation format:
- Constitution Articles: `Art. I, § 1` (Article I, Section 1)
- Bill of Rights: `Amend. I` (Amendment I)
- Domain Statutes: `T.10, § 1` (Title 10, Section 1) — Title numbers from `domains.json` priority field
- Rules of Procedure: `R.P. § 9.7.1` (already using Part/Section numbering)
- Domain Regulations: `T.10 C.F.R. § 1.1` (Title 10 Code of Federal Regulations)

### D2: Document Restructuring

| Current File | New File | Constitutional Role |
|---|---|---|
| `ai-interaction-principles.md` | `constitution.md` | Declaration + Preamble + Articles I-IV + Bill of Rights (Amendments) |
| `ai-governance-methods.md` | `rules-of-procedure.md` | Framework maintenance methods (already uses TITLE/Part structure) |
| `ai-coding-domain-principles.md` | `title-10-ai-coding.md` | Federal Statute — AI Coding |
| `ai-coding-methods.md` | `title-10-ai-coding-cfr.md` | Code of Federal Regulations — AI Coding |
| `ui-ux-domain-principles.md` | `title-15-ui-ux.md` | Federal Statute — UI/UX |
| `ui-ux-methods.md` | `title-15-ui-ux-cfr.md` | Code of Federal Regulations — UI/UX |
| `multi-agent-domain-principles.md` | `title-20-multi-agent.md` | Federal Statute — Multi-Agent |
| `multi-agent-methods.md` | `title-20-multi-agent-cfr.md` | Code of Federal Regulations — Multi-Agent |
| `kmpd-domain-principles.md` | `title-25-kmpd.md` | Federal Statute — KM&PD |
| `kmpd-methods.md` | `title-25-kmpd-cfr.md` | Code of Federal Regulations — KM&PD |
| `storytelling-domain-principles.md` | `title-30-storytelling.md` | Federal Statute — Storytelling |
| `storytelling-methods.md` | `title-30-storytelling-cfr.md` | Code of Federal Regulations — Storytelling |
| `multimodal-rag-domain-principles.md` | `title-40-multimodal-rag.md` | Federal Statute — Multimodal RAG |
| `multimodal-rag-methods.md` | `title-40-multimodal-rag-cfr.md` | Code of Federal Regulations — Multimodal RAG |

Title numbers derive from existing `domains.json` priority field (ai-coding=10, ui-ux=15, multi-agent=20, kmpd=25, storytelling=30, multimodal-rag=40).

### D3: Constitution Internal Structure

**Current:**
```
## Core Architecture Principles
### Context Engineering
### Single Source of Truth
...
## Safety & Ethics Principles
### Non-Maleficence, Privacy & Security
...
```

**New:**
```
## Declaration
(prompt → context → intent engineering; from v4 document)

## Preamble
(interpretive context — condensed binding purposes, referenced by Admission Test Q0)

## Article I: Core Architecture (Legislative Branch) — C-Series
### Section 1: Context Engineering
### Section 2: Single Source of Truth
### Section 3: Separation of Instructions and Data
### Section 4: Structural Foundations
### Section 5: Discovery Before Commitment
### Section 6: Systemic Thinking

## Article II: Operational Efficiency (Executive Branch) — O-Series
### Section 1: Atomic Task Decomposition
### Section 2: Explicit Over Implicit
### Section 3: Interaction Mode Adaptation
### Section 4: Resource Efficiency & Waste Reduction
### Section 5: Goal-First Dependency Mapping
### Section 6: Failure Recovery & Resilience

## Article III: Quality & Integrity (Judicial Branch) — Q-Series
### Section 1: Verification & Validation
### Section 2: Structured Output Enforcement
### Section 3: Visible Reasoning & Traceability
### Section 4: Effective & Efficient Communication

## Article IV: Governance & Evolution (Administrative State) — G-Series
### Section 1: Risk Mitigation by Design
### Section 2: Continuous Learning & Adaptation
### Section 3: Human-AI Authority & Accountability

## Bill of Rights (Amendments) — S-Series
### Amendment I: Non-Maleficence, Privacy & Security
### Amendment II: Bias Awareness & Fairness (Equal Protection)
### Amendment III: Transparent Limitations
```

The series codes (C, Q, O, G, S) are preserved for machine use — they map to Articles I-IV and Amendments. The series code → Constitutional element mapping becomes first-class documentation.

### D4: Series Code Preservation

Series codes stay. They're referenced in ~400 places across code and docs. The mapping becomes explicit:

| Series Code | Constitutional Element | Branch |
|---|---|---|
| S | Bill of Rights (Amendments) | Supreme Protections |
| C | Article I | Legislative Branch |
| O | Article II | Executive Branch |
| Q | Article III | Judicial Branch |
| G | Article IV | Administrative State |

### D5: Domain Internal Structure — Fix Cross-Domain Numbering Collisions

**Problem being fixed:** Multiple domains reuse identical series codes, creating ambiguity for AI retrieval:
- `A1` = "Unified Embedding Space" (Multimodal RAG) AND "Audience Discovery First" (Storytelling)
- `C1` = "Specificity Over Abstraction" (Storytelling) — collides with C-Series (Core) at constitutional level
- `P1` = "Inline Image Integration" (Multimodal RAG) — collides with P-Series (Process) in AI Coding
- `R1` = "Image-Text Collocation" (Multimodal RAG) — collides with R-Series (Reliability) in Multi-Agent
- Same pattern across `E1`, `F1`, `V1`, `O1`, etc.

An AI querying "A1" or "C1" gets ambiguous cross-domain results. The slug IDs are unique (`mrag-architecture-a1-unified-embedding-space` vs `stor-architecture-a1-audience-discovery-first`), but the in-document short codes are not.

**Fix:** The Title-based numbering system makes every reference globally unique. Each domain gets a unique Title number, so section numbers never collide:

| Current (Ambiguous) | New (Globally Unique) | Domain |
|---|---|---|
| `A1: Unified Embedding Space` | `T.40, § 1: Unified Embedding Space` | Multimodal RAG |
| `A1: Audience Discovery First` | `T.30, § 1: Audience Discovery First` | Storytelling |
| `C1: Specificity Over Abstraction` | `T.30, § 9: Specificity Over Abstraction` | Storytelling |
| `P1: Inline Image Integration` | `T.40, § 5: Inline Image Integration` | Multimodal RAG |

Domain principle series become Chapters within their Title, with section numbers that are unique within the Title (continuous numbering across chapters, not restarting per chapter):
```
## Chapter 1: Context Statutes (C-Series)
### T.10, § 1: Specification Completeness
### T.10, § 2: Sequential Phase Dependencies
...
## Chapter 2: Process Statutes (P-Series)
### T.10, § 3: Validation Gates
...
```

**Extractor changes required:** The title-stripping regex evolves across two phases:
- **Phase 2C** (constitution only): strips `Section N:` and `Amendment N:` prefixes
- **Phase 4F** (domains): extends to also strip `T.NN, § N:` prefixes

Final regex (applied in Phase 4F):
```python
# Strip Constitutional prefixes from all principle headers
title = re.sub(r'^(?:Section|Amendment)\s+[IVXLC\d]+[:\.]?\s*', '', raw_title)  # Phase 2C
title = re.sub(r'^T\.\d+,?\s*§\s*\d+[:\.]?\s*', '', title)  # Phase 4F addition
```

**Regex safety note (contrarian F2):** The Roman numeral character class `[IVXLC\d]+` is greedy and could consume leading characters of titles starting with I, V, X, L, or C. Use an anchored pattern with a colon delimiter lookahead, e.g., `[IVXLC]+(?=\s*:)|\d+(?=\s*:)` to prevent over-matching. Write unit tests for every principle title before applying.

This ensures the slug IDs remain unchanged while the visible numbering becomes globally unique.

### D6: Preamble Classification — Interpretive Context (Not Operative, Not Purely Communicative)

The Preamble states the framework's binding purposes but does not itself create rules. It sits between the Declaration (narrative/communication) and the Articles (operative governance) as a **translation layer**.

**Why not operative:** A vague operative Preamble ("encode intent, standards, and judgment") becomes a rubber stamp that competes with the Admission Test. Almost anything touching AI could claim alignment. Two gates with different standards = forum shopping.

**Why not purely communicative:** If the Preamble's purposes aren't loaded in operational contexts, nothing prevents scope drift. New principles pass the Admission Test (coverage, placement, derivation) but nobody asks "does this serve what this framework is for?" — Failure Narrative 3 from contrarian review.

**The solution — Admission Test Question 0:** Add a Purpose Alignment question to the existing Admission Test (Part 9.8.1) that references the Preamble's stated purposes:

> **Question 0 — Purpose Alignment:** Does this content serve one or more of the purposes stated in the Preamble? Which one(s)? If the content cannot cite a specific Preamble purpose it serves, it fails the admission test regardless of other criteria.

This gives structural enforcement through the existing gate without creating a new operative layer. The Preamble is the *source* of the criteria; the Admission Test is the *enforcement mechanism*. Each does what it does best.

**Contrarian-verified (HIGH confidence):** This matches how the US Preamble actually works — courts reference it when interpreting amendments, but it doesn't independently grant powers. The Admission Test is CRITICAL-tagged with structural enforcement, making casual modification unlikely.

| Section | Role | Storytelling applies? | Enforcement |
|---|---|---|---|
| Declaration | Communication — story, provenance, comprehension | Yes — purpose IS communication | None — background/context only |
| Preamble | Interpretive context — states binding purposes | No — precise and scannable | Indirect — referenced by Admission Test Q0 |
| Framework Structure | Structural reference — document navigation | No — functional reference | None — orientation aid |
| Articles/Amendments | Operative governance — the actual principles | No | Direct — Supremacy Clause, S-Series veto |

### D7: Storytelling Scope Boundary

Storytelling domain principles (`stor-*`) apply to sections whose **purpose is communication**: Declaration, README, onboarding materials. They do NOT apply to sections whose purpose is operative governance (Articles, Methods, Appendices) or interpretive context (Preamble — precise and scannable per D6).

This boundary is self-enforcing — it derives from the content's purpose, not an arbitrary line. The Declaration was reviewed against storytelling principles and two improvements were identified:
1. **Resolution calibration (`stor-medium-m4`):** The narrative opens a loop (AI needs judgment) that must close on THIS framework as the answer, not on the US Constitution as provenance. Beat 3 must loop back.
2. **Hook calibration (`stor-medium-m1`):** Lead with "giving AI judgment" (the most compelling framing from the v4 document) not "three phases of AI" (a topic sentence, not a hook).

These are built into Phase 1 drafting from the start (zero marginal cost), not applied as a separate pass. Per `kmpd-knowledge-architecture-ka3` and `meta-core-context-engineering`: engagement is a delivery mechanism for comprehension, not decoration.

### D8: What Does NOT Change
- **Slug IDs** — all existing IDs preserved (`meta-core-context-engineering`, etc.)
- **S-Series detection logic** — `series_code == "S"` checks remain
- **Domain names in domains.json** — `constitution`, `ai-coding`, etc.
- **Domain prefixes** — `meta`, `coding`, `multi`, etc.
- **CATEGORY_SERIES_MAP** — only additive changes
- **Existing principle content** — only structural framing changes
- **Reference Library** — unchanged (case law remains case law)
- **Subagent definitions** — format unchanged

---

## Implementation Phases

### Phase 0: Preparation & Safety Net
**Scope: Small | Risk: Minimal | ~1 hour**

**Revert strategy (contrarian-reviewed, HIGH confidence):** Work on main (trunk-based), not a feature branch. CI triggers on push to main — a branch would remove automatic CI from the highest-risk phases. The pre-work tag provides equivalent rollback. Gate-aligned tags (5 total) created only after full test suite passes.

**Step 1: Verify clean baseline**
```bash
pytest tests/ -v --tb=short -m "not slow"   # Must be green
git status                                    # Must be clean
```
Do not proceed if tests fail. Fix first.

**Step 2: Tag the safety anchor**
```bash
git tag v1.8.0-pre-constitutional -m "Safety anchor before Constitutional restructuring"
git push origin v1.8.0-pre-constitutional
```
Pushed to remote — from any state, `git reset --hard v1.8.0-pre-constitutional` returns to pre-restructuring.

**Step 3: Archive reference copies**
```bash
mkdir -p documents/archive/
cp documents/ai-interaction-principles.md documents/archive/ai-interaction-principles-v3.0.0.md
cp documents/ai-governance-methods.md documents/archive/ai-governance-methods-v3.23.2.md
```

**Step 4: Create migration tracking file:** `documents/migration/constitutional-alignment.md`

**Step 5: Document rationale in PROJECT-MEMORY.md**

**Step 6: Commit Phase 0**
```bash
git add documents/archive/ documents/migration/ PROJECT-MEMORY.md
git commit -m "refactor(phase-0): safety net — tag, archive, migration doc"
```

#### Gate Tag Protocol (applies to all subsequent phases)

Tags are created **only** at review gates, **only** after the full test suite passes:

| Gate | Tag | After Phase | Time at Risk | Revert Command |
|------|-----|-------------|-------------|----------------|
| — | `v1.8.0-pre-constitutional` | Pre-work | 0 | — |
| Gate 1 | `const/gate-1` | Phase 1 | ~2-3 hrs | `git reset --hard v1.8.0-pre-constitutional` |
| Gate 2 | `const/gate-2` | Phase 2 | ~4-6 hrs | `git reset --hard const/gate-1` |
| Gate 3 | `const/gate-3` | Phase 3 | ~2-3 hrs | `git reset --hard const/gate-2` |
| Gate 4 | `const/gate-4` | Phase 4 | ~4-5 hrs | `git reset --hard const/gate-3` |
| Gate 5 | `const/gate-5` | Phase 6 | ~3-5 hrs | `git reset --hard const/gate-4` |

```bash
# Tag creation protocol (same for every gate):
pytest tests/ -v --tb=short -m "not slow"  # 1. Full test suite must pass
git tag const/gate-N                        # 2. Tag only if tests pass
# 3. Present to user for review gate approval
```

#### Revert Cheat Sheet

| Situation | Command |
|-----------|---------|
| Revert to any gate boundary | `git reset --hard const/gate-N` |
| Abandon everything, back to pre-restructuring | `git reset --hard v1.8.0-pre-constitutional` |
| Stash WIP to debug mid-phase | `git stash push -m "description"` |
| See changes since last gate | `git diff const/gate-N` |
| Nuclear: restore from remote | `git fetch origin && git reset --hard v1.8.0-pre-constitutional` |
| Hotfix needed mid-restructuring | Commit at gate boundary, push fix, continue |
| Index/embeddings corrupted | `rm -rf index/ && pytest tests/test_extractor.py -v` |

**Files created/modified:**
- `documents/archive/` (2 copied files)
- `documents/migration/constitutional-alignment.md` (new)
- `PROJECT-MEMORY.md` (append)
- Git tag (pushed to remote)

**Test impact:** None.

**No review gate** — this is scaffolding only.

---

### Phase 1: Declaration + Preamble + Framework Structure
**Scope: Medium | Risk: Low | ~2-3 hours**

Add the two missing foundational layers as new sections at the top of `ai-interaction-principles.md`. No structural changes to existing sections yet — purely additive.

1. **Add Declaration section** after YAML frontmatter, before "SYSTEM INSTRUCTION" block. The Declaration tells a story in three beats:
   - **Beat 1 — Why this exists:** The prompt → context → intent engineering evolution (sourced from v4 document). Engages the reader with the problem this framework solves.
   - **Beat 2 — The pattern:** Any governance system must solve five problems (Authority, Process, Protection, Relations, Continuity). Introduces the abstract framework pattern.
   - **Beat 3 — Provenance:** The US Constitution is the most proven implementation of this pattern — 237 years, stress-tested. Include the v4 mapping table showing how Constitutional elements implement the five purposes (Bill of Rights → Protection, Articles → Authority/Process, Amendment process → Continuity, etc.). This gives readers the concrete "oh, I get it" anchor before seeing how ai-governance applies the same pattern to AI interactions. Pedagogical, not prescriptive — builds comprehension, doesn't drive decisions.
   - The Declaration bridges naturally into the Preamble (condensed purpose) and Framework Structure (how this document is organized on its own terms).
   
2. **Add Preamble section** immediately after Declaration
   - **Role: Interpretive context** — states the framework's binding purposes but does not itself create rules (see D6)
   - Condensed purpose statement (~1 paragraph) — precise and scannable, not narrative
   - Include self-application commitment: "This framework governs its own development by the same standards it defines"
   - The Preamble's stated purposes become the criteria for Admission Test Question 0 (added in Phase 3)
   - **Storytelling does NOT apply here** — the Preamble's purpose is operative alignment, not communication (see D7)
   
3. **Replace the entire Legal Analogy Interpretation Guide** (lines 28-66) with a **Framework Structure** section
   - This is a structural reference for the actual document organization, not an analogy mapping
   - Include the five root purposes table (Authority, Process, Protection, Relations, Continuity) connecting the Declaration's philosophy to the document's structure
   - Include the structural layers table (Declaration → Preamble → Bill of Rights → Articles → Statutes → Rules of Procedure → Regulations → SOPs → Case Law) with override order and stability
   - Include Supremacy Clause, derivation chain, and "where does new content belong?" flowchart — all updated from Level 1-5 to named layers
   - **Replaces** the existing 39-line section (lines 28-66), does not add to it — keeps pre-principle preamble from growing
   - Frame as "here's how this document is organized" not "here's how we map to the US Constitution"
   - **Contextual vs operative layers:** Declaration and Preamble appear in the table for document flow but do NOT participate in override mechanics. Structure the table in two sections: "Contextual layers (non-operative)" for Declaration/Preamble, and "Operative hierarchy (override order)" for Bill of Rights through Case Law. This prevents implying Declaration overrides the Bill of Rights.

4. **Update `_get_category_from_section()` in extractor.py** — add defensive category mappings:
   ```python
   "declaration": "declaration",
   "preamble": "preamble",
   ```
   (These sections won't have principle indicators, so no phantom principles get created)

**Files modified:**
- `documents/ai-interaction-principles.md` — add 2 sections, update hierarchy table
- `src/ai_governance_mcp/extractor.py` — add 2 category mapping entries

**Test impact:** Low. Declaration/Preamble have no principle indicators (no `**Definition**`, no `**Failure Mode(s)**`) so the extractor skips them. May need to update any test that asserts exact line numbers for the hierarchy table. Run full test suite.

#### Review Gate 1: Declaration + Preamble + Framework Structure
**Stop and present to user before proceeding to Phase 2.**

Review checklist:
- [ ] Read the Declaration section — does the three-beat narrative (why → pattern → provenance) flow naturally and engage you? Does the US Constitution mapping table feel like a helpful "I get it" anchor or like forced analogy?
- [ ] Read the Preamble — is it the right condensed "elevator pitch"? Does the self-application commitment feel natural?
- [ ] Review the Framework Structure section — does it read as "here's how this document works" (good) or "here's how we map to the US Constitution" (bad)? Does it feel like a structural reference a reader would actually use?
- [ ] Confirm the overall direction feels right before committing to the structural restructuring in Phase 2

This is the cheapest point to course-correct on tone, framing, and naming before those choices cascade into every subsequent phase.

---

### Phase 2: Restructure Constitution into Articles + Amendments
**Scope: Large | Risk: High | ~4-6 hours**

THE core structural change. Reorganize the constitution's section headers to use Article/Section/Amendment numbering while preserving all principle content.

**2A: Update section headers**

Transform existing headers:
- `## Core Architecture Principles` → `## Article I: Core Architecture (Legislative Branch)`
- `### Context Engineering` → `### Section 1: Context Engineering`
- `## Safety & Ethics Principles` → `## Bill of Rights (Amendments)`
- `### Non-Maleficence, Privacy & Security` → `### Amendment I: Non-Maleficence, Privacy & Security`
- (Apply to all 22 principles across all 5 series)

**2B: Add `constitutional_ref` to Principle model**

In `src/ai_governance_mcp/models.py`, add field to `Principle`:
```python
constitutional_ref: Optional[str] = Field(
    None,
    description="Constitutional citation (e.g., 'Art. I, § 1', 'Amend. I', 'T.10, § 1')"
)
```

**2C: Update extractor to handle new headers**

In `src/ai_governance_mcp/extractor.py`:

1. `_get_category_from_section()` — add Article-based mappings:
   ```python
   "article i": "core",
   "article ii": "operational",
   "article iii": "quality",
   "article iv": "governance",
   "bill of rights": "safety",
   "amendment": "safety",
   ```

2. Title extraction — strip Constitutional prefixes from principle titles:
   ```python
   # Strip "Section N:" or "Amendment N:" prefix from principle headers
   title = re.sub(r'^(?:Section|Amendment)\s+[IVXLC\d]+[:\.]?\s*', '', raw_title)
   ```
   This ensures `### Section 1: Context Engineering` generates title `Context Engineering` (not `Section 1: Context Engineering`), preserving the existing slug ID `meta-core-context-engineering`.

3. Constitutional reference generation — compute `constitutional_ref` during extraction:
   - Track Article number from parent `##` header
   - Track Section number from `###` header
   - Generate citation string (`Art. I, § 1`, `Amend. I`, etc.)
   - Store on Principle object

**2D: Update retrieval.py**

- `_CONSTITUTION_HIERARCHY` — add Constitutional element comments (values unchanged):
  ```python
  _CONSTITUTION_HIERARCHY: dict[str, int] = {
      "S": 0,  # Bill of Rights (Amendments) — immutable safety guardrails
      "C": 1,  # Article I: Core Architecture (Legislative)
      "Q": 2,  # Article III: Quality & Integrity (Judicial)
      "O": 3,  # Article II: Operational Efficiency (Executive)
      "G": 4,  # Article IV: Governance & Evolution (Administrative)
  }
  ```

**2E: Update server.py display formatting**

When displaying principles in tool output, include Constitutional citation alongside slug ID:
```
[Art. I, § 1] Context Engineering (meta-core-context-engineering)
```

**2F: Update Framework Overview section**

Rewrite the "Five Principle Series" overview (lines 70-94) to use Article/Amendment language:
```
The Constitution organizes 22 principles into four Articles and a Bill of Rights:

1. **Article I: Core Architecture (C-Series)** — 6 principles
   Legislative Foundation establishing the structural laws...

2. **Article II: Operational Efficiency (O-Series)** — 6 principles
   Executive Branch for execution and resource management...
   
3. **Article III: Quality & Integrity (Q-Series)** — 4 principles
   Judicial Branch for verification and judgment...
   
4. **Article IV: Governance & Evolution (G-Series)** — 3 principles
   Administrative State for long-term system health...

5. **Bill of Rights (S-Series)** — 3 Amendments
   Immutable safety guardrails with veto authority...
```

**2G: Update tiers.json**

The universal floor in `tiers.json` references specific principle IDs. Verify all referenced IDs still resolve after the restructuring. Add Constitutional citations as display metadata if the format supports it.

**Files modified:**
- `documents/ai-interaction-principles.md` — all section headers restructured
- `src/ai_governance_mcp/models.py` — add `constitutional_ref` field
- `src/ai_governance_mcp/extractor.py` — category mappings, title stripping, citation generation
- `src/ai_governance_mcp/retrieval.py` — comments update
- `src/ai_governance_mcp/server.py` — display formatting
- `documents/tiers.json` — verify/update

**Test impact: HIGH.**
- `tests/test_extractor.py` — principle count assertions, title extraction tests, category mapping tests
- `tests/test_extractor_integration.py` — integration tests parsing real constitution
- `tests/test_models.py` — Principle model schema tests (new field)
- `tests/test_server.py` — display format assertions
- `tests/test_retrieval.py` — hierarchy ordering tests
- `tests/benchmarks/` — baseline files will need regeneration
- **Strategy:** Update tests alongside each code change. Regenerate benchmarks after all Phase 2 changes. Run full suite.

**Risk mitigation:**
- The title-stripping regex is the highest-risk change. It MUST preserve existing titles exactly (not just approximately). Write unit tests for every principle before applying.
- If title stripping fails, the fallback is titles like `Section 1: Context Engineering` which would generate new IDs like `meta-core-section-1-context-engineering` — breaking everything. Test this rigorously.
- Do Phase 2 as a single atomic commit. If tests fail, revert and debug.

#### Review Gate 2: Articles + Amendments Structure
**Stop and present to user before proceeding to Phase 3. This is the most critical review.**

Review checklist:
- [ ] Read the restructured constitution top-to-bottom — does the Article I/II/III/IV + Amendments structure read naturally?
- [ ] Check section numbering: `### Section 1: Context Engineering` — is the format comfortable? Too formal? Not formal enough?
- [ ] Check Amendment numbering: `### Amendment I: Non-Maleficence, Privacy & Security` — does it work?
- [ ] Review the Constitutional citation format in tool output (e.g., `[Art. I, § 1] Context Engineering`) — is it useful or cluttered?
- [ ] Verify all 22 principles are still correctly extracted: `pytest tests/test_extractor.py -v`
- [ ] **Slug ID regression test:** Diff extracted principle IDs against `tests/benchmarks/baseline_2026-04-10.json` — zero ID changes. This is the single most critical check. If any ID changed, title stripping failed.
- [ ] Try a `query_governance` call — do citations appear? Do they help?
- [ ] **Critical:** Does the document still feel like a governance framework, or has the Constitutional metaphor overtaken the substance?

This gate exists because every subsequent phase builds on this structure. If the Article/Section format needs adjustment, fix it here.

---

### Phase 3: Constitutional Concept Additions
**Scope: Medium | Risk: Medium | ~2-3 hours**

The original gap analysis identified 8 missing Constitutional concepts. After applying systemic thinking (per `meta-core-systemic-thinking`), the question shifted from "which individual leaves are missing?" to "which branches need strengthening?" All five root purposes (Authority, Process, Protection, Relations, Continuity) are already covered. The additions below strengthen edges and fill one genuine gap identified by contrarian review.

**Contrarian review disposition (2 rounds, both HIGH confidence):**
- 4 items added (genuine gaps or branch-edge strengthening)
- 2 items → surgical edits to existing sections (already covered but not explicitly named)
- 2 items cleanly cut (structurally enforced by existing architecture)

**3A: New Methods/Amendments (4 items)**

1. **Elastic Clause (Necessary and Proper)** — Strengthens *Authority* branch at the ambiguity edge
   - **New meta-method** in rules-of-procedure, Title 8 after Part 8.5
   - **Method ID:** `meta-method-elastic-clause-derived-authority`
   - **Content:** "When no existing principle directly governs a situation, the AI may derive guidance from the most analogous existing principle's *intent*, documenting the reasoning chain. This derivation must be flagged for human review."

2. **Unenumerated Rights (9th Amendment)** — Strengthens *Authority* branch against loophole thinking
   - **Recommend: Amendment IV** in the Bill of Rights (the 9th Amendment IS part of the Bill of Rights)
   - **Content:** "These principles are not exhaustive. Professional judgment, ethical reasoning, and domain expertise apply even in areas not explicitly covered. The absence of a principle doesn't mean the absence of a standard."

3. **Reserved Powers (10th Amendment)** — Strengthens *Authority* branch by clarifying silence
   - **Recommend: Amendment V** in the Bill of Rights (the 10th Amendment IS part of the Bill of Rights)
   - **Content:** "Where the constitution is silent, domains have authority to establish their own standards appropriate to their subject area."
   - Pairs with the Supremacy Clause: supremacy handles conflicts, reserved powers handle silence

4. **Full Faith and Credit** — Fills genuine gap in *Relations* branch (contrarian-verified: no existing mechanism)
   - **New meta-method** in rules-of-procedure, Title 9 after cross-domain sections
   - **Method ID:** `meta-method-full-faith-credit`
   - **Content:** "Outputs validated under one domain's governance are recognized as valid inputs by other domains. Re-validation under a second domain's standards is not required unless the output falls within that domain's specific quality gates."

**3B: Admission Test Update — Question 0: Purpose Alignment**

Add to the existing 6-question Admission Test at Part 9.8.1 in rules-of-procedure:

> **Question 0 — Purpose Alignment:** Does this content serve one or more of the purposes stated in the Preamble? Which one(s)? If the content cannot cite a specific Preamble purpose it serves, it fails the admission test regardless of other criteria.

This is the enforcement mechanism for the Preamble's stated purposes. The Preamble defines WHAT the purposes are; the Admission Test enforces them. No new operative layer needed. (See D6 for full rationale.)

**Cascading updates required:** Adding Q0 changes the Admission Test from 6 to 7 questions. Update in this phase (not deferred to Phase 5):
- Part 9.8.1 header: "6 Questions" → "7 Questions"
- Opening sentence: "Six binary questions" → "Seven binary questions"
- All "all 6 questions" references within Part 9.8 → "all 7 questions"
- Any forward references in Title 8 that cite "6-question Admission Test"

**3C: Surgical Edits to Existing Sections (2 items — not new content, just explicit naming)**

5. **Equal Protection** — Already covered by `Bias Awareness & Fairness (Amendment II)` for output bias. Cross-domain equal application is covered by Part 9.7/9.8 templates but not named.
   - **Add one sentence to Part 9.7:** "Constitutional principles and methods must apply equally across all domains. If a method cannot be applied to a domain without modification, the method may be domain-biased and should be evaluated for generality."

6. **Impeachment (Emergency Removal)** — Breaking changes protocol (Part 9.6.3) covers planned removal. No documented fast-path for emergency removal of actively harmful principles.
   - **Add one paragraph to Part 9.6.3:** Emergency removal fast-path for principles demonstrating active harm — skip multi-step deprecation, require documented "charges" (demonstrated harm evidence) and "conviction" (human authorization), followed by post-removal audit.

**3D: Cleanly Cut (2 items — structurally enforced, naming adds no value)**

7. ~~**Separation of Powers**~~ — Already structurally enforced by Article I (Legislative/C), Article II (Executive/O), Article III (Judicial/Q), Article IV (Administrative/G). Part 8.5 Override Protocols explicitly enforces separation. Documented in Declaration's five root purposes and Preamble prose. No new content needed.

8. ~~**Right to Petition**~~ — Already covered by Part 7.11 (Discovered Issue Triage), S-Series escalation, and the constitutional amendment process. The *spirit* of petition is the default behavior when scope is ambiguous. No new content needed.

**Files modified:**
- Constitution — Amendments IV-V (if approved as Bill of Rights additions)
- Rules-of-procedure — 2 new methods (Elastic Clause, Full Faith and Credit) + 2 surgical edits (Equal Protection sentence in §9.7, Impeachment paragraph in §9.6.3)

**Test impact:** Medium.
- If Amendments IV-V added: principle count changes (22 → 24), S-Series count changes (3 → 5). Tests asserting S-Series count=3 need updating to count=5. Safety detection (`series_code == "S"`) will work automatically — new amendments inherit "safety" category from the Bill of Rights section.
- 2 new methods: method count changes
- Admission Test references: "6 Questions" → "7 Questions" (see 3B cascading updates)
- Rebuild index

#### Review Gate 3: Constitutional Concepts + Admission Test
**Stop and present to user before proceeding to Phase 4.**

Review checklist:
- [ ] Read the Elastic Clause method — is "derive from intent + document + flag for review" practical?
- [ ] Amendments IV-V (Unenumerated Rights, Reserved Powers) — confirm they belong in the Bill of Rights, not as methods
- [ ] Full Faith and Credit — does the cross-domain recognition rule make sense operationally?
- [ ] Equal Protection sentence in Part 9.7 — sufficient coverage?
- [ ] Impeachment paragraph in Part 9.6.3 — is the emergency fast-path clear enough?
- [ ] **Admission Test Question 0** — read it in context of the full Admission Test. Does it reference the Preamble's purposes clearly? Is it binary enough (pass/fail) to prevent rubber-stamping?
- [ ] Run `evaluate_governance("novel situation with no matching principle")` — does the Elastic Clause influence the response?

---

### Phase 4: Rename Files + Domain Restructuring
**Scope: Large | Risk: High | ~4-5 hours**

Rename all document files to Constitutional naming. This is the second highest-risk phase because filenames are referenced in domains.json, code, tests, and cross-references.

**4A: Rename Constitution files**
- `ai-interaction-principles.md` → `constitution.md`
- `ai-governance-methods.md` → `rules-of-procedure.md`

**4B: Rename domain files to Title-based naming**
- `ai-coding-domain-principles.md` → `title-10-ai-coding.md`
- `ai-coding-methods.md` → `title-10-ai-coding-cfr.md`
- `ui-ux-domain-principles.md` → `title-15-ui-ux.md`
- `ui-ux-methods.md` → `title-15-ui-ux-cfr.md`
- `multi-agent-domain-principles.md` → `title-20-multi-agent.md`
- `multi-agent-methods.md` → `title-20-multi-agent-cfr.md`
- `kmpd-domain-principles.md` → `title-25-kmpd.md`
- `kmpd-methods.md` → `title-25-kmpd-cfr.md`
- `storytelling-domain-principles.md` → `title-30-storytelling.md`
- `storytelling-methods.md` → `title-30-storytelling-cfr.md`
- `multimodal-rag-domain-principles.md` → `title-40-multimodal-rag.md`
- `multimodal-rag-methods.md` → `title-40-multimodal-rag-cfr.md`

**4C: Update `documents/domains.json`**
```json
{
  "constitution": {
    "principles_file": "constitution.md",
    "methods_file": "rules-of-procedure.md",
    ...
  },
  "ai-coding": {
    "principles_file": "title-10-ai-coding.md",
    "methods_file": "title-10-ai-coding-cfr.md",
    ...
  },
  // ... all 7 domains
}
```

**4D: Update code references**
- `src/ai_governance_mcp/config.py` — `_default_domains()` fallback filenames (line ~289-299)
- `documents/ai-instructions.md` — references to constitution filename (line 18)
- Any other code that hardcodes document filenames

**4E: Update `governance_level` YAML frontmatter** in renamed files:
- `constitution.md`: `governance_level: "constitution"` (unchanged)
- `rules-of-procedure.md`: `governance_level: "rules-of-procedure"`
- Domain files: `governance_level: "federal-statute"` (was "domain-principles")
- Domain methods: `governance_level: "federal-regulations"` (was "domain-methods")

**4F: Update domain internal structure** (if time permits, otherwise Phase 5)

Inside each domain file, update series headers to Chapter/Section format:
```markdown
## Chapter 1: Context Statutes (C-Series)
### T.10, § 1: Specification Completeness
```

Add `constitutional_ref` (e.g., `T.10, § 1`) to domain principle extraction in extractor.py. **Extend the title-stripping regex** to handle `T.NN, § N:` prefixes (the second stage described in D5). This is separate from Phase 2C's constitution-only regex.

**4G: Grep and update all cross-references**

Run grep for every old filename across all markdown files and update:
```
ai-interaction-principles.md → constitution.md
ai-governance-methods.md → rules-of-procedure.md
ai-coding-domain-principles.md → title-10-ai-coding.md
...
```

Also update: `README.md`, `ARCHITECTURE.md`, `API.md`, `SPECIFICATION.md`, `CLAUDE.md`, `SESSION-STATE.md`, all domain `.md` files, all agent definitions.

**Files modified:**
- 14 document files renamed
- `documents/domains.json`
- `src/ai_governance_mcp/config.py`
- `documents/ai-instructions.md`
- `README.md`, `ARCHITECTURE.md`, `API.md`, `SPECIFICATION.md`, `CLAUDE.md`
- All domain `.md` files (cross-references)
- `documents/agents/*.md`
- Potentially test fixtures

**Test impact: HIGH.**
- Grep for all old filenames in `tests/`: `ai-interaction-principles`, `ai-governance-methods`, `ai-coding-domain-principles`, etc.
- Update `tests/test_config.py`, `tests/test_extractor.py`, `tests/test_extractor_integration.py`
- Update any mock `domains.json` in test fixtures
- Rebuild index after all renames

**Risk mitigation:**
- **Two commits, not one:** Commit 1 = `git mv` renames + `domains.json` + `config.py` (git tracks renames cleanly). Commit 2 = cross-reference updates in all markdown + test fixtures. This gives a clean revert boundary — if cross-ref grep misses something, revert commit 2 without losing the renames.
- The extractor's `validate_domain_files()` will fail-fast if any file reference is missed
- Run `grep -r "ai-interaction-principles\|ai-governance-methods\|domain-principles\|coding-methods\|multi-agent-methods\|storytelling-methods\|multimodal-rag-methods\|ui-ux-methods\|kmpd-methods" .` after rename to catch stragglers
- **Test fixtures:** Update `governance_level` values in test fixtures (at least `test_extractor.py` line ~1190 uses `governance_level`). Add to test impact checklist.

#### Review Gate 4: File Structure + Domain Naming
**Stop and present to user before proceeding to Phase 5.**

Review checklist:
- [ ] `ls documents/` — does the new file listing look right? Does `title-10-ai-coding.md` alongside `constitution.md` and `rules-of-procedure.md` tell a coherent story?
- [ ] Spot-check one domain file (e.g., AI Coding) — does the Chapter/Section format work inside domain files?
- [ ] Check `domains.json` — all entries resolve to correct new filenames?
- [ ] Run `list_domains` via MCP — all 7 domains load?
- [ ] Run `query_governance("AI coding specification completeness")` — does the domain principle come back with a `T.10, § N` citation?
- [ ] Run full test suite — all passing after renames?
- [ ] **Gut check:** Browse the `documents/` directory. Does it feel organized? Would a new user understand the structure?

---

### Phase 5: Cross-References, Documentation & Polish
**Scope: Medium | Risk: Low | ~2-3 hours**

1. **Update the Supremacy Clause** (Part 9.7.4 in rules-of-procedure.md):
   - Replace `Bill of Rights > Constitution > Statutes > Regulations > SOPs` with full named hierarchy
   - Reference Articles by number: `Bill of Rights (Amendments) > Articles I-IV > Federal Statutes (Titles) > Federal Regulations (CFR) > Agency SOPs`

2. **Update the Level Classification Procedure** (Part 9.7.2):
   - Replace "Step 1: Safety Check → Level 1" with "Step 1: Safety Check → Bill of Rights (Amendment)"
   - Replace all "Level N" references with Constitutional element names
   - Add "Step 0: Purpose/Foundation → Declaration/Preamble" for foundational content

3. **Update the Derivation Principle** (Part 9.7.3):
   - Replace `Constitution (Level 2)` tree with `Article I` tree using Constitutional references

4. **Update all domain files' hierarchy references** — any domain file that mentions "Level 3" or "Federal Statutes" should use consistent Constitutional naming

5. **Update `ARCHITECTURE.md`** — system structure diagram, component descriptions

6. **Update `README.md`** — document structure listing, setup instructions

7. **Curate domain descriptions in `domains.json`** (from v4 action item #5 — the keyword walls)

8. **Run coherence audit** (per Part 4.3) across all files for consistency

**Files modified:**
- `documents/rules-of-procedure.md` (multiple sections)
- All domain `.md` files (hierarchy references)
- `README.md`, `ARCHITECTURE.md`
- `documents/domains.json` (descriptions)

**Test impact:** Minimal. Documentation changes don't affect code tests.

**No review gate** — Phase 5 is polish work. Phase 6 has the final review.

---

### Phase 6: Verify, Version & Release
**Scope: Small | Risk: Low | ~1-2 hours**

1. **Full test suite** — all tests must pass (`pytest tests/ -v`)
2. **Rebuild index** — run extractor, verify principle/method counts
3. **Verify Constitutional citations** — spot-check that `constitutional_ref` fields are correct
4. **Coherence audit** — subagent review for cross-reference consistency
5. **Version bumps:**
   - `constitution.md`: v3.0.0 → **v4.0.0** (major: structural restructuring)
   - `rules-of-procedure.md`: v3.23.2 → **v4.0.0** (major: rename + new methods)
   - All domain files: **minor bump** (structural framing change, content preserved)
   - `pyproject.toml` / server version: v1.8.0 → **v2.0.0** (major: document restructuring)
6. **Update SESSION-STATE.md** — new Current Position, version table
7. **Populate migration tracking** — `documents/migration/constitutional-alignment.md` with summary
8. **Update LEARNING-LOG.md** — capture lessons from the restructuring
9. **Git tag:** `v2.0.0` — Constitutional Alignment Release

**Test commands:**
```bash
pytest tests/ -v                    # Full suite
pytest tests/ -v --tb=short -q      # Quick check
pytest --cov src/ai_governance_mcp  # Coverage
```

#### Review Gate 5: Final Release Review
**Stop and present to user before tagging v2.0.0.**

Review checklist:
- [ ] Full test suite green
- [ ] Browse `constitution.md` top to bottom — Declaration → Preamble → Articles → Amendments. Reads as a coherent document?
- [ ] Browse one domain file top to bottom — Title/Chapter/Section structure works?
- [ ] `query_governance` returns Constitutional citations correctly
- [ ] `evaluate_governance` still triggers S-Series (Bill of Rights) veto on safety issues
- [ ] `list_domains` shows all 7 domains with new filenames and curated descriptions
- [ ] README accurately describes the new structure
- [ ] **Ship/no-ship decision:** Ready to tag v2.0.0?

---

## Summary

| Phase | Scope | Risk | Core Change | Review Gate |
|-------|-------|------|-------------|-------------|
| 0 | Small | Minimal | Safety net — tag, archive, migration doc | — |
| 1 | Medium | Low | Declaration (incl. five root purposes) + Preamble + Framework Structure | **Gate 1:** Review tone, framing, naming |
| 2 | **Large** | **High** | Articles/Amendments structure + dual-layer IDs | **Gate 2:** THE critical review — structure + citations |
| 3 | Medium | Medium | 4 additions + Admission Test Q0 + 2 surgical edits | **Gate 3:** Review concepts + Admission Test |
| 4 | **Large** | **High** | Rename all 14 files to Constitutional names | **Gate 4:** File structure + domain naming |
| 5 | Medium | Low | Cross-references + documentation polish | — |
| 6 | Small | Low | Verify + version v4.0.0/v2.0.0 + release | **Gate 5:** Final ship/no-ship decision |

**Total estimated effort:** ~16-23 hours across multiple sessions (plus review gate time between phases). Each phase is a natural stopping point.

## Open Questions for Implementation

1. **Amendments IV-V:** Recommendation is Amendments (Bill of Rights) since 9th and 10th are part of the actual Bill of Rights. Confirm at Review Gate 3.
2. **Domain internal restructuring (Phase 4F):** Should domain series headers become `Chapter N: [Topic] (X-Series)` with `§ N:` principle numbering in the first pass, or defer to a follow-up PR?
3. **Methods file (rules-of-procedure.md) internal structure:** It already uses TITLE/Part numbering. Should these become more explicitly "Title N" or stay as "TITLE N" (they're already aligned)?
4. **Five root purposes placement in Declaration:** Exact format TBD — clean table? Prose with inline mapping? Confirm at Review Gate 1.

## Verification Plan

After all phases:
1. `pytest tests/ -v` — all 1125+ tests pass
2. Rebuild index — verify principle count (22 + 2 Amendments = 24), method count (672 + 2 new methods)
3. `query_governance("context engineering")` — returns `Art. I, § 1` citation + correct slug ID
4. `evaluate_governance("test action")` — S-Series (Bill of Rights) detection still works
5. `list_domains` — all 7 domains resolve with new filenames
6. Coherence audit subagent — cross-references consistent
7. Contrarian review subagent — final review of structural alignment
