# 01 — Phase 1: Structural Review

**Sections (populated progressively):**
- §A — As-Derived Mapping (Step 3)
- §B — Memory & Reference Classification (Step 4)
- §C — Declared-vs-Derived Comparison (Step 5)
- §D — Phase 1 Findings (Step 6)

---

## §B — Memory & Reference Classification (Step 4)

### §B.1 — Template vs Instance Split

The framework ships **templates** for memory files (embedded in `src/ai_governance_mcp/server.py` at SCAFFOLD_CORE_FILES and SCAFFOLD_STANDARD_EXTRAS) and **instances** of those same files exist in each adopting project (including this framework repo itself — root-level `SESSION-STATE.md` etc.).

| File | Template (governance-artifact) | Instance (project-artifact) | Scaffolded? | Notes |
|---|---|---|---|---|
| SESSION-STATE.md | `SCAFFOLD_SESSION_STATE` in server.py | this repo's root `SESSION-STATE.md` (148 lines) | YES (code + document kits) | Per-session current-work tracker |
| PROJECT-MEMORY.md | `SCAFFOLD_PROJECT_MEMORY` | this repo's `PROJECT-MEMORY.md` (683 lines) | YES | Cross-session binding decisions + ADRs |
| LEARNING-LOG.md | `SCAFFOLD_LEARNING_LOG` | this repo's `LEARNING-LOG.md` (512 lines, lessons + Graduated Patterns table) | YES | Lessons from mistakes + promotion-tracking |
| AGENTS.md | `SCAFFOLD_AGENTS_MD` | this repo's root `AGENTS.md` (57 lines) | YES (code kit only) | Framework context for agents |
| `_ai-context/README.md` | `SCAFFOLD_AI_CONTEXT_README` | n/a here (code project) | YES (document kit only) | Readme for document-project context dir |
| CLAUDE.md | `SCAFFOLD_CLAUDE_MD` | this repo's `CLAUDE.md` (78 lines) | standard-kit only | Behavioral floor + hook rules |
| COMPLETION-CHECKLIST.md | `SCAFFOLD_COMPLETION_CHECKLIST` | `workflows/COMPLETION-CHECKLIST.md` (186 lines) | standard-kit only | Post-change sequence |
| **BACKLOG.md** | **NO TEMPLATE** | this repo's root `BACKLOG.md` (620 lines) | NO | **Project-artifact only. Structural asymmetry: the framework uses BACKLOG heavily (620 lines) but does not scaffold one for adopters.** |

### §B.2 — Reference Library Classification

| Artifact | Classification | Notes |
|---|---|---|
| `reference-library/` directory structure | governance-artifact | Ships with framework; not copied into consumer projects. Consumers access via MCP retrieval. |
| `reference-library/ai-coding/_criteria.yaml` | governance-artifact | 4 auto-capture + 4 suggestion rules. Ai-coding only — 5 other domains have no admission criteria. |
| `reference-library/ai-coding/ref-*.md` (13 entries) | governance-artifact | Accreted patterns. Each has maturity (`evergreen`, `current`) + decay class. |
| `reference-library/ai-coding/staging/` | governance-artifact (ingestion buffer) | Pending-review entries before maturity promotion. |
| Other domains (ui-ux, multi-agent, kmpd, storytelling, multimodal-rag) | **missing** | Zero reference entries or criteria. |

### §B.3 — Promotion Pathway

**Observed promotion structure (from LEARNING-LOG.md "Graduated Patterns" table lines 474–513, 30+ entries):**

```
Instance artifact (project)       Framework artifact (governance)
────────────────────────          ──────────────────────────────
LEARNING-LOG entry          ───►  · principle (constitution.md)
  in adopting project              · method (domain CFR §X.Y)
                                   · ARCHITECTURE.md section
                                   · Gotcha entry (PROJECT-MEMORY)
                                   · reference-library entry

PROJECT-MEMORY ADR          ───►  · principle (if constitutional-grade)
                                   · method (if procedural)

reference-library entry     ───►  (rarely further graduated; it IS the terminal
                                   form for secondary authority)
```

**Promotion signals observed in LEARNING-LOG:**
- "Graduated to §X.Y" marker (existing convention)
- `meta-methods Part 7.10` referenced as graduation discipline
- Manual curation — no automated trigger

**Gaps in the promotion pathway:**
1. **No reverse pathway.** Principles never de-graduate back to methods even when evidence weakens them. The LEARNING-LOG:185-192 "Multi-Mechanism Context Degradation Model" entry CORRECTS a prior single-mechanism framing, but the correction is done *in LEARNING-LOG* rather than amending the principles that relied on the earlier framing. That is amendment-by-commentary, not amendment-by-rule-change.
2. **No LEARNING-LOG → reference-library automation.** The `_criteria.yaml` defines auto-capture rules, but only for the ai-coding domain, and the hook wiring for applying them is not visible in scaffold templates or server.py tool dispatch.
3. **Cross-project promotion is manually mediated.** A consumer project's LEARNING-LOG cannot feed back into the framework except via the human sending a PR. No mechanism for aggregated lesson submission. For a framework that governs agents at scale, this is a single-user bottleneck on the promotion pipeline.
4. **Reference-library only exists for 1 of 6 domains**, so the pathway `LEARNING-LOG → reference-library` is functional only within ai-coding. For other domains, LEARNING-LOG entries must skip the "secondary authority" stage and be promoted directly to principle or method, which is a higher bar than the pathway design implies.

### §B.4 — Classification Consequences

