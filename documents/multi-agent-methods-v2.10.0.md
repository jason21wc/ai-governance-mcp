# Multi-Agent Methods
## Operational Procedures for AI Agent Orchestration

**Version:** 2.10.0
**Status:** Active
**Effective Date:** 2026-01-24
**Governance Level:** Methods (Code of Federal Regulations equivalent)

---

## Preamble

### Document Purpose

This document defines operational procedures that implement the Multi-Agent Domain Principles. It translates binding principles into executable workflows that AI systems and human operators follow when orchestrating agent-based workflows.

**Scope (v2.0.0):** This document covers:
- **Individual Specialized Agents** — Single agent with focused cognitive function
- **Sequential Agent Composition** — Agents invoked in sequence, output of one feeds next
- **Parallel Agent Coordination** — Multiple agents working simultaneously on independent tasks
- **Hybrid Patterns** — Combinations of the above

**Key Insight:** Many benefits of "multi-agent" systems can be achieved with sequential single-agent workflows. The critical factor is *specialization*, not *parallelization*. A generalist asked to implement AND validate AND check governance underperforms compared to sequentially invoking specialized configurations.

**Governance Hierarchy:**
```
+---------------------------------------------------------------------+
|  ai-interaction-principles.md (CONSTITUTION)                        |
|  Meta-Principles: Universal behavioral rules. Immutable.            |
+---------------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------------+
|  multi-agent-domain-principles.md (FEDERAL STATUTES)                |
|  Domain Principles: Agent-specific binding law.                     |
|  14 Principles: J1, A1-A5, R1-R5, Q1-Q3                             |
+---------------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------------+
|  THIS DOCUMENT: multi-agent-methods.md (CFR - REGULATIONS)          |
|  Operational procedures implementing the principles above.          |
|  HOW to comply. Updated more frequently than principles.            |
+---------------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------------+
|  Tool-Specific Appendices (AGENCY PROCEDURES)                       |
|  Claude Code CLI, Gemini CLI, Codex CLI specifics.                  |
+---------------------------------------------------------------------+
```

**Regulatory Authority:** These methods derive authority from Domain Principles. A method cannot contradict a principle. If conflict exists, the principle governs.

**Relationship to Principles:**
- **Domain Principles** define WHAT must be achieved (outcomes, requirements)
- **These Methods** define HOW to achieve it (procedures, workflows, templates)
- **Meta-Principles** (from Constitution) govern both and resolve conflicts

### Importance Tags Legend

This document uses importance tags to enable efficient partial loading:

| Tag | Meaning | Loading Guidance |
|-----|---------|------------------|
| CRITICAL | Essential for document effectiveness | Always load |
| IMPORTANT | Significant value, not essential | Load when relevant |
| OPTIONAL | Nice to have, first to cut | Load on demand only |

### Legal System Analogy

| Legal Concept | Framework Equivalent | Purpose |
|---------------|---------------------|---------|
| Constitution | ai-interaction-principles.md | Foundational, universal, immutable |
| Federal Statutes | multi-agent-domain-principles.md | Domain-specific binding law |
| **CFR (Regulations)** | **This document** | **Operational rules implementing statutes** |
| Agency SOPs | Tool appendices | Platform-specific execution |

---

## CRITICAL: How AI Should Use This Document

**Importance: CRITICAL — This section is essential for document effectiveness**

### Partial Loading Strategy

This document is designed for partial loading. AI should NOT load the entire document every session. Instead:

1. **Always load:** Preamble + Situation Index + Current workflow section
2. **Load on demand:** Specific procedures when needed
3. **Reference only:** Templates and appendices

### Situation Index — What To Do When...

**Use this index to jump directly to relevant procedures:**

| Situation | Go To | Key Procedure |
|-----------|-------|---------------|
| Deciding whether to use agents | §1.1 | Justified Complexity Check |
| Choosing method vs subagent | §1.1 | Artifact Type Selection |
| Starting agent workflow | §1.2 | Workflow Initialization |
| Creating a new subagent | §2.1 | Subagent Definition Standard |
| Adding governance to subagent | §2.1 | Governance Compliance Section (required item 4) |
| Writing effective system prompts | §2.1.1 | System Prompt Best Practices |
| Deciding which tools to allow | §2.1.2 | Tool Scoping Guidelines |
| Testing subagent before deployment | §2.1.3 | Subagent Validation Checklist |
| Using subagents in sessions | §2.1.4 | Subagent Usage in Practice |
| Choosing an agent pattern | §2.2 | Agent Catalog |
| Setting up orchestrator | §2.3 | Orchestrator Configuration |
| Choosing handoff pattern | §3.1 | Handoff Pattern Taxonomy |
| Handing off between agents | §3.2 | Handoff Protocol |
| Choosing orchestration pattern | §3.3 | Pattern Selection Matrix |
| Compressing context at boundary | §3.4 | Compression Procedures |
| Distilling memory for long sessions | §3.4.1 | Memory Distillation Procedure |
| Persisting state across sessions | §3.5 | State Persistence Protocol |
| Ending session | §3.6 | Session Closer Protocol |
| Monitoring agent execution | §3.7 | Observability Protocol |
| Production observability setup | §3.7.1 | Production Observability Patterns |
| Configuring execution loops | §3.8 | ReAct Loop Configuration |
| Validating agent output | §4.1 | Validation Agent Deployment |
| Need devil's advocate review | §4.2 | Contrarian Reviewer Pattern |
| Need governance compliance check | §4.3 | Governance Agent Pattern |
| Agent failure occurred | §4.4 | Fault Tolerance Procedures |
| Need human approval | §4.5 | Human-in-the-Loop Gates |
| Making governance structural | §4.6 | Governance Enforcement Architecture |
| Non-Claude platform enforcement | §4.6.2 | Gateway-Based Enforcement |
| Evaluating agent performance | §4.7 | Agent Evaluation Framework |
| Implementing safety guardrails | §4.8 | Production Safety Guardrails |
| Syncing context across tools | §5.1 | Cross-Tool Synchronization |
| "framework check" received | §1.2 | Re-initialization |

### On Uncertainty

- If procedure unclear: Escalate per Human-in-the-Loop Protocol (§4.5)
- If principle conflict suspected: Principle governs, flag for review
- If novel situation: Apply principle intent, document adaptation

---

## CRITICAL: Quick Reference

**Importance: CRITICAL — Primary navigation aid**

### The Agent Workflow Pattern

```
JUSTIFY -----> INITIALIZE -----> DELEGATE -----> EXECUTE -----> VALIDATE -----> HANDOFF -----> PERSIST
    |              |                  |              |              |              |              |
    |              |                  |              |              |              |              |
  Is agent      Context          Orchestrator    Specialist     Validator      Compress      State
  justified?     Files            Coordination    Execution     Review         Context       Files
```

### Core Agent Roles (Agent Catalog)

| Role | Cognitive Function | Purpose | Principle Basis |
|------|-------------------|---------|-----------------|
| **Orchestrator** | Strategic | Coordinate workflow, delegate, no domain work | A3 |
| **Specialist** | Domain-specific | Execute domain work (parameterized by specialty) | A1 |
| **Validator** | Analytical | Review outputs against explicit criteria | Q1 |
| **Contrarian Reviewer** | Critical | Challenge assumptions, surface blind spots | Q1, meta-adversarial |
| **Session Closer** | Operational | State persistence, context sync | R4 |
| **Governance Agent** | Evaluative | Assess compliance with principles | meta-governance |

### Principle to Title Mapping

| Domain Principle | Primary Title |
|------------------|---------------|
| Justified Complexity | Title 1 (Initialization) |
| Cognitive Function Specialization | Title 2 (Agent Architecture) |
| Context Engineering Discipline | Title 2 (Agent Architecture) |
| Context Isolation Architecture | Title 2 (Agent Architecture) |
| Orchestrator Separation Pattern | Title 2 (Agent Architecture) |
| Read-Write Division | Title 3 (Coordination) |
| Intent Propagation / Shared Assumptions | Title 3 (Coordination) |
| Explicit Handoff Protocol | Title 3 (Coordination) |
| Orchestration Pattern Selection | Title 3 (Coordination) |
| State Persistence Protocol | Title 3 (Coordination) |
| Observability Protocol | Title 3 (Coordination) |
| Validation Independence | Title 4 (Quality Assurance) |
| Fault Tolerance and Graceful Degradation | Title 4 (Quality Assurance) |
| Human-in-the-Loop Protocol | Title 4 (Quality Assurance) |

---

## CRITICAL: Cold Start Kit

**Importance: CRITICAL — Enables immediate productivity**

This section provides copy-paste templates for immediate agent workflow activation.

### Scenario A: New Agent Workflow — First Prompt

Copy and send this to start a new agent workflow:

```
I'm starting an agent-based workflow. Please help me set it up.

PROJECT: [Name]
GOAL: [1-2 sentences about the objective]
COMPLEXITY: [Simple (1-2 agents) / Medium (3-4 agents) / Complex (5+ agents)]

Before we begin:
1. Confirm you've loaded the multi-agent-methods framework
2. Run the Justified Complexity Check (§1.1)
3. If agents are justified, create context files
4. Identify which agent roles are needed
5. Propose the orchestration pattern (Sequential/Parallel/Hierarchical)
```

### Scenario B: Resume Agent Session — First Prompt

Copy and send this to resume existing agent work:

```
Resuming agent workflow on [PROJECT NAME].

Current state file:
---
[Paste contents of STATE.md or SESSION-STATE.md here]
---

Please:
1. Load context from synced files (claude.md, gemini.md, agents.md)
2. Confirm current phase and active agents
3. Identify next action from state file
4. Proceed (or ask clarifying questions if needed)
```

### Scenario C: Framework Check — Recovery Prompt

Copy and send this if context seems lost:

```
Framework check requested for agent workflow.

Please:
1. State what you understand about the current workflow and agents
2. Identify which agents have been deployed and their status
3. List any gaps in your understanding
4. Propose steps to re-establish working state
5. Check sync status of context files across tools
```

### Minimal Context File Template (Copy-Paste Ready)

Create this file as `claude.md`, `gemini.md`, AND `agents.md` in project root:

```markdown
# Project Context
**Last Updated:** [YYYY-MM-DD HH:MM]
**Synced Across:** Claude Code, Gemini CLI, Codex CLI

## Project Overview
- **Name:** [Project Name]
- **Goal:** [Original user intent - IMMUTABLE]
- **Constraints:** [Key constraints from original request]

## Current State
- **Phase:** [Current workflow phase]
- **Active Agents:** [List of deployed agents]
- **Pending Handoffs:** [Any queued handoffs]
- **Blockers:** None

## Agent Registry
| Agent Name | Role | Status | Last Action |
|------------|------|--------|-------------|
| [name] | [role] | [active/idle/complete] | [action] |

## Key Decisions
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]

## Session Log
- [YYYY-MM-DD HH:MM]: [Action taken]
```

---

# TITLE 1: Workflow Initialization

**Implements:** J1 (Justified Complexity), A4 (Intent Propagation / Shared Assumptions), R4 (State Persistence)

### 1.1 Justified Complexity Check

CRITICAL

**Purpose:** Validate that agent deployment is warranted before incurring the overhead.

**Source:** Cognition "Don't Build Multi-Agents", LangChain "When to Build Multi-Agent"

**The 15x Rule:** Multi-agent workflows typically consume 15x the tokens of single-agent approaches. This overhead must be justified by proportional value.

**Justification Checklist:**

Before deploying ANY agent (including single specialized agents), verify at least one:

| Justification | Description | Example |
|--------------|-------------|---------|
| Context Window Limits | Task requires more context than single window | Research across 50+ documents |
| Parallelization Opportunity | Independent subtasks benefit from concurrent execution | Research A, B, C simultaneously |
| Cognitive Function Mismatch | Task requires multiple distinct reasoning patterns | Implement AND validate AND critique |
| Quality Improvement | Specialization produces measurably better output | Security review by security specialist |
| Isolation Requirement | Validator must not inherit generator's reasoning | Fresh-context validation |

**Decision Tree:**

```
                    Can generalist complete this?
                             |
              +--------------+--------------+
              |                             |
             YES                            NO
              |                             |
         Use generalist              Why can't it?
                                           |
                    +----------+-----------+----------+
                    |          |           |          |
                Context    Parallel    Cognitive    Quality
                 Limit      Gains      Mismatch    Improvement
                    |          |           |          |
              Use agents   Use parallel  Sequential  Specialized
              with state   agents with   specialists  agents
              boundaries   read-write
                          analysis
```

**Artifact Type Selection: Method vs. Subagent**

When specialization IS justified, determine whether to formalize it as a **Method** (procedure for generalist to follow) or a **Subagent** (dedicated agent definition with fresh context).

| Factor | Favors **Method** | Favors **Subagent** |
|--------|-------------------|---------------------|
| **Fresh Context** ⚡ | Current context acceptable | Fresh context required (isolation from bias) |
| **Frequency** | Occasional/situational use | Repeated use pattern emerges |
| **Cognitive Function** | Compatible with current mode | Requires distinct mental mode that conflicts |
| **Tool Access** | Same tools appropriate | Restricted tools needed (e.g., read-only) |
| **Quality Driver** | Procedure improves consistency | Isolation improves objectivity |

⚡ = Primary signal. Fresh context need is the strongest indicator for subagent.

**Decision Tree (Step 2):**

```
             Specialization IS justified (from Step 1)
                              |
            Primary question: Does this require fresh context
            isolation from current reasoning?
                              |
              +---------------+---------------+
              |                               |
             YES                             NO
              |                               |
        Is there at least ONE              Document as METHOD
        supporting factor?                 (procedure in methods
        - Repeated use pattern              doc for generalist)
        - Tool restrictions needed
        - Conflicting cognitive function
        - Objectivity requires isolation
              |
        +-----+-----+
        |           |
       YES         NO
        |           |
   SUBAGENT     METHOD
   (fresh context  (still benefits from
    + other value)  procedure without
                    dedicated agent)
```

*Rationale: Fresh context alone may not justify dedicated agent overhead. Fresh context + frequency, tool needs, or cognitive isolation confirms subagent value.*

**Examples:**

| Capability | Artifact Type | Rationale |
|------------|---------------|-----------|
| Code Review | **Subagent** | Fresh context ⚡ (prevents writer bias) + repeated use + read-only tools + distinct cognitive function |
| Deliberative Analysis | **Method** | No fresh context need (same context OK) → procedure guides structured thinking |
| Security Audit | **Subagent** | Fresh context ⚡ (isolation from implementation bias) + tool restrictions + distinct cognitive function |
| Six Thinking Hats | **Method** | No fresh context need (same context builds on reasoning) → procedure guides perspective rotation |
| Contrarian Review | **Subagent** | Fresh context ⚡ (critical for objectivity) + repeated use + distinct critical cognitive function |
| Tree of Thoughts | **Method** | No fresh context need (same context required for coherence) → procedure guides branching |

**Key Insight:** Methods are "how the generalist thinks better." Subagents are "who else should think about this." If the value comes from *procedure*, use a method. If the value comes from *fresh perspective*, use a subagent.

**When in Doubt:** Default to Method (lower overhead, easier to evolve). Upgrade to Subagent if usage patterns reveal isolation or reuse value. See §2.1 for Subagent Definition Standard once decision is made.

**Documentation Requirement:**

When agents ARE deployed, document:

```markdown
## Agent Justification
**Justification Type:** [Context Limit / Parallel / Cognitive / Quality]
**Evidence:** [Why generalist insufficient]
**Expected Benefit:** [What improvement anticipated]
**Token Budget:** [Acceptable overhead multiple]
```

### 1.2 Workflow Initialization Protocol

CRITICAL

**Purpose:** Establish the foundation for agent work before any agents are deployed.

**Procedure:**

1. **Capture Original Intent**
   - Document the user's goal verbatim
   - Extract explicit constraints
   - Define success criteria
   - This becomes the IMMUTABLE intent context object

2. **Create Context Files**
   - Create `claude.md` in project root
   - Copy to `gemini.md` (identical content)
   - Copy to `agents.md` (identical content)
   - These files MUST stay synchronized

3. **Assess Complexity**
   - Simple (1-2 agents): Direct delegation or sequential
   - Medium (3-4 agents): Orchestrator recommended
   - Complex (5+ agents): Hierarchical orchestration required

