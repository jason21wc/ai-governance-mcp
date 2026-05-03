# Execution Framework — Working Document

**Version:** v0.1-draft (8-bucket layer); 3-function root view present but not yet examined or locked
**Type:** Active brainstorm / pre-plan working document (this is reasoning capture, not a permanent framework artifact)
**Started:** 2026-04-29 (session-139)
**Last updated:** 2026-04-30 (session-140 mid-arc, v0.1 mark applied)
**Status:** Discussion phase — first-draft bucket model recorded; empirical testing deferred until workflows/skills design begins
**Trigger source:** External article — Akshay Pachaar, *"The Anatomy of an Agent Harness"* (April 6, 2026), at `/Users/jasoncollier/Downloads/AI Stuff Currently Working/anatomy_of_an_agent_harness_v2.md`
**Purpose:** Capture full-nuance reasoning. Summary loses too much context; this file preserves alternatives considered, contrarian rounds, dead-ends, and open questions so a plan can be drafted later from real ground truth, not a compressed gloss. **A future reader opening this file cold should be able to pick up exactly where the conversation left off.**

---

## 1. Decisions reached so far

| Decision | Status |
|---|---|
| **Name:** Execution Framework | Adopted (session-140) |
| **Type:** Method (works with anything following ai-governance's *structure*, regardless of *content/context*) | Adopted (session-140) |
| **Aim:** Architectural coherence | Adopted (session-140) |
| **Primary metaphor:** Custom computer (swappable components) | Adopted (session-140); supersedes earlier body/skeleton metaphor as primary; body/skeleton retained as supporting framing |
| **Two complementary views:** 3-function root + 8-bucket component | Adopted (session-140) |
| **Bucket layer is v0.1-draft** — first complete pass, expected to be empirically tested when workflows/skills design begins | Adopted (session-140) |
| **3-function root view:** Information Flow / Control Flow / Quality Gates | **Tentative — not yet examined as its own conversation. User noted: "not locked, just up next at some point."** Held as candidate root layer pending dedicated review. |
| **Bucket 6 (Verification & Quality) is SEPARATE from Bucket 7 (Governance Policy)** — earlier proposed collapse REVERTED | Resolved (session-140) per `constitution.md:120-133` evidence: enforcement is cross-cutting, not OS-internal; "normative layers answer 'what is the rule?' — enforcement mechanisms answer 'how is the rule made sticky?'" |
| **Constitutional sub-buckets are generic structural truths** (per the framework's Declaration) | Adopted (session-140) — user's amendment-as-file-editing analogy resolved contrarian's "anchored to F-P2-04" concern |
| **Mapping (with caveats):** Bucket = principle / sub-bucket = method / specific tool = appendix | Adopted with caveats (session-140) — see §6 |
| **Storage location:** ai-governance docs vs project files | **Pending** — leaning multi-layer (principles where principles live; methods where methods live; appendices where appendices live) per §6's mapping |
| **Schema:** Whether the article's 12 components are root or symptom-level | **Resolved (session-140):** symptom-level. 3 functions are root. 8 buckets are component layer. |
| **Trigger to ship:** What upcoming decision warrants codifying this? | **Pending** — Q5 of coaching questions (§8) |

---

## 2. The framing reached

### 2.1 The body/skeleton metaphor (initial framing, session-140)

User reframe (verbatim): *"I see the ai-governance docs (constitution, procedures, domains, etc.) as the meat of the ai-governance-mcp. What I'm seeing is that this article is essentially describing the [execution framework] that allows the ai-governance docs to work."*

- **ai-governance docs (intent layer)** = muscle and organs — what does the work
- **Execution Framework** = skeleton/frame — what holds it together and lets it move

This metaphor seeded the conversation and remains useful as supporting framing, but was superseded as the *primary* metaphor by the computer architecture view (§2.4).

### 2.2 The 5-layer engineering stack (README.md:9-22)

The framework already names a 5-layer engineering stack in `README.md:9-22`:

```
Prompt engineering    →  how you phrase the request
Retrieval engineering →  grounding (vector stores, chunking, reranking)
Context engineering   →  assembling memory + tools + history per inference
Harness engineering   →  orchestration, guardrails, approval gates, durable state
Intent engineering    →  what good looks like, runs ACROSS all four above ← ai-governance lives here
```

User clarification (session-140): intent engineering REQUIRES the other 4 layers to function. Context Engine MCP server exists precisely because context engineering is a prerequisite for intent enforcement. Hooks exist because harness engineering (approval gates) is a prerequisite for principle enforceability. Sometimes you only need prompt; sometimes prompt+retrieval; sometimes the full stack — depending on what you're building.

### 2.3 ai-governance IS a harness (an "intent harness")

ai-governance is not a sub-component of someone else's harness. It's a harness in its own right — specifically, the **intent harness**. The scaffolding that makes principles enforceable rather than advisory.

- Hooks = our orchestration loop equivalent (PreToolUse blocking)
- Subagents = our verification mechanisms (validator, contrarian, coherence-auditor)
- Context Engine = our retrieval
- SESSION-STATE / PROJECT-MEMORY / LEARNING-LOG = our memory architecture
- BACKLOG = our prospective memory

The article isn't a competing taxonomy — it's a catalog of mechanisms from harness teams (Anthropic, OpenAI, LangChain, Perplexity) that could potentially sharpen our intent enforcement.

### 2.4 The custom-computer metaphor (primary, session-140)

User reframe (verbatim): *"The best analogy I have is what we are doing is like looking at a custom computer. You need memory (RAM), data flow (motherboard with different connectors to different types of devices), an operating system (our ai-governance docs), etc. We have a working computer, but I'm looking to see if there is better components we should switch out, faster RAM, a motherboard with ports we don't have but think we could use, etc."*

**Why this metaphor works better than body/skeleton.** Bodies don't get RAM upgrades; computers do. The computer metaphor adds *swappability* — the explicit purpose of identifying buckets is to evaluate "is there a better component available for this slot?" That's exactly what we want to do.

**Caveat acknowledged.** Computer architecture has clean separation enforced by physics; software systems have leaky abstractions. The metaphor is a thinking tool, not a literal architecture. Per `meta-quality-explicit-over-implicit`: surface the leakiness rather than pretending it doesn't exist.

### 2.5 The F-P2-08 disposition (reversed in constitution v7.0.0)

**Historical context.** Three contrarian-reviewer rounds (audits `a59c1dad9e3a2d3da`, `aa9bf233b1fb0bc18`, `ae1e98cf36382abd3`) flagged `constitution.md:98` (F-P2-08 disposition, v5.0.6) which rejected adding "Harness" as a 4th stage of the 3-step AI Interaction Model (Prompt→Context→Intent). This section previously defended F-P2-08 as a "category error" — arguing the interaction model and engineering stack were different abstractions on purpose.

**Superseded.** Session-143 analysis (3 Explore agents, 2 contrarian rounds, coherence audit) determined that the "different abstractions" defense was anchor bias: the session-140 AI fabricated a "single inference" vs "disciplines" distinction the constitution never stated, then used procedural language to suppress re-examination. The F-P2-08 disposition evaluated a narrower 4-step proposal that predated the 5-layer model; its rationale that "harness is operationally indistinct from Context Engineering" was incorrect. Constitution v7.0.0 reversed F-P2-08 and adopted the 5-layer engineering stack (Prompt → Retrieval → Context → Harness → Intent) as canonical. See `documents/constitution.md` Historical Amendments v7.0.0 entry for full rationale.

The substantive critiques from the contrarian rounds (Rule of Three, retroactive grouping, phantom failure mode, source-codification risk, deferral pattern) remain valid on their own merits and are unaffected by the F-P2-08 reversal.

---

## 3. The systemic-vs-symptom analysis

### 3.1 The question the user surfaced (session-140)

*"The 12ish components could be at the systemic level or they could be symptoms level and we need to extract the root cause layer. The fact they overlap the categories we have points to two things. Either our categories aren't or can't be generalized further or we haven't broken apart the 12ish items to a level that identifies what are they doing for each category that is causing them to do multiple duties."*

### 3.2 Proposed 3-function root reduction (CANDIDATE — not yet examined as its own conversation)

Grouping the article's 12 by underlying *function*:

| Root function | Article components | Why they group |
|---|---|---|
| **Information Flow** | Tools (#2), Memory (#3), Context Management (#4), Prompt Construction (#5), Output Parsing (#6), State Management (#7) | All move or store information |
| **Control Flow** | Orchestration Loop (#1), Subagent Orchestration (#11), Lifecycle Management (#12) | All decide what happens next |
| **Quality Gates** | Error Handling (#8), Guardrails & Safety (#9), Verification Loops (#10) | All catch failures or prevent bad outcomes |

**Status:** held across all rounds of bucket-layer iteration. **NOT YET examined as its own dedicated conversation** — user noted: "not locked, just up next at some point." When that conversation happens, we may discover the 3-function reduction needs revision (e.g., adding a 4th function for Authority/Accountability or Resource Stewardship). Until then, this is the best candidate root view.

### 3.3 Mapping the 3 root functions to ai-governance principles (CANDIDATE)

| Root function | ai-governance principles that govern it |
|---|---|
| Information Flow | `meta-core-informational-readiness`, `meta-method-single-source-of-truth`, `meta-quality-explicit-over-implicit`, `coding-context-context-window-management`, `coding-context-session-state-continuity` |
| Control Flow | `coding-process-discovery-before-commitment`, `coding-process-goal-first-dependency-mapping`, `coding-process-atomic-task-decomposition`, `multi-architecture-orchestration-pattern-selection`, `multi-coordination-state-persistence-protocol` |
| Quality Gates | `meta-quality-verification-validation`, `meta-operational-failure-recovery-resilience`, `meta-quality-visible-reasoning-traceability`, `meta-safety-non-maleficence-privacy-security` (S-Series), `coding-quality-validation-gates`, `multi-quality-fault-tolerance-and-graceful-degradation` |

### 3.4 What overlap means (resolved)

Article's 12 components each touch multiple ai-governance principles because each component is doing multiple FUNCTIONS at once. Example: "Orchestration Loop" is Control Flow + Quality Gates because it both sequences AND verifies.

The 12 are **operational composites** of the 3 root functions. Overlap is structural, not accidental.

---

## 4. The 8-bucket component view v0.1-draft

### 4.1 What v0.1-draft means

This is the **first complete pass** of the bucket model. We've identified buckets, sub-buckets, and resolved several conflations + the Bucket 6/7 collapse question. The model is **NOT** considered finalized; it should be **empirically tested** when workflows/skills design begins (Q9, §8). Continuing to abstract-reason about buckets without a real instantiation is forward-continuation bias dressed as rigor (per session-140 contrarian round 3 finding).

**Naming convention update:** each bucket has a **canonical name** (preferred going forward) and a **legacy name** (used in earlier prose). Move toward canonical naming as content stabilizes.

### 4.2 The 8 buckets

#### Bucket 1: Inference Engine *(canonical)* / Compute *(legacy — equivalent to "the LLM")*

The processor doing the actual reasoning. Not built by us — provided by Claude Code or whichever host harness runs us.

| Sub-bucket (generic method level) | What it is | Component swap question |
|---|---|---|
| Model selection | Choosing which model to use for a task | Opus 4.7 → Opus 5? Per-task right-sizing? |
| Inference parameters | Temperature, max tokens, thinking mode | Tunable per task? |
| Reasoning configuration | Plan-mode vs ReAct, plus-thinking | Host harness primarily decides |
| **Substrate-level safety/quality** | Built-in alignment + RLHF + safety classifiers (analogous to ECC RAM, hardware-level security) | Different model = different substrate-level quality (see §4.5 Hardware-vs-Software dimension) |

**Why surface this even though we don't own it:** swapping the model can change what scaffolding we still need (article's co-evolution insight — harness should thin as model improves).

**Caveat acknowledged previously withdrawn (session-140):** Bucket 1 is a peer bucket. The principle/method/appendix mapping applies (principle: "match model capability to task stakes"; method: "right-size by task type"; appendix: "Opus for D2+ in Claude Code").

#### Bucket 2: Memory *(canonical, kept)*

Persistent and transient state. Already mapped via CoALA in `PROJECT-MEMORY.md` ADR-5.

| Sub-bucket (generic method level) | What it is | ai-governance specific (appendix-level) | RAM-vs-disk failure mode |
|---|---|---|---|
| Working memory | Current task state | `SESSION-STATE.md` | Storing decisions here → lost when pruned |
| Semantic memory | Decisions & constraints | `PROJECT-MEMORY.md` | Storing transient context here → bloat |
| Episodic memory | Lessons from past failures | `LEARNING-LOG.md` | Storing decisions here → mixes "what we believe" with "what we learned" |
| Procedural memory | How-to patterns | `workflows/*` | Storing principles here → conflates rules with procedures |
| Prospective memory | Future intentions | `BACKLOG.md` | Storing decisions here → intentions and decisions get confused |
| Reference memory | External knowledge | `reference-library/` | Treating as authoritative when it's secondary authority |

Component-level questions: Are markdown files the right format? Should `LEARNING-LOG.md` be append-only structured data so we can analyze patterns? Should `reference-library/` move to a vector index?

**Sub-bucket abstraction status:** clean — these ARE generic methods (CoALA framework is generic, not ai-governance-specific).

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

**Open question:** should mechanism-level and policy-level be split into Bucket 3a / 3b, or kept as parallel sub-bucket lists within Bucket 3? Defer until empirical testing.

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
| Triggered handlers | Event-driven actions | 6 hooks (PreToolUse) |
| Subagent delegation | Hand off to specialist | Task tool with subagent definitions |

| Sub-bucket (scope level) | What it is | Current implementation |
|---|---|---|
| Multi-agent coordination | Sequential / parallel / handoff patterns across agents | `multi-architecture-orchestration-pattern-selection` |

**Open question:** should these three layers be split into Bucket 5a/5b/5c? Defer until empirical testing.

#### Bucket 6: Verification & Quality *(canonical)* / Quality Gates *(legacy)*

Catching problems and verifying correctness. **Stays SEPARATE from Bucket 7** per `constitution.md:120-133`: enforcement is cross-cutting, not OS-internal. Enforcement answers "how is the rule made sticky?" while Bucket 7 answers "what is the rule?" — different questions, different buckets.

| Sub-bucket (generic method level) | What it is | Current implementation |
|---|---|---|
| Pre-action gates | Block before damage | 6 hard-mode hooks (PreToolUse blocking) |
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

**Status of "Authority & adoption" sub-bucket:** see §11 open questions — uncertain whether this is a sub-bucket of Bucket 7, a cross-cutting concern (like enforcement), or a transition/binding event in Bucket 8 (Lifecycle).

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

### 4.3 The 4-layer portability story (CPU/motherboard refinement, session-140)

User's CPU/motherboard refinement (session-140): different LLMs (CPUs) work on different host harnesses (motherboards). Some CPU/motherboard combos have features others lack. ai-governance is the OS that runs across these combos via "drivers" (appendices).

This produces a 4-layer portability story:

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

### 4.4 Hardware-vs-software dimension (session-140 open discussion)

User question: are there two types of quality (and possibly security) — software-equivalent (rules and principles you write) and hardware-equivalent (built-in mechanisms in components)? If so, where do they fit?

**General-knowledge research summary** (formal online research deferred — flag to revisit if user wants empirical sources):

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

**Implication for the bucket model:**

Substrate-level safety/quality is INTERNAL to Bucket 1 (Inference Engine) — it's what the LLM ships with. It's not a separate bucket; it's a sub-bucket of Bucket 1 ("Substrate-level safety/quality" — already added in §4.2).

Application-level quality lives in Bucket 6 (Verification & Quality).

So the answer to the user's question: yes, two types exist, but they don't require splitting Bucket 6. Substrate-level lives in Bucket 1; application-level lives in Bucket 6. Each is a different layer of the stack.

**Open status:** this analysis is from general knowledge. Formal sources (cited security/quality architecture research) are a follow-up research task if needed; for v0.1-draft purposes, the gut-check examples above are sufficient evidence the analogy is grounded.

---

## 5. Two views of the Execution Framework — function and component

Both views co-exist and serve different decisions. Per `meta-method-single-source-of-truth`: each view has a distinct purpose; using the wrong view for a question produces noise.

| View | Best used for | Question it answers |
|---|---|---|
| **3-function root view** (Information Flow / Control Flow / Quality Gates) | Design coherence at architectural level. Auditing whether a subsystem covers all needed functional dimensions. Explaining the framework to a new adopter at high abstraction. Determining if a proposed new principle/method/feature fits an existing function or surfaces a gap. | *"Are we covering all the necessary functional dimensions?"* |
| **8-bucket component view** (Inference Engine, Memory, Retrieval, Action Layer, Orchestration, Verification & Quality, Governance Policy, Lifecycle) | Component-level swap and improvement decisions. Comparing implementations across systems. Mapping our framework to other frameworks. Identifying which areas have gaps vs solid coverage. | *"Which specific components do we have, and is there a better one available for this slot?"* |

**Mapping between views.** The 3-function root layer groups the 8 buckets:

| Root function (3) | Component buckets it groups |
|---|---|
| Information Flow | Memory + Retrieval + Action Layer (Buckets 2, 3, 4) |
| Control Flow | Orchestration + Lifecycle (Buckets 5, 8) |
| Quality Gates | Verification & Quality (Bucket 6) — operates cross-cuttingly on Bucket 7 |
| (Substrate) | Inference Engine (Bucket 1) — substrate, not a function we orchestrate |
| (Container) | Governance Policy (Bucket 7) — defines what Quality Gates enforce |

When to switch between views:
- Start a design conversation with the **3-function view** to ensure all dimensions are covered conceptually
- Move to the **8-bucket view** when comparing implementations, evaluating swaps, or auditing component-level coverage
- The 3-function view answers *what must be true*; the 8-bucket view answers *what specifically does it*

---

## 6. Bucket / sub-bucket / specific = principle / method / appendix mapping

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

## 7. Storage location analysis (TBD — informed by §6 mapping)

| Option | Argument for | Argument against |
|---|---|---|
| **`documents/rules-of-procedure.md` (new method section)** | Meta-method telling HOW to design subsystems that enforce intent. RoP is canonical home for meta-methods. Universal across projects following ai-governance. Sits next to §9.7.7 Constitutional Analogy Register and §9.8.9 Legal System Analogy Authoring (similar meta-architectural content) | RoP already large; one more method adds doc surface |
| **`documents/title-10-ai-coding-cfr.md` (appendix)** | If specifically about coding subsystems, this could fit | Method is broader than coding |
| **Multi-layer placement** (per §6 mapping) | Honors the principle/method/appendix hierarchy: 8 buckets as principles in their natural homes; sub-buckets as methods alongside; appendices for tool-specific details | More cross-references; harder to maintain coherence |
| **New title (e.g., title-50-execution-frameworks)** | Clean home; signals importance | Premature for unvalidated method; violates Rule of Three |
| **Project files (`ARCHITECTURE.md`)** | Lowest commitment | Doesn't capture user's "works with other things following ai-governance's structure" intent |

**Tentative read:** Multi-layer placement per §6 mapping is most coherent with how ai-governance already organizes content. Concrete: bucket-level statements in `rules-of-procedure.md` (since they're meta-methods describing system structure); method-level descriptions co-located; appendix-level details tied to specific platform appendices.

---

## 8. Coaching questions — status

### 8.1 Q1 — Concrete instance test (ANSWERED 2026-04-30)

**Question:** Has subsystem-design inconsistency caused observable harm? If not, the method is solving an unobserved problem.

**User answer:** *"I have not seen subsystem design inconsistency cause observable harm, but your assumption is that the only reason to look at something like this is to fix a problem... we don't need a problem to justify this kind of work."*

**Implication:** The "phantom problem" filter was being over-applied to anticipatory and improvement work. Filed as BACKLOG #147 — proactive-vs-reactive bias. Q1 is closed in favor of the proactive framing.

### 8.2 Q2 — Subtraction test (ANSWERED partially)

**Question:** If `meta-core-informational-readiness`, `coding-quality-validation-gates`, `multi-architecture-orchestration-pattern-selection`, `coding-process-session-state-continuity` were removed, what would Execution Framework still cover?

**Status (session-140):** answered implicitly via the 3-function root reduction. The 3-function layer adds genuinely new meta-organizational structure that doesn't exist in those principles. The 8-bucket layer is largely re-arrangement (some buckets ARE those principles in new vocabulary; some — like Compute, Lifecycle — are partially new framing).

### 8.3 Q3 — Rule of Three (PENDING discussion, partially neutralized by Q1 answer)

**Question:** 3 real subsystems + 1 hypothetical. Wait until 5 subsystems before abstracting?

**Status:** partially neutralized by Q1 (proactive work is valid). But the empirical-test discipline survives: defer FINAL bucket-layer commitment until workflows/skills design instantiates the model on a real new subsystem. Hence v0.1-draft framing.

### 8.4 Q4 — Future-proofing self-test (PENDING)

**Question:** Article says good harness designs get *thinner* as models improve. Does the 3-function reduction (vs 12-component map) pass that test better?

**Status:** Not yet answered. Holding for the dedicated 3-function root view conversation.

### 8.5 Q5 — Trigger question (PENDING — high priority per contrarian round 3)

**Question:** What upcoming decision benefits from having this method?

**Status:** Not yet answered. Workflows/skills design (Q9) is the natural answer; if there's nothing else, sequencing matters: ship workflows/skills first, let it stress-test the bucket model empirically.

### 8.6 Q6 — 3-function resonance test (NOT YET DEDICATED CONVERSATION)

**Question:** Do Information Flow / Control Flow / Quality Gates feel like the right root layer? Authority/Accountability as 4th dimension? Resource Efficiency as cross-cutting?

**Status:** Held until dedicated 3-function root conversation. User noted "not locked, just up next at some point."

### 8.7 Q7 — Overlap status check (RESOLVED)

**Question:** Does the original "they overlap our categories" concern resolve under the operational-composites framing?

**Status:** Resolved — overlap is structural, not accidental. The 12 are operational composites of the 3 functions.

### 8.8 Q8 — Article's role (PENDING)

**Question:** With the Execution Framework anchored at the 3-function root, what role does Pachaar's article play?

**Status:** Not yet answered. Tentative: cited as one operational example + Reference Library entry for adopter discoverability.

### 8.9 Q9 — Workflows/skills coupling (PENDING — load-bearing for trigger sequencing)

**Question:** Does the method help us design workflows, or does designing workflows tell us whether the method is right?

**Status:** Not yet answered. If the latter, sequence: workflows first → method second.

---

## 9. Subagent rounds — what happened across this arc

### 9.1 Round 1 (session-139, audit `a59c1dad9e3a2d3da`)

Pressure-tested the original "ai-governance is the governance LAYER of a harness" framing with a 7-item improvement list. Contrarian flipped:
- Surfaced F-P2-08 (later identified as category error — see §2.5)
- Caught "stronger on Four-Layer Validation" overclaim
- Recommended cutting 7 items to 1-2

Survived: cost-asymmetry framing, proportional-rigor discipline. Withdrew: F-P2-08 invocation as decisive.

### 9.2 Round 2 (session-140, audit `aa9bf233b1fb0bc18`)

Pressure-tested "Governance Chassis Pattern" generalization. Strong critiques:
- Rule of Three violated (3 real + 1 hypothetical)
- External-schema lock-in self-contradiction (Pachaar's own thesis: harness should THIN)
- Retroactive grouping (memory ≠ CE ≠ hooks ≠ workflows)
- Re-arrangement not new capability
- Phantom failure mode

User pushed back on the "phantom failure mode" filter being applied to proactive work. That move produced the 3-function root reduction (§3.2) and BACKLOG #147 (proactive-vs-reactive bias).

### 9.3 Round 3 (session-140, audit `ae1e98cf36382abd3`)

Pressure-tested two structural decisions: (a) collapse Bucket 6 into Bucket 7, (b) Constitutional sub-buckets as generic governance methods.

**Bucket 6 collapse — REJECTED with citation.** `constitution.md:120-133` explicitly rejects it: enforcement is cross-cutting, not OS-internal. Forced reversal of my agreement to the collapse — caught a deferral pattern (assistant integrating user pushback without independent verification).

**Constitutional sub-buckets — partially accepted.** Contrarian said items 4 (supremacy), 5 (amendment), 8 (adoption) don't generalize. User defended (session-140): amendment process IS generic — it's "OS rules for adding/changing/deleting policy." Adopted user's position — the items are generic at concept level even if mechanisms vary.

**Other findings:**
- Buckets 3, 4, 5 also have content/method conflations (now resolved in §4.2)
- Sub-bucket count for Bucket 7 was lopsided (8 sub-buckets in one bucket while others have 4-5)
- Three restructuring rounds suggest forward-continuation bias dressed as collaboration; recommended freezing 3-function root and marking 8-bucket layer v0.1-draft

Most recommendations adopted. v0.1-draft mark applied to bucket layer.

---

## 10. What we have explicitly chosen NOT to do

### 10.1 Codify Pachaar's 12-component schema as authoritative

Reasons: the article's own thesis says harness should thin; the 12 are operational composites; other harness teams use different counts; codifying anchors us to April-2026 vendor consensus.

### 10.2 Adopt "Governance Chassis Pattern" as a single-file template

Reasons: forcing every subsystem into a 12-cell template generates filler; memory/CE/hooks/workflows aren't the same execution-loop topology; re-arrangement of existing principles into new vocabulary.

### 10.3 Treat the article as a competing taxonomy

It isn't. It's input — one author's catalog of mechanisms that could inform our intent enforcement. Pick selectively.

### 10.4 Collapse Bucket 6 (Verification & Quality) into Bucket 7 (Governance Policy)

Considered (session-140) and REJECTED per `constitution.md:120-133`: enforcement is cross-cutting, not OS-internal. The Constitution explicitly distinguishes "what is the rule?" (normative content, Bucket 7) from "how is the rule made sticky?" (enforcement, Bucket 6). A hierarchy that conflates them hides the answer to either.

### 10.5 Continue restructuring the bucket model in the abstract

After three rounds, contrarian flagged forward-continuation bias. The 3-function root has held; the 8-bucket layer is v0.1-draft pending empirical instantiation when workflows/skills design begins.

---

## 11. Open questions / decisions pending

1. **Storage location** (§7) — Multi-layer placement leaning, not confirmed. Final decision deferred until bucket model is empirically tested.

2. **3-function root view dedicated conversation** (Q6) — has not yet happened. Information Flow / Control Flow / Quality Gates is candidate root layer; user noted "not locked, just up next at some point." Possible additions: 4th dimension for Authority/Accountability? Resource Efficiency as cross-cutting?

3. **Trigger to ship** (Q5) — what upcoming decision warrants codifying this method? Workflows/skills design is leading candidate.

4. **Q9 dependency direction** — does the method enable workflows/skills design, or does workflows/skills design produce the method? Sequencing depends on this.

5. **Article's role** (Q8) — Reference Library entry only? Or cited inline as example?

6. **Subtraction test** (Q2) — if listed principles removed, what's left? Partially answered via 3-function root analysis; full audit deferred.

7. **Bucket 3 sub-bucket abstraction split** (§4.2) — should mechanism-level (semantic/lexical/direct read) and policy-level (always-on/selective load) be split into Bucket 3a/3b? Defer until empirical testing.

8. **Bucket 5 sub-bucket abstraction split** (§4.2) — should pattern-level / mechanism-level / scope-level be split into Bucket 5a/5b/5c? Defer until empirical testing.

9. **Adoption/Authority sub-bucket placement** (§4.2 Bucket 7) — currently placed in Bucket 7 as "Authority & adoption" sub-bucket, but that placement is uncertain.

   **Question to ask user when picking this back up:** *"Adoption/Authority is the mechanism by which a governance OS gains operative authority over a particular project (e.g., framework activates via CLAUDE.md inclusion in ai-governance; homeowner enables AI control of devices in home-automation). Three plausible homes for it:*
   - *(a) Sub-bucket of Bucket 7 (Governance Policy) — the OS itself defines how it gains authority. Currently placed here.*
   - *(b) Cross-cutting concern, like enforcement (per `constitution.md:120-133` precedent) — operates across multiple buckets simultaneously, isn't OS-internal.*
   - *(c) Transition/binding event in Bucket 8 (Lifecycle) — happens at OS-installation/activation moments, similar to 'user accepts EULA during install.'*

   *Each placement implies a different mental model. Which framing fits the systemic-thinking lens you want for the Execution Framework?"*

   **Why this matters:** the placement determines whether Adoption/Authority is content the OS contains (a), a cross-cutting concern operating across the system (b), or an event that fires at lifecycle transitions (c). The choice shapes how adopters reason about granting governance authority.

10. **Hardware-vs-software quality dimension formal grounding** (§4.4) — current analysis is from general knowledge; if we want hard sources (cited security/quality architecture research), that's a follow-up research task.

11. **Bucket renaming convention adoption** (§4.1) — canonical names introduced; need to migrate prose to canonical naming as content stabilizes. Currently using both canonical + legacy.

12. **Substrate-level safety/quality classification** (§4.4) — placed inside Bucket 1 (Inference Engine) as a sub-bucket. Confirm or revisit.

---

## 12. References

- Article: `/Users/jasoncollier/Downloads/AI Stuff Currently Working/anatomy_of_an_agent_harness_v2.md` (Pachaar 2026)
- README 5-layer stack: `README.md:9-22`
- F-P2-08 disposition (reversed in constitution v7.0.0; see Historical Amendments): `documents/constitution.md:98`
- Enforcement-is-cross-cutting (decisive for Bucket 6/7 separation): `documents/constitution.md:120-133`
- Cognitive memory taxonomy: `PROJECT-MEMORY.md` ADR-5
- "Adoption and Authority" subsection (Bucket 7 Authority & adoption sub-bucket): `documents/constitution.md:96`
- BACKLOG #146 (taxonomy split for tripwires/cadences/projects)
- BACKLOG #147 (proactive-vs-reactive bias — filed during this conversation)
- BACKLOG #148 (Execution Framework — references this file as primary content; minimal entry)
- Subagent audits: `a59c1dad9e3a2d3da` (round 1), `aa9bf233b1fb0bc18` (round 2), `ae1e98cf36382abd3` (round 3)
- Governance audits: `gov-1ce1278cc85e` (article review), `gov-a2d2b84d5b99` (#146 filing), `gov-5ba8aa3ff93b` (this file initial creation + #147 filing), `gov-266235bbac6e` (bucket model addition), `gov-9452d3f7e513` (v0.1 update)

---

## 13. Article reference content (Pachaar 2026 — narrative stripped)

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

Use the article as **evidence catalog and pattern source**, not as authoritative taxonomy. The 3-function root view in this Execution Framework discussion is meant to be one level of abstraction ABOVE Pachaar's 12-component view, precisely so we don't anchor to a 2026 vendor consensus snapshot.

---

## 14. Maintenance notes

- This file is **working memory for an in-flight design conversation**, not a permanent framework artifact. When the conversation resolves into either (a) a plan to codify the Execution Framework method or (b) a decision to drop the idea, this file should be retired or moved to the appropriate permanent home.
- Per `meta-method-single-source-of-truth`: when content from this file lands in `rules-of-procedure.md` (or wherever), the canonical home is there, and this file becomes archive material.
- Per session-140 user direction: **do not summarize or compress this file's content** during routine SESSION-STATE updates — the nuance is the point.
- **Pickup discipline:** a future reader (human or AI) opening this file cold should be able to resume exactly where the conversation left off. If you find yourself unable to do that, the file has lost necessary context and should be enriched, not compressed.
- **Bucket layer is v0.1-draft.** Treat it as such — propose changes, flag conflations, surface gaps. The 3-function root view has not yet been examined as its own conversation; when it is, expect possible revision (additional dimensions, different decomposition).
