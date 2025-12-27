#### P2. Validation Gates (The Checkpoint Act)

**Failure Mode(s) Addressed:**
- **B1: Skipped Validation → Bugs in Production** — AI-generated code deployed without adequate review/testing
- **B2: Inadequate Testing → Vulnerability Exposure** — Insufficient test coverage leaves vulnerabilities undetected
- **B3: Missing Security Scanning → Exploitable Code** — Security vulnerabilities not detected before deployment
- **C2: Implementation Before Architecture** — Work proceeds despite incomplete prerequisites

**Constitutional Basis:**
- Derives from **Q1 (Verification):** Validate output against requirements before considering work complete
- Derives from **Q3 (Fail-Fast Detection):** Catch errors early before they propagate
- Derives from **Q7 (Failure Recovery):** Define clear recovery paths when errors detected

**Why Meta-Principles Alone Are Insufficient:**
Meta-Principle Q1 states "validate outputs against requirements" but doesn't specify **WHEN** validation must occur in AI coding or **WHAT** happens when validation fails. Traditional development often defers validation to QA phases. AI coding velocity makes this dangerous—thousands of lines can be generated before any validation, amplifying error propagation. This domain principle establishes: (1) mandatory gate points, (2) gate types (technical vs. vision), and (3) failure protocols.

**Domain Application:**
Each development phase must end with explicit validation gates that verify completeness and quality **before progression to the next phase**. Validation gates are pass/fail checkpoints—not "check and continue regardless." Gates include both technical validation (AI self-checking against objective criteria) and vision validation (Product Owner review for alignment with intent). Failed gates trigger recovery protocols, not workarounds.

**Two Types of Validation:**
1. **Technical Validation (AI performs):** Objective criteria AI can verify
   - Tests pass
   - Security scans clear
   - Code follows standards
   - Requirements traceability complete
   - No obvious gaps or errors
   
2. **Vision Validation (Product Owner performs):** Subjective alignment with intent
   - Output matches expected direction
   - Business logic correctly interpreted
   - User experience appropriate
   - Strategic alignment maintained

**Truth Sources:**
- Phase completion criteria (what "done" means for each phase)
- Validation checklists (objective criteria per phase)
- Quality standards and acceptance criteria
- Architecture alignment requirements
- Test results and coverage reports
- Security scan results

**How AI Applies This Principle:**
- **Pre-Gate Self-Validation (Before Requesting PO Review):**
  1. Run through technical validation checklist for current phase
  2. Verify: Does output meet ALL stated completion criteria?
  3. Verify: Are ALL requirements addressed (no gaps)?
  4. Verify: Do automated tests pass (if applicable)?
  5. Verify: Does code follow standards/conventions?
  6. Identify and document any known issues or concerns
  7. ONLY request PO review after technical validation passes
- **Explicit Gate Declaration:** State clearly: *"Phase X validation gate reached. Technical validation: [PASS/FAIL with summary]. Ready for vision validation."*
- **Gate Failure Protocol:**
  1. Identify specific failure reason(s)
  2. Determine if issue is in CURRENT phase or UPSTREAM phase
  3. If upstream: Flag for upstream revision—do not patch around it
  4. If current: Apply failure recovery, fix issues, re-validate
  5. Re-run full validation after fixes—no partial passes
- **No Gate Bypassing:** CANNOT proceed to next phase with failed validation, even for "minor issues." Minor issues compound. Fix before proceeding.
- **Repeated Failure Escalation:** If same gate fails 3+ times, escalate to Product Owner—indicates systemic issue, not fixable iteration.

**Why This Principle Matters:**
Errors compound; gates interrupt. *This corresponds to "Appellate Review"—checkpoints exist to catch errors before they become irreversible. Without gates, AI hallucinations propagate through dependent code, contaminating entire implementations. Gates are not bureaucracy; they are error firewalls.*

**Relationship to Q-Series Principles:**
- **P2 (Validation Gates):** Defines WHEN validation must occur (process gate)
- **Q1-Q3 (Quality Standards):** Define WHAT passing means (quality standard)

P-series mandates *that* verification happens at specific points; Q-series defines *what satisfies* that verification.

**When Product Owner Interaction Is Needed:**
- ⚠️ At EVERY phase boundary for vision validation (mandatory)
- ⚠️ When technical validation fails repeatedly (same issue 3+ times)
- ⚠️ When validation criteria themselves are unclear or conflicting
- ⚠️ When validation reveals upstream issues requiring scope decisions
- ⚠️ When "good enough" pressure conflicts with validation requirements

**Common Pitfalls or Failure Modes:**
- **The "Good Enough" Trap:** Proceeding with minor validation failures planning to "fix later." Later never comes; minor issues compound. *Prevention: Pass means PASS, not "mostly pass."*
- **The "Rubber Stamp" Trap:** Going through validation motions without actually checking. Validation becomes ceremony, not substance. *Prevention: Validation requires evidence, not just declaration.*
- **The "Blame Upstream" Trap:** Failing current phase but blaming incomplete upstream phases as excuse to proceed. *Prevention: If upstream is incomplete, return to upstream—don't proceed with excuses.*
- **The "Velocity Pressure" Trap:** Skipping validation because "we're behind schedule." This creates more schedule pressure from rework. *Prevention: Validation is non-negotiable regardless of schedule.*

**Success Criteria:**
- ✅ Every phase ends with explicit validation gate
- ✅ Technical validation automated where possible (tests, linting, security scans)
- ✅ Failed gates trigger recovery protocols, NEVER workarounds or bypass
- ✅ <5% of validation failures due to hallucination (indicates good C1 compliance)
- ✅ Vision validation documented with Product Owner approval
- ✅ No phase progression without both technical AND vision validation passing

---