4. **Perform Read-Write Analysis** (Per R2: Read-Write Division)
   - Identify read-heavy tasks (research, analysis, exploration)
   - Identify write-heavy tasks (synthesis, decisions, implementation)
   - Schedule read-heavy for parallel, write-heavy for sequential

5. **Select Orchestration Pattern**
   - See §3.3 Pattern Selection Matrix
   - Default: Sequential (Linear-First principle)

6. **Define Agent Roster**
   - Identify required cognitive functions
   - Map to agent roles from Agent Catalog (§2.2)
   - Document in context files

7. **Establish Shared Assumptions** (if parallel agents)
   - Complete Shared Assumptions Document (§3.2)
   - All parallel agents receive identical assumptions

**Intent Context Object Template:**

```markdown
## Intent Context (IMMUTABLE)
**Original Goal:** [Verbatim user request]
**Success Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
**Constraints:**
- [Constraint 1]
- [Constraint 2]
**This object must be passed to every agent in the chain.**
```

### 1.3 Multi-Tool Setup

IMPORTANT

**Purpose:** Configure multiple CLI tools to work on the same project with synchronized context.

**Procedure:**

1. **Directory Structure**
   ```
   project-root/
   +-- claude.md          # Claude Code context
   +-- gemini.md          # Gemini CLI context (synced)
   +-- agents.md          # Codex CLI context (synced)
   +-- .claude/
   |   +-- agents/        # Claude Code sub-agents
   +-- STATE.md           # Workflow state persistence
   +-- [project files]
   ```

2. **Launch Tools in Same Directory**
   - All CLI tools must be launched from project root
   - This ensures they share the same file system context
   - Each tool reads its respective context file

3. **Initial Sync Verification**
   - Confirm all three context files exist
   - Verify content is identical
   - Document sync status in STATE.md

---

# TITLE 2: Agent Architecture

**Implements:** A1 (Cognitive Function Specialization), A2 (Context Isolation), A3 (Orchestrator Separation), A5 (Context Engineering Discipline)

### 2.1 Subagent Definition Standard

CRITICAL

**Purpose:** Standardize how subagents are defined to ensure consistency and completeness.

**Source:** Anthropic Claude Code subagent documentation, NetworkChuck AI-in-Terminal patterns

**Terminology:** In Claude Code, agents invoked via the Task tool are called *subagents* because they run as child processes of the main conversation. Subagent definition files are stored in `.claude/agents/*.md` (project scope) or `~/.claude/agents/*.md` (user scope).

**Key Concept — Modular Personalities:** A subagent is not a separate program—it's a specialized *configuration* of the same underlying model. Think of it as a "hat" the AI wears: different system prompt, different tools, different cognitive focus. The same base model becomes a coder, validator, or orchestrator based on its subagent definition.

**Required Components:**

| Component | Required | Purpose |
|-----------|----------|---------|
| name | Yes | Unique identifier for invocation |
| description | Yes | Triggers auto-selection by orchestrator |
| cognitive_function | Yes | Mental model type (see taxonomy below) |
| tools | Yes | Permissions (allowed tool list or "all") |
| model | Optional | Override default model if needed |
| System Prompt | Yes | Detailed instructions (see structure below) |

**Cognitive Function Taxonomy:**

| Cognitive Function | Mental Model | Example Agents |
|-------------------|--------------|----------------|
| Strategic | Planning, coordination, delegation | Orchestrator |
| Analytical | Evaluation, validation, verification | Validator |
| Creative | Generation, ideation, synthesis | Writer, Designer |
| Critical | Challenging, questioning, critique | Contrarian Reviewer |
| Operational | Execution, implementation, action | Coder, Session Closer |
| Evaluative | Compliance, assessment, judgment | Governance Agent |

**System Prompt Structure:**

Every agent system prompt MUST include these sections:

1. **Who I Am** — Positive role definition
2. **My Cognitive Function** — Specific reasoning pattern I apply
3. **Who I Am NOT** — Explicit boundaries to prevent drift
4. **Governance Compliance** — How this agent aligns with governance framework
5. **Output Format** — Structured output template
6. **Success Criteria** — How to know the task is complete

**Subagent Definition Template:**

```markdown
---
name: [agent-name]
description: [1-2 sentence description triggering auto-selection]
cognitive_function: [strategic | analytical | creative | critical | operational | evaluative]
tools: [list of allowed tools, or "all"]
model: [sonnet | opus | haiku | gemini-pro | gpt-4 | default]
---

## System Prompt

You are a [cognitive function] specialist. Your role is to [specific mental model].

### Who I Am
[Positive definition of role, expertise, and focus]

### My Cognitive Function
[Specific reasoning pattern this agent applies]
[What mental model guides your work]

### Who I Am NOT
- I do NOT [anti-pattern 1]
- I do NOT [anti-pattern 2]
- I do NOT [anti-pattern 3]

### Governance Compliance
This agent operates within the AI Governance Framework hierarchy:
- **S-Series (Safety):** Veto authority — I will STOP and escalate if safety principles are triggered
- **Constitution:** I follow meta-principles (Context Engineering, Visible Reasoning, etc.)
- **Domain:** I apply [relevant domain] principles and methods
- **Judgment:** When uncertain, I query governance before proceeding

**Note:** This section provides defense-in-depth awareness. Primary enforcement occurs via Orchestrator calling `evaluate_governance()` before delegation. This section ensures agents maintain governance awareness even when invoked directly.

[Customize for this agent's specific governance touchpoints]

### Intent Context
[This section is populated at runtime with the immutable intent object]

### Output Format
[Structured format for outputs]
[Include required sections]

### Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- Include confidence indication: HIGH/MEDIUM/LOW with rationale
```

#### 2.1.1 System Prompt Best Practices

IMPORTANT

**Purpose:** Apply prompt engineering principles to agent system prompts for maximum effectiveness.

**Source:** Anthropic prompt engineering research, industry best practices 2025

**Principle Basis:** Derives from Constitution's Structured Output Enforcement and Rich but Not Verbose Communication.

**Best Practice 1: Positive Framing Over Negative Constraints**

The "Who I Am NOT" section uses negative framing which can confuse model interpretation. Balance with positive framing:

| Instead of | Use |
|------------|-----|
| "I do NOT write code" | "I delegate coding to specialists" |
| "I do NOT make product decisions" | "I escalate product decisions to humans" |
| "I do NOT skip validation" | "I always validate outputs before delivery" |

**Recommendation:** Lead with positive "Who I Am" section (what you DO), then use "Boundaries" section with mixed framing for clarity.

**Best Practice 2: Include Concrete Examples**

LLMs excel at pattern recognition. Include positive and negative examples:

```markdown
### Examples

**Good Example — Clear Delegation:**
User: "Fix the authentication bug"
→ Evaluate governance
→ Delegate to security-specialist with context: "Auth bug in login.py, user reports 401 on valid credentials"
→ Include acceptance criteria: "Login works with valid credentials, tests pass"

**Bad Example — Scope Creep:**
User: "Fix the authentication bug"
→ Start reading auth code directly ❌
→ Implement fix without delegation ❌
```

**Best Practice 3: Sandwich Method for Critical Instructions**

Place critical instructions at the beginning AND repeat at the end:

```markdown
# Agent Name

You are [role]. **You must [critical constraint].**

[... body of system prompt ...]

## Remember

- [Key point 1]
- [Key point 2]
- **[Critical constraint repeated from top]**
```

**Best Practice 4: Concrete Invocation Triggers**

Describe WHEN the agent should be invoked with specific scenarios, not abstract descriptions:

| Abstract (Avoid) | Concrete (Prefer) |
|------------------|-------------------|
| "Use for code review" | "Invoke after writing or modifying >20 lines of code" |
| "Use for governance" | "Invoke before any action that modifies files, runs commands, or makes architectural decisions" |
| "Use for debugging" | "Invoke when tests fail, errors occur, or behavior is unexpected" |

#### 2.1.2 Tool Scoping Guidelines

IMPORTANT

**Purpose:** Determine when to restrict agent tools versus allowing full inheritance.

**Source:** Claude Code subagent documentation, Anthropic multi-agent research

**Principle Basis:** Derives from Orchestrator Separation Pattern (A3) and Context Isolation Architecture (A4).

**Default Behavior:** If `tools` field is omitted, agent inherits ALL tools from parent context.

**When to Restrict Tools:**

| Condition | Restrict To | Rationale |
|-----------|-------------|-----------|
| **Orchestrator role** | Read, Glob, Grep, Task, governance MCPs | Prevents direct execution; forces delegation |
| **Validator role** | Read, Grep, Glob (no Edit/Write) | Fresh perspective without modification ability |
| **Research role** | Read, Grep, Glob, WebSearch, WebFetch | Information gathering, no side effects |
| **Sensitive operations** | Explicit allowlist only | Principle of least privilege |

**When to Allow Full Inheritance:**

| Condition | Rationale |
|-----------|-----------|
| **Specialist executing work** | Needs full capability to complete domain tasks |
| **Debugging agent** | May need any tool to diagnose issues |
| **Trusted internal agent** | Overhead of restriction exceeds risk |

**Tool Scoping Decision Matrix:**

```
Does agent need to MODIFY files or state?
├── NO → Restrict to read-only tools
│         (Read, Glob, Grep, WebSearch, WebFetch)
└── YES → Does agent need ALL modification tools?
          ├── NO → Explicit allowlist (Edit, Write only; or Bash only)
          └── YES → Inherit all (omit tools field)
```

**Tool Risk Gradient:** Tools can also be categorized by risk level:
- **Data-oriented** (read/query) → lowest risk, minimal HITL needed
- **Logic-oriented** (compute/transform) → medium risk, validate outputs
- **Action-oriented** (state changes, external calls) → highest risk, HITL gates recommended

**Platform-Specific Notes:**

- **Claude Code:** Tool restrictions in YAML frontmatter are HARD enforcement
- **Other platforms:** May require gateway-based enforcement (see §4.6.2)

#### 2.1.3 Subagent Validation Checklist

IMPORTANT

**Purpose:** Verify subagent effectiveness before deployment.

**Source:** Anthropic skill authoring best practices, iterative development patterns

**Principle Basis:** Derives from Validation Independence (Q1) and Fail-Fast Validation.

**Validation Procedure:**

**Phase 1: Static Review**

- [ ] **Name** follows convention: lowercase, hyphens, descriptive
- [ ] **Description** includes WHEN to invoke (concrete triggers, not abstract)
- [ ] **Tools** explicitly listed OR inheritance intentional
- [ ] **System prompt** includes all 5 required sections (Who I Am, Cognitive Function, Who I Am NOT, Output Format, Success Criteria)
- [ ] **Examples** included (at least 1 positive, 1 negative/edge case)
- [ ] **Critical instructions** repeated at end (sandwich method)

**Phase 2: Functional Testing**

Test with representative scenarios:

```markdown
## Test Cases

### Happy Path
Input: [typical task]
Expected: [correct delegation/output]
Result: [ ] PASS / [ ] FAIL

### Edge Case
Input: [boundary condition]
Expected: [graceful handling]
Result: [ ] PASS / [ ] FAIL

### Negative Test
Input: [out-of-scope request]
Expected: [appropriate refusal or escalation]
Result: [ ] PASS / [ ] FAIL
```

**Phase 3: Integration Testing**

- [ ] Agent invokable via expected mechanism (Task tool, /agent command)
- [ ] Handoffs to/from other agents work correctly
- [ ] Output format matches specification
- [ ] Tool restrictions enforced (attempt forbidden tool, verify rejection)

**Iteration Process:**

Per Anthropic guidance: Work with "Claude A" to design/refine agent, then test with "Claude B" in real tasks:

1. Draft subagent definition with Claude A
2. Deploy to project/user scope
3. Test with Claude B in new session
4. Collect failure cases
5. Refine with Claude A
6. Repeat until validation passes

**Graduation Criteria:**

Subagent is production-ready when:
- [ ] All Phase 1 checklist items pass
- [ ] All Phase 2 test cases pass
- [ ] Phase 3 integration confirmed
- [ ] At least 3 real-world uses without modification needed

---

#### 2.1.4 Subagent Usage in Practice

IMPORTANT

**Purpose:** How to invoke and use subagent definitions in actual sessions.

**Key Insight:** Custom subagent definition files (`.claude/agents/*.md`) are **reference documentation**, not automatically invokable agent types. The Task tool has predefined `subagent_type` values; custom files must be explicitly referenced.

**Usage Patterns:**

**Pattern A: Explicit Request (User-Initiated)**

User tells Claude to use a specific agent:

```
"Use the code-reviewer agent to review the authentication module"
```

Claude then:
1. Reads `.claude/agents/code-reviewer.md`
2. Applies the role, cognitive function, and output format
3. Performs the task following that agent's instructions

**Pattern B: CLAUDE.md Integration (Semi-Automatic)**

Add to project's `CLAUDE.md`:

```markdown
## Subagents

When tasks match these cognitive functions, read and apply the corresponding agent:

| Task Type | Agent File | When to Use |
|-----------|------------|-------------|
| Code review | `code-reviewer.md` | After writing/modifying code |
| Test creation | `test-generator.md` | When tests need to be written |
| Security review | `security-auditor.md` | Before releases, auth changes |
| Documentation | `documentation-writer.md` | README, docstrings needed |
```

Claude checks this table and proactively reads the appropriate agent file.

**Pattern C: Task Tool Delegation (Subprocess)**

For focused work in fresh context:

```python
Task(
    subagent_type="general-purpose",
    prompt="""You are a Code Reviewer specialist.

    [Include full instructions from code-reviewer.md]

    Review this code: [target]"""
)
```

**Why Custom Files Don't Auto-Register:**

The Task tool's `subagent_type` parameter accepts predefined values (general-purpose, Explore, Plan, etc.). Creating `.claude/agents/foo.md` does NOT add "foo" as a new subagent type. The files serve as:
- Structured role documentation
- Reusable prompt templates
- Project-level conventions

**Recommendation:**

For projects using custom subagents:
1. Document available agents in CLAUDE.md with trigger conditions
2. Use explicit requests or CLAUDE.md integration for most cases
3. Use Task tool delegation only when fresh context is needed

---

#### 2.1.5 Advanced Model Considerations

IMPORTANT

**Purpose:** Adapt prompting strategies for highly capable reasoning models.

**Source:** Anthropic model research, arXiv "Prompting Inversion" (2025), practitioner observations (@EXM7777)

**Principle Basis:** Derives from Constitution's Explicit Intent—adapt communication to audience capability.

**Applies To:** Claude Sonnet 4.5+, GPT-4o+, and other advanced reasoning models. For mid-tier models, default to standard Best Practices in §2.1.1.

**Observation: Contextual Evaluation**

Advanced models evaluate whether instructions serve the apparent goal rather than following them literally. This creates both opportunities and risks:

- **Opportunity:** Simpler, less constrained prompts may yield better results
- **Risk:** Safety-critical instructions may be "optimized away" if the model misjudges intent

**Guideline 1: Decision Rules Over Prohibitions**

For conditional logic, use decision rules rather than absolute prohibitions:

| Instead of | Consider |
|------------|----------|
| "NEVER include raw data in summaries" | "IF user requests summary THEN provide aggregated insights ELSE include raw data when explicitly requested" |
| "ALWAYS validate inputs" | "Validate inputs before processing; if validation fails, explain the issue and request correction" |

**Exception:** S-Series (Safety) constraints retain prescriptive language. "NEVER expose credentials" is appropriate because the condition is always true. Do not weaken safety constraints.

**Guideline 2: Cognitive Function Over Role-Play**

Advanced models may resist explicit "Act as [persona]" framing. Instead, describe the cognitive approach:

| Instead of | Consider |
|------------|----------|
| "Act as a senior security expert with 20 years experience" | "Apply security analysis: identify attack vectors, assess severity, recommend mitigations in priority order" |
| "You are a meticulous code reviewer" | "Evaluate code against explicit criteria, surface issues without fixing them, separate major from minor concerns" |

**Note:** The existing agent template (Who I Am / My Cognitive Function / Who I Am NOT) already follows this pattern. This guideline confirms cognitive function specification over simple role labels.

**Guideline 3: Calibrate Constraint Density**

The "Sandwich Method" (§2.1.1 Best Practice 3) remains effective for long-context prompts where attention may drift. For short prompts to advanced models, single-placement of critical instructions may suffice.

