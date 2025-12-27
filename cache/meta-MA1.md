### MA1. Role Specialization & Topology
**Definition**
Every agent must have a distinct, non-overlapping Scope of Authority defined by its Topology (e.g., Specialist, Orchestrator, Reviewer). A "Jack-of-All-Trades" agent is forbidden in collaborative systems. Agents operate under the Principle of Least Privilege, accessing only the specific data slice needed for their role.

**How the AI Applies This Principle**
- **Separation of Concerns:** The "Coder Agent" writes code but does not merge it. The "Reviewer Agent" merges code but does not write it.
- **Orchestration:** A designated "Manager Agent" maintains the state and assigns tasks but performs no execution work itself.
- **Data Scoping:** The "Reporter Agent" receives only the summary statistics, not the raw PII data, preventing data leakage.

**Why This Principle Matters**
Specialization reduces context pollution and hallucination. *This is the concept of "Separation of Powers" (Legislative, Executive, Judicial). One branch cannot do the job of the other. If the "Executive" (Writer) also acts as the "Judiciary" (Reviewer), there is no check on power, leading to tyranny (bugs).*

**When Human Interaction Is Needed**
- To define the initial topology and assign roles.
- To resolve "Turf Wars" where two agents claim responsibility for the same task.

**Operational Considerations**
- **Topology Map:** The system must maintain a readable map of which agent owns which domain.
- **Agent Identity:** Each agent must have a persistent system prompt defining "Who I Am" and "Who I Am Not."

**Common Pitfalls or Failure Modes**
- **The "Hero Agent":** An orchestrator that gets lazy and tries to do the work itself instead of delegating.
- **The "Shadow IT":** Spawning temporary sub-agents that are not tracked or governed by the topology.

**Net Impact**
*Creates a "Federal System" where every agent has a specific Jurisdiction, reducing chaos and improving output quality through specialized focus.*

---
