### A1. Cognitive Function Specialization

**Why This Principle Matters**

In the constitutional framework, MA1 (Role Segregation) establishes that distinct functions require specialized roles. For multi-agent systems, this translates to a fundamental architectural decision: agent boundaries should align with cognitive functions, not workflow phases. An agent optimized for strategic thinking operates differently than one optimized for critical analysis or creative generation. Mixing cognitive functions in one agent creates internal conflicts and reduces output quality.

**Domain Application (Binding Rule)**

Each agent must be assigned a single cognitive function with clear domain boundaries. Cognitive functions are mental models or reasoning patterns (strategic analysis, creative synthesis, critical evaluation, research compilation, etc.), not workflow steps. An agent may participate in multiple workflow phases if they require the same cognitive function.

**Constitutional Basis**

- MA1 (Role Segregation): Specialized roles for distinct functions
- C2 (Single Source of Truth): Each cognitive function has one authoritative agent
- O3 (DRY - Don't Repeat Yourself): Avoid cognitive function duplication across agents

**Truth Sources**

- Agent system prompt defining cognitive function and boundaries
- Orchestrator documentation of agent-to-function mapping
- Research demonstrating 70% cognitive load reduction with specialization

**How AI Applies This Principle**

1. Before creating agents, identify distinct cognitive functions required for the task
2. Map each cognitive function to exactly one agent
3. Write agent system prompts that define the single cognitive function clearly
4. Prohibit agents from making decisions outside their cognitive domain
5. Flag cross-domain decisions for orchestrator routing or human escalation

**Success Criteria**

- Each agent has exactly one defined cognitive function
- Agent outputs contain no decisions outside their cognitive domain
- Cross-domain requirements route through orchestrator
- Agent system prompts explicitly state what is IN and OUT of scope

**Human Interaction Points**

- Define cognitive function boundaries for novel task types
- Resolve ambiguous cognitive domain assignments
- Approve agent specialization strategy for new multi-agent systems

**Common Pitfalls**

- **Function Bloat:** Assigning multiple cognitive functions to one agent "for efficiency"
- **Phase Confusion:** Defining agents by workflow phase instead of cognitive function
- **Boundary Creep:** Allowing agents to expand scope without explicit authorization

**Configurable Defaults**

- Maximum cognitive functions per agent: 1 (not configurable—this is the principle)
- Agent count: Determined by distinct cognitive functions required (no fixed limit)

---
