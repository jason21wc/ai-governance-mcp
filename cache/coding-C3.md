#### C3. Session State Continuity (The Persistent Memory Act)

**Failure Mode(s) Addressed:**
- **A2: Context Loss Between Sessions → Inconsistent Outputs** — AI "forgets" decisions, architecture, and progress between sessions, causing redundant work and contradictory implementations.

**Constitutional Basis:**
- Derives from **C1 (Context Engineering):** Maintain necessary information across interactions—sessions are just interaction boundaries
- Derives from **G3 (Documentation):** Capture decisions and rationale for future reference
- Derives from **C2 (Single Source of Truth):** Centralized state management prevents conflicting sources

**Why Meta-Principles Alone Are Insufficient:**
Meta-Principle G3 states "document decisions for future reference" but doesn't address the **unique statelessness of AI sessions**. Traditional documentation assumes human memory bridges gaps between documents. AI sessions have no memory—each starts completely fresh. This domain principle establishes: (1) what state components must persist, (2) protocols for session start/end, and (3) mechanisms for seamless resumption.

**Domain Application:**
AI coding sessions reset between interactions, losing ALL context. Multi-session development projects require explicit state management mechanisms to maintain continuity: what's been completed, what decisions were made, what's next, and why. Without state continuity, each session starts from zero, causing redundant work ("re-contextualizing"), contradictory decisions, and lost architectural coherence.

**State Components Required:**
1. **Progress Tracking:** Current phase, completed phases, next actions
2. **Decision History:** Choices made with rationale (ADRs)
3. **Context References:** Which outputs exist, their locations, what they contain
4. **Validation Status:** What's passed gates, what's pending
5. **Recovery Capability:** Ability to restore to previous valid state

**Truth Sources:**
- Orchestrator state files (JSON tracking project status)
- Session handoff documents (Markdown summaries for human + AI consumption)
- Transaction logs (chronological record of changes within and across sessions)
- Recovery points (save states for rollback)
- Decision logs / Architecture Decision Records (ADRs)

**How AI Applies This Principle:**
- **Session Start Protocol (MANDATORY):**
  1. Load orchestrator state to understand current project status
  2. Read last session handoff to understand recent work and next steps
  3. Review recent transaction log entries for context on latest decisions
  4. Confirm understanding before proceeding: *"Resuming from [state]. Last session completed [X]. Current phase: [Y]. Next steps: [Z]. Correct?"*
  5. If state conflicts with observed codebase, FLAG for Product Owner clarification
- **Session End Protocol (MANDATORY):**
  1. Update orchestrator state: current phase, completed work, pending items, blockers
  2. Write session handoff: human-readable summary of what was accomplished and what's next
  3. Append to transaction log: machine-readable record of all changes and decisions
  4. Create recovery point if major milestone reached (phase completion, architectural decision)
  5. Document any decisions made with rationale (ADRs for significant choices)
- **Continuous Updates:** Update state files progressively DURING session, not just at end. Session crashes shouldn't lose all progress.
- **Conflict Resolution Protocol:** If current state conflicts with observed reality (codebase differs from state claims):
  1. STOP work
  2. Flag discrepancy explicitly
  3. Request Product Owner guidance on which source to trust
  4. Do NOT proceed with conflicting state

**Why This Principle Matters:**
Amnesia defeats expertise. *This corresponds to "Stare Decisis"—courts rely on precedent to ensure consistency. AI sessions have no inherent memory; without explicit state persistence, each session starts from zero, making different decisions than prior sessions. State continuity transforms isolated interactions into coherent project development.*

**When Product Owner Interaction Is Needed:**
- ⚠️ Session state conflicts with observed codebase state (reality doesn't match records)
- ⚠️ State files are missing, corrupted, or incomplete
- ⚠️ Making major state transitions (phase changes, architectural pivots, scope changes)
- ⚠️ Recovery needed from failed session (rollback decision)
- ⚠️ Multiple conflicting state sources exist

**Common Pitfalls or Failure Modes:**
- **The "Clean Slate" Trap:** Not loading state at session start, causing AI to re-discover or contradict previous work. *Prevention: Session start protocol is MANDATORY, not optional.*
- **The "Stale State" Trap:** Not updating state during session, causing state drift from reality. *Prevention: Continuous updates, not just end-of-session.*
- **The "State Explosion" Trap:** Storing too much detail in state files, causing context overflow when loading state. *Prevention: Store summaries in state; details in external references.*
- **The "Verbal Agreement" Trap:** Making decisions in conversation but not persisting to state files. *Prevention: If it's not in state files, it didn't happen.*
- **The "Single Point of Failure" Trap:** Relying on one state file that, if corrupted, loses everything. *Prevention: Multiple state components (orchestrator, handoff, transaction log, recovery points).*

**Success Criteria:**
- ✅ Every session STARTS with state loading and confirmation
- ✅ Every session ENDS with state updates and handoff creation
- ✅ State files track: current phase, completed work, pending tasks, decisions made, validation status
- ✅ New session can resume exactly where previous session ended
- ✅ Re-contextualization time: <5% of session (configurable threshold)
- ✅ Zero contradictory decisions due to forgotten prior reasoning

---

### P-Series: Process Principles
