---
title: Execution Framework
version: v1.1.0
type: Permanent blueprint — system architecture reference
memory_type: Architectural
started: 2026-04-29 (session-139)
last_updated: 2026-05-03 (session-145)
status: Blueprint — permanent reference. v0.1-draft bucket layer pending further empirical validation.
trigger: External article — Akshay Pachaar, "The Anatomy of an Agent Harness" (April 2026)
---

# Execution Framework

> **What this document is.** The system architecture blueprint for ai-governance. Maps every project component to a computer architecture analog, assessing modularization readiness and identifying gaps. The primary metaphor — ai-governance as a custom computer with swappable components — serves a practical purpose: evaluate "is there a better component available for this slot?"
>
> **How to read it.** Sections 1-9 are the permanent reference (root view, component model, analogies, system map, interface assessment, memory contracts, context retention, portability, gap analysis). Sections 10-11 track live decision state. Section 12 preserves the full design history — contrarian rounds, coaching questions, dead-ends, and open discussions — so any future reader can reconstruct the reasoning behind every decision. Sections 13-15 are reference material.
>
> **Pickup discipline.** A future reader (human or AI) opening this file cold should be able to resume exactly where the conversation left off. If you find yourself unable to do that, the file has lost necessary context and should be enriched, not compressed. Per session-140 user direction: do not summarize or compress this file's content during routine SESSION-STATE updates — the nuance is the point.
>
> **Bucket layer is v0.1-draft.** Treat it as such — propose changes, flag conflations, surface gaps. The root view was extended from 3-function to 4-function (Authority added) in the 2026-05-03 fresh-eyes analysis. The 8-bucket component layer remains v0.1-draft pending further empirical instantiation beyond the first skill.

---

## 1. Root View — 4-Function Architecture

The 12 production-harness components identified by Pachaar (2026) are **operational composites** of underlying root functions. Grouping the article's 12 by underlying *function* produces a root layer one level of abstraction ABOVE the component view, so the framework doesn't anchor to any single vendor's component count.

| Root Function | What It Governs | Article Components It Groups | ai-governance Principles | Computer Analog |
|---|---|---|---|---|
| **Information Flow** | How data moves and persists | Tools, Memory, Context Mgmt, Prompt Construction, Output Parsing, State Mgmt | `meta-core-informational-readiness`, `meta-method-single-source-of-truth`, `meta-quality-explicit-over-implicit`, `coding-context-context-window-management`, `coding-context-session-state-continuity` | Data bus, memory subsystem |
| **Control Flow** | What happens next | Orchestration Loop, Subagent Orchestration, Lifecycle Mgmt | `coding-process-discovery-before-commitment`, `coding-process-goal-first-dependency-mapping`, `coding-process-atomic-task-decomposition`, `multi-architecture-orchestration-pattern-selection`, `multi-coordination-state-persistence-protocol` | CPU scheduler, process management |
| **Quality Gates** | Catching problems | Error Handling, Guardrails & Safety, Verification Loops | `meta-quality-verification-validation`, `meta-operational-failure-recovery-resilience`, `meta-quality-visible-reasoning-traceability`, `meta-safety-non-maleficence-privacy-security` (S-Series), `coding-quality-validation-gates`, `multi-quality-fault-tolerance-and-graceful-degradation` | Error checking, watchdog, test fixtures |
| **Authority** | Who can do what | Permission systems, hierarchy resolution, adoption/activation, S-Series veto | `meta-safety-non-maleficence-privacy-security` (S-Series), `meta-governance-human-ai-authority`, `meta-governance-reserved-powers-unenumerated-rights` | Privilege rings, MMU, access control |

**Why Authority is distinct from Quality Gates:** Quality Gates check *correctness* ("is this output right?"). Authority checks *permission* ("is this actor allowed to do this?"). A correct action by an unauthorized actor should still be blocked. A privileged actor making an incorrect choice should be caught by Quality Gates. They're independent dimensions. Per `meta-core-systemic-thinking`: conflating them hides the answer to both. In computer architecture, this is the **privilege ring model** (ring 0 = kernel, ring 3 = user) or the **MMU** (memory management unit). The governance framework has a clear authority hierarchy (Bill of Rights > Constitution > Statutes > ...) that functions exactly like privilege rings.

### 1.1 Mapping between root view and component view

Both views co-exist and serve different decisions. Per `meta-method-single-source-of-truth`: each view has a distinct purpose; using the wrong view for a question produces noise.

| View | Best used for | Question it answers |
|---|---|---|
| **4-function root view** (Information Flow / Control Flow / Quality Gates / Authority) | Design coherence at architectural level. Auditing whether a subsystem covers all needed functional dimensions. Explaining the framework to a new adopter at high abstraction. Determining if a proposed new principle/method/feature fits an existing function or surfaces a gap. | *"Are we covering all the necessary functional dimensions?"* |
| **8-bucket component view** (Inference Engine, Memory, Retrieval, Action Layer, Orchestration, Verification & Quality, Governance Policy, Lifecycle) | Component-level swap and improvement decisions. Comparing implementations across systems. Mapping our framework to other frameworks. Identifying which areas have gaps vs solid coverage. | *"Which specific components do we have, and is there a better one available for this slot?"* |

| Root Function (4) | Component Buckets |
|---|---|
| Information Flow | Memory + Retrieval + Action Layer (Buckets 2, 3, 4) |
| Control Flow | Orchestration + Lifecycle (Buckets 5, 8) |
| Quality Gates | Verification & Quality (Bucket 6) |
| Authority | Cross-cutting — operates on Buckets 6 and 7 jointly; S-Series veto cross-cuts all |
| (Substrate) | Inference Engine (Bucket 1) — substrate, not a function we orchestrate |
| (Container) | Governance Policy (Bucket 7) — defines what Authority enforces and Quality Gates verify |

When to switch between views:
- Start a design conversation with the **root view** to ensure all dimensions are covered conceptually
- Move to the **8-bucket view** when comparing implementations, evaluating swaps, or auditing component-level coverage
- The root view answers *what must be true*; the bucket view answers *what specifically does it*

**Evolution:** Extended from 3-function (Information Flow / Control Flow / Quality Gates) to 4-function on 2026-05-03. The 3-function candidate was held across all session-140 bucket-layer iteration rounds as "not locked" (user note). The 4th function was identified during fresh-eyes analysis when reviewing the permission model — S-Series veto, hook permissions, constitutional hierarchy don't fit Quality Gates (they check permission, not correctness). See §12.7 for the full analysis context.

---

## 2. Component View — 8-Bucket Model (v0.1-draft)

### 2.1 What v0.1-draft means

This is the **first complete pass** of the bucket model. We've identified buckets, sub-buckets, and resolved several conflations + the Bucket 6/7 collapse question. The model is **NOT** considered finalized; it should be **empirically tested** as more workflows/skills are designed. Continuing to abstract-reason about buckets without real instantiation is forward-continuation bias dressed as rigor (per session-140 contrarian round 3 finding).

**Naming convention:** each bucket has a **canonical name** (preferred going forward) and a **legacy name** (used in earlier prose). Move toward canonical naming as content stabilizes.

### 2.2 The 8 buckets

#### Bucket 1: Inference Engine *(canonical)* / Compute *(legacy — equivalent to "the LLM")*

The processor doing the actual reasoning. Not built by us — provided by Claude Code or whichever host harness runs us.

| Sub-bucket (generic method level) | What it is | Component swap question |
|---|---|---|
| Model selection | Choosing which model to use for a task | Opus 4.7 → Opus 5? Per-task right-sizing? |
| Inference parameters | Temperature, max tokens, thinking mode | Tunable per task? |
| Reasoning configuration | Plan-mode vs ReAct, plus-thinking | Host harness primarily decides |
| **Substrate-level safety/quality** | Built-in alignment + RLHF + safety classifiers (analogous to ECC RAM, hardware-level security) | Different model = different substrate-level quality (see §8.2 Hardware-vs-Software dimension) |

**Why surface this even though we don't own it:** swapping the model can change what scaffolding we still need (article's co-evolution insight — harness should thin as model improves).

**Caveat previously withdrawn (session-140):** Bucket 1 is a peer bucket. The principle/method/appendix mapping applies (principle: "match model capability to task stakes"; method: "right-size by task type"; appendix: "Opus for D2+ in Claude Code").

#### Bucket 2: Memory *(canonical, kept)*

Persistent and transient state. Already mapped via CoALA in `PROJECT-MEMORY.md` ADR-5.

| Sub-bucket (generic method level) | What it is | ai-governance specific (appendix-level) | RAM-vs-disk failure mode |
|---|---|---|---|
| Working memory | Current task state | `SESSION-STATE.md` | Storing decisions here → lost when pruned |
| Semantic memory | Decisions & constraints | `PROJECT-MEMORY.md` | Storing transient context here → bloat |
| Episodic memory | Lessons from past failures | `LEARNING-LOG.md` | Storing decisions here → mixes "what we believe" with "what we learned" |
| Procedural memory | How-to patterns | `workflows/*` | Storing principles here → conflates rules with procedures |
| Prospective memory | Future intentions | `BACKLOG.md` | Storing decisions here → intentions and decisions get confused |
| Operational memory | Recurring commitments | `OPERATIONS.md` | Storing projects here → confuses discrete work with ongoing monitoring |
| Reference memory | External knowledge | `reference-library/` | Treating as authoritative when it's secondary authority |

Component-level questions: Are markdown files the right format? Should `LEARNING-LOG.md` be append-only structured data so we can analyze patterns? Should `reference-library/` move to a vector index?

**Sub-bucket abstraction status:** clean — these ARE generic methods (CoALA framework is generic, not ai-governance-specific). Extended from 6 to 7 types with Operational memory (OPERATIONS.md, 2026-05-03).

#### Bucket 3: Retrieval *(canonical, kept)*

How memory becomes context. The motherboard pathways. **Sub-bucket abstraction needs sharpening — current list mixes mechanism-level and policy-level methods (contrarian found, session-140 round 3).**

| Sub-bucket (mechanism-level — generic) | What it is | Current implementation |
|---|---|---|
| Semantic retrieval | Vector similarity over corpus | Context Engine MCP server (`query_project`, BGE-small-en-v1.5, 384d) |
| Lexical retrieval | Exact text match | grep, glob, ripgrep |
| Direct read | Known-path access | Read tool, file open by path |

| Sub-bucket (policy-level — when to retrieve) | What it is | Current implementation |
|---|---|---|
| Always-on context | Auto-loaded at every turn | CLAUDE.md, AGENTS.md, system reminders |
| Selective load | Loaded on demand | Memory files read by session-start protocol |

**Open question:** should mechanism-level and policy-level be split into Bucket 3a / 3b, or kept as parallel sub-bucket lists within Bucket 3? Defer until further empirical testing.

