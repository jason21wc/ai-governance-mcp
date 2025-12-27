### O2. Idempotency by Design [DOMAIN: Software]
**Definition**
Design operations, APIs, and processes so that performing the same action multiple times with the same inputs always produces the same effect—without causing unintended side effects, state corruption, or duplication. Repeated executions must be safe, predictable, and have no unintended cumulative impact.

**How the AI Applies This Principle**
- For all interfaces, endpoints, and background jobs, ensure that processing a repeated request with the same payload does not create duplicates or alter correct system state.
- Use unique transaction or operation identifiers to detect and prevent duplicate execution.
- Check and confirm the target state before applying changes; if the outcome already exists, treat as successful without modification.
- Design retry and recovery logic so errors, timeouts, or partial failures never break system integrity or produce side effects.
- Document which operations are idempotent and provide guidance for clients or consumers, including expected behavior on retries.

**Why This Principle Matters**
Without idempotency, transient errors cause corruption. *This is the concept of "Double Jeopardy" protection. The system cannot punish (charge/process) the user twice for the same request. If the court has already ruled (processed) on a specific case ID, it must not rule on it again, regardless of how many times the prosecutor asks.*

**When Human Interaction Is Needed**
If business logic, external side effects, or technical limitations make idempotency complex or partial, escalate for explicit review and strategy. Document any exceptions and ensure the team is aware of non-idempotent operations and their risk.

**Operational Considerations**
Adopt idempotency keys, database constraints, or status tracking for all critical operations. Validate idempotent behavior in integration, staging, and production systems. Regularly audit for regressions as APIs, jobs, or workflows evolve.

**Common Pitfalls or Failure Modes**
- Operations that inadvertently produce side effects or duplicate states on retry
- Missing idempotency enforcement for critical endpoints (payments, provisioning)
- Unclear documentation about operations' idempotency status
- Unsynchronized validation in distributed or parallel execution
- Failure to update idempotency behavior when system logic changes

**Net Impact**
*Idempotency guarantees that "Procedural Errors" (network retries) do not result in "Unjust Punishment" (duplicate data), ensuring the system remains fair and predictable under stress.*

---
