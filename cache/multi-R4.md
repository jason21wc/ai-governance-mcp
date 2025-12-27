### R4. Observability Protocol

**Why This Principle Matters**

The constitutional principle MA6 (Synchronization & Observability) requires that long-running agents proactively broadcast their status rather than operating as "black boxes" until completion. Without observability, the orchestrator cannot detect stalls, resource contention, or silent failures until they cascade into system-wide problems. Proactive status visibility enables rapid unblocking and dynamic re-planning.

**Domain Application (Binding Rule)**

Long-running agents must proactively broadcast status (current task, progress, blockers) to the orchestrator at defined intervals. Agents must not operate silently until completion. The orchestrator must have visibility into all active agent states to detect stalls, deadlocks, and resource contention before they become failures.

**Constitutional Basis**

- MA6 (Synchronization & Observability): Agents must implement heartbeat/standup mechanism
- MA4 (Blameless Error Reporting): Proactive reporting of blockers and issues
- Q3 (Fail-Fast): Detect problems early through visibility

**Truth Sources**

- MA6: "Long-running agents must proactively broadcast status at defined intervals"
- Enterprise patterns: Real-time situational awareness for orchestrators
- Azilen: Log every step in the process, create metrics for monitoring

**How AI Applies This Principle**

1. Define status broadcast requirements for each agent type
2. Long-running agents emit periodic status: current task, progress, blockers, estimate
3. Agents proactively signal blockers ("I am waiting on Agent B") rather than silently timing out
4. Orchestrator monitors all active agent states for anomalies
5. Detect stalls, deadlocks, and resource contention through status analysis
6. Status updates are structured and concise (not conversational) to minimize overhead

**Success Criteria**

- No agent operates as "black box" for extended periods
- Orchestrator can query state of all active agents at any time
- Blockers surfaced proactively, not discovered after timeout
- Stalls and deadlocks detected before they cascade
- Status overhead does not exceed value (concise, structured updates)

**Human Interaction Points**

- Define status broadcast frequency for different agent/task types
- Review status dashboards for complex multi-agent workflows
- Intervene when orchestrator detects unresolvable blockers
- Adjust observability levels based on workflow criticality

**Common Pitfalls**

- **Black Box:** Agent goes silent for extended period, orchestrator cannot tell if stuck or working
- **Micromanager:** Status updates so frequent that agents spend more tokens reporting than working
- **Silent Blocker:** Agent waiting on external resource without signaling, causing invisible delays
- **Chatty Status:** Conversational status updates that waste tokens and obscure signal

**Configurable Defaults**

- Status broadcast: Required for tasks exceeding defined duration threshold
- Status format: Structured data (not conversational)
- Blocker escalation: Immediate upon detection

---

## Quality Principles (Q-Series)
