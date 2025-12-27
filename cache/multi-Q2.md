### Q2. Fault Tolerance and Graceful Degradation

**Why This Principle Matters**

Multi-agent systems have multiple failure points—any agent can fail, any handoff can corrupt, any context can overflow. Without explicit fault tolerance, a single failure cascades through the agent network, corrupting all downstream outputs. The constitutional principle Q3 (Fail-Fast) requires catching failures early; for multi-agent systems, this extends to isolating failures and degrading gracefully. Additionally, MA4 (Blameless Error Reporting) establishes that any agent can "stop the line" when critical issues are detected—this authority must be preserved and respected.

**Domain Application (Binding Rule)**

Multi-agent workflows must implement fault isolation and graceful degradation. Agent failures must not cascade to other agents. Failed operations must be retried, escalated, or gracefully degraded—never silently ignored or passed downstream. Any agent detecting a critical safety or logic flaw can halt the entire workflow ("stop the line") without penalty. The orchestrator detects failures and implements recovery or degradation protocols.

**Constitutional Basis**

- Q3 (Fail-Fast): Catch failures early and prevent propagation
- Q7 (Failure Recovery): Explicit strategies for recovering from errors
- MA4 (Blameless Error Reporting): Any agent can halt workflow; reporting failure is success
- G3 (Documentation): Log all failures, near-misses, and recovery actions

**Truth Sources**

- Microsoft Azure: Checkpoint features for recovery from interrupted orchestration
- Databricks: Retry strategies, fallback logic, simpler fallback chains
- Azilen: Fallback paths for resilience; if one agent fails, system remains functional
- MA4: "The 'Stop the Line' Cord: Any agent can halt the entire assembly line"

**How AI Applies This Principle**

1. Define failure detection for each agent type (timeout, error response, validation failure)
2. Implement retry strategy: how many attempts, with what modifications
3. Define fallback: alternative agent, simplified approach, or graceful degradation
4. Isolate failures: failed agent's outputs do not propagate to other agents
5. Honor stop-the-line: any agent detecting critical flaw can halt workflow
6. Log all failures and near-misses for system improvement
7. Escalate unrecoverable failures to human with full context

**Success Criteria**

- Agent failures detected within defined timeout
- Retry attempts logged with modifications
- Fallback strategies defined for all critical agents
- Stop-the-line authority respected regardless of source agent
- Unrecoverable failures escalate with actionable context
- No silent failures or error propagation
- Near-misses logged for system learning

**Human Interaction Points**

- Define acceptable degradation modes for critical workflows
- Handle escalated unrecoverable failures
- Respond immediately to stop-the-line events
- Approve retry/fallback strategies for high-stakes tasks
- Review near-miss logs for systemic issues

**Common Pitfalls**

- **Silent Failure:** Agent errors ignored, corrupted output passed downstream
- **Infinite Retry:** Retry loops without modification or escalation
- **Cascade Acceptance:** Accepting outputs from agents downstream of a failed agent
- **Missing Timeouts:** Agents hanging indefinitely without failure detection
- **Penalized Reporting:** Agents pressured to "always return a result" instead of reporting failure
- **Ignored Stop-the-Line:** Workflow continuing despite critical flaw detection

**Configurable Defaults**

- Agent timeout: Configurable per agent type (default: defined in methods)
- Retry attempts: Defined limit with modification before escalation
- Failure isolation: Required (failed agent outputs quarantined)
- Stop-the-line authority: All agents (not configurable—this is the principle)
- Near-miss logging: Required

---