Component-level questions: Is BGE-small-en-v1.5 still right (BACKLOG #16)? Is 512-token chunking optimal? Should we add reranking?

#### Bucket 4: Action Layer *(canonical)* / Tools *(legacy)*

How the system affects the world. I/O — both inbound (sensors) and outbound (effectors). **Sub-bucket abstraction REVISED (session-140 round 3) — old list ("Governance tools / Retrieval tools / File operations") was content-level, not method-level.**

| Sub-bucket (generic method level) | What it is | ai-governance specific (appendix-level) |
|---|---|---|
| Tool schema definition | Define what a tool does and what it accepts | MCP tool definitions in server.py |
| Tool registration | Make tools discoverable to the host | MCP server protocol registration |
| Argument validation | Check inputs before execution | Pydantic models, JSON schema validation |
| Sandboxed execution | Run tools without compromising the system | Host harness sandbox; permission system |
| Result formatting | Structure outputs for the model to consume | TextContent, structured tool results |
| Tool authorization | Decide which tools are allowed when | `install_agent` gating, hooks |

Component-level questions: Which tools should be `install_agent`-gated rather than always-available? Should we expose more analysis tools (BACKLOG #42 Feedback Loop Analysis Tool)?

#### Bucket 5: Orchestration *(canonical)* / Control Flow *(legacy)*

What happens next. The CPU scheduler equivalent. **Sub-bucket abstraction needs sharpening — current list mixes pattern-level, mechanism-level, and scope-level (contrarian found, session-140 round 3).**

| Sub-bucket (control-pattern level) | What it is | Current implementation |
|---|---|---|
| Reactive loop | Input → decide → act → observe → repeat | Host harness ReAct cycle |
| Planned execution | Plan-then-execute | Plan Mode (D2+ tasks) |

| Sub-bucket (mechanism level) | What it is | Current implementation |
|---|---|---|
| Triggered handlers | Event-driven actions | 8 hooks (PreToolUse, PrePush, etc.) |
| Subagent delegation | Hand off to specialist | Task tool with subagent definitions |

| Sub-bucket (scope level) | What it is | Current implementation |
|---|---|---|
| Multi-agent coordination | Sequential / parallel / handoff patterns across agents | `multi-architecture-orchestration-pattern-selection` |

**Open question:** should these three layers be split into Bucket 5a/5b/5c? Defer until further empirical testing. Mild signal from compliance-review skill: the skill acts as both "orchestration" (sequencing 12 checks) and "application program" (user-invokable workflow) — a future sub-bucket split between orchestration mechanisms and application programs may be warranted as more skills are created.

#### Bucket 6: Verification & Quality *(canonical)* / Quality Gates *(legacy)*

Catching problems and verifying correctness. **Stays SEPARATE from Bucket 7** per `constitution.md:120-133`: enforcement is cross-cutting, not OS-internal. Enforcement answers "how is the rule made sticky?" while Bucket 7 answers "what is the rule?" — different questions, different buckets.

| Sub-bucket (generic method level) | What it is | Current implementation |
|---|---|---|
| Pre-action gates | Block before damage | 8 hard-mode hooks (PreToolUse blocking, etc.) |
| Post-action verification | Catch errors after | Subagent battery (validator, contrarian-reviewer, coherence-auditor) |
| Hard stops | Absolute veto | S-Series ESCALATE |
| Soft modifications | Adjust before proceeding | PROCEED_WITH_MODIFICATIONS |
| Audit trail | What happened and why | governance_audit.jsonl, deny logs |
| Static correctness checks | Tests, linters, type checkers | pytest, ruff, mypy |

**Boundary with Bucket 7 (per `constitution.md:120-133`):**
- Bucket 7 (Governance Policy) defines "what is the rule?" — normative content
- Bucket 6 (Verification & Quality) defines "how is the rule made sticky?" — enforcement mechanisms
- Bucket 6 cross-cuts — operates on multiple Bucket 7 sub-buckets simultaneously
- A hierarchy that conflates them hides the answer to either

#### Bucket 7: Governance Policy *(canonical)* / Intent / Governance OS *(legacy)*

What good looks like. The OS-equivalent that defines policies the system operates within. **Sub-bucket abstraction REVISED (session-140 round 3) — old list ("Constitution / Domain principles / Methods / Behavioral floor") was *content-inside-ai-governance*, not generic methods of a governance OS.**

The corrected sub-buckets are derived from the framework's own Constitutional structure (per the user's defense, session-140 — supersedes contrarian round 3 anchoring concern; user's argument: "amendment process = the OS dictating rules for adding/changing/deleting files"):

| Sub-bucket (generic governance method level) | What it provides | ai-governance specific | Home-automation-governance equivalent |
|---|---|---|---|
| Foundational constraints | Absolute rules that cannot be overridden | S-Series (Bill of Rights) | Smoke alarms, child safety locks (cannot be overridden by AI) |
| Organized normative content | Structured policy hierarchy at appropriate scope | Articles → meta-principles → domain principles | Policy hierarchy: house rules → room rules → device rules |
| Procedural rules | How policies get applied/interpreted | Rules of Procedure (methods) | Procedure for AI handling ambiguous commands |
| Authority resolution | Resolving conflicts when policies contradict | Constitutional supremacy clause + 7-layer hierarchy | Safety policy trumps convenience policy when they conflict |
| Amendment process | How policy changes over time (the OS dictating rules for adding/changing/deleting policy content) | MAJOR/MINOR/PATCH versioning per `meta-method-content-updates` | Adding new device types, deprecating old behaviors |
| Domain application | Context-specific application | Domain principles (title-NN) | Different rules for kitchen vs bathroom vs bedroom |
| Authority & adoption | How the OS gains operative authority over a project + resolves authority hierarchy | "Adoption and Authority" subsection at constitution.md:96; framework activates via CLAUDE.md inclusion | Homeowner enables AI control of specific devices |

**Status of "Authority & adoption" sub-bucket:** Partially resolved (2026-05-03). Authority is now a root function (§1). "Adoption" specifically is a Lifecycle event (Bucket 8) — the activation moment where a governance OS gains authority over a project. See §11 open questions for remaining placement uncertainty.

**Caveat previously claimed for Bucket 7 (session-140 round 2) — WITHDRAWN.** I had said "Bucket 7 is the meta-layer that recursively contains principle/method/appendix." That was a category error. I was looking inside ai-governance's specific OS instantiation (Constitution / Methods / Appendices) and calling that the bucket structure. User correction: Bucket 7's components are GENERIC governance OS functions — separate from the content INSIDE any specific governance OS.

#### Bucket 8: Lifecycle *(canonical, kept)*

Boot, shutdown, sleep, wake. Different timescale than runtime control flow.

| Sub-bucket (generic method level) | What it is | Current implementation |
|---|---|---|
| Initialization | Bring system to ready state | CLAUDE.md session-start protocol |
| Steady-state persistence | Save state during normal operation | SESSION-STATE updates, git checkpoints |
| Shutdown | Persist final state cleanly | SESSION-STATE update + commit |
| Resumption | Pick up across context windows | Ralph Loop equivalent (ACTION ON RESUME blocks) |
| Inter-agent handoff | Context transfer between specialists | Multi-agent handoff protocols |

### 2.3 Empirical assessment — compliance-review skill vs 8-bucket model (2026-05-03)

Per §2.1: "the model should be empirically tested when workflows/skills design begins." The compliance-review skill (`.claude/skills/compliance-review/SKILL.md`) is the first instantiation. Assessment:

| Bucket | How the Skill Touches It | Interaction Type |
|--------|--------------------------|-----------------|
| **1 — Inference Engine** | Skill loads into main LLM context (application program running on CPU) | Direct — skill IS a program on the inference engine |
| **2 — Memory** | Reads COMPLIANCE-REVIEW.md review history, checks SESSION-STATE (V-005), reads LEARNING-LOG (Check 4), references BACKLOG (Check 8) | Heavy consumer — reads from 4 memory surfaces |
| **3 — Retrieval** | Check 6 runs `query_governance()` canary — tests retrieval system health | Direct test of retrieval pipeline |
| **4 — Action Layer** | Tests MCP server (Check 6 canary), governance tool calls during execution | Indirect — exercises the action layer, doesn't modify it |
| **5 — Orchestration** | Skill IS an orchestration mechanism: coordinates 12-check workflow, spawns validator subagent (Check 5d), uses dynamic content injection | The skill lives here — it is the application program |
| **6 — Verification & Quality** | The entire compliance review IS a verification activity. Checks hook integrity (1), enforcement mode (1b), audit logs (6b) | The skill's PURPOSE is this bucket — cross-cutting quality gate |
| **7 — Governance Policy** | Checks tiers.json/CLAUDE.md alignment (Check 3), constitutional register integrity (Check 9) | Validates governance policy surfaces are coherent |
| **8 — Lifecycle** | Review has cadence lifecycle (10-15 days). V-series experiments track behavioral evolution. Review log captures longitudinal data. | Lifecycle management of the review process itself |

**Assessment: Model held.** All 8 buckets are distinct and the skill interacts with each in a characteristically different way. No bucket felt redundant, misplaced, or missing.

**Key finding — Bucket 5/6 boundary:** The skill (Bucket 5, orchestration tool) executes verification checks (Bucket 6, verification activity). This confirms the bucket separation is about the component's *nature* (what it is), not its *consumer* (who uses it). The compliance-review skill is an orchestration mechanism; the checks it runs are verification activities. A skill that runs analytics would be a Bucket 5 component exercising Bucket 3 retrieval — same pattern.

**Open questions updated:**
- §11 item 7 (Bucket 3 sub-bucket split): No signal from this test — skill's retrieval interaction is a single canary query, not enough to assess sub-bucket structure.
- §11 item 8 (Bucket 5 sub-bucket split): Mild signal — see Bucket 5 open question above.

**Conclusion:** No bucket adjustments needed for Phase 2 (OPERATIONS.md). The 8-bucket model maps cleanly to the first real instantiation.

---

## 3. Computer Architecture Analogies

The following refine the bucket model's computer analogies. Each captures a connection the initial session-140 analysis missed or mapped too literally. Added 2026-05-03 during fresh-eyes analysis.

### 3.1 BIOS/bootloader — CLAUDE.md, AGENTS.md, ai-instructions.md

CLAUDE.md and AGENTS.md are NOT part of the OS — they're the **BIOS/bootloader**. They fire before anything else, loading the OS into the system. The OS is the governance framework itself (constitution, domains, methods).

This distinction matters for modularization: if you moved to a different host (Cursor, Windsurf, GPT), you'd rewrite the BIOS (CLAUDE.md equivalent) but the OS (governance docs) would port unchanged. The BIOS is the one thing that's truly host-specific.

Mapping:
- `CLAUDE.md` = simplified bootloader for the current host (Claude Code)
- `AGENTS.md` = POST (Power-On Self-Test) checklist — what memory exists, startup sequence, what to check
- `documents/ai-instructions.md` = full BIOS ROM — the reference implementation of what any bootloader should do
- `.claude/settings.json` + `settings.local.json` = BIOS settings / CMOS — persistent configuration controlling bootloader behavior

User confirmed (2026-05-03): "excellent analogy" — the OS ports unchanged, the BIOS is rewritten per platform (or developed ahead of time as a driver for adopters, or noted for AI to know this piece would need to be built if someone were to use the framework in a different system).

### 3.2 System bus — MCP protocol

MCP is more fundamental than a tool in the Action Layer (Bucket 4). It's the **system bus** — the standardized interface that lets components talk to each other regardless of implementation. The governance server exposes tools via MCP. The Context Engine exposes tools via MCP. Claude Code consumes them via MCP. External tools can connect via MCP. That's PCIe — a standardized interconnect.

The *tools themselves* (query_governance, evaluate_governance) are the *devices on the bus*. The bus is the protocol. This distinction matters because the bus is what makes everything else swappable — as long as the new component speaks MCP, it plugs in.

User note (2026-05-03): there's a push toward APIs as an alternative bus type. The analogy holds — just a different bus standard (like PCIe vs USB vs Thunderbolt). Research pending on latest developments.

### 3.3 Interrupt controller — hooks

The hooks in `.claude/hooks/` fire on specific events (PreToolUse, PostToolUse, UserPromptSubmit, PrePush) and can halt execution. That's an **interrupt controller (PIC/APIC)** — hardware interrupts that preempt normal execution. Some are maskable (e.g., `CONTENT_SECURITY_SKIP=1`), some are effectively non-maskable (governance check has no practical bypass in normal operation).

Current hook inventory (8 hooks + Rampart tripwired):
- `pre-tool-governance-check.sh` — governance consultation enforcement
- `pre-tool-content-security.sh` — credential path access blocking (Layer 2)
- `pre-exit-plan-mode-gate.sh` — contrarian review before plan approval
- `pre-push-quality-gate.sh` — test/lint before push
- `pre-test-oom-gate.sh` — OOM-risk pattern detection before pytest
- `post-push-ci-check.sh` — CI status after push
- `user-prompt-governance-inject.sh` — governance context injection on prompt submit
- `scan_transcript.py` — transcript scanning
- **Rampart** (tripwired, OPERATIONS.md T-019) — agent firewall with YAML policy, native Claude Code PreToolUse integration. When adopted, adds stateful inspection layer (currently basic packet filtering via hooks).

Calling hooks "quality gates" undersells the architectural role. They're the mechanism that gives enforcement its teeth — the programmable interrupt controller between devices and the CPU.

### 3.4 Heterogeneous coprocessors — subagents

The 10 subagents have different roles that the existing Bucket 6 (Verification & Quality) placement underrepresents:

| Coprocessor type | Subagents | Computer analog |
|---|---|---|
| **Verification coprocessors** | code-reviewer, security-auditor, validator, coherence-auditor | Error-checking hardware (ECC, parity) |
| **Adversarial coprocessor** | contrarian-reviewer | TPM — independent validation at a different trust level |
| **Production coprocessors** | documentation-writer, test-generator | GPU — specialized for a workload type, produces output |
| **Coordination coprocessor** | orchestrator | DMA controller — manages data flow without CPU intervention |
| **Domain-specific coprocessors** | voice-coach, continuity-auditor | DSP — specialized signal processing for a domain |

Lumping them all in "verification" misses that some produce output, some verify output, and some coordinate. They're a heterogeneous compute cluster.

### 3.5 Filesystem — git repository

Git is the filesystem — where everything persists. Every component stores state in git: governance docs, memory files, hooks, agents, source code, tests. The git commit is the filesystem's fsync — the moment state becomes durable.

Key directory mappings:
- `.claude/` = dotfile config directory (like `~/.config/`)
- `documents/` = `/etc` (system configuration) + `/usr/lib` (shared libraries)
- `src/` = `/usr/local/lib` (locally built packages)
- `index/` = filesystem cache (pre-computed data for fast access)
- `staging/` = `/tmp` or build staging area
- `tests/` = test fixtures

**Why this is the right choice for the current use case:** Git gives versioning (every state is recoverable), branching (parallel work), diffing (see exactly what changed), blame (who changed what), and distributed backup — all for free. The AI session model (one conversation at a time) maps naturally to git's single-writer model. You'd only hit walls with concurrent multi-user writes, real-time updates, or structured queries — none of which are current requirements.

User confirmed (2026-05-03): good with git as filesystem given the assessment.

### 3.6 Workload modules and drivers — domains and CFRs

Domains are **workload modules** — specialized operating modes. When your computer runs a game, it uses the graphics subsystem. When it plays music, it uses the audio subsystem. When ai-governance handles coding, it loads the coding workload module.

- `title-NN-*.md` (domain principles) = the **workload module** — what rules and capabilities apply for this type of work
- `title-NN-*-cfr.md` (domain regulations) = the **driver** — the operational procedures that make the governance OS work with this specific workload type on specific platforms

This pattern is already modular — adding a new domain means adding a new module+driver pair without modifying the kernel. Each pair:
- Derives from the core kernel (constitution + rules-of-procedure)
- Has its own specialized rules (domain principles)
- Has its own operational procedures (CFR)
- Can be added or removed independently

Current workload modules: ai-coding (title-10), UI/UX (title-15), multi-agent (title-20), KM&PD (title-25), storytelling (title-30), multimodal-RAG (title-40).

### 3.7 Application programs — skills

Skills (`.claude/skills/*/SKILL.md`) are **application programs** — user-invocable instruction sequences that load into the main processor (Claude's context) when triggered via `/skill-name`. They bridge the gap between workflows (manuals someone follows) and hooks (automatic interrupt handlers).

Key distinctions in the computer analogy:
- **Skills** = application programs (Word, Photoshop). Invoked by user, run in main context, full memory access. Use for repeatable workflows and on-demand reference material. Can inject dynamic content at invocation (run `git diff` and include output).
- **Subagents** = coprocessors. Isolated context, specialized workload, return summary. Use for independent analysis where isolation is the feature.
- **Hooks** = interrupt handlers. Fire automatically on events, can halt execution. Use for enforcement that can't be forgotten.
- **Workflows** (`workflows/*.md`) = runbooks/manuals. Describe steps but don't execute them. Use for documented procedures.

Skills live in `.claude/skills/my-skill/SKILL.md` — project-specific (checked into git) or personal (`~/.claude/skills/`). The directory name becomes the slash command.

**Current status:** First skill shipped (2026-05-03): `.claude/skills/compliance-review/SKILL.md` — orchestrates the 12-check governance compliance review. Validates the application-program model: skill reads workflow definitions from `workflows/COMPLIANCE-REVIEW.md` (the runbook), spawns validator subagent (coprocessor) for Check 5d, operates under hook enforcement (interrupt controller). BACKLOG #55 discusses broader workflow codification.

**Decision matrix — when to use which mechanism:**

| Need | Mechanism | Why |
|------|-----------|-----|
| Repeatable on-demand workflow with dynamic context | **Skill** | Loads into main context, can inject live data (`!`git diff``), user controls timing |
| Independent analysis where isolation prevents bias | **Subagent** | Fresh context = independence (`multi-quality-validation-independence`). No access to session state. |
| Enforcement that must never be forgotten | **Hook** | Fires automatically on tool events. Structural > advisory (LEARNING-LOG: "advisory fails at 87%"). |
| Documented procedure a human or AI follows step-by-step | **Workflow** | Reference material. Doesn't execute — describes how to execute. |
| Automatic response to external events on a schedule | **Scheduled agent** | Cron-triggered via `/schedule`. No user prompt needed. For cadence-driven operations. |

Selection test: "What happens if the human forgets to invoke this?" If forgetting is dangerous → hook. If forgetting delays a cadence → scheduled agent. If forgetting wastes effort but isn't dangerous → skill (user invokes when ready). If the procedure changes frequently → workflow (easy to update, no code).

### 3.8 Package repository — reference library

The reference library is secondary authority — non-binding patterns accumulated from practice. That's **npm/apt/brew** — a growing catalog of community patterns you can draw on but aren't required to use. Non-authoritative (packages don't override the kernel), accumulates over time, informs practice without mandating it.

Supporting files as registry metadata:
- `documents/domains.json` + `tiers.json` = device registry / ACPI tables — machine-readable manifests of what workload modules and capability tiers exist

---

## 4. System Map — Complete Analogy-to-Project Mapping

Maps every identified project component to its computer analog. Organized by role, with interface type assessment for modularization readiness.

### 4.1 Core system

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **CPU** | LLM (the processor) | Claude Opus 4.6/4.7 via Anthropic API | Host harness API. Swappable if drivers (appendices) updated. |
| **OS Kernel** | Core governance framework | `documents/constitution.md` (v8.0.0) + `documents/rules-of-procedure.md` | 7-layer hierarchy, supremacy clause, derivation chain. **Coupled by design** — tight integration is architectural coherence, not a defect. |
| **Kernel interrupt handlers (NMI)** | S-Series (Bill of Rights) | 3 amendments in `constitution.md` | Veto authority, immutable. Part of kernel — not independently swappable by design. |
| **System libraries** | Meta-methods | `rules-of-procedure.md` methods | Referenced by ID. Swappable if contract (method ID, inputs, outputs) preserved. |

### 4.2 BIOS / boot subsystem

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **BIOS / Bootloader** | Session initialization | `CLAUDE.md` (simplified for Claude Code) | **Host-specific** — rewrite per platform, OS stays. |
| **POST checklist** | Agent configuration | `AGENTS.md` | Startup sequence, memory manifest. Host-specific. |
| **BIOS ROM** | Full boot reference | `documents/ai-instructions.md` | Reference implementation for any host. |
| **BIOS settings (CMOS)** | Settings files | `.claude/settings.json` + `.claude/settings.local.json` | Persistent bootloader config (permissions, hooks, allowed tools). |

### 4.3 System bus and interconnect

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **System bus (PCIe)** | MCP protocol | FastMCP server protocol (JSON-RPC over stdio) | Standardized — any MCP client can connect. **The bus makes everything swappable.** |
| **Devices on bus** | MCP tools | `server.py` tools + CE tools | JSON schema per tool. Swappable if schema preserved. |

### 4.4 Memory subsystem (Bucket 2)

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **CPU registers / program counter** | Working memory | `SESSION-STATE.md` | **Implicit contract** — hardcoded paths, format is convention. Interface contracts documented in §6. |
| **Hard disk (persistent)** | Semantic memory | `PROJECT-MEMORY.md` | **Implicit contract.** Interface contracts documented in §6. |
| **Event journal** | Episodic memory | `LEARNING-LOG.md` | **Implicit contract.** Interface contracts documented in §6. |
| **Job queue / task scheduler** | Prospective memory | `BACKLOG.md` | **Implicit contract.** Interface contracts documented in §6. |

### 4.5 Retrieval subsystem (Bucket 3)

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **Memory controller / DMA** | Context Engine | `src/.../context_engine/` (separate MCP server) | `BaseStorage` + `BaseConnector` abstractions + MCP tools. **Exemplar of modular design.** |
| **Filesystem cache** | Pre-built index | `index/` (global_index.json + embeddings) | Rebuilt by extractor. Swappable — extractor regenerates from source. |
| **Filesystem monitor** | Watcher daemon | `context_engine/watcher.py` + `watcher_daemon.py` | Auto-updates index on file changes. DMA-like. |

### 4.6 Action layer (Bucket 4)

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **Device firmware** | Governance MCP server | `server.py` + `retrieval.py` + `enforcement.py` | MCP tool schema contracts. Modular — internals can change if contracts preserved. |
| **Offline compiler** | Index builder | `extractor.py` | Parses docs → index. Runs offline. |
| **Type system** | Data schemas | `models.py` (Pydantic) | Internal data contract. |

### 4.7 Orchestration + Lifecycle (Buckets 5 & 8)

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **CPU scheduler** | Host harness orchestration | Claude Code ReAct loop | Host-provided. We influence via hooks/skills, don't own. |
| **Coprocessors (heterogeneous)** | Subagents | `.claude/agents/` (10, canonical: `documents/agents/`) | Task delegation, return summary. Modular — add/remove independently. |
| **Application programs** | Skills | `.claude/skills/` (1: compliance-review) | User-invocable instruction sequences. Decision matrix in §3.7. |
| **Runbooks / stored procedures** | Workflows | `workflows/` (3 checklists) | Human-triggered. Modular — standalone. |
| **Design review template** | Plan template | `.claude/plan-template.md` | Template for plan mode. Standalone. |

### 4.8 Verification & Quality (Bucket 6)

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **Interrupt controller (PIC/APIC)** | Hook system | `.claude/hooks/` (8 scripts + Rampart tripwired) | Event → exit code. Modular — each standalone. |
| **Watchdog timer** | CI workflows | `.github/workflows/` | Merge-blocking. Modular. |
| **Test bench** | Test suite | `tests/` + `tests/benchmarks/` | pytest. Modular. |
| **Utility programs** | Analysis scripts | `scripts/` | CLI tools. Standalone. |
| **Audit logger** | Governance audit log | `governance_audit.jsonl` + deny logs | Append-only structured log. |

### 4.9 Governance Policy (Bucket 7)

| Computer Component | Project Equivalent | Current Implementation | Interface Type |
|---|---|---|---|
| **OS kernel** (restated) | Constitution + RoP | `documents/constitution.md` + `rules-of-procedure.md` | **Coupled by design** — tight integration IS coherence. |
| **Workload modules** | Domain principles | `documents/title-NN-*.md` (6 domains) | Derives from kernel. Modular — add/remove without kernel changes. |
| **Drivers** | Domain regulations (CFR) | `documents/title-NN-*-cfr.md` (6 files) | Translates OS rules to domain-specific ops. Paired with module. |
| **Device registry (ACPI)** | Manifests | `documents/domains.json` + `tiers.json` | Machine-readable catalog of installed modules + tiers. |
| **Errata / known bugs** | Failure mode registry | `failure-mode-registry.md` + `test-failure-mode-map.md` | Documented failure modes with mitigations + test coverage. |
| **Package repository** | Reference library | `reference-library/` (staging infra exists) | Non-binding patterns. Additive, no dependencies. |

### 4.10 Documentation and meta

| Computer Component | Project Equivalent | File |
|---|---|---|
| **System schematic** | Architecture doc | `ARCHITECTURE.md` |
| **Hardware spec sheet** | Specification | `SPECIFICATION.md` |
| **Protocol spec** | API docs | `API.md` |
| **Bill of materials** | Software BOM | `SBOM.md` |
| **Security spec** | Security docs | `SECURITY.md` |
| **Design references** | Influences catalog | `INFLUENCES.md` |
| **Product manual** | README | `README.md` |
| **Build configuration** | Project config | `pyproject.toml` |
| **Portable system image** | Container | `Dockerfile` |
| **Build staging** | Staging area | `staging/` |
| **System blueprint** | This document | `EXECUTION-FRAMEWORK.md` |

---

## 5. Interface Assessment — Modularization Readiness

### 5.1 The interface boundaries insight

The 8-bucket taxonomy is useful for *thinking about* the system, but the thing that actually matters for modularization is **interface boundaries**. A computer component is swappable not because someone drew a nice taxonomy of it — it's swappable because there's a standardized interface between it and everything else. PCIe, SATA, USB, DIMM slots. The slot shape is the contract.

The project already has this in some places and not others:

- **Context Engine** is the exemplar — `BaseStorage` (abstract class at `context_engine/storage/base.py`) and `BaseConnector` (abstract class at `context_engine/connectors/base.py`) define explicit interfaces. You could swap filesystem storage for a database by implementing `BaseStorage`. You could add PDF parsing by implementing `BaseConnector`. The MCP tool contracts (`query_project`, `index_project`) are the external interface. That's a fully modular component.

- **Memory files** (SESSION-STATE, PROJECT-MEMORY, LEARNING-LOG, BACKLOG, OPERATIONS) are the opposite — they're referenced by hardcoded paths throughout CLAUDE.md and AGENTS.md, with implicit contracts (what fields exist, what format they use, what operations are valid). If you wanted to swap memory to a database, you'd have to rewrite every reference.

**The key reframe:** the 8 buckets describe WHAT the system has. Interface boundaries describe WHETHER those things are swappable. Both views are needed — the buckets for architectural reasoning, the interface assessment for modularization work.

User confirmed (2026-05-03): "100% agree."

### 5.2 Already modular — explicit interfaces, ready to swap

These components have defined interface contracts and can be replaced independently:

- **Context Engine** — `BaseStorage` + `BaseConnector` abstract classes + MCP tool contracts. The exemplar. If every component looked like this, the modularization goal would be met.
- **Hooks** — standalone scripts, exit-code interface (0=allow, 1=block), event-type routing. Add/remove/replace independently.
- **Subagents** — standalone markdown definitions, Task tool delegation interface. Add/remove/replace independently.
- **Domain workload modules + drivers** — paired title/CFR files, derive from kernel. Add new domain without kernel changes.
- **MCP tools** — JSON schema contracts. Swap internal implementation if schema preserved.
- **CI workflows** — independent workflow files, merge-blocking interface.
- **Reference library** — non-binding, additive, no dependencies.
- **Workflows** — standalone procedure files, manually triggered.
- **Test suite** — pytest, independent test files.
- **Scripts** — standalone CLI tools.

### 5.3 Implicit interface — phase 2 modularization candidates

These components work but have implicit contracts that would need to be made explicit for true swappability:

- **Memory files** (SESSION-STATE, PROJECT-MEMORY, LEARNING-LOG, BACKLOG, OPERATIONS) — every consumer knows the file paths and formats, but there's no abstract interface. The "contract" is scattered across CLAUDE.md, AGENTS.md, and session protocols. See §6 for documented interface contracts — the equivalent of what `BaseStorage` does for the Context Engine. This would enable swapping markdown files for a database, MCP server, or any other backend that implements the interface.
- **BIOS/bootloader** (CLAUDE.md, AGENTS.md) — the boot sequence is documented but not abstracted. Porting to a new host requires manual rewriting. A portable boot specification that any host's BIOS can implement would close this gap.
- **Index format** (global_index.json + embeddings) — rebuilt by extractor, consumed by retrieval. Format is implicit. Swapping embedding model requires rebuilding, but format contract isn't documented. Lower priority — extractor abstracts this already.

### 5.4 Coupled by design — deliberate tight integration

These components are tightly coupled AND SHOULD BE. Like a real kernel, tight integration is what makes the system coherent. Modularizing them would be like going from a monolithic kernel to a microkernel — a valid architectural choice but a fundamental redesign, not a component swap.

- **Constitution + Rules of Procedure** — the governance hierarchy, supremacy clause, and derivation chain are the tight coupling. Every domain derives from the constitution. Every method references the hierarchy. This is BY DESIGN — constitutional coherence requires it. Loosening would undermine the framework's authority model.
- **S-Series + enforcement mechanisms** — the Bill of Rights has veto authority specifically because it's tightly coupled to the enforcement layer. If you could "swap" the S-Series, you'd undermine the safety guarantee. This is the TPM equivalent — not meant to be removable.
- **The 7-layer hierarchy itself** — the override order (Bill of Rights > Constitution > Statutes > RoP > Regulations > SOPs > Secondary Authority) is the architectural invariant. It's not a component; it's the bus topology. Changing it changes the system's fundamental behavior.

**Why this coupling is correct per `meta-core-structural-foundations`:** The OS kernel SHOULD have "single responsibilities, explicit boundaries, and minimal coupling" *between its subsystems* — but the kernel itself is a cohesive unit. The constitution's internal structure (Articles, Bill of Rights, Preamble) has clear boundaries between subsystems while maintaining tight coherence as a whole. This is the same pattern as a well-designed kernel: drivers are loosely coupled, but the scheduler + memory manager + IPC are tightly integrated because they must be.

---

## 6. Memory Interface Contracts

**Added:** 2026-05-03 (Phase 2 Task 3.3). **Scope:** documentation-only — defines the implicit contracts that currently exist. Future phases may implement these as abstract interfaces (the Context Engine's `BaseStorage` pattern).

The Context Engine exemplar (`src/ai_governance_mcp/context_engine/storage/base.py`) defines explicit `read()`, `write()`, `search()`, `delete()` operations with typed parameters. Memory files currently have equivalent operations but as implicit conventions, not enforced interfaces.

| Memory Type | File | Valid Operations | Format Contract | Consumer |
|---|---|---|---|---|
| **Working** | `SESSION-STATE.md` | read, write (overwrite), prune (§7.0.4 distillation) | Markdown. "Current Position" + "Session Summaries" sections. <300 lines target. | Session-start protocol, session-end update |
| **Semantic** | `PROJECT-MEMORY.md` | read, append (new decisions), update (amend existing) | Markdown. ADR-style decision records with date, session, rationale. | Session-start protocol, mid-session decision routing |
| **Episodic** | `LEARNING-LOG.md` | read, append (new lessons), archive (>60-day entries) | Markdown. Date-headed entries with "What happened / Why / What changed" structure. | Session-start protocol, pre-action reference |
| **Prospective** | `BACKLOG.md` | read, append (new items), remove (on close — git is archive) | Markdown. Numbered items with difficulty tags. Philosophy block at top. Active + Discussion sections. | Mid-session discovery routing, compliance review (Check 8) |
| **Operational** | `OPERATIONS.md` | read, append (new items), update (audit logs, status) | Markdown. 5 sections: Cadences, Tripwires, V-series, Metrics, Scheduled Ops. C-NNN/T-NNN/M-NNN/V-NNN prefixes. | Compliance review, cadence triggers, tripwire evaluation |
| **Reference** | `reference-library/` | read, stage (propose new entry), promote (accept staged) | Markdown per entry. YAML frontmatter (maturity, source, tags). Staging area for proposed entries. | On-demand retrieval, domain-specific guidance |

**What implementing explicit interfaces would enable:**
- Swap markdown files for a database backend (implement the same operations against a DB)
- Swap for an MCP-based memory service (each operation becomes a tool call)
- Test memory operations in isolation (mock the interface, not the file system)
- Enforce format contracts via validation (currently convention-only)

**Why this is Phase 2 (documentation) not Phase 3 (implementation):** The current implicit contracts work. Making them explicit is documentation that enables future modularization, not a requirement for current operation. Implementing abstract interfaces would touch CLAUDE.md, AGENTS.md, session protocols, and potentially the Context Engine — a D3 effort that should be justified by a concrete consumer (e.g., adopter needing non-markdown storage).

---

## 7. Context Retention Priority Policy

When the host (Claude Code) compresses prior messages to stay within context limits, not all memory content has equal priority. This policy defines which information should be preserved longest and which can be evicted earliest, guiding both automatic host compaction and manual SESSION-STATE pruning (§7.0.4 in CLAUDE.md session lifecycle).

| Priority | Level | Content Type | Retention Rule |
|----------|-------|-------------|----------------|
| P0 | Never evict | CLAUDE.md, AGENTS.md, active plan file, hook definitions | Always loaded by host. Not subject to compaction. |
| P1 | Preserve across full session | SESSION-STATE current position, PROJECT-MEMORY active decisions, LEARNING-LOG recent entries (<60 days), OPERATIONS.md active tripwire/cadence state | Load at session start per CLAUDE.md session lifecycle. Re-read if context approaches limits. |
| P2 | Preserve during active task | Plan tasks in progress, verification criteria for current phase, governance evaluation results for current arc | May be summarized between arcs but must be recoverable from files. |
| P3 | Summarize when space-constrained | Prior session summaries in SESSION-STATE, completed task details, historical audit IDs | Distill to one-line pointers during §7.0.4 pruning. Full content recoverable via `git log`. |
| P4 | Archive (evict first) | LEARNING-LOG entries >60 days, closed BACKLOG item details, old session summaries (>3 sessions back), EXECUTION-FRAMEWORK design history sections | Remove from active memory files. Recoverable from git history. |

**Existing mechanisms that implement this policy:**
- **Host compaction:** Claude Code automatically compresses prior messages as context approaches limits. P0 content is exempt (loaded via system instructions). P1-P4 content in conversation history is subject to compaction in reverse priority order.
- **SESSION-STATE pruning (§7.0.4):** Manual distillation when file exceeds 300 lines. Route decisions to PROJECT-MEMORY (P1), lessons to LEARNING-LOG (P1), remove old summaries (P3→P4).
- **Memory-file routing:** CLAUDE.md session lifecycle directs which files to load at session start (P0-P1) vs. consult on demand (P2-P3).

**What this policy does NOT do:** It does not control Claude Code's internal compaction algorithm (that's host-level, not user-configurable). It provides a shared vocabulary for prioritization decisions when humans or AI agents prune memory files, and a reference for future automation when session-end hooks become available.

### 7.2 Session-end automation assessment (Phase 4 finding)

**The hard problem:** Claude Code has no `on-session-end` hook event. Session-end detection cannot be automated — neither CronCreate (fires on idle, not on exit) nor cloud routines (remote, periodic) can observe that a local session is ending.

**Current compensating controls:**
1. **Session-start pruning** (CLAUDE.md § Session Lifecycle): catches what the prior session missed by pruning stale SESSION-STATE content on next load.
2. **Session Closer Protocol** (`multi-method-session-closer-protocol`): defines what the operator should request at session end — manually invoked.
3. **Context retention priorities** (§7.1): define what to preserve, providing a rubric for both manual updates and future automation.

**When this changes:** If Claude Code adds an `on-session-end` hook event (analogous to `PreToolUse`/`PostToolUse`), configure it to trigger automatic SESSION-STATE.md update. Until then, the session-start compensating control is adequate — the cost of one stale session summary is low, and the pruning protocol recovers it. See OPERATIONS.md SO-003 for operational tracking.

---

## 8. Portability Model

### 8.1 The 4-layer portability story

User's CPU/motherboard refinement (session-140): different LLMs (CPUs) work on different host harnesses (motherboards). Some CPU/motherboard combos have features others lack. ai-governance is the OS that runs across these combos via "drivers" (appendices).

| Layer | Portability scope | Where it lives | Example |
|---|---|---|---|
| **Principles** | Universal — any CPU, any motherboard | `constitution.md`, meta-principles | "Verification must precede irreversible action" |
| **Generic methods** | CPU-agnostic, mostly motherboard-agnostic | `rules-of-procedure.md`, domain methods | "Use 6 cognitive memory types" |
| **Cross-platform standards** | Any motherboard that supports the standard (POSIX-equivalent) | AGENTS.md, MCP protocol | "Project context lives in AGENTS.md at repo root" |
| **Drivers + translators** | One CPU+motherboard combo (or translation between) | Appendices A/D/E + MCP itself | "Add this hook block to `.claude/settings.json`"; MCP translates between Anthropic's tool format and OpenAI's |

**Refinements to note:**
1. Subagents and hooks are NOT CPU features — they're host-harness (motherboard) features. Driver = specific CPU+motherboard combo, not just CPU.
2. AGENTS.md (Appendix K of title-10) is a cross-tool standard supported by 14+ tools — POSIX-equivalent for AI tooling.
3. Appendices include both DRIVERS (configure features) and TRANSLATORS (bridge instruction sets when LLM lacks native capability — MCP plays this role).
4. **Co-evolution caveat:** Claude Code's models are post-trained with the harness. Swapping the LLM (CPU) while keeping the motherboard (Claude Code) might degrade because the model wasn't trained on the new combo. This is unlike CPU swaps in computers; it's more like GPU/CUDA coupling — same coupling phenomenon, different domain.

### 8.2 Hardware-vs-software quality dimension

User question (session-140): are there two types of quality (and possibly security) — software-equivalent (rules and principles you write) and hardware-equivalent (built-in mechanisms in components)? If so, where do they fit?

In computer architecture, there ARE two distinct levels of security and quality verification:

| Level | Security examples | Quality examples |
|---|---|---|
| **Hardware-level (substrate)** | TPM (Trusted Platform Module), CPU security extensions (Intel SGX, AMD SEV), hardware firewalls, IOMMU, DMA protection, secure enclaves | ECC (Error-Correcting Code) memory, watchdog timers, hardware-based test fixtures (JTAG), Built-in self-test (BIST) |
| **Software-level (application)** | OS firewall, antivirus, signed binaries, file permissions, kernel sandboxing | Tests (unit, integration), linters, type checkers, code review, CI assertions |

These are genuinely distinct concerns even when they cooperate. Hardware-level is built INTO the substrate; software-level operates ABOVE it. You can write better software-level security but you can't (easily) add hardware-level security — that requires the chip itself to support it.

**Mapping to AI agents:**

| Level | AI agent equivalent |
|---|---|
| **Substrate (hardware-equivalent)** | Alignment training (RLHF), model card constraints, API-level rate limits, built-in safety classifiers (Anthropic's harm classifiers, OpenAI's moderation) |
| **Application (software-equivalent)** | Hooks, subagent battery, prompts, governance principles, MCP tool gates |

**Quick gut-check examples from real AI deployments (session-140):**

Substrate-level (hardware-equivalent) examples that exist today:
- **Apple Intelligence + Secure Enclave** — on-device AI inference attested by Secure Enclave hardware. Privacy guarantees are *literally* hardware-anchored, not policy-anchored. Closest analog to TPM-style hardware security in the AI world.
- **Anthropic's Constitutional AI** — safety constitution baked into the model via RLHF training. Not "rules applied on top of inference" — rules trained INTO the weights. Analogous to ECC RAM correcting bit errors at the substrate level.
- **OpenAI's Moderation API + safety classifiers** — separate models running on the inference path, infrastructure-enforced. Adopters can't easily disable them.
- **Google Gemini's built-in safety filters** — operate at the API layer; same pattern.
- **Llama Guard / NeMo Guardrails (when integrated at infrastructure layer)** — separate gating models that pre-screen inputs/outputs before they reach the application.

Application-level (software-equivalent) examples:
- **Hooks systems** like Claude Code's PreToolUse — application code in the host harness blocking actions
- **Subagent verification batteries** (like ours: validator, contrarian, coherence-auditor) — application-level review
- **Prompt-level safety instructions** ("don't do X" in system prompt) — weakest tier; easily overridden by clever prompting
- **MCP tool authorization gates** — application code deciding which tools are allowed when
- **CrewAI Flows / LangGraph state-graph guardrails** — application-level enforcement woven through the orchestration layer

**Gut check:** the analogy holds. There ARE genuinely two distinct levels in AI just like in computer architecture. Substrate-level enforcement is harder to add or modify after the fact (requires retraining, API-provider cooperation, or hardware updates). Application-level enforcement is more flexible but weaker — bypassable by clever prompting or by adopters who disable the layer.

**Implication for the bucket model:** Substrate-level safety/quality is INTERNAL to Bucket 1 (Inference Engine) — it's what the LLM ships with. It's not a separate bucket; it's a sub-bucket of Bucket 1 ("Substrate-level safety/quality" — see §2.2). Application-level quality lives in Bucket 6 (Verification & Quality). Two types exist, but they don't require splitting Bucket 6. Substrate-level lives in Bucket 1; application-level lives in Bucket 6.

**Open status:** this analysis is from general knowledge. Formal sources (cited security/quality architecture research) are a follow-up research task if needed; for v0.1-draft purposes, the gut-check examples above are sufficient evidence the analogy is grounded.

### 8.3 Principle / method / appendix mapping

User proposed (session-140): bucket level corresponds to principle level, sub-bucket level corresponds to method level, specific tool corresponds to appendix level.

**Where this mapping holds (most buckets):**

| Computer view | ai-governance view | Example |
|---|---|---|
| Bucket | Principle level — *what must be true* | "AI must maintain context appropriate to task across session boundaries" |
| Sub-bucket | Method level — *how to do it generically* (multiple valid approaches) | "Use 6 cognitive memory types" |
| Specific tool | Appendix level — *one specific implementation* | "`SESSION-STATE.md` template at this path" |

This aligns with how ai-governance docs are already organized: `constitution.md` holds principles → `rules-of-procedure.md` holds meta-methods → `title-NN-*.md` files hold domain principles + methods → appendices in title-10 hold tool-specific configs.

**Caveat 1: Some principles are cross-cutting, not bucket-mappable to one bucket.** S-Series safety, `meta-quality-visible-reasoning-traceability`, `meta-method-single-source-of-truth` apply across MULTIPLE buckets. They're *constitutional invariants* that constrain how every bucket is implemented.

**Caveat 2 (REVISED session-140):** Original caveat was "Compute (Bucket 1) and Intent (Bucket 7) are exceptions." Both are now WITHDRAWN:

- **Bucket 1 (Inference Engine) caveat withdrawn.** It IS a peer bucket. Principle: "Match model capability to task stakes." Method: "Right-size by task type." Appendix: "Opus 4.7 for D2+ in Claude Code."
- **Bucket 7 (Governance Policy) caveat withdrawn but with care.** Bucket 7 is a peer bucket; its sub-buckets are GENERIC governance methods (foundational constraints, organized normative content, etc.). The earlier "recursion" claim was a category error — I was conflating CONTENT INSIDE ai-governance (its specific principles/methods/appendices) with the COMPONENT structure (generic governance OS functions).

**Why this mapping matters for storage decisions.** If we adopt this mapping, then when codifying the Execution Framework method:
- The 8 buckets correspond to *principle-level* statements → could land at constitution / domain-principle level
- The sub-buckets correspond to *method-level* descriptions → could land in rules-of-procedure / domain methods
- Specific implementations correspond to *appendix-level* specifics → could land in tool appendices

The answer may not be "one method in rules-of-procedure" but "principles where principles live, methods where methods live, appendices where appendices live, with cross-references."

---

## 9. Gap Analysis — Computer Components with No Project Equivalent

| Missing Component | What It Does | Project Gap | Status |
|---|---|---|---|
| **Stateful firewall** | Deep inspection, threat patterns, I/O sanitization | Hooks = basic packet filtering. Rampart = stateful firewall. | Tripwired (OPERATIONS.md T-019). Deferred upgrade, not missing link. |
| **Resource monitor / power management** | Tracks resource consumption, provides telemetry | No token/API/context utilization tracking. OOM gate prevents catastrophe but no normal-operation observability. | **Genuine gap.** BACKLOG #58 adjacent but scoped to re-injection, not telemetry. |
| **Scheduler / clock** | Automated time-based operations | Cadences tracked in OPERATIONS.md. 3 scheduled operations defined (SO-001–SO-003). CronCreate demonstrated but session-only (7-day expiry). Cloud routines available but lack local MCP access. | **Partially closed (Phase 4, 2026-05-03).** Operations defined; full automation blocked by mechanism constraints (§7.2). |
| **Virtual memory manager** | Page replacement policy, eviction priority | Host handles compaction; no framework say in eviction. Context retention policy defined (§7.1). Session-end automation assessed (§7.2) — deferred pending on-session-end hook. | **Partially addressed** by §7. Full automation deferred. |
| **Diagnostic / debug port** | Real-time decision debugging | governance_audit.jsonl is post-hoc. No step-through of governance decisions. | **Minor gap.** Current audit trail adequate for most use. |
| **Application programs** | User-invocable software | First skill shipped: `compliance-review`. `.claude/skills/` created. | **Closed (Phase 1, 2026-05-03).** Decision matrix documented in §3.7. |

---

## 10. Decision Log

All decisions reached across the Execution Framework arc. A reader can scan this table for the current state of any decision.

| Decision | Status |
|---|---|
| **Name:** Execution Framework | Adopted (session-140) |
| **Type:** Method (works with anything following ai-governance's *structure*, regardless of *content/context*) | Adopted (session-140) |
| **Aim:** Architectural coherence | Adopted (session-140) |
| **Primary metaphor:** Custom computer (swappable components) | Adopted (session-140); supersedes earlier body/skeleton metaphor as primary; body/skeleton retained as supporting framing |
| **Two complementary views:** 4-function root + 8-bucket component | Adopted (session-140, extended 2026-05-03) |
| **Bucket layer is v0.1-draft** — first complete pass, expected to be empirically tested as workflows/skills are designed | Adopted (session-140) |
| **4-function root view:** Information Flow / Control Flow / Quality Gates / Authority | Adopted (2026-05-03); extends 3-function candidate |
| **Bucket 6 (Verification & Quality) is SEPARATE from Bucket 7 (Governance Policy)** — earlier proposed collapse REVERTED | Resolved (session-140) per `constitution.md:120-133` evidence: enforcement is cross-cutting, not OS-internal |
| **Constitutional sub-buckets are generic structural truths** (per the framework's Declaration) | Adopted (session-140) — user's amendment-as-file-editing analogy resolved contrarian's "anchored to F-P2-04" concern |
| **Mapping (with caveats):** Bucket = principle / sub-bucket = method / specific tool = appendix | Adopted with caveats (session-140) — see §8.3 |
| **Storage location:** ai-governance docs vs project files | **Pending** — leaning multi-layer (principles where principles live; methods where methods live; appendices where appendices live) per §8.3's mapping |
| **Schema:** Whether the article's 12 components are root or symptom-level | **Resolved (session-140):** symptom-level. 4 functions are root. 8 buckets are component layer. |
| **Trigger to ship:** What upcoming decision warrants codifying this? | **Partially resolved** — map demonstrates independent value; document transformation should happen before final codification |
| **Interface boundaries are the actionable insight for modularization** — buckets describe WHAT; interfaces determine WHETHER things are swappable | Adopted (2026-05-03) |
| **BIOS/bootloader distinction:** CLAUDE.md + AGENTS.md are host-specific bootloader, not part of the OS | Adopted (2026-05-03) |
| **MCP is the system bus** — standardized interconnect, not just a tool | Adopted (2026-05-03) |
| **Hooks are the interrupt controller (PIC/APIC)** — not just "quality gates" | Adopted (2026-05-03) |
| **Subagents are heterogeneous coprocessors** — verification, adversarial, production, coordination, domain-specific | Adopted (2026-05-03) |
| **Domains are workload modules, CFRs are drivers** | Adopted (2026-05-03) |
| **Skills are application programs** — bridge between workflows (manuals) and hooks (automatic) | Adopted (2026-05-03) |
| **Git as filesystem is correct** for current use case (single-developer, document-shaped state) | Confirmed (2026-05-03) |
| **OS kernel coupling is by design** — constitution + RoP tight integration is architectural coherence, not a defect | Confirmed (2026-05-03) |
| **Complete analogy-to-project map** — see §4 | Adopted (2026-05-03) |
| **Document transformation:** this file restructured from chronological brainstorm to permanent thematic blueprint | Completed (2026-05-03, session-145) |
| **Scheduling mechanism assessment:** CronCreate is session-local (7-day expiry); cloud routines lack local MCP access. Neither fully automates 10+ day cadences. | Assessed (2026-05-03, session-145). Documented in §7.2 and OPERATIONS.md SO-001–SO-003. |
| **Session-end automation deferred** — no on-session-end hook exists. Session-start pruning is the compensating control. | Deferred (2026-05-03). See §7.2. |

---

## 11. Open Questions / Decisions Pending

1. **Storage location** (§8.3) — Multi-layer placement leaning, not confirmed. Final decision deferred until bucket model is further empirically tested. Document transformation to permanent blueprint may resolve — if blueprint becomes permanent project file, the question changes.

2. ~~**3-function root conversation**~~ — **Resolved (2026-05-03).** Extended to 4-function: Information Flow, Control Flow, Quality Gates, Authority. See §1.

3. **Trigger to ship** — **Partially resolved.** Map demonstrates independent value — doesn't need workflows/skills as prerequisite. Document transformation completed (2026-05-03). Remaining: final codification into governance documents.

4. ~~**Q9 dependency direction**~~ — **Resolved (2026-05-03).** Map IS useful independent of workflows/skills. Method worth codifying on own merits. Workflows/skills = one empirical test, not prerequisite.

5. **Article's role** — Reference library entry + cited inline as example. Unchanged.

6. **Subtraction test** — if listed principles removed, what's left? Partially answered via root reduction; full audit deferred.

7. **Bucket 3 sub-bucket split** — should mechanism-level (semantic/lexical/direct read) and policy-level (always-on/selective load) be split into Bucket 3a/3b? No signal from first empirical test. Defer until further testing.

8. **Bucket 5 sub-bucket split** — should pattern-level / mechanism-level / scope-level be split into Bucket 5a/5b/5c? Mild signal from first empirical test (compliance-review skill acts as both "orchestration" and "application program"). Defer until more skills exist.

9. **Adoption/Authority placement** — **Partially resolved (2026-05-03).** Authority is now a root function (§1). "Adoption" specifically is a Lifecycle event (Bucket 8) — the activation moment where a governance OS gains authority over a project. Remaining uncertainty: is adoption a sub-bucket of Bucket 7 (the OS defines how it gains authority), a cross-cutting concern (like enforcement, per `constitution.md:120-133` precedent), or a transition/binding event in Bucket 8? Each placement implies a different mental model.

10. **Hardware-vs-software formal grounding** (§8.2) — current analysis is from general knowledge; if hard sources needed, that's a follow-up research task. Unchanged.

11. **Bucket renaming convention adoption** — canonical names introduced; need to migrate prose to canonical naming as content stabilizes. In progress.

12. ~~**Substrate-level safety classification**~~ — **Confirmed (2026-05-03).** Placed inside Bucket 1 (Inference Engine) as a sub-bucket. Substrate-level safety is internal to the CPU per hardware-vs-software dimension.

---

## 12. Design History

This section preserves the full deliberation trail — contrarian rounds, coaching questions, dead-ends, and framing evolution — so any future reader can reconstruct the reasoning behind every decision. Per pickup discipline: do not compress this section.

### 12.1 Framing evolution

#### The body/skeleton metaphor (initial framing, session-140)

User reframe (verbatim): *"I see the ai-governance docs (constitution, procedures, domains, etc.) as the meat of the ai-governance-mcp. What I'm seeing is that this article is essentially describing the [execution framework] that allows the ai-governance docs to work."*

- **ai-governance docs (intent layer)** = muscle and organs — what does the work
- **Execution Framework** = skeleton/frame — what holds it together and lets it move

This metaphor seeded the conversation and remains useful as supporting framing, but was superseded as the *primary* metaphor by the computer architecture view.

#### The 5-layer engineering stack (README.md:9-22)

The framework already names a 5-layer engineering stack in `README.md:9-22`:

```
Prompt engineering    →  how you phrase the request
Retrieval engineering →  grounding (vector stores, chunking, reranking)
Context engineering   →  assembling memory + tools + history per inference
Harness engineering   →  orchestration, guardrails, approval gates, durable state
Intent engineering    →  what good looks like, runs ACROSS all four above ← ai-governance lives here
```

User clarification (session-140): intent engineering REQUIRES the other 4 layers to function. Context Engine MCP server exists precisely because context engineering is a prerequisite for intent enforcement. Hooks exist because harness engineering (approval gates) is a prerequisite for principle enforceability. Sometimes you only need prompt; sometimes prompt+retrieval; sometimes the full stack — depending on what you're building.

#### ai-governance IS a harness (an "intent harness")

ai-governance is not a sub-component of someone else's harness. It's a harness in its own right — specifically, the **intent harness**. The scaffolding that makes principles enforceable rather than advisory.

- Hooks = our orchestration loop equivalent (PreToolUse blocking)
- Subagents = our verification mechanisms (validator, contrarian, coherence-auditor)
- Context Engine = our retrieval
- SESSION-STATE / PROJECT-MEMORY / LEARNING-LOG = our memory architecture
- BACKLOG = our prospective memory

The article isn't a competing taxonomy — it's a catalog of mechanisms from harness teams (Anthropic, OpenAI, LangChain, Perplexity) that could potentially sharpen our intent enforcement.

#### The custom-computer metaphor (primary, session-140)

User reframe (verbatim): *"The best analogy I have is what we are doing is like looking at a custom computer. You need memory (RAM), data flow (motherboard with different connectors to different types of devices), an operating system (our ai-governance docs), etc. We have a working computer, but I'm looking to see if there is better components we should switch out, faster RAM, a motherboard with ports we don't have but think we could use, etc."*

**Why this metaphor works better than body/skeleton.** Bodies don't get RAM upgrades; computers do. The computer metaphor adds *swappability* — the explicit purpose of identifying buckets is to evaluate "is there a better component available for this slot?" That's exactly what we want to do.

**Caveat acknowledged.** Computer architecture has clean separation enforced by physics; software systems have leaky abstractions. The metaphor is a thinking tool, not a literal architecture. Per `meta-quality-explicit-over-implicit`: surface the leakiness rather than pretending it doesn't exist.

#### The F-P2-08 disposition (reversed in constitution v7.0.0)

**Historical context.** Three contrarian-reviewer rounds (audits `a59c1dad9e3a2d3da`, `aa9bf233b1fb0bc18`, `ae1e98cf36382abd3`) flagged `constitution.md:98` (F-P2-08 disposition, v5.0.6) which rejected adding "Harness" as a 4th stage of the 3-step AI Interaction Model (Prompt→Context→Intent). This section previously defended F-P2-08 as a "category error" — arguing the interaction model and engineering stack were different abstractions on purpose.

**Superseded.** Session-143 analysis (3 Explore agents, 2 contrarian rounds, coherence audit) determined that the "different abstractions" defense was anchor bias: the session-140 AI fabricated a "single inference" vs "disciplines" distinction the constitution never stated, then used procedural language to suppress re-examination. The F-P2-08 disposition evaluated a narrower 4-step proposal that predated the 5-layer model; its rationale that "harness is operationally indistinct from Context Engineering" was incorrect. Constitution v7.0.0 reversed F-P2-08 and adopted the 5-layer engineering stack (Prompt → Retrieval → Context → Harness → Intent) as canonical. See `documents/constitution.md` Historical Amendments v7.0.0 entry for full rationale.

The substantive critiques from the contrarian rounds (Rule of Three, retroactive grouping, phantom failure mode, source-codification risk, deferral pattern) remain valid on their own merits and are unaffected by the F-P2-08 reversal.

### 12.2 Systemic-vs-symptom analysis

#### The question the user surfaced (session-140)

*"The 12ish components could be at the systemic level or they could be symptoms level and we need to extract the root cause layer. The fact they overlap the categories we have points to two things. Either our categories aren't or can't be generalized further or we haven't broken apart the 12ish items to a level that identifies what are they doing for each category that is causing them to do multiple duties."*

#### What overlap means (resolved)

Article's 12 components each touch multiple ai-governance principles because each component is doing multiple FUNCTIONS at once. Example: "Orchestration Loop" is Control Flow + Quality Gates because it both sequences AND verifies.

The 12 are **operational composites** of the 3 root functions. Overlap is structural, not accidental.

### 12.3 Storage location analysis (TBD — informed by §8.3 mapping)

| Option | Argument for | Argument against |
|---|---|---|
| **`documents/rules-of-procedure.md` (new method section)** | Meta-method telling HOW to design subsystems that enforce intent. RoP is canonical home for meta-methods. Universal across projects following ai-governance. Sits next to §9.7.7 Constitutional Analogy Register and §9.8.9 Legal System Analogy Authoring (similar meta-architectural content) | RoP already large; one more method adds doc surface |
| **`documents/title-10-ai-coding-cfr.md` (appendix)** | If specifically about coding subsystems, this could fit | Method is broader than coding |
| **Multi-layer placement** (per §8.3 mapping) | Honors the principle/method/appendix hierarchy: 8 buckets as principles in their natural homes; sub-buckets as methods alongside; appendices for tool-specific details | More cross-references; harder to maintain coherence |
| **New title (e.g., title-50-execution-frameworks)** | Clean home; signals importance | Premature for unvalidated method; violates Rule of Three |
| **Project files (`ARCHITECTURE.md`)** | Lowest commitment | Doesn't capture user's "works with other things following ai-governance's structure" intent |

**Tentative read:** Multi-layer placement per §8.3 mapping is most coherent with how ai-governance already organizes content.

### 12.4 Coaching questions — status

#### Q1 — Concrete instance test (ANSWERED 2026-04-30)

**Question:** Has subsystem-design inconsistency caused observable harm? If not, the method is solving an unobserved problem.

**User answer:** *"I have not seen subsystem design inconsistency cause observable harm, but your assumption is that the only reason to look at something like this is to fix a problem... we don't need a problem to justify this kind of work."*

**Implication:** The "phantom problem" filter was being over-applied to anticipatory and improvement work. Filed as BACKLOG #147 — proactive-vs-reactive bias. Q1 is closed in favor of the proactive framing.

#### Q2 — Subtraction test (ANSWERED partially)

**Question:** If `meta-core-informational-readiness`, `coding-quality-validation-gates`, `multi-architecture-orchestration-pattern-selection`, `coding-process-session-state-continuity` were removed, what would Execution Framework still cover?

**Status (session-140):** answered implicitly via the root reduction. The root layer adds genuinely new meta-organizational structure that doesn't exist in those principles. The 8-bucket layer is largely re-arrangement (some buckets ARE those principles in new vocabulary; some — like Compute, Lifecycle — are partially new framing).

#### Q3 — Rule of Three (PENDING discussion, partially neutralized by Q1 answer)

**Question:** 3 real subsystems + 1 hypothetical. Wait until 5 subsystems before abstracting?

**Status:** partially neutralized by Q1 (proactive work is valid). But the empirical-test discipline survives: defer FINAL bucket-layer commitment until more workflows/skills design instantiates the model. Hence v0.1-draft framing.

#### Q4 — Future-proofing self-test (PENDING)

**Question:** Article says good harness designs get *thinner* as models improve. Does the root reduction (vs 12-component map) pass that test better?

**Status:** Not yet answered. Holding for a dedicated root view conversation if needed.

#### Q5 — Trigger question (PARTIALLY RESOLVED)

**Question:** What upcoming decision benefits from having this method?

**Status:** Partially resolved (2026-05-03). Map demonstrates independent value. Document transformation completed. Remaining: final codification.

#### Q6 — Root resonance test (RESOLVED 2026-05-03)

**Question:** Do Information Flow / Control Flow / Quality Gates feel like the right root layer? Authority/Accountability as 4th dimension?

**Status:** Resolved — Authority adopted as 4th root function. See §1.

#### Q7 — Overlap status check (RESOLVED)

**Question:** Does the original "they overlap our categories" concern resolve under the operational-composites framing?

**Status:** Resolved — overlap is structural, not accidental. The 12 are operational composites of the root functions.

#### Q8 — Article's role (PENDING)

**Question:** With the Execution Framework anchored at the root layer, what role does Pachaar's article play?

**Status:** Not yet answered. Tentative: cited as one operational example + Reference Library entry for adopter discoverability.

#### Q9 — Workflows/skills coupling (RESOLVED 2026-05-03)

**Question:** Does the method help us design workflows, or does designing workflows tell us whether the method is right?

**Status:** Resolved — the map is useful independent of workflows/skills. Method worth codifying on own merits.

### 12.5 Subagent rounds — what happened across the arc

#### Round 1 (session-139, audit `a59c1dad9e3a2d3da`)

Pressure-tested the original "ai-governance is the governance LAYER of a harness" framing with a 7-item improvement list. Contrarian flipped:
- Surfaced F-P2-08 (later identified as category error — see §12.1)
- Caught "stronger on Four-Layer Validation" overclaim
- Recommended cutting 7 items to 1-2

Survived: cost-asymmetry framing, proportional-rigor discipline. Withdrew: F-P2-08 invocation as decisive.

#### Round 2 (session-140, audit `aa9bf233b1fb0bc18`)

Pressure-tested "Governance Chassis Pattern" generalization. Strong critiques:
- Rule of Three violated (3 real + 1 hypothetical)
- External-schema lock-in self-contradiction (Pachaar's own thesis: harness should THIN)
- Retroactive grouping (memory ≠ CE ≠ hooks ≠ workflows)
- Re-arrangement not new capability
- Phantom failure mode

User pushed back on the "phantom failure mode" filter being applied to proactive work. That move produced the root reduction and BACKLOG #147 (proactive-vs-reactive bias).

#### Round 3 (session-140, audit `ae1e98cf36382abd3`)

Pressure-tested two structural decisions: (a) collapse Bucket 6 into Bucket 7, (b) Constitutional sub-buckets as generic governance methods.

**Bucket 6 collapse — REJECTED with citation.** `constitution.md:120-133` explicitly rejects it: enforcement is cross-cutting, not OS-internal. Forced reversal of my agreement to the collapse — caught a deferral pattern (assistant integrating user pushback without independent verification).

**Constitutional sub-buckets — partially accepted.** Contrarian said items 4 (supremacy), 5 (amendment), 8 (adoption) don't generalize. User defended (session-140): amendment process IS generic — it's "OS rules for adding/changing/deleting policy." Adopted user's position — the items are generic at concept level even if mechanisms vary.

**Other findings:**
- Buckets 3, 4, 5 also have content/method conflations (now resolved in §2.2)
- Sub-bucket count for Bucket 7 was lopsided (8 sub-buckets in one bucket while others have 4-5)
- Three restructuring rounds suggest forward-continuation bias dressed as collaboration; recommended freezing root and marking 8-bucket layer v0.1-draft

Most recommendations adopted. v0.1-draft mark applied to bucket layer.

### 12.6 Explicit non-decisions

#### Not done: Codify Pachaar's 12-component schema as authoritative

Reasons: the article's own thesis says harness should thin; the 12 are operational composites; other harness teams use different counts; codifying anchors us to April-2026 vendor consensus.

#### Not done: Adopt "Governance Chassis Pattern" as a single-file template

Reasons: forcing every subsystem into a 12-cell template generates filler; memory/CE/hooks/workflows aren't the same execution-loop topology; re-arrangement of existing principles into new vocabulary.

#### Not done: Treat the article as a competing taxonomy

It isn't. It's input — one author's catalog of mechanisms that could inform our intent enforcement. Pick selectively.

#### Not done: Collapse Bucket 6 (Verification & Quality) into Bucket 7 (Governance Policy)

Considered (session-140) and REJECTED per `constitution.md:120-133`: enforcement is cross-cutting, not OS-internal. The Constitution explicitly distinguishes "what is the rule?" (normative content, Bucket 7) from "how is the rule made sticky?" (enforcement, Bucket 6). A hierarchy that conflates them hides the answer to either.

#### Not done: Continue restructuring the bucket model in the abstract

After three rounds, contrarian flagged forward-continuation bias. The root view has held; the 8-bucket layer is v0.1-draft pending empirical instantiation.

### 12.7 Fresh-eyes analysis context (2026-05-03)

**Context:** User brought Opus 4.6 for a fresh-eyes review of the entire Execution Framework, noting that Opus 4.7 (prior sessions) "was too literal and missed a lot of connections." Goal: identify improvements, missed connections, and produce a complete analogy-to-project map. User confirmed: the purpose is modularization — each major component should be swappable independently, like going from monolithic to object-oriented design.

This analysis produced: the interface boundaries insight (§5.1), all refined analogies (§3), the 4-function root view (§1), the complete system map (§4), the gap analysis (§9), and the modularization assessment (§5.2-5.4). The analysis is integrated into its thematic sections above; this entry preserves the provenance and session context.

---

## 13. Article Reference Content (Pachaar 2026 — narrative stripped)

**Purpose:** Capture the substantive elements of *"The Anatomy of an Agent Harness"* (Akshay Pachaar, April 6, 2026) so this conversation doesn't drift from the source. Narrative flourishes, marketing prose, and image descriptions removed; facts, frameworks, quotes, and evidence retained. Original at `/Users/jasoncollier/Downloads/AI Stuff Currently Working/anatomy_of_an_agent_harness_v2.md`.

### 13.1 Core thesis

- The harness is the complete software infrastructure wrapping an LLM: orchestration loop, tools, memory, context management, state persistence, error handling, guardrails.
- "If you're not the model, you're the harness" (Vivek Trivedy, LangChain).
- The "agent" is emergent behavior; the "harness" is the machinery producing it. "When someone says 'I built an agent,' they mean they built a harness and pointed it at a model."
- Anthropic's Claude Code documentation: the SDK is "the agent harness that powers Claude Code."
- OpenAI's Codex team uses identical framing — agent and harness refer to the **non-model infrastructure**.

### 13.2 The Beren Millidge analogy ("Scaffolded LLMs as Natural Language Computers", 2023)

A raw LLM = CPU with no RAM, no disk, no I/O.
- Context window = RAM (fast but limited)
- External databases = disk storage (large but slow)
- Tool integrations = device drivers
- The harness = operating system

> "We have reinvented the Von Neumann architecture" — Millidge

### 13.3 Three levels of engineering (Pachaar's taxonomy)

- **Prompt engineering** — crafts the instructions the model receives
- **Context engineering** — manages what the model sees and when
- **Harness engineering** — encompasses both, plus tool orchestration, state persistence, error recovery, verification loops, safety enforcement, lifecycle management

### 13.4 The 12 production-harness components

| # | Component | One-line essence |
|---|---|---|
| 1 | Orchestration Loop | The Thought-Action-Observation (TAO/ReAct) cycle. Often "just a while loop" — Anthropic calls theirs a "dumb loop" with all intelligence in the model. |
| 2 | Tools | Schemas (name, description, parameter types) injected into LLM context + handlers for registration, schema validation, sandboxed execution, result formatting. Claude Code provides 6 categories: file ops, search, execution, web access, code intelligence, subagent spawning. |
| 3 | Memory | Short-term (conversation history) + long-term (cross-session persistence). Claude Code uses 3-tier hierarchy: lightweight index (~150 chars/entry, always loaded) → detailed topic files (on demand) → raw transcripts (search only). Critical principle: **agent treats its own memory as a "hint" and verifies against actual state before acting.** |
| 4 | Context Management | Prevents context rot. Strategies: compaction (summarize old), observation masking (hide old tool outputs while keeping calls visible — JetBrains Junie pattern), just-in-time retrieval (lightweight identifiers + dynamic load), sub-agent delegation (each subagent returns 1-2k token condensed summary). Goal per Anthropic: "smallest possible set of high-signal tokens." |
| 5 | Prompt Construction | Hierarchical assembly: system prompt + tool definitions + memory + history + current message. OpenAI Codex strict priority stack: server-controlled system message > tool definitions > developer instructions > user instructions (cascading AGENTS.md, 32 KiB limit) > conversation history. |
| 6 | Output Parsing | Modern: native tool calling (model returns structured `tool_calls` objects). Legacy: free-text + parser + retry-on-failure. Pydantic models for structured outputs. `RetryWithErrorOutputParser` (feeds prompt + failed completion + parsing error back to model) for edge cases. |
| 7 | State Management | LangGraph: typed state dicts through graph nodes, checkpointing at super-step boundaries, time-travel debugging. OpenAI: 4 mutually-exclusive strategies (application memory / SDK sessions / server-side Conversations API / `previous_response_id` chaining). **Claude Code: git commits as checkpoints + progress files as structured scratchpads.** |
| 8 | Error Handling | LangGraph 4-type taxonomy: transient (retry with backoff), LLM-recoverable (return error as ToolMessage so model can adjust), user-fixable (interrupt for human), unexpected (bubble up for debugging). Anthropic returns errors within tool handlers as error results. Stripe caps retry attempts at 2. **Math:** 10-step process × 99% per-step success = 90.4% end-to-end. Errors compound fast. |
| 9 | Guardrails and Safety | OpenAI SDK 3 levels: input guardrails (first agent), output guardrails (final output), tool guardrails (every invocation). "Tripwire" mechanism halts immediately. Anthropic separates permission from reasoning architecturally — model decides what to attempt; tool system decides what's allowed. **Claude Code gates ~40 discrete tool capabilities independently** with 3 stages: trust establishment at project load, permission check before each tool call, explicit user confirmation for high-risk operations. |
| 10 | Verification Loops | 3 approaches per Anthropic: rules-based (tests, linters, type checkers), visual (screenshots via Playwright for UI), LLM-as-judge (separate subagent evaluates output). **Boris Cherny (Claude Code creator): "giving the model a way to verify its work improves quality by 2 to 3x."** |
| 11 | Subagent Orchestration | Claude Code 3 execution models: Fork (byte-identical context copy), Teammate (separate terminal pane + file mailbox), Worktree (own git worktree, isolated branch per agent). OpenAI: agents-as-tools (specialist for bounded subtask) + handoffs (specialist takes full control). LangGraph: subagents as nested state graphs. |
| 12 | Lifecycle Management | Initialization, runtime, shutdown, resumption. Anthropic's "Ralph Loop" pattern for long-running tasks: Initializer Agent sets up environment (init script, progress file, feature list, initial git commit) → Coding Agent in subsequent sessions reads git logs and progress files, picks highest-priority incomplete feature, works on it, commits, summarizes. **Filesystem provides continuity across context windows.** |

### 13.5 The orchestration loop — step-by-step

1. **Prompt Assembly** — system prompt + tool schemas + memory + history + user message. Important content at beginning AND end (per Stanford "Lost in the Middle" finding — models lose 30%+ performance when key content falls in mid-window positions).
2. **LLM Inference** — model generates text, tool calls, or both.
3. **Output Classification** — text only → END; tool calls → execute; handoff → switch agent.
4. **Tool Execution** — validate args → check permissions → sandbox execute → capture results. Read-only ops run concurrently; mutating ops run serially.
5. **Result Packaging** — format as LLM-readable messages. Errors returned as error results for self-correction.
6. **Context Update** — append to history. If near context limit → trigger compaction.
7. **Loop** — return to step 1.

**Termination conditions (layered):** model produces response with no tool calls / max turn limit exceeded / token budget exhausted / guardrail tripwire fires / user interrupts / safety refusal returned.

### 13.6 The seven architectural decisions

1. **Single-agent vs. multi-agent.** Anthropic + OpenAI both recommend: maximize a single agent first. Split only when tool overload exceeds ~10 overlapping tools or clearly separate task domains exist.

2. **ReAct vs. plan-and-execute.** ReAct interleaves reasoning + action (flexible, higher per-step cost). Plan-and-execute separates them. **LLMCompiler: 3.6x speedup over sequential ReAct.**

3. **Context window management.** 5 production approaches: time-based clearing, conversation summarization, observation masking, structured note-taking, sub-agent delegation. **ACON research: 26-54% token reduction while preserving 95%+ accuracy** by prioritizing reasoning traces over raw tool outputs.

4. **Verification loop design.** Computational (deterministic — tests, linters) vs. inferential (semantic — LLM-as-judge). Martin Fowler/Thoughtworks framing: *guides* (feedforward, steer before action) vs. *sensors* (feedback, observe after action).

5. **Permission and safety architecture.** Permissive (auto-approve most) vs. restrictive (approve each action). Choice depends on deployment context.

6. **Tool scoping.** More tools = often worse performance. **Vercel removed 80% of tools from v0 and got better results. Claude Code achieves 95% context reduction via lazy loading.** Principle: expose minimum tool set for current step.

7. **Harness thickness.** Anthropic bets on thin harnesses + model improvement. Graph-based frameworks (LangGraph) bet on explicit control. **Anthropic regularly DELETES planning steps from Claude Code's harness as new model versions internalize the capability.**

### 13.7 Scaffolding metaphor + co-evolution principle

- Scaffolding is temporary infrastructure that enables workers to build a structure they couldn't reach otherwise. It doesn't do the construction; without it, workers can't reach upper floors.
- **Key insight: scaffolding is removed when the building is complete.** As models improve, harness complexity should decrease.
- **Manus rebuilt 5 times in 6 months — each rewrite removing complexity.** "Management agents" became simple structured handoffs. Complex tool definitions became general shell execution.
- **Co-evolution principle:** models are now post-trained with specific harnesses in the loop. Claude Code's model learned to use the specific harness it was trained with. Changing tool implementations can degrade performance because of this tight coupling.
- **The "future-proofing test":** if performance scales up with more powerful models without adding harness complexity, the design is sound.

### 13.8 Framework implementations (brief)

| Framework | Pattern | Key feature |
|---|---|---|
| Anthropic Claude Agent SDK | `query()` async iterator, "dumb loop" | All intelligence in model. Claude Code uses Gather-Act-Verify cycle. |
| OpenAI Agents SDK | Runner class with async/sync/streamed modes | Code-first (native Python, not graph DSL). Codex 3-layer architecture: Core + App Server + Client Surfaces — "Codex models feel better on Codex surfaces than a generic chat window." |
| LangGraph | Explicit state graph with conditional edges | Two nodes (`llm_call`, `tool_node`) connected by conditional edge. Replaced AgentExecutor (deprecated v0.2: too rigid, no multi-agent support). LangChain Deep Agents explicitly use term "agent harness." |
| CrewAI | Role-based multi-agent | Agent (role + goal + backstory + tools) → Task → Crew. Flows layer adds "deterministic backbone with intelligence where it matters." |
| AutoGen / Microsoft Agent Framework | Conversation-driven orchestration | 3-layer (Core / AgentChat / Extensions). 5 patterns: sequential, concurrent, group chat, handoff, magentic (manager agent with dynamic task ledger). |

### 13.9 Key evidence cited in the article

- **TerminalBench:** LangChain changed only the infrastructure (same model, same weights) and jumped from outside top 30 to rank 5 on TerminalBench 2.0.
- **76.4% pass rate** by having an LLM optimize the infrastructure itself, surpassing hand-designed systems.
- **30%+ degradation** when key content falls in mid-window positions (Chroma research, Stanford "Lost in the Middle").
- **3.6x speedup** of LLMCompiler over sequential ReAct (plan-and-execute pattern).
- **26-54% token reduction with 95%+ accuracy preservation** (ACON research).
- **2-3x quality improvement** from verification loops (Boris Cherny, Claude Code).
- **Vercel: 80% tool reduction → better results.**
- **Claude Code: 95% context reduction via lazy loading.**

### 13.10 Headline quote (closing)

> "**The next time your agent fails, don't blame the model. Look at the harness.**"

### 13.11 What this article does NOT establish (anti-drift notes)

To prevent over-anchoring to one author's synthesis:
- The 12-component count is one author's choice. LangChain uses 4-7. Anthropic SDK docs use a different breakdown.
- The "Three Levels of Engineering" is Pachaar's framing, not industry consensus. Other frames exist (e.g., Beren Millidge's OS-architecture analogy, Vellum's 4-strategy framework, AWS Bedrock's agent abstractions).
- Claims like "the harness is the product" are persuasive marketing for harness investment, not architectural truth. They cut against the article's own scaffolding-thinning thesis.
- Some examples (Manus, JetBrains Junie) are vendor-specific anecdotes, not published research.

Use the article as **evidence catalog and pattern source**, not as authoritative taxonomy. The root view in this Execution Framework is meant to be one level of abstraction ABOVE Pachaar's 12-component view, precisely so we don't anchor to a 2026 vendor consensus snapshot.

---

## 14. References

- Article: `/Users/jasoncollier/Downloads/AI Stuff Currently Working/anatomy_of_an_agent_harness_v2.md` (Pachaar 2026)
- README 5-layer stack: `README.md:9-22`
- F-P2-08 disposition (reversed in constitution v7.0.0; see Historical Amendments): `documents/constitution.md:98`
- Enforcement-is-cross-cutting (decisive for Bucket 6/7 separation): `documents/constitution.md:120-133`
- Cognitive memory taxonomy: `PROJECT-MEMORY.md` ADR-5
- "Adoption and Authority" subsection (Bucket 7 Authority & adoption sub-bucket): `documents/constitution.md:96`
- BACKLOG #147 (proactive-vs-reactive bias — filed during this conversation)
- BACKLOG #148 (Execution Framework — references this file as primary content)
- Context Engine interface exemplar: `src/ai_governance_mcp/context_engine/storage/base.py`
- Context Engine connector exemplar: `src/ai_governance_mcp/context_engine/connectors/base.py`
- Subagent audits: `a59c1dad9e3a2d3da` (round 1), `aa9bf233b1fb0bc18` (round 2), `ae1e98cf36382abd3` (round 3)
- Governance audits: `gov-1ce1278cc85e` (article review), `gov-a2d2b84d5b99` (#146 filing), `gov-5ba8aa3ff93b` (this file initial creation + #147 filing), `gov-266235bbac6e` (bucket model addition), `gov-9452d3f7e513` (v0.1 update)

---

## 15. Version History

| Date | Version | Change | Session |
|------|---------|--------|---------|
| 2026-04-29 | v0.1 | Initial creation. Body/skeleton metaphor. | 139 |
| 2026-04-30 | v0.1 | Computer metaphor adopted. 8-bucket model v0.1-draft. 3 contrarian rounds. | 140 |
| 2026-05-03 | v0.2 | Fresh-eyes analysis. Interface boundaries insight. 4-function root. Complete system map. Gap analysis. | 145 |
| 2026-05-03 | v1.0.0 | Restructured from chronological brainstorm to permanent thematic blueprint. Added §6 Memory Interface Contracts, §7 Context Retention Policy. All content preserved; format transformation only. | 145 |
| 2026-05-03 | v1.1.0 | Phase 4: Added §7.2 session-end automation assessment. Updated §9 gap analysis (Scheduler partially closed, VM manager updated). Decision log entries for scheduling constraints. | 145 |
