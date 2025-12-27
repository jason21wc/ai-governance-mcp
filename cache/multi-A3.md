### A3. Orchestrator Separation Pattern

**Why This Principle Matters**

The constitutional principle MA5 (Coordination Protocols) requires established protocols for agent interaction. In practice, this means a dedicated orchestrator must manage workflow, validation, and human interface WITHOUT executing domain-specific work. When an orchestrator also performs execution tasks, it becomes a "do everything" monolith that violates specialization and creates single points of failure. Separation of coordination from execution enables clear responsibility boundaries.

**Domain Application (Binding Rule)**

A dedicated orchestrator agent manages workflow coordination, validation gates, state tracking, and human interface. The orchestrator never executes phase-specific or domain-specific work—it delegates to specialized agents. The orchestrator is the single point of interface for the human Product Owner.

**Constitutional Basis**

- MA5 (Coordination Protocols): Established protocols govern interaction
- MA1 (Role Segregation): Orchestration is a distinct function from execution
- G3 (Documentation): Orchestrator maintains authoritative workflow state

**Truth Sources**

- Microsoft Azure: Agent orchestration patterns with explicit coordinator roles
- Google ADK: Hierarchical patterns with coordinator managing sub-agents
- Enterprise patterns: Orchestrator agent coordinates without executing

**How AI Applies This Principle**

1. Define orchestrator with explicit coordination-only responsibilities
2. Prohibit orchestrator from generating domain-specific outputs
3. Route all human interactions through orchestrator
4. Maintain workflow state, phase completion, and validation status in orchestrator
5. Spawn specialized agents for all execution work

**Success Criteria**

- Orchestrator outputs contain only: workflow coordination, validation management, human interface, state tracking
- No domain-specific implementations originate from orchestrator
- All specialized work traces to a specialized agent
- Human sees single coherent interface (orchestrator) not multiple agent interfaces

**Human Interaction Points**

- Define workflow phases and validation gates
- Approve phase transitions through orchestrator interface
- Receive synthesized results and decision points from orchestrator

**Common Pitfalls**

- **Orchestrator Overreach:** Orchestrator "helping" by doing execution work
- **Bypass:** Specialized agents communicating directly with human, bypassing orchestrator
- **State Fragmentation:** Workflow state scattered across multiple agents instead of centralized

**Configurable Defaults**

- Orchestrator execution permissions: None (coordination and delegation only)
- Human interface point: Orchestrator only (specialized agents do not interface directly)

---