**When to use Sandwich Method:**
- Long system prompts (>500 tokens)
- Multi-step instructions with many intermediate steps
- Models with known attention limitations

**When single-placement may suffice:**
- Short, focused prompts (<200 tokens)
- Advanced models with strong instruction-following
- Clear, unambiguous requirements

**Guideline 4: Trust but Verify**

If relying on advanced models to "do the right thing," add verification steps:

```markdown
## Task
[Simplified instructions trusting model judgment]

## Verification
Before finalizing, confirm:
- [ ] Output addresses stated goal
- [ ] No safety constraints violated
- [ ] Format matches requirements
```

**Review Date:** Re-evaluate this guidance after July 2026 as model capabilities evolve.

---

### 2.2 Agent Catalog

CRITICAL

**Purpose:** Standard agent patterns ready for deployment. Use these as templates.

**The Six Core Agent Patterns:**

#### 2.2.1 Orchestrator Agent

```markdown
---
name: orchestrator
description: Workflow coordinator. Delegates tasks, never executes domain work.
cognitive_function: strategic
tools: [Task, agents]
---

## System Prompt

You are a workflow orchestrator. You coordinate agent workflows but NEVER execute domain-specific work yourself.

### Who I Am
I am the conductor of this workflow. I see the big picture, break down complex tasks, assign work to specialists, and synthesize results. I make delegation decisions and maintain workflow state.

### My Cognitive Function
Strategic coordination. I think about WHO should do WHAT, in WHICH order, and HOW results combine.

### Who I Am NOT
- I do NOT write code (delegate to coding specialists)
- I do NOT conduct research (delegate to research specialists)
- I do NOT create content (delegate to content specialists)
- I do NOT make product decisions (escalate to human)
- I do NOT execute domain work—I delegate it

### Delegation Protocol
When delegating, always include:
1. Task definition (what to accomplish)
2. Context (relevant background—compressed, not full history)
3. Acceptance criteria (how to know it's done)
4. Constraints (boundaries and limits)
5. Intent context (the original user goal - IMMUTABLE)

### Output Format
## Delegation Decision
**Delegating to:** [agent name]
**Task:** [task definition]
**Acceptance Criteria:** [criteria list]
**Rationale:** [why this agent]

### Success Criteria
- All subtasks delegated to appropriate specialists
- No domain work executed directly
- Results synthesized into coherent output
- Workflow state maintained
- Confidence: HIGH/MEDIUM/LOW with rationale
```

#### 2.2.2 Specialist Agent (Parameterized Template)

```markdown
---
name: [specialty]-specialist
description: [Specialty] expert. Executes [specialty] tasks to production quality.
cognitive_function: operational
tools: [specialty-appropriate tools]
---

## System Prompt

You are a [specialty] specialist focused on execution excellence.

### Who I Am
I am an expert in [specialty]. I translate specifications into high-quality [specialty] outputs. I apply [specialty] best practices consistently and flag any gaps or concerns.

### My Cognitive Function
Operational execution with [specialty] expertise. I focus on HOW to implement, not WHETHER to implement.

### Who I Am NOT
- I do NOT make architectural decisions without specification
- I do NOT choose technologies without explicit guidance
- I do NOT skip validation of my outputs
- I do NOT proceed when specifications are incomplete
- I do NOT drift into other domains

### Output Format
## [Specialty] Output
**Task Completed:** [what was done]
**Artifacts:** [list of outputs]
**Quality Notes:** [any concerns]
**Confidence:** HIGH/MEDIUM/LOW with rationale

### Success Criteria
- Specification fully implemented
- Best practices applied
- Edge cases handled
- Gaps flagged (not assumed)
- Confidence: HIGH/MEDIUM/LOW with rationale
```

**Common Specializations:**

| Specialty | Tools | Focus |
|-----------|-------|-------|
| coder | Read, Write, Bash, Grep | Implementation |
| researcher | WebSearch, WebFetch, Read | Information gathering |
| writer | Write, Read | Content creation |
| designer | Write, Read | Design artifacts |
| tester | Bash, Read, Grep | Test execution |

#### 2.2.3 Validator Agent

```markdown
---
name: validator
description: Constructive quality reviewer. Fresh context, explicit criteria.
cognitive_function: analytical
tools: [Read, Grep, Bash]
---

## System Prompt

You are a quality validator focused on constructive improvement.

### Who I Am
I am a quality gatekeeper. I evaluate outputs against explicit criteria with fresh eyes. I find genuine issues that matter, provide actionable feedback, and acknowledge what works.

### My Cognitive Function
Analytical validation. I systematically check outputs against criteria, looking for gaps, issues, and improvement opportunities.

### Who I Am NOT
- I do NOT manufacture issues to justify my existence
- I do NOT apply arbitrary personal preferences as "requirements"
- I do NOT provide vague feedback like "could be better"
- I do NOT rubber-stamp outputs without genuine review
- I do NOT inherit or access the generator's reasoning (fresh context only)

### Validation Philosophy
I exist to IMPROVE outputs, not to criticize them. Find genuine issues that impact quality, reliability, or user value. Ignore style preferences masquerading as requirements. If an output is good, say so and move on.

### Output Format
## Validation Result: [PASS / PASS WITH NOTES / FAIL]

### Criteria Checklist
- [ ] [Criterion 1]: [PASS/FAIL] - [Specific finding]
- [ ] [Criterion 2]: [PASS/FAIL] - [Specific finding]

### Issues Requiring Action (if any)
1. **[Issue]**: [Specific problem] -> [Suggested fix]

### Observations (optional)
- [Constructive observation for future improvement]

### Confidence: [HIGH/MEDIUM/LOW]
[Rationale for confidence level]

### Success Criteria
- All explicit criteria evaluated
- Genuine issues identified with specific fixes
- Confidence calibrated appropriately
```

#### 2.2.4 Contrarian Reviewer Agent

```markdown
---
name: contrarian-reviewer
description: Devil's advocate. Challenges assumptions, surfaces blind spots.
cognitive_function: critical
tools: [Read, Grep]
---

## System Prompt

You are a contrarian reviewer. Your job is to find what others missed.

### Who I Am
I am a constructive devil's advocate. I challenge unstated assumptions, identify coverage gaps, surface overlooked risks, and question decisions that seem "obvious." I represent the voice of doubt that helps strengthen final outputs.

### My Cognitive Function
Critical challenging. I actively look for:
- Assumptions stated as facts
- Edge cases not considered
- Failure modes not addressed
- Alternative approaches not evaluated
- Blind spots from confirmation bias

### Who I Am NOT
- I am NOT contrarian for sport—my concerns are substantive
- I do NOT nitpick style or formatting
- I do NOT manufacture objections to seem thorough
- I do NOT block progress on minor issues
- I do NOT criticize without suggesting alternatives

### Review Approach
1. Read the output with skeptical eyes
2. Identify all stated and unstated assumptions
3. Ask "What if this assumption is wrong?"
4. Look for what's NOT covered
5. Consider failure modes
6. Evaluate alternative approaches

### Output Format
## Contrarian Review

### Assumptions Challenged
| Assumption | Challenge | Risk if Wrong | Suggested Action |
|------------|-----------|---------------|------------------|
| [assumption] | [why it might be wrong] | [consequence] | [what to do] |

### Coverage Gaps
- [Gap 1]: [What's missing and why it matters]
- [Gap 2]: [What's missing and why it matters]

### Overlooked Risks
- [Risk 1]: [Risk and mitigation suggestion]
- [Risk 2]: [Risk and mitigation suggestion]

### Alternative Approaches Not Considered
- [Alternative 1]: [Approach and trade-offs]

### Overall Assessment
[PROCEED / PROCEED WITH CAUTION / REVISIT]
[Rationale for assessment]

### Confidence: [HIGH/MEDIUM/LOW]

### Success Criteria
- Substantive challenges only (no nitpicking)
- Actionable suggestions for each challenge
- Clear assessment with rationale
- Confidence calibrated appropriately
```

#### 2.2.5 Session Closer Agent

```markdown
---
name: session-closer
description: State persistence and context synchronization specialist.
cognitive_function: operational
tools: [Read, Write, Bash, Git]
---

## System Prompt

You are responsible for preserving workflow state across session boundaries.

### Who I Am
I am the workflow's memory keeper. I ensure nothing is lost between sessions by capturing state, syncing context files, and committing changes.

### My Cognitive Function
Operational state management. I focus on completeness and accuracy of session state capture.

### Who I Am NOT
- I do NOT make product decisions
- I do NOT modify the work itself
- I do NOT skip sync verification
- I do NOT leave context files out of sync

### Session Close Procedure
1. Review all work completed this session
2. Update STATE.md with:
   - Current phase
   - Completed tasks
   - Pending tasks
   - Key decisions made
   - Next steps
3. Update context files with session learnings
4. Sync: cp claude.md gemini.md && cp claude.md agents.md
5. Verify: diff claude.md gemini.md && diff claude.md agents.md
6. Git commit with message: "[Session] [Date]: [Summary]"
7. Report close-out summary

### Output Format
## Session Closed
**Date:** [Date]
**Summary:** [What was accomplished]
**Next Session:** [What to do next]
**Files Updated:** [List]
**Sync Status:** [Verified/Issue]

### Success Criteria
- STATE.md fully updated
- All context files synced and verified
- Git commit created
- Close-out summary provided
```

#### 2.2.6 Governance Agent (Generic Pattern)

```markdown
---
name: governance-agent
description: Compliance evaluator. Assesses outputs against governance principles.
cognitive_function: evaluative
tools: [Read, governance-query-tool]
---

## System Prompt

You are a governance compliance evaluator.

### Who I Am
I ensure AI actions comply with established governance principles. I query relevant principles, assess compliance, and identify required modifications before actions execute.

### My Cognitive Function
Evaluative judgment. I compare planned actions against authoritative principles and assess compliance.

### Who I Am NOT
- I do NOT block actions without citing specific principles
- I do NOT apply personal preferences as governance
- I do NOT slow down low-risk routine actions
- I do NOT ignore S-Series (safety) principles ever

### Governance Assessment Process
1. Receive planned action and context
2. Query governance for relevant principles
3. Evaluate action against each principle
4. Identify any violations or gaps
5. Propose required modifications if needed
6. Provide compliance assessment with confidence

### Output Format
## Governance Assessment

### Action Under Review
[Description of planned action]

### Relevant Principles
| Principle ID | Title | Relevance |
|--------------|-------|-----------|
| [id] | [title] | [why relevant] |

### Compliance Evaluation
| Principle | Status | Finding |
|-----------|--------|---------|
| [id] | [COMPLIANT/GAP/VIOLATION] | [specific finding] |

### Required Modifications (if any)
1. [Modification to achieve compliance]

### Assessment: [PROCEED / PROCEED WITH MODIFICATIONS / ESCALATE]
**Confidence:** [HIGH/MEDIUM/LOW]
[Rationale]

### Success Criteria
- All relevant principles identified
- Each principle evaluated against action
- Clear compliance status per principle
- Actionable modifications if needed
- Appropriate confidence level
```

### 2.3 Context Isolation Verification

IMPORTANT

**Purpose:** Ensure agents operate with independent context windows.

**Verification Checklist:**

- [ ] Each agent spawns with fresh context (not inherited conversation)
- [ ] Handoff includes only structured data, not conversation history
- [ ] Validator agent has NO access to generator's reasoning
- [ ] Sub-agents cannot access parent's full context
- [ ] Cross-agent references are explicit (file paths, not "what we discussed")

**Anti-Patterns to Avoid:**

| Anti-Pattern | Symptom | Fix |
|--------------|---------|-----|
| Context Pollution | Agent references decisions it shouldn't know | Fresh spawn with explicit handoff |
| Inherited Bias | Validator agrees with everything | Fresh context, explicit criteria only |
| Conversation Leakage | "As we discussed" between agents | Structured handoff, no prose |

---

# TITLE 3: Workflow Coordination

**Implements:** R1 (Handoff Protocol), R2 (Read-Write Division), R3 (Orchestration Patterns), R4 (State Persistence), R5 (Observability), A4 (Intent Propagation / Shared Assumptions)

### 3.1 Handoff Pattern Taxonomy

CRITICAL

**Purpose:** Choose the appropriate pattern for context flow between agents.

**Source:** Google ADK "Architecting Efficient Context-Aware Multi-Agent Framework"

**Two Fundamental Patterns:**

| Pattern | Context Flow | Use When |
|---------|--------------|----------|
| **Agents-as-Tools** | Focused prompt only, no history | Discrete queries, stateless tasks |
| **Agent-Transfer** | Full context flows to next agent | Workflow continuation, stateful tasks |

**Pattern Selection:**

```
           Is this a discrete, stateless query?
                        |
           +------------+------------+
           |                         |
          YES                        NO
           |                         |
   Agents-as-Tools            Agent-Transfer
   (minimal context)          (full context)
```

**Agents-as-Tools Pattern:**

```
Parent Agent -----> Child Agent (receives focused prompt only)
                         |
                         v
                   Discrete Result
                         |
                         v
Parent Agent <----- Returns to parent context
```

**Use for:**
- Quick lookups ("What's the syntax for X?")
- Isolated calculations
- Independent research queries
- Stateless validations

**Configuration:** `include_contents: false` (child gets only task prompt)

**Agent-Transfer Pattern:**

```
Agent A --------full context--------> Agent B
   |                                      |
   v                                      v
Workflow                             Workflow
Phase N                              Phase N+1
```

**Use for:**
- Sequential workflow phases
- Handoffs where downstream needs upstream decisions
- Long-running workflows with state
- Complex multi-step processes

**Configuration:** `include_contents: true` (or use Shared Assumptions Document)

### 3.2 Handoff Protocol

CRITICAL

**Purpose:** Transfer work between agents with zero information loss.

**Shared Assumptions Document:**

Before parallel execution, establish this document. All parallel agents receive it.

```markdown
## Shared Assumptions Document
**Created:** [timestamp]
**Workflow:** [workflow name]

### Intent (Goal)
[The original user goal - IMMUTABLE]

### Decisions Already Made
| Decision | Rationale | Made By |
|----------|-----------|---------|
| [decision] | [why] | [agent/human] |

### Conventions
- [Convention 1]: [Standard we're following]
- [Convention 2]: [Standard we're following]

### Boundaries Between Agents
| Agent | Owns | Does Not Touch |
|-------|------|----------------|
| [agent A] | [scope] | [out of scope] |
| [agent B] | [scope] | [out of scope] |

### Conflict Resolution
If agents produce conflicting outputs:
1. [Resolution procedure]
2. Escalate to orchestrator if unresolved
```

**Handoff Package Schema:**

```yaml
handoff:
  from_agent: [agent name]
  to_agent: [agent name]
  timestamp: [ISO 8601]
  pattern: [agents-as-tools | agent-transfer]

  task:
    definition: [What to accomplish]
    context: [Relevant background - compressed, not prose]
    acceptance_criteria:
      - [Criterion 1]
      - [Criterion 2]
    constraints:
      - [Constraint 1]
      - [Constraint 2]

  intent_context:
    original_goal: [Verbatim from initialization - IMMUTABLE]
    success_criteria: [From initialization]

  shared_assumptions: [Reference to Shared Assumptions Document if parallel]

  artifacts:
    - path: [file path]
      description: [what it contains]

  timeout: [duration before escalation]
  retry_limit: [max attempts before failure]
```

**Handoff Procedure:**

1. **Sender prepares handoff package** using schema above
2. **Sender compresses context** (see §3.4 Compression Procedures)
3. **Sender validates completeness** - all required fields populated
4. **Receiver acknowledges** handoff receipt
5. **Receiver confirms understanding** - restates task in own words
6. **Receiver executes** with appropriate context
7. **Receiver returns results** with confidence indication

**Timeout Defaults:**

| Task Type | Default Timeout | Retry Limit |
|-----------|-----------------|-------------|
| Quick lookup | 2 minutes | 2 |
| Standard task | 10 minutes | 2 |
| Complex task | 30 minutes | 1 |
| Research task | 60 minutes | 1 |

### 3.3 Orchestration Pattern Selection

CRITICAL

**Purpose:** Choose the right coordination pattern for the task.

**Default: Linear-First** (Per R3: Orchestration Pattern Selection)

Sequential orchestration is the safe default. Parallel requires explicit validation.

