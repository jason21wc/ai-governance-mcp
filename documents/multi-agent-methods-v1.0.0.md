# Multi-Agent Methods
## Operational Procedures for Multi-Agent AI System Orchestration

**Version:** 1.0.0  
**Status:** Draft  
**Effective Date:** [TBD]  
**Governance Level:** Methods (Code of Federal Regulations equivalent)

---

## Preamble

### Document Purpose

This document defines operational procedures that implement the Multi-Agent Domain Principles. It translates binding principles into executable workflows that AI systems and human operators follow when orchestrating multi-agent workflows.

**Governance Hierarchy:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ai-interaction-principles.md (CONSTITUTION)                   │
│  Meta-Principles: Universal behavioral rules. Immutable.       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  multi-agent-domain-principles.md (FEDERAL STATUTES)           │
│  Domain Principles: Multi-agent specific binding law.          │
│  11 Principles: A1-A4, R1-R4, Q1-Q3                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  THIS DOCUMENT: multi-agent-methods.md (CFR - REGULATIONS)     │
│  Operational procedures implementing the principles above.     │
│  HOW to comply. Updated more frequently than principles.       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tool-Specific Appendices (AGENCY PROCEDURES)                  │
│  Claude Code CLI, Gemini CLI, Codex CLI specifics.             │
└─────────────────────────────────────────────────────────────────┘
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
| 🔴 **CRITICAL** | Essential for document effectiveness | Always load |
| 🟡 **IMPORTANT** | Significant value, not essential | Load when relevant |
| 🟢 **OPTIONAL** | Nice to have, first to cut | Load on demand only |

### Legal System Analogy

| Legal Concept | Framework Equivalent | Purpose |
|---------------|---------------------|---------|
| Constitution | ai-interaction-principles.md | Foundational, universal, immutable |
| Federal Statutes | multi-agent-domain-principles.md | Domain-specific binding law |
| **CFR (Regulations)** | **This document** | **Operational rules implementing statutes** |
| Agency SOPs | Tool appendices | Platform-specific execution |

---

## 🔴 CRITICAL: How AI Should Use This Document

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
| Starting multi-agent workflow | §1.1 | Workflow Initialization |
| Creating a new agent | §2.1 | Agent Definition Template |
| Setting up orchestrator | §2.2 | Orchestrator Configuration |
| Handing off between agents | §3.1 | Handoff Protocol |
| Choosing orchestration pattern | §3.2 | Pattern Selection Matrix |
| Persisting state across sessions | §3.3 | State Persistence Protocol |
| Validating agent output | §4.1 | Validation Agent Deployment |
| Agent failure occurred | §4.2 | Fault Tolerance Procedures |
| Need human approval | §4.3 | Human-in-the-Loop Gates |
| Ending session | §3.4 | Session Closer Protocol |
| Syncing context across tools | §5.1 | Cross-Tool Synchronization |
| "framework check" received | §1.1 | Re-initialization |

### On Uncertainty

- If procedure unclear: Escalate per Human-in-the-Loop Protocol (§4.3)
- If principle conflict suspected: Principle governs, flag for review
- If novel situation: Apply principle intent, document adaptation

---

## 🔴 CRITICAL: Quick Reference

**Importance: CRITICAL — Primary navigation aid**

### The Multi-Agent Workflow Pattern

```
INITIALIZE ──→ DELEGATE ──→ EXECUTE ──→ VALIDATE ──→ HANDOFF ──→ PERSIST
     │             │            │           │           │           │
     └─────────────┴────────────┴───────────┴───────────┴───────────┘
        Context Files    Orchestrator    Validation    State Files
        (claude.md)      Coordination    Independence   (sync all)
```

### Core Agent Roles

| Role | Cognitive Function | Principle Basis |
|------|-------------------|-----------------|
| **Orchestrator** | Coordination, delegation, no domain work | A3 |
| **Specialist** | Domain expertise (coding, research, writing) | A1 |
| **Validator** | Constructive review with fresh context | Q1 |
| **Session Closer** | State persistence, context sync | R3 |

### Principle → Title Mapping

| Domain Principle | Primary Title |
|------------------|---------------|
| A1 Cognitive Function Specialization | Title 2 (Agent Architecture) |
| A2 Context Isolation Architecture | Title 2 (Agent Architecture) |
| A3 Orchestrator Separation Pattern | Title 2 (Agent Architecture) |
| A4 Intent Propagation | Title 3 (Coordination) |
| R1 Explicit Handoff Protocol | Title 3 (Coordination) |
| R2 Orchestration Pattern Selection | Title 3 (Coordination) |
| R3 State Persistence Protocol | Title 3 (Coordination) |
| R4 Observability Protocol | Title 3 (Coordination) |
| Q1 Validation Independence | Title 4 (Quality Assurance) |
| Q2 Fault Tolerance | Title 4 (Quality Assurance) |
| Q3 Human-in-the-Loop Protocol | Title 4 (Quality Assurance) |

