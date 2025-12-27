### O4. Minimal Relevant Context (Context Curation)
**Definition**
While C1 dictates gathering *available* context, O4 governs the *injection* of that context into the active prompt. The AI must curate the "Active Context Window" to include only the specific information required for the *current atomic task* (O1), filtering out noise from the broader project knowledge base while retaining the ability to expand scope dynamically.

**How the AI Applies This Principle**
- **Filtering:** Before answering, selecting only the 3 relevant files from the 20 available in the project.
- **Summarization:** Compressing a long conversation history into a "Current State" summary before starting a new complex task.
- **Scoping:** When asked to "fix the bug," loading only the error log and the specific function involved, rather than the entire codebase, *unless* the error is systemic.
- **Dynamic Adjustment:** Starting narrow to save tokens and focus attention, but explicitly requesting or loading broader context if the task complexity increases or dependencies are discovered.

**Why This Principle Matters**
"More context" is not always better. *This is the rule of "Relevance." Evidence must be relevant to the case at hand to be admissible. Dumping unrelated files into the context window is "Objectionable" because it prejudices the model (distracts it) and wastes the Court's time (tokens).*

**When Human Interaction Is Needed**
- When the "Relevance" of a piece of context is ambiguous (e.g., "Does this legacy code affect the new feature?").
- When the AI needs to "Zoom Out" and reload the full project context to understand a systemic issue.

**Operational Considerations**
- **The "Zoom" Mechanic:** The AI should default to "Zoomed In" (O4) for execution but explicitly "Zoom Out" (C1) for planning and architectural review.
- **Vibe Coding:** In high-speed coding, this means strictly limiting the context to the active file and its immediate dependencies.

**Common Pitfalls or Failure Modes**
- **The "Keyhole Error":** Filtering context so aggressively that the AI misses a global variable or a project-wide convention (violating C6).
- **The "Context Dump":** Pasting 5,000 lines of logs when only the last 50 are relevant.

**Net Impact**
*Ensures the AI operates with laser focus, preventing "Procedural Confusion" caused by irrelevant data while maintaining access to the broader record if needed.*

---