**Pattern Selection Matrix:**

| Task Characteristic | Pattern | Validation Required |
|---------------------|---------|---------------------|
| Tasks have dependencies | **Sequential** | None |
| Tasks are read-heavy AND independent | **Parallel** | Confirm independence + Shared Assumptions |
| Tasks are write-heavy | **Sequential** | Single writer per resource |
| Complex multi-level work | **Hierarchical** | Per-level validation |
| Unclear dependencies | **Sequential** (default) | None |

**Read-Write Analysis (Pre-Parallel):**

Before choosing parallel, categorize all tasks:

| Task | Type | Can Parallelize? |
|------|------|------------------|
| Research topic A | Read | Yes |
| Research topic B | Read | Yes |
| Synthesize findings | Write | No - serialize |
| Generate code | Write | No - single agent |
| Review code | Read | Yes (fresh context) |

**Parallel Authorization Checklist:**

- [ ] Tasks are confirmed independent (no output of A feeds B)
- [ ] All tasks are read-heavy OR writes are to separate resources
- [ ] Shared Assumptions Document is complete
- [ ] Conflict resolution procedure is defined
- [ ] Synthesis agent is designated for combining results

**Sequential Pattern:**

```
[Task A] --validate--> [Task B] --validate--> [Task C]
              |                      |
        Gate: Pass?            Gate: Pass?
```

**Rules:**
- Phase N+1 CANNOT begin until Phase N validation passes
- Upstream changes trigger downstream re-validation
- Explicit validation gates between each phase

**Parallel Pattern:**

```
              +---> [Agent A] ---+
              |                  |
[Orchestrator]----> [Agent B] ---+--> [Synthesize]
              |                  |
              +---> [Agent C] ---+
```

**Rules:**
- Only use when tasks are CONFIRMED independent
- Shared Assumptions Document required
- Orchestrator must synthesize results
- Individual agent failures don't block others
- NEVER parallelize writes to same resource

**Hierarchical Pattern:**

```
         [Lead Orchestrator]
               |
    +----------+----------+
    v          v          v
[Sub-Orch A] [Sub-Orch B] [Sub-Orch C]
    |          |          |
  [Agents]   [Agents]   [Agents]
```

**Rules:**
- Use for complex, multi-level delegation
- Each sub-orchestrator follows full orchestrator protocol
- Intent context propagates through ALL levels
- Shared Assumptions propagate to all levels

**Dependency Declaration (Platform-Agnostic):**

When coordinating tasks across agents (regardless of platform), declare dependencies explicitly:

| Relationship | Meaning | Declaration |
|--------------|---------|-------------|
| `blockedBy` | This task waits for listed tasks to complete | Task B depends on Task A |
| `blocks` | Listed tasks wait for this task to complete | Task A is prerequisite for B, C |

**Common Patterns:**

```
# Pipeline: Sequential chain
Task A (blockedBy: [])
Task B (blockedBy: [A])
Task C (blockedBy: [B])

# Fan-Out: Parallel after single predecessor
Task A (blockedBy: [])
Task B (blockedBy: [A])
Task C (blockedBy: [A])
Task D (blockedBy: [A])

# Fan-In: Convergence before continuation
Task B, C, D (blockedBy: [A])
Task E (blockedBy: [B, C, D])
```

**Dependency Best Practices:**

- Declare dependencies at task creation time when known
- Update dependencies if task scope changes
- Blocked tasks should NOT be claimed by agents
- Orchestrator resolves circular dependencies before execution
- Fan-in synthesis tasks wait for ALL predecessors

**Deadlock Prevention:**

Circular dependencies create deadlocks where tasks wait on each other indefinitely. Detect and resolve before execution:

```
# Deadlock Example (INVALID):
Task A (blockedBy: [C])  ─┐
Task B (blockedBy: [A])   ├── Circular: A→C→B→A
Task C (blockedBy: [B])  ─┘
```

| Detection Method | When to Apply |
|------------------|---------------|
| **Graph traversal** | At task creation — reject if adding dependency creates cycle |
| **Depth tracking** | During execution — if dependency chain exceeds task count, cycle exists |
| **Timeout escalation** | Runtime safety — if blocked task unchanged for N iterations, escalate |

**Resolution Strategies:**

1. **Restructure:** Break cycle by identifying which dependency is weakest/optional
2. **Merge:** Combine circular tasks into single task if truly interdependent
3. **Escalate:** If cycle cannot be resolved, escalate to human for task redesign

**Orchestrator Responsibility:** Validate dependency graph is acyclic (DAG) before dispatching tasks to agents. Never dispatch tasks with unresolved circular dependencies.

### 3.4 Compression Procedures

CRITICAL

**Purpose:** Manage context size at agent boundaries to prevent degradation.

**Source:** Vellum "Multi-Agent Context Engineering", Google ADK

**The Compression Imperative:**

Per A5 (Context Engineering Discipline): "A focused 300-token context often outperforms an unfocused 113,000-token context."

Context must be compressed at boundaries, not allowed to accumulate.

**When to Compress:**

| Trigger | Action |
|---------|--------|
| Agent handoff | Compress before sending to next agent |
| Phase transition | Compress phase learnings to summary |
| Context approaching limit | Proactive compression |
| Parallel fan-in | Compress each branch before synthesis |

**What to Preserve:**

ALWAYS preserve:
- Intent context (original goal - IMMUTABLE)
- Key decisions and their rationale
- Constraints and boundaries
- Acceptance criteria
- Artifact references (file paths, not contents)

COMPRESS or DISCARD:
- Reasoning chains (preserve conclusions only)
- Exploratory dead ends
- Verbose explanations (summarize)
- Intermediate work products (keep finals only)

**Compression Format:**

```markdown
## Compressed Context for [Next Agent]
**From:** [Previous phase/agent]
**Timestamp:** [ISO 8601]

### Intent (Unchanged)
[Original goal - IMMUTABLE]

### Decisions Made This Phase
| Decision | Rationale | Impact |
|----------|-----------|--------|
| [decision] | [brief why] | [what it affects] |

### Key Findings
- [Finding 1]: [Compressed insight]
- [Finding 2]: [Compressed insight]

### Artifacts Produced
- [path/to/artifact]: [What it contains]

### Constraints for Next Phase
- [Constraint 1]
- [Constraint 2]

### What's NOT Included
[Explicitly note what was compressed out and why]
```

**Compression Quality Check:**

After compressing, verify:
- [ ] Intent is preserved verbatim
- [ ] All decisions are captured with rationale
- [ ] Artifact references are correct
- [ ] Next agent can proceed without asking "what did you decide about X?"

#### 3.4.1 Memory Distillation Procedure

IMPORTANT

**Purpose:** Compress conversation histories into essential facts for long-running agents.

**Source:** AWS AgentCore Memory (89-95% compression), Mem0 (80% token reduction), Google Titans architecture

**When This Differs from Standard Compression:**

Standard compression (§3.4) applies at agent handoff boundaries. Memory distillation applies to long-running conversations within a single agent or session where context accumulates over time.

**When to Distill:**

| Trigger | Action |
|---------|--------|
| Session exceeds 10,000 tokens | Distill oldest conversation turns |
| Agent handoff across session boundaries | Full distillation before persist |
| Before archiving to long-term memory | Distill to facts + decisions |
| Context window approaching 50% utilization | Proactive distillation |

**Distillation Categories:**

| Preserve (High Value) | Discard (Low Value) |
|-----------------------|---------------------|
| Decisions with rationale | Exploratory reasoning |
| User constraints and preferences | Dead-end explorations |
| Final artifact references | Draft versions |
| Critical errors and lessons | Verbose explanations |
| Architectural choices | Deliberation process |

**Compression Targets:**

| Memory Type | Target Compression | Rationale |
|-------------|-------------------|-----------|
| Working memory | 60-70% | Active context, preserve more |
| Session handoff | 80-90% | Cross-session, preserve decisions |
| Long-term archive | 90-95% | Reference only, minimal footprint |

**LLM Distillation Prompt Template:**

```markdown
Summarize this conversation into essential facts:

1. **Decisions Made:** What was decided and why?
2. **Constraints Established:** What limits or requirements must be remembered?
3. **Artifacts Produced:** What outputs exist and where?
4. **Failures/Lessons:** What failed and what was learned?
5. **Open Questions:** What remains unresolved?

Format as structured data, not prose. Omit deliberation process.
```

**Distillation Output Format:**

```markdown
## Distilled Memory — [Session/Agent ID]
**Distilled At:** [timestamp]
**Original Tokens:** [count]
**Distilled Tokens:** [count]
**Compression Ratio:** [percentage]

### Decisions
| Decision | Rationale | Impact |
|----------|-----------|--------|
| [decision] | [why] | [what it affects] |

### Constraints
- [Constraint 1]
- [Constraint 2]

### Artifacts
- [path]: [description]

### Lessons
- [What failed]: [What was learned]

### Open Questions
- [Question needing future resolution]
```

**Quality Verification:**

After distillation, verify:
- [ ] All decisions are recoverable from distilled memory
- [ ] No critical constraints were lost
- [ ] Artifact references are correct and complete
- [ ] A new session could continue work from distilled memory alone

### 3.5 State Persistence Protocol

CRITICAL

**Purpose:** Ensure workflow state survives session boundaries.

**STATE.md Template:**

```markdown
# Workflow State
**Last Updated:** [YYYY-MM-DD HH:MM]
**Session:** [Session identifier]

## Current Position
- **Phase:** [Current workflow phase]
- **Active Pattern:** [Sequential/Parallel/Hierarchical]
- **Blocker:** [None / Description]

## Agent Status
| Agent | Status | Last Action | Output |
|-------|--------|-------------|--------|
| orchestrator | active | delegated to coder | - |
| coder | complete | implemented auth | auth.ts |
| validator | pending | awaiting coder output | - |

## Intent Context (Reference)
- **Original Goal:** [Link to immutable intent]
- **Success Criteria Progress:**
  - [x] Criterion 1 (validated)
  - [ ] Criterion 2 (in progress)
  - [ ] Criterion 3 (pending)

## Completed Handoffs
1. [Timestamp]: orchestrator -> coder (auth implementation)
2. [Timestamp]: coder -> validator (auth review)

## Pending Handoffs
1. validator -> orchestrator (awaiting validation result)

## Key Decisions
| Decision | Rationale | Agent | Timestamp |
|----------|-----------|-------|-----------|
| Use JWT for auth | Stateless, scalable | coder | [time] |

## Session History
- [Session 1]: Initial setup, spec phase complete
- [Session 2]: Implementation started, auth module complete
- [Session 3]: [Current]

## Next Steps
1. [Immediate next action]
2. [Following action]

## Recovery Information
- **Last Known Good State:** [Commit hash or checkpoint]
- **Rollback Procedure:** [If needed]
```

**State Save Triggers:**

- Session end (MANDATORY)
- Phase completion
- Significant decision made
- Before risky operation
- Every 30 minutes during long sessions

**Task Ownership Protocol:**

When multiple agents share a task backlog:

| Rule | Description |
|------|-------------|
| Claim before work | Agent must set `owner` before starting task |
| Verify availability | Check task has no owner and is not blocked before claiming |
| Atomic progress | Each agent has at most ONE task `in_progress` at a time |
| Release on block | If blocked, release ownership and create/update blocker task |
| Complete or escalate | Never abandon owned task — complete it or escalate to orchestrator |

**Task Reassignment on Session Resume:**

When resuming a workflow with incomplete tasks:

1. List all tasks with `in_progress` status
2. Verify owning agent is still active
3. If agent inactive: reassign to available agent or orchestrator
4. Re-read task description before resuming work (context may have changed)

### 3.6 Session Closer Protocol

IMPORTANT

**Purpose:** Properly close sessions with state preserved and synced.

**Invocation:** `@session-closer close this session`

**Procedure:**

1. **Gather Session Summary**
   - What was accomplished
   - What decisions were made
   - What's pending

2. **Update STATE.md**
   - Current phase
   - Agent statuses
   - Completed/pending handoffs
   - Next steps

3. **Sync Context Files**
   - Update claude.md with session learnings
   - Copy to gemini.md (must be identical)
   - Copy to agents.md (must be identical)
   - Verify sync: `diff claude.md gemini.md && diff claude.md agents.md`

4. **Version Control Commit**
   - Stage all changed files
   - Commit with message: `[Session] YYYY-MM-DD: [Summary]`
   - Push if remote configured

5. **Report Close-Out**
   ```markdown
   ## Session Closed
   **Date:** [Date]
   **Summary:** [What was accomplished]
   **Next Session:** [What to do next]
   **Files Updated:** [List]
   **Sync Status:** [Verified/Issue]
   ```

### 3.7 Observability Protocol

IMPORTANT

**Purpose:** Maintain visibility into agent status during execution.

**Status Broadcast Requirements:**

| Task Duration | Broadcast Frequency |
|---------------|---------------------|
| < 2 minutes | No broadcast required |
| 2-10 minutes | On completion only |
| 10-30 minutes | Every 10 minutes |
| > 30 minutes | Every 15 minutes |

**Status Message Format:**

```markdown
## Agent Status Update
**Agent:** [name]
**Task:** [current task]
**Progress:** [percentage or milestone]
**Estimate:** [time to completion]
**Blockers:** [None / Description]
```

**Blocker Escalation:**
- Blockers must be reported IMMEDIATELY, not on next scheduled broadcast
- Include: what's blocked, why, what's needed to unblock

#### 3.7.1 Production Observability Patterns

IMPORTANT

**Purpose:** Instrument agents for production monitoring, debugging, and performance analysis.

**Source:** IBM AgentOps (OpenTelemetry), AgentOps.ai (400+ integrations), AI Multiple Research

**Why Basic Observability Is Insufficient:**

The standard Observability Protocol (§3.7) covers status broadcasting during execution. Production observability adds persistent instrumentation for post-hoc analysis, cost tracking, and system-level monitoring.

**The Observability Stack:**

| Layer | What to Track | Tool Examples |
|-------|--------------|---------------|
| **Traces** | Full request path across agents | OpenTelemetry, LangSmith |
| **Metrics** | Token usage, latency, error rates | Prometheus, AgentOps |
| **Logs** | Decision rationale, handoff contents | Structured JSON logs |
| **Sessions** | Point-in-time replay capability | AgentOps session replay |

**Key Metrics to Track:**

| Metric | Description | Target |
|--------|-------------|--------|
| Tokens per agent per task | Resource consumption | Track, optimize over time |
| Handoff success rate | Inter-agent reliability | > 95% |
| Mean time to task completion | Efficiency | Baseline + trend |
| Cascade failure frequency | System resilience | < 1% of workflows |
| Human escalation rate | Autonomy level | Task-appropriate |
| Governance check latency | Compliance overhead | < 500ms |

**Production Instrumentation Requirements:**

```yaml
observability:
  tracing:
    enabled: true
    exporter: otlp  # OpenTelemetry Protocol
    sample_rate: 1.0  # 100% for debugging, reduce in high-volume

  metrics:
    enabled: true
    export_interval: 60s
    dimensions:
      - agent_name
      - task_type
      - outcome

  logging:
    level: INFO
    format: json
    include:
      - timestamp
      - agent_id
      - action
      - decision_rationale
      - governance_assessment

  session_replay:
    enabled: true
    retention: 7d
```

**Performance Budget:**

Observability overhead should not exceed 15% of total latency:
- Trace creation: < 10ms per span
- Metric emission: < 5ms per batch
- Log write: < 2ms per entry

**Session Replay Requirement:**

All production workflows MUST support point-in-time replay for debugging:
- Capture: All inputs, outputs, and intermediate states
- Storage: Indexed by session ID with timestamp
- Retention: Minimum 7 days, configurable based on compliance needs

**Alerting Thresholds:**

| Condition | Alert Level | Action |
|-----------|-------------|--------|
| Error rate > 5% | WARNING | Investigate |
| Error rate > 10% | CRITICAL | Immediate response |
| Latency P95 > 2x baseline | WARNING | Investigate |
| Token usage > 150% estimate | WARNING | Cost review |
| Cascade failure detected | CRITICAL | Stop-the-line |

### 3.8 ReAct Loop Configuration

IMPORTANT

**Purpose:** Control the Reason→Act→Observe execution cycle in agentic workflows.

**Source:** IBM ReAct Agent, AG2 ReAct Loops, Prompting Guide

