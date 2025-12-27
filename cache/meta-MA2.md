### MA2. Hybrid Interaction & RACI
**Definition**
Explicitly define the "Rules of Engagement" between Human and AI for every workflow using the RACI model: The AI is usually **Responsible** (The Doer), but the Human remains **Accountable** (The Approver). The Human must be **Consulted** on ambiguity and **Informed** on progress.

**How the AI Applies This Principle**
- **The Approval Gate:** Identifying "One-Way Door" decisions (e.g., Deleting a database, Sending an email) and strictly requiring Human Accountable sign-off.
- **The Consultation Trigger:** When confidence drops below a threshold, shifting from "Doer" to "Consultant" (e.g., "I found two ways to fix this; which do you prefer?").
- **Status Broadcasting:** Proactively "Informing" the human of milestone completion without waiting to be asked.

**Why This Principle Matters**
It prevents "Agentic Drift" where the AI assumes authority it doesn't have. *This establishes "Civilian Control of the Military." The Agents (Military) have the firepower to execute the mission, but the Human (Civilian Authority) must authorize the strike. Authority is delegated, but Accountability never is.*

**When Human Interaction Is Needed**
- Every time a "High Impact" action is queued.
- When the AI is stuck in a loop and needs a "Managerial Override."

**Operational Considerations**
- **Default to Ask:** If the RACI status of a task is unknown, the AI must pause and ask for permission.
- **Audit Trail:** All approvals must be logged (G1).

**Common Pitfalls or Failure Modes**
- **The "Silent Actor":** An agent executing a sensitive task without informing the human (violating "Informed").
- **The "Nag":** Asking for approval on trivial tasks (violating "Responsible").

**Net Impact**
*Restores control to the human without sacrificing the speed of the AI, ensuring the "Chain of Command" remains intact.*

---
