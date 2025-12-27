### A2. Context Isolation Architecture

**Why This Principle Matters**

Context pollution—where information from one domain inappropriately influences another—is the primary cause of structural inconsistencies in multi-agent outputs. When agents share context windows or leak information between domains, errors compound rather than isolate. The constitutional principle C1 (Context Engineering) requires loading necessary information; for multi-agent systems, this means loading ONLY relevant information to EACH agent, preventing cross-contamination.

**Domain Application (Binding Rule)**

Each specialized agent must operate in a completely independent context window with zero unintended information cross-contamination between agents. Context flows through the orchestrator, not directly between execution agents. Each agent receives only context relevant to its cognitive function.

**Constitutional Basis**

- C1 (Context Engineering): Load necessary information—implies NOT loading unnecessary information
- MA2 (Handoffs): Transitions maintain state—implies state is transferred explicitly, not leaked
- O4 (Context Optimization): Minimize context consumption—implies isolation prevents bloat

**Truth Sources**

- LangChain research: Subagent isolation saves 67% tokens vs. context accumulation
- Anthropic research: Token usage explains 80% of performance variance
- Factory.ai: "Treat context as scarce, high-value resource"

**How AI Applies This Principle**

1. Create fresh context windows for each specialized agent spawn
2. Load only task-relevant information into each agent's context
3. Route all inter-agent communication through orchestrator
4. Never allow direct agent-to-agent context sharing
5. Explicitly transfer required outputs, not full context histories

**Success Criteria**

- Each agent spawn begins with fresh context window
- No agent can access another agent's internal reasoning or intermediate work
- Orchestrator manages all context flow between agents
- Context window utilization per agent is trackable and optimized

**Human Interaction Points**

- Approve context loading strategy for complex multi-agent workflows
- Review context isolation when debugging unexpected agent behavior
- Define what context is "relevant" for ambiguous tasks

**Common Pitfalls**

- **Context Dumping:** Passing full conversation history to sub-agents
- **Shared Memory Anti-Pattern:** Using shared memory stores without access controls
- **Result Bloat:** Passing verbose intermediate results instead of synthesized summaries

**Configurable Defaults**

- Maximum context transfer per handoff: Summary + essential inputs only (configurable per task complexity)
- Context window monitoring: Required (tool-specific implementation)

---