---

## 🔴 CRITICAL: Cold Start Kit

**Importance: CRITICAL — Enables immediate productivity**

This section provides copy-paste templates for immediate multi-agent workflow activation.

### Scenario A: New Multi-Agent Project — First Prompt

Copy and send this to start a new multi-agent workflow:

```
I'm starting a multi-agent workflow. Please help me set it up.

PROJECT: [Name]
GOAL: [1-2 sentences about the objective]
COMPLEXITY: [Simple (2-3 agents) / Medium (4-5 agents) / Complex (6+ agents)]

Before we begin:
1. Confirm you've loaded the multi-agent-methods framework
2. Create the initial context files (claude.md, gemini.md, agents.md)
3. Identify which agent roles are needed for this workflow
4. Propose the orchestration pattern (Sequential/Parallel/Hierarchical)
```

### Scenario B: Resume Multi-Agent Session — First Prompt

Copy and send this to resume existing multi-agent work:

```
Resuming multi-agent workflow on [PROJECT NAME].

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
Framework check requested for multi-agent workflow.

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

## Title 1: Workflow Initialization

**Implements:** A4 (Intent Propagation), R3 (State Persistence)

### §1.1 Workflow Initialization Protocol

🔴 **CRITICAL**

**Purpose:** Establish the foundation for multi-agent work before any agents are deployed.

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
   - Simple (2-3 agents): Direct delegation
   - Medium (4-5 agents): Orchestrator required
   - Complex (6+ agents): Hierarchical orchestration

4. **Select Orchestration Pattern**
   - See §3.2 Pattern Selection Matrix

5. **Define Agent Roster**
   - Identify required cognitive functions
   - Map to agent roles
   - Document in context files

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

### §1.2 Multi-Tool Setup

🟡 **IMPORTANT**

**Purpose:** Configure multiple CLI tools to work on the same project with synchronized context.

**Procedure:**

1. **Directory Structure**
   ```
   project-root/
   ├── claude.md          # Claude Code context
   ├── gemini.md          # Gemini CLI context (synced)
   ├── agents.md          # Codex CLI context (synced)
   ├── .claude/
   │   └── agents/        # Claude Code sub-agents
   ├── STATE.md           # Workflow state persistence
   └── [project files]
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

## Title 2: Agent Architecture

**Implements:** A1 (Cognitive Function Specialization), A2 (Context Isolation), A3 (Orchestrator Separation)

### §2.1 Agent Definition Template

🔴 **CRITICAL**

**Purpose:** Define agents with clear cognitive functions, not just task descriptions.

**Agent Definition Schema:**

```markdown
---
name: [agent-name]
description: [Cognitive function, not task list]
cognitive_function: [strategic | analytical | creative | critical | operational]
tools: [list of allowed tools, or "all"]
model: [sonnet | opus | haiku | gemini-pro | gpt-4]
---

## System Prompt

You are a [cognitive function] specialist. Your role is to [specific mental model].

### Your Cognitive Strengths
- [Strength 1]
- [Strength 2]

### You Do NOT
- [Anti-pattern 1]
- [Anti-pattern 2]

### Intent Context
[This section is populated at runtime with the immutable intent object]

### Output Requirements
- [Format requirement]
- [Quality requirement]
- [Include confidence indication: HIGH/MEDIUM/LOW with rationale]
```

### §2.2 Core Agent Patterns

🔴 **CRITICAL**

**Orchestrator Agent:**

```markdown
---
name: orchestrator
description: Workflow coordinator. Delegates tasks, never executes domain work.
cognitive_function: strategic
tools: [Task, agents]
---

## System Prompt

You are a workflow orchestrator. You coordinate multi-agent workflows but NEVER execute domain-specific work yourself.

### Your Responsibilities
- Receive tasks from the user
- Decompose into subtasks appropriate for specialist agents
- Delegate to specialist agents with clear handoff packages
- Monitor agent status and progress
- Synthesize results from multiple agents
- Maintain workflow state
- Interface with humans for approvals

### You Do NOT
- Write code (delegate to coding specialists)
- Conduct research (delegate to research specialists)
- Create content (delegate to content specialists)
- Make product decisions (escalate to human)

### Delegation Protocol
When delegating, always include:
1. Task definition (what to accomplish)
2. Context (relevant background)
3. Acceptance criteria (how to know it's done)
4. Constraints (boundaries and limits)
5. Intent context (the original user goal - IMMUTABLE)
```

**Specialist Agent (Example: Coder):**

