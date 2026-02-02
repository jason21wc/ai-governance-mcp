# AI Coding Methods
## Operational Procedures for AI-Assisted Software Development

**Version:** 2.5.0
**Status:** Active
**Effective Date:** 2026-01-18
**Governance Level:** Methods (Code of Federal Regulations equivalent)

---

## Preamble

### Document Purpose

This document defines operational procedures that implement the AI Coding Domain Principles. It translates binding principles into executable workflows that AI systems follow during software development tasks.

**Governance Hierarchy:**
```
┌─────────────────────────────────────────────────────────────┐
│  ai-interaction-principles.md (CONSTITUTION)                │
│  Meta-Principles: Universal behavioral rules. Immutable.    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ai-coding-domain-principles.md (FEDERAL STATUTES)          │
│  Domain Principles: AI coding-specific binding law.         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  THIS DOCUMENT: ai-coding-methods.md (CFR - REGULATIONS)    │
│  Operational procedures implementing the principles above.  │
│  HOW to comply. Updated more frequently than principles.    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Tool-Specific Guides (AGENCY PROCEDURES)                   │
│  Platform-specific execution. Separate documents.           │
└─────────────────────────────────────────────────────────────┘
```

**Regulatory Authority:** These methods derive authority from Domain Principles. A method cannot contradict a principle. If conflict exists, the principle governs.

**Relationship to Principles:** 
- **Domain Principles** define WHAT must be achieved (outcomes, thresholds)
- **These Methods** define HOW to achieve it (procedures, workflows)
- **Meta-Principles** (from Constitution) govern both and resolve conflicts

### Importance Tags Legend

This document uses importance tags to enable efficient partial loading and future pruning:

| Tag | Meaning | Loading Guidance |
|-----|---------|------------------|
| 🔴 **CRITICAL** | Essential for document effectiveness | Always load |
| 🟡 **IMPORTANT** | Significant value, not essential | Load when relevant |
| 🟢 **OPTIONAL** | Nice to have, first to cut | Load on demand only |

### Legal System Analogy

This document functions as the Code of Federal Regulations (CFR) in the US Legal System:

| Legal Concept | Framework Equivalent | Purpose |
|---------------|---------------------|---------|
| Constitution | ai-interaction-principles.md | Foundational, universal, immutable |
| Federal Statutes | ai-coding-domain-principles.md | Domain-specific binding law |
| **CFR (Regulations)** | **This document** | **Operational rules implementing statutes** |
| Agency SOPs | Tool-specific guides | Platform-specific execution |

---

### 🔴 CRITICAL: How AI Should Use This Document

**Importance: CRITICAL — This section is essential for document effectiveness**

#### Partial Loading Strategy

This document is designed for partial loading. AI should NOT load the entire document every session. Instead:

1. **Always load:** Preamble + Situation Index + Current Phase section
2. **Load on demand:** Specific procedures when needed
3. **Reference only:** Appendices and templates

#### On Session Start

1. Check for **Session State File** (see Title 7)
2. If exists: Load state, identify current phase, load that phase's section
3. If new project: Execute **Project Calibration Protocol** (§1.3)
4. Load appropriate phase procedures based on current work

#### Situation Index — What To Do When...

**Use this index to jump directly to relevant procedures:**

| Situation | Go To | Key Procedure |
|-----------|-------|---------------|
| Starting new project | Cold Start Kit | Scenario A: New Project Prompt |
| Resuming work | Cold Start Kit | Scenario B: Resume Work Prompt |
| Need to calibrate mode | §1.3 | Project Calibration Protocol |
| Writing requirements | §2.2 | Specification Writing |
| Completing Specify phase | Phase Gates | Update PROJECT-MEMORY gate table |
| Choosing technologies | §3.1 | Architecture Definition |
| Completing Plan phase | Phase Gates | Update PROJECT-MEMORY gate table |
| Breaking down work | §4.1 | Decomposition Requirements |
| Completing Tasks phase | Phase Gates | Update PROJECT-MEMORY gate table |
| Writing code | §5.1 | Implementation Loop |
| Completing Implementation | Phase Gates | Update PROJECT-MEMORY gate table |
| Something seems wrong | §6.1 | Technical Validation Gates |
| Setting up CI/CD pipeline | §6.4 | Automated Validation |
| Need human decision | §8.1 | Escalation Triggers |
| Session ending | §7.4 | Session End Procedure |
| Context seems lost | Cold Start Kit | Scenario C: Recovery Prompt |
| Uncertain about approach | §8.2 | Decision Presentation |
| "framework check" received | Cold Start Kit | Scenario C: Recovery Prompt |
| Deploying to Docker | §9.2 | Docker Distribution |
| Building MCP server | §9.3 | MCP Server Development |
| Config validation needed | §9.1 | Pre-Flight Validation |

#### On Uncertainty

- If procedure unclear: Escalate per Human-AI Collaboration (Domain)
- If principle conflict suspected: Principle governs, flag for review
- If novel situation: Apply principle intent, document adaptation

### 🔴 CRITICAL: Quick Reference

**Importance: CRITICAL — Primary navigation aid**

#### The 4-Phase Workflow

```
SPECIFY ──→ PLAN ──→ TASKS ──→ IMPLEMENT
   │          │         │          │
   └──────────┴─────────┴──────────┘
      Validation Gates (Domain: Validation Gates)
      Memory Management (Domain: Session State Continuity)
      Human Collaboration (Domain: Human-AI Collaboration)
```

#### Procedural Modes (Adaptive Rigor)

| Mode | When to Use | Depth |
|------|-------------|-------|
| **EXPEDITED** | High certainty, low stakes, replication | Minimal |
| **STANDARD** | Medium certainty, moderate stakes | Full |
| **ENHANCED** | Low certainty OR high stakes, innovation | Maximum + iteration |

#### Principle → Title Mapping

| Domain Principle | Primary Title | 
|------------------|---------------|
| Specification Completeness | Title 2 (Specify) |
| Context Window Management | Title 3 (Plan), Title 7 (Memory) |
| Session State Continuity | Title 7 (Memory) |
| Sequential Phase Dependencies | Titles 2-5 (All Phases) |
| Validation Gates | Title 6 (Validation) |
| Atomic Task Decomposition | Title 4 (Tasks) |
| Human-AI Collaboration | Title 8 (Collaboration) |
| Production-Ready Standards | Title 5 (Implement) |
| Security-First Development | Title 5 (Implement) |
| Testing Integration | Title 5 (Implement) |
| Supply Chain Integrity | Title 5 (Implement) |
| Workflow Integrity | Title 8 (Collaboration) |

#### Memory Architecture Overview (see Title 7)

Memory files map to cognitive memory types from AI agent research:

| Cognitive Type | File | Purpose | Lifecycle |
|----------------|------|---------|-----------|
| **Working Memory** | `SESSION-STATE.md` | What's active now | Overwritten each session |
| **Semantic Memory** | `PROJECT-MEMORY.md` | Facts, decisions, gates | Accumulates, summarize periodically |
| **Episodic Memory** | `LEARNING-LOG.md` | Events, lessons learned | Prune when internalized |
| **Procedural Memory** | Methods documents | How to do things | Evolves with practice |

**Key Principle:** Memory serves reasoning, not archival. Retain what informs future decisions.

---

### 🔴 CRITICAL: Cold Start Kit

**Importance: CRITICAL — Enables "working in 2-3 exchanges" goal**

This section provides copy-paste templates for immediate framework activation. A fresh AI instance should be productive within 2-3 message exchanges using these artifacts.

> ⚠️ **IMPORTANT:** Paste prompts verbatim. Do not paraphrase or summarize—exact wording ensures consistent AI interpretation.

#### Scenario A: New Project — First Prompt

Copy and send this to start a new project:

```
I'm starting a new project. Please help me set it up using the AI Coding Methods framework.

PROJECT: [Name]
DESCRIPTION: [1-2 sentences about what we're building]

Before we begin, let's calibrate:
- Novelty: [YES exact pattern exists / PARTIALLY similar / NO genuinely novel]
- Requirements Certainty: [HIGH / MEDIUM / LOW]
- Stakes: [LOW prototype / MEDIUM production / HIGH critical system]
- Longevity: [SHORT throwaway / MEDIUM 1-2 years / LONG multi-year]

Please:
1. Confirm the procedural mode (Expedited/Standard/Enhanced)
2. Create the initial SESSION-STATE.md
3. Begin the Specify phase with discovery questions
```

#### Scenario B: Resume Work — First Prompt

Copy and send this to resume existing work:

```
Resuming work on [PROJECT NAME].

Current SESSION-STATE.md:
---
[Paste contents of SESSION-STATE.md here]
---

Please:
1. Confirm you understand the current state
2. Identify the next action from the state file
3. Proceed with that action (or ask clarifying questions if needed)
```

#### Scenario C: Framework Check — Recovery Prompt

Copy and send this if context seems lost:

```
Framework check requested.

Please:
1. State what you understand about the current project
2. Identify what phase we should be in
3. List any gaps in your understanding
4. Propose next steps to re-establish working state
```

#### Minimal SESSION-STATE.md Template (Copy-Paste Ready)

Create this file in project root immediately.

> ⚠️ **NOTE:** The "Phase" field below defaults to "Specify" for new projects. When resuming or recovering, you MUST update this field to reflect actual current phase before use.

```markdown
# Session State

**Last Updated:** [YYYY-MM-DD HH:MM]
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position
- **Phase:** Specify
- **Mode:** [Expedited/Standard/Enhanced]
- **Active Task:** Initial discovery
- **Blocker:** None

## Immediate Context
Starting new project. Need to complete discovery and write specification.

## Next Actions
1. Answer calibration questions to confirm mode
2. Complete discovery procedure for selected mode
3. Write specification document

## Session Notes
[Any relevant context]
```

#### Minimal PROJECT-MEMORY.md Template (Copy-Paste Ready)

Create this file after Specify phase completes:

```markdown
# Project Memory

**Project:** [Name]
**Started:** [Date]
**Mode:** [Expedited/Standard/Enhanced]
**Memory Type:** Semantic (accumulates)
**Lifecycle:** Prune when decisions superseded per §7.0.4

> Preserves significant decisions and rationale.
> Mark superseded decisions with date and replacement link.

---

## Specification Summary
- **Problem:** [One sentence]
- **Users:** [Target audience]
- **Core Features:** [Bulleted list, ≤7 items]
- **Out of Scope:** [What we're NOT building]

## Phase Gates

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Specify → Plan | ⏳ Pending | — | — |
| Plan → Tasks | ⏳ Pending | — | — |
| Tasks → Implement | ⏳ Pending | — | — |
| Implement → Complete | ⏳ Pending | — | — |

> Status: ⏳ Pending | ✓ Passed | ❌ Failed. Add "Approver" column for team projects.

## Architecture Decisions
[Add decisions as they're made using ADR format]

## Technical Stack
- **Frontend:** [TBD or technologies]
- **Backend:** [TBD or technologies]
- **Database:** [TBD or technologies]
- **Infrastructure:** [TBD or technologies]

## Constraints & Standards
- [Add constraints as identified]

## Key Artifacts
| Artifact | Location | Status |
|----------|----------|--------|
| Specification | [TBD] | In Progress |
| Architecture | [TBD] | Not Started |
```

#### Minimal LEARNING-LOG.md Template (Copy-Paste Ready)

Create this file when the first lesson emerges (not at project start):

```markdown
# Learning Log

**Project:** [Name]
**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> When lesson becomes pattern: Add to methods doc, mark "Graduated to §X.Y"

---

## Lessons

### [Date] - [Brief Title]
**Context:** [What we were doing]
**What Happened:** [The unexpected outcome]
**Lesson:** [What we learned]
**Action:** [How we'll apply this]

---

## Patterns That Worked
| Pattern | Context | Why It Worked |
|---------|---------|---------------|
| [Pattern] | [When used] | [Why effective] |

## Patterns That Failed
| Pattern | Context | Why It Failed |
|---------|---------|---------------|
| [Pattern] | [When tried] | [Why ineffective] |
```

#### Mode Selection Decision Tree (Visual)

See §1.3.3 for complete decision logic. Quick reference:

```
                    Is this genuinely novel?
                    (No existing pattern to follow)
                              │
               ┌──────────────┴──────────────┐
               │ YES                         │ NO
               ▼                             ▼
         ═══════════              Are requirements clear?
         ║ ENHANCED ║                        │
         ═══════════               ┌─────────┴─────────┐
                                   │ NO                │ YES
                                   ▼                   ▼
                             ═══════════         What are the stakes?
                             ║ ENHANCED ║              │
                             ═══════════        ┌──────┴──────┐
                                                │ HIGH        │ LOW/MEDIUM
                                                ▼             ▼
                                          ═══════════   Known pattern
                                          ║ ENHANCED ║   + LOW stakes?
                                          ═══════════        │
                                                       ┌─────┴─────┐
                                                       │ YES       │ NO
                                                       ▼           ▼
                                                  ═══════════  ═══════════
                                                  ║EXPEDITED║  ║ STANDARD ║
                                                  ═══════════  ═══════════
```

**Quick Mode Selection:**
- **ENHANCED:** Novel OR Uncertain OR High-stakes (any one triggers Enhanced)
- **EXPEDITED:** Known pattern + Clear requirements + Low stakes (all three required)
- **STANDARD:** Everything else (the default for typical production work)

---

### 🔴 CRITICAL: Phase Gates

**Importance: CRITICAL — Gates are checkpoints recorded in semantic memory**

Each phase transition requires validation and approval. Gate status is recorded inline in `PROJECT-MEMORY.md` under the Phase Gates section — not as separate files.

**Rationale for inline gates (v2.0.0):**
1. Gates are facts about project state (semantic memory), not decisions (which use ADRs)
2. Separate files create coordination overhead and sync issues
3. Gate criteria live in procedural memory (this document) — no need to duplicate
4. Aligns with industry quality gate patterns (Sonar, CI/CD integration)

**On Gate Failure:** If any checklist item cannot be satisfied, the gate fails. Return to the current phase, address the deficiency, then attempt the gate again. Document failures in the Learning Log.

#### Gate Recording Format

Update the Phase Gates table in `PROJECT-MEMORY.md`:

