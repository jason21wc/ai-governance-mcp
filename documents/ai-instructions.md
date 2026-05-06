---
version: "4.0.1"
status: "active"
effective_date: "2026-05-05"
domain: "meta"
governance_level: "framework-activation"
---

# AI Governance Framework Activation

**Version:** 4.0.1
**Purpose:** Loader document that activates the governance framework for AI sessions.
**Updated:** 2026-05-03

---

<primary_directive>
Read and follow constitution.md as the governing constitution for all behavior.
</primary_directive>

<domain_activation>
**AI Coding Domain** — When working in AI-assisted software development:
1. Load **title-10-ai-coding.md** as binding domain law (WHAT to achieve)
2. Load **title-10-ai-coding-cfr.md** for operational procedures (HOW to achieve it)

**Domain detection:** If project contains code files, build configurations, or development specifications → AI Coding jurisdiction applies.

**Multi-Agent Domain** — When orchestrating multi-agent workflows:
1. Load **title-20-multi-agent.md** as binding domain law
2. Load **title-20-multi-agent-cfr.md** for operational procedures

**Domain detection:** If task involves multiple AI agents, delegation patterns, or orchestration → Multi-Agent jurisdiction applies.

**Storytelling Domain** — When assisting with narrative communication:
1. Load **title-30-storytelling.md** as binding domain law
2. Load **title-30-storytelling-cfr.md** for operational procedures

**Domain detection:** If task involves creative writing, narrative structure, character development, dialogue, storytelling coaching, or communication using narrative techniques → Storytelling jurisdiction applies.

**Multimodal RAG Domain** — When retrieving and presenting images inline with text:
1. Load **title-40-multimodal-rag.md** as binding domain law
2. Load **title-40-multimodal-rag-cfr.md** for operational procedures

**Domain detection:** If task involves retrieving reference images, presenting visual materials inline with text responses, or procedural documentation with screenshots → Multimodal RAG jurisdiction applies.

**UI/UX Domain** — When building or reviewing interactive software interfaces:
1. Load **title-15-ui-ux.md** as binding domain law
2. Load **title-15-ui-ux-cfr.md** for operational procedures

**Domain detection:** If task involves UI design, accessibility, responsive layouts, design systems, component libraries, or visual hierarchy → UI/UX jurisdiction applies.

**Knowledge Management & People Development Domain** — When creating organizational knowledge or training:
1. Load **title-25-kmpd.md** as binding domain law
2. Load **title-25-kmpd-cfr.md** for operational procedures

**Domain detection:** If task involves knowledge bases, SOPs, training materials, cross-training matrices, job descriptions, or onboarding programs → KM&PD jurisdiction applies.

**Note:** Domains can overlap. Multiple domains may apply simultaneously (e.g., AI Coding + Multi-Agent when agents perform coding tasks).
</domain_activation>

<methods_activation>
**AI Coding workflow** (when AI Coding domain is active):
1. Check for **SESSION-STATE.md** in project root
2. If exists: Load state, resume from documented position
3. If new project: Execute Cold Start Kit (see Methods §Cold Start Kit)
4. Follow 4-phase workflow: **Specify → Plan → Tasks → Implement**
5. Create Gate Artifacts at each phase transition

Other domains: Load the corresponding CFR document for operational procedures.
</methods_activation>

<first_response_protocol>
Your first response in every conversation MUST begin with:
"Framework active. Jurisdiction: [AI Coding | UI/UX | Multi-Agent | KM&PD | Storytelling | Multimodal RAG | Multiple | General]. Ready."

If AI Coding jurisdiction:
- State current phase (from SESSION-STATE.md) or "New Project"
- State procedural mode if known (Expedited/Standard/Enhanced)

If UI/UX jurisdiction:
- State design system context if known
- State accessibility requirements if known

If Multi-Agent jurisdiction:
- State orchestration pattern if known (Sequential/Parallel/Hierarchical)
- State active agents from context files

If KM&PD jurisdiction:
- State pillar focus (Manage Process / Lead People)
- State artifact type if known

If Storytelling jurisdiction:
- State mode if known (Generate/Coach)
- State target medium if known

If Multimodal RAG jurisdiction:
- State reference document availability

Then address the user's request.
</first_response_protocol>

<recovery_trigger>
When user says "framework check":
1. Re-read governance documents (constitution + domain + methods)
2. Output current framework status including:
   - Jurisdiction
   - Current phase
   - Procedural mode
   - Active task or blocker
3. Resume with refreshed compliance
</recovery_trigger>

<operational_requirements>
Follow the Operational Application Protocol:
- Cite principles when they influence significant decisions
- Pause and request clarification when specification gaps are detected
- Check SESSION-STATE.md and PROJECT-MEMORY.md before claiming lack of context
- Follow domain-specific escalation triggers (see Methods §8.1)
- Create Gate Artifacts before phase transitions (see Methods §Gate Artifacts)
</operational_requirements>

<governance_hierarchy>

| Layer | Framework Element | Authority |
|---|---|---|
| **Bill of Rights** | S-Series (Safety Principles) in constitution.md | **Veto Power** — overrides ALL other guidance |
| **Constitution** | Meta-Principles (C, Q, O, G Series) in constitution.md | **Foundation** — domain-agnostic reasoning laws |
| **Federal Statutes** | Domain Principles (title-NN-domain.md) | **Context** — derived from Constitution for specific fields |
| **Rules of Procedure** | rules-of-procedure.md | **Process** — how principles are applied and maintained |
| **Federal Regulations** | Domain Methods (title-NN-domain-cfr.md) | **Execution** — implementation details |
| **Agency SOPs** | CLAUDE.md, GEMINI.md, project configs | **Tactical** — platform-specific guidance |
| **Secondary Authority** | Reference Library | **Informative (non-overriding)** — concrete artifacts that inform interpretation |

