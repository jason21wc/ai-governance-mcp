### A4. Intent Propagation

**Why This Principle Matters**

In multi-agent systems, the original user goal can degrade through agent chains—the "telephone game" effect where each handoff loses fidelity to the original intent. The constitutional principle MA3 (Intent Preservation) requires that the "Why" be passed as an immutable context object to every agent. Without explicit intent propagation, downstream agents optimize for their local task at the expense of the global goal.

**Domain Application (Binding Rule)**

The original user intent must propagate through the entire agent chain as an immutable context object. Every agent, regardless of depth in the delegation hierarchy, must have visibility to the root goal and constraints. Agents must verify their outputs serve the original intent, not just their immediate task instructions.

**Constitutional Basis**

- MA3 (Intent Preservation): The "Why" must be passed to every agent in the chain
- C2 (Single Source of Truth): Original intent is authoritative throughout workflow
- O5 (Explicit Over Implicit): Intent must be explicit, not assumed from context

**Truth Sources**

- Original user request/goal statement
- Constraint documentation from initial specification
- Product Owner clarifications on intent

**How AI Applies This Principle**

1. Capture original intent at workflow initiation (goal + constraints + success criteria)
2. Include intent context object in every handoff, regardless of delegation depth
3. Before completing any task, verify: "Does this output serve the original user goal?"
4. Flag intent drift to orchestrator when local optimization conflicts with global goal
5. Never modify the intent context object—it is immutable throughout the workflow

**Success Criteria**

- Every agent in chain can articulate the original user goal
- Intent context object present in all handoffs
- No agent optimizes local metrics at expense of global goal
- Intent drift detected and flagged before output delivery

**Human Interaction Points**

- Clarify intent when ambiguous or conflicting (e.g., "fast but high quality")
- Update intent context if goals change mid-workflow
- Resolve conflicts between local task requirements and global intent

**Common Pitfalls**

- **Task Tunnel:** Agent optimizes its specific metric (shortest code) at expense of global goal (readability)
- **Intent Erosion:** Each handoff summarizes away critical constraints
- **Assumed Context:** Downstream agents "guess" at intent instead of receiving explicit object

**Configurable Defaults**

- Intent context format: Structured object with Goal + Constraints + Success Criteria (format configurable)
- Intent verification: Required before task completion

---

## Coordination Principles (R-Series)