```markdown
## Phase Gates

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Specify → Plan | ✓ Passed | 2025-01-15 | Spec complete, 7 features |
| Plan → Tasks | ✓ Passed | 2025-01-17 | Architecture approved |
| Tasks → Implement | ⏳ Pending | — | Awaiting task review |
| Implement → Complete | ⏳ Pending | — | — |
```

**Status values:** ✓ Passed | ⏳ Pending | ❌ Failed (with remediation notes)
**Team projects:** Add "Approver" column for accountability.

#### Gate Checklists (Reference)

Use these checklists to validate gates. Do not create separate files — verify items, then update the Phase Gates table.

**Specify → Plan Gate:**
- [ ] Problem statement clear
- [ ] Target users identified
- [ ] Core features listed (≤7)
- [ ] Acceptance criteria defined
- [ ] Out of scope documented
- [ ] Product Owner approved

**Plan → Tasks Gate:**
- [ ] Technology stack selected
- [ ] System structure defined
- [ ] Security architecture addressed
- [ ] Risks identified and mitigated
- [ ] Product Owner approved

**Tasks → Implement Gate:**
- [ ] All tasks ≤15 files affected
- [ ] All tasks independently testable
- [ ] Dependencies explicit (no cycles)
- [ ] Full specification coverage verified
- [ ] Product Owner approved

**Implement → Complete Gate:**
- [ ] All tasks completed
- [ ] All tests passing
- [ ] Test coverage ≥80%
- [ ] Security scan: Zero HIGH/CRITICAL
- [ ] All dependencies verified
- [ ] Acceptance criteria met
- [ ] Product Owner approved

#### Measurement Guidance (Tool-Neutral)

Gate metrics must be measured. Here's how to obtain them without assuming specific tools:

| Metric | How to Measure | Delegation |
|--------|----------------|------------|
| **Test Coverage** | Run coverage tool for your stack (Jest, pytest-cov, go test -cover, etc.). Report line or branch coverage. | See tool appendices for specific commands |
| **Tests Passing** | Run test suite. Count passed/total. All must pass (100%). | Stack-specific test runner |
| **Security Scan** | Run SAST tool (Semgrep, Bandit, npm audit, etc.). Count HIGH/CRITICAL findings. Must be zero. | See §5.3 for security procedures |
| **Dependencies Verified** | For each dependency: confirm exists in registry, check for known vulnerabilities, verify license. | See §5.4 for verification procedure |
| **Acceptance Criteria** | Review each criterion from specification. Mark pass/fail. All must pass. | Manual review against spec |

If your stack lacks tooling for a metric, document the gap and use manual review with explicit rationale.

#### Solo Developer Mode

For Solo Developer Mode, gates can be combined at natural breakpoints. Update the Phase Gates table with combined entries:

```markdown
| Gate | Status | Date | Approver | Notes |
|------|--------|------|----------|-------|
| Specify + Plan | ✓ Passed | 2025-01-15 | @user | Spec and architecture approved |
| Tasks + Implement | ⏳ Pending | — | — | — |
```

---

# TITLE 1: GENERAL PROVISIONS

**Importance: 🔴 CRITICAL — Foundation for all procedures**

## Part 1.1: Scope and Applicability

### 1.1.1 Scope

These methods apply to all AI-assisted software development activities within the AI Coding Domain jurisdiction, including:

- New application development (greenfield)
- Feature additions to existing applications
- Bug fixes and maintenance
- Refactoring and modernization
- Technical documentation

### 1.1.2 Applicability

**Applies when:**
- AI is the primary code generator
- Human serves as Product Owner / decision-maker
- Output is intended for production use (or production-quality standards)

**Does not apply to:**
- Exploratory conversations about concepts
- Code review without modification
- Pure documentation tasks (use general writing principles)

### 1.1.3 Relationship to Other Domains

When tasks span multiple domains:
1. AI Coding Methods govern code-related activities
2. Other domain principles govern their respective activities
3. Meta-principles govern cross-domain conflicts
4. Escalate to Product Owner if jurisdiction unclear

---

## Part 1.2: Definitions

### 1.2.1 Workflow Terms

**Phase:** A major stage of the development workflow. Four phases exist: Specify, Plan, Tasks, Implement.

**Procedure:** A defined sequence of actions within a phase that produces a specific output.

**Validation Gate:** A checkpoint between phases where outputs are verified before proceeding.

**Procedural Mode:** The level of rigor applied to procedures (Expedited, Standard, Enhanced).

### 1.2.2 Role Terms

**Product Owner (PO):** Human responsible for vision, requirements, prioritization, and validation. Makes all strategic decisions. Reviews significant AI recommendations.

**AI Implementer:** The AI system executing procedures. Proposes solutions, executes approved plans, escalates when triggers activate.

**Solo Developer Mode:** Configuration where one human serves as both Product Owner and technical decision-maker. Reduces ceremony while maintaining validation gates.

### 1.2.3 Artifact Terms

**Specification:** Document defining WHAT to build—requirements, user stories, acceptance criteria, constraints.

**Architecture:** Document defining HOW to build—technology choices, system structure, integration patterns.

**Task:** Atomic unit of implementation work. Must be independently testable, ≤15 files affected.

**State File:** Persistent record of project progress, decisions, and context for session continuity.

### 1.2.4 Quality Terms

**Production-Ready:** Code that meets all Q-series principle thresholds: zero HIGH/CRITICAL vulnerabilities, ≥80% test coverage, verified dependencies, documented patterns.

**Technical Debt:** Intentional shortcuts documented for future resolution. Must be explicit, tracked, and approved by Product Owner.

**Validation:** Verification that outputs meet defined criteria. Technical validation (automated) + Vision validation (human).

---

## Part 1.3: Project Calibration Protocol

**Importance: 🔴 CRITICAL — The "adaptive rigor" mechanism**

### 1.3.1 Purpose

Before applying phase procedures, calibrate the procedural mode to match project characteristics. This implements the meta-principle "Discovery Depth Calibration: Match discovery investment to commitment magnitude."

### 1.3.2 Calibration Questions

Execute this protocol at project start and when scope significantly changes:

**Question 1: Novelty Assessment**
> Has this type of application been built before?

| Answer | Indicator |
|--------|-----------|
| YES, exact pattern exists | Accounting app, blog, e-commerce store |
| PARTIALLY, similar but adapted | Accounting app with AI categorization |
| NO, genuinely novel | First-of-kind solution to unique problem |

**Question 2: Requirements Certainty**
> How well-understood are the requirements?

| Answer | Indicator |
|--------|-----------|
| HIGH certainty | Written specs, proven user needs, clear acceptance criteria |
| MEDIUM certainty | General direction known, details to be discovered |
| LOW certainty | Exploring problem space, requirements will emerge |

**Question 3: Stakes Assessment**
> What's the cost of being wrong?

| Answer | Indicator |
|--------|-----------|
| LOW stakes | Prototype, internal tool, learning project |
| MEDIUM stakes | Production app, real users, moderate business impact |
| HIGH stakes | Critical system, safety implications, significant investment |

**Question 4: Longevity Expectation**
> What's the expected lifespan?

| Answer | Indicator |
|--------|-----------|
| SHORT-TERM | Prototype, proof-of-concept, throwaway |
| MEDIUM-TERM | MVP with iteration expected, 1-2 year horizon |
| LONG-TERM | Production system, multi-year maintenance |

### 1.3.3 Mode Selection Matrix

**Canonical Decision Rule** (one source of truth):

```
IF genuinely novel (pattern never built before):
    MODE = ENHANCED
    
ELSE IF requirements uncertain (LOW certainty):
    MODE = ENHANCED
    
ELSE IF stakes are HIGH:
    MODE = ENHANCED
    
ELSE IF known pattern AND clear requirements AND low stakes:
    MODE = EXPEDITED
    
ELSE:
    MODE = STANDARD
```

**Visual Decision Tree** (same logic, graphical form):

```
                    Is this genuinely novel?
                    (No existing pattern to follow)
                              │
               ┌──────────────┴──────────────┐
               │ YES                         │ NO
               ▼                             ▼
         ═══════════              Are requirements clear?
         ║ ENHANCED ║                        │
         ═══════════               ┌─────────┴─────────┐
                                   │ NO                │ YES
                                   ▼                   ▼
                             ═══════════         What are the stakes?
                             ║ ENHANCED ║              │
                             ═══════════        ┌──────┴──────┐
                                                │ HIGH        │ LOW/MEDIUM
                                                ▼             ▼
                                          ═══════════   Known pattern
                                          ║ ENHANCED ║   + LOW stakes?
                                          ═══════════        │
                                                       ┌─────┴─────┐
                                                       │ YES       │ NO
                                                       ▼           ▼
                                                  ═══════════  ═══════════
                                                  ║EXPEDITED║  ║ STANDARD ║
                                                  ═══════════  ═══════════
```

**Quick Reference:**
- **ENHANCED:** Novel OR Uncertain OR High-stakes (any one triggers Enhanced)
- **EXPEDITED:** Known pattern + Clear requirements + Low stakes (all three required)
- **STANDARD:** Everything else (the default for typical production work)

### 1.3.4 Mode Override

Product Owner may override the calculated mode:

- **Upgrade to ENHANCED:** When risk tolerance is low despite other factors
- **Downgrade to EXPEDITED:** When time pressure justifies accepting more risk (must be explicit)

Document mode selection and any override in the State File (Title 7).

---

## Part 1.4: Procedural Mode Definitions

### 1.4.1 EXPEDITED Mode

**When to use:** High certainty, low stakes, replicating known patterns.

**Characteristics:**
- Reference-based specification (point to existing patterns)
- Proven architecture templates
- Standard decomposition
- Basic validation gates
- Minimal documentation overhead

**Risk acceptance:** Higher tolerance for discovering issues during implementation. Iteration expected.

**Time investment:** Proportionally minimal discovery and planning.

### 1.4.2 STANDARD Mode

**When to use:** Medium certainty, moderate stakes, typical production work.

**Characteristics:**
- Full specification development
- Architecture decision records
- Dependency-aware decomposition
- Complete validation gates
- Standard documentation

**Risk acceptance:** Balanced approach. Major issues should be caught in planning.

**Time investment:** Proportional to project size and complexity.

### 1.4.3 ENHANCED Mode

**When to use:** Low certainty OR high stakes. Novel problems, uncertain requirements, critical systems.

**Characteristics:**
- Discovery sprints before specification
- Proof-of-concept before architecture commitment
- Milestone-based tasks with learning checkpoints
- Iteration protocols between phases
- Comprehensive documentation
- External validation where appropriate

**Risk acceptance:** Low tolerance. Invest heavily in understanding before committing.

**Time investment:** Front-loaded in discovery and validation. May include deliberate prototyping.

### 1.4.4 Mode Transitions

Projects may transition between modes:

- **EXPEDITED → STANDARD:** When unexpected complexity discovered
- **STANDARD → ENHANCED:** When novel challenges emerge
- **ENHANCED → STANDARD:** When uncertainty resolves through discovery

Document transitions in State File with rationale.

---

# TITLE 2: SPECIFY PROCEDURES

**Importance: 🔴 CRITICAL — Foundation for all downstream work**

**Implements:** Specification Completeness (Domain)  
**Validates:** Discovery Before Commitment (Meta)  
**Gate:** Specification Completeness Checklist (§2.3)

## Part 2.1: Discovery Requirements

### 2.1.1 Purpose

Discovery establishes shared understanding before specification writing. This prevents the "Confident Ignorance" trap (assuming understanding is complete because no questions come to mind).

### 2.1.2 Discovery by Mode

**EXPEDITED Mode:**
- [ ] Identify reference pattern or prior art
- [ ] Confirm applicability to current context
- [ ] Note any adaptations required
- [ ] Estimate: 10-30 minutes

**STANDARD Mode:**
- [ ] Problem statement clarification
- [ ] User persona identification
- [ ] Success criteria definition
- [ ] Constraint identification
- [ ] Prior art research
- [ ] Estimate: 1-4 hours depending on scope

**ENHANCED Mode:**
- [ ] All STANDARD activities, plus:
- [ ] User interviews or feedback synthesis
- [ ] Competitive analysis
- [ ] Technical feasibility exploration
- [ ] Prototype or proof-of-concept
- [ ] Unknown-unknown hunting (explicitly seek gaps)
- [ ] Estimate: 1-5 days depending on novelty

### 2.1.3 Discovery Outputs

At minimum, discovery produces:

1. **Problem Statement:** What problem are we solving? For whom?
2. **Success Criteria:** How will we know we've succeeded?
3. **Constraints:** What limitations exist (technical, business, regulatory)?
4. **Known Unknowns:** What questions do we know we need to answer?
5. **Risk Indicators:** What could go wrong? What's the impact?

### 2.1.4 Discovery Escalation

Escalate to Product Owner when:
- Discovery reveals initial assumptions were significantly wrong
- Constraints make the original goal infeasible
- Risk indicators exceed acceptable thresholds
- Time allocated for discovery proves insufficient

---

## Part 2.2: Specification Writing

### 2.2.1 Purpose

Specifications translate discovery findings into precise requirements that AI can implement. Specifications are contracts—ambiguity creates implementation divergence.

### 2.2.2 Specification Components

**Required for ALL modes:**

| Component | Description | Validation |
|-----------|-------------|------------|
| Elevator Pitch | Single-sentence description of the application | Clear, testable, memorable |
| Target Users | Who will use this and why | Specific enough to validate |
| Core Features | MVP feature list | Prioritized, limited (3-7 items) |
| Acceptance Criteria | How we verify each feature works | Measurable, testable |
| Out of Scope | What we're explicitly NOT building | Prevents scope creep |

**Additional for STANDARD mode:**

| Component | Description | Validation |
|-----------|-------------|------------|
| User Stories | Behavior-focused requirements | "As a [user], I want [goal], so that [benefit]" |
| Non-Functional Requirements | Performance, security, accessibility | Quantified thresholds |
| Constraints | Technical, business, regulatory limits | Documented with rationale |
| Dependencies | External systems, APIs, data sources | Integration requirements |

**Additional for ENHANCED mode:**

| Component | Description | Validation |
|-----------|-------------|------------|
| User Journey Maps | End-to-end experience flows | Visual or narrative |
| Edge Cases | Boundary conditions and error states | Explicit handling defined |
| Validation Hypotheses | What we're testing with this build | Measurable learning outcomes |
| Iteration Triggers | Conditions that prompt re-specification | Defined checkpoints |

