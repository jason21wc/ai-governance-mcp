# 02 — Phase 2: Content Review

**Verification method:** For each artifact class from §A.4, check whether the content fulfills the role the framework claims for it. Where a meta-principle coherence check is required, the coherence-auditor subagent runs it (§VI); findings are merged inline.

---

## §I — Declaration (`constitution.md:18-53`)

| Spec criterion | Evidence | Verdict |
|---|---|---|
| States purpose | Yes (line 20–24, 32, 38) — "AI has potential…"; problem "knowledge without judgment"; solution "baking in what you're actually trying to achieve" | PASS |
| Articulates founding intent (AI serves human's root-cause intent over surface symptoms) | Yes (line 34) — "An instruction says 'write this document.' Intent says 'produce a document that meets these standards, follows this process, applies these quality checks…'" | PASS |
| Value proposition falsifiable (not merely asserted) | **No.** Line 38 claim: "consistent, reliable results that actually deliver on the potential we all know is there." No test in `tests/` compares framework-guided AI outputs vs. unguided outputs. `tests/benchmarks/baseline_*.json` measure retrieval MRR (the mechanism), not the outcome (output quality with/without framework). `staging/benchmark_ab_test.py` (8 untracked file) is an early A/B skeleton, not wired. | **FAIL — F-P2-01 Critical** |

**F-P2-01 — Value proposition is asserted, not falsifiable**
- **Severity:** Critical (spec Step 8 rule: "Missing = Critical")
- **Category:** ungrounded
- **Threatened:** effective, reliable, predictable
- **Evidence:** `documents/constitution.md:38`; `README.md:1-50` (Problem/Solution frames); absence of comparator test in `tests/` (grep: no file named `*output_quality*`, `*ab_test*`, `*governed_vs_unguided*`, etc.; `tests/benchmarks/` measures retrieval MRR only).
- **Root-cause hypothesis:** framework was built to serve a human stakeholder who has direct observational evidence of improvement ("I wanted what I think everyone…"). The stakeholder's first-hand experience stood in for collective falsifiability. For a framework that aims to be adopted beyond one user, that substitution doesn't scale — adopters need a test harness that measures governed-output quality against baseline. Framework mechanism tests (MRR, recall) verify the plumbing, not the claim.

---

## §II — Preamble (`constitution.md:56-62`)

| Spec criterion | Evidence | Verdict |
|---|---|---|
| Identifies governed subject | "AI" / "the system" / "the person using it" — the governed subject is AI behavior; the person is the recipient of guarantees. | PASS |
| Granting authority | "That architecture, applied to AI, becomes this framework" — authority is claimed by the framework itself under the adopted US-Constitution pattern. Explicit via plan line 30 ("pattern, not analogy"). | PASS (with caveat — see §II.1) |
| Ordered goals match `{reliable, predictable, dependable, repeatable, effective, efficient}` | **Partial.** Preamble names: "reliable, safe, aligned with the standards" — three properties, first is `reliable`. "Predictable" / "dependable" / "repeatable" / "effective" / "efficient" not named in the Preamble. Framework's 5-purpose set (APPRC) is at a different level of abstraction than spec's 6-property set — already noted as F-P1-09. | **AMBIGUOUS** (resolved under F-P1-09; no new finding) |

### §II.1 — Granting-authority caveat

The Preamble's grant of authority is self-referential: the framework grants itself authority via "pattern, not analogy." In §1 terms, the US Constitution's grant is "We the People of the United States, in Order to… do ordain and establish this Constitution" — an external sovereign (the people) grants authority to the framework. The ai-governance Preamble does not name an external sovereign; authority flows from "I borrowed it [the US Constitution]. Not as a metaphor. As an architecture." The author takes authority that the plan file (line 30) acknowledges as "pattern-level adoption."

**F-P2-02 — Preamble lacks an external granting authority; authority is self-referential via pattern-borrowing**
- **Severity:** Low
- **Category:** ambiguity
- **Threatened:** dependable (downstream users may wonder on what ground rules bind them)
- **Evidence:** `documents/constitution.md:56-62` + `.claude/plans/project-constitutional-framework-alignment.md:28-34`.
- **Root-cause hypothesis:** framework is single-authored, so the author's own commitment is the granting authority. For adoption beyond the author, some users will need a more explicit "you are subject to this framework by virtue of X" clause — e.g., "by installing the MCP server, you consent to these rules governing AI actions in your project."

---

## §III — Meta-Principles (Constitution) — coherence dependency check (`constitution.md:125-1050`)

*Primary analysis pending from coherence-auditor (see §VI). Surface-level observations below.*

| Spec criterion | Observation |
|---|---|
| Foundational (each principle not derivable from another) | The Historical Amendments log (constitution.md:1094–1107) documents 13 merges + 7 demotions during v2.8.0 consolidation — a prior pass was made. Not yet re-verified for v4.1.0 additions (Unenumerated Rights, Reserved Powers). |
| Universal (each applies across all domains) | LEARNING-LOG 2026-04-12 entry "Metaphor-Driven Classification" flags risk; v4.1.0 itself reclassified Unenumerated Rights + Reserved Powers from S-Series to G-Series after contrarian pushback. Active discipline evident. |
| Mutually independent (no shared primary FM codes) | Meta-principles use prose "Common Pitfalls or Failure Modes" sections without structured FM codes — unlike kmpd domain which uses `KM-F8`, `KM-F2`, etc. This makes FM-collision audit harder at the meta level. | 
| Jointly sufficient (cover "universal behavioral rules" with no major gaps) | Deferred to coherence-auditor. |

**F-P2-03 — Meta-principles use prose "Common Pitfalls" without structured FM codes, while domain principles use FM codes (KM-F8, MR-F10, etc.). Merge-audit at the meta level is unstructured.**
- **Severity:** Low
- **Category:** ambiguity / inconsistency
- **Threatened:** predictable (harder to do automated overlap detection at meta level)
- **Evidence:** `documents/constitution.md:969-976` etc. (prose failure mode lists); `documents/title-25-kmpd.md` ("KM-F8 Broken Derivation Chain"); `documents/title-40-multimodal-rag.md:342` ("MR-F10").
- **Root-cause hypothesis:** meta-principle admission predated the structured-FM convention used in newer domains. The older prose format was grandfathered when FM codes became standard at the domain level.

---

## §IV — S-Series (`constitution.md:935-1050`)

| Spec criterion | Evidence | Verdict |
|---|---|---|
| Operationally pre-emptive | Each Amendment explicitly states override: Amendment I "non-negotiable preconditions"; II "not a compliance checkbox — core architectural requirement"; III "Accuracy of state must always take priority over task completion". | PASS |
| Veto authority | `constitution.md:86` "Veto Power — overrides ALL other guidance"; supremacy clause line 111 places S-Series first. | PASS |
| Not name-matched to US Bill of Rights | **PARTIAL.** S-Series names mirror US concepts in prose: Amendment I "Due Process, Protection from Unreasonable Search and Seizure"; Amendment II "Equal Protection Clause"; Amendment III "Duty of Candor, Perjury prevention, Whistleblower Protection." Each links to specific US amendments **as illustration** (line 956, 996, 1030). Per LEARNING-LOG 2026-04-12 "Metaphor-Driven Classification", the classification criterion must be operational, not metaphor. The operational criterion (pre-emptive veto) is verified — S-Series content IS operationally pre-emptive. But the framing *invites* the metaphor-conflation risk the LEARNING-LOG explicitly warns against. | **PASS operationally** + ongoing risk flag |

**F-P2-04 — S-Series uses US-Constitutional prose framing (Equal Protection, Due Process, Perjury) which, while operationally pre-emptive, increases risk of future name-match classification errors**
- **Severity:** Low (known risk, active mitigation)
- **Category:** ambiguity
- **Threatened:** predictable (future principle admissions could be misclassified into S-Series on metaphor grounds)
- **Evidence:** `documents/constitution.md:956, 996, 1030` — each Amendment ends with a US-law illustrative paragraph.
- **Mitigation already active:** v4.1.0 reclassified Unenumerated Rights + Reserved Powers out of S-Series after contrarian review (constitution.md:1060). Framework shows awareness; finding is preventive.
- **Root-cause hypothesis:** same "pattern as pedagogical anchor" design choice (plan line 34). Illustrative framing is legitimate; must be balanced by explicit LEARNING-LOG entries — which exist.

---

## §V — Domain Titles (`title-10`, `title-15`, `title-20`, `title-25`, `title-30`, `title-40`)

### §V.1 — Domain stays in-domain (no cross-title overlap)

Each domain-principles file has an explicit **Scope and Non-Goals** section (e.g., `title-10-ai-coding.md:39-60`, `title-25-kmpd.md:39-70`). Out-of-Scope sections cross-reference to other domains ("Software documentation → AI-Coding domain"; "Narrative engagement → Storytelling domain"). Good hygiene.

**PASS** — scope boundaries are explicit and cross-referenced.

### §V.2 — Each domain principle has Constitutional Basis (derivation chain integrity)

| Domain file | `Constitutional Basis` count | `Constitutional Derivation` count | Notes |
|---|---|---|---|
| title-10 ai-coding | 18 | 0 | 12 declared principles; >1:1 because some cite multiple meta-principles |
| title-15 ui-ux | 22 | 0 | ~20 principles; good coverage |
| title-20 multi-agent | 18 | 0 | ~17 principles; good coverage |
| title-25 kmpd | 12 | 0 | 10 principles; 1:1+ coverage |
| title-30 storytelling | 17 | 0 | 15 principles; good coverage |
| **title-40 multimodal-rag** | **1** | **32** | **32 principles; uses different field name** |

Rules-of-procedure §3.5.1 Alias Table (per session-111 memory entry) accepts `Constitutional Derivation` as an alias for `Constitutional Basis`. So the terminology variance is documented — **but it remains the only domain using the alias**, which is inconsistency even if rule-compliant.

**F-P2-05 — `title-40-multimodal-rag.md` alone uses "Constitutional Derivation" as the derivation-chain citation header; all five other domain principle files use "Constitutional Basis"**
- **Severity:** Low
- **Category:** ambiguity / inconsistency
- **Threatened:** predictable (one-off terminology diverges from the other 5 of 6 files)
- **Evidence:** grep counts above; `documents/title-40-multimodal-rag.md:345, 372, 409` etc. show "Constitutional Derivation".
- **Mitigation:** alias already documented in rules-of-procedure §3.5.1 (per memory). Framework allows the variance.
- **Decision point:** normalize on one term (pick `Constitutional Basis`; it is used 5:1) or accept the variance permanently. Accepting permanently means users encounter both names and must know they're synonyms. Documentation minor.

### §V.3 — Each domain has implementing CFR

| Principle file | CFR file | Both present |
|---|---|---|
| title-10 | title-10-ai-coding-cfr.md | ✓ |
| title-15 | title-15-ui-ux-cfr.md | ✓ |
| title-20 | title-20-multi-agent-cfr.md | ✓ |
| title-25 | title-25-kmpd-cfr.md | ✓ |
| title-30 | title-30-storytelling-cfr.md | ✓ |
| title-40 | title-40-multimodal-rag-cfr.md | ✓ |

**PASS.**

### §V.4 — No contradictions with Constitution

Sampling: `title-10-ai-coding.md:12` states Supremacy chain ending in "Methods/Tools (SOPs)" — matches constitution.md:111. Other domain principle files use the same supremacy preamble. No conflicts visible.

**PASS (sample-based).**

---

## §VI — CFR / Methods (per-method statute traceability)

| Spec criterion | Evidence | Verdict |
|---|---|---|
| Every method traces to a statute | Per-method frontmatter carries only `governance_level: federal-regulations`; no `enabling_authority` / `implements_principle` field. Per-method `Applies To:` prose lines name domain principles in text but not in structured/grep-able form. | **FAIL** → collapsed under F-P1-04 |
| No orphans either direction | A grep audit of "Constitutional Basis" count in CFR files: title-10-cfr=7 citations across 9000 lines, title-25-cfr=1 citation, others=0. Most CFR methods do not cite the principle(s) they implement. | **FAIL** → F-P1-04 |
| Cross-reference convention | When citations exist, they take the form of prose links (e.g., "Derived from Context Engineering"). No citation tool validates them. | GAP |

**No new finding** — this is subsumed under F-P1-04 (per-method enabling-authority missing).

---

## §VII — Reference Library

| Spec criterion | Evidence | Verdict |
|---|---|---|
| Maturity tags applied consistently | 13 entries in `reference-library/ai-coding/` all carry `maturity: evergreen`/`current` + `decay_class: framework`/`recipe`/etc. Verified on sample — `pytest-fixture-patterns.md:8` `maturity: evergreen`; `vitest-hoisted-mocks.md:8` similar. | PASS (within ai-coding) |
| Entries generalize (not project-specific) | Entry titles — "Pytest Fixture Patterns," "Next.js Middleware Auth Exemptions," "Supabase SSR Async setAll" — are pattern-level, not project-specific. | PASS |
| Documented promotion pathway exists | `reference-library/ai-coding/_criteria.yaml` (4 auto-capture + 4 suggestion triggers). No cross-domain criteria file. `LEARNING-LOG.md:474-513` Graduated Patterns table documents the destination ladder. | PASS (partial: ai-coding only; see F-P1-07) |

**No new finding** — F-P1-07 covers the single-domain-coverage gap.

---

## §VIII — Rules of Procedure

| Spec criterion | Evidence | Verdict |
|---|---|---|
| Amendment process operational | `rules-of-procedure.md:46` ("methods derive authority from Constitutional principles; they govern HOW the framework itself evolves") + Title 2 "Document Update Workflow" + Part 2.1.1 "Update Flow (11 steps)" per situation-index at lines 96-120. Full workflow not read (time budget). | PASS (by index presence) |
| CHANGELOG amendments traceable to invocations of the process | `constitution.md:1053-1245` is in-file amendment history (Historical Amendments). Each entry names the v-number and the change. **But** whether each amendment was preceded by an `evaluate_governance()` call + rules-of-procedure Part 2.1.1 invocation is not checkable from the log alone — the audit trail is in `governance_audit.log` (separate MCP audit log), not cross-linked in the amendment entry. | **PARTIAL** |

**F-P2-06 — Amendment history entries (constitution.md:1053-1245) name the change and rationale but do not link to the rules-of-procedure process invocation (e.g., audit_id) that authorized the amendment**
- **Severity:** Medium
- **Category:** gap
- **Threatened:** dependable, repeatable
- **Evidence:** `constitution.md:1057-1067` (v4.1.0 entry) — has rationale + changes but no `audit_id` / `PR link` / `rules-of-procedure §X invoked on date Y`.
- **Root-cause hypothesis:** amendment-log convention was established before the MCP audit log existed with stable `audit_id`s. Linking retroactively is effort-intensive; no rule requires forward-linking. Consequence: "is this amendment compliant with rules-of-procedure?" is not answerable from log state.

---

## §IX — Subagent definitions

| Spec criterion | Evidence | Verdict |
|---|---|---|
| Role descriptions match operational behavior | `documents/agents/orchestrator.md:1-70` — explicit tool list, role, boundaries, "never do domain work directly." Matches the orchestrator pattern in CLAUDE.md. 10 agents each have Governance Compliance section citing S-Series veto. | PASS (sample) |
| No charter overlap | `documents/agents/contrarian-reviewer.md` (per earlier grep) explicitly delineates scope vs code-reviewer, security-auditor, coherence-auditor. LEARNING-LOG 2026-02-08 graduated rule: "Cognitive Function Labels Must Be Distinct." Enforcement via human review of PRs; no test. | PASS (with process, not structural) |
| No governance-relevant role without a subagent | 10 agents cover: code-review, security, coherence, continuity, contrarian, docs, orchestrator, tests, validator, voice. **Gap**: no subagent for drift-detection of framework state itself (cross-project, cross-time). `coherence-auditor` checks cross-file at one point-in-time; nothing checks drift across sessions in the adopter project. | PARTIAL |

**F-P2-07 — No subagent covers cross-session drift detection in adopter projects (as distinct from single-point-in-time coherence audit)**
- **Severity:** Low
- **Category:** gap
- **Threatened:** repeatable (cross-session continuity relies on manual SESSION-STATE + PROJECT-MEMORY hygiene, without a specialist to audit drift)
- **Evidence:** `documents/agents/` file list; `continuity-auditor.md` is storytelling-specific (narrative consistency), not governance-drift.
- **Root-cause hypothesis:** framework inherited subagent set from ai-coding + storytelling use cases; cross-session governance drift is a recognized concern (LEARNING-LOG:185-192 multi-mechanism context-degradation) but no dedicated agent watches for it in adopter projects.

---

## §X — Tests (Judicial Review at the code level)

| Spec criterion | Evidence | Verdict |
|---|---|---|
| Cover the framework's claims about itself | `tests/` has 29 modules (1308 passing safe-subset tests). Coverage includes: retrieval quality (MRR), hooks, enforcement, extractor, path resolution, config, server integration, watcher daemon, embedding IPC. **But**: no test validates the Declaration's value-proposition claim (governed-AI > unguided-AI outcomes). See F-P2-01. | PARTIAL (mechanism covered, claim not) |
| Dogfood recursion testable | `tests/test_reference_library.py` + `tests/test_retrieval_quality.py` run the framework's own principles through its retrieval. LEARNING-LOG 2026-04-12 "Dogfooding Catches What Reviews Miss" entry graduated this as practice. | PASS |

No new Phase 2 finding; F-P2-01 captures the gap.

---

## §XI — Prompt → Context → Harness → Intent progression

| Spec criterion | Evidence |
|---|---|
| Explicitly invoked somewhere in the framework text | **NOT FOUND.** `grep -ci "harness" documents/constitution.md documents/rules-of-procedure.md documents/ai-instructions.md CLAUDE.md README.md` returns 0 across all. |

The framework articulates a 3-step progression (`prompt → context → intent`, `constitution.md:26-32`), not the spec's 4-step `prompt → context → harness → intent`. Several readings possible:

1. **Framework is wrong** — "harness" is a load-bearing Intent Engineering concept the framework should name but doesn't.
2. **Spec is stricter than necessary** — the framework's 3-step is sufficient; "harness" was an additional spec-side concept not universal in the literature.
3. **Framework subsumes harness implicitly** — the "harness" (Claude Code hooks, MCP server, enforcement infrastructure) IS what the framework builds but calls it "system of principles, processes, and tools that sit between me and AI" (constitution.md:36) without the "harness" label.

I cannot adjudicate (1) vs (2) vs (3) without external Intent Engineering source material the spec drew from.

**F-P2-08 — Framework does not invoke the term "harness" in its Prompt→Context→Intent progression; spec required 4-step "Prompt→Context→Harness→Intent"**
- **Severity:** Low (definitional; framework is internally consistent with 3-step)
- **Category:** ambiguity (framework vs spec concept alignment)
- **Threatened:** effective (if "harness" names a load-bearing concept missing from the framework's self-description)
- **Evidence:** `documents/constitution.md:26-36`; grep for "harness" returns 0 in constitution.md, rules-of-procedure.md, ai-instructions.md, CLAUDE.md, README.md.
- **Root-cause hypothesis:** framework author adopted the progression from the 2024–2025 prompt-engineering → context-engineering → intent-engineering arc (visible in constitution.md:32). The "harness" label may be more recent or from a different literature branch. Framework's 3-step is consistent; adding "harness" would require either incorporating the concept or explicitly disclaiming it.

---

## §XII — Summary of Phase 2 findings

| ID | Severity | Category | Threatened | One-line |
|---|---|---|---|---|
| F-P2-01 | **Critical** | ungrounded | effective, reliable, predictable | Value proposition asserted, not falsifiable; no outcome-level test |
| F-P2-02 | Low | ambiguity | dependable | Preamble's granting authority is self-referential via pattern-borrowing |
| F-P2-03 | Low | ambiguity | predictable | Meta-principles use prose "Common Pitfalls" while domains use structured FM codes |
| F-P2-04 | Low | ambiguity | predictable | S-Series uses US-Constitutional prose framing, risking future name-match classification |
| F-P2-05 | Low | ambiguity | predictable | `title-40-multimodal-rag.md` alone uses "Constitutional Derivation" vs "Constitutional Basis" elsewhere |
| F-P2-06 | Medium | gap | dependable, repeatable | Amendment log entries don't link to rules-of-procedure process invocations (no audit_id) |
| F-P2-07 | Low | gap | repeatable | No subagent covers cross-session governance drift in adopter projects |
| F-P2-08 | Low | ambiguity | effective | "Harness" term not in framework's 3-step progression; spec required 4-step |

### §XII.1 — Counts

| Severity | Count |
|---|---|
| Critical | 1 (F-P2-01) |
| High | 0 |
| Medium | 1 (F-P2-06) |
| Low | 6 (F-P2-02..F-P2-08 except F-P2-06) |
| **Total** | **8** |

### §XII.2 — Threatened-property distribution (Phase 2 only)

| Property | Findings threatening it |
|---|---|
| reliable | F-P2-01 |
| predictable | F-P2-01, F-P2-03, F-P2-04, F-P2-05 |
| dependable | F-P2-02, F-P2-06 |
| repeatable | F-P2-06, F-P2-07 |
| effective | F-P2-01, F-P2-08 |
| efficient | — |

---

## §VI-A — Coherence-Auditor Output (completed 2026-04-18T~06:30Z, `aadc28c4155d6c47d`)

Full report at `/tmp/claude-501/.../tasks/aadc28c4155d6c47d.output`. Findings merged below using this review's numbering; one-per-cause discipline applied (auditor findings 1 + 5 share root cause → collapsed into F-P2-09).

### F-P2-09 (collapses auditor-1 + auditor-5) — **Risk Mitigation by Design significantly duplicates Non-Maleficence**; shared failure-mode content + near-identical bullets

- **Severity:** High
- **Category:** redundancy
- **Threatened:** predictable, efficient, dependable
- **Evidence:**
  - `documents/constitution.md:754-784` (Risk Mitigation by Design) vs. `documents/constitution.md:939-978` (Non-Maleficence) — "Defense in Depth," "Safest defaults / Secure Defaults," "layered validation / independent layers of defense," "continuous monitoring," "living risk register / audit logging" appear in both.
  - Shared failure-mode content (verbatim-similar):
    - Risk Mitigation `constitution.md:777` "Only considering risks at project end"
    - Non-Maleficence `constitution.md:972` "Treating security and privacy safeguards as late-phase 'bolted on' features"
  - Per LEARNING-LOG 2026-03-29 "Shared Failure Mode Codes Are the Primary Consolidation Signal" (lines 239-245) — shared primary failure-mode content is the strongest merge signal. The surface distinction (Risk Mitigation = governance tier; Non-Maleficence = safety veto) is defensible as framing but not operationally independent.
- **Root-cause hypothesis:** v2.8.0 Phase 1 consolidation (47→34) absorbed some security/risk content into Non-Maleficence (per history line 1103: "Merged Security, Privacy, and Compliance by Default (from G-Series) into S-Series Non-Maleficence"). Risk Mitigation was retained as a separate G-Series principle covering parallel ground. The consolidation didn't go far enough to eliminate the overlap.
- **Coherence-auditor explicitly flagged a potential disagreement with contrarian**: "If the contrarian-reviewer concluded that Risk Mitigation by Design is independent of Non-Maleficence, I disagree based on the shared failure-mode evidence." Contrarian did NOT evaluate intra-constitutional principle overlap — the contrarian's Task 1/Task 2 focused on artifact→§1 mapping, not on independence of meta-principles. No actual disagreement; different scope.

### F-P2-10 (auditor-2) — Discovery Before Commitment ↔ Systemic Thinking boundary overlap

- **Severity:** Medium
- **Category:** ambiguity
- **Threatened:** reliable, repeatable
- **Evidence:** `constitution.md:298-345` (DBC) vs. `349-391` (Systemic Thinking). Line 379-381 attempts to carve responsibilities (DBC = when to reframe; ST = how to think about problems) but reframe-language at DBC 310-315 and ST 365 are near-duplicates. ST is explicitly described as "the underlying reasoning discipline that Discovery draws from" — making DBC partially derivable from ST.
- **Root-cause hypothesis:** Systemic Thinking was added in v2.7.0 (constitution.md:1111) as a consolidation of previously-scattered root-cause content. Its parent-to-DBC relationship creates the overlap risk. Division by carve-out is process-level; one edit on either can erode the boundary.

### F-P2-11 (auditor-3) — Goal-First Dependency Mapping reads as method-level, not principle-level

- **Severity:** Medium
- **Category:** misplacement
- **Threatened:** predictable
- **Evidence:** `constitution.md:683-716` — backward-chaining mechanics with Blocker Scan, Execution Order bullets. Passes universality narrowly; bullets are procedural. v2.8.0 history (`constitution.md:1106`) moved it C-Series → O-Series in v1.1 rather than demoting to methods. Admission Test Q2 (Placement, rules-of-procedure §9.8.1) would flag it for re-examination.
- **Root-cause hypothesis:** Goal-First Dependency Mapping was admitted pre-Admission-Test-maturity. Its re-examination under current admission criteria (particularly Q2) would likely demote it to methods. Not done because the principle is in active use and the re-examination hasn't been scheduled.

### F-P2-12 (auditor-4) — Visible Reasoning & Traceability ↔ Explicit Over Implicit: overlapping "surface assumptions" bullets

- **Severity:** Low
- **Category:** redundancy
- **Threatened:** efficient
- **Evidence:** `constitution.md:478` "Explicitly listing assumptions made when the user's prompt was ambiguous" (Visible Reasoning) vs. `constitution.md:591-592` "surface and clarify any implicit assumptions before proceeding" (Explicit Over Implicit). Division is output-side vs. rule-side but bullet-level language is near-identical.
- **Root-cause hypothesis:** both principles were retained in v2.8.0 with slightly different framings; no one audited bullet-level overlap. Easy to drift further if either is edited without cross-check.

### F-P2-13 (auditor-6) — "Relations" purpose is under-operationalized at constitutional level

- **Severity:** Medium
- **Category:** gap
- **Threatened:** effective, dependable
- **Evidence:**
  - Preamble names Relations as a fundamental governance problem (`constitution.md:45`).
  - Only Structural Foundations (arch-layer: 256-294) and Human-AI Authority (human↔AI: 827-867) operationalize it at constitutional level.
  - Multi-agent↔agent, domain↔domain, agent↔user (beyond authority) relations fall through to domain documents.
  - Full Faith and Credit (`constitution.md:1065`) is a method, not a principle — addresses cross-domain recognition but at the Methods layer only.
- **Consequence noted by auditor:** Preamble-as-interpretive-tiebreaker (added v4.1.0, line 1063-1064) assumes all five purposes are covered in the operative set. If Relations is thin, the tiebreaker function weakens for Relations-heavy edge cases.
- **Root-cause hypothesis:** "Relations" is the youngest of the five purposes to be named at Preamble level (v4.1.0 addition). Coverage at the principle level has not caught up. Per LEARNING-LOG "Demotion Decisions Require Constitutional Coverage Verification" (272-275), this is the same failure mode as the "Rich but Not Verbose Communication" demotion — a purpose declared without verified-principle coverage.

### F-P2-14 (auditor-7) — Historical Amendment v2.8.0 "Rich but Not Verbose Communication" demotion rationale cites insufficient constitutional basis (Resource Efficiency) that was later supplemented by a new principle addition

- **Severity:** Low (cosmetic — history "carries no force of law", line 1055)
- **Category:** ungrounded (in the history record)
- **Threatened:** reliable (historical record accuracy)
- **Evidence:** `constitution.md:1081` cites Resource Efficiency as constitutional basis for demoting "Rich but Not Verbose Communication" to Methods Part 16.5. LEARNING-LOG 2026-03-29 "Demotion Decisions Require Constitutional Coverage Verification" (lines 271-275) documents that this basis was insufficient — the demotion created a gap that was later filled by adding Effective & Efficient Communication (now at `constitution.md:509-544`).
- **Root-cause hypothesis:** amendment log was written contemporaneously with the demotion; retroactive correction wasn't added when the gap was detected and filled. "History does not carry force of law" escape clause removes urgency, but accuracy of the historical record still has value for future amendment decisions — and this is the entry the LEARNING-LOG cites as the origin of the "coverage verification" rule.

### F-P2-15 (auditor-8) — Presentation order of Articles in document body diverges from announced order in Framework Overview

- **Severity:** Medium
- **Category:** loose-end / inconsistency
- **Threatened:** predictable
- **Evidence:**
  - Framework Overview (`constitution.md:127-144`) announces Article I (C-Series) → Article II (O-Series) → Article III (Q-Series) → Article IV (G-Series) → Bill of Rights.
  - Document body: Article I C-Series at line 149, **then Article III Q-Series at line 395**, **then Article II O-Series at line 548**, then Article IV G-Series. Q comes before O in the body.
- **Root-cause hypothesis:** ordering was presumably driven by dependency of content (Q depends less on O than O on Q, or some similar reasoning) rather than nominal Article number. Framework Overview's claim of Article I→II→III→IV sequence is then cosmetically wrong for readers scanning article numbers.

### F-P2-16 (auditor-9) — "Multi-agent collaboration principles reside in the Multi-Agent Domain Principles document" callout at `constitution.md:146` singles out one domain without stating why

- **Severity:** Low
- **Category:** conflict / ambiguity
- **Threatened:** reliable
- **Evidence:** `constitution.md:146` — last sentence of Framework Overview. If the intent is that *all* domain-specific principles live in domain docs (the usual pattern), why is Multi-Agent singled out? Reader-unclear.
- **Root-cause hypothesis:** leftover from v2.8.0 Phase 2 when Multi-Agent principles (MA-Series, 6 principles) were demoted from constitution to domain. At the time, the callout distinguished "principles that used to live here, don't anymore." Post-dissolution of MA-Series (confirmed in F-P2-17), the callout no longer serves that pedagogical purpose but remains in text.

### F-P2-17 (auditor-10) — Amendment log references "MA-Series: Now empty (0 principles). Section header retained for Phase 4 dissolution" (constitution.md:1091) — Phase 4 disposition not narrated in v4.0.0/v4.1.0 entries

- **Severity:** Low
- **Category:** orphan
- **Threatened:** dependable (amendment-narrative completeness)
- **Evidence:** `constitution.md:1091` in v2.8.0 Phase 2 entry; no corresponding "Phase 4: MA-Series dissolved" entry in v4.0.0 (lines 1068-1074) or v4.1.0 (lines 1057-1067).
- **Root-cause hypothesis:** MA-Series dissolution occurred implicitly during a subsequent version bump; no explicit "we completed Phase 4 dissolution" entry was added. Amendment narrative is slightly incomplete as an audit trail.

### §VI-A.1 — Counts added by coherence-auditor

| Severity | Count added |
|---|---|
| Critical | 0 |
| High | 1 (F-P2-09) |
| Medium | 4 (F-P2-10, F-P2-11, F-P2-13, F-P2-15) |
| Low | 4 (F-P2-12, F-P2-14, F-P2-16, F-P2-17) |

### §VI-A.2 — Updated Phase 2 totals

| Severity | Total Phase 2 |
|---|---|
| Critical | 1 (F-P2-01) |
| High | 1 (F-P2-09) |
| Medium | 5 (F-P2-06, F-P2-10, F-P2-11, F-P2-13, F-P2-15) |
| Low | 10 (F-P2-02..F-P2-05, F-P2-07, F-P2-08, F-P2-12, F-P2-14, F-P2-16, F-P2-17) |
| **Total** | **17** |

### §VI-A.3 — Threatened-property distribution (full Phase 2)

| Property | Findings |
|---|---|
| reliable | F-P2-01, F-P2-10, F-P2-14, F-P2-16 |
| predictable | F-P2-01, F-P2-03, F-P2-04, F-P2-05, F-P2-09, F-P2-11, F-P2-15 |
| dependable | F-P2-02, F-P2-06, F-P2-09, F-P2-13, F-P2-17 |
| repeatable | F-P2-06, F-P2-07, F-P2-10 |
| effective | F-P2-01, F-P2-08, F-P2-13 |
| efficient | F-P2-09, F-P2-12 |

Preliminary root-cause signal (Phase 2): `predictable` (7 findings) leads, followed by `dependable` (5) and `reliable` (4). Full synthesis with Phase 1 in Step 9.