**Domain Files** (select applicable for Federal Statutes + Federal Regulations):
- title-10-ai-coding.md (15 principles) / title-10-ai-coding-cfr.md
- title-15-ui-ux.md (20 principles) / title-15-ui-ux-cfr.md
- title-20-multi-agent.md (17 principles) / title-20-multi-agent-cfr.md
- title-25-kmpd.md (10 principles) / title-25-kmpd-cfr.md
- title-30-storytelling.md (15 principles) / title-30-storytelling-cfr.md
- title-40-multimodal-rag.md (32 principles) / title-40-multimodal-rag-cfr.md

**Supremacy Rule:** Higher layers override lower. If conflict: **Bill of Rights** > **Constitution** > **Statutes** > **Rules of Procedure** > **Regulations** > **SOPs**. Secondary Authority informs interpretation but does not override normative layers.
</governance_hierarchy>

<memory_architecture>
AI Coding domain uses three memory files for session continuity:

| File | Purpose | Load Frequency |
|------|---------|----------------|
| **SESSION-STATE.md** | Current position, next actions | Every session start |
| **PROJECT-MEMORY.md** | Decisions, architecture, constraints | When relevant to current work |
| **LEARNING-LOG.md** | Lessons learned, patterns | When similar situation arises |

Create these files in the **project repository root** using templates in Methods §Cold Start Kit. These are project artifacts tracked in version control — they are NOT platform-native memory (e.g., Claude Code's `~/.claude/projects/*/memory/MEMORY.md`, Cursor's `.cursor/rules/`). The project instructions file (CLAUDE.md, etc.) is the one overlap point between governance and the platform's memory system.
</memory_architecture>

<quick_reference>
## Immediate Escalation Triggers
- S-Series (Safety) violation detected → STOP, flag, request guidance
- Specification gap preventing safe execution → Pause, clarify before proceeding
- Multiple valid approaches with significant implications → Present options to Product Owner
- Security vulnerability (HIGH/CRITICAL) → Block, do not defer
- Gate checklist item cannot be checked → Return to phase, address deficiency

## Decision Authority
- Technical implementation details → AI proceeds autonomously
- Product/business decisions → Escalate with options and recommendation
- Phase validation gates → Require Product Owner approval via Gate Artifact

## Phase Workflow
```
SPECIFY ──[GATE]──→ PLAN ──[GATE]──→ TASKS ──[GATE]──→ IMPLEMENT ──[GATE]──→ COMPLETE
```
</quick_reference>

<mcp_integration>
When AI Governance MCP server is available (check for `ai-governance` in MCP tools):

**Server Instructions:** The MCP server provides behavioral guidance during initialization. This includes governance hierarchy, key behaviors, and usage guidance. If you have access to ai-governance tools, you've already received these instructions.

**Use semantic retrieval instead of full document loading:**
1. Query `query_governance` for relevant principles based on current task
2. Use `get_principle` for full details when needed
3. Use `list_domains` to see available governance domains

**Benefits:** ~98% token savings, <100ms retrieval, smart domain routing.

**Example:** Instead of loading full title-10-ai-coding-cfr.md, query:
```
query_governance("how to handle incomplete specifications")
→ Returns: Specification Completeness principle + relevant methods
```

**Note:** Server instructions provide orientation; tools provide detailed content.
</mcp_integration>