### 2.2.3 Specification Quality Criteria

Before proceeding to Plan phase, specifications must meet:

- **Complete:** All required components present
- **Consistent:** No internal contradictions
- **Testable:** Each requirement has verification method
- **Prioritized:** Clear MVP vs future distinction
- **Bounded:** Explicit scope limits defined

### 2.2.4 MVP Discipline

> "Every feature you add in planning multiplies complexity during implementation."

Apply aggressive scope limitation:

1. List all desired features
2. Identify the minimum set that delivers core value
3. Defer everything else to "Future Iteration"
4. Validate: "Could this be built in a weekend with proper planning?"

If NO to the validation question, scope is likely too large. Iterate.

---

## Part 2.3: Completeness Validation

### 2.3.1 Purpose

Verify specification meets C1 requirements before proceeding to Plan phase. This is a Validation Gate (P2).

### 2.3.2 Completeness Checklist

**EXPEDITED Mode Checklist:**
- [ ] Problem statement clear
- [ ] Reference pattern identified
- [ ] Adaptations documented
- [ ] Success criteria defined
- [ ] Product Owner approval received

**STANDARD Mode Checklist:**
All EXPEDITED items, plus:
- [ ] All specification components present
- [ ] User stories cover core features
- [ ] Acceptance criteria testable
- [ ] Non-functional requirements quantified
- [ ] Dependencies identified
- [ ] Out of scope documented
- [ ] No internal contradictions
- [ ] Product Owner approval received

**ENHANCED Mode Checklist:**
All STANDARD items, plus:
- [ ] User journey maps complete
- [ ] Edge cases documented
- [ ] Learning hypotheses stated
- [ ] Iteration triggers defined
- [ ] External validation complete (if applicable)
- [ ] Product Owner approval received

### 2.3.3 Checklist Failures

If checklist fails:
1. Identify missing or deficient items
2. Return to appropriate procedure (Discovery or Specification Writing)
3. Iterate until checklist passes
4. Document iterations in State File

Do NOT proceed to Plan phase with incomplete specification.

---

## Part 2.4: UX Elaboration [ENHANCED Mode]

**Importance: 🟢 OPTIONAL — Only for UX-critical projects**

### 2.4.1 When to Apply

Apply UX Elaboration procedures when:
- User experience is critical to success
- Novel interaction patterns required
- Multiple user personas with different needs
- Accessibility requirements significant

### 2.4.2 UX Elaboration Procedures

1. **User Flow Mapping**
   - Document primary user journeys
   - Identify decision points and branching
   - Map emotional states through journey
   - Identify friction points

2. **Interaction Design**
   - Define key interaction patterns
   - Specify feedback mechanisms
   - Document error handling UX
   - Define accessibility requirements

3. **Prototype Development**
   - Create low-fidelity wireframes or mockups
   - Validate with stakeholders
   - Iterate based on feedback
   - Document approved designs

### 2.4.3 UX Validation Gate

Before proceeding:
- [ ] User flows documented and approved
- [ ] Key interactions specified
- [ ] Accessibility requirements defined
- [ ] Prototype validated with stakeholders

---

## Part 2.5: Visual Design Specs [ENHANCED Mode]

**Importance: 🟢 OPTIONAL — Only for brand-critical projects**

### 2.5.1 When to Apply

Apply Visual Design procedures when:
- Brand consistency critical
- User-facing application
- Design system required
- Visual differentiation is competitive advantage

### 2.5.2 Visual Design Procedures

1. **Design System Definition**
   - Color palette specification
   - Typography scale
   - Spacing system
   - Component library outline

2. **Visual Mockups**
   - Key screen designs
   - Responsive breakpoints
   - Animation/transition specifications
   - Asset requirements

3. **Design Validation**
   - Stakeholder review
   - Accessibility audit
   - Cross-device verification
   - Final approval

### 2.5.3 Visual Design Validation Gate

Before proceeding:
- [ ] Design system documented
- [ ] Key screens designed
- [ ] Responsive behavior specified
- [ ] Accessibility verified
- [ ] Stakeholder approval received

---

# TITLE 3: PLAN PROCEDURES

**Importance: 🟡 IMPORTANT — Defines HOW we build**

**Implements:** Sequential Phase Dependencies (Domain), Context Window Management (Domain)  
**Input:** Validated Specification (Title 2)  
**Gate:** Architecture Validation (§3.2.4)

## Part 3.1: Architecture Definition

### 3.1.1 Purpose

Define the technical architecture that will implement the specification. Architecture decisions constrain all downstream work—this is the foundation.

### 3.1.2 Architecture by Mode

**EXPEDITED Mode:**
- [ ] Select proven architecture pattern
- [ ] Confirm pattern fits requirements
- [ ] Document any adaptations
- [ ] Identify technology stack
- [ ] Estimate: 30-60 minutes

**STANDARD Mode:**
- [ ] Evaluate architecture alternatives
- [ ] Create Architecture Decision Records (ADRs)
- [ ] Define system boundaries
- [ ] Specify integration patterns
- [ ] Plan data model
- [ ] Address security architecture
- [ ] Estimate: 2-8 hours

**ENHANCED Mode:**
- [ ] All STANDARD activities, plus:
- [ ] Technical spike or proof-of-concept
- [ ] Performance modeling
- [ ] Scalability analysis
- [ ] Failure mode analysis
- [ ] External architecture review (if applicable)
- [ ] Estimate: 1-5 days

### 3.1.3 Architecture Components

**Required for ALL modes:**

| Component | Description |
|-----------|-------------|
| Technology Stack | Languages, frameworks, libraries, services |
| System Structure | High-level component organization |
| Data Model | Core entities and relationships |
| Integration Points | External systems, APIs, services |

**Additional for STANDARD mode:**

| Component | Description |
|-----------|-------------|
| Architecture Decision Records | Rationale for key decisions |
| Security Model | Authentication, authorization, data protection |
| Deployment Architecture | Environments, infrastructure, CI/CD |
| Observability Plan | Logging, monitoring, alerting |

**Additional for ENHANCED mode:**

| Component | Description |
|-----------|-------------|
| Scalability Model | Growth path, capacity planning |
| Failure Analysis | Failure modes and recovery strategies |
| Performance Model | Latency, throughput, resource requirements |
| Migration Path | If applicable, transition from existing systems |

### 3.1.4 Technology Selection Criteria

Technologies should be:
- [ ] **Proven:** Mature ecosystem, good documentation
- [ ] **Team-appropriate:** Matches expertise or quickly learnable
- [ ] **Feature-enabling:** Directly supports specification requirements
- [ ] **Scalable:** Growth path clear without rewrites
- [ ] **Cost-effective:** Reasonable for expected usage

**Red flags to avoid:**
- [ ] Technology tourism (choosing for learning vs. fitness)
- [ ] Over-engineering (complex solutions for simple problems)
- [ ] Vendor lock-in (dependencies preventing future flexibility)
- [ ] Premature optimization (solving scale problems not yet present)

---

## Part 3.2: Technical Planning

### 3.2.1 Purpose

Translate architecture into implementation-ready technical plan. This bridges architecture decisions to task decomposition.

### 3.2.2 Technical Plan Components

**Required for ALL modes:**

| Component | Description |
|-----------|-------------|
| Feature → Technology Mapping | How each feature will be implemented |
| Development Sequence | Order of implementation (respecting dependencies) |
| Risk Register | Technical risks and mitigations |
| Definition of Done | What "complete" means for this project |

**Additional for STANDARD/ENHANCED modes:**

| Component | Description |
|-----------|-------------|
| API Contracts | Interface definitions between components |
| Database Schema | Detailed data model |
| Security Checklist | Security requirements per component |
| Testing Strategy | Unit, integration, E2E approach |
| Performance Targets | Specific metrics per component |

### 3.2.3 Development Sequence Planning

Sequence implementation to:
1. Build foundation before features that depend on it
2. Enable parallel work where dependencies allow
3. Deliver value incrementally (vertical slices)
4. Address highest-risk items early (fail fast)

Document sequence with explicit dependencies.

### 3.2.4 Architecture Validation Gate

Before proceeding to Tasks phase:

**EXPEDITED Mode:**
- [ ] Technology stack confirmed
- [ ] Pattern applicability verified
- [ ] Risk register reviewed
- [ ] Product Owner approval received

**STANDARD Mode:**
All EXPEDITED items, plus:
- [ ] ADRs documented for major decisions
- [ ] Security architecture reviewed
- [ ] Integration points specified
- [ ] Development sequence defined
- [ ] Product Owner approval received

**ENHANCED Mode:**
All STANDARD items, plus:
- [ ] Proof-of-concept validates key assumptions
- [ ] Performance model reviewed
- [ ] Failure analysis complete
- [ ] External review incorporated (if applicable)
- [ ] Product Owner approval received

---

## Part 3.3: Context Strategy

### 3.3.1 Purpose

Plan context window utilization to maintain AI effectiveness throughout implementation. Implements C2 (Context Window Management).

### 3.3.2 Context Inventory

Before implementation, identify:

1. **Essential Context** (always loaded):
   - Specification summary
   - Architecture overview
   - Current task details
   - Relevant code files

2. **Reference Context** (loaded on demand):
   - Full specification
   - Detailed architecture docs
   - Related but not current code
   - External documentation

3. **Historical Context** (summarized):
   - Previous session summaries
   - Decision history
   - Completed task summaries

### 3.3.3 Context Loading Plan

For each major implementation phase:
- What essential context is required?
- What reference context may be needed?
- What can be summarized vs. loaded in full?
- Estimated token budget per phase

### 3.3.4 Context Monitoring

During implementation:
- Track estimated context usage
- Prune completed work from active context
- Summarize and offload historical context
- Alert when approaching 32K token effective limit

---

## Part 3.4: Proof-of-Concept Protocol [ENHANCED Mode]

**Importance: 🟢 OPTIONAL — Only when technical approach unproven**

### 3.4.1 When to Apply

Execute proof-of-concept when:
- Core technical approach is unproven
- Integration with unfamiliar systems required
- Performance requirements are demanding
- Novel algorithms or techniques needed

### 3.4.2 PoC Scope

A proof-of-concept should:
- Test specific technical hypotheses
- Be minimal (just enough to prove/disprove)
- Be time-boxed (hours to days, not weeks)
- Produce clear success/failure signal

### 3.4.3 PoC Procedure

1. **Hypothesis Statement:** What are we testing?
2. **Success Criteria:** How do we know if it works?
3. **Implementation:** Build minimal test
4. **Evaluation:** Did it meet criteria?
5. **Decision:** Proceed, adapt, or abandon approach

### 3.4.4 PoC Outcomes

Based on PoC results:
- **PROCEED:** Hypothesis validated, continue with architecture
- **ADAPT:** Partially validated, modify approach
- **ABANDON:** Hypothesis failed, reconsider architecture

Document outcomes in State File.

---

# TITLE 4: TASKS PROCEDURES

**Importance: 🟡 IMPORTANT — Enables effective AI execution**

**Implements:** Atomic Task Decomposition (Domain)  
**Input:** Validated Architecture (Title 3)  
**Gate:** Task Validation (§4.2)

## Part 4.1: Decomposition Requirements

### 4.1.1 Purpose

Break planned work into atomic tasks that AI can effectively execute. Proper decomposition prevents context overflow and enables independent validation.

### 4.1.2 Task Characteristics

Every task MUST be:

| Characteristic | Requirement | Validation |
|----------------|-------------|------------|
| **Atomic** | Single coherent change | Cannot be meaningfully subdivided |
| **Bounded** | ≤15 files affected | Count before starting |
| **Testable** | Can be verified independently | Acceptance criteria defined |
| **Traceable** | Links to specification requirement | Explicit reference |
| **Estimable** | Reasonable effort prediction | Typically 1-4 hours |

### 4.1.3 Decomposition by Mode

**EXPEDITED Mode:**
- Standard task breakdown
- Minimal dependency documentation
- Sequential execution assumed

**STANDARD Mode:**
- Detailed task breakdown
- Explicit dependency mapping
- Priority sequencing
- Parallel opportunity identification

**ENHANCED Mode:**
- All STANDARD activities, plus:
- Milestone grouping
- Learning checkpoints
- Iteration boundaries
- Validation hypotheses per milestone

### 4.1.4 Task Documentation

Each task includes:

```
TASK: [Identifier]
────────────────────
Requirement: [Link to specification]
Description: [What to build]
Acceptance Criteria: [How to verify]
Files Affected: [List, must be ≤15]
Dependencies: [Prior tasks required]
Estimated Effort: [Time range]
```

---

## Part 4.2: Sizing Validation

### 4.2.1 Purpose

Verify tasks meet P3 requirements before implementation begins.

### 4.2.2 Size Checklist

For each task:
- [ ] Files affected ≤15?
- [ ] Can be tested independently?
- [ ] Single coherent change?
- [ ] Dependencies explicit?
- [ ] Effort estimate reasonable?

### 4.2.3 Oversized Task Remediation

If a task exceeds thresholds:

1. **Identify natural boundaries:** Where can the task be split?
2. **Create subtasks:** Each subtask must meet all task characteristics
3. **Define integration task:** If subtasks need connection, make that explicit
4. **Re-validate:** Run size checklist on all subtasks

### 4.2.4 Validation Gate

Before proceeding to Implement phase:
- [ ] All tasks meet size requirements
- [ ] All tasks have acceptance criteria
- [ ] Dependencies form valid DAG (no cycles)
- [ ] Coverage: tasks cover all specification requirements
- [ ] Product Owner approval for task list

---

## Part 4.3: Dependency Mapping

### 4.3.1 Purpose

Identify task dependencies to enable proper sequencing and parallel execution.

### 4.3.2 Dependency Types

| Type | Description | Example |
|------|-------------|---------|
| **Hard** | Must complete before starting | Database schema before API endpoints |
| **Soft** | Beneficial but not required | Utility functions before main features |
| **Resource** | Requires same resource (serialization) | Both modify same file |
| **Integration** | Connects outputs of other tasks | Combines frontend and backend |

### 4.3.3 Dependency Documentation

Create dependency graph or matrix:

```
Task A → Task B → Task D
            ↘
              Task C → Task D
```

Or:

