### R3. State Persistence Protocol

**Why This Principle Matters**

Multi-agent systems amplify the stateless session problem. Individual agent context, orchestration state, delegation history, and cross-agent decisions all require persistence to maintain coherence across sessions. The constitutional principle G3 (Documentation) requires capturing decisions for future reference; for multi-agent systems, this means comprehensive state management that enables any future session to reconstruct context and continue work.

**Domain Application (Binding Rule)**

Multi-agent workflow state must be persisted to structured files that survive session boundaries. State includes: current phase, agent assignments, completed tasks, pending handoffs, key decisions, and validation results. Session start must load persisted state; session end must save current state.

**Constitutional Basis**

- G3 (Documentation): Capture decisions for future reference
- MA2 (Handoffs): Transitions maintain state—includes cross-session transitions
- C1 (Context Engineering): Load necessary information—includes prior session context

**Truth Sources**

- AWS Bedrock AgentCore Memory: Short-term and long-term memory separation
- AI Coding Methods: SESSION-STATE.md, PROJECT-MEMORY.md patterns
- Context engineering research: Working memory + long-term memory architecture

**How AI Applies This Principle**

1. Define state schema covering all critical workflow information
2. Save state at session end and after significant milestones
3. Load state at session start before any agent work
4. Include: phase, assignments, decisions, validations, pending work, context summaries
5. Validate state integrity on load; flag corruptions for human review

**Success Criteria**

- New session can reconstruct full workflow context from persisted state
- No "what were we working on?" confusion across sessions
- State files are human-readable for debugging and auditing
- State corruption is detected and flagged, not silently accepted

**Human Interaction Points**

- Review state files when resuming complex multi-session projects
- Resolve state conflicts or corruptions
- Define state retention policy for long-running projects

**Common Pitfalls**

- **State Amnesia:** Starting fresh each session, losing prior progress
- **State Bloat:** Persisting everything, creating unmanageable state files
- **Implicit State:** Relying on conversation history instead of explicit state files

**Configurable Defaults**

- State file format: Markdown (human-readable, tool-agnostic)
- State save triggers: Session end + phase completion + significant decisions
- State retention: Until project completion (archive policy configurable)

---