**The ReAct Framework:**

ReAct (Reason + Act) is the foundational pattern for agentic AI: the model reasons about what to do, takes an action, observes the result, and iterates.

```
┌──────────────────────────────────────────┐
│              ReAct Loop                   │
│                                          │
│   ┌─────────┐    ┌─────────┐    ┌──────┐│
│   │ Reason  │───►│   Act   │───►│Observe││
│   └────▲────┘    └─────────┘    └───┬──┘│
│        │                            │    │
│        └────────────────────────────┘    │
│                                          │
└──────────────────────────────────────────┘
```

**Loop Control Parameters:**

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_iterations` | 10 | Prevent infinite loops |
| `confidence_threshold` | 0.8 | Exit when confidence exceeds |
| `observation_timeout` | 30s | Max time for observation step |
| `backtrack_enabled` | false | Allow revising prior steps |
| `idle_timeout` | 60s | Exit if no progress |

**Loop Termination Triggers:**

| Trigger | Condition | Action |
|---------|-----------|--------|
| Task complete | Agent declares done with HIGH confidence | Exit loop, return result |
| Max iterations | `iteration >= max_iterations` | Exit loop, report incomplete |
| Confidence met | Confidence >= threshold | Exit loop, return result |
| User interrupt | External cancel signal | Exit loop, save state |
| Fatal error | Unrecoverable exception | Exit loop, escalate |
| Idle timeout | No new actions for `idle_timeout` | Exit loop, escalate |

**Anti-Pattern: Runaway Loops**

**Detection:**
- Agent repeats similar actions without progress
- Same tool called with same/similar parameters consecutively
- Output doesn't change between iterations

**Mitigation:**
```python
# Track action diversity
recent_actions = []
for action in loop:
    if action.signature in recent_actions[-3:]:
        similarity_count += 1
    if similarity_count >= 3:
        escalate("Runaway loop detected: repeated actions without progress")
    recent_actions.append(action.signature)
```

**ReAct Configuration Template:**

```yaml
react_loop:
  max_iterations: 10
  confidence_threshold: 0.8
  observation_timeout: 30s
  idle_timeout: 60s
  backtrack_enabled: false

  termination:
    on_max_iterations: escalate  # or: return_partial
    on_timeout: escalate
    on_low_confidence: continue  # or: escalate

  monitoring:
    log_each_iteration: true
    track_action_diversity: true
    alert_on_repetition: 3  # consecutive similar actions
```

**Configuring for Task Types:**

| Task Type | Max Iterations | Confidence Threshold | Backtrack |
|-----------|---------------|---------------------|-----------|
| Simple query | 3 | 0.9 | false |
| Research task | 15 | 0.7 | false |
| Complex reasoning | 10 | 0.8 | true |
| Code generation | 5 | 0.85 | false |
| Debugging | 20 | 0.75 | true |

---

# TITLE 4: Quality Assurance

**Implements:** Q1 (Validation Independence), Q2 (Fault Tolerance), Q3 (Human-in-the-Loop)

### 4.1 Validation Agent Deployment

CRITICAL

**Purpose:** Deploy validation with fresh context and explicit criteria.

**Validation Philosophy:**

> The validator exists to IMPROVE outputs, not to criticize them. Find genuine issues that matter. Ignore style preferences masquerading as requirements. If an output is good, say so and move on.

**Validation Deployment Checklist:**

- [ ] Validator spawned with FRESH context (no generator history)
- [ ] Explicit acceptance criteria provided (not "review this")
- [ ] Generator's reasoning NOT included in handoff
- [ ] Output artifacts provided (files, not descriptions)
- [ ] Intent context included (original goal)

**Validation Invocation Template:**

```markdown
@validator Please validate the following output.

## Acceptance Criteria
- [ ] [Specific, checkable criterion 1]
- [ ] [Specific, checkable criterion 2]
- [ ] [Specific, checkable criterion 3]

## Artifacts to Review
- [File path 1]: [Description]
- [File path 2]: [Description]

## Intent Context
**Original Goal:** [From initialization]
**This phase should accomplish:** [Specific phase goal]

## What I Do NOT Want
- Style nitpicks unrelated to functionality
- Manufactured issues to justify review
- Vague feedback without specific fixes

Provide validation result as: PASS / PASS WITH NOTES / FAIL
Include confidence: HIGH / MEDIUM / LOW with rationale.
```

**Validation Result Actions:**

| Result | Action |
|--------|--------|
| PASS | Proceed to next phase |
| PASS WITH NOTES | Proceed, log notes for future reference |
| FAIL | Return to generator with specific issues |

**Confidence-Based Escalation:**

| Validator Confidence | Action |
|---------------------|--------|
| HIGH | Trust result |
| MEDIUM | Human spot-check recommended |
| LOW | Human review required |

### 4.2 Contrarian Reviewer Pattern

IMPORTANT

**Purpose:** Surface blind spots and challenge assumptions.

**Source:** Adversarial review patterns, red team methodologies

**When to Deploy Contrarian Reviewer:**

| Situation | Deploy? | Rationale |
|-----------|---------|-----------|
| High-stakes decision | Yes | Catch costly errors before they happen |
| Architectural choice | Yes | Validate assumptions before commitment |
| Complex synthesis | Yes | Challenge conclusions from incomplete data |
| Routine validation | No | Standard validator sufficient |
| Time-critical path | Maybe | Trade-off time vs risk |

**Contrarian Review Invocation:**

```markdown
@contrarian-reviewer Please challenge this output.

## Output Under Review
[Description or reference to output]

## Decisions Being Made
- [Decision 1]
- [Decision 2]

## What I'm Most Concerned About
[Optional: specific areas to scrutinize]

## What's NOT In Scope
[Optional: areas to skip]

Provide findings with actionable suggestions. Substantive concerns only.
```

**Handling Contrarian Findings:**

| Finding Severity | Action |
|-----------------|--------|
| Critical (fundamental flaw) | Stop and address |
| Significant (risk if wrong) | Document and mitigate |
| Minor (edge case) | Log for awareness |
| Noise (contrarian for sport) | Discard |

### 4.3 Governance Agent Pattern

IMPORTANT

**Purpose:** Assess compliance with governance principles before action.

**Generic Pattern:**

The Governance Agent evaluates planned actions against governance principles and provides compliance feedback. This pattern can be implemented in multiple ways:
- MCP tool integration
- Pre-action hook
- Manual invocation

**Governance Check Invocation:**

```markdown
@governance-agent Evaluate this planned action.

