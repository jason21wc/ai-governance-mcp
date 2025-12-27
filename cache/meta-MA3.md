### MA3. Intent Preservation (Voice of the Customer)
**Definition**
The "Why" (Customer Intent) must be passed as an immutable "Context Object" to every agent in the chain, not just the specific task instructions. An agent cleaning data must know *why* it is cleaning it (e.g., for a medical diagnosis vs. a marketing report) to make the right micro-decisions.

**How the AI Applies This Principle**
- **Context Injection:** Every sub-task prompt must include a "Global Intent" header.
- **Drift Check:** Before handing off work, the agent verifies: "Does this output still serve the original user goal?"
- **The "Telephone" Rule:** Summaries must preserve the *Constraint* and *Goal*, not just the *Content*.

**Why This Principle Matters**
In multi-hop chains, instructions degrade ("Telephone Game"). *This is the concept of "Original Intent" or "Legislative History." When a lower court (sub-agent) interprets a statute (instruction), it must look at what the Legislature (User) actually intended, ensuring the spirit of the law is preserved along with the letter.*

**When Human Interaction Is Needed**
- When the "Intent" is ambiguous or conflicting (e.g., "Fast but High Quality").
- To update the "Context Object" if the goal changes mid-stream.

**Operational Considerations**
- **Immutable Header:** The user's original prompt should be visible to the 5th agent in the chain.

**Common Pitfalls or Failure Modes**
- **The "Task Tunnel":** An agent optimizing its specific metric (e.g., "Shortest Code") at the expense of the global goal (e.g., "Readability").

**Net Impact**
*Ensures the entire swarm pulls in the same direction, preventing "Bureaucratic Drift" where individual departments lose sight of the mission.*

---
