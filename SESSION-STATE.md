# Session State

**Last Updated:** 2026-01-17

## Current Position

- **Phase:** Released (v1.6.0)
- **Mode:** Standard
- **Active Task:** None
- **Blocker:** None

## Recent Work (This Session)

### Method Retrieval Quality Improvement ✓ RESOLVED

**Problem:** Method "Advanced Model Considerations" had low semantic similarity (0.28) compared to principles (0.46+).

**Root Causes Identified:**
1. `all-MiniLM-L6-v2` has 256 token max — content truncated
2. Methods get minimal embedding: `title + content[:500]` only
3. Methods have NO metadata (principles get keywords, trigger_phrases, etc.)

**Solution Implemented:**
1. **Model Upgrade:** `all-MiniLM-L6-v2` → `BAAI/bge-small-en-v1.5` (512 tokens, better quality)
2. **MethodMetadata Model:** Added rich metadata extraction for methods (keywords, trigger_phrases, purpose_keywords, applies_to, guideline_keywords)
3. **Text Limit Increase:** Embedding text increased from 500→1500 chars for methods, 1000→1500 for principles
4. **BM25 Enhancement:** Methods now include metadata fields in keyword search

**Results (Benchmark Tests):**
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Method MRR | 0.34 | **0.72** | +112% |
| Principle MRR | 0.42 | **0.61** | +45% |
| Method Recall@10 | 0.50 | **0.88** | +76% |
| Principle Recall@10 | 0.50 | **1.00** | +100% |

**Key Problem Case (Advanced Model Considerations):**
| Metric | Before | After |
|--------|--------|-------|
| Semantic Score | 0.54 | **0.82** |
| Combined Score | 0.72 | **0.89** |

**Files Changed:**
- `src/ai_governance_mcp/config.py` — New embedding model default
- `src/ai_governance_mcp/models.py` — Added MethodMetadata class
- `src/ai_governance_mcp/extractor.py` — `_generate_method_metadata()`, `_get_method_embedding_text()`, increased limits
- `src/ai_governance_mcp/retrieval.py` — `_get_method_bm25_text()` with metadata
- `tests/benchmarks/` — New quality benchmark infrastructure
- `tests/test_retrieval_quality.py` — MRR, Recall@K metrics
- Updated test references to new embedding model

**All 337 tests passing.**

### v1.6.0 Released

- **GitHub:** Tag `v1.6.0` created and pushed
- **Release:** https://github.com/jason21wc/ai-governance-mcp/releases/tag/v1.6.0
- **Docker Hub:** `jason21wc/ai-governance-mcp:1.6.0` and `:latest` pushed
- **Note:** MCP server restart required to load new index with BGE model

---

### Previous: Index Verification Investigation (led to above fix)

---

## Previous Work

### Advanced Model Considerations (multi-agent-methods v2.9.0)

**Source:** @EXM7777 prompt engineering thread (X.com), validated against research