| Task | Depends On | Enables |
|------|-----------|---------|
| A | (none) | B |
| B | A | C, D |
| C | B | D |
| D | B, C | (none) |

### 4.3.4 Parallel Identification

Identify tasks that can execute in parallel:
- No hard dependencies between them
- No resource conflicts
- Independent validation possible

Document parallel opportunities for efficiency.

---

# TITLE 5: IMPLEMENT PROCEDURES

**Importance: 🔴 CRITICAL — Where code gets written**

**Implements:** Production-Ready Standards (Domain), Security-First Development (Domain), Testing Integration (Domain), Supply Chain Integrity (Domain), Workflow Integrity (Domain)  
**Input:** Validated Tasks (Title 4)  
**Validation:** Per-task and integration validation

## Part 5.1: Implementation Loop

### 5.1.1 Purpose

Execute tasks using the Write → Run → Validate cycle. This pattern ensures continuous quality integration.

### 5.1.2 The Implementation Cycle

For each task:

```
┌─────────────────────────────────────────────────────────┐
│  1. WRITE                                               │
│     - Implement task requirements                       │
│     - Write tests alongside code (Q3)                   │
│     - Apply security patterns (Q2)                      │
│     - Verify dependencies (Q4)                          │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  2. RUN                                                 │
│     - Execute tests                                     │
│     - Run linters/formatters                            │
│     - Run security scan (if applicable)                 │
│     - Verify build success                              │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  3. VALIDATE                                            │
│     - Check acceptance criteria                         │
│     - Review against specification                      │
│     - Verify no regressions                             │
│     - Confirm task complete                             │
└─────────────────────────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         PASS │                     │ FAIL
              │                     │
              ▼                     ▼
        Next Task              Fix & Re-run
```

### 5.1.3 Implementation Quality Standards

During WRITE phase, apply:

| Standard | Requirement | Source |
|----------|-------------|--------|
| Test Coverage | ≥80% for new code | Q1 |
| Security Scan | Zero HIGH/CRITICAL | Q2 |
| Test-with-Implementation | Tests written with code | Q3 |
| Dependency Verification | All packages verified | Q4 |
| Input Validation | Untrusted input sanitized | Q5 |

### 5.1.4 Implementation Escalation

Escalate to Product Owner when:
- Task cannot be completed as specified
- Security vulnerability requires architecture change
- Dependency issue blocks progress
- Scope creep detected during implementation

---

## Part 5.2: Testing Integration

### 5.2.1 Purpose

Implement Q3 (Testing Integration) by writing tests alongside implementation.

### 5.2.2 Test-First or Test-With

Two acceptable patterns:

**Test-First (TDD):**
1. Write failing test
2. Write minimal code to pass
3. Refactor
4. Repeat

**Test-With:**
1. Write code and test together
2. Both complete before moving on
3. Neither deferred to "later"

Both patterns satisfy Q3. Choose based on preference and context.

### 5.2.3 Test Types by Layer

| Layer | Test Type | Responsibility |
|-------|-----------|----------------|
| Unit | Function/method behavior | AI implements |
| Integration | Component interaction | AI implements |
| E2E | User workflow | AI implements key paths |
| Manual | Edge cases, exploratory | Product Owner |

### 5.2.4 Coverage Verification

Before task completion:
- [ ] Unit tests written for new functions
- [ ] Integration tests for new components
- [ ] Coverage meets ≥80% threshold
- [ ] All tests passing

### 5.2.5 Test Organization Patterns

🟡 **IMPORTANT** — Patterns for organizing test suites at scale.

#### Test File Structure

Separate unit tests from integration tests using file naming conventions:

```
tests/
├── conftest.py                    # Shared fixtures (always load first)
├── test_{module}.py               # Unit tests (mock dependencies)
├── test_{module}_integration.py   # Integration tests (real components)
└── __init__.py
```

**Rationale:** Unit tests run fast with mocks; integration tests verify real component interaction. Separation enables running fast tests during development (`pytest tests/test_*.py -m "not integration"`) and full suite in CI.

#### Fixture Categories (conftest.py)

Organize fixtures by purpose:

| Category | Purpose | Example |
|----------|---------|---------|
| **Path Fixtures** | Isolated temp directories | `test_settings(tmp_path)` |
| **Model Fixtures** | Sample valid objects | `sample_principle()` |
| **State Reset** | Clear global state between tests | `reset_server_state()` |
| **Mock Fixtures** | Pre-configured mocks for external dependencies | `mock_embedder()` |

**State Reset Pattern:**
```python
@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset module-level state before each test."""
    import my_module
    my_module._global_cache = None
    my_module._singleton = None
    yield
    # Cleanup after test if needed
```

#### Test Markers

Use markers to categorize tests for selective execution:

```python
@pytest.mark.slow           # ML models, network calls
@pytest.mark.integration    # Full pipeline tests
@pytest.mark.real_data      # Tests against production data
@pytest.mark.asyncio        # Async tests (pytest-asyncio)
```

**pytest.ini configuration:**
```ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks integration tests
    real_data: marks tests using production data
```

**CI optimization:** Run `-m "not slow"` for fast feedback, full suite nightly.

#### Standard Edge Cases Checklist

Every function accepting input should test:

- [ ] Empty string `""`
- [ ] Missing required field / `None`
- [ ] Boundary values (exactly at threshold, just below/above)
- [ ] Invalid type (string where int expected)
- [ ] Unicode/special characters
- [ ] Very long input (truncation behavior)
- [ ] Whitespace-only input `"   "`

#### Response Parsing Helper

When testing tools that wrap responses (footers, metadata), create a helper:

```python
def extract_json_from_response(text: str) -> str:
    """Strip wrappers/footers from tool responses for JSON parsing."""
    separator = "\n\n---\n"  # Common footer pattern
    if separator in text:
        return text.split(separator)[0]
    return text

# Usage in test
response = await call_tool("my_tool", {"arg": "value"})
parsed = json.loads(extract_json_from_response(response[0].text))
assert parsed["status"] == "success"
```

#### When to Parameterize

| Parameterize When | Keep Separate When |
|-------------------|-------------------|
| Same logic, different inputs | Different assertions per case |
| >4 similar tests | Complex setup differs per case |
| Boundary value testing | Need clear failure identification |
| Enum/status code coverage | Debugging specific edge cases |

**Parameterization example:**
```python
@pytest.mark.parametrize("score,expected_level", [
    (0.8, "high"),
    (0.5, "medium"),
    (0.2, "low"),
])
def test_confidence_level(score, expected_level):
    assert get_confidence(score) == expected_level
```

#### Mocking Strategy

| Layer | Mock? | Rationale |
|-------|-------|-----------|
| External APIs | Always | Deterministic, fast, no network |
| Database | Usually | Use in-memory or fixtures |
| File system | Usually | Use `tmp_path` fixture |
| Internal modules | Unit only | Integration uses real |
| ML models | Unit only | Slow to load; mock embeddings |

**Mock at boundaries, not internals.** Unit tests mock dependencies; integration tests use real components with controlled inputs.

#### ML Model Mocking Pattern

When testing code that uses ML models (embeddings, LLMs, rerankers, classifiers), standard mocking often fails due to lazy loading and batch processing. These patterns address common gotchas:

**1. Patch at source, not import location:**

ML models are often lazy-loaded inside properties or functions. Patch the source library, not where it's imported:

```python
# WRONG: Patches where used — fails if model is lazy-loaded in property
with patch("my_module.SentenceTransformer"):
    ...

# CORRECT: Patches source library before any import triggers loading
with patch("sentence_transformers.SentenceTransformer", Mock(return_value=mock_embedder)):
    ...
```

**2. Import after patching:**

If the module instantiates models at import time or in class properties, import AFTER establishing the patch:

```python
def test_embedding_generation(self, mock_embedder):
    mock_constructor = Mock(return_value=mock_embedder)

    with patch("sentence_transformers.SentenceTransformer", mock_constructor):
        # Import AFTER patch is active
        from my_module import EmbeddingService

        service = EmbeddingService()
        result = service.embed("test query")

        assert result.shape == (384,)
```

**3. Use seeded random for deterministic embeddings:**

Mock embeddings must be deterministic across test runs for reproducibility:

```python
@pytest.fixture
def mock_embedder():
    """Mock SentenceTransformer with deterministic embeddings."""
    embedder = Mock()
    np.random.seed(42)  # Same seed = same "random" vectors every run

    def mock_encode(texts, *args, **kwargs):
        # Handle both single string and batch inputs
        if isinstance(texts, str):
            return np.random.rand(384).astype(np.float32)
        return np.random.rand(len(texts), 384).astype(np.float32)

    embedder.encode = Mock(side_effect=mock_encode)
    embedder.get_sentence_embedding_dimension = Mock(return_value=384)
    return embedder
```

**Key elements:**
- `side_effect` with callable (not static `return_value`) — responds to varying batch sizes
- Match real interface contract (`encode`, `get_sentence_embedding_dimension`)
- Correct dtype (`float32`) for numpy compatibility
- Seeded random ensures test determinism

**4. Mock rerankers with realistic score patterns:**

Rerankers return relevance scores. Mock with decreasing scores to simulate realistic ranking:

```python
@pytest.fixture
def mock_reranker():
    """Mock CrossEncoder with plausible rerank scores."""
    reranker = Mock()

    def mock_predict(pairs, *args, **kwargs):
        # Return decreasing scores: first pair most relevant
        if isinstance(pairs, list):
            return np.array([0.9 - i * 0.1 for i in range(len(pairs))])
        return np.array([0.5])

    reranker.predict = Mock(side_effect=mock_predict)
    return reranker
```

**Common Gotchas:**

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| Patch wrong location | `Mock` object has no attribute `encode` | Patch `sentence_transformers.X`, not `my_module.X` |
| Static return value | Shape mismatch on batch operations | Use `side_effect` with callable |
| Missing seed | Tests pass locally, fail in CI | Add `np.random.seed()` before generating arrays |
| Wrong dtype | numpy casting errors | Explicitly use `.astype(np.float32)` |
| Import before patch | Real model loads (slow, or fails) | Import target module inside `with patch` block |

---

## Part 5.3: Security Validation

### 5.3.1 Purpose

Implement Q2 (Security-First) by integrating security throughout implementation.

### 5.3.2 Security Checklist

Apply per task:

**Input Handling:**
- [ ] All user input validated
- [ ] No direct SQL construction (use parameterized)
- [ ] No direct HTML rendering of user content (use sanitization)
- [ ] File uploads validated and constrained

**Authentication/Authorization:**
- [ ] Auth checks on all protected endpoints
- [ ] Proper session management
- [ ] No hardcoded credentials
- [ ] Secrets in environment variables

**Data Protection:**
- [ ] Sensitive data encrypted at rest
- [ ] Secure transmission (HTTPS)
- [ ] No sensitive data in logs
- [ ] Proper data retention/deletion

### 5.3.3 Security Scanning

When available, run automated security scanning:
- Static analysis (SAST)
- Dependency vulnerability scan
- Secret detection

**Threshold:** Zero HIGH/CRITICAL vulnerabilities before task completion.

### 5.3.4 Security Escalation

Escalate immediately when:
- Vulnerability cannot be fixed within task scope
- Security requirement conflicts with functionality
- Third-party dependency has known vulnerability
- Architecture change required for security

---

## Part 5.4: Dependency Verification

### 5.4.1 Purpose

Implement Q4 (Supply Chain Integrity) by verifying all dependencies.

### 5.4.2 Verification Procedure

For each new dependency:

1. **Existence Check:** Verify package exists in registry
2. **Popularity Check:** Reasonable download counts, stars, activity
3. **Maintenance Check:** Recent updates, responsive maintainers
4. **Security Check:** No known vulnerabilities
5. **License Check:** Compatible with project requirements

### 5.4.3 Hallucination Prevention

AI-recommended packages require verification:

- [ ] Package name exactly matches registry
- [ ] Package provides claimed functionality
- [ ] Import statements match actual package API
- [ ] Version specified is published version

**If package cannot be verified:** Do not use. Find alternative or escalate.

### 5.4.4 Lock File Maintenance

- Commit lock files (package-lock.json, yarn.lock, etc.)
- Verify lock file updated with changes
- Review lock file changes in version control

---

## Part 5.5: Iteration Protocol [ENHANCED Mode]

**Importance: 🟢 OPTIONAL — Only for MVP/uncertain projects**

### 5.5.1 When to Apply

Apply iteration protocol when:
- Requirements are uncertain
- Learning is a primary goal
- MVP validation approach
- Experimental features

### 5.5.2 Iteration Structure

```
MILESTONE 1
├── Tasks 1-N
├── Validation
└── Learning Checkpoint
    ├── What worked?
    ├── What didn't?
    └── What changes for next milestone?

MILESTONE 2
├── Tasks (adjusted based on M1 learning)
├── Validation
└── Learning Checkpoint

[Continue until complete or pivot]
```

### 5.5.3 Pivot Triggers

Consider pivoting when:
- Learning invalidates core assumptions
- User feedback contradicts specification
- Technical approach proves infeasible
- Business requirements change

Document pivot decision and rationale in State File.

### 5.5.4 Iteration Documentation

After each milestone:
- [ ] Learning captured
- [ ] Adjustments documented
- [ ] Next milestone refined
- [ ] Product Owner informed

---

# TITLE 6: VALIDATION PROCEDURES

**Importance: 🔴 CRITICAL — Prevents downstream failures**

**Implements:** Validation Gates (Domain)  
**Applies to:** All phase transitions and significant outputs

## Part 6.1: Technical Validation Gates

### 6.1.1 Purpose

Verify outputs meet technical requirements before proceeding. Technical validation is automated or AI-performed.

### 6.1.2 Validation by Phase

**Specify → Plan Gate:**
- [ ] Specification complete (§2.3 checklist)
- [ ] No contradictions detected
- [ ] Scope appropriate for resources
- [ ] Product Owner approved

**Plan → Tasks Gate:**
- [ ] Architecture validated (§3.2.4 checklist)
- [ ] Technology choices justified
- [ ] Risks identified and mitigated
- [ ] Product Owner approved

**Tasks → Implement Gate:**
- [ ] All tasks meet size requirements
- [ ] Dependencies valid (no cycles)
- [ ] Full coverage of requirements
- [ ] Product Owner approved

