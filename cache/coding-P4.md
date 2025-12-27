#### P4. Human-AI Collaboration Model (The Separation of Powers Act)

**Failure Mode(s) Addressed:**
- **D1: AI Makes Product Decisions** — AI makes strategic, business, or user-experience decisions it's unqualified for, causing feature misalignment and requiring rework
- **D2: Automation Bias** — Human over-relies on AI recommendations, accepting suggestions without appropriate critical review

**Constitutional Basis:**
- Derives from **MA1 (Role Segregation):** Clear separation between executor and validator roles
- Derives from **MA5 (Handoff Protocols):** Explicit handoff between different roles
- Derives from **G10 (Human Agency Boundary):** Human makes strategic decisions; AI executes technical implementation

**Why Meta-Principles Alone Are Insufficient:**
Meta-Principle G10 states "humans make strategic decisions, AI executes" but doesn't define **specific decision boundaries** for AI coding or protocols for the inverted paradigm where AI is primary executor rather than assistant. Traditional development assumes human coder with AI assistance. AI-assisted development inverts this: AI codes, human directs. This requires explicit protocols for: which decisions AI owns, which require escalation, how to present options, and how to prevent both over-escalation (slowing velocity) and under-escalation (AI overreach). The principle also addresses automation bias—the tendency to accept AI outputs without critical review.

**Domain Application:**
AI serves as primary executor implementing technical tasks, while Product Owner provides strategic direction, makes key decisions, and validates alignment with product vision. This inverted paradigm requires explicit protocols for decision authority, escalation triggers, option presentation, and human review expectations.

**Decision Authority Matrix:**

| Decision Type | Authority | AI Action |
|--------------|-----------|-----------|
| Technical implementation details | AI | Proceed autonomously |
| Code structure and patterns | AI | Proceed autonomously |
| Error handling approaches | AI | Proceed autonomously |
| Feature scope or priority | Product Owner | Escalate with options |
| User-facing behavior | Product Owner | Escalate with options |
| Architectural tradeoffs | Product Owner | Present options with recommendation |
| Business logic interpretation | Product Owner | Clarify before proceeding |
| Security risk acceptance | Product Owner | Escalate—no autonomous override |

**Truth Sources:**
- Decision authority matrix (which decisions belong to which role)
- Escalation criteria (when to pause for Product Owner input)
- Validation protocols (what requires PO review vs. AI self-validation)
- Specification documents (what's explicitly defined vs. requires decision)

**How AI Applies This Principle:**
- **Autonomous Execution Zone (Proceed Independently):**
  * Specifications are complete and explicit—no gaps requiring interpretation
  * Implementation approach clearly documented in specifications
  * Technical decision has single valid solution (no meaningful alternatives)
  * Work is within current phase boundaries
  * Decision doesn't affect user-facing behavior or business logic
- **Product Owner Consultation Zone (STOP and Request Input):**
  * Multiple valid implementation approaches exist with different tradeoffs
  * Specification has gaps or ambiguities affecting behavior
  * Work would cross phase boundaries
  * Decision has substantial rework implications if wrong choice made
  * Tradeoffs involve business priorities or user experience
  * Security risk acceptance required
- **Option Presentation Protocol (When Consulting PO):**
  1. State the decision needed clearly
  2. Present 2-3 viable options with pros/cons for each
  3. Include AI's recommendation with rationale
  4. Explain implications of each choice
  5. Wait for explicit decision—do not proceed on assumption
- **Validation Checkpoints (Present for Review):**
  * At phase completion gates (mandatory)
  * When implementing user-facing features
  * Before major architectural changes
  * When making assumptions that weren't explicit in specs
- **Automation Bias Mitigation:**
  * When presenting recommendations, include confidence level and limitations
  * Flag areas where human judgment is particularly important
  * Encourage critical review, not rubber-stamping
  * Document reasoning so PO can evaluate, not just accept

**Solo Developer Mode:**

When the developer IS the Product Owner (common in solo development or small teams), the collaboration model adapts:

**Internal Checkpoints Replace External Handoffs:**
- Developer-as-PO still performs vision validation at phase gates
- "Escalation" becomes explicit pause for self-reflection, not waiting for another person
- Document decisions AS IF explaining to someone else (forces rigor)

**Solo Developer Protocol:**
1. **Specification Phase:** Write specs as if for another developer. Gaps you'd ask someone else about = gaps AI will hallucinate around.
2. **Decision Points:** When AI would escalate, PAUSE and explicitly decide. Don't let momentum carry past decisions.
3. **Validation Gates:** Review your own work with fresh eyes. Take breaks between completion and review.
4. **Bias Check:** Solo developers are MORE susceptible to automation bias (no second set of eyes). Build in explicit review steps.

**Solo Developer Red Flags:**
- Accepting AI output without reading it because "it's probably right"
- Skipping validation gates because "I know what I wanted"
- Not documenting decisions because "I'll remember"
- Letting AI make product decisions because it's faster than deciding yourself

**Why This Principle Matters:**
Execution without authority is tyranny; authority without execution is paralysis. *This corresponds to "Separation of Powers"—each branch has defined authority. AI excels at rapid technical execution; humans excel at strategic judgment. Blurring these boundaries creates either runaway AI (making product decisions) or micro-managed AI (negating its capabilities). Clear role boundaries maximize both.*

**When Product Owner Interaction Is Needed:**
- ⚠️ Any business/product decision (features, priorities, tradeoffs)
- ⚠️ Architectural decisions with multiple valid approaches (present options)
- ⚠️ Phase validation gates (mandatory vision validation)
- ⚠️ When AI detects specification gaps affecting behavior
- ⚠️ When AI encounters unexpected obstacles or blockers
- ⚠️ Security risk decisions (PO must explicitly accept risk)
- ⚠️ When AI recommendation confidence is low

**Common Pitfalls or Failure Modes:**
- **The "Runaway AI" Trap:** AI makes product decisions without consultation, implementing what seems logical but doesn't match business intent. *Prevention: Clear escalation triggers; when in doubt, ask.*
- **The "Micro-Management" Trap:** Product Owner makes detailed technical decisions, slowing velocity and not leveraging AI capabilities. *Prevention: Trust AI on technical implementation within clear specifications.*
- **The "Analysis Paralysis" Trap:** AI escalates trivial decisions unnecessarily, creating bottlenecks. *Prevention: Clear authority matrix; technical decisions within specs don't require escalation.*
- **The "Rubber Stamp" Trap:** PO approves AI work without meaningful review (automation bias). *Prevention: Explicit review protocols; AI highlights areas needing human judgment.*
- **The "Silent Assumption" Trap:** AI makes assumptions without flagging them, PO doesn't know to review. *Prevention: AI documents all assumptions explicitly.*

**Success Criteria:**
- ✅ Clear decision authority matrix documented and followed
- ✅ AI autonomously executes technical decisions within specifications
- ✅ AI escalates product/business decisions with options and recommendations
- ✅ Product Owner validation occurs at all defined gates
- ✅ <10% of escalations deemed "should have proceeded autonomously" (not over-escalating)
- ✅ <5% of autonomous decisions required PO correction (not under-escalating)
- ✅ All assumptions documented and reviewable

---

### Q-Series: Quality Principles