**Analysis Process:**
- Evaluated practitioner claims against academic research
- Confirmed Sonnet 4.5 contextual evaluation behavior ([The Agent Architect](https://theagentarchitect.substack.com/p/claude-sonnet-4-prompts-stopped-working), [Mikhail Shilkov](https://mikhail.io/2025/09/sonnet-4-5-system-prompt-changes/))
- Found arXiv paper on "Guardrail-to-Handcuff" transition in advanced models
- Applied contrarian-reviewer to challenge proposed changes
- Scoped changes as addendum (model-tier specific), not replacement

**New Section Added (§2.1.5 Advanced Model Considerations):**
- **Guideline 1:** Decision rules over prohibitions (except S-Series safety)
- **Guideline 2:** Cognitive function over role-play framing
- **Guideline 3:** Calibrate constraint density (sandwich method nuance)
- **Guideline 4:** Trust but verify pattern

**Files Changed:**
- `documents/multi-agent-methods-v2.8.0.md` → `multi-agent-methods-v2.9.0.md` (renamed + ~75 lines added)
- `documents/domains.json` (updated path reference and description)
- `SESSION-STATE.md` (this update)

**Key Insight:** Advanced models (Sonnet 4.5+) evaluate contextual necessity rather than following instructions literally. This requires adapted prompting strategies, but S-Series safety constraints should retain prescriptive language.

**Review Date:** Re-evaluate guidance after July 2026.

**Retrieval Note:** ~~Content was combined into parent sections~~ **FIXED** — Extractor now splits #### subsections into separate indexed methods. multi-agent methods: 24 → 43. Index rebuilt on disk. **Requires MCP server restart to load new index into memory.**

### Evaluation Methods Enhancement (multi-agent-methods v2.8.0)

**Source:** Anthropic Engineering "Demystifying Evals for AI Agents" (2025)

**Analysis Process:**
- Applied Anchor Bias Mitigation Protocol (4-step re-evaluation)
- Used contrarian-reviewer subagent to challenge assumptions
- Compared article concepts against existing 4-layer evaluation framework
- Initial analysis focused only on principles; user feedback redirected to methods perspective
- Identified genuine gaps at methods level (not principles)

**New Sections Added (§4.7.1-4.7.4):**
1. **§4.7.1 Grader Types** — Code-Based, Model-Based, Human selection guidance with strengths/weaknesses table
2. **§4.7.2 Non-Determinism Measurement** — pass@k (capability) and pass^k (reliability) formulas with target thresholds
3. **§4.7.3 Capability vs Regression Evals** — When to use each, metrics differences, workflow integration
4. **§4.7.4 Grader Design Principles** — Grade outcomes not paths, partial credit, multi-shot grading

**Files Changed:**
- `documents/multi-agent-methods-v2.7.0.md` → `multi-agent-methods-v2.8.0.md` (renamed + ~270 lines added)
- `documents/domains.json` (updated path reference)
- `index/` (rebuilt)

**Key Insight:** Existing 4-layer framework (Component/Trajectory/Outcome/System) was at the right abstraction level, but lacked specific grader implementation guidance that practitioners need.

**Testing Note:** After rebuilding the index, discovered MCP server caches the index in memory at startup. The disk index is correct (verified: line range [2658, 3083], includes all new sections), but queries won't return new content until server restart.

## Previous Session

### Storytelling Domain Promoted to Production

**Changes:**
- Moved `drafts/storytelling-domain-principles-v0.2.0.md` → `storytelling-domain-principles-v1.0.0.md`
- Moved `drafts/storytelling-context-management-method-v0.2.0.md` → `storytelling-methods-v1.0.0.md`
- Updated domains.json with new paths
- Updated version numbers and changelogs (v0.2.0 → v1.0.0)
- Removed DRAFT designation
- Rebuilt index (87 principles + 300 methods = 387 total)

### Comprehensive Document Review

**Scope:** Full review of all cognitive memory documents for obsolete info, structure compliance, and cross-document consistency.

**Documents Reviewed:**
- CLAUDE.md — ✓ Structure correct, test count accurate (337)
- SESSION-STATE.md — ✓ Structure correct
- PROJECT-MEMORY.md — Fixed test count inconsistencies (205 → 337)
- LEARNING-LOG.md — ✓ No pruning needed (102KB but valuable episodic memory)
- Storytelling domain documents — ✓ Both properly structured

**Issues Found & Fixed:**
| Document | Issue | Resolution |
|----------|-------|------------|
| PROJECT-MEMORY.md Line 21 | Phase gate said "205 tests" | Updated to "337 tests" |
| PROJECT-MEMORY.md Line 715 | "TEST — 205 tests passing" | Updated to "337 tests" |

**Cross-Document Consistency Verified:**
- Version: 1.4.1 (pyproject.toml, __init__.py, SESSION-STATE.md) ✓
- Test count: 337 (CLAUDE.md, SESSION-STATE.md, PROJECT-MEMORY.md) ✓
- Tool count: 11 (consistent across docs) ✓
- Domain count: 4 (domains.json, SESSION-STATE.md) ✓

**Note:** User mentioned "aboutme.md" but no such file exists in this project.

### Previous Session: Storytelling Domain v0.2.0 (Draft)

**New domain for creative writing and narrative development:**

**Principles (17):**
- **Safety (E-Series):** E1 Human Voice Preservation, E2 Persuasion-Manipulation Boundary
- **Architecture (A-Series):** A1 Audience Discovery First, A2 Cultural Context Awareness, A3 Accessibility
- **Context (C-Series):** C1-C5 (Hook Variation, Show-Tell Balance, Pacing, Emotional Honesty, Dialogue Craft)
- **General (ST/M-Series):** ST1-ST5, M1-M4 (Stakes, Perspective, Platform, Format, Resolution)

**Methods (20):**
- Story Bible architecture (3-tier memory model)
- Context loading protocol for long narratives
- Non-linear writing protocol (fragment tracking, assembly)
- Revision management and auto-tracking
- Voice preservation integration
- Platform-specific adaptations

**Testing Results:**
- Domain routing: Working (enhanced description for genres, world-building terms)
- Principle retrieval: HIGH confidence on core queries
- Method retrieval: HIGH confidence on protocol queries
- All 337 tests passing

**Files:**
- `documents/drafts/storytelling-domain-principles-v0.2.0.md`
- `documents/drafts/storytelling-context-management-method-v0.2.0.md`
- `documents/domains.json` (storytelling domain added)

**Commit:** `093778a feat(storytelling): Add storytelling domain with 17 principles and 20 methods`

### Coaching Mode Guidance

**Issue:** Domain mentioned "coaching" in scope but lacked guidance on WHEN to coach vs generate, and HOW to coach through questions.

**Research conducted:**
- Khan Academy Writing Coach ("guides without writing a word for them")
- Jennifer Lewy's reflective questioning approach
- Socratic method for discovery learning
- Contrarian review to challenge assumptions

**Changes to storytelling-domain-principles-v0.2.0.md:**
1. **ST-F13: Premature Generation** — New failure mode for AI generating when coaching would serve better
2. **Mode Selection guidance** — Decision table for Generate vs Coach based on user signals
3. **Enhanced coaching section** — References Progressive Inquiry Protocol, adds question examples
4. **Planned Methods** — Added "Storytelling coaching playbook" for future development

**Key insight:** The real gap wasn't questioning technique (Progressive Inquiry Protocol exists) — it was mode selection.

**Commit:** `4f876d8 feat(storytelling): Add coaching mode guidance for questions over generation`

### Also This Session

- **LEARNING-LOG.md:** Added prompt repetition research evaluation (decided NOT to incorporate - 78% no benefit for reasoning models)

## Previous Session

### v1.4.1 - Progressive Inquiry Protocol Enhancement

**Issue:** AI defaulting to structured selection UI for Foundation/Branching tier questions.

**Changes to Constitution:**
1. Clarified Format by Tier with "and Branching" + "(conversational dialogue)"
2. Added "The Structured Selection Trap" failure mode

### v1.4.0 - Anchor Bias Mitigation

- New principle: "Periodic Re-evaluation" (C-Series)
- New method: Part 7.10 "Anchor Bias Mitigation Protocol"
- Contrarian reviewer updated with Step 6: "Check for Anchor Bias"

## Quick Reference

| Metric | Value |
|--------|-------|
| Version | **v1.6.0** (server), **v2.3** (Constitution), **v3.7.0** (governance-methods), **v2.9.0** (multi-agent-methods) |
| Tests | **337 passing** |
| Coverage | ~90% |
| Tools | **11 MCP tools** |
| Domains | **4** (constitution, ai-coding, multi-agent, storytelling) |
| Index | **87 principles + 319 methods (406 total)** |

## Next Actions

1. ~~Promote storytelling from drafts to production~~ ✓ Done (v1.0.0)
2. ~~Investigate X.com post (EXM7777/status/2011800604709175808)~~ ✓ Done (v2.9.0)
3. Optional: Develop storytelling coaching playbook (question taxonomies, Socratic patterns)
4. Optional: Add platform-specific playbooks (TikTok, LinkedIn, long-form)

## Links

- **GitHub:** https://github.com/jason21wc/ai-governance-mcp
- **Docker Hub:** https://hub.docker.com/r/jason21wc/ai-governance-mcp