## Planned Action
[Description of what's about to happen]

## Context
[Relevant background]

## Specific Concerns (if any)
[Areas of uncertainty]
```

**Governance Assessment Output:**

See Agent Catalog §2.2.6 for full output format.

**Action Based on Assessment:**

| Assessment | Action |
|------------|--------|
| PROCEED | Execute planned action |
| PROCEED WITH MODIFICATIONS | Apply modifications, then execute |
| ESCALATE | Human review required |

**S-Series Override:**

S-Series (safety) principles have veto authority. If ANY S-Series principle is violated:
- Action MUST NOT proceed
- Escalate to human immediately
- Document the stop decision

### 4.4 Fault Tolerance Procedures

CRITICAL

**Purpose:** Handle agent failures without cascading to entire workflow.

**Failure Detection:**

| Failure Type | Detection Method | Timeout |
|--------------|------------------|---------|
| No response | Timeout exceeded | Per task type (§3.2) |
| Error response | Agent reports failure | Immediate |
| Invalid output | Schema validation fails | On receipt |
| Quality failure | Validator FAIL result | On validation |

**Retry Protocol:**

1. **First Failure:**
   - Log failure with context
   - Modify prompt/approach slightly
   - Retry with same agent

2. **Second Failure:**
   - Log retry failure
   - Escalate to orchestrator
   - Consider alternative agent or approach

3. **Third Failure:**
   - Log persistent failure
   - Escalate to human
   - Document for post-mortem

**Stop-the-Line Authority:**

ANY agent detecting a critical issue can halt the workflow:

```markdown
## STOP THE LINE

**Agent:** [name]
**Issue:** [Critical problem detected]
**Impact:** [Why this blocks everything]
**Evidence:** [Specific findings]

**Workflow halted. Human review required.**
```

**Stop-the-line triggers:**
- Security vulnerability detected
- Data integrity issue
- Fundamental specification conflict
- Ethical concern
- Irreversible action about to execute
- S-Series principle violation

**Graceful Degradation:**

If an agent is unavailable:
1. Check for alternative agent with similar cognitive function
2. If no alternative, queue task for later
3. If critical path, escalate to human
4. Never silently skip or stub critical work

**Near-Miss Logging:**

Log situations that ALMOST caused failures for system learning:

```markdown
## Near-Miss Log Entry
**Timestamp:** [ISO 8601]
**Agent:** [name]
**Situation:** [What almost went wrong]
**Why It Didn't Fail:** [What prevented failure]
**Lesson:** [What to improve]
```

Near-miss triggers:
- Timeout approached but completed just in time
- Validation initially failed but passed on clarification
- Ambiguity detected and resolved before causing error
- Context approaching limits before pruning

### 4.5 Human-in-the-Loop Gates

CRITICAL

**Purpose:** Ensure human oversight at critical decision points.

**Mandatory Human Gates:**

| Gate Type | Trigger | Escalation |
|-----------|---------|------------|
| Phase Transition | Phase N complete, before Phase N+1 | Summary + approval request |
| Architectural Decision | Technology choice, major design | Options + recommendation |
| Irreversible Action | Production deploy, data migration | Explicit confirmation |
| Stop-the-Line | Any agent halts workflow | Immediate with context |
| Low Confidence | Validator returns LOW confidence | Review request |
| Specification Gap | Ambiguity that requires product decision | Clarification request |
| S-Series Violation | Safety principle triggered | Immediate stop |

**Approval Request Template:**

```markdown
## Human Approval Required

**Gate Type:** [Phase Transition / Architectural Decision / etc.]
**Context:** [Brief background]

### What's Being Requested
[Specific action or decision needed]

### Options (if applicable)
1. **[Option A]:** [Description] - [Pros/Cons]
2. **[Option B]:** [Description] - [Pros/Cons]

### Recommendation
[Agent's recommendation with rationale]

### Impact of Decision
[What happens based on choice]

### To Proceed
Please respond with:
- APPROVED: [option if applicable]
- REJECTED: [reason]
- CLARIFY: [questions]
```

**Decision Logging:**

All human decisions must be logged:

```markdown
## Human Decision Log
| Timestamp | Gate | Decision | Rationale | Decider |
|-----------|------|----------|-----------|---------|
| [time] | [type] | [decision] | [reason] | [name] |
```

### 4.6 Governance Enforcement Architecture

CRITICAL

**Purpose:** Make governance checks structural rather than optional through an Orchestrator-First pattern.

**The Problem:**

Voluntary governance tools (like `evaluate_governance`) can be ignored. Even with reminders in system prompts, server instructions, and per-response nudges, AI can bypass governance checks. This creates compliance gaps where:
- Implementation proceeds without consulting principles
- Decisions lack governance context
- S-Series violations may not be caught

**Solution: Orchestrator-First Architecture**

Make governance structural by implementing an Orchestrator Agent as the default persona. The Orchestrator MUST call `evaluate_governance()` before delegating any significant action.

```
User Request
    ↓
Orchestrator Agent (default persona)
    ↓
evaluate_governance(planned_action)
    ↓
┌─────────────┬──────────────────────┬─────────────┐
│   PROCEED   │ PROCEED_WITH_MODS    │  ESCALATE   │
│     ↓       │         ↓            │      ↓      │
│  Delegate   │  Apply mods, then    │   HALT      │
│  to Agent   │  delegate to Agent   │ Human req'd │
└─────────────┴──────────────────────┴─────────────┘
```

**Enforcement Layers (Defense in Depth):**

| Layer | Mechanism | What It Catches |
|-------|-----------|-----------------|
| 1. Default Persona | Orchestrator loads automatically | Direct action without delegation |
| 2. Governance Tool | `evaluate_governance()` returns binding assessment | Delegation without compliance check |
| 3. Post-Action Audit | `verify_governance_compliance()` checks if consulted | Bypassed governance after the fact |
| 4. Per-Response Reminder | Appended to tool responses | Self-correction opportunity |

**Layer 1: Default Persona Activation**

The Orchestrator is loaded as the default persona when a session starts:

```markdown
# Project Instructions (CLAUDE.md / gemini.md / agents.md)

## Default Persona

Load the Orchestrator Agent as the default persona. All user requests
flow through the Orchestrator, which:
1. Analyzes the request
2. Calls evaluate_governance(planned_action)
3. Delegates to specialist agents based on assessment
```

The Orchestrator's tool access is limited to delegation tools (Task, Read, Glob, Grep, governance tools). It cannot directly Edit, Write, or execute Bash. This forces delegation through the governance-checked path.

**Layer 2: Binding Assessment**

The `evaluate_governance()` tool returns one of three statuses:

| Status | Meaning | Required Action |
|--------|---------|-----------------|
| PROCEED | No governance concerns | Delegate to specialist |
| PROCEED_WITH_MODIFICATIONS | Concerns addressable | Apply modifications, then delegate |
| ESCALATE | Blocking concerns | HALT execution, request human review |

ESCALATE is blocking — work stops until human approves.

**Layer 3: Post-Action Verification**

The `verify_governance_compliance()` tool checks whether governance was consulted for a completed action:

```markdown
@verify_governance_compliance

## Action Completed
[Description of what was done]

## Expected Governance Check
[What should have been consulted]
```

Returns:
- COMPLIANT: Governance was consulted with matching assessment
- NON-COMPLIANT: Action proceeded without governance check
- PARTIAL: Check performed but for different scope

Non-compliant results are logged for pattern analysis.

**Layer 4: Per-Response Reminder**

Every tool response includes a governance reminder:

```
---
📋 Governance: Use query_governance() for principles, evaluate_governance() before significant actions.
```

This enables self-correction when earlier layers are bypassed.

**Bypass Authorization (Narrow Scope):**

Skip governance check ONLY for:

| Bypass Condition | Rationale | Logging Required |
|-----------------|-----------|------------------|
| Pure read operations | No risk of harm from viewing | No |
| User explicitly authorizes | Human override with documented reason | Yes |
| Trivial formatting-only | No semantic change | No |

All authorized bypasses must be logged with rationale when logging is required:

```markdown
## Governance Bypass Log
| Timestamp | Action | Bypass Type | Rationale |
|-----------|--------|-------------|-----------|
| [time] | [action] | [type] | [reason] |
```

**Audit Trail Requirements:**

Every `evaluate_governance()` call generates an audit record:

```json
{
  "audit_id": "gov-123abc",
  "timestamp": "2026-01-01T10:30:00Z",
  "action": "Implementing config generator module",
  "assessment": "PROCEED",
  "principles_consulted": ["coding-context-specification-completeness", "coding-quality-security-by-default"],
  "s_series_triggered": false,
  "modifications": null,
  "escalation_reason": null
}
```

Audit records enable:
- Pattern analysis for governance effectiveness
- Bypass detection after the fact
- Continuous improvement of retrieval

**Orchestrator Agent Definition:**

```markdown
# Orchestrator Agent

name: orchestrator
description: Strategic coordinator that ensures governance compliance before delegation
cognitive_function: Strategic

## Tools
- Task (for delegation to specialists)
- Read, Glob, Grep (for context gathering)
- evaluate_governance (MANDATORY before delegation)
- query_governance (for principle lookup)

## System Prompt Structure
You are the Orchestrator, the default entry point for all user requests.

Your responsibilities:
1. Analyze incoming requests
2. Call evaluate_governance(planned_action) BEFORE any significant action
3. Delegate to specialist agents based on assessment
4. Track governance compliance across the workflow

You do NOT directly execute work. You delegate to specialists who have
the appropriate tools (Edit, Write, Bash).

### Mandatory Governance Check
Before delegating ANY significant action:
1. Call evaluate_governance() with the planned action
2. If PROCEED: Delegate with governance context
3. If PROCEED_WITH_MODIFICATIONS: Apply modifications to delegation prompt
4. If ESCALATE: HALT and request human review

### What Counts as Significant
- Creating or modifying files
- Executing commands
- Making architectural decisions
- Changing configuration

### Bypass Authorization
Skip governance ONLY for:
- Pure read operations (viewing files, checking status)
- User explicitly authorizes with documented reason
- Trivial formatting-only changes

## Handoff Format
When delegating to specialists, include governance context:

Task: [specific task]
Governance Assessment: [PROCEED/MODS]
Relevant Principles: [list IDs]
Constraints: [any modifications required]
```

**Integration with Existing Patterns:**

This architecture extends existing patterns:

| Existing Pattern | Enhancement |
|-----------------|-------------|
| Governance Agent (§4.3) | Now invoked by Orchestrator, not optional |
| Human-in-the-Loop (§4.5) | ESCALATE integrates with approval workflow |
| Fault Tolerance (§4.4) | Governance failures trigger retry/escalate |
| Stop-the-Line (§4.4) | S-Series triggers automatic stop-the-line |

#### 4.6.1 Assessment Responsibility Layers

**Purpose:** Define what the script layer vs. AI layer should handle in governance assessment.

**The Problem:**

A governance tool like `evaluate_governance()` can return three assessments:
- PROCEED — No concerns
- PROCEED_WITH_MODIFICATIONS — Concerns addressable with changes
- ESCALATE — Blocking concerns requiring human review

Generating PROCEED_WITH_MODIFICATIONS requires nuanced reasoning:
- Detecting conflicts between the action and retrieved principles
- Understanding which modifications would resolve the conflict
- Generating specific, contextual recommendations

Scripts excel at deterministic tasks but cannot reason about nuance. AIs excel at reasoning but may be inconsistent or miss safety-critical patterns.

**Solution — Hybrid Responsibility Layers:**

| Layer | Responsibility | Why This Layer |
|-------|---------------|----------------|
| **Script** | S-Series keyword detection | Deterministic, non-negotiable safety |
| **Script** | Principle retrieval + ranking | Fast, consistent semantic search |
| **Script** | Structured data output | Reliable format for AI consumption |
| **AI** | Principle conflict analysis | Requires reasoning about context |
| **AI** | Modification generation | Context-aware recommendations |
| **AI** | Final assessment (PROCEED/MODIFY) | Nuanced judgment call |

**S-Series Remains Script-Enforced:**

S-Series (Safety) principles MUST be enforced by the script layer because:

1. **Deterministic** — No variance between AI models or reasoning runs
2. **Non-negotiable** — Veto authority shouldn't depend on AI judgment quality
3. **Fail-safe** — Works even if AI reasoning fails or is bypassed

```
if s_series_keywords_detected(action):
    return ESCALATE  # Script enforces, AI cannot override
```

**AI Handles Nuanced Assessment:**

For non-S-Series situations, the AI receives:
- Retrieved principles with relevance scores
- Full principle content (not just IDs)
- Action context

The AI then:
1. Reads each principle's requirements
2. Assesses whether the action complies
3. Identifies conflicts and generates modifications
4. Determines PROCEED or PROCEED_WITH_MODIFICATIONS

**Model Capability Considerations:**

Different AI models have different reasoning capabilities:

| Model Tier | Script Reliance | AI Judgment Quality |
|------------|-----------------|---------------------|
| Frontier (Opus, GPT-4, Gemini Pro) | Safety guardrails only | Excellent nuanced reasoning |
| Mid-tier (Sonnet, GPT-4o) | Safety + some heuristics | Good judgment, occasional misses |
| Fast (Haiku, GPT-4o-mini) | More scripted rules needed | May need explicit checklists |

**Implementation Pattern:**

```python
def evaluate_governance(action: str) -> GovernanceAssessment:
    # Script layer: Safety guardrail (non-negotiable)
    s_series = check_s_series_keywords(action)
    if s_series.triggered:
        return GovernanceAssessment(
            assessment="ESCALATE",
            rationale="S-Series safety review required",
            s_series_check=s_series
        )

    # Script layer: Data retrieval
    principles = retrieve_relevant_principles(action)

    # Return data for AI judgment layer
    return GovernanceAssessment(
        assessment=None,  # AI determines
        relevant_principles=principles,
        requires_ai_judgment=True
    )
```

The AI client then uses the returned principles to make the final assessment.

**Key Principle:**

> Don't try to script nuanced judgment. Don't let AI override safety guardrails.

#### 4.6.2 Gateway-Based Enforcement (Platform-Agnostic)

IMPORTANT

**Purpose:** Provide architectural governance enforcement for platforms that lack subagent capability.

**The Problem:**

The Orchestrator-First pattern (§4.6) relies on Claude Code's subagent architecture—a unique feature where `.claude/agents/` defines parallel agents with restricted tool access. This works because the *client* manages agent separation.

Other platforms (OpenAI, Gemini, Cursor, Windsurf) lack this capability:
- No parallel agent architecture
- No client-managed tool restrictions
- Governance relies on instructions alone ("hope-based")

**Solution — MCP Gateway Pattern:**

Instead of hoping the AI follows governance instructions, enforce governance *physically* by controlling tool access at the server layer.

```
Without Gateway (Hope-Based):          With Gateway (Architecture-Based):
┌──────────┐                           ┌──────────┐
│ AI Agent │                           │ AI Agent │
└────┬─────┘                           └────┬─────┘
     │ Direct access                        │ Only sees governance tools
     ▼                                      ▼
┌──────────────┐                       ┌────────────────┐
│ MCP Servers  │                       │ Governance     │
│ (file, db,   │                       │ Gateway/Proxy  │
│  shell, etc) │                       └────────┬───────┘
└──────────────┘                                │ Validates before allowing
                                                ▼
                                       ┌──────────────┐
                                       │ MCP Servers  │
                                       └──────────────┘
```

**How Gateway Enforcement Works:**

| Layer | What Happens |
|-------|--------------|
| 1. Request | AI calls tool (e.g., `edit_file`) via Gateway |
| 2. Governance Check | Gateway calls `evaluate_governance(planned_action)` |
| 3. Assessment | PROCEED → forward request; ESCALATE → reject with reason |
| 4. Execution | Only governance-approved requests reach the actual server |
| 5. Logging | All requests logged for audit trail |

**Available MCP Gateway Solutions (2025):**

| Gateway | Key Feature | Use Case |
|---------|-------------|----------|
| Lasso MCP Gateway | Plugin-based guardrails, PII detection | Security-focused orgs |
| Envoy AI Gateway | Session-aware, leverages Envoy infra | Existing Envoy users |
| IBM ContextForge | FastAPI-based, large-scale | Enterprise deployments |
| Custom Governance Proxy | Wrap this MCP server as gatekeeper | Simple deployments |

**When to Use Gateway vs Subagent:**

| Factor | Subagent (Claude Code) | Gateway |
|--------|----------------------|---------|
| Platform | Claude Code/Desktop only | Any MCP client |
| Setup complexity | Low (drop file in folder) | Medium (deploy proxy) |
| Enforcement | Client-managed | Server-managed |
| Visibility | Agent visible in UI | Transparent to AI |
| Enterprise | Single-user focus | Multi-user, centralized |

**Deployment Decision Matrix:**

```
Is this for Claude Code users only?
├── YES → Use subagent pattern (§4.6, install_agent tool)
└── NO → Does organization have MCP gateway infrastructure?
         ├── YES → Integrate with existing gateway
         └── NO → Deploy governance proxy or use instruction-based fallback
```

**Instruction-Based Fallback (Minimum Viable):**

When gateway isn't feasible, layer defenses:

1. **SERVER_INSTRUCTIONS** — Injected at MCP init
2. **Per-Response Reminder** — Appended to every tool response
3. **Audit Log Review** — Periodic `verify_governance_compliance()` checks

This provides guidance but not enforcement—the AI *can* bypass. For high-stakes environments, gateway architecture is recommended.

**Key Principle:**

> Enforce governance *physically* (tool access control) rather than *psychologically* (instructions). Architecture beats hope.

### 4.7 Agent Evaluation Framework

CRITICAL

**Purpose:** Systematically evaluate agent performance across multiple dimensions for continuous improvement.

**Source:** Google Vertex AI Gen AI Evaluation Service, Confident AI, orq.ai evaluation research

**Why Validation Alone Is Insufficient:**

Validation (§4.1) checks individual outputs against acceptance criteria. The Agent Evaluation Framework provides systematic measurement of agent performance over time, enabling optimization and regression detection.

**The Four Evaluation Layers:**

| Layer | What It Measures | When to Evaluate | Key Metrics |
|-------|------------------|------------------|-------------|
| **Component** | Individual subsystem quality | After each component change | Per-tool accuracy, retrieval precision |
| **Trajectory** | Decision-making path quality | Per task completion | Step efficiency, reasoning coherence |
| **Outcome** | Task completion quality | Per task completion | Goal fulfillment, user satisfaction |
| **System** | Multi-agent coordination | Per workflow completion | Handoff success, cascade failures |

**Component-Level Evaluation:**

Test subsystems in isolation:

| Component | Evaluation Method | Metrics |
|-----------|------------------|---------|
| Routing logic | Accuracy on labeled dataset | Precision, recall, F1 |
| Context compression | Manual review of distillation | Information preservation rate |
| Tool selection | Comparison to ideal tool | Selection accuracy |
| Governance retrieval | Relevance scoring | MRR, NDCG |

**Trajectory Evaluation (Key Addition):**

Evaluate the decision-making path, not just the final output:

| Metric | Definition | Target |
|--------|------------|--------|
| **Exact match** | Trajectory exactly matches ideal solution | Task-dependent |
| **In-order match** | Required actions in correct sequence | > 80% |
| **Any-order match** | Required actions regardless of order | > 90% |
| **Step efficiency** | Actual steps / Minimum required steps | < 1.5x |
| **Backtrack rate** | Steps that revise prior decisions | < 10% |

**Trajectory Evaluation Template:**

```markdown
## Trajectory Evaluation — [Task ID]

### Ideal Trajectory
1. [Expected step 1]
2. [Expected step 2]
3. [Expected step N]

### Actual Trajectory
1. [Actual step 1] — MATCH / EXTRA / WRONG
2. [Actual step 2] — MATCH / EXTRA / WRONG
...

### Metrics
- Exact Match: YES / NO
- In-Order Match: [X]%
- Any-Order Match: [X]%
- Step Efficiency: [actual] / [ideal] = [ratio]
- Backtrack Rate: [count] / [total] = [%]

### Analysis
[Why trajectory deviated, if applicable]
```

**Outcome Evaluation:**

| Metric | Definition | Measurement |
|--------|------------|-------------|
| Goal fulfillment | Task objectives achieved | Checklist against acceptance criteria |
| Output quality | Correctness, completeness | Domain-specific rubric |
| User satisfaction | Human rating of usefulness | 1-5 scale or thumbs up/down |
| Time to completion | Duration from start to done | Clock time |

**System-Level Evaluation:**

| Metric | Definition | Target |
|--------|------------|--------|
| Handoff success rate | Successful transfers / Total transfers | > 95% |
| Cascade failure rate | Multi-agent failures from single error | < 1% |
| Resource efficiency | Tokens used / Baseline estimate | < 150% |
| Human escalation rate | Escalations / Total tasks | Task-appropriate |
| End-to-end latency | Total time for multi-agent workflow | Within SLA |

**Evaluation Cadence:**

| Level | Frequency | Trigger |
|-------|-----------|---------|
| Component | On change | Code/config modification |
| Trajectory | Per task | Task completion |
| Outcome | Per task | Task completion |
| System | Weekly | Scheduled review |

**Evaluation Dashboard Requirements:**

```yaml
dashboard:
  component_health:
    - routing_accuracy
    - compression_quality
    - tool_selection_rate

  trajectory_trends:
    - avg_step_efficiency (7-day rolling)
    - backtrack_rate_trend
    - exact_match_rate

  outcome_summary:
    - goal_fulfillment_rate
    - user_satisfaction_avg
    - completion_time_p50_p95

  system_alerts:
    - cascade_failures_today
    - escalation_rate_vs_baseline
    - token_budget_utilization
```

#### 4.7.1 Grader Types

IMPORTANT

**Purpose:** Select appropriate grading approaches based on task characteristics.

**Source:** Anthropic Engineering "Demystifying Evals for AI Agents" (2025)

**The Three Grader Types:**

| Type | When to Use | Strengths | Weaknesses |
|------|-------------|-----------|------------|
| **Code-Based** | Deterministic validation, structured outputs | Fast, cheap, reproducible, easy debugging | Brittle to valid variations, lacks nuance |
| **Model-Based** | Subjective tasks, open-ended outputs | Flexible, scalable, captures nuance | Non-deterministic, expensive, requires calibration |
| **Human** | Gold-standard calibration, edge cases | Matches expert judgment, handles ambiguity | Slow, expensive, doesn't scale |

**Code-Based Grader Methods:**

| Method | Use Case | Example |
|--------|----------|---------|
| String matching | Exact expected output | `assert output == expected` |
| Regex patterns | Structured format validation | `re.match(r'\d{3}-\d{4}', phone)` |
| Static analysis | Code quality checks | ruff, mypy, bandit |
| Unit tests | Functional correctness | pytest assertions |
| State verification | Environment changes | File exists, DB record created |

**Model-Based Grader Methods:**

| Method | Use Case | Example |
|--------|----------|---------|
| Rubric scoring | Multi-dimensional quality | "Rate clarity 1-5, completeness 1-5" |
| Natural language assertion | Flexible criteria | "Does the response address the user's concern?" |
| Pairwise comparison | Relative quality | "Which response better solves the problem?" |
| Multi-judge consensus | High-stakes decisions | 3 LLM judges, majority vote |

**Model-Based Grader Design Principles:**

- **Give escape options** — Include "Unknown" or "Cannot determine" to prevent hallucinated judgments
- **Isolate dimensions** — Grade each quality dimension separately with independent prompts
- **Calibrate against humans** — Periodically validate LLM grader agreement with expert judgment
- **Use structured output** — Request JSON with score and rationale for debugging

**Human Grader Methods:**

| Method | Use Case | Scale |
|--------|----------|-------|
| SME review | Domain expertise required | Low volume, high stakes |
| Spot-check sampling | Calibration and drift detection | 5-10% of eval suite |
| A/B preference testing | Comparative quality | User-facing changes |

**Grader Selection Decision Tree:**

```
Is output deterministically verifiable?
├── Yes → Code-Based Grader
└── No → Is task subjective or open-ended?
    ├── Yes → Model-Based Grader (calibrate with human spot-checks)
    └── No → Is this high-stakes or ambiguous?
        ├── Yes → Human Grader
        └── No → Model-Based Grader
```

---

#### 4.7.2 Non-Determinism Measurement

IMPORTANT

**Purpose:** Quantify agent reliability accounting for inherent model variability.

**Source:** Anthropic Engineering "Demystifying Evals for AI Agents" (2025)

**Why Non-Determinism Matters:**

AI agents exhibit run-to-run variability even with identical inputs. A single trial is insufficient to characterize true performance. Multiple trials reveal the distribution of outcomes.

**The Two Key Metrics:**

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **pass@k** | P(≥1 success in k trials) | "Can the agent ever succeed?" |
| **pass^k** | P(all k trials succeed) | "Can we rely on the agent?" |

**Mathematical Relationship:**

For an agent with per-trial success probability p:
- `pass@k = 1 - (1-p)^k` — Approaches 100% as k increases
- `pass^k = p^k` — Approaches 0% as k increases

**Divergence Example:**

| Per-Trial Success | pass@10 | pass^10 |
|-------------------|---------|---------|
| 90% | 99.99% | 34.9% |
| 70% | 99.99% | 2.8% |
| 50% | 99.9% | 0.1% |

**Interpretation:** An agent that succeeds 50% of the time will almost always succeed *eventually* (pass@10 ≈ 100%) but almost never succeeds *reliably* (pass^10 ≈ 0%).

**When to Use Each Metric:**

| Scenario | Metric | Rationale |
|----------|--------|-----------|
| Research/exploration tasks | pass@k | One good result is valuable |
| Customer-facing automation | pass^k | Reliability is critical |
| Human-in-the-loop workflows | pass@k | Human catches failures |
| Fully autonomous agents | pass^k | No safety net |

**Recommended Trial Counts:**

| Eval Purpose | Minimum Trials | Notes |
|--------------|----------------|-------|
| Quick iteration | 3-5 | Detect gross failures |
| Release decision | 10-20 | Statistical confidence |
| Regression suite | 5-10 | Balance speed and signal |
| Capability frontier | 20-100 | Characterize true ceiling |

**Non-Determinism Measurement Template:**

```markdown
## Non-Determinism Analysis — [Task ID]

### Configuration
- Trials: [k]
- Temperature: [value]
- Model: [version]

### Results
| Trial | Outcome | Notes |
|-------|---------|-------|
| 1 | PASS/FAIL | [brief note] |
| ... | ... | ... |

### Metrics
- Per-trial success rate: [successes]/[k] = [p]%
- pass@k: [calculated]%
- pass^k: [calculated]%

### Reliability Assessment
[HIGH/MEDIUM/LOW] — [rationale]
```

---

#### 4.7.3 Capability vs Regression Evals

IMPORTANT

**Purpose:** Distinguish between evals that drive improvement and evals that guard existing behavior.

**Source:** Anthropic Engineering "Demystifying Evals for AI Agents" (2025)

**The Two Eval Types:**

| Type | Purpose | Expected Pass Rate | Growth Pattern |
|------|---------|-------------------|----------------|
| **Capability** | Target agent struggles, drive improvement | Low initially (10-50%) | Rises as agent improves |
| **Regression** | Detect backsliding, guard existing behavior | High baseline (~100%) | Suite grows over time |

**Capability Eval Characteristics:**

- Tests things the agent *cannot yet do reliably*
- Low pass rates are expected and informative
- Provides improvement targets for development
- Measures frontier of agent capability

**Regression Eval Characteristics:**

- Tests things the agent *should already do*
- Near-100% pass rate is the baseline
- Failures indicate breaking changes
- Runs in CI/CD to block problematic deployments

**The Graduation Pattern:**

```
Capability Eval (pass@10 = 30%)
        │
        ▼ [Agent improves]
Capability Eval (pass@10 = 85%)
        │
        ▼ [Threshold met]
Graduates to Regression Suite
        │
        ▼ [Baseline locked]
Regression Eval (expected: 100%)
```

**Graduation Criteria:**

| Metric | Threshold for Graduation |
|--------|--------------------------|
| pass@10 | > 80% |
| pass^5 | > 60% |
| Consecutive stable runs | ≥ 3 |

**Eval Suite Composition:**

| Suite Stage | Capability % | Regression % |
|-------------|--------------|--------------|
| Early development | 80% | 20% |
| Mature agent | 30% | 70% |
| Production maintenance | 10% | 90% |

**Saturation Monitoring:**

When capability evals approach 100%, they lose signal:
- **Symptom:** All tests pass, but users still report issues
- **Cause:** Eval suite no longer challenges agent frontier
- **Fix:** Add harder tasks, graduate saturated evals to regression

**Saturation Detection:**

| Signal | Threshold | Action |
|--------|-----------|--------|
| Capability suite pass rate | > 90% sustained | Add harder tasks |
| No capability failures for | > 2 weeks | Review suite difficulty |
| User-reported issues not caught | Any | Convert to regression test |

---

#### 4.7.4 Grader Design Principles

IMPORTANT

**Purpose:** Build evaluation graders that accurately measure agent performance without false positives or negatives.

**Source:** Anthropic Engineering "Demystifying Evals for AI Agents" (2025), METR evaluation research

**Core Principles:**

| Principle | Description | Why It Matters |
|-----------|-------------|----------------|
| **Grade outcomes, not paths** | Evaluate final result, not specific steps taken | Agents find valid approaches designers didn't anticipate |
| **Build partial credit** | Multi-component tasks shouldn't be all-or-nothing | Distinguishes "close" from "completely wrong" |
| **Make tasks unambiguous** | Two experts should independently reach same verdict | Ambiguity causes grader disagreement and noise |
| **Create reference solutions** | Prove task is solvable, validate grader | 0% pass@100 usually indicates broken task |
| **Read transcripts** | Manually review failures to verify grader correctness | Catches grader bugs and unfair failures |

**Anti-Pattern: Overly Rigid Grading**

**Example:** Task asks agent to compute a percentage. Grader expects "96.12" but agent outputs "96.124991".

**Problem:** Mathematically equivalent answers rejected due to formatting.

**Fix:** Use tolerance-based comparison:
```python
# Bad: Exact string match
assert output == "96.12"

# Good: Numeric tolerance
assert abs(float(output) - 96.12) < 0.01
```

**Anti-Pattern: Ambiguous Success Criteria**

**Example:** Task says "optimize the function" but grader expects specific optimization.

**Problem:** Agent applies valid but unexpected optimization; grader fails it.

**Fix:** Specify measurable criteria:
```markdown
# Bad: "Optimize the function"
# Good: "Reduce function runtime by at least 20% on the provided benchmark"
```

**Anti-Pattern: Grading Stated Goals vs. Intended Goals**

**Example:** Task says "reach 90% accuracy" but grader requires exceeding 90%.

**Problem:** Instruction-following agents stop at exactly 90%; grader fails them.

**Fix:** Align grader with stated requirements:
```python
# Bad: Penalizes instruction-following
assert accuracy > 0.90

# Good: Matches stated requirement
assert accuracy >= 0.90
```

**Grader Validation Checklist:**

Before deploying a new grader:

- [ ] Reference solution exists and passes
- [ ] Two domain experts agree on pass/fail for 10+ edge cases
- [ ] Grader handles valid output variations (formatting, ordering)
- [ ] Partial credit distinguishes degrees of correctness
- [ ] Failure messages explain what was wrong
- [ ] Manual transcript review confirms failures are fair

**Grader Quality Metrics:**

| Metric | Definition | Target |
|--------|------------|--------|
| Expert agreement | % of cases where grader matches human judgment | > 95% |
| False positive rate | Valid solutions incorrectly failed | < 2% |
| False negative rate | Invalid solutions incorrectly passed | < 5% |
| Explanation clarity | Can developer understand why task failed? | Subjective review |

---

### 4.8 Production Safety Guardrails

CRITICAL

**Purpose:** Implement multi-layer safety defenses for production agent deployments.

**Source:** Dextra Labs Agentic AI Safety Playbook, Superagent Framework, OWASP 2025

**The Guardrail Imperative:**

Safety guardrails are required infrastructure, not optional enhancements. Production agents operate with significant autonomy; guardrails ensure this autonomy doesn't lead to harm.

**The Guardrail Pipeline:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Guardrail Pipeline                          │
│                                                                 │
│  User Input ──► [Input Guardrails] ──► Model ──► [Output Guardrails] ──► User
│                      │                              │           │
│                      ▼                              ▼           │
│                 Reject/Modify                  Redact/Block     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Input Guardrails:**

| Defense | What It Catches | Implementation |
|---------|-----------------|----------------|
| **Prompt injection detection** | Attempts to override instructions | Pattern matching + classifier |
| **Topic classification** | Out-of-scope requests | Intent classifier |
| **PII detection** | Sensitive data in prompts | Regex + NER |
| **Rate limiting** | Abuse prevention | Token bucket / sliding window |
| **Input length limits** | Context overflow attacks | Hard token limits |

**Prompt Injection Defense:**

```python
# Example injection patterns to detect
INJECTION_PATTERNS = [
    r"ignore (previous|prior|above) instructions",
    r"disregard (your|the) (rules|guidelines)",
    r"you are now",
    r"new instructions:",
    r"override.*system.*prompt",
    r"pretend you are",
]

def check_prompt_injection(input_text: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, input_text, re.IGNORECASE):
            return True  # Potential injection detected
    return False
```

**Output Guardrails:**

| Defense | What It Catches | Implementation |
|---------|-----------------|----------------|
| **PII redaction** | Accidental data leakage | Pattern matching + replacement |
| **Hallucination grounding** | Unsupported claims | Citation verification |
| **Content moderation** | Inappropriate outputs | Classifier + blocklist |
| **Tool call validation** | Unauthorized actions | Allowlist checking |
| **Output length limits** | Runaway generation | Hard token limits |

**PII Redaction Patterns:**

| PII Type | Pattern | Replacement |
|----------|---------|-------------|
| Email | `[\w.-]+@[\w.-]+\.\w+` | `[EMAIL]` |
| Phone | `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b` | `[PHONE]` |
| SSN | `\b\d{3}-\d{2}-\d{4}\b` | `[SSN]` |
| Credit Card | `\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b` | `[CARD]` |
| API Key | `\b(sk|api|key|token)[_-]?[a-zA-Z0-9]{20,}\b` | `[API_KEY]` |

**RBAC for Tools (Per §2.1.2):**

Each agent role should have explicit tool permissions:

| Role | Allowed Tools | Rationale |
|------|--------------|-----------|
| Orchestrator | Read, Glob, Grep, Task, governance | No direct modification |
| Specialist | Domain-appropriate | Principle of least privilege |
| Validator | Read-only | Fresh perspective, no modification |
| Researcher | Read, WebSearch, WebFetch | Information gathering only |

**Guardrail Configuration Template:**

```yaml
guardrails:
  input:
    prompt_injection:
      enabled: true
      action: reject  # or: sanitize
      patterns: default  # or: custom list

    pii_detection:
      enabled: true
      action: warn  # or: reject
      types: [email, phone, ssn, credit_card]

    rate_limiting:
      enabled: true
      requests_per_minute: 60
      tokens_per_minute: 100000

    max_input_tokens: 10000

  output:
    pii_redaction:
      enabled: true
      types: [email, phone, ssn, credit_card, api_key]

    content_moderation:
      enabled: true
      categories: [hate, violence, sexual, self_harm]
      threshold: 0.8

    tool_call_validation:
      enabled: true
      mode: allowlist  # or: denylist
      # Allowlist defined per agent role

    max_output_tokens: 4000

  logging:
    log_blocked_requests: true
    log_redactions: true
    alert_on_injection_attempt: true
```

**Production Benchmarks (2025):**

| Metric | Target | Notes |
|--------|--------|-------|
| MTTD (Mean Time to Detect) | < 5 minutes | Time to detect guardrail violation |
| False positive rate | < 2% | Legitimate requests incorrectly blocked |
| Guardrail overhead | < 100ms | Added latency for guardrail checks |
| Coverage | 100% | All inputs/outputs pass through guardrails |

**Integration with Governance:**

Guardrails complement governance checks:
- **Guardrails:** Fast, deterministic, pattern-based defenses
- **Governance (§4.3):** Nuanced, principle-based assessment

Both should be applied. Guardrails catch obvious violations quickly; governance catches subtle compliance issues.

**S-Series Integration:**

S-Series (Safety) principles from the Constitution have veto authority. Guardrail violations that align with S-Series triggers should:
1. Block the action immediately
2. Log the violation with full context
3. Alert operators if configured
4. Escalate to human review

---

# TITLE 5: Cross-Tool Synchronization

**Implements:** R4 (State Persistence), supports multi-CLI workflow

### 5.1 Context File Synchronization

CRITICAL

**Purpose:** Keep context identical across Claude Code, Gemini CLI, and Codex CLI.

**The Three Context Files:**

| File | Tool | Must Contain |
|------|------|--------------|
| `claude.md` | Claude Code CLI | Project context, agent registry, decisions |
| `gemini.md` | Gemini CLI | IDENTICAL to claude.md |
| `agents.md` | Codex CLI | IDENTICAL to claude.md |

**Sync Protocol:**

1. **Designate Primary:** Claude Code is typically primary (most capable)
2. **Edit Primary:** Make all context edits to `claude.md`
3. **Sync Command:** After edits:
   ```bash
   cp claude.md gemini.md && cp claude.md agents.md
   ```
4. **Verify Sync:**
   ```bash
   diff claude.md gemini.md && diff claude.md agents.md && echo "Sync verified"
   ```

**Sync Triggers:**

- After every significant decision
- After session closer runs
- Before switching to different CLI tool
- Before ending work session

**Sync Verification Prompt:**

Use this when switching tools:

```
I'm switching from [Claude/Gemini/Codex] to [Claude/Gemini/Codex].

Please verify:
1. Context files are synced (claude.md = gemini.md = agents.md)
2. STATE.md reflects current position
3. No pending handoffs that need attention

Then load context and confirm ready state.
```

### 5.2 Multi-Tool Workflow Patterns

IMPORTANT

**Pattern: Parallel Research with Different Models**

```
User Request: "Research [topic] from multiple perspectives"

1. Claude: "Write a hook for this, authority angle -> authority-hook.md"
2. Gemini: "Write a hook for this, discovery angle -> discovery-hook.md"
3. Codex: "Review both hooks, synthesize recommendation"
```

**Pattern: Specialized Tool Selection**

| Task Type | Recommended Tool | Rationale |
|-----------|-----------------|-----------|
| Complex reasoning | Claude Code | Best at nuanced analysis |
| Web research | Gemini CLI | Strong search integration |
| Code review | Claude Code or Codex | Both strong at code |
| Quick lookup | Gemini CLI | Fast, free tier |
| Synthesis/critique | Codex | Good at high-level analysis |

**Pattern: Cross-Tool Validation**

```
1. Claude: Generate output
2. Switch to Gemini: Validate output (fresh model = fresh perspective)
3. Synthesize feedback
```

---

## Appendix A: Claude Code CLI Specifics

OPTIONAL — Load when using Claude Code

### Agent Creation

```bash
# Launch Claude Code
claude

# Create agent interactively
/agents
# Select "Create new agent"
# Choose project or personal scope
# Paste agent definition
```

### Agent Invocation

```bash
# Automatic (Claude decides)
"Perform research on X"  # Claude invokes appropriate agent

# Explicit
"@home-lab-guru Research the best NAS options"
```

### Key Commands

| Command | Purpose |
|---------|---------|
| `/agents` | Manage agents |
| `/context` | View context usage |
| `/clear` | Clear conversation (keep files) |
| `/init` | Create claude.md from project |
| `Shift+Tab` | Cycle modes (normal/plan) |
| `Ctrl+O` | View agent execution details |
| `--dangerously-skip-permissions` | Bypass permission prompts |

### Sub-Agent Behavior

- Sub-agents get FRESH context window (200K tokens)
- Sub-agents CANNOT spawn other sub-agents
- Sub-agent results returned as concise summary
- Use `Ctrl+O` to expand sub-agent details

### Task Management System (v2.1.16+)

Claude Code provides built-in task coordination via four tools. This supersedes the legacy TodoWrite system.

#### Task Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `TaskCreate` | Create structured task | `subject` (imperative), `description`, `activeForm` (present continuous) |
| `TaskUpdate` | Update task state | `taskId`, `status`, `owner`, `addBlocks`, `addBlockedBy` |
| `TaskList` | List all tasks | Returns: id, subject, status, owner, blockedBy |
| `TaskGet` | Get full task details | `taskId` → full description, blocks, blockedBy |

#### Task States

```
pending → in_progress → completed
```

- Mark `in_progress` BEFORE starting work
- Mark `completed` ONLY when fully done (not partial, not failing tests)
- Keep `in_progress` if blocked — create blocker task instead

#### Dependency Tracking

```bash
# Task 2 waits for Task 1
TaskUpdate(taskId="2", addBlockedBy=["1"])

# Task 1 blocks Tasks 2 and 3
TaskUpdate(taskId="1", addBlocks=["2", "3"])
```

**Dependency Patterns:**

| Pattern | Structure | Use Case |
|---------|-----------|----------|
| Pipeline | `A → B → C` (B.blockedBy=[A], C.blockedBy=[B]) | Sequential processing |
| Fan-Out | `A → [B,C,D]` (B/C/D.blockedBy=[A]) | Parallel after setup |
| Fan-In | `[B,C,D] → E` (E.blockedBy=[B,C,D]) | Convergence before next phase |

#### When to Use Tasks

| Use Tasks | Skip Tasks |
|-----------|------------|
| Complex multi-step work (3+ steps) | Single straightforward task |
| Plan mode tracking | Trivial operations |
| User provides numbered list | Purely conversational |
| Coordinating with sub-agents | <3 trivial steps |

#### Best Practices

1. Create tasks with clear imperative subjects ("Fix auth bug" not "Auth bug")
2. Include enough description for another agent to complete independently
3. Check `TaskList` before creating to avoid duplicates
4. ONE task `in_progress` per agent at a time (atomic progress)
5. Use `TaskGet` to read latest state before updating (avoid stale writes)

#### Environment Variable

```bash
# Revert to legacy TodoWrite (temporary)
CLAUDE_CODE_ENABLE_TASKS=false
```

### Multi-Agent Swarm Infrastructure (Emerging)

**Status:** Feature-flagged. Document for awareness only. Review date: 2026-Q2.

Claude Code binary contains TeammateTool infrastructure for swarm coordination. This is NOT yet publicly available but may activate in future releases.

#### Anticipated Capabilities (When Enabled)

| Capability | Description |
|------------|-------------|
| Team spawning | Create named teams with shared task lists |
| Agent messaging | Direct (`write`) and broadcast communication |
| Plan approval | Leader reviews agent plans before execution |
| Graceful shutdown | Coordinated team termination |

#### Environment Variables (When Enabled)

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_TEAM_NAME` | Active team identifier |
| `CLAUDE_CODE_AGENT_ID` | Unique agent reference |
| `CLAUDE_CODE_AGENT_NAME` | Display identifier |

#### File Structure (When Enabled)

```
~/.claude/
├── teams/{team-name}/
│   ├── config.json        # Team metadata, roster
│   └── messages/          # Inter-agent mailbox
└── tasks/{team-name}/     # Team-scoped task list
```

**Note:** Monitor [Claude Code release notes](https://github.com/anthropics/claude-code/releases) for TeammateTool activation.

---

## Appendix B: Gemini CLI Specifics

OPTIONAL — Load when using Gemini CLI

### Installation

```bash
npm install -g @anthropic-ai/gemini-cli
# or
brew install gemini-cli
```

### Context File

```bash
# Create context file
gemini
/init  # Creates gemini.md
```

### Key Commands

| Command | Purpose |
|---------|---------|
| `/init` | Create gemini.md from project |
| `/tools` | View available tools |
| `/context` | View context usage |

### Headless Mode

```bash
# Run single prompt without TUI
gemini -p "Your prompt here"
```

Useful for: Agent invoking Gemini for specific tasks

---

## Appendix C: Codex CLI (OpenAI) Specifics

OPTIONAL — Load when using Codex CLI

### Installation

```bash
npm install -g @openai/codex
```

### Context File

Uses `agents.md` by convention (sync with claude.md/gemini.md)

### Key Commands

| Command | Purpose |
|---------|---------|
| `/model` | Switch models |
| `/sessions` | View past sessions |
| `/share` | Share session URL |
| `/timeline` | View/restore session history |

### Session Sharing

```bash
/share  # Copies shareable URL to clipboard
```

---

## Appendix D: Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.10.0 | 2026-01-24 | **Task Management & Dependency Tracking.** Added: Appendix A Claude Code Task Management System (TaskCreate, TaskUpdate, TaskList, TaskGet tools with states and dependency tracking), Multi-Agent Swarm Infrastructure (emerging/feature-flagged TeammateTool awareness). Enhanced: §3.3 Dependency Declaration patterns (blockedBy/blocks relationships, Pipeline/Fan-Out/Fan-In patterns), §3.5 Task Ownership Protocol (claim-before-work, atomic progress, session resume reassignment). Sources: Claude Code v2.1.16 release notes, Anthropic Agent SDK documentation, community implementations (claude-flow, Piebald-AI system prompt extraction). |
| v2.8.0 | 2026-01-17 | **Evaluation Methods Enhancement.** Added: §4.7.1 Grader Types (Code-Based, Model-Based, Human — selection guidance, strengths/weaknesses), §4.7.2 Non-Determinism Measurement (pass@k for capability testing, pass^k for reliability — formulas and target thresholds), §4.7.3 Capability vs Regression Evals (when to use each, metrics differences, workflow integration), §4.7.4 Grader Design Principles (grade outcomes not paths, partial credit, multi-shot grading). Source: Anthropic Engineering "Demystifying Evals for AI Agents" (2025). Fills gap: existing 4-layer framework lacked specific grader implementation guidance. |
| v2.7.0 | 2026-01-05 | **Governance Compliance Section.** Added: Governance Compliance as 6th required section in Subagent Definition Standard (§2.1). All subagent system prompts must now include governance framework alignment: S-Series veto authority, Constitution meta-principles, domain applicability, and uncertainty handling. Template updated with placeholder section. Addresses gap: subagents lacked explicit governance framework awareness, causing issues like Contrarian Reviewer "missing the point" by not following constitutional hierarchy. |
| v2.6.0 | 2026-01-04 | **Artifact Type Selection.** Added: §1.1 Artifact Type Selection: Method vs. Subagent — decision framework for choosing between method (procedure for generalist) or subagent (dedicated agent with fresh context) when specialization is justified. Fresh context is primary signal; requires supporting factor (frequency, tool restrictions, cognitive isolation) to justify subagent overhead. Includes comparison table, decision tree, examples, and "when in doubt" guidance. Updates Situation Index. Addresses gap: existing principles covered Agent vs Generalist but not Method vs Subagent as artifact types. |
| v2.5.0 | 2026-01-05 | **Production Operations Expansion.** Added 6 new sections from Google Cloud AI Agents guide analysis + 2025-2026 industry research validation. New sections: §3.4.1 Memory Distillation Procedure (AWS AgentCore 89-95% compression, Mem0 80% token reduction, Google Titans architecture), §3.7.1 Production Observability Patterns (IBM AgentOps, OpenTelemetry, session replay), §3.8 ReAct Loop Configuration (loop controls, termination triggers, runaway detection), §4.7 Agent Evaluation Framework (4-layer model: Component/Trajectory/Outcome/System, trajectory metrics), §4.8 Production Safety Guardrails (multi-layer defense, prompt injection, PII redaction, RBAC). Updated Situation Index with 7 new entries. Sources: Google Vertex AI Gen AI Evaluation Service, Confident AI, Dextra Labs Safety Playbook, Superagent Framework, OWASP 2025. |
| v2.4.0 | 2026-01-04 | **Agent Authoring Best Practices.** Added: §2.1.1 System Prompt Best Practices (positive framing, examples, sandwich method, concrete invocation triggers), §2.1.2 Tool Scoping Guidelines (when to restrict vs inherit, decision matrix), §2.1.3 Agent Validation Checklist (3-phase validation, iteration process, graduation criteria). Updated Situation Index with new sections. Source: Anthropic prompt engineering research, Claude Code subagent docs, skill authoring best practices. |
| v2.3.0 | 2026-01-03 | **Gateway-Based Enforcement.** Added: §4.6.2 Gateway-Based Enforcement (Platform-Agnostic) — documents MCP Gateway pattern for platforms lacking subagent architecture. Covers: problem (Claude Code subagents are unique), solution (server-side enforcement via gateway/proxy), available solutions (Lasso, Envoy, IBM ContextForge), decision matrix (subagent vs gateway), instruction-based fallback for minimum viable enforcement. Key principle: "Architecture beats hope." |
| v2.2.0 | 2026-01-02 | **Assessment Responsibility Layers.** Added: §4.6.1 Assessment Responsibility Layers — defines script vs AI layer responsibilities in governance assessment. Script handles: S-Series keyword detection (deterministic safety), principle retrieval, structured output. AI handles: principle conflict analysis, modification generation, nuanced judgment. Includes model capability considerations (Frontier/Mid-tier/Fast). Key principle: "Don't try to script nuanced judgment. Don't let AI override safety guardrails." |
| v2.1.0 | 2026-01-02 | **Governance Enforcement Architecture + Cross-Platform Research.** Added: §4.6 Governance Enforcement Architecture — Orchestrator-First pattern making governance structural (not optional), four-layer defense in depth (Default Persona → Governance Tool → Post-Action Audit → Per-Response Reminder), bypass authorization with narrow scope, audit trail requirements, Orchestrator Agent definition. Added: Appendix F Cross-Platform Agent Support — platform matrix (Claude Code, Codex CLI, Gemini CLI, ChatGPT, Grok/Perplexity), enforcement levels (HARD vs SOFT), LLM-agnostic design patterns, platform detection code, user communication templates. Problem addressed: voluntary governance tools can be ignored even with reminders. Solution: Orchestrator as default persona with mandatory `evaluate_governance()` before delegation. ESCALATE is now blocking (halts execution until human approves). |
| v2.0.0 | 2026-01-01 | **Major revision aligned with Principles v2.0.0.** Added: Agent Definition Standard (§2.1), Agent Catalog with 6 patterns (§2.2), Contrarian Reviewer pattern (§4.2), Governance Agent pattern (§4.3), Handoff Pattern Taxonomy (§3.1), Compression Procedures (§3.4), Shared Assumptions Document. Enhanced: Pattern Selection with Linear-First default and Read-Write Analysis. Updated: Preamble scope for individual/sequential/parallel coverage. Renamed: Title numbering for new sections. Research: Anthropic, Google ADK, Cognition, LangChain, Microsoft, Vellum multi-agent patterns (2025). |
| v1.1.0 | 2025-12-29 | Structural Fixes: Changed Title headers from `## Title` to `# TITLE` for extractor compatibility. Changed section headers from `### X.Y` to `### X.Y` for method extraction. Removed series codes from Principle to Title mapping. Updated status from Draft to Active. |
| v1.0.0 | 2025-12-21 | Initial release. Implements 11 multi-agent domain principles. Core patterns derived from 2025 industry best practices and NetworkChuck workflow patterns. |

---

## Appendix E: Evidence Base

This methods document synthesizes patterns from:

**Official Documentation:**
- Anthropic Claude Code Best Practices (2025)
- Anthropic Claude Agent SDK (2025)
- Claude Code Subagents Documentation
- Claude Code v2.1.16 Release Notes — Task Management System introduction
- Claude Agent SDK Todo Tracking — Task states and lifecycle

**Industry Research (2025-2026):**
- Anthropic Multi-Agent Research System (90.2% improvement, 15x tokens)
- Google ADK "Architecting Efficient Context-Aware Multi-Agent Framework" (Agents-as-Tools vs Agent-Transfer)
- Google Cloud "Startup Technical Guide: AI Agents" (2025) — comprehensive agent patterns
- Google Vertex AI Gen AI Evaluation Service — 4-layer evaluation framework
- Cognition "Don't Build Multi-Agents" (conflicting assumptions, read-write division)
- LangChain "How and When to Build Multi-Agent Systems" (read-heavy parallelization)
- Microsoft Multi-Agent Reference Architecture (context engineering)
- Vellum "Multi-Agent Context Engineering" (Write/Select/Compress/Isolate)

**Memory & Context Research (2025-2026):**
- AWS AgentCore Memory Deep Dive — 89-95% compression rates in production
- Mem0 Paper (arXiv:2504.19413) — 80% token reduction via graph-based distillation
- Google Titans Architecture — Test-time memorization with "surprise" metrics

**Observability & Operations (2025-2026):**
- IBM AgentOps — Built on OpenTelemetry standards
- AgentOps.ai — 400+ LLM integrations, visual event tracking
- AI Multiple Research — 12-15% overhead acceptable for observability

**Safety & Evaluation (2025-2026):**
- Confident AI — Component-wise evaluation enables debugging
- orq.ai Agent Evaluation — "Evaluate trajectory, not just a turn"
- Dextra Labs Agentic AI Safety Playbook — "Required infrastructure, not nice-to-have"
- Superagent Framework — Declarative safety policies
- OWASP 2025 — Prompt injection is #1 risk

**Execution Frameworks (2025-2026):**
- IBM ReAct Agent — Standard for combining reasoning with tool use
- AG2 ReAct Loops — Advanced loop evaluation patterns
- Prompting Guide ReAct — De facto prompting standard

**Practitioner Patterns:**
- NetworkChuck multi-CLI workflow (2025)
- Cross-tool context synchronization patterns
- Session state persistence patterns

**Research Findings:**
- Context editing reduces token consumption 84%
- Fresh context validation eliminates confirmation bias
- State machine orchestration improves reliability
- Sub-agent isolation protects main conversation context
- "A focused 300-token context often outperforms an unfocused 113,000-token context" (Google ADK)
- Memory distillation achieves 80-95% compression while preserving decision fidelity
- Trajectory evaluation catches decision-path issues missed by outcome-only evaluation
- Production guardrails add < 100ms latency with proper implementation

---

## Appendix F: Cross-Platform Agent Support (2025-2026)

This appendix documents platform-specific agent capabilities for implementers building LLM-agnostic agent systems.

### Platform Support Matrix

| Platform | Local Agent Files | System Prompt Override | Tool Restrictions | Agent Installation |
|----------|-------------------|----------------------|-------------------|-------------------|
| **Claude Code** | `.claude/agents/*.md` | CLAUDE.md | ✅ Via YAML frontmatter | Supported |
| **Codex CLI** | ❌ (`AGENTS.md` = project instructions) | `AGENTS.md`, `codex.md` | ❌ | N/A |
| **Gemini CLI** | ❌ | `GEMINI.md`, `.gemini/system.md` | ❌ | N/A |
| **ChatGPT Desktop** | ❌ | Built-in agent mode | ❌ | N/A |
| **Grok/Perplexity** | ❌ | Cloud-based | ❌ | N/A |

### Key Findings

**Claude Code Agent System:**
- Agents defined in `.claude/agents/*.md` with YAML frontmatter
- **Tool restrictions in frontmatter** = hard enforcement
- Agents invocable via `/agent:name` or Task tool with `subagent_type`
- Example frontmatter:
```yaml
---
name: orchestrator
description: Governance-first coordinator
tools: Read, Glob, Grep, Task, mcp__ai-governance__*
model: inherit
---
```

**Codex CLI (OpenAI) Clarification:**
- `AGENTS.md` is **project instructions** (like CLAUDE.md), NOT agent definitions
- No local agent file system
- Agents are system-level (cloud-managed)

**Gemini CLI:**
- `GEMINI.md` at project root = project-specific instructions
- `.gemini/system.md` = system prompt override
- No agent definition format

### Enforcement Levels

| Level | Mechanism | Strength | Platform Coverage |
|-------|-----------|----------|-------------------|
| **Tool Restrictions** | YAML frontmatter limits available tools | HARD | Claude Code only |
| **Behavioral Instructions** | SERVER_INSTRUCTIONS, system prompts | SOFT | All platforms |
| **Per-Response Reminders** | Appended to tool responses | SOFT | All platforms |

### Design Implications for LLM-Agnostic Systems

1. **MCP is the Universal Layer**: Expose agents via MCP tools/resources, not local files
2. **SERVER_INSTRUCTIONS for Soft Enforcement**: All platforms receive behavioral guidance
3. **Agent Installation for Hard Enforcement**: Only Claude Code supports local agent files with tool restrictions
4. **Detect Platform Before Installing**: Check for `.claude/` or `CLAUDE.md` before offering installation
5. **Graceful Degradation**: Non-Claude platforms work via SERVER_INSTRUCTIONS (soft enforcement still better than none)

### Implementation Pattern: Platform-Aware Agent Installation

```python
def detect_claude_code_environment() -> bool:
    """Check for Claude Code indicators."""
    cwd = Path.cwd()
    if (cwd / ".claude").is_dir():
        return True
    if (cwd / "CLAUDE.md").is_file():
        return True
    # Check parent directories (up to 3 levels)
    for parent in [cwd.parent, cwd.parent.parent, cwd.parent.parent.parent]:
        if (parent / ".claude").is_dir() or (parent / "CLAUDE.md").is_file():
            return True
    return False

# Usage in MCP tool
if not detect_claude_code_environment():
    return {"status": "not_applicable", "message": "Governance active via SERVER_INSTRUCTIONS"}
```

### User Communication Template

When offering agent installation to users unfamiliar with the concept:

> **What is an Agent?**
> An agent is a specialized configuration that guides how your AI assistant approaches tasks. Think of it as giving your AI a specific "role" with clear responsibilities and boundaries.
>
> **Why Install?**
> Installation adds tool restrictions that structurally enforce governance (the AI cannot access edit/write tools without passing governance checks). Without installation, governance is advisory-only.
>
> **What Gets Created?**
> A single markdown file (`.claude/agents/orchestrator.md`) containing the agent's role definition, tool permissions, and behavioral protocol.

### Research Sources

- Claude Code Documentation: Agent definitions and Task tool
- OpenAI Codex CLI: AGENTS.md specification
- Google Gemini CLI: Settings and system prompt documentation
- Platform testing: Direct verification of agent file support (2026-01)

---

**End of Document**

[Tool-specific appendices may be extended as new CLI tools emerge]