**Implement → Complete Gate:**
- [ ] All tasks completed
- [ ] All tests passing
- [ ] Security scan clean
- [ ] Coverage meets threshold
- [ ] Product Owner approved

### 6.1.3 Gate Failure Procedure

When validation fails:

1. **Identify failure:** Which checks failed?
2. **Diagnose cause:** Why did they fail?
3. **Remediate:** Fix the underlying issue
4. **Re-validate:** Run checks again
5. **Document:** Record failure and resolution

Do NOT bypass gates. Gates exist to prevent downstream problems.

---

## Part 6.2: Vision Validation (PO Review)

### 6.2.1 Purpose

Verify outputs align with Product Owner's intent. Vision validation is human-performed.

### 6.2.2 Vision Validation Points

Request Product Owner review at:
- End of Specify phase (specification approval)
- End of Plan phase (architecture approval)
- End of Tasks phase (task list approval)
- End of significant implementation milestones
- Project completion (final acceptance)

### 6.2.3 Vision Validation Format

Present to Product Owner:

```
PHASE COMPLETE: [Phase Name]
──────────────────────────────
Summary: [What was accomplished]
Key Decisions: [Decisions made and rationale]
Outputs: [Artifacts produced]
Next Phase: [What comes next]
Questions: [Any items requiring PO input]

REQUEST: Approval to proceed / Feedback required
```

### 6.2.4 Vision Validation Outcomes

| Outcome | Action |
|---------|--------|
| **Approved** | Proceed to next phase |
| **Approved with comments** | Note comments, proceed |
| **Revision requested** | Return to appropriate step, revise |
| **Rejected** | Major rework or project reassessment |

Document outcome in State File.

---

## Part 6.3: Phase Transition Protocol

### 6.3.1 Purpose

Formalize the transition between phases to ensure nothing is missed.

### 6.3.2 Transition Checklist

Before any phase transition:

- [ ] Phase work complete
- [ ] Technical validation passed
- [ ] Vision validation passed
- [ ] State file updated
- [ ] Context prepared for next phase
- [ ] Next phase entry criteria met

### 6.3.3 Transition Documentation

At each transition, document:

```
TRANSITION: [From Phase] → [To Phase]
──────────────────────────────────────
Date: [Date]
Mode: [Expedited/Standard/Enhanced]
Outputs: [List of artifacts]
Carryforward: [Items for next phase attention]
State File: [Updated location]
```

---

## Part 6.4: Automated Validation (CI/CD)

**Importance: 🟡 IMPORTANT — Enables continuous quality assurance**

### 6.4.1 Purpose

Continuous Integration/Continuous Deployment (CI/CD) automates validation gates, ensuring code quality is verified on every change. This implements Q-series principles (Production-Ready Standards, Security-First Development, Testing Integration) through automated enforcement.

### 6.4.2 CI/CD Benefits

| Benefit | Implementation |
|---------|----------------|
| **Automated Testing** | Tests run on every push/PR |
| **Security Scanning** | Vulnerabilities caught before merge |
| **Code Quality** | Linting enforces standards |
| **Reproducibility** | Same checks run for everyone |
| **Documentation** | Pipeline defines quality gates |

### 6.4.3 Minimum CI Pipeline

Every production project should have automated validation:

**Required Jobs:**

| Job | Purpose | Tools (Examples) |
|-----|---------|------------------|
| **test** | Run test suite | pytest, jest, go test |
| **lint** | Check code quality | ruff, eslint, golangci-lint |
| **security** | Scan for vulnerabilities | pip-audit, npm audit, bandit |

**Recommended Additions:**

| Job | Purpose | When to Add |
|-----|---------|-------------|
| **build** | Verify compilation | Compiled languages |
| **coverage** | Enforce test coverage | ≥80% threshold |
| **type-check** | Static type analysis | TypeScript, Python with mypy |

### 6.4.4 GitHub Actions Template

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/ -v

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Scan dependencies
        run: pip-audit --strict
      - name: Scan source code
        run: bandit -r src/

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install linter
        run: pip install ruff
      - name: Check code style
        run: ruff check src/ tests/
      - name: Check formatting
        run: ruff format --check src/ tests/
```

### 6.4.5 CI/CD Integration Points

**With Validation Gates (§6.1):**
- CI results become part of gate checklist
- Failed CI blocks phase transition
- CI logs provide gate failure diagnostics

**With Security Validation (§5.3):**
- Automated security scans supplement manual review
- Zero HIGH/CRITICAL threshold enforced automatically
- Dependency vulnerabilities caught at PR stage

**With Testing Integration (§5.2):**
- Coverage reports generated in CI
- Test failures block merge
- Cross-platform testing via matrix strategy

### 6.4.6 CI/CD Best Practices

**Speed Optimization:**
- Cache dependencies between runs
- Run independent jobs in parallel
- Skip slow tests with markers (`-m "not slow"`)
- Use matrix strategy for multi-version testing

**Reliability:**
- Pin action versions (`@v4` not `@latest`)
- Use `continue-on-error` for non-blocking checks
- Set reasonable timeouts
- Handle rate limits gracefully

**Security:**
- Never expose secrets in logs
- Use GitHub secrets for credentials
- Scan for secrets in commits
- Pin dependencies to exact versions

**ML/AI Projects:**
- Use CPU-only PyTorch in CI to avoid disk space issues:
  ```yaml
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  pip install -e ".[dev]"
  ```
- GPU dependencies (CUDA, cuDNN) add 3-4GB; runners have ~14GB total
- Set `fail-fast: false` during debugging to see all matrix results
- Mark slow embedding tests with `@pytest.mark.slow` and skip in CI

### 6.4.7 CI/CD Checklist

Before deploying CI/CD:
- [ ] Test job runs full test suite
- [ ] Security job scans dependencies and source
- [ ] Lint job checks code style
- [ ] Jobs run in parallel where possible
- [ ] Caching configured for dependencies
- [ ] Matrix covers supported versions
- [ ] Failure notifications configured

---

## Part 6.5: Project Hygiene

**Importance: 🟡 IMPORTANT — Maintains codebase health over time**

**Implements:** Q3 (Testing Standards), G1 (Sustainable Practices)
**Applies to:** All project phases, especially before releases and after major milestones

### 6.5.1 Purpose

Project hygiene prevents accumulation of obsolete files, maintains clear organization, and ensures the repository remains navigable. Clean projects:
- Reduce cognitive load when onboarding or resuming
- Prevent confusion about which files are current
- Keep repository size manageable
- Pass security audits (no exposed secrets or debug artifacts)

### 6.5.2 Standard Directory Structure

**Python Projects:**
```
project-root/
├── src/                    # Source code (package directory)
│   └── package_name/       # Main package
├── tests/                  # Test files mirror src/ structure
├── documents/              # Specifications, governance docs
│   └── archive/            # Historical versions, completed gates
├── index/                  # Generated indexes, embeddings (if applicable)
├── .github/                # CI/CD workflows, issue templates
├── README.md               # External-facing documentation
├── CLAUDE.md               # AI governance loader
├── SESSION-STATE.md        # Current session state
├── PROJECT-MEMORY.md       # Architectural decisions
├── LEARNING-LOG.md         # Lessons learned
├── pyproject.toml          # Project configuration
└── .gitignore              # Exclusion rules
```

**Key Principles:**
- Source code in `src/` (not root)
- Tests mirror source structure
- Generated files in dedicated directories
- Documentation versioned with `archive/` for historical versions

### 6.5.3 File Classification

| Category | Action | Examples |
|----------|--------|----------|
| **Generated** | Delete + gitignore | `htmlcov/`, `.coverage`, `*.pyc`, `__pycache__/` |
| **Cache** | Delete + gitignore | `.pytest_cache/`, `.ruff_cache/`, `.cache/` |
| **IDE** | Delete + gitignore | `.idea/`, `.vscode/`, `*.swp` |
| **Platform** | Delete + gitignore | `.DS_Store`, `Thumbs.db`, `.Rhistory` |
| **Historical** | Archive | Completed gate artifacts, superseded specs |
| **Obsolete** | Delete | Abandoned experiments, deprecated code |
| **Duplicate** | Delete lower priority | `claude.md` when `CLAUDE.md` exists |

### 6.5.4 Essential .gitignore Entries

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Virtual environments
venv/
.venv/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
coverage.xml

# Linting
.ruff_cache/
.mypy_cache/

# IDE
.idea/
.vscode/
*.swp

# Platform
.DS_Store
Thumbs.db

# Cache
.cache/

# Environment
.env
.env.local

# Project-specific logs
logs/*.jsonl
```

### 6.5.5 Archive vs Delete Decision Matrix

| Condition | Decision | Rationale |
|-----------|----------|-----------|
| Contains historical decisions | Archive | Preserves decision context |
| Gate artifact (completed) | Archive | Audit trail for methodology |
| Superseded specification | Archive | Reference for what changed |
| Generated/reproducible | Delete | Can be regenerated |
| Duplicate of canonical file | Delete | Single source of truth |
| Abandoned experiment | Delete | No ongoing value |
| Debug/temp files | Delete | Not project artifacts |

### 6.5.6 Cleanup Triggers

**When to perform cleanup:**

| Trigger | Scope | Focus |
|---------|-------|-------|
| Before release | Full | Remove all debug artifacts, verify .gitignore |
| After phase completion | Phase | Archive gate artifacts, clean generated files |
| Before major commit | Changed areas | Ensure no temp files staged |
| Repository size growing | Full | Identify large unnecessary files |
| Onboarding new contributor | Full | Verify project is navigable |

### 6.5.7 Cleanup Procedure

1. **Inventory current state:**
   ```bash
   # List all files not in .gitignore
   git ls-files

   # Find large files
   find . -type f -size +1M | head -20

   # Check for common cleanup targets
   find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store"
   ```

2. **Classify files** using the table in §6.5.3

3. **Delete generated/cache/obsolete files:**
   ```bash
   # Remove Python caches
   find . -type d -name "__pycache__" -exec rm -rf {} +
   find . -type f -name "*.pyc" -delete

   # Remove coverage artifacts
   rm -rf htmlcov/ .coverage coverage.xml
   ```

4. **Archive historical files:**
   ```bash
   mkdir -p documents/archive
   mv GATE-*.md documents/archive/
   ```

5. **Update .gitignore** for any new patterns discovered

6. **Verify cleanup:**
   ```bash
   git status  # Should show deletions, no untracked junk
   ```

### 6.5.8 Project Hygiene Checklist

Before release or major milestone:
- [ ] No generated files committed (htmlcov, .coverage, __pycache__)
- [ ] No IDE/platform files committed (.DS_Store, .idea)
- [ ] Completed gate artifacts archived
- [ ] Superseded specs archived with version suffix
- [ ] .gitignore covers all reproducible artifacts
- [ ] No duplicate files (lowercase/uppercase variants)
- [ ] No abandoned experiments in repository
- [ ] Large files justified or removed

---

# TITLE 7: MEMORY ARCHITECTURE

**Importance: 🔴 CRITICAL — Enables context continuity across sessions**

**Implements:** Session State Continuity (Domain), Context Window Management (Domain)
**Applies to:** All sessions and project lifecycle

## Part 7.0: Memory System Overview

### 7.0.1 Purpose