<document_versions>
This loader is designed for use with:
- constitution.md v8.0.0+
- rules-of-procedure.md v3.31.5+
- title-10-ai-coding.md v2.8.0+
- title-10-ai-coding-cfr.md v2.44.0+
- title-20-multi-agent.md v2.7.3+
- title-20-multi-agent-cfr.md v2.17.3+
- title-30-storytelling.md v1.4.2+
- title-30-storytelling-cfr.md v1.1.3+
- title-15-ui-ux.md v1.2.2+
- title-15-ui-ux-cfr.md v1.0.0+
- title-25-kmpd.md v1.4.2+
- title-25-kmpd-cfr.md v1.2.0+
- title-40-multimodal-rag.md v2.4.3+
- title-40-multimodal-rag-cfr.md v2.1.3+
</document_versions>

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 4.0.1 | 2026-05-05 | PATCH: title-10-ai-coding.md pin update v2.7.6+ → v2.8.0+ and title-10-ai-coding-cfr.md pin update v2.43.3+ → v2.44.0+ for AI Coding Design Philosophy Integration (3 new principles, 8 new CFR methods, preamble addition, existing principle extensions). Updated principle count reference 12→15. PATCH-on-MINOR per BACKLOG #130 canonical pin-discipline rule. Governance: `gov-07287670fb01`. |
| 4.0.0 | 2026-05-03 | MAJOR: constitution.md pin update v7.0.0+ to v8.0.0+ for BACKLOG #152 (principle rename: `meta-core-context-engineering` to `meta-core-informational-readiness`). MAJOR-on-MAJOR per BACKLOG #130 canonical pin-discipline rule (constitution MAJOR source = ai-instructions MAJOR consequence). Constitutional change: Art. I section 1 renamed from "Context Engineering" to "Informational Readiness" and reframed from procedural implementation guidance to universal reasoning obligation. ID changed; alias preserves backward compatibility. Motivation: v7.0.0's 5-layer stack adoption created naming collision — "Context Engineering" now specifically means layer 3, but the principle governs layers 2-4. Constitutional Basis: `meta-core-systemic-thinking` (root cause = naming collision creating governance scope narrowing risk), `meta-core-informational-readiness` (reframing preserves obligation while correcting label), `meta-quality-verification-validation` (alias regression test + retrieval benchmark validation). Contrarian: `aab157aa58b78ba36` (PROCEED WITH MODIFICATIONS, HIGH confidence). Cascading PATCHes applied to 10 domain files (name-string-only propagation): title-10 v2.7.6, title-15 v1.2.2, title-20 v2.7.3, title-25 v1.4.2, title-30 v1.4.2, title-40 v2.4.3, title-10-cfr v2.43.3, title-20-cfr v2.17.3, title-30-cfr v1.1.3, rules-of-procedure v3.31.5. Governance: `gov-466045fd5dbd`, `gov-d05cd633fc20`, `gov-97a116b020b2`. |
| 3.0.0 | 2026-05-02 | MAJOR: constitution.md pin update v6.0.1+ → v7.0.0+ for BACKLOG #151 (F-P2-08 reversal — 5-layer engineering stack adopted as canonical model, replacing 3-step AI Interaction Model). MAJOR-on-MAJOR per BACKLOG #130 canonical pin-discipline rule (constitution MAJOR source = ai-instructions MAJOR consequence). Constitutional change: "AI-Interaction Model (3-step canonical)" subsection replaced with "AI Engineering Stack (5-layer canonical)" — Prompt → Retrieval → Context → Harness → Intent. README §"Why this exists" designated as SSOT for layer definitions. v5.0.6 F-P2-08 disposition reversed with documented rationale (narrower 4-step proposal evaluated, harness operationally distinct from Context Engineering). New Historical Amendment entry v7.0.0 supersedes v5.0.6 entry (preserved immutable). Constitutional Basis: `meta-core-systemic-thinking` (structural cause = constitution carries factually-wrong disposition about an abstraction it has evolved past), `meta-core-context-engineering` (principle scope spans both retrieval and context assembly — broader than any single 5-layer layer), `meta-quality-verification-validation` (3 Explore agents + 2 contrarian rounds + coherence audit verified evidence). Governance: `gov-225dda764f95`. |
| 2.11.6 | 2026-05-01 | PATCH: rules-of-procedure.md pin update v3.31.3+ → v3.31.4+ for BACKLOG #147 post-double-check fold-in remediation (new §7.8.1 "Reactive vs Proactive Work-Class Distinction" canonical method-level home + cross-refs from CLAUDE.md Behavioral Floor + contrarian-reviewer Boundaries/Step-0.5 + tiers.json proportional-rigor directive). PATCH-on-PATCH per BACKLOG #130 canonical pin-discipline rule. Driven by post-edit subagent battery on prior commit `0911534` (validator APPROVE + coherence-auditor 1 HIGH + 2 MEDIUM + 2 LOW + contrarian-reviewer 2 HIGH + 2 MEDIUM PROCEED_WITH_CAUTION) finding the original #147 close left three half-statements without canonical home. Constitutional Basis: `meta-method-single-source-of-truth`, `meta-core-systemic-thinking`, `meta-quality-explicit-over-implicit`, `meta-quality-verification-validation`. Governance: `gov-e1c50d38e20f` (this remediation), `gov-20dcbdd98f9e` (parent #147 close). |
| 2.11.5 | 2026-04-28 | PATCH: rules-of-procedure.md pin update v3.31.2+ → v3.31.3+ for BACKLOG #100 Commit 6 (deferred LOW + MEDIUM findings addressed: §9.7.7 register-integrity rules + §9.8.9 citation-discipline subsection + BACKLOG #144 filed for CI check D2 follow-up). PATCH-on-PATCH per BACKLOG #130 canonical pin-discipline rule. Per user directive "we shouldn't be deferring low findings" — applied per CLAUDE.md Defer-vs-Fix-Now (≤3 files, no cascading discovery, known fixes). Constitutional Basis: `meta-method-single-source-of-truth`, `meta-quality-verification-validation`, `meta-core-systemic-thinking`. Governance: `gov-fd820e2fd260` (parent post-arc remediation arc). |
| 2.11.4 | 2026-04-28 | PATCH: rules-of-procedure.md pin update v3.31.1+ → v3.31.2+ for BACKLOG #100 post-arc remediation (apply §9.8.9 spec to host file: 6 method-level analogies removed; add Rules of Procedure register row; fix Stare Decisis citation; fix 2 stale F-P2-04 narrative surfaces; add §9.7.1 SSOT cross-reference). PATCH-on-PATCH per BACKLOG #130 canonical pin-discipline rule. Findings caught by post-arc double-check audit (contrarian `a7a951cb33f490ada` + coherence-auditor `aa443ab0670fe55a8`) — internal self-consistency gap that prior batteries missed (arc shipped spec without applying to host file). Constitutional Basis: `meta-method-single-source-of-truth`, `meta-quality-verification-validation`, `meta-core-systemic-thinking`. Governance: `gov-fd820e2fd260`. |
| 2.11.3 | 2026-04-28 | PATCH: rules-of-procedure.md pin update v3.31.0+ → v3.31.1+ for BACKLOG #100 Commit 4 close-out (line-citation drift fix in §9.7.7 register + §9.8.9 placement targets + §9.8.1 Q7 PASS exemplar). PATCH-on-PATCH per BACKLOG #130 canonical pin-discipline rule. Drift caught by final coherence-auditor pass (`a6649bf7aee986477`) — citations shifted +2 lines after Commit 2's SSOT note + analogy removals; corrections aligned to actual file headers. Constitutional Basis: `meta-method-single-source-of-truth`, `meta-quality-verification-validation`. Governance: `gov-08a1271476d3` (parent execution). |
| 2.11.2 | 2026-04-28 | PATCH: title-10-ai-coding.md pin update v2.7.4+ → v2.7.5+ for BACKLOG #100 Commit 3 of 4-arc (removal of 12 misplaced principle-level analogies per §9.8.9 eligibility rule). PATCH-on-PATCH per BACKLOG #130 canonical pin-discipline rule. Per-instance wisdom-check confirmed no irreplaceable wisdom in any of the 12 blocks (anchor-bias warning honored). Constitutional Basis: `meta-method-single-source-of-truth` (canonical home for analogies). Governance: `gov-08a1271476d3` (parent execution). |
| 2.11.1 | 2026-04-28 | PATCH: constitution.md pin update v6.0.0+ → v6.0.1+ for BACKLOG #100 Commit 2 of 4-arc (SSOT designation note at constitution.md:84-92 Operative Hierarchy + removal of 3 misplaced principle-level analogies at lines 397/608/1025). PATCH-on-PATCH per BACKLOG #130 canonical pin-discipline rule. Per-instance wisdom-check confirmed no irreplaceable wisdom before removal (anchor-bias warning honored). Constitutional Basis: `meta-method-single-source-of-truth` (canonical translation table designated). Governance: `gov-08a1271476d3` (parent execution). |
| 2.11.0 | 2026-04-27 | MINOR: rules-of-procedure pin update v3.30.2+ → v3.31.0+ for BACKLOG #100 spec layer (new §9.7.7 Constitutional Analogy Register + new §9.8.9 Legal System Analogy Authoring). MINOR-on-MINOR per BACKLOG #130 canonical pin-discipline rule (RoP MINOR source = ai-instructions MINOR consequence). Governance trail: `gov-3a7f9c645742` (round 1 design eval), `gov-08a1271476d3` (execution eval). Constitutional Basis: `meta-method-single-source-of-truth` (pin currency for adopters), `meta-core-systemic-thinking` (canonical pin-discipline rule applied recursively). |
| 2.10.5 | 2026-04-26 | PATCH: Pin tracks PATCH bump from BACKLOG #142 close — `rules-of-procedure.md v3.30.1 → v3.30.2` (§9.8.3 "Known Limitation" footnote at line 2842 updated to reflect post-#136 reality: backfill across 9 platform-specific appendices completed 2026-04-26, footnote now enumerates the 9 appendices explicitly and clarifies out-of-scope retention rationale). Bumped `rules-of-procedure.md v3.30.1+` → `v3.30.2+`. **PATCH-on-PATCH per canonical pin-discipline rule** (BACKLOG #130 close, COMPLETION-CHECKLIST item 7c). Source bump is PATCH because single-paragraph drift fix on existing footnote — schema itself unchanged, rule itself unchanged. CLAUDE.md Behavioral Floor + tiers.json directives both unchanged — this PATCH operates entirely below the rule-abstraction level (the §9.8.3 schema was always the rule; the footnote was the descriptive metadata about backfill status). Body-header v2.10.4 → v2.10.5 + frontmatter version + Updated date all synced per §2.1.1 Step 3 + COMPLETION-CHECKLIST item 7c (a)/(b)/(c). Governance: `gov-9f9aaed15df5`. |
| 2.10.4 | 2026-04-26 | PATCH: Pin tracks PATCH bump from session-135 pre-push harmonization — `title-10-ai-coding.md v2.7.3 → v2.7.4` (migration form on §825 harmonized with §7.12.2 worked-example pattern + CFR-class precedent commit `32ff553`: `plan exceeds D2 effort tier per meta-method-effort-not-time-estimation (rules-of-procedure §7.12.2)` → `plan exceeds D2 (new tool/hook/section, moderate research, plan mode required) per meta-method-effort-not-time-estimation`). Bumped `title-10-ai-coding.md v2.7.3+` → `v2.7.4+`. **PATCH-on-PATCH per canonical pin-discipline rule** (BACKLOG #130 close, COMPLETION-CHECKLIST item 7c). Source bump is PATCH because pure form harmonization with no semantic change. Filed by pre-push contrarian audit `a7f6f57bc2ef0d5c1` MEDIUM-1 on the in-flight session-135 commit `2e4533c` — caught before push to avoid the "consistent post-commit drift class" pattern (LEARNING-LOG 2026-04-20) where post-commit drift gets harmonized in a follow-up PATCH days later. CLAUDE.md Behavioral Floor "Effort, not time" + tiers.json `effort-not-time` directive both unchanged. Body-header v2.10.3 → v2.10.4 + frontmatter version + Updated date all synced per §2.1.1 Step 3 + COMPLETION-CHECKLIST item 7c (a)/(b)/(c). Governance: `gov-a8c7e0faed4e` (same audit_id as v2.10.3 — same task arc). |
| 2.10.3 | 2026-04-26 | PATCH: Pin tracks PATCH bump from BACKLOG #141 close — `title-10-ai-coding.md v2.7.2 → v2.7.3` (§7.12 sweep extension to principle-file class: migrated `Atomic Task Decomposition` Task Sizing Assessment item 2 from `>2 hours focused work` to `plan exceeds D2 effort tier per meta-method-effort-not-time-estimation §7.12.2`). Sweep across the 6 domain-principle files (title-10/15/20/25/30/40-*.md, non-cfr) confirmed this is the single residual; all other time-unit references are descriptive prose, real-world operational facts (rate limits, retention periods, throughput metrics), example narratives in failure-mode illustrations, or operational characteristics of agent types — none fall within §7.12 scope. File:line citations enumerated in `title-10-ai-coding.md` v2.7.3 changelog row for spot-check verifiability. Bumped `title-10-ai-coding.md v2.7.2+` → `v2.7.3+`. **PATCH-on-PATCH per canonical pin-discipline rule** (BACKLOG #130 close, COMPLETION-CHECKLIST item 7c). Source bump is PATCH because compliance migration with no normative change to principle behavior — mirrors v2.10.1 PATCH-on-PATCH rationale for the CFR-class sweep (BACKLOG #131). CLAUDE.md Behavioral Floor "Effort, not time" + tiers.json `effort-not-time` directive both unchanged — this completes the compliance migration that v2.10.1 began on the CFR side. Body-header v2.10.2 → v2.10.3 + frontmatter version + Updated date all synced per §2.1.1 Step 3 + COMPLETION-CHECKLIST item 7c (a)/(b)/(c). Governance: `gov-a8c7e0faed4e`. |
| 2.10.2 | 2026-04-26 | PATCH: Pin tracks coordinated PATCH bumps from BACKLOG #136 close (§9.8.3 field backfill across 3 CFR files): `title-10-ai-coding-cfr.md v2.43.1 → v2.43.2` (5 platform-specific appendices: A Claude Code, D Gemini CLI, E Claude App, I Postgres/Supabase, K AGENTS.md), `title-20-multi-agent-cfr.md v2.17.1 → v2.17.2` (3 platform-specific appendices: A Claude Code, B Gemini CLI, C Codex CLI), `title-40-multimodal-rag-cfr.md v2.1.2 → v2.1.3` (1 platform-specific appendix: A Claude vision). Bumped `title-10-ai-coding-cfr.md v2.43.1+` → `v2.43.2+`, `title-20-multi-agent-cfr.md v2.17.1+` → `v2.17.2+`, `title-40-multimodal-rag-cfr.md v2.1.1+` → `v2.1.3+` (latter also corrects a pre-existing pin lag at v2.1.1 — actual source was v2.1.2 since 2026-04-14; both lag and new bump folded into one pin update). **PATCH-on-PATCH per canonical pin-discipline rule** (BACKLOG #130 close, COMPLETION-CHECKLIST item 7c). All 3 source bumps are PATCH because §9.8.3 fields are descriptive metadata for adopter discoverability — no normative change to appendix procedural content. Body-header v2.10.1 → v2.10.2 + frontmatter version + Updated date all synced per §2.1.1 Step 3 + COMPLETION-CHECKLIST item 7c (a)/(b)/(c). Governance: `gov-21ee559d88f0`. |
| 2.10.1 | 2026-04-26 | PATCH: Pin tracks coordinated PATCH bumps from BACKLOG #131 sweep — `rules-of-procedure.md v3.30.0 → v3.30.1` (§7.12 worked migration example added + anti-example genericized) + `title-10-ai-coding-cfr.md v2.43.0 → v2.43.1` (6 planning-band time-unit estimates migrated to effort indicators in §2.1.2 + §3.1.2, bringing existing checklist content into compliance with §7.12 rule shipped v3.28.0). Bumped `rules-of-procedure.md v3.30.0+` → `v3.30.1+` and `title-10-ai-coding-cfr.md v2.43.0+` → `v2.43.1+`. **PATCH-on-PATCH per canonical pin-discipline rule** (BACKLOG #130 close, COMPLETION-CHECKLIST item 7c). Both source bumps are PATCH because: (rules-of-procedure) descriptive addition of one worked example + drift-fix on existing anti-example, no new rule; (title-10) compliance migration with no normative change. CLAUDE.md Behavioral Floor "Effort, not time" + tiers.json `effort-not-time` directive both unchanged — they operate at the rule-abstraction level the new worked example illustrates. Body-header v2.10.0 → v2.10.1 + frontmatter version + Updated date all synced per §2.1.1 Step 3 + COMPLETION-CHECKLIST item 7c (a)/(b)/(c). Governance: `gov-21ee559d88f0`. |
| 2.10.0 | 2026-04-26 | MINOR: Pin tracks rules-of-procedure.md MINOR bump v3.29.0 → v3.30.0 (BACKLOG #139 close — expanded Part 7.13 BLUF-Pyramid Briefing to close 6 gaps vs. Minto / AR 25-50 / Brief Lab consensus: SCQA opening scaffold, MECE check on options, single-governing-thought roll-up rule, repetition rule via new required "Close" section, false-BLUF detector requiring verb-based directives, and new §7.13.7 AI-specific anti-LLM-default framing). Bumped `rules-of-procedure.md v3.29.0+` → `v3.30.0+`. **MINOR-on-MINOR per canonical pin-discipline rule** (BACKLOG #130 close, commit `4762962`, COMPLETION-CHECKLIST item 7c, codified from contrarian round-2 HIGH-2 in v2.8.0 entry). Source rules-of-procedure went MINOR; pin direction matches source direction. **Note on framing:** v3.30.0 is *additive but tightening* — the new required Close section and false-BLUF rejection mean v3.29.0-form briefs without a Close or with topic-statement openings would FAIL v3.30.0 validation. This is not a strict subset relationship; it is a tightening, and MINOR is the canonical bump for a tightening. Earlier rationale that referenced "v2.9.1 alias-preserved subset pattern" was rejected per session-133 contrarian-reviewer HIGH-2 (`a8648ee322443f496`) which flagged the framing as cargo-culting v2.9.1's deviation — the v2.8.1-v2.8.4 family of justifications #130 ruled out are structurally identical. Body-header v2.9.0 → v2.10.0 corrects session-131 (`0bd0a9b`) frontmatter lag along the way: changelog already had v2.9.1 row dated 2026-04-26 but body-header still showed v2.9.0 (recurrence of the v2.7 dogfood failure on §2.1.1 Step 3 frontmatter-must-match rule); jumping v2.9.0 → v2.10.0 directly fixes the lag. CLAUDE.md Behavioral Floor "BLUF for user-facing briefs" + tiers.json `bluf-pyramid-briefing` directive both unchanged — they operate at the abstraction level the new sub-rules ride along under via the §7.13 reference (universal-floor granularity is correct: SCQA/MECE/false-BLUF are decision-brief-specific, not universal-action checks). Governance: `gov-5839fdf4195e`. |
| 2.9.1 | 2026-04-26 | PATCH: Pin tracks coordinated v6.0.0 governance rename — constitution.md v5.0.7 → v6.0.0 (MAJOR: rename and rescope of Art. III §4 from "Effective & Efficient Communication" to "Effective & Efficient Outputs"), rules-of-procedure.md v3.28.2 → v3.29.0 (MINOR: new §16.7 Solution Comparison via Effectiveness × Efficiency Product method), and 4 domain title PATCHes (title-10 v2.7.2, title-15 v1.2.1, title-20 v2.7.2, title-25 v1.4.1 — crosswalk row additions for the renamed principle), plus title-40 v2.4.1 → v2.4.2 (changelog-only entry per scope carve-out, no crosswalk row). Pin bump is PATCH because the cross-doc effect on adopters is alias-preserved (pre-v6.0.0 ID `meta-quality-effective-efficient-communication` resolves to the rescoped principle via the new extractor `_parse_principle_aliases` mechanism); no breaking change to retrieval. Plan: `~/.claude/plans/this-is-back-and-tidy-crescent.md`. PROJECT-MEMORY.md ADR-17. Governance: `gov-64ecfb9372df`, `gov-e38a3fa7488c`, `gov-05de0fadc801`. |
| 2.9.0 | 2026-04-25 | MINOR: Pin tracks title-10-ai-coding-cfr.md MINOR bump v2.42.3 → v2.43.0 (BACKLOG #57 close — new §3.3.4 Status Bar Plugin sub-paragraph + new Appendix M Optional Ecosystem Tools with M.1 Warp Terminal and M.2 Sequential Thinking MCP Server + Appendix A.4 cross-reference to M.2). Bumped `title-10-ai-coding-cfr.md v2.42.3+` → `v2.43.0+`. MINOR-on-MINOR per canonical pin-discipline rule (COMPLETION-CHECKLIST item 7c) — title-10 source is MINOR (additive normative method content: new sub-paragraph in §3.3.4 + new Appendix M; no breaking change to existing protocol structure or numbering). Body-header + effective-date synced per §115-canonicalized checklist item. Governance: `gov-3116c50bb6e7`. |
| 2.8.8 | 2026-04-25 | PATCH: Pin tracks title-10-ai-coding-cfr.md PATCH bump v2.42.2 → v2.42.3 (BACKLOG #133 close — replaced literal stale `AI Coding Methods v2.30.0` framework pins in three template surfaces with the established `(current version)` placeholder convention from §7.4.3 Minimal Loader Template; rot-immune fix). Bumped `title-10-ai-coding-cfr.md v2.42.2+` → `v2.42.3+`. PATCH-on-PATCH per canonical pin-discipline rule (COMPLETION-CHECKLIST item 7c). Surfaces fixed: title-10 Appendix A.1 (`:7390`), Appendix K.2 (`:8559`), and `src/ai_governance_mcp/server.py:765` SCAFFOLD_AGENTS_MD (was `v2.28.0`, 14 MINOR stale). Governance: `gov-7083d6c85ffc`. |
| 2.8.7 | 2026-04-25 | PATCH: Pin tracks rules-of-procedure.md PATCH bump v3.28.1 → v3.28.2 (scope clarification to §7.12.1 5th exception — added explicit anti-example for planning-band time estimates + distinguishing test, per post-ship contrarian battery `abd327fd5e8174348` HIGH-leverage finding). Bumped `rules-of-procedure.md v3.28.1+` → `v3.28.2+`. PATCH-on-PATCH per canonical pin-discipline rule (COMPLETION-CHECKLIST item 7c). No title-10-cfr re-bump needed: §5.1.8's verbatim quote of the 5th exception is the v3.28.1 form (no anti-example), which is correct because §5.1.8's case is exactly the type of research-anchored threshold the exception covers (process-trigger, not planning-band — anti-example doesn't apply); citation already includes "(canonicalized v3.28.1)" provenance stamp. Governance: `gov-0d9f7303cbd5`. |
| 2.8.6 | 2026-04-25 | PATCH: Two pin updates bundled (both PATCH-on-PATCH per canonical pin-discipline rule codified BACKLOG #130 close, COMPLETION-CHECKLIST item 7c). (1) `rules-of-procedure.md v3.28.0+` → `v3.28.1+` (closes BACKLOG #132 — added 5th explicit exception to §7.12.1 Scope for "Research-anchored operational thresholds" — runtime/turn/iteration values from empirical research used as process gates, not effort estimates). (2) `title-10-ai-coding-cfr.md v2.42.1+` → `v2.42.2+` (citation chain closure: §5.1.8 + COMPLETION-CHECKLIST 16a switched from "by analogy with §7.12.1" to direct citation of the now-canonicalized 5th exception). Both bumps PATCH-on-PATCH per canonical rule (single-bullet additive subsection in rules-of-procedure; citation update only in title-10 — no normative change to existing rules). Governance: `gov-adbf247c0f44`. |
| 2.8.5 | 2026-04-25 | PATCH: Pin tracks title-10-ai-coding-cfr.md PATCH bump v2.42.0 → v2.42.1 (process-integrity strengthening per post-ship contrarian battery audit `a62e96c04a3f91721` — §5.1.8 step 3 written-artifact requirement closes checkpoint-theater meta-loop; §1.3.5 ENHANCED-OR-no-precedent override closes AI-under-calibration anchor-bias gap). Bumped `title-10-ai-coding-cfr.md v2.42.0+` → `v2.42.1+`. PATCH pin bump on PATCH target — both source and pin are PATCH (rule semantics strengthened, no breaking change to existing protocol structure). **[NOTE 2026-04-25 per BACKLOG #130 close (commit `4762962`)]:** v2.8.5 is correctly PATCH-on-PATCH per the canonical pin-discipline rule (COMPLETION-CHECKLIST item 7c) — title-10 source was PATCH (v2.42.0 → v2.42.1), so PATCH pin is correct. Unlike the v2.8.1-v2.8.4 misbumps (which were PATCH-on-MINOR), v2.8.5 was always correct under the canonical rule; the previous "until #130 ships" note was struck since the canonical rule is now codified. Governance trail: `gov-71c1d6662fa7`. |
| 2.8.4 | 2026-04-25 | PATCH: Pin tracks title-10-ai-coding-cfr.md MINOR bump v2.41.0 → v2.42.0 (new §5.1.8 Mid-Execution Checkpoint Protocol — bridges pre/post-action gate gap for long-running plans; concept in title-10, tunable threshold in `workflows/COMPLETION-CHECKLIST.md` per SSOT pattern; orchestrator agent + .claude copy + AGENT_TEMPLATE_HASHES regenerated to reflect mid-execution checkpoint discipline addition — per plan `~/.claude/plans/federated-plotting-karp.md` Commit 7 of 8). Bumped `title-10-ai-coding-cfr.md v2.41.0+` → `v2.42.0+`. PATCH pin bump on MINOR target per current pin discipline (BACKLOG #130 tracks the discipline self-contradiction follow-up). Governance trail: `gov-b95156c01466`. |
| 2.8.3 | 2026-04-25 | PATCH: Pin tracks title-10-ai-coding-cfr.md MINOR bump v2.40.0 → v2.41.0 (new §1.3.5 Brainstorming Method ENHANCED-mode-only — Socratic Q&A discovery + design-doc artifact + plan-mode hand-off; folded §4.1.2 Task Characteristics fix replacing time-based "Estimable" row with effort-shaped row pointing at plan-template + rules-of-procedure §7.12 — per plan `~/.claude/plans/federated-plotting-karp.md` Commit 4 of 8). Bumped `title-10-ai-coding-cfr.md v2.40.0+` → `v2.41.0+`. PATCH pin bump on MINOR target per current pin discipline (additive normative subsection; see BACKLOG #130 for the Changelog pin-discipline self-contradiction follow-up). Governance trail: `gov-5fb17ed70248`. |
| 2.8.2 | 2026-04-25 | PATCH: Pin tracks title-10-ai-coding-cfr.md MINOR bump v2.39.0 → v2.40.0 (new §5.1.7.1 Sequenced Two-Stage Review under §5.1.7 Subagent Review Triggers, normative — codifies Stage 1 mutation candidates → Stage 2 coherence/validation sequencing per plan `~/.claude/plans/federated-plotting-karp.md` Commit 3 of 8). Bumped `title-10-ai-coding-cfr.md v2.39.0+` → `v2.40.0+`. PATCH pin bump on MINOR target because the source MINOR is additive (extends §5.1.7 trigger model with sequencing discipline; no breaking change to existing reviewer roles). Governance trail: `gov-dd439ba39014`. |
| 2.8.1 | 2026-04-25 | PATCH: Pin tracks rules-of-procedure.md MINOR bump v3.27.4 → v3.28.0 (new §7.12 Effort-Not-Time Estimation + §7.13 BLUF-Pyramid Briefing, two new methods codifying behavioral floor additions per plan `~/.claude/plans/federated-plotting-karp.md` Commit 1). Bumped `rules-of-procedure.md v3.27.4+` → `v3.28.0+`. PATCH pin bump on MINOR target because the source MINOR is additive (no breaking change to existing methods); pin discipline allows PATCH per session-121 canonicalization (semver-consistent unless target is breaking). Governance trail: `gov-8e449341b2d3`. **[CORRECTION 2026-04-25 per BACKLOG #130 close]:** This entry's "PATCH-on-MINOR per session-121 canonicalization" rationale is **wrong**. Investigation (see BACKLOG #130 → COMPLETION-CHECKLIST item #7c) found "session-121 canonicalization" refers to the pin-sync MECHANICS (BACKLOG #115 → checklist item #7), NOT the semver direction. The audit-trailed semver-direction rule per round-2 contrarian HIGH-2 (commit `c22e35c`, codified in v2.8.0 entry below) is **MINOR-on-MINOR**. This entry should have been v2.9.0, not v2.8.1. Same correction applies to v2.8.2, v2.8.3, v2.8.4 (all four under-bumped relative to canonical rule; all four cited the same fabricated "session-121 canonicalization" authority). v2.8.5 (PATCH-on-PATCH for title-10 v2.42.1) is correct under the canonical rule. Going forward: follow MINOR-on-MINOR per checklist item #7c (the now-canonical home for the rule). Numbers v2.8.1-v2.8.4 are kept in place rather than retroactively renumbered (no destructive history rewrite); the discipline applies to future bumps. |
| 2.8.0 | 2026-04-23 | MINOR: Pin tracks title-10-ai-coding-cfr.md MINOR bump v2.38.5 → v2.39.0 (new §5.2.8 Redundancy & Consolidation, normative). Bumped `title-10-ai-coding-cfr.md v2.38.5+` → `v2.39.0+`. MINOR pin bump because the target is a MINOR bump (additive normative rule) — per round-2 contrarian HIGH-2 on the test-suite-optimization plan: semver consistency between pin and source, not PATCH-on-MINOR. New cross-referenced artifacts shipped with v2.39.0: `documents/failure-mode-registry.md` (SSOT for FM-* IDs cited by `Covers:` annotations), `documents/test-failure-mode-map.md` (auto-generated derived map), `scripts/generate-test-failure-map.py` (rot-immune generator), `workflows/TEST-AUTHORING-CHECKLIST.md` (author-time 9-step gate), `tests/test_validator.py::TestFailureModeCoverage` (lint with 4 tests: unknown-id-rejected, must-cover-has-annotation, retired-id-warning, yaml-parses). Governance trail: `gov-ab70d05c6ca7` (this commit). Pattern: MINOR-on-MINOR pin discipline canonicalized session-121 as pin-sync discipline (BACKLOG #115 → COMPLETION-CHECKLIST item #7). |
| 2.7.4 | 2026-04-23 | PATCH: Session-122 #116 shipping — pin sync per new CFR §9.3.10 checklist item #7 canonicalized v2.38.4. Bumped `title-10-ai-coding-cfr.md v2.38.4+` → `v2.38.5+` (title-10 shipped Layer 6 Pre-Plan-Approval Gate + 17 unit tests + `.claude/hooks/pre-exit-plan-mode-gate.sh` + scanner extension + Behavioral Floor pairing in tiers.json). Governance trail: `gov-94e385575297` (Phase A-F execution eval). Pattern: same pin-sync discipline that BACKLOG #115 canonicalized — applied here on its first application post-canonicalization. |
| 2.7.3 | 2026-04-21 | PATCH: Session-121 Task 5 post-commit double-check (coherence-auditor MISLEADING #1) — `<document_versions>` pin for `title-10-ai-coding-cfr.md` lagged three PATCH bumps (`v2.36.0+` pinned while shipped is `v2.38.4`). Bumped pin to `v2.38.4+` so adopters inherit the canonical fail-closed hook recipe shipped in §9.3.10. Governance trail: `gov-cb3074ca144b` (Task 5 execution eval). Pattern: same pin-lag class as v2.7.1/v2.7.2 — this is now a recurring post-commit drift category (adopter-facing surfaces outside the plan's explicit file list). New BACKLOG item filed to add body-header + pin sync to the CFR PATCH authoring template as the structural fix per `meta-core-systemic-thinking`. |
| 2.7.2 | 2026-04-20 | PATCH: Cross-cohort meta-review remediation (coherence-auditor `a593b82d189eb502d` flagged `<document_versions>` pin for rules-of-procedure lagged post-commit PATCH bump to v3.27.4). Bumped `rules-of-procedure.md v3.27.3+` → `v3.27.4+` and `constitution.md v5.0.6+` → `v5.0.7+` (meta-remediation added v5.0.7 Historical Amendment entry). Governance trail: `gov-9ab4e2bca855` (Cohort 5 post-commit carry-forward). Pattern: identical to v2.7.1 pin-lag remediation two commits prior — reinforces contrarian arc-level finding that adopter-facing version pins are a consistent post-commit drift class. |
| 2.7.1 | 2026-04-20 | PATCH: Cohort 5 post-commit double-check (sessions 5-1 + 5-2, commits `b0e14e4` + `bdafbc6`) found `<document_versions>` pins lagging shipped state. Bumped `constitution.md v5.0.3+` → `v5.0.6+` (Session 5-1 Article reorder v5.0.5 + Session 5-2 v5.0.6 additions) and `rules-of-procedure.md v3.27.2+` → `v3.27.3+` (Session 5-2 §1.1.3 enum + governance_level removal). Convergent HIGH/DANGEROUS finding per contrarian + coherence; same pattern as Cohort 4 Phase 4a post-commit PATCH where this same pin block lagged. Governance trail: `gov-9ab4e2bca855`. |
| 2.7 | 2026-04-19 | PATCH: Added this Changelog section (closes F-P1-06 gap flagged in 2026-04-18 self-review; ai-instructions.md was the only normative document lacking a version-history section per rules-of-procedure §2.1.1 Step 3). Bumped document-version pins in `<document_versions>` block to reflect constitution v5.0.3+ (post-Cohort-4 Phase 4a) and rules-of-procedure v3.27.2+ (new §2.1.1 Notes rules: version-history required + audit_id citation). Per Cohort 4 Phase 4a (session-117). Post-commit double-check patch: synced body-header Version/Updated fields with frontmatter — commit formalizing the "frontmatter must match" rule had violated it (dogfood failure). |
| 2.6 | 2026-04-12 | MINOR: Prior versions — pre-Changelog era; full history reconstructable via `git log documents/ai-instructions.md`. Snapshot recorded here as baseline when the Changelog section was introduced. |
