#### P1. Sequential Phase Dependencies (The Causation Chain Act)

**Failure Mode(s) Addressed:**
- **C2: Implementation Before Architecture** — Coding begins before architectural decisions are made, forcing AI to make architectural decisions during implementation (decisions it's not qualified to make), causing technical debt and rework cascades.

**Constitutional Basis:**
- Derives from **C5 (Foundation-First Architecture):** Establish architectural foundations before implementation
- Derives from **C6 (Discovery Before Commitment):** Complete discovery phases before committing to downstream work
- Derives from **Q1 (Verification):** Validate each phase before proceeding to next
- Derives from **O1 (Prioritization):** Work in dependency order, not arbitrary order

**Why Meta-Principles Alone Are Insufficient:**
Meta-Principle C5 states "establish foundations before implementation" but doesn't define **what constitutes a complete foundation** in AI coding or **how phases relate to each other**. Traditional development assumes human judgment bridges phase gaps. AI coding requires explicit phase dependencies because AI will confidently proceed with incomplete upstream context, generating plausible-looking code that violates unstated architectural constraints. This domain principle establishes: (1) phase dependency order, (2) what "complete" means for each phase, and (3) cascade protocols when upstream changes occur.

**Domain Application:**
Software development work must progress through clear sequential phases where each phase produces validated outputs that become **required inputs** for subsequent phases. Upstream phases define architectural foundations and constraints; downstream phases implement **within** those constraints. Phase progression is unidirectional: upstream → downstream. Skipping phases or executing out of order creates specification gaps that force AI to make decisions it shouldn't make.

**Phase Dependency Logic:**
```
Phase N outputs → Required inputs for Phase N+1
Phase N incomplete → Phase N+1 CANNOT begin (blocked)
Phase N changes → All downstream phases (N+1, N+2, ...) require re-validation
```

**Truth Sources:**
- Phase completion criteria and validation gates
- Dependency maps showing prerequisite → dependent relationships
- Architecture decisions made in upstream phases
- Specifications validated in previous phases
- Phase output documents (structured, referenceable)

**How AI Applies This Principle:**
- **Phase Dependency Check (BEFORE Starting Any Phase):**
  1. Identify all prerequisite phases for current work
  2. Verify each prerequisite phase is COMPLETE and VALIDATED
  3. Load outputs from prerequisite phases into context
  4. If ANY prerequisite incomplete: STOP and flag, do not proceed
- **Upstream First:** If implementing a feature requires architectural decisions not yet made, STOP and return to architectural phase. Never make architectural decisions during implementation.
- **No Skipping:** Cannot skip phases even if work "seems simple." Each phase prevents specific downstream failures. Simple-seeming features often reveal complexity during proper upstream phases.
- **Cascade Awareness:** When upstream changes occur:
  1. Identify ALL downstream phases that depend on changed outputs
  2. Flag each for re-validation
  3. Do not proceed with downstream work until re-validation complete
- **Output Documentation:** Each phase produces explicit, structured outputs that next phase CONSUMES. Outputs are not optional documentation—they are required inputs.
- **Bidirectional Discovery:** If downstream work reveals upstream gaps (missing requirements, unclear architecture), PAUSE downstream work and return to upstream phase for completion. Do not patch around gaps.

**Why This Principle Matters:**
You cannot build the roof before the foundation. *This corresponds to "Procedural Due Process"—cases must proceed through proper stages. When AI implements before architecture is defined, it makes architectural decisions it's unqualified to make. Sequential progression keeps AI in its execution role, not the design role.*

**When Product Owner Interaction Is Needed:**
- ⚠️ Prerequisite phases appear incomplete—PO confirmation needed before proceeding
- ⚠️ Upstream changes would cascade to completed downstream work—scope decision required
- ⚠️ Phase boundaries unclear for specific work item
- ⚠️ Downstream discovery reveals upstream gap—decision on how to handle
- ⚠️ "Fast track" request to skip phases—risk acknowledgment required

**Common Pitfalls or Failure Modes:**
- **The "Quick Feature" Trap:** Skipping architecture/design phases for "simple" features that later reveal complexity. *Prevention: No exceptions—all work follows phase order.*
- **The "Parallel Path" Trap:** Working on dependent phases simultaneously, causing integration conflicts when outputs don't align. *Prevention: Sequential, not parallel. Finish Phase N before starting Phase N+1.*
- **The "Waterfall Rigidity" Trap:** Refusing to revisit upstream phases when new information emerges, forcing workarounds instead. *Prevention: Bidirectional discovery is expected—return upstream when gaps found, don't patch around them.*
- **The "Implicit Dependency" Trap:** Assuming AI "knows" architectural constraints without loading them from upstream outputs. *Prevention: Explicitly load upstream outputs; never assume inherited context.*

**Success Criteria:**
- ✅ Phase progression follows documented dependency order
- ✅ Rework rate due to missing upstream decisions: <5%
- ✅ Implementation NEVER makes architectural decisions (all architecture from upstream phases)
- ✅ Each phase completion triggers validation BEFORE next phase begins
- ✅ Upstream changes trigger downstream re-validation (no orphaned downstream work)
- ✅ All downstream work traceable to specific upstream outputs

---