AI has no persistent memory between sessions. The Memory Architecture creates external memory through structured files that enable:
- Session continuity (pick up where we left off)
- Decision preservation (don't re-debate settled questions)
- Learning accumulation (improve over project lifetime)
- Context efficiency (load relevant memory, not everything)

### 7.0.2 Cognitive Memory Types

**Importance: 🔴 CRITICAL — Core memory taxonomy aligned with AI agent research**

Memory files map to cognitive memory types from the CoALA framework (Cognitive Architectures for Language Agents):

| Cognitive Type | File | Purpose | Lifecycle |
|----------------|------|---------|-----------|
| **Working Memory** | `SESSION-STATE.md` | What's active right now | Overwritten each session |
| **Semantic Memory** | `PROJECT-MEMORY.md` | Facts, decisions, gates, knowledge | Accumulates, periodically summarized |
| **Episodic Memory** | `LEARNING-LOG.md` | Events, experiences, lessons | Pruned when internalized |
| **Procedural Memory** | Methods documents | How to do things | Evolves with practice |

**Why cognitive framing matters:**
- **Working memory** is transient — don't try to preserve it across sessions
- **Semantic memory** is facts — decisions don't expire, they get superseded
- **Episodic memory** is experiences — valuable until the lesson becomes a pattern
- **Procedural memory** is skills — when a lesson becomes a general practice, move it from LEARNING-LOG to methods

### 7.0.3 Memory Loading Strategy

**On session start:**
1. Always load: `SESSION-STATE.md` (know where we are)
2. Load if relevant: `PROJECT-MEMORY.md` sections (decisions affecting current work)
3. Reference on demand: `LEARNING-LOG.md` (when similar situation arises)

**Context efficiency:**
- Don't load entire memory files if not needed
- Reference specific sections when relevant
- Summarize historical context rather than loading verbatim

### 7.0.4 Memory Lifecycle Principles

**Core Principle:** *"Memory serves reasoning, not archival. Retain what informs future decisions; prune what only describes the past."*

| Memory Type | Retain | Prune When |
|-------------|--------|------------|
| **Working** (SESSION-STATE) | Current session only | Every session start (overwrite) |
| **Semantic** (PROJECT-MEMORY) | Active decisions, constraints | Decision is superseded or obsolete |
| **Episodic** (LEARNING-LOG) | Lessons not yet patterns | Lesson internalized into procedures |

**Anti-principle:** Never prune for size alone. If memory is too large, this indicates either:
1. Too much detail (summarize instead of delete)
2. Scope creep (split the project)

**Superseded decisions:** Don't delete — mark as superseded with date and link to new decision. Context of why we changed matters.

**Distillation Triggers:**

| Memory File | Trigger | Action |
|-------------|---------|--------|
| SESSION-STATE.md | > 300 lines | Prune to current state only |
| PROJECT-MEMORY.md | > 800 lines | Condense decisions, check superseded |
| LEARNING-LOG.md | Entry > 6 months | Graduate to methods or delete |

**Memory Health Check:**
```bash
wc -l SESSION-STATE.md PROJECT-MEMORY.md LEARNING-LOG.md
# Targets: SESSION < 300, PROJECT < 800
```
Run this check: session end, before releases, when files feel bloated.

---

## Part 7.1: Session State

**Importance: 🔴 CRITICAL — Required for session continuity**

### 7.1.1 Purpose

Track current work state so any session (same AI, new AI, different tool) can resume seamlessly.

### 7.1.2 Session State File Structure

File: `SESSION-STATE.md` (project root)

```markdown
# Session State

**Last Updated:** [ISO timestamp]
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position
- **Phase:** [Specify/Plan/Tasks/Implement]
- **Mode:** [Expedited/Standard/Enhanced]
- **Active Task:** [Task ID or "between tasks"]
- **Blocker:** [None or description]

## Active Tasks
> Include during Implement phase. For team projects, reference GitHub Issues instead.

| ID | Task | Status |
|----|------|--------|
| T1 | Implement user auth | ✓ Complete |
| T2 | Add validation | 🔄 In Progress |
| T3 | Write tests | ⏳ Pending |

## Immediate Context
[2-3 sentences: What was happening when session ended]

## Next Actions
1. [First priority - specific and actionable]
2. [Second priority]
3. [Third priority if applicable]

## Session Notes
[Any context the next session needs that doesn't fit elsewhere]
```

### 7.1.3 Task Tracking Rationale

**Why tasks are inline:** Research on AI agent memory architecture shows that task decomposition "becomes part of the agent's state" during active work. Project-specific tasks (unlike reusable procedures) are ephemeral—created in Tasks phase, consumed in Implement phase, then cleared. Keeping them in SESSION-STATE (working memory) provides immediate access without cross-reference friction.

**Task status values:** 🔄 In Progress | ⏳ Pending | ✓ Complete

**When to use GitHub Issues instead:**
- Team/collaborative projects (shared visibility)
- Open source projects (external contributor coordination)
- Need for automation (auto-close, cross-references)
- Long-term backlog management (persists beyond project)

When using GitHub Issues, reference them in Active Task field: `Active Task: #42 - Implement auth`

### 7.1.4 Update Triggers

Update `SESSION-STATE.md` when:
- Completing a task
- Hitting a blocker
- Making a decision
- Changing focus
- Before ending session (ALWAYS)

### 7.1.5 Session State is Transient

Session state captures the CURRENT moment. Historical information belongs in Project Memory or Learning Log. Keep session state minimal and actionable.

---

## Part 7.2: Project Memory (Semantic Memory)

**Importance: 🟡 IMPORTANT — Preserves decisions, rationale, and gate status**

### 7.2.1 Purpose

Preserve significant decisions, specifications, architecture, and phase gate status so they don't need to be re-discovered or re-debated. This is the project's semantic memory — facts that remain true until superseded.

### 7.2.2 Project Memory File Structure

File: `PROJECT-MEMORY.md` (project root)

```markdown
# Project Memory

**Project:** [Name]
**Started:** [Date]
**Mode:** [Expedited/Standard/Enhanced]
**Memory Type:** Semantic (accumulates)
**Lifecycle:** Prune when decisions superseded per §7.0.4

> Preserves significant decisions and rationale.
> Mark superseded decisions with date and replacement link.

---

## Specification Summary
[Condensed version of key requirements - not full spec]
- **Problem:** [One sentence]
- **Users:** [Target audience]
- **Core Features:** [Bulleted list]
- **Out of Scope:** [What we're NOT building]

## Phase Gates

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Specify → Plan | ⏳ Pending | — | — |
| Plan → Tasks | ⏳ Pending | — | — |
| Tasks → Implement | ⏳ Pending | — | — |
| Implement → Complete | ⏳ Pending | — | — |

> Status: ⏳ Pending | ✓ Passed | ❌ Failed. Add "Approver" column for team projects.

## Architecture Decisions

### [Decision Title]
- **Decision:** [What we decided]
- **Rationale:** [Why we decided it]
- **Alternatives Considered:** [What we rejected]
- **Date:** [When decided]
- **Status:** [Active / Superseded by X]

[Repeat for each significant decision]

## Technical Stack
- **Frontend:** [Technologies]
- **Backend:** [Technologies]
- **Database:** [Technologies]
- **Infrastructure:** [Technologies]

## Constraints & Standards
- [Constraint 1 with rationale]
- [Constraint 2 with rationale]

## Key Artifacts
| Artifact | Location | Status |
|----------|----------|--------|
| Specification | [path] | [status] |
| Architecture | [path] | [status] |
| [etc.] | | |

## Known Gotchas
> Project-specific pitfalls discovered during development. Review before making changes.

### [Gotcha Title]
**Issue:** [What goes wrong]
**Solution:** [How to avoid or fix it]

[Repeat for each gotcha discovered]
```

### 7.2.3 Update Triggers

Update `PROJECT-MEMORY.md` when:
- Completing a phase (specification, architecture, etc.)
- Making architecture decisions
- Changing technology choices
- Adding/removing constraints
- NOT for routine task completion (that's session state)

### 7.2.4 Memory vs. Source Documents

Project Memory is a SUMMARY, not a replacement for source documents:
- Full specification lives in its own file
- Full architecture lives in its own file
- Project Memory provides quick reference and decision rationale
- When details needed, reference source documents

---

## Part 7.3: Learning Log (Episodic Memory)

**Importance: 🟡 IMPORTANT — Captures experiences for continuous improvement**

### 7.3.1 Purpose

Capture lessons learned, patterns discovered, and insights that improve future work on this project (and potentially others). This is the project's episodic memory — specific events and experiences.

### 7.3.2 Creation Timing

Create `LEARNING-LOG.md` when the first lesson emerges — typically during implementation when something unexpected happens (good or bad). Don't create it empty at project start.

### 7.3.3 Learning Log File Structure

File: `LEARNING-LOG.md` (project root)

```markdown
# Learning Log

**Project:** [Name]
**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> When lesson becomes pattern: Add to methods doc, mark "Graduated to §X.Y"

---

## Lessons Learned

### [Date]: [Lesson Title]
**Context:** [What situation prompted this learning]
**Lesson:** [What we learned]
**Application:** [How to apply this going forward]

[Repeat for each lesson]

## Patterns That Worked

### [Pattern Name]
**Situation:** [When to use this pattern]
**Approach:** [What to do]
**Why It Works:** [Rationale]

[Repeat for each pattern]

## Patterns That Failed

### [Pattern Name]
**Situation:** [When we tried this]
**What Happened:** [How it failed]
**Instead Do:** [Better alternative]

[Repeat for each anti-pattern]

## Technical Discoveries

### [Discovery Title]
**Discovery:** [What we found]
**Implication:** [How it affects our work]

[Repeat for each discovery]
```

### 7.3.4 Update Triggers

Update `LEARNING-LOG.md` when:
- Something unexpected happens (good or bad)
- A pattern proves effective (or ineffective)
- Technical assumption proves wrong
- A better approach is discovered
- At milestone retrospectives (ENHANCED mode)

### 7.3.5 Learning Log Review

Before starting similar work:
- Review relevant Learning Log entries
- Apply lessons to current context
- Reference specific entries when they inform decisions

### 7.3.6 Graduation to Procedural Memory

When a lesson becomes a general pattern (applies beyond this specific project):
1. Document the pattern in the appropriate methods document
2. Add a note to the LEARNING-LOG entry: "Graduated to [methods doc] §X.Y"
3. The original episode can then be pruned (the pattern persists in procedural memory)

---

## Part 7.4: Project Instructions File (Loader)

**Importance: 🔴 CRITICAL — Enables AI to discover and activate memory**

### 7.4.1 Purpose

The Project Instructions File is the entry point that tells AI how to find context. It's a "loader" that points to memory files — not a container for all context.

**Key Principle:** Progressive disclosure — tell AI how to find info, don't front-load all info.

### 7.4.2 Tool Implementations

| Tool | File | Auto-loaded |
|------|------|-------------|
| Claude Code | `CLAUDE.md` | Yes, at session start |
| Gemini CLI | `GEMINI.md` | Yes, via @file.md imports |
| Cursor | `.cursor/rules/` | Yes, based on file patterns |
| Cross-tool | `AGENTS.md` | Emerging standard |

### 7.4.3 Minimal Loader Template

```markdown
# Project: [Name]

## Governance
- Framework: AI Coding Methods (current version)
- Mode: [Expedited/Standard/Enhanced]

## Memory
Load these files for context:
- SESSION-STATE.md — Current position, next actions
- PROJECT-MEMORY.md — Decisions, architecture, gates
- LEARNING-LOG.md — Lessons learned (reference when relevant)

## On Session Start
1. Load SESSION-STATE.md
2. Follow Next Actions
3. Reference PROJECT-MEMORY for constraints

## Key Commands
[Project-specific build/test/lint commands]
```

**Note:** For projects with source documents (ARCHITECTURE.md, README.md), extend Memory section per §7.5. See §7.8 for full initialization checklist.

### 7.4.4 Loader Best Practices

From [Anthropic Claude Code Best Practices](https://code.claude.com/docs/en/best-practices):

1. **Less is more** — Include as few instructions as reasonably possible
2. **Progressive disclosure** — Tell AI how to find info, not all info
3. **Universally applicable** — Keep content relevant to all sessions
4. **Hierarchical** — Use subdirectory files for scoped context (e.g., `src/backend/CLAUDE.md`)

**CLAUDE.md Content Guide:**

| ✅ Include | ❌ Exclude |
|-----------|-----------|
| Bash commands Claude can't guess | What Claude can figure out by reading code |
| Code style rules differing from defaults | Standard language conventions |
| Test instructions and preferred runners | Detailed API docs (link instead) |
| Repo etiquette (branch naming, PR conventions) | Frequently changing information |
| Architectural decisions specific to project | Long explanations or tutorials |
| Developer environment quirks (required env vars) | File-by-file codebase descriptions |
| Common gotchas or non-obvious behaviors | Self-evident practices ("write clean code") |

**Test for each line:** "Would removing this cause Claude to make mistakes?" If not, cut it. Bloated files cause instructions to be ignored.

**Anti-patterns:**
- Duplicating memory file content in the loader
- Including session-specific context (that's for SESSION-STATE)
- Long lists of rules (that's for methods documents)

---

## Part 7.5: Source Document Registry

**Importance: 🟢 OPTIONAL — Enhances context discovery for specialized projects**

### 7.5.1 Purpose

Projects may have specialized source documents beyond the core memory files. These documents contain factual information (semantic memory content) but warrant explicit registration so AI knows when to consult them.

**Key Distinction:** Source documents are *repositories of facts* — they don't represent different cognitive functions from the CoALA 4-type model. They're semantic memory stored in dedicated files for organizational clarity.

### 7.5.2 Common Patterns

| Document | Cognitive Role | Question Answered |
|----------|---------------|-------------------|
| ARCHITECTURE.md | Structural reference | How is it built? Component structure, data flow |
| README.md | Charter/scope | What is this for? Does new work fit scope? |
| SPECIFICATION.md | Requirements reference | What must it do? Acceptance criteria |
| API.md | Interface reference | What endpoints exist? Expected inputs/outputs |

### 7.5.3 When to Consult

| Document | Consult Before |
|----------|---------------|
| ARCHITECTURE.md | Modifying system structure, adding components, changing data flow |
| README.md | Adding features (scope validation), changing public contract |
| SPECIFICATION.md | Implementation decisions, acceptance testing |

### 7.5.4 Registry Template

Add to PROJECT-MEMORY.md when the project has specialized source documents:

```markdown
## Source Documents

| File | Purpose | Consult When |
|------|---------|--------------|
| ARCHITECTURE.md | System design, component responsibilities | Modifying structure |
| README.md | Project charter, scope definition | Adding features (scope validation) |
| [other files...] | [purpose] | [trigger conditions] |
```

### 7.5.5 Project Instructions Integration

Reference source documents in the loader file (e.g., CLAUDE.md) using the Memory table pattern:

```markdown
## Memory (Cognitive Types)

| Type | File | Purpose |
|------|------|---------|
| Working | SESSION-STATE.md | Current position, next actions |
| Semantic | PROJECT-MEMORY.md | Decisions, constraints, gates |
| Episodic | LEARNING-LOG.md | Lessons learned |
| Structural | ARCHITECTURE.md | System design, component responsibilities |
| Charter | README.md | Project scope, public contract |
```

**Note:** "Structural" and "Charter" labels are *organizational shortcuts*, not new cognitive types. Both contain semantic (factual) memory content.

---

## Part 7.6: Handoff Protocol

**Importance: 🔴 CRITICAL — Enables smooth session transitions**

### 7.6.1 Session End Procedure

Before ending any session:

1. **Complete atomic unit** (if close to done)
2. **Update SESSION-STATE.md** with current position
3. **Update PROJECT-MEMORY.md** if decisions were made
4. **Update LEARNING-LOG.md** if insights emerged
5. **Memory hygiene check:**
   - Remove completed work from SESSION-STATE (keep only current state)
   - Mark graduated lessons in LEARNING-LOG
   - Check for superseded decisions in PROJECT-MEMORY
6. **Pre-commit validation** (if governance/methods documents changed):
   - Version: filename version matches header version
   - Memory files: cognitive type headers present
   - Index: rebuild if documents changed (`python -m ai_governance_mcp.extractor`)
7. **Commit changes** if using version control

### 7.6.2 Session Start Procedure

When starting a new session:

1. **Load SESSION-STATE.md** — Where are we?
2. **Review Next Actions** — What should we do?
3. **Load relevant PROJECT-MEMORY.md sections** — What constraints apply?
4. **Check LEARNING-LOG.md** — Any relevant lessons?
5. **Confirm understanding** — Ask PO if unclear

### 7.6.3 Handoff Summary (for complex transitions)

When transitioning to different AI/tool/collaborator:

```
HANDOFF SUMMARY
───────────────
Date: [Timestamp]
From: [Tool/AI/Session ending, e.g., "Claude Code session #3"]
To: [Tool/AI/Session starting, e.g., "New collaborator" or "Claude App"]

Current State:
[Copy of SESSION-STATE.md current position]

Key Context:
[Critical decisions from PROJECT-MEMORY.md]

Watch Out For:
[Relevant lessons from LEARNING-LOG.md]

Immediate Priority:
[First thing next session should do]
```

---

## Part 7.7: Recovery Procedures

**Importance: 🟡 IMPORTANT — Handles unexpected interruptions**

### 7.7.1 Recovery Triggers

Execute recovery when:
- Session ended unexpectedly
- Memory files seem stale or inconsistent
- Context seems wrong
- "framework check" command received

### 7.7.2 Recovery Procedure

1. **Assess memory files:**
   - Check SESSION-STATE.md timestamp
   - Verify consistency with actual file states
   - Check for partial/corrupted updates

2. **Verify code state:**
   - Review recent commits/changes
   - Check for uncommitted work
   - Identify any conflicts

3. **Reconcile discrepancies:**
   - Update memory files to match reality
   - Document any lost work
   - Identify recovery actions

4. **Re-establish working state:**
   - Update SESSION-STATE.md
   - Reload governance documents
   - Confirm next actions

### 7.7.3 Recovery Documentation

Add to LEARNING-LOG.md:

```markdown
### [Date]: Recovery Event
**Trigger:** [What caused the recovery need]
**Lost Work:** [If any]
**Recovery Actions:** [What we did]
**Prevention:** [How to avoid in future]
```

---

## Part 7.8: Project Initialization Protocol

**Importance: 🔴 CRITICAL — Ensures consistent project setup**

### 7.8.1 Purpose

Single authoritative checklist for initializing new projects. Consolidates guidance from Cold Start Kit, §1.3, and memory architecture into one discoverable location.

### 7.8.2 Initialization Checklist

**Keywords:** project initialization, new project, bootstrap, cold start, project setup, starting fresh

Execute in order:

| Step | Action | Reference |
|------|--------|-----------|
| 1 | Calibrate procedural mode (Expedited/Standard/Enhanced) | §1.3 |
| 2 | Create SESSION-STATE.md | Cold Start Kit |
| 3 | Create PROJECT-MEMORY.md (start with Phase Gates table) | §7.2 |
| 4 | Create LEARNING-LOG.md (stub with usage header) | §7.3, §7.8.3 |
| 5 | Create project instructions file (CLAUDE.md, etc.) | §7.4.3 |
| 6 | Register source documents if applicable | §7.5 |
| 7 | Begin Specify phase | Title 2 |

### 7.8.3 File Creation Notes

| File | Guidance |
|------|----------|
| LEARNING-LOG.md | Create stub with usage header (no entries yet). Entries added when lessons emerge per §7.3.2 |
| Detailed ARCHITECTURE.md | Create after Plan phase when technical decisions are made |

**LEARNING-LOG.md stub template:**
```markdown
# Learning Log

**Project:** [Name]
**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> When lesson becomes pattern: Add to methods doc, mark "Graduated to §X.Y"

---

Record lessons learned during this project. Add entries when:
- Something unexpected happens (good or bad)
- A workaround is discovered
- A decision proves right/wrong
- A pattern emerges worth remembering

## Entries

<!-- Add entries below as lessons emerge during implementation -->
```

### 7.8.4 Minimal Viable Initialization (Expedited Mode)

1. SESSION-STATE.md (current position)
2. PROJECT-MEMORY.md (empty Phase Gates table)
3. LEARNING-LOG.md (stub with usage header)

### 7.8.5 Cross-Reference Index

| Topic | Section |
|-------|---------|
| Mode selection | §1.3 |
| Session state format | §7.1 |
| Project memory format | §7.2 |
| Learning log timing | §7.3.2 |
| Loader template | §7.4.3 |
| Source documents | §7.5 |

---

# TITLE 8: COLLABORATION PROTOCOLS

**Importance: 🟡 IMPORTANT — Maintains human authority**

**Implements:** Human-AI Collaboration (Domain), Workflow Integrity (Domain)  
**Applies to:** All human-AI interactions

## Part 8.1: Escalation Triggers

### 8.1.1 Purpose

Define conditions that require human decision-making. Prevents both automation bias (over-trusting AI) and decision paralysis (over-escalating).

### 8.1.2 Mandatory Escalation

**Always escalate when:**

| Trigger | Rationale |
|---------|-----------|
| Scope change | Human owns scope decisions |
| Architecture change | Significant downstream impact |
| Security concern | Risk requires human judgment |
| Principle conflict | Framework governance issue |
| Resource constraint | Business decision |
| External dependency issue | May require business action |
| Ambiguous requirement | Specification authority is human |

### 8.1.3 Judgment Escalation

**Consider escalating when:**

| Trigger | Guidance |
|---------|----------|
| Multiple valid approaches | Present options if significant |
| Trade-off decision | Human may have preferences |
| Edge case interpretation | Specification may not cover |
| Risk/speed trade-off | Business judgment |

### 8.1.4 Non-Escalation

**Do NOT escalate for:**
- Routine implementation decisions
- Standard pattern selection
- Minor code style choices
- Obvious best practices

AI should make reasonable decisions within established patterns without constant escalation.

---

## Part 8.2: Decision Presentation

### 8.2.1 Purpose

When escalating, present decisions in format that enables informed human choice.

### 8.2.2 Decision Presentation Format

```
DECISION REQUIRED
─────────────────
Context: [What situation requires decision]
Options:
  A. [Option description]
     - Pros: [Benefits]
     - Cons: [Drawbacks]
     - Implications: [Downstream effects]
  
  B. [Option description]
     - Pros: [Benefits]
     - Cons: [Drawbacks]
     - Implications: [Downstream effects]

Recommendation: [If AI has one, with rationale]
Information Needed: [What would help decide]
Urgency: [How time-sensitive]
```

### 8.2.3 Presenting Uncertainty

Be explicit about confidence:

- "I am confident that..." (high certainty)
- "I believe..." (moderate certainty)
- "I'm uncertain, but..." (low certainty)
- "I don't know..." (no basis for judgment)

### 8.2.4 After Decision

Document decisions in state file:
- What was decided
- Why (rationale)
- Who decided (PO or AI)
- When

---

## Part 8.3: Solo Developer Mode

### 8.3.1 Purpose

Optimize collaboration for single-person projects where one human serves all roles.

### 8.3.2 Solo Mode Adjustments

**Reduced ceremony:**
- Abbreviated decision presentations
- Combined approval gates
- Informal state updates

**Maintained rigor:**
- All validation gates still apply
- All quality thresholds unchanged
- All escalation triggers still active

### 8.3.3 Solo Mode Triggers

Enter Solo Developer Mode when:
- Explicitly configured in project
- Single human is Product Owner AND implementer
- Project scale is appropriate (small to medium)

### 8.3.4 Solo Mode Workflow

```
Standard: Specify → [PO Approval] → Plan → [PO Approval] → Tasks → [PO Approval] → Implement → [PO Approval]

Solo:     Specify → Plan → [Combined Approval] → Tasks → Implement → [Final Approval]
```

Gates are combined but not eliminated.

---

# TITLE 9: DEPLOYMENT & DISTRIBUTION

**Importance: 🟡 IMPORTANT — Load when deploying or distributing**

**Implements:** Domain Principle "Security by Default" (coding-quality-security-by-default), Meta Principle "Risk Mitigation by Design" (meta-governance-risk-mitigation-by-design)

---

## Part 9.1: Pre-Flight Validation

### 9.1.1 Purpose

Validate configuration and external references at system startup, failing fast with actionable error messages rather than failing silently mid-execution.

### 9.1.2 The Pattern

**Problem:** Config-driven systems that silently accept invalid configurations cause hard-to-debug runtime failures.

**Solution:** Validate all external references before expensive operations:

```python
def validate_config_at_startup():
    """Call this BEFORE any processing begins."""
    errors = []

    # Check all file references
    for ref in config.file_references:
        if not ref.path.exists():
            errors.append(f"Missing file: {ref.path}")

    # Check all external dependencies
    for dep in config.external_deps:
        if not dep.is_available():
            errors.append(f"Unavailable: {dep.name}")

    # Report ALL errors at once, not just first
    if errors:
        raise ConfigurationError(
            "Configuration validation failed:\n" +
            "\n".join(f"  - {e}" for e in errors) +
            "\n\nCheck your configuration file."
        )
```

### 9.1.3 Key Principles

| Principle | Rationale |
|-----------|-----------|
| **Fail fast** | Discover problems before expensive operations |
| **Report all errors** | Don't make user fix one error at a time |
| **Actionable messages** | Include what to check and how to fix |
| **Validate at boundaries** | Check config on load, not during use |

### 9.1.4 Common Validation Points

| What | When | How |
|------|------|-----|
| File references | Startup | Check existence |
| Environment variables | Startup | Check required vars set |
| API endpoints | First use | Health check or timeout |
| Database connections | Startup | Connection test |
| External service configs | Startup | Validate schema |

### 9.1.5 Anti-Pattern

❌ **Don't do this:**
```python
def process_item(item):
    config = load_config()  # Loads each time
    if not config.valid:    # Fails mid-batch
        raise Error(...)    # After partial work done
```

✅ **Do this:**
```python
def main():
    validate_config()       # Fails immediately
    for item in items:
        process_item(item)  # Config known-good
```

---

## Part 9.2: Docker Distribution

### 9.2.1 Purpose

Package applications for distribution to users who may not have development environments configured.

### 9.2.2 Multi-Stage Build Pattern

**When to use:** Applications with build-time dependencies (compilers, ML model downloads) that aren't needed at runtime.

```dockerfile
# Stage 1: BUILDER — Heavy dependencies, build artifacts
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build dependencies (gcc, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Build your artifacts
COPY . .
RUN pip install . && python -m build_index

# Stage 2: RUNTIME — Minimal image
FROM python:3.11-slim AS runtime
WORKDIR /app

# Copy only what's needed from builder
COPY --from=builder /app/dist/ ./dist/
COPY --from=builder /app/index/ ./index/

# Non-root user for security
RUN useradd --create-home appuser
USER appuser

CMD ["python", "-m", "your_app"]
```

### 9.2.3 Security Hardening

| Practice | Implementation | Rationale |
|----------|---------------|-----------|
| **Non-root user** | `USER appuser` | Limit container privileges |
| **Minimal base** | `python:3.11-slim` | Smaller attack surface |
| **No secrets in image** | Use env vars at runtime | Secrets shouldn't be baked in |
| **Health checks** | `HEALTHCHECK` instruction | Orchestration monitoring |
| **Read-only where possible** | `:ro` volume mounts | Prevent container writes |

### 9.2.4 ML-Specific Optimizations

**CPU-Only PyTorch** (saves ~1.8GB):
```dockerfile
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Pre-built Indexes:**
- Build embeddings/indexes in builder stage
- Copy pre-built artifacts to runtime stage
- Avoids model downloads at container start

### 9.2.5 CI/CD Integration

```yaml
# Trigger on version tags
on:
  push:
    tags:
      - 'v*.*.*'

# Build and publish
- uses: docker/build-push-action@v5
  with:
    push: true
    tags: |
      ${{ env.IMAGE }}:${{ env.VERSION }}
      ${{ env.IMAGE }}:latest
```

### 9.2.6 .dockerignore Best Practices

```dockerignore
# Development files
.git
.venv
__pycache__
*.pyc
tests/
.pytest_cache/

# Documentation (unless needed by build)
*.md
!README.md  # Keep if pyproject.toml references it

# IDE
.vscode/
.idea/
```

---

## Part 9.3: MCP Server Development

### 9.3.1 Purpose

Patterns specific to developing Model Context Protocol (MCP) servers for AI client integration.

### 9.3.2 MCP Architecture Constraints

| Constraint | Implication |
|------------|-------------|
| **stdio transport** | stdout is reserved for JSON-RPC; all logging → stderr |
| **Synchronous I/O** | Can't gracefully cancel; use os._exit() for shutdown |
| **Per-process lifecycle** | Server starts when AI client connects, exits when disconnected |
| **No persistent state** | Each connection is fresh; state via index files |

### 9.3.3 stdout/stderr Discipline

**Critical:** MCP uses stdout for JSON-RPC communication. Any non-JSON output breaks the protocol.

```python
import sys
import logging

# Configure logging to stderr ONLY
logging.basicConfig(
    stream=sys.stderr,  # NOT stdout
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# Never use print() without explicit file=
print("Debug info", file=sys.stderr)  # OK
print("Debug info")  # BREAKS MCP PROTOCOL
```

### 9.3.4 Graceful Shutdown Pattern

**Problem:** stdio transport blocks on synchronous reads; asyncio cancellation doesn't work.

**Solution:** Use os._exit() for immediate termination:

```python
import signal
import os

def handle_signal(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    logging.info("Shutdown signal received")
    os._exit(0)  # Immediate exit

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

async def main():
    try:
        await server.run()
    finally:
        # Also exit when pipes close (client disconnected)
        os._exit(0)
```

### 9.3.5 Server Instructions Pattern

**Purpose:** Provide behavioral guidance to AI clients at connection time.

```python
server = FastMCP(
    name="your-server",
    instructions="""
## Required Actions
- Call `your_tool()` before governed actions
- Cite results when they influence your approach

## Forbidden Actions
- Do NOT proceed without checking first
- Do NOT ignore ESCALATE responses

## Tool Summary
| Tool | Purpose |
|------|---------|
| your_tool | Brief description |
"""
)
```

**Key principles:**
- Use constraint-based framing ("Required", "Forbidden")
- Include quick-reference tables
- Keep under 500 tokens for context efficiency

### 9.3.6 Per-Response Reminders

**Problem:** Server instructions load once at connection; AI may drift over long conversations.

**Solution:** Append compact reminder to every tool response:

```python
REMINDER = "\n\n---\n⚖️ **Reminder:** Query governance on decisions. Cite principles."

def append_reminder(response: dict) -> dict:
    """Append governance reminder to tool response."""
    if "content" in response:
        response["content"] += REMINDER
    return response
```

**Reminder guidelines:**
- Keep under 50 tokens
- Focus on most critical behaviors
- Use symbols for visual distinction

### 9.3.7 Docker for MCP Servers

**Key considerations:**
- Must run with `-i` flag (interactive for stdin)
- Include `stdin_open: true` in docker-compose
- Health check should import module, not start server:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "from your_module import server; print('OK')"
```

### 9.3.8 Multi-Platform Configuration

When supporting multiple AI platforms, use a config generator:

```python
def generate_config(platform: str) -> dict:
    """Generate platform-specific MCP configuration."""
    base = {
        "command": "python",
        "args": ["-m", "your_module.server"]
    }

    if platform == "gemini":
        base["timeout"] = 30000  # Gemini-specific

    return {"mcpServers": {"your-server": base}}
```

**Supported platforms (2026):**
- Claude Code CLI, Claude Desktop
- Gemini CLI
- ChatGPT Desktop (Developer Mode)
- Cursor, Windsurf
- Others via MCP SuperAssistant browser extension

---

# APPENDICES

**Importance: 🟢 OPTIONAL — Reference material, load on demand**

## Appendix A: Claude Code CLI Configuration

**Importance: 🟢 OPTIONAL — Only when using Claude Code CLI**

### A.1 CLAUDE.md Template

```markdown
# Project: [Name]

## Governance
- Framework: AI Coding Domain Principles v2.2.1
- Mode: [Expedited/Standard/Enhanced]

## Current State
- Phase: [Current phase]
- Task: [Current task]
- Updated: [Timestamp]

## Project Context
[Brief project description]

## Active Decisions
[Key decisions affecting current work]

## Constraints
[Technical, business, or other constraints]

## Next Actions
[What to do next]
```

### A.2 Session Start Commands

```bash
# Load session state
cat SESSION-STATE.md

# Review project memory if needed
cat PROJECT-MEMORY.md

# Check learning log if relevant
cat LEARNING-LOG.md

# Check recent changes
git log --oneline -10
```

### A.3 Session End Commands

```bash
# Update memory files before ending
# [Update SESSION-STATE.md with current position]
# [Update PROJECT-MEMORY.md if decisions were made]
# [Update LEARNING-LOG.md if insights emerged]

# Commit state
git add SESSION-STATE.md PROJECT-MEMORY.md LEARNING-LOG.md
git commit -m "Session state update: [summary]"
```

---

## Appendix B: Memory File Templates

**Importance: 🟡 IMPORTANT — Reference when creating memory files**

### B.1 Minimal State (EXPEDITED Mode)

```markdown
# State

Phase: [Phase]
Task: [Task]
Next: [Next action]
Updated: [Timestamp]
```

### B.2 Standard State

```markdown
# Project State

## Status
- Phase: [Phase]
- Mode: Standard
- Updated: [Timestamp]

## Progress
[Checklist of completed items]

## Current Focus
[Active work]

## Decisions
[Key decisions]

## Next Session
[Continuation guidance]
```

### B.3 Enhanced State

```markdown
# Project State

## Status
- Phase: [Phase]
- Mode: Enhanced
- Milestone: [Current milestone]
- Updated: [Timestamp]

## Progress
[Detailed checklist]

## Learning Log
[What we've learned]

## Decisions
[Detailed decision record]

## Risks & Issues
[Active risks and issues]

## Iteration Status
[Current iteration and adjustments]

## Next Session
[Detailed continuation guidance]
```

---

## Appendix C: Checklist Quick Reference

**Importance: 🔴 CRITICAL — May be the most frequently used section**

### C.1 Specification Completeness (§2.3)

- [ ] Problem statement clear
- [ ] Target users identified
- [ ] Core features listed (≤7)
- [ ] Acceptance criteria defined
- [ ] Out of scope documented
- [ ] Product Owner approved

### C.2 Architecture Validation (§3.2.4)

- [ ] Technology stack selected
- [ ] System structure defined
- [ ] Security addressed
- [ ] Risks identified
- [ ] Product Owner approved

### C.3 Task Validation (§4.2)

- [ ] All tasks ≤15 files
- [ ] All tasks testable
- [ ] Dependencies explicit
- [ ] Full coverage verified
- [ ] Product Owner approved

### C.4 Implementation Quality (§5.1.3)

- [ ] Tests written with code
- [ ] Coverage ≥80%
- [ ] Security scan clean
- [ ] Dependencies verified
- [ ] Acceptance criteria met

---

## Appendix D: Gemini CLI Configuration

**Importance: 🟢 OPTIONAL — Only when using Gemini CLI**

### D.1 Overview

Gemini CLI uses `GEMINI.md` files for project context (analogous to Claude's `CLAUDE.md`). Key differences:
- Hierarchical context loading (global → project → subdirectory)
- Built-in `/memory` commands for context management
- MCP server support for extensions
- Checkpointing for rollback capability

### D.2 GEMINI.md Template (Framework-Aligned)

Create `GEMINI.md` in project root:

```markdown
# Project: [Name]

## Governance
Follow AI Coding Methods framework:
- Load SESSION-STATE.md for current position
- Load PROJECT-MEMORY.md for decisions and architecture
- Reference LEARNING-LOG.md when similar situations arise

## Framework Principles
When coding, apply these Domain Principles:
- Specification Completeness: Ensure requirements are complete before implementation
- Atomic Task Decomposition: Keep changes to ≤15 files per task
- Testing Integration: Write tests alongside code
- Security-First: Zero HIGH/CRITICAL vulnerabilities
- Supply Chain Integrity: Verify all dependencies before use

## Project Context
[Brief project description]

## Technical Stack
[Technologies in use]

## Coding Standards
[Project-specific standards]

## Key Commands
- Build: [command]
- Test: [command]
- Lint: [command]
```

### D.3 Memory File Integration

Gemini CLI can import other markdown files using `@path/to/file.md` syntax:

```markdown
# GEMINI.md

## Current State
@./SESSION-STATE.md

## Project Decisions
@./PROJECT-MEMORY.md

## Lessons Learned
@./LEARNING-LOG.md
```

### D.4 Session Commands

```bash
# Check loaded context
/memory show

# Reload context files after changes
/memory refresh

# List available checkpoints (for rollback)
/restore list

# Restore to checkpoint if needed
/restore <checkpoint_id>
```

### D.5 Framework Compliance Notes

- Gemini CLI's `/memory` system provides similar functionality to our Memory Architecture
- Use same memory file structure (SESSION-STATE.md, PROJECT-MEMORY.md, LEARNING-LOG.md)
- Gemini's checkpointing provides additional safety for implementation phase
- MCP server support enables similar extensibility to Claude Code

---

## Appendix E: Claude App & Chrome Extension

**Importance: 🟢 OPTIONAL — For web-based and browser-assisted workflows**

### E.1 Overview

Claude is available through multiple interfaces:
- **Claude.ai (Web/App)**: Chat interface with Projects feature
- **Claude in Chrome**: Browser extension for web automation
- **Claude Code (Web)**: Browser-based coding at claude.com/code

Each interface has different context management approaches.

### E.2 Claude.ai Projects Configuration

Claude Projects provide persistent context through:
- Project Instructions (system-level guidance)
- Project Knowledge (uploaded documents)
- Project Files (reference materials)

**Framework Integration:**

In Project Instructions, add:
```
Follow the AI Coding Methods framework:
1. At session start, review uploaded memory files
2. Apply the 4-phase workflow: Specify → Plan → Tasks → Implement
3. Use validation gates between phases
4. Maintain memory files as specified in framework

When user says "framework check", confirm:
- Current phase
- Active task
- Memory file status
```

Upload to Project Knowledge:
- ai-coding-methods.md (this document)
- ai-coding-domain-principles.md
- Current PROJECT-MEMORY.md
- Current LEARNING-LOG.md

### E.3 Claude in Chrome Integration

Claude in Chrome works alongside Claude Code for build-test-verify workflow:

```
Build (Claude Code CLI) → Test (Chrome Extension) → Debug (Both)
```

**Key Capabilities:**
- Read console errors and DOM state
- Navigate and interact with web apps
- Verify UI against specifications
- Record workflows for repetition

**Framework Application:**
- Use during Implementation phase for testing
- Verify visual design specs (ENHANCED mode)
- Validate user flows against specification
- Debug issues with live browser context

### E.4 Claude Code Web (claude.com/code)

Browser-based Claude Code for:
- GitHub repository integration
- Parallel task execution
- Session transfer to local CLI

**Framework Considerations:**
- Memory files stored in repository (GitHub-synced)
- Same workflow applies as CLI
- Can transfer session context to local CLI for continuation

### E.5 Cross-Interface Workflow

When switching between interfaces:

1. **Always update SESSION-STATE.md** before switching
2. **Sync memory files** to accessible location (repository, project knowledge)
3. **Brief new interface** on current state and next actions
4. **Verify understanding** before continuing work

**Example Handoff (CLI → Web):**
```markdown
## Handoff: CLI → Claude.ai
Moving to web interface for [reason]

Current State:
- Phase: Implement
- Task: User authentication
- Next: Complete login form validation

Files to upload to Project Knowledge:
- SESSION-STATE.md (current)
- PROJECT-MEMORY.md
- Relevant source files
```

---

## Appendix F: Tool Comparison Quick Reference

**Importance: 🟢 OPTIONAL — Reference when choosing tools**

| Feature | Claude Code CLI | Gemini CLI | Claude.ai | Claude Chrome |
|---------|-----------------|------------|-----------|---------------|
| **Context File** | CLAUDE.md | GEMINI.md | Project Instructions | N/A |
| **Memory Import** | Manual | @file.md syntax | Upload to Knowledge | N/A |
| **Session State** | SESSION-STATE.md | Same + /memory | Conversation history | Task-based |
| **Checkpointing** | Git-based | Built-in /restore | N/A | N/A |
| **MCP Support** | Yes | Yes | Limited | N/A |
| **Browser Integration** | /chrome command | /ide (VS Code) | Connector | Native |
| **Best For** | Complex backend, multi-file | Large context (1M tokens), Google ecosystem | Planning, documentation | Testing, verification |

**Framework Compatibility:** All tools can implement the AI Coding Methods framework using their respective context management features. The memory file structure (SESSION-STATE.md, PROJECT-MEMORY.md, LEARNING-LOG.md) works across all tools.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.5.0 | 2026-01-18 | **Memory Hygiene & Cognitive Headers:** (1) Added standardized cognitive type headers to all memory file templates (§7.1.2, §7.2.2, §7.3.3) with Memory Type, Lifecycle, and purpose guidance. (2) Added §7.0.4 distillation triggers (size thresholds for pruning). (3) Added §7.6.1 step 5: memory hygiene check to session end procedure. (4) Updated all Cold Start Kit minimal templates with headers. (5) Updated §7.8.3 initialization stub. Headers improve RAG chunking and provide clear lifecycle guidance per context engineering best practices. |
| 2.4.0 | 2026-01-18 | Added §7.8 Project Initialization Protocol, §7.5 Source Document Registry, §5.2.5 ML Model Mocking Pattern. Added Metrics Registry System with regression tests. |
| 2.3.0 | 2026-01-03 | Added Title 9: Deployment & Distribution. (1) §9.1 Pre-Flight Validation: fail-fast config validation pattern, actionable error reporting, validation points table. (2) §9.2 Docker Distribution: multi-stage build pattern, security hardening, ML optimizations (CPU-only PyTorch), CI/CD integration, .dockerignore best practices. (3) §9.3 MCP Server Development: stdio/stderr discipline, graceful shutdown with os._exit(), server instructions pattern, per-response reminders, multi-platform configuration. Derived from ai-governance-mcp production patterns. |
| 2.2.0 | 2026-01-02 | Added §5.2.5 Test Organization Patterns: test file structure (unit vs integration separation), fixture categories (path, model, state reset, mock), test markers for selective execution, standard edge cases checklist, response parsing helper pattern, parameterization guidance, mocking strategy by layer. Derived from production test suite patterns (ai-governance-mcp: 271 tests, 90% coverage). |
| 2.1.0 | 2025-12-31 | (1) Integrated Active Tasks table into main SESSION-STATE template (§7.1.2) with research rationale (§7.1.3). (2) Added Known Gotchas section to PROJECT-MEMORY template (§7.2.2). (3) Simplified Phase Gates table (removed Approver column, now optional for team projects). (4) Fixed loader template version reference. (5) Clarified Handoff Summary From/To fields. Based on 2025 AI agent memory architecture research (AIS, Zep, MongoDB patterns). |
| 2.0.0 | 2025-12-31 | **BREAKING:** Major memory architecture revision. (1) Aligned memory files to cognitive types (Working, Semantic, Episodic, Procedural). (2) Eliminated separate gate artifact files (GATE-*.md) — gates now recorded inline in PROJECT-MEMORY.md. (3) Added Project Instructions File concept (loader document) formalizing CLAUDE.md as progressive disclosure pointer. (4) Added task tracking for solo mode in SESSION-STATE.md. (5) Added principles-based pruning guidance. (6) Added LEARNING-LOG creation timing and graduation to procedural memory. Based on industry research: CoALA framework, ADR patterns, Anthropic best practices, Mem0 memory architecture. |
| 1.1.1 | 2025-12-29 | PATCH: Updated Document Governance version reference from v2.1 to v2.2. |
| 1.1.0 | 2025-12-27 | Added Part 6.4: Automated Validation (CI/CD) covering CI pipeline setup, GitHub Actions templates, security scanning integration, and best practices. Updated situation index with CI/CD reference. |
| 1.0.3 | 2025-12-20 | Added Cold Start Kit (copy-paste prompts, minimal templates, mode decision tree). Added Gate Artifacts (structured documents for phase transitions). Added Measurement Guidance for tool-neutral metrics. Fixed mode decision tree inconsistency (one canonical format). Added gate failure pathway. Addresses Perplexity review feedback. |
| 1.0.2 | 2025-12-20 | Added Appendix D (Gemini CLI), Appendix E (Claude App/Chrome Extension), Appendix F (Tool Comparison). Multi-tool support for framework. |
| 1.0.1 | 2025-12-20 | Added Memory Architecture (Title 7 expansion), Situation Index, importance tags, partial loading strategy. Fixed principle references to use names instead of codes. |
| 1.0.0 | 2025-12-20 | Initial release. 4-phase workflow with adaptive depth. Derived from 7-phase framework and 2025 industry best practices. |

---

## Document Governance

**Authority:** This document implements ai-coding-domain-principles.md (v2.2.1). Methods cannot contradict principles.

**Updates:** Methods may be updated independently of principles. Version increments indicate significant procedural changes.

**Feedback:** Document gaps, conflicts, or improvement suggestions to be captured and addressed in next version.

**Relationship to Tools:** Tool-specific appendices may be added without changing core methods. Each appendix must comply with methods defined herein.

---

### v2.5.0.1 (2026-02-01)
- Replaced "significant action" with skip-list model per v1.7.0 operational change