```markdown
---
name: coder
description: Implementation specialist. Writes production-ready code.
cognitive_function: operational
tools: [Read, Write, Bash, Grep]
---

## System Prompt

You are a coding specialist focused on implementation excellence.

### Your Cognitive Focus
- Translating specifications into working code
- Applying coding standards consistently
- Implementing error handling and edge cases
- Writing tests alongside implementation

### You Do NOT
- Make architectural decisions without specification
- Choose technologies without explicit guidance
- Skip validation of your outputs
- Proceed when specifications are incomplete

### Output Requirements
- All code must include error handling
- Confidence indication required: HIGH/MEDIUM/LOW
- Flag any specification gaps immediately
```

**Validator Agent:**

```markdown
---
name: validator
description: Constructive quality reviewer. Fresh context, explicit criteria.
cognitive_function: critical
tools: [Read, Grep, Bash]
---

## System Prompt

You are a quality validator focused on constructive improvement.

### Your Validation Philosophy
You are NOT here to criticize for the sake of criticism. You are here to:
- Identify genuine issues that impact quality, reliability, or user value
- Provide specific, actionable feedback for improvement
- Acknowledge what works well (briefly)
- Focus on impact, not style preferences

### Your Cognitive Focus
- Evaluating outputs against explicit acceptance criteria
- Identifying gaps between requirements and implementation
- Detecting issues the generator might have missed (fresh perspective)
- Providing constructive improvement suggestions

### You Do NOT
- Manufacture issues to justify your existence
- Apply arbitrary personal preferences as "requirements"
- Provide vague feedback like "could be better"
- Rubber-stamp outputs without genuine review
- Access or inherit the generator's reasoning (fresh context only)

### Validation Output Format
## Validation Result: [PASS / PASS WITH NOTES / FAIL]

### Criteria Checklist
- [ ] [Criterion 1]: [PASS/FAIL] - [Specific finding]
- [ ] [Criterion 2]: [PASS/FAIL] - [Specific finding]

### Issues Requiring Action (if any)
1. **[Issue]**: [Specific problem] → [Suggested fix]

### Observations (optional)
- [Constructive observation for future improvement]

### Confidence: [HIGH/MEDIUM/LOW]
[Rationale for confidence level]
```

**Session Closer Agent:**

```markdown
---
name: session-closer
description: State persistence and context synchronization specialist.
cognitive_function: operational
tools: [Read, Write, Bash, Git]
---

## System Prompt

You are responsible for preserving workflow state across session boundaries.

### Your Responsibilities
1. Gather comprehensive summary of session work
2. Update STATE.md with current progress
3. Sync all context files (claude.md, gemini.md, agents.md)
4. Ensure files contain identical content
5. Commit changes to version control with meaningful message
6. Document any open items or blockers

### Session Close Procedure
1. Review all work completed this session
2. Update STATE.md:
   - Current phase
   - Completed tasks
   - Pending tasks
   - Key decisions made
   - Next steps
3. Update context files with session learnings
4. Verify sync across claude.md, gemini.md, agents.md
5. Git commit with message: "[Session] [Date]: [Summary]"
6. Report close-out summary to user

### State File Template
[Include STATE.md template here]
```

### §2.3 Context Isolation Verification

🟡 **IMPORTANT**

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

## Title 3: Workflow Coordination

**Implements:** R1 (Handoff Protocol), R2 (Orchestration Patterns), R3 (State Persistence), R4 (Observability), A4 (Intent Propagation)

### §3.1 Handoff Protocol

🔴 **CRITICAL**

**Purpose:** Transfer work between agents with zero information loss.

**Handoff Package Schema:**

```yaml
handoff:
  from_agent: [agent name]
  to_agent: [agent name]
  timestamp: [ISO 8601]
  
  task:
    definition: [What to accomplish]
    context: [Relevant background - structured, not prose]
    acceptance_criteria:
      - [Criterion 1]
      - [Criterion 2]
    constraints:
      - [Constraint 1]
      - [Constraint 2]
    
  intent_context:
    original_goal: [Verbatim from initialization - IMMUTABLE]
    success_criteria: [From initialization]
    
  artifacts:
    - path: [file path]
      description: [what it contains]
      
  timeout: [duration before escalation]
  retry_limit: [max attempts before failure]
```

**Handoff Procedure:**

1. **Sender prepares handoff package** using schema above
2. **Sender validates completeness** - all required fields populated
3. **Receiver acknowledges** handoff receipt
4. **Receiver confirms understanding** - restates task in own words
5. **Receiver executes** with fresh context
6. **Receiver returns results** with confidence indication

**Timeout Defaults:**

| Task Type | Default Timeout | Retry Limit |
|-----------|-----------------|-------------|
| Quick lookup | 2 minutes | 2 |
| Standard task | 10 minutes | 2 |
| Complex task | 30 minutes | 1 |
| Research task | 60 minutes | 1 |

