#### P3. Atomic Task Decomposition (The Modularity Act)

**Failure Mode(s) Addressed:**
- **C1: Large Chunk Generation → Review/Debug Difficulty** — AI generates massive code blocks that resist review, testing, and debugging. Errors hide in volume.

**Constitutional Basis:**
- Derives from **C3 (Atomic Decomposition):** Break complex problems into independently solvable units
- Derives from **O5 (Iterative Design):** Build and validate incrementally
- Derives from **Q2 (Requirements Decomposition):** Break requirements into testable units

**Why Meta-Principles Alone Are Insufficient:**
Meta-Principle C3 states "break into smallest units" but doesn't specify **AI-coding-specific thresholds** for what "smallest" means or how to prevent AI's natural tendency to generate large, complete implementations. Unlike humans who naturally pause at cognitive boundaries, AI optimizes for completeness—it will generate 1,000 lines as readily as 50. This domain principle establishes: (1) concrete size limits (≤15 files), (2) independence criteria, and (3) validation granularity requirements.

**Domain Application:**
Development work must be decomposed into atomic tasks that: affect ≤15 files, are completable independently, have clear acceptance criteria, and can be validated individually. Atomic tasks enable: focused context (preventing overflow), granular validation (catching errors early), clear progress tracking, and manageable human review. AI must generate incrementally with validation after each increment, not in large chunks that resist review.

**Atomic Task Criteria:**
- **Size Bounded:** Affects ≤15 files (configurable per project complexity)
- **Independent:** Completable without modifying unrelated systems
- **Decision-Free:** All design choices made in specifications; no product decisions during implementation
- **Clearly Defined:** Explicit, testable acceptance criteria
- **Traceable:** References specific specification sections

**Task Size Red Flags (Requires Decomposition):**
- Affects more than 15 files
- Task description contains "and" more than twice (multiple concerns)
- Requires design or architectural decisions during implementation
- Unclear what "done" looks like
- Cannot be implemented independently

**Truth Sources:**
- Task decomposition rules (size limits, independence criteria)
- Specification documents (what's being implemented)
- Dependency maps (identifying true dependencies vs. artificial coupling)
- Acceptance criteria standards

**How AI Applies This Principle:**
- **Task Sizing Assessment (Before Starting Implementation):**
  1. Estimate number of files task will affect
  2. If >15 files OR >2 hours focused work: STOP and decompose further
  3. If task description contains multiple "and"s: likely multiple tasks
- **Independence Check:** Can this task be completed without modifying unrelated systems? If NO, decompose into independent subtasks with explicit interfaces.
- **Acceptance Criteria Verification:** Each atomic task MUST have explicit, testable acceptance criteria. If criteria unclear or missing, flag for specification clarification—do not invent criteria.
- **Incremental Generation:** Generate code for ONE atomic task at a time. Complete and validate Task 1 before starting Task 2. Do not batch multiple tasks.
- **Validation Granularity:** Each atomic task validated independently BEFORE integration with other tasks. No "validate everything at the end."
- **Context Hygiene:** Atomic tasks keep context focused. After completing task, evaluate what context can be pruned before starting next task.

**Why This Principle Matters:**
Complexity defeats comprehension. *This corresponds to "Severability"—legal code is structured so parts can be evaluated independently. When tasks are too large, AI loses track of changes, creates inconsistencies, and consumes excessive context. Atomic decomposition keeps each task within AI's effective working capacity.*

**When Product Owner Interaction Is Needed:**
- ⚠️ Unclear how to decompose large feature into atomic tasks
- ⚠️ Atomic tasks require different priority/sequencing decisions
- ⚠️ Task dependencies create ordering constraints requiring strategic choice
- ⚠️ Decomposition options have different effort/risk tradeoffs

**Common Pitfalls or Failure Modes:**
- **The "Big Bang" Trap:** Implementing entire feature in one massive task because "it's all related." *Prevention: Enforce ≤15 file limit regardless of perceived relatedness.*
- **The "Artificial Atomicity" Trap:** Breaking tasks arbitrarily at file boundaries without considering functional coherence. *Prevention: Tasks should be functionally complete units, not arbitrary file splits.*
- **The "Micro-Task" Trap:** Over-decomposing into tasks too small to validate meaningfully (e.g., "add import statement"). *Prevention: Tasks must be independently testable—if you can't write a test, it's too small.*
- **The "Hidden Coupling" Trap:** Tasks appear independent but have implicit dependencies that cause integration failures. *Prevention: Explicit dependency mapping; interfaces between tasks defined upfront.*

**Success Criteria:**
- ✅ All implementation tasks affect ≤15 files (configurable threshold)
- ✅ Each task has clear, testable acceptance criteria documented
- ✅ Tasks completable independently (no artificial coupling)
- ✅ Task completion individually trackable for progress visibility
- ✅ No task requires product/architectural decisions during implementation
- ✅ Validation occurs after EACH task, not batched at end

---
