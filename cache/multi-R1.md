### R1. Explicit Handoff Protocol

**Why This Principle Matters**

The constitutional principle MA2 (Handoffs) requires that transitions maintain state and avoid rework. In multi-agent systems with isolated contexts, handoffs are the ONLY mechanism for transferring work between agents. Implicit or informal handoffs lose critical information and force downstream agents to guess or hallucinate context. Additionally, MA5 (Standardized Protocols) requires structured contracts rather than conversational exchange—natural language is ambiguous; structured data is precise.

**Domain Application (Binding Rule)**

Every inter-agent transfer must follow an explicit handoff protocol that includes: task definition, relevant context, acceptance criteria, and constraints. Handoffs must use structured data formats, not conversational natural language. All handoffs must include deadlock prevention mechanisms (timeouts, retry limits). The receiving agent must have sufficient information to complete its task without accessing the sending agent's context.

**Constitutional Basis**

- MA2 (Handoffs): Transitions maintain state and avoid rework
- MA5 (Standardized Protocols): Structured contracts, not natural language; deadlock prevention required
- C1 (Context Engineering): Load necessary information to prevent hallucination
- G3 (Documentation): Capture decisions for future reference

**Truth Sources**

- Azilen Enterprise Patterns: Log every handoff between agents for traceability
- LangChain: Handoff patterns with explicit state transfer
- MA5: "All interactions must have defined timeouts to prevent deadlocks"

**How AI Applies This Principle**

1. Define handoff schema for each agent-to-agent transfer type
2. Use structured data format (not conversational prose) for all handoffs
3. Include: task definition, input context, acceptance criteria, constraints, relevant prior decisions
4. Specify timeout and retry limits for every handoff to prevent deadlocks
5. Validate handoff completeness and schema compliance before executing transfer
6. Log all handoffs for traceability and debugging
7. Receiving agent confirms understanding before proceeding

**Success Criteria**

- Every handoff follows defined structured schema
- No conversational/prose handoffs between agents
- Timeout and retry limits specified for all transfers
- Receiving agent can complete task without querying sending agent
- Handoff log enables reconstruction of decision flow
- No deadlocks (agents waiting indefinitely for each other)

**Human Interaction Points**

- Define handoff schema for novel agent interactions
- Review handoff logs when debugging multi-agent issues
- Resolve schema validation failures that agents cannot auto-resolve
- Approve handoff content for high-stakes transitions

**Common Pitfalls**

- **Context Assumptions:** Assuming receiving agent "knows" what sending agent knows
- **Chatty Handoffs:** Agents sending paragraphs of prose instead of structured data
- **Implicit References:** "Continue with the approach" without specifying which approach
- **Missing Constraints:** Handoff includes task but not boundaries or acceptance criteria
- **Infinite Wait:** Agent A waiting for Agent B, who is waiting for Agent A (deadlock)

**Configurable Defaults**

- Handoff schema: Task + Context + Criteria + Constraints (required fields)
- Handoff format: Structured data (specific format in methods)
- Timeout specification: Required (values configurable per task type)
- Handoff logging: Required (format configurable per tool)

---