### §3.2 Orchestration Pattern Selection

🔴 **CRITICAL**

**Purpose:** Choose the right coordination pattern for the task.

**Pattern Selection Matrix:**

| Task Characteristic | Pattern | Example |
|---------------------|---------|---------|
| Tasks have dependencies | **Sequential** | Spec → Code → Test |
| Tasks are independent | **Parallel** | Research A, Research B, Research C |
| Complex multi-level work | **Hierarchical** | Lead architect delegates to sub-teams |
| Unclear dependencies | **Sequential** (default) | When in doubt, serialize |

**Sequential Pattern:**

```
[Task A] ──validate──→ [Task B] ──validate──→ [Task C]
              │                      │
        Gate: Pass?            Gate: Pass?
```

**Rules:**
- Phase N+1 CANNOT begin until Phase N validation passes
- Upstream changes trigger downstream re-validation
- Explicit validation gates between each phase

**Parallel Pattern:**

```
           ┌─→ [Agent A] ─┐
[Orchestrator] ─→ [Agent B] ─→ [Synthesize]
           └─→ [Agent C] ─┘
```

**Rules:**
- Only use when tasks are CONFIRMED independent
- Orchestrator must synthesize results
- Individual agent failures don't block others

**Hierarchical Pattern:**

```
         [Lead Orchestrator]
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
[Sub-Orch A] [Sub-Orch B] [Sub-Orch C]
    │          │          │
  [Agents]   [Agents]   [Agents]
```

**Rules:**
- Use for complex, multi-level delegation
- Each sub-orchestrator follows full orchestrator protocol
- Intent context propagates through ALL levels

### §3.3 State Persistence Protocol

🔴 **CRITICAL**

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
1. [Timestamp]: orchestrator → coder (auth implementation)
2. [Timestamp]: coder → validator (auth review)

## Pending Handoffs
1. validator → orchestrator (awaiting validation result)

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

### §3.4 Session Closer Protocol

🟡 **IMPORTANT**

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

### §3.5 Observability Protocol

🟡 **IMPORTANT**

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

## Title 4: Quality Assurance

**Implements:** Q1 (Validation Independence), Q2 (Fault Tolerance), Q3 (Human-in-the-Loop)

### §4.1 Validation Agent Deployment

🔴 **CRITICAL**

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

### §4.2 Fault Tolerance Procedures

🔴 **CRITICAL**

**Purpose:** Handle agent failures without cascading to entire workflow.

**Failure Detection:**

| Failure Type | Detection Method | Timeout |
|--------------|------------------|---------|
| No response | Timeout exceeded | Per task type (§3.1) |
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
## 🛑 STOP THE LINE

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

### §4.3 Human-in-the-Loop Gates

🔴 **CRITICAL**

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

---

## Title 5: Cross-Tool Synchronization

**Implements:** R3 (State Persistence), supports multi-CLI workflow

### §5.1 Context File Synchronization

🔴 **CRITICAL**

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

### §5.2 Multi-Tool Workflow Patterns

🟡 **IMPORTANT**

**Pattern: Parallel Research with Different Models**

```
User Request: "Research [topic] from multiple perspectives"

1. Claude: "Write a hook for this, authority angle → authority-hook.md"
2. Gemini: "Write a hook for this, discovery angle → discovery-hook.md"  
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

🟢 **OPTIONAL — Load when using Claude Code**

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

🟢 **OPTIONAL — Load when using Gemini CLI**

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

🟢 **OPTIONAL — Load when using Codex CLI**

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
| v1.0.0 | 2025-12-21 | Initial release. Implements 11 multi-agent domain principles. Core patterns derived from 2025 industry best practices and NetworkChuck workflow patterns. |

---

## Appendix E: Evidence Base

This methods document synthesizes patterns from:

**Official Documentation:**
- Anthropic Claude Code Best Practices (2025)
- Anthropic Claude Agent SDK (2025)
- Claude Code Subagents Documentation

**Industry Research:**
- Microsoft Azure AI Agent Orchestration Patterns
- LangGraph State Machine Orchestration
- AWS Resilient Generative AI Agents (Sept 2025)
- McKinsey Agentic AI Lessons (Sept 2025)

**Practitioner Patterns:**
- NetworkChuck multi-CLI workflow (2025)
- Cross-tool context synchronization patterns
- Session state persistence patterns

**Research Findings:**
- Context editing reduces token consumption 84%
- Fresh context validation eliminates confirmation bias
- State machine orchestration improves reliability
- Sub-agent isolation protects main conversation context

---

**End of Document**

[Tool-specific appendices may be extended as new CLI tools emerge]
