# Multi-Agent Methods
## Operational Procedures for AI Agent Orchestration

**Version:** 2.4.0
**Status:** Active
**Effective Date:** 2026-01-04
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
| Starting agent workflow | §1.2 | Workflow Initialization |
| Creating a new agent | §2.1 | Agent Definition Standard |
| Writing effective system prompts | §2.1.1 | System Prompt Best Practices |
| Deciding which tools to allow | §2.1.2 | Tool Scoping Guidelines |
| Testing agent before deployment | §2.1.3 | Agent Validation Checklist |
| Choosing an agent pattern | §2.2 | Agent Catalog |
| Setting up orchestrator | §2.3 | Orchestrator Configuration |
| Choosing handoff pattern | §3.1 | Handoff Pattern Taxonomy |
| Handing off between agents | §3.2 | Handoff Protocol |
| Choosing orchestration pattern | §3.3 | Pattern Selection Matrix |
| Compressing context at boundary | §3.4 | Compression Procedures |
| Persisting state across sessions | §3.5 | State Persistence Protocol |
| Validating agent output | §4.1 | Validation Agent Deployment |
| Need devil's advocate review | §4.2 | Contrarian Reviewer Pattern |
| Need governance compliance check | §4.3 | Governance Agent Pattern |
| Agent failure occurred | §4.4 | Fault Tolerance Procedures |
| Need human approval | §4.5 | Human-in-the-Loop Gates |
| Making governance structural | §4.6 | Governance Enforcement Architecture |
| Non-Claude platform enforcement | §4.6.2 | Gateway-Based Enforcement |
| Ending session | §3.6 | Session Closer Protocol |
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

### 2.1 Agent Definition Standard

CRITICAL

**Purpose:** Standardize how agents are defined to ensure consistency and completeness.

**Source:** Anthropic Claude Agent SDK, NetworkChuck AI-in-Terminal patterns

**Key Concept — Modular Personalities:** An agent is not a separate program—it's a specialized *configuration* of the same underlying model. Think of it as a "hat" the AI wears: different system prompt, different tools, different cognitive focus. The same base model becomes a coder, validator, or orchestrator based on its agent definition.

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
4. **Output Format** — Structured output template
5. **Success Criteria** — How to know the task is complete

**Agent Definition Template:**

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

**Platform-Specific Notes:**

- **Claude Code:** Tool restrictions in YAML frontmatter are HARD enforcement
- **Other platforms:** May require gateway-based enforcement (see §4.6.2)

#### 2.1.3 Agent Validation Checklist

IMPORTANT

**Purpose:** Verify agent effectiveness before deployment.

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

1. Draft agent definition with Claude A
2. Deploy to project/user scope
3. Test with Claude B in new session
4. Collect failure cases
5. Refine with Claude A
6. Repeat until validation passes

**Graduation Criteria:**

Agent is production-ready when:
- [ ] All Phase 1 checklist items pass
- [ ] All Phase 2 test cases pass
- [ ] Phase 3 integration confirmed
- [ ] At least 3 real-world uses without modification needed

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

**Industry Research (2025):**
- Anthropic Multi-Agent Research System (90.2% improvement, 15x tokens)
- Google ADK "Architecting Efficient Context-Aware Multi-Agent Framework" (Agents-as-Tools vs Agent-Transfer)
- Cognition "Don't Build Multi-Agents" (conflicting assumptions, read-write division)
- LangChain "How and When to Build Multi-Agent Systems" (read-heavy parallelization)
- Microsoft Multi-Agent Reference Architecture (context engineering)
- Vellum "Multi-Agent Context Engineering" (Write/Select/Compress/Isolate)

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