- **Instances are project state, not framework content**, so changes to them in the framework's own repo are project-evolution data (for Step 10 miss-check) but not framework amendments.
- **Templates are framework content**, so changes to `SCAFFOLD_*` strings in server.py are framework amendments and should have amendment history (they do not — covered by gap C4 in §A.3).
- **BACKLOG.md asymmetry** (620-line instance here, zero template for adopters) means the framework relies on a file-class it doesn't propagate. Either the file class is only useful for the framework's own dev (in which case the asymmetry is fine) or the framework under-provisions adopters (in which case it's a gap). Flagged for Phase 2 review.

---

## §A — As-Derived Mapping (Step 3)

**Method:** Derived independently from §1 (99-appendix-inventory.md §1, US Constitution Framework) against §2 (Artifact Inventory). Mappings assigned by *operational function*, not name-match. Ambiguous cases list all candidates. Contrarian-reviewer subsequently challenged every mapping marked "clean" (§A.2).

### §A.1 — Draft Mapping (pre-contrarian)

| Artifact (from §2) | Best §1 analog by operational function | Secondary candidates | Tag | Reasoning (one line) |
|---|---|---|---|---|
| A — `constitution.md` | **Split: S-Series → §1.4 Bill of Rights; C/O/Q/G → §1.3 Articles I–VII** | — | **multi-analog / blur** | One file carries two §1 analogs (vetoes + structural rules). In US framework these are separate artifacts. |
| B — `rules-of-procedure.md` | **§1.3 Articles + §1.5 Amendment Clause (Article V) + §1.11 Executive Orders** | — | **multi-analog / blur** | Conflates authoring rules, amendment process, and session-procedure SOP in one file. |
| C — Domain principles (`title-NN.md`) | **§1.6 Federal Statutes** | — | clean | Domain-specific binding conduct rules that must comply with constitution. |
| D — Domain CFR (`title-NN-cfr.md`) | **§1.7 CFR** | — | clean | Procedural/methods translation of statutes — matches operational function exactly. |
| E — `ai-instructions.md` | (no direct analog) | §1.11 Executive Orders (boot-sequencing directive) | loose-end | Runtime boot-loader; not a rule-bearing layer. |
| F — `domains.json` | (infrastructure, no analog) | statutory-compilation index (Title/Chapter numbering) | loose-end | Configuration lookup, not governance content. |
| G — `tiers.json` | (infrastructure, no analog) | — | loose-end | Floor-selection *mechanism*, not content. The S-Series is the content; tiers.json picks when to apply it. |
| H — Subagents (canonical `documents/agents/`) | **§1.12 Subordinate Jurisdictions** | §1.11 Executive Orders (scoped directive) | ambiguous | Each agent has own protocol + scope, but is bound by framework — matches subordinate jurisdiction. Alternative: executive-order-with-delegation. |
| I — Subagents (deployed `.claude/agents/`) | same as H — installed copy | — | same | Byte-matched mirror. |
| J — `COMPLETION-CHECKLIST.md` | **§1.11 Executive Orders** | §1.3 Articles (procedural rules) | ambiguous | Operational sequencing directive triggered by phrase. |
| K — `COMPLIANCE-REVIEW.md` | **§1.13 Judicial Review (scheduled variant)** | §1.11 Executive Orders | ambiguous | Meta-enforcement: periodically audits whether framework is functioning. Differs from US judicial review in being scheduled, not case-triggered. |
| L — Reference library | **§1.8 Case Law / precedent** | *Secondary authority* (Restatements, ALR) — non-binding | ambiguous | Accreted applied patterns. But: advisory, not binding → may be secondary authority rather than primary precedent. |
| L' — `_criteria.yaml` (missing/empty) | would-be §1.8-admission criteria | — | **GAP** | Admission/maturity criteria for case-law-equivalent are undefined. |
| M — Scaffold templates (embedded in server.py) | **Subordinate-jurisdiction charter template** | — | loose-end / infrastructure | Blueprint for creating lower jurisdictions (consumer projects). |
| N — Project memory instances (`SESSION-STATE` etc.) | **§1.10 Congressional Record** | — | clean | Contemporaneous operational record. |
| O — `CLAUDE.md` / `AGENTS.md` | §1.2 Preamble (for this project) + §1.11 Executive Orders (skip list, hook rule) | — | ambiguous | Project-level Preamble-plus-operating-directive. |
| P — README / ARCHITECTURE / API / SPECIFICATION / SBOM / SECURITY | **§1.9 Federalist Papers (design commentary)** — for ARCHITECTURE/SPECIFICATION/README; *not a §1 analog* for SBOM/SECURITY | — | mixed | Reviewer/external-audience explanatory docs. SBOM & SECURITY = supply-chain / incident-response policies, no §1 analog. |
| Q — `LICENSE` / `LICENSE-CONTENT` | (no §1 analog) | — | infrastructure | External legal instrument governing distribution, not internal behavior. |
| R — Enforcement hooks | **§1.13 Judicial Review (preventive variant)** | §1.11 Executive Orders (runtime directive) | ambiguous | Preventive, pre-action; differs from US judicial review (reactive, case-triggered). Closer to *clerk-level procedural gatekeeping* in functional terms. |
| S — scripts/ | (no analog) | — | infrastructure | Operator tools. |
| T — `src/ai_governance_mcp/` | (no analog) | — | infrastructure | Implementation of the governance *mechanism* itself. |
| U — Test suite | **§1.13 Judicial Review (binding self-test)** + §1.6 Federal Statutes (of-the-code) | — | ambiguous | Dual: audits framework claims *and* binds code via CI. |
| V — Drift baselines | (no analog) | "contemporaneous record" (§1.10-like) | infrastructure | Daily surveillance data. |
| W — CI workflows | **§1.13 Judicial Review (at PR level)** | §1.11 Executive Orders | ambiguous | Automated enforcement directives. |
| X/Y — Archive / Migration | (weak §1.10 analog) | — | infrastructure | Historical record of framework evolution. |
| Z — Examples | (no analog) | — | infrastructure | Tutorials for downstream jurisdictions. |
| AA — Staging | n/a — not governance | — | n/a | Scratch. |
| AB — Reviews (this) | **§1.13 Judicial Review (output artifact)** | — | clean | Self-audit output. |

### §A.2 — Gap Analysis: §1 Components Without Repo Analogs

| §1 Component | Repo analog present? | Notes |
|---|---|---|
| §1.1 Declaration of Independence | **Partial / unconfirmed** | README "Problem + Solution" sections may serve; not fully read pre-Step-5. Flag: if absent, framework has no explicit *founding-intent* statement distinct from the README marketing frame. |
| §1.2 Preamble (ordered ends) | **Unconfirmed** | Spec Step 7 requires ordered ends match `{reliable, predictable, dependable, repeatable, effective, efficient}`. Constitution.md body not yet read. Flagged for Step 7. |
| §1.3 Articles I–VII | Partial via constitution.md C/O/Q/G + rules-of-procedure | Scattered, not a single "structural rules" document. |
| §1.4 Bill of Rights | **Yes** — S-Series in constitution.md + `tiers.json` universal-floor selection | Mapping is clean in content; S-Series is pre-emptive veto. |
| §1.5 Subsequent Amendments | Partial — version bumps tracked in frontmatter; **no `CHANGELOG.md` at root** | Amendment process exists (rules-of-procedure); amendment *history* is a gap. |
| §1.6 Federal Statutes | **Yes** — 5 domain principle files | Clean. |
| §1.7 CFR | **Yes** — 5 domain CFR files | Clean. |
| §1.8 Case Law | **Partial** — reference-library only populated for ai-coding (1 of 6 domains); `_criteria.yaml` referenced but apparently missing | Admission criteria + coverage both gaps. |
| §1.9 Federalist Papers | **Yes** — ARCHITECTURE / SPECIFICATION / PROJECT-MEMORY ADRs | Mapped cleanly to design-commentary role. |
| §1.10 Congressional Record | **Yes** — PROJECT-MEMORY + git log + SESSION-STATE | Adequate. |
| §1.11 Executive Orders | Implicit via CLAUDE.md skip list + COMPLETION-CHECKLIST + hooks | No dedicated EO-like artifact; distributed across several layers. |
| §1.12 Subordinate Jurisdictions | **Yes** — Subagents (10) | Clean. |
| §1.13 Judicial Review | **Yes — multiply realized** — hooks (preventive), CI (commit-time), compliance-review (scheduled), tests (claim-audit) | Four instantiations with different trigger semantics. Not a gap, but worth noting as layered. |

### §A.3 — Contrarian Review Outcome (xhigh effort, agentId `af09b49df669729cd`)

**Protocol note:** Contrarian read some forbidden-set material (constitution.md:79-144, rules-of-procedure.md:65-73) while verifying operational function. Exposure logged in `06-compliance-audit.md E-02`. Findings retained because each passes operational-function check independently of the self-declared mapping — see mitigation note.

**Substantive corrections accepted from contrarian (applied below):**

| # | §A.1 row(s) affected | Change |
|---|---|---|
| C1 | §A.2 `§1.1 Declaration` | "Partial/unconfirmed" → **"Present at `constitution.md:18-53`"**. The file has an explicit `## Declaration` section articulating founding intent. My flag was too conservative. |
| C2 | §A.2 `§1.2 Preamble` | "Unconfirmed" → **"Present at `constitution.md:56-62`; uses 5-property goal set (Authority, Process, Protection, Relations, Continuity), NOT the Intent Engineering 6-property {reliable, predictable, dependable, repeatable, effective, efficient} set."** Definition mismatch — material for Step 5/7. |
| C3 | §A.2 `§1.4 Bill of Rights` | "Yes — S-Series + tiers.json universal-floor" → **"Yes for S-Series in `constitution.md:935-1050` (content match). NO for tiers.json floor — it selects on universality (3 non-S + 1 S), not veto authority. Conflation = LEARNING-LOG:165 metaphor-vs-operational error."** |
| C4 | §A.2 `§1.5 Amendment History` | "No CHANGELOG.md at root" → narrow gap: **constitution.md has embedded history at lines 1053-1245; the gap is every OTHER document (rules-of-procedure v3.26.8 at heavy churn, domain principles, domain methods, config files) has no history.** |
| C5 | §A.2 `§1.8 Case Law` | "Partial" → **"STRUCTURAL GAP — reference-library explicitly stripped of override authority per `constitution.md:101, 112`. No artifact binds future AI runs via stare-decisis. Deepest §1 gap in the repo."** |
| C6 | §A.1 row A (constitution.md) | multi-analog confirmed; elevate to Phase 1 finding: "5 of 13 §1 components (Declaration, Preamble, Articles, Bill of Rights, Amendment History) are collapsed into one file." |
| C7 | §A.1 row B (rules-of-procedure) | primary analog narrowed to **§1.5 Amendment Mechanism** (Article V). Drop §1.11 EO. |
| C8 | §A.1 rows H/I (subagents) | "ambiguous §1.12 primary + §1.11 secondary" → **"clean §1.11 Executive Orders / delegated agencies."** Subagents operate within delegated scope, not as independent jurisdictions. Evidence: `.claude/agents/orchestrator.md:44-67`. |
| C9 | §A.1 row L (reference library) | "§1.8 Case Law" → **"Secondary Authority (Restatements-equivalent)."** Framework self-strips override authority at constitution.md:101, 112. |
| C10 | §A.1 row N (project memory) | "clean → §1.10 Congressional Record" → **multi-analog split:** SESSION-STATE ≈ §1.10 Record; LEARNING-LOG is consulted *to avoid repeating mistakes* (`CLAUDE.md:44`) = operational stare-decisis; PROJECT-MEMORY holds *constraints and decisions* = binding-decisions register; BACKLOG = committee docket. |
| C11 | §A.1 row R (hooks) | "§1.13 Judicial Review (preventive)" → **"No clean §1 analog — novel pre-action structural gate."** Hooks prevent, they don't void; §1.13 is post-action voiding. Framework exploits AI runtime hookability unavailable in US legal system. |
| C12 | §A.1 row K (COMPLIANCE-REVIEW) | "§1.13 Judicial Review (scheduled)" → **"No clean §1 analog — scheduled internal audit / IG-style."** Not case-triggered, no voiding power. |
| C13 | §A.1 row AB (reviews) | "clean §1.13 Judicial Review output" → **"ambiguous — IG-style audit report; voiding authority sits in hooks/CI/pre-push gates, not reviews/."** |
| C14 | §A.1 row U (tests) | "§1.13 Judicial Review + §1.6 Federal Statutes" → **"§1.6 Federal Statutes of-the-code (primary, via `tests/benchmarks/baseline_*.json` regression floor); pre-merge gate half has no §1 analog (same as hooks R)."** |
| C15 | §A.1 row §1.12 Subordinate Jurisdictions | slot was tentatively assigned to subagents. **Re-assign to artifact M (scaffold templates) + consumer projects that instantiate them.** The framework's §1.12 slot is empty inside itself; it is filled by downstream adopters. |
| C16 | §2.1 observation O4 | `_criteria.yaml` exists in `reference-library/ai-coding/` (1449 bytes, 4 auto-capture rules + 4 suggestion triggers). Gap is scope, not presence. Observation updated. |

**Challenges that survived (my draft mapping retained):**
- C (domain principles → §1.6 Federal Statutes) — **survives.** Hierarchy and supremacy confirmed at `constitution.md:111`.
- D (domain CFR → §1.7 CFR) — **survives with caveat:** per-method enabling-authority citation is weaker than US CFR (new finding F-04 below).
- §1.9 Federalist Papers ↔ ARCHITECTURE / SPECIFICATION / PROJECT-MEMORY ADRs — survives.
- O (CLAUDE.md / AGENTS.md → Preamble + EO at project level) — survives.

**Name-match smuggling risks flagged for Step 5:**
- HIGH: the repo's `governance_level` labels (`federal-statute`, `federal-regulations`) are US-statutory terms. C and D pass operational check, so the name-match is confirmed, not smuggled. But future mappings using the same label pattern must independently re-verify.
- CONFIRMED SMUGGLING: `tiers.json universal-floor → Bill of Rights` was pure metaphor (the word "floor" ≈ "rights floor"), operationally false.
- MEDIUM: the framework's own text calls reference-library "Case Law" (at constitution.md:92) while operationally making it non-binding. The name-match is **embedded in the framework**, which is the source of the smuggling risk my draft inherited.

### §A.4 — Finalized As-Derived Mapping (post-contrarian)

| Artifact | §1 analog (post-contrarian) | Tag |
|---|---|---|
| A — `constitution.md` | §1.1 + §1.2 + §1.3 + §1.4 + §1.5 combined in one file | 5-in-1 (structural finding, not an error) |
| B — `rules-of-procedure.md` | §1.5 Amendment Mechanism (primary) + §1.3 procedural Articles (secondary) | multi-analog |
| C — title-NN | §1.6 Federal Statutes | clean |
| D — title-NN-cfr | §1.7 CFR | clean-with-caveat |
| E — ai-instructions.md | no §1 analog — boot-loader | loose-end |
| F — domains.json | no §1 analog — lookup infrastructure | infrastructure |
| G — tiers.json | no §1 analog — universality-selection infrastructure; NOT §1.4 | infrastructure (corrected) |
| H/I — subagents | §1.11 Executive Orders / delegated agencies | clean (corrected) |
| J — COMPLETION-CHECKLIST | §1.11 EO with ENFORCED items backed by hook/CI | dual-tier |
| K — COMPLIANCE-REVIEW | no clean §1 analog — scheduled IG audit | loose-end |
| L — reference-library | Secondary Authority (Restatements-equivalent) | clean (corrected; NOT §1.8) |
| L' — `_criteria.yaml` | would-be secondary-authority admission rules | partial (ai-coding only) |
| M — scaffold templates | §1.12 Subordinate Jurisdiction charter template | clean (re-assigned) |
| N — project memory | multi-analog: SESSION-STATE ≈ §1.10; LEARNING-LOG ≈ stare-decisis-by-consultation; PROJECT-MEMORY ≈ binding decisions register; BACKLOG ≈ docket | multi-analog |
| O — CLAUDE.md / AGENTS.md | §1.2 Preamble (project-level) + §1.11 EO | dual-role |
| P — README / ARCHITECTURE / API / SPECIFICATION / SBOM / SECURITY | §1.9 Federalist Papers (ARCH/SPEC/part of README); API/SBOM/SECURITY no §1 analog | mixed |
| Q — LICENSE / LICENSE-CONTENT | no §1 analog — external legal instruments | infrastructure |
| R — hooks | **novel — no §1 analog**; pre-action structural gate | novel |
| S — scripts | no analog | infrastructure |
| T — src/ | no analog — implementation | infrastructure |
| U — tests | §1.6 Statutes (of-the-code) + pre-merge gate (novel, ≡ R) | dual |
| V — drift baselines | no analog — monitoring infrastructure | infrastructure |
| W — CI | **novel — no §1 analog**; same category as R | novel |
| X/Y — archive, migration | weak §1.10 (historical record) | infrastructure |
| Z — examples | no analog | infrastructure |
| AA — staging | n/a | n/a |
| AB — reviews | IG-style audit (not primary judicial review) | loose-end |

### §A.5 — Gap Table Rewritten

| §1 Component | Repo analog | Status |
|---|---|---|
| §1.1 Declaration | `constitution.md:18-53` | PRESENT |
| §1.2 Preamble | `constitution.md:56-62` with 5-property goal set (APPRC, NOT Intent Eng's 6-property set) | PRESENT with definition mismatch |
| §1.3 Articles I-VII | `constitution.md` C/O/Q/G series + portions of rules-of-procedure | PRESENT (distributed) |
| §1.4 Bill of Rights | S-Series in `constitution.md:935-1050` | PRESENT (tiers.json is NOT this) |
| §1.5 Amendment Mechanism | `rules-of-procedure.md` (primary) + `constitution.md:1053-1245` in-file history | PRESENT (mechanism), ASYMMETRIC HISTORY |
| §1.6 Federal Statutes | 5 domain principle files | PRESENT |
| §1.7 CFR | 5 domain CFR files | PRESENT (weak per-method enabling-authority) |
| §1.8 Case Law (binding) | — | **STRUCTURAL GAP — deepest in repo** |
| §1.9 Federalist Papers | ARCHITECTURE.md, SPECIFICATION.md, PROJECT-MEMORY ADRs | PRESENT |
| §1.10 Congressional Record | SESSION-STATE + git log | PRESENT |
| §1.11 Executive Orders | subagents + COMPLETION-CHECKLIST (partial) + CLAUDE.md operational rules | PRESENT (distributed) |
| §1.12 Subordinate Jurisdictions | scaffold templates + consumer projects | PRESENT (downstream) |
| §1.13 Judicial Review | **ONLY as pre-action gates (hooks, CI, pre-push); no post-action voiding** | PRESENT in asymmetric form |

---

## §C — Declared-vs-Derived Comparison (Step 5)

**Forbidden set revealed in full:**
- `constitution.md` lines 77–123 (Framework Structure: contextual layers + 7-layer operative hierarchy + branch-mapping of C/O/Q/G)
- `constitution.md` lines 127–144 (Article I=Legislative / II=Executive / III=Judicial / IV=Administrative State mapping)
- `rules-of-procedure.md` lines 63–73 (Legal System Analogy — self-declares as Amendment Process)
- `README.md:42` + `:861` (7-layer governance-hierarchy summary + file-tree labels)
- `.claude/plans/project-constitutional-framework-alignment.md` (825 lines; read first ~100 lines — Context + "Pattern, Not Analogy" governing principle + Five Root Purposes + D1 Dual-Layer IDs + D2 File Renames)

**Governing meta-context from the plan (line 28–34):** Framework consciously adopts US Constitution as "pattern, not analogy" — "pattern-level alignment, not 1:1 component alignment." Five Root Purposes: Authority, Process, Protection, Relations, Continuity. Explicit scope clause: "we follow the framework closely enough that the structural connection is visible to AI and humans, but never shoe-horn content to match a specific Constitutional provision." This is the interpretive default against which "misalignment" must be measured — pattern-level divergence is expected, but semantic contradictions (e.g., calling something "Case Law" while stripping its binding authority) are not exempt.

### §C.1 — Mapping comparison table

| Artifact class | As-Derived (§A.4, post-contrarian) | Self-Declared (`constitution.md:77–144`, `rules-of-procedure.md:63–73`, `README.md:42`, plan) | Delta |
|---|---|---|---|
| S-Series | §1.4 Bill of Rights — pre-emptive veto | "Bill of Rights \| S-Series \| Veto Power \| Immutable" (line 86) | **AGREE** (operational + labelled) |
| C/O/Q/G series | §1.3 Articles I-VII — structural rules | "Constitution \| Meta-Principles (C, Q, O, G Series) \| Foundation \| Very Stable" (line 87); further mapped to Legislative/Executive/Judicial/Administrative branches (lines 131-141) | **AGREE** at hierarchy-layer level. **Additional branch-mapping not in §1**: framework maps 4 series onto 4 governmental branches. Pattern-level choice, not a contradiction. |
| `constitution.md` Declaration section | §1.1 Declaration (`constitution.md:18-53`) | "Declaration \| This document \| States why the framework exists" (line 79); declared **non-operative** contextual layer | **AGREE** (both content + non-operative status) |
| `constitution.md` Preamble section | §1.2 Preamble with 5-purpose goal set (APPRC) | "Preamble \| This document \| States binding purposes — interpretive context that resolves ambiguity" (line 80); explicitly **non-operative** | **AGREE** on presence + non-operative role. Definition divergence vs. spec: framework uses 5-purpose set (APPRC), spec-given Intent Engineering set is 6-property (RPDREE). See §C.4. |
| Historical Amendments (`constitution.md:1053-1245`) | §1.5 in-file amendment history | Implicitly present (section exists); rules-of-procedure §7.x cites "Historical Amendments" | **AGREE** (for constitution only) |
| `rules-of-procedure.md` | §1.5 Amendment Mechanism (primary) + §1.3 procedural Articles | "Rules of Procedure \| Constitutional Methods \| Process — how principles are applied and maintained" (line 89); AND "Amendment Process \| This document \| How to evolve the framework itself" (`rules-of-procedure.md:70`) | **AGREE** on Article V role. **Divergence**: framework places "Constitutional Methods" as a separate *operative* layer between Statutes and Regulations (line 89) — a layer that does not exist in US hierarchy. Article V in US law is a *procedure* inside the Constitution; the framework promotes it to a peer document. Pattern-level choice; not a contradiction, but a finding. |
| Domain principles (5 files) | §1.6 Federal Statutes | "Federal Statutes \| Domain Principles \| Context — derived from Constitution" (line 88) | **AGREE** (operational match) |
| Domain CFR (5 files) | §1.7 CFR with weak per-method enabling-authority | "Federal Regulations \| Domain Methods \| Execution — implementation details" (line 90) | **AGREE** at layer level. **Derived divergence**: §1.7 requires per-regulation enabling-authority citation; framework's CFR files do not carry per-method statutory-citation frontmatter (verified via frontmatter schema — only `governance_level: federal-regulations`, no `enabling_authority: meta-core-xxx`). |
| Reference library | Secondary Authority (Restatements-equivalent) | "Case Law \| Reference Library \| Precedent — concrete artifacts from real application \| Accumulating" (line 92). AND explicitly **"Case Law (Reference Library): Precedent from real application. Informs future decisions but does not override normative layers above."** (line 101). AND supremacy clause **"Case Law (Reference Library) informs interpretation but does not override any normative layer."** (line 112) | **NAME-MATCH SMUGGLING, SELF-ADMITTED**: framework uses the "Case Law" label at line 92 while lines 101 + 112 strip the defining property of §1.8 (binding precedent). Framework is internally consistent (it states non-overriding twice) but the label is operationally misleading. Finding: content matches secondary authority; label says primary case law. |
| Tool/Model Appendices (embedded in CFR: `title-10-ai-coding-cfr.md:7217–8599` Appendices A–L; `rules-of-procedure.md:4946–5223` Appendices G–J) | Derived-silent (missed in my §2 as a distinct class) | "Agency SOPs \| Tool/Model Appendices \| Tactical \| Frequently Updated" (line 91) | **DERIVED-SILENT**: framework declares a 7th layer my inventory did not call out as a distinct artifact class. Appendices exist (12 in ai-coding CFR + 4 in rules-of-procedure) but embedded in larger files. §2 should be amended to add class AC — Tool/Model Appendices. |
| Subagents | §1.11 Executive Orders / delegated agencies | Self-silent at the canonical hierarchy level (not in constitution.md:77-123 table); AGENTS.md + individual agent files describe their roles | **SELF-SILENT**: declared hierarchy does not include subagents as a governance layer. My derivation places them as §1.11. Framework uses them heavily (10 agents) without naming them a hierarchy layer. |
| Hooks + CI + pre-push gates | Novel — no §1 analog (pre-action structural gate) | Self-silent (not in constitution.md hierarchy) | **SELF-SILENT**: framework's most operationally-binding mechanism has no self-declared hierarchy position. Described procedurally in CLAUDE.md + rules-of-procedure, but not mapped to US-Constitution structure. Consistent with my derivation "novel." |
| Scaffold templates (embedded in server.py) | §1.12 Subordinate-Jurisdiction charter template | Self-silent — no hierarchy mapping; plan file (line 30) implicitly positions the framework as replicable at lower scales | **SELF-SILENT**. |
| Project memory files (SESSION/PROJECT/LEARNING/BACKLOG) | Multi-analog: Record + stare-decisis consulted + binding decisions + docket | Self-silent at hierarchy level; `CLAUDE.md:43-44` ritually consults them; no Constitutional mapping | **SELF-SILENT on mapping**; operationally their consultation is mandated. |
| `tiers.json` universal-floor | Universality-selection infrastructure; NOT §1.4 | Self-silent (tiers.json frontmatter says "Tiered Governance Principle Activation — universal floor") | **AGREE BY ABSENCE**: framework does not claim floor = Bill of Rights. My original draft conflation was mine alone. |
| `CLAUDE.md` / `AGENTS.md` | Project-level Preamble + EO stack | Scaffolded by `scaffold_project` standard kit (code); not mapped in hierarchy | **SELF-SILENT**; functions as project-level activator. |
| `ai-instructions.md` | No §1 analog — boot-loader | Frontmatter labels `framework-activation` as a `governance_level` that is not in the 7-layer hierarchy | **SELF-ADMITTED OUTSIDE HIERARCHY**. Not a finding — correctly classified as infrastructure. |
| Product docs (README/ARCH/API/SPEC/SBOM/SECURITY) | §1.9 Federalist Papers (for ARCH/SPEC) + no analog for others | Self-silent (ARCHITECTURE + SPECIFICATION are project docs, not governance content); README has the 7-layer summary in prose | **AGREE** — framework does not claim these are governance layers. |

### §C.2 — Seven-layer Declared Hierarchy vs. Thirteen-component §1

| §1 component | In declared 7-layer hierarchy? | Commentary |
|---|---|---|
| §1.1 Declaration | **Separately named as non-operative "Contextual Layer"** (`constitution.md:77-80`) | Declaration-equivalent is present but outside the operative hierarchy. Consistent with §1 — Declaration is pre-constitutional. |
| §1.2 Preamble | **Separately named as non-operative "Contextual Layer"** | Consistent with §1. |
| §1.3 Articles I-VII | Layer 2 — Constitution (Meta-Principles) | Merged with §1.4 in-file (not in-hierarchy). |
| §1.4 Bill of Rights | Layer 1 — S-Series | Top of operative hierarchy. |
| §1.5 Amendment Mechanism | Layer 4 — Rules of Procedure | **Divergent placement**: US has amendment INSIDE Constitution (Article V); framework has amendment as a separate *operative* document between Statutes (layer 3) and Regulations (layer 5). |
| §1.6 Federal Statutes | Layer 3 — Federal Statutes / Domain Principles | Consistent. |
| §1.7 CFR | Layer 5 — Federal Regulations / Domain Methods | Consistent; weak per-method enabling-authority. |
| §1.8 Case Law | Layer 7 — Reference Library | **Label-vs-semantics divergence**: labelled Case Law, operationally non-binding. |
| §1.9 Federalist Papers | NOT in hierarchy | Implicit in ARCHITECTURE/SPECIFICATION/PROJECT-MEMORY ADRs. |
| §1.10 Congressional Record | NOT in hierarchy | Implicit in SESSION-STATE + git log. |
| §1.11 Executive Orders | Partially as Layer 6 — Agency SOPs (Tool/Model Appendices) | Executive-order function also distributed across subagents, CLAUDE.md, hooks — not a clean single layer. |
| §1.12 Subordinate Jurisdictions | NOT in hierarchy | Framework itself exists at the top level; consumer projects receive scaffolded charters. |
| §1.13 Judicial Review | NOT in hierarchy | Realized via hooks + CI + pre-push + compliance-review, but not named a hierarchy layer. |

### §C.3 — Classified deltas

**AGREE on operational function:** S-Series↔BoR, Domain principles↔Statutes, Domain methods↔CFR, Declaration+Preamble non-operative, rules-of-procedure as amendment mechanism.

**DISAGREE at content-vs-label:**
- Reference library labelled "Case Law" while explicitly stripped of override authority (constitution.md:101, 112). Framework's own text admits the divergence. **Finding F-01.**
- Framework places "Constitutional Methods" (Rules of Procedure) as a separate *operative* hierarchy layer between statutes and regulations — a layer that has no §1 equivalent (US Article V is procedural, not a separate layer). Novel structural choice; pattern-level divergence. **Finding F-02** (non-critical — documentation issue, not a semantics contradiction).

**SELF-SILENT (framework has no declared mapping for):**
- Subagents (§1.11)
- Hooks / CI / pre-push gates (novel / §1.13 partial)
- Scaffold templates (§1.12)
- Project memory (§1.10 + stare decisis)
- CLAUDE.md / AGENTS.md (project-Preamble)
- Product docs (§1.9)

Silence isn't inherently a gap — but the **totality of silence** is: 6 of 13 §1 components have no declared mapping, and several of those silences hide load-bearing operational mechanisms (hooks, subagents, CI). Users reading constitution.md's 7-layer hierarchy would miss that enforcement actually sits in a layer the hierarchy doesn't name. **Finding F-03.**

**DERIVED-SILENT (I missed in Step 2, declared present):**
- Tool/Model Appendices — 12+ in ai-coding CFR, 4 in rules-of-procedure. My §2 inventory did not break these out. Amendment to §2 (artifact class AC). **Not a finding** against the framework — a correction in my own inventory.

### §C.4 — Five-Purpose Preamble vs Spec's Six-Property Intent Engineering Set

| Framework (plan line 36-48 + constitution.md:58-62) | Spec-given Intent Engineering properties |
|---|---|
| Authority | *(no 1:1 equivalent; embedded across reliable+dependable+predictable)* |
| Process | *(no 1:1 equivalent)* |
| Protection | (closest: dependable — "can be depended on not to harm") |
| Relations | *(no 1:1 equivalent — framework-internal integration)* |
| Continuity | repeatable + effective-over-time |

The two sets are not translatable 1:1. Framework's 5-purposes are **organizational categories of the problems governance must solve** (Authority, Process, Protection, Relations, Continuity). Spec's 6-properties are **quality attributes of the governed output** (reliable, predictable, dependable, repeatable, effective, efficient). Different level of abstraction.

The spec told the reviewer "property(ies) appearing most often = root-cause signal" (Step 9). Given this divergence, the synthesis will need to either: (a) adopt the framework's 5-purposes as the property set and invert the spec rule, or (b) retain spec's 6-properties and flag every finding by which framework-purpose it threatens as well. Decision deferred to Step 9 — it's a synthesis choice, not a Step 5 finding.

### §C.5 — Updated inventory additions (amendment to §2)

| Artifact class | Path pattern | Count | Self-claimed role | Operational content | Producer | Consumer |
|---|---|---|---|---|---|---|
| AC — Tool/Model Appendices (embedded) | `documents/title-NN-*-cfr.md` §Appendix, `documents/rules-of-procedure.md` §Appendix | 12 in ai-coding CFR (A–L) + 4 in rules-of-procedure (G–J) + 2 in title-10 principles (A–B) = 18+ embedded | Agency SOPs / Tool-specific operational guides (per constitution.md:91) | Platform-specific guidance: Claude Code, Gemini CLI, Perplexity, Postgres/Supabase, Chrome Extension, Context Engine | Human author | AI when platform-specific method applies |

### §C.6 — Summary of structural findings surfaced by reveal

1. **F-01** — "Case Law" label on reference-library contradicts framework's own stripping of override authority (self-admitted at constitution.md:101, 112). Name creates operational expectation that framework doesn't fulfill.
2. **F-02** — "Constitutional Methods" as a separate *operative* layer between statutes and regulations is a framework-invented layer without §1 analog. Pattern-level divergence; should be named as such in docs rather than called "Rules of Procedure" (US term) without noting the structural innovation.
3. **F-03** — 6 of 13 §1 components are self-silent in the declared hierarchy. Load-bearing enforcement mechanisms (hooks, CI, subagents) have no hierarchy position. Users reading the 7-layer table cannot locate where enforcement happens.
4. **F-04** — Domain CFR methods lack per-method enabling-authority citation (unlike US CFR where every regulation traces to a specific U.S.C. statute section). Frontmatter only carries `governance_level: federal-regulations`.
5. **F-05** — Deepest structural gap: no §1.8-equivalent binding-precedent artifact. Reference library is explicitly non-overriding; subagents' repeated decisions don't accrete; LEARNING-LOG is consulted but not binding by rule.
6. **F-06** — Amendment history is embedded only in constitution.md (lines 1053-1245). Rules-of-procedure (v3.26.8, heavy churn), 5 domain principle files, 5 domain CFR files, tiers.json, domains.json have no embedded history and no centralized CHANGELOG.
7. **F-07** — Reference library is populated in 1 of 6 domains. `_criteria.yaml` admission rules likewise defined in ai-coding only.
8. **F-08** — BACKLOG.md is used heavily by the framework itself (620 lines) but not scaffolded into adopter projects. Asymmetry between framework self-use and what it provisions for adopters.
9. **F-09** — §1.13 Judicial Review realized only as pre-action gates (no post-action voiding). Documented as Finding but not a deficiency — pattern-level divergence enabled by runtime hookability.
10. **F-10** — Preamble goal set (Authority/Process/Protection/Relations/Continuity) is at a different level of abstraction than spec's Intent Engineering property set (reliable/predictable/dependable/repeatable/effective/efficient). Affects synthesis (Step 9).

Full severity/category/threatened-properties classification follows in §D (Phase 1 Findings).

---

## §D — Phase 1 Findings (Step 6)

**Record schema:** `id` | `severity` (Critical/High/Medium/Low) | `category` (loose-end/misplacement/gap/redundancy/ambiguity/conflict/ungrounded/orphan) | `threatened-properties` (subset of {reliable, predictable, dependable, repeatable, effective, efficient}) | `evidence` (path + line) | `root-cause-hypothesis` (one sentence). One finding per cause — symptoms with shared cause collapsed.

---

### F-P1-01 — Metaphor label carries semantic weight the operation does not honor ("Case Law" ↔ non-binding)

- **Severity:** Medium
- **Category:** conflict (self-admitted in the framework itself)
- **Threatened:** predictable, effective
- **Evidence:**
  - `documents/constitution.md:92` — Reference Library labeled "Case Law \| Precedent"
  - `documents/constitution.md:101` — "Case Law (Reference Library): Precedent from real application. **Informs future decisions but does not override normative layers above.**"
  - `documents/constitution.md:112` — supremacy clause "Case Law (Reference Library) informs interpretation but does not override any normative layer."
  - `documents/rules-of-procedure.md:53` (via contrarian) — loading-guidance table reinforces advisory framing.
- **Root-cause hypothesis:** framework adopted US labels as pedagogical anchor (plan line 34 — "pattern, not analogy … pedagogical anchor"), but when the operational semantics diverged from §1.8's stare-decisis-binding meaning, the label was retained. Users inheriting the §1.8 mental model will expect binding precedent; the framework provides non-binding commentary. "Pattern, not analogy" stance does not protect against label-inherited expectations when the operation materially differs.

---

### F-P1-02 — Declared 7-layer hierarchy omits the mechanisms that make the framework binding (hooks, CI, subagents, scaffold templates, pre-push gates)

- **Severity:** High
- **Category:** orphan / misplacement (load-bearing mechanisms with no hierarchy position)
- **Threatened:** reliable, dependable, effective, predictable
- **Evidence:**
  - `documents/constitution.md:82-92` — 7-layer "Operative Hierarchy" table names only: S-Series, Meta-Principles, Domain Principles, Constitutional Methods, Domain Methods, Tool/Model Appendices, Case Law. Hooks, CI, subagents, scaffold templates are absent.
  - `.claude/hooks/pre-tool-governance-check.sh` — hard-blocks tool calls missing evaluate_governance+query_project.
  - `documents/agents/` (10 files) — delegation mechanism.
  - `src/ai_governance_mcp/server.py:846-867` — `SCAFFOLD_CORE_FILES`/`STANDARD_EXTRAS` — subordinate-jurisdiction charter provisioning.
  - `.github/workflows/` (CI) + `workflows/COMPLETION-CHECKLIST.md` ENFORCED tier — additional binding enforcement.
  - `README.md:42` — states "7-layer governance hierarchy" as the canonical description; readers seeking "where does enforcement live?" get no answer from the hierarchy.
- **Root-cause hypothesis:** the declared hierarchy inherits the US Constitution's structure (which has no hookable-runtime equivalent). When the framework added runtime enforcement that the US Constitution cannot have, the existing hierarchy was not amended to name the new layers. Users reading the canonical 7-layer description cannot locate the mechanisms that actually do the binding.

---

### F-P1-03 — "Constitutional Methods" inserted as operative layer between Statutes and Regulations — novel layer, no §1 pattern-level analog, not named as a pattern innovation

- **Severity:** Low
- **Category:** ambiguity
- **Threatened:** predictable
- **Evidence:**
  - `documents/constitution.md:89` — "Rules of Procedure \| Constitutional Methods \| Process — how principles are applied and maintained \| Stable" positioned as operative layer 4 of 7, between Statutes (layer 3) and Regulations (layer 5).
  - §1 derivation: Amendment Mechanism (Article V) in US law is a procedure *inside* the Constitution, not a separate document between statutes and regulations.
  - `rules-of-procedure.md:63-73` — self-declares as "Amendment Procedure," which is consistent with §1.5 but inconsistent with its layer-4-between-statutes-and-regulations placement.
- **Root-cause hypothesis:** framework wanted a separate document for "how principles apply and evolve," which is reasonable, but placed it in the operative hierarchy at a position that has no US analog. The choice is defensible (framework goes to lengths to avoid shoe-horning, per plan line 32), but the 7-layer presentation does not flag this as a pattern-level innovation, so readers may miss that it departs from the borrowed structure.

---

### F-P1-04 — CFR methods lack per-method enabling-authority citation (unlike §1.7 CFR where each regulation must trace to a specific statute)

- **Severity:** Medium
- **Category:** gap
- **Threatened:** dependable, predictable
- **Evidence:**
  - Frontmatter schema for `documents/title-NN-*-cfr.md` (5 files, sampled all): only `version`, `status`, `effective_date`, `domain`, `governance_level`. No `enabling_authority: meta-core-*` field.
  - `documents/rules-of-procedure.md:46` — asserts abstractly that "methods derive authority from Constitutional principles," but no per-method citation is enforced.
  - Per-method surface inspection (title-10-ai-coding-cfr `Applies To:` lines) typically names domain principles in prose but does not carry a structured citation that tooling can validate.
- **Root-cause hypothesis:** the framework states the authority-derivation rule at the document level (rules-of-procedure:46), but did not propagate the requirement to per-method frontmatter or authoring template. Without a structured citation, there is no mechanical check that a method actually implements a principle, and a drifting method cannot be detected by comparing its declared authority to its content.

---

### F-P1-05 — No stare-decisis-binding artifact exists; reference library is self-stripped of override authority — the framework's deepest structural gap vs §1

- **Severity:** High
- **Category:** gap
- **Threatened:** repeatable, dependable, effective
- **Evidence:**
  - `documents/constitution.md:101, 112` — explicitly strip override authority from reference library.
  - `reference-library/` populated only in `ai-coding/` — even the non-binding secondary-authority layer is absent for 5 of 6 domains (see F-P1-07).
  - LEARNING-LOG "Graduated Patterns" table (lines 474-513) — graduation is from LEARNING-LOG → methods/principles via human curation, not accretion.
- **Root-cause hypothesis:** framework design prioritized avoiding uncontrolled rule-proliferation from accreted decisions. Rather than admit precedent-as-binding and discipline it, the framework excluded precedent-binding entirely. Consequence: repeated AI-generated decisions don't accumulate into binding norms, so repeatability across sessions depends entirely on re-querying principles — no "this is how we've done it for the last 20 times" signal exists.

---

### F-P1-06 — Amendment history is embedded only in `constitution.md`; no centralized CHANGELOG; rules-of-procedure (v3.26.8, heavy churn) and 10 domain documents have no amendment log

- **Severity:** Medium
- **Category:** gap
- **Threatened:** dependable, repeatable
- **Evidence:**
  - `documents/constitution.md:1053-1245` — in-file Historical Amendments section covers v1.1 → v4.1.0.
  - `find . -maxdepth 2 -name "CHANGELOG*"` returns nothing; no root CHANGELOG.
  - `documents/rules-of-procedure.md:2` — `version: "3.26.8"` indicates heavy churn, but no embedded history section visible in first 120 lines.
  - 5 domain principle files + 5 domain CFR files: frontmatter shows versions v1.0.1 – v2.38.2 but no in-file history section.
  - `documents/tiers.json:3` — `_version: "1.4.0"` but no history.
- **Root-cause hypothesis:** when the framework restructured to Constitutional naming (per plan D2), amendment-history was embedded only in the constitution. The pattern didn't propagate to other documents, and no CHANGELOG was added. Consequence: future readers (or AI agents doing impact analysis) cannot answer "what changed between v2.36 and v2.38.2 of rules-of-procedure?" from in-repo state.

---

### F-P1-07 — Reference library and `_criteria.yaml` admission rules exist only for `ai-coding/` (1 of 6 domains)

- **Severity:** Medium
- **Category:** gap
- **Threatened:** repeatable, effective
- **Evidence:**
  - `ls reference-library/` shows only `ai-coding/` subdirectory.
  - `reference-library/ai-coding/_criteria.yaml` (1449 bytes, 4 auto-capture + 4 suggestion triggers) — no corresponding files for multi-agent, kmpd, storytelling, multimodal-rag, ui-ux.
  - Graduation pathway (`LEARNING-LOG.md` Graduated Patterns table) functional for ai-coding only; other domains can only graduate lessons directly to methods/principles, bypassing the secondary-authority stage.
- **Root-cause hypothesis:** reference-library was seeded for ai-coding (framework's highest-churn domain) and scheduled to spread to other domains, but that spread hasn't happened. No per-domain automation or structural gate ensures the pathway exists where LEARNING-LOG entries can land below the principle/method bar.

---

### F-P1-08 — `BACKLOG.md` is heavily used in the framework's self-governance (620 lines) but is not scaffolded into adopter projects

- **Severity:** Low
- **Category:** misplacement (framework uses a class it doesn't propagate)
- **Threatened:** effective (adopters miss a class of persistent state the framework itself requires)
- **Evidence:**
  - `BACKLOG.md` at repo root — 620 lines, 1 Active + 32 Discussion items.
  - `src/ai_governance_mcp/server.py:846-867` — `SCAFFOLD_CORE_FILES` + `SCAFFOLD_STANDARD_EXTRAS` list SESSION-STATE, PROJECT-MEMORY, LEARNING-LOG, AGENTS, CLAUDE.md, COMPLETION-CHECKLIST. **BACKLOG.md not in either tier.**
  - `CLAUDE.md:66` — "Backlog items: Discussion and deferred items live in BACKLOG.md, not SESSION-STATE.md" — framework's own routing rule assumes BACKLOG exists.
- **Root-cause hypothesis:** BACKLOG emerged as a framework-dev need (deferred items + discussion) but was not added to the scaffold template because it wasn't considered universal. Adopter projects that follow the framework's Defer-vs-Fix rule (CLAUDE.md:52-63, per §7.11) have nowhere to put "Defer-with-tracking" items unless they invent their own file. Either (a) framework should scaffold BACKLOG as part of Standard kit, or (b) the Defer rule should route deferred items to PROJECT-MEMORY for adopters who don't have BACKLOG.

---

### F-P1-09 — Framework's 5-purpose Preamble goal set (APPRC) operates at a different abstraction level than spec's 6-property Intent Engineering set (RPDREE); affects Step-9 synthesis, not framework integrity

- **Severity:** Low (for framework — this is a valid pattern-level choice)
- **Category:** ambiguity (between spec assumption and framework declaration, not within framework)
- **Threatened:** n/a at the framework level; relevant to review synthesis
- **Evidence:**
  - `documents/constitution.md:42-46` + plan line 36-48 — 5 root purposes: Authority, Process, Protection, Relations, Continuity (APPRC).
  - Spec Step 9 — 6 Intent Engineering properties: reliable, predictable, dependable, repeatable, effective, efficient (RPDREE).
  - Framework abstraction: "problems the governance system must solve."
  - Spec abstraction: "quality attributes of the governed output."
- **Root-cause hypothesis:** spec's property set was chosen independently of the framework's stated purpose set. Both are defensible; they describe different layers of the same system. Step 9 synthesis must either (a) adopt framework's 5-purposes as synthesis lens, (b) retain spec's 6-properties and cross-map each finding to a framework purpose, or (c) treat divergence as data and report both. Decision deferred to Step 9.

---

### §D.1 — Symptoms collapsed into causes (one-per-cause discipline)

| Symptom noticed in §C | Cause finding it collapses to |
|---|---|
| C/O/Q/G mapped to Leg/Exec/Jud/Adm branches (2nd mapping in same file) | Not a finding — pattern-level choice, consistent with "pattern, not analogy" |
| Tool/Model Appendices embedded in CFR rather than separate files | Not a finding — my §2 inventory correction (logged in §A.3 amendment) |
| `ai-instructions.md` as `framework-activation` with no §1 analog | Not a finding — correctly classified as infrastructure |
| Subagents labelled as §1.12 by my draft — actually §1.11 | Not a finding — corrected in §A.3 |
| `tiers.json` universal-floor initially conflated with Bill of Rights | Not a finding — my own mapping error, logged in §A.3 C3 |
| §1.13 Judicial Review realized only pre-action, not post-action | Not a standalone finding — subsumed under F-P1-02 (hierarchy omits enforcement mechanisms) |

### §D.2 — Summary counts

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 2 (F-P1-02, F-P1-05) |
| Medium | 4 (F-P1-01, F-P1-04, F-P1-06, F-P1-07) |
| Low | 3 (F-P1-03, F-P1-08, F-P1-09) |
| **Total** | **9** |

### §D.2a — Amendments from Step 10 (post-hoc miss-check of LEARNING-LOG + PROJECT-MEMORY + BACKLOG)

**A-01 — F-P1-08 severity upgraded from Low to Medium.**

`BACKLOG.md:614-617` already documents a self-contradiction known to the framework: "The `scaffold_project` tool creates 6 files for standard tier (core 4 + CLAUDE.md + COMPLETION-CHECKLIST.md), but CFR §1.5.2 defines Standard Kit as 8 files (core 4 + ARCHITECTURE.md + SPECIFICATION.md + COMPLETION-CHECKLIST.md + BACKLOG.md). The tool creates a different set than the CFR defines. Pre-existing misalignment — predates the BACKLOG.md addition."

This is not merely "adopters lack a file class the framework uses" — it is a **compliance violation against the framework's own CFR definition**. The framework itself has filed the gap as a discussion item without resolution.

Updated F-P1-08:
- **Severity:** Medium (was Low) — self-declared CFR violation
- **Threatened:** effective, **dependable** (added — CFR defines Standard Kit one way; tool implements a different way)
- **Additional evidence:** `BACKLOG.md:614-617`
- **Additional root-cause data:** pre-existing gap; not caused by BACKLOG.md addition. The scaffold definition predates the CFR revision; CFR was updated (per PROJECT-MEMORY "Backlog Separation" 2026-04-14) to add BACKLOG.md to Standard Kit but the scaffold was not updated in lockstep.

**A-02 — F-P1-07 extended: reference-library auto-staging infrastructure exists but is dormant.**

`BACKLOG.md:350-356` (item #41 "Reference Library Auto-Staging Proposals"): "The reference library staging infrastructure exists (`staging/` directory, `_criteria.yaml` per domain, completion sequence prompt) but is dormant — `.gitkeep` placeholder, never activated."

The §2 inventory assumed `_criteria.yaml` exists only in `ai-coding/`; the BACKLOG item says `_criteria.yaml per domain` — implying criteria files exist but are unactivated for the other domains. Need to re-verify in a future pass; for now note that the gap may be activation-pending rather than structurally-absent.

Updated F-P1-07:
- **Severity:** Medium (unchanged)
- **Additional evidence:** `BACKLOG.md:350-356` — framework has open discussion item for activation
- **Additional root-cause data:** staging infrastructure exists as dormant placeholders; activation logic hasn't been wired to the `capture_reference` MCP tool. Fix is partly about activation, not just content.

**A-03 — F-P1-02 strengthened by empirical compliance data in PROJECT-MEMORY.**

`PROJECT-MEMORY.md:54` "Hard-Mode Enforcement 2026-02-28": "Compliance: 13%→expected 90%+ (deterministic enforcement)."

This is not a reversal of F-P1-02 — the hook compliance measure (13% advisory → 90%+ structural) is at the *mechanism* level, and confirms the enforcement mechanisms work when they exist. The finding is not that hooks don't work; it's that they exist *outside* the declared hierarchy. The 13→90% figure supports the framework's operational effectiveness claim for mechanisms that ARE declared somewhere; it does not address F-P1-02's structural concern that the enforcement layer is absent from the canonical 7-layer presentation.

**A-04 — F-C-01 confirmed by self-aware discipline, but preventive gate still absent.**

`PROJECT-MEMORY.md:84` "S-Series Scope Boundary 2026-04-12": "The operational criteria for S-Series classification is 'does this prevent user harm?' not 'is this in the Bill of Rights?' Established when contrarian review reclassified Unenumerated Rights and Reserved Powers from S-Series to G-Series."

This confirms the framework is self-aware of the metaphor-hazard class of error (reactive). F-C-01 finding remains — a *preventive* Admission Test question hasn't been added. The existing discipline is human-mediated contrarian review, which catches most but not all (F-P1-01 Case Law is still current).

**A-05 — Framework has rejected "unfalsifiable escape clauses" as a known anti-pattern, supporting F-P2-01.**

`SESSION-STATE.md:74`: "rejected original #101 approach (soften 'always use canonical' authoring rule) as creating unfalsifiable 'coherent alternative' escape clause that conflicts with `meta-method-single-source-of-truth`."

Framework has explicit methodology of rejecting unfalsifiable framings at the content-authoring level. F-P2-01 Critical (the framework's own value proposition is unfalsifiable) is thereby **reinforced by the framework's own principle** — applying its own discipline, the Declaration's value claim would need to be either falsifiable or softened. The finding is consistent with framework methodology, not against it.

**A-06 — No findings reversed by Step 10 check.**

All 31 findings survive the post-hoc miss-check. Amendments extend context; none invalidate.

### §D.3 — Threatened-property distribution (Phase 1 only)

| Property | Findings threatening it |
|---|---|
| reliable | F-P1-02 |
| predictable | F-P1-01, F-P1-03, F-P1-04 |
| dependable | F-P1-02, F-P1-04, F-P1-05, F-P1-06 |
| repeatable | F-P1-05, F-P1-06, F-P1-07 |
| effective | F-P1-01, F-P1-02, F-P1-05, F-P1-07, F-P1-08 |
| efficient | — (no Phase 1 finding threatens efficient) |

Preliminary root-cause signal (Phase 1 only): `dependable` and `effective` are the most-threatened properties. Full signal computation with Phase 2 findings in Step 9.




