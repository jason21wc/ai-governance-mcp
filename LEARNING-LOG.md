# AI Governance MCP - Learning Log

**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> **Entry rules:** Each entry ≤5 lines. State what happened, then the actionable rule.
> Record conclusions, not evidence. If it wouldn't change future behavior, it doesn't belong here.
> When lesson graduates: Add to methods doc, mark "Graduated to §X.Y"
> Route other content: decisions → PROJECT-MEMORY, architecture → ARCHITECTURE.md

---

## Active Lessons

### Matched Timeouts on Both Sides of an RPC Produce Environment-Dependent Flakes (2026-04-17)

The IPC reconnect test was flaky on CI but passed locally because two independent 30s timers raced: the server handler's `result_event.wait(timeout=CONNECTION_TIMEOUT)` waiting for a worker that had already exited, and the client's `conn.settimeout(CONNECTION_TIMEOUT)` waiting for a response. On macOS the client's timer fired first (triggers reconnect → success). On Linux CI the handler's timer fired first (sends `{"error": "Worker timeout"}` → client raises RuntimeError). Both valid outcomes from the same code; scheduler-dependent which one "wins."

**Rule:** When an RPC system has a timeout on both ends set to the same value, the winner is environment-dependent — macOS and Linux make different scheduling choices, and CI runners add further noise. Either (a) make the timeouts asymmetric with a clear "who detects the failure" contract, or (b) remove the race at its source (the test fix: close accepted conns on shutdown so handlers exit fast and the race never starts). Symmetric timeouts should be treated as a design smell in any IPC layer.

**Principle:** `meta-core-systemic-thinking` — the test wasn't "flaky due to CI resource constraints" (the BACKLOG framing). It was a deterministic race that the structural fix (release accepted conns on shutdown) eliminates rather than papers over with retries or longer timeouts.

---

### Claude Code Hook Exit 1 = Fail-Open, Not Fail-Closed (2026-04-16)

The OOM gate hook uses `set -euo pipefail`. If any unhandled command fails, bash exits with code 1. Claude Code treats exit 1 as a **non-blocking error that ALLOWS the action through** — only exit 2 blocks. This means `set -e` without an ERR trap makes a security hook fail-open on unexpected errors, the opposite of what a security gate intends. Timeouts also allow through.

**Rule:** All security-relevant Claude Code hooks must include `trap 'exit 2' ERR` immediately after `set -euo pipefail`. This converts unhandled failures to deny (exit 2) instead of non-blocking allow (exit 1). Additionally, never use `exit 1` intentionally in a hook that needs to block — always `exit 2`. Source: Anthropic hooks reference (code.claude.com/docs/en/hooks).

**Principle:** `meta-core-systemic-thinking` — the root cause is a mismatch between Unix convention (exit 1 = error = stop) and Claude Code convention (exit 1 = non-blocking = continue). Advisory knowledge of the convention isn't enough; the ERR trap makes it structural.

---

### MRR Baseline Numbers Recalled from Memory Were Wrong (2026-04-16)

Session-107 planning used "0.694 methods, 0.688 principles" as Phase 2 verification targets — numbers from SESSION-STATE that originated in the 03-12 to 03-22 era. The contrarian reviewer caught it: actual stable baseline (04-01 through 04-13, 13 consecutive days) is **method_mrr=0.711, principle_mrr=0.750**. The 04-14 baseline shows method_mrr=0.646 (a 0.065 drop, predating Phase 2). Measuring against stale numbers would have produced a false pass/fail.

**Rule:** Before using numeric baselines in verification criteria, read the actual baseline file (`tests/benchmarks/baseline_*.json`). Do not recall numbers from memory or SESSION-STATE — they go stale when content or test cases change. Per `meta-safety-transparent-limitations`: presenting recalled baselines as current values is factually wrong.

---

### RSS Lies on macOS — Use phys_footprint (2026-04-16)

Diagnosed a memory problem using `ps aux` RSS numbers (800 MB - 1 GB per process) and reported "5% of RAM, not a crisis." Activity Monitor showed 9 GB / 6 GB / 3-4 GB per process. The discrepancy is 5x. macOS `ps` RSS only counts pages currently resident in physical RAM. `vmmap -summary` reports `phys_footprint` which includes resident + compressed + swapped — the correct metric that Activity Monitor displays. For a long-running process with idle regions, RSS drastically understates the real committed memory.

**Rule:** On macOS, always use `vmmap -summary $PID | grep "Physical footprint"` for memory analysis, never `ps aux` RSS. When reporting memory to a user who sees Activity Monitor numbers, use the same metric they see.

**Principle:** `meta-safety-transparent-limitations` — presenting RSS as the footprint was factually wrong, not just imprecise. The 5x understatement led to a "not a crisis" conclusion that contradicted the user's direct observation.

---

### Forcing Functions Are Floors, Not Ceilings (2026-04-16)

Phase 0's `PHASE2_TRIGGERED` forcing function was designed to prevent Phase 2 from being forgotten after Phase 0 removed the acute pain. The contrarian-reviewer interpreted it as a gate that should BLOCK Phase 2 until the measurement fired. The user correctly overrode: the forcing function's purpose was anti-procrastination (a floor — "don't forget"), not anti-eagerness (a ceiling — "don't start"). When the user has more information than the forcing function (Activity Monitor, 32 GB viability concern), the user's judgment supersedes the gate.

**Rule:** When designing forcing functions, document whether they're floors or ceilings. A floor says "at minimum, do this by date X." A ceiling says "do not start until condition Y." The BACKLOG #49 forcing function was a floor masquerading as neutral, which the contrarian read as a ceiling.

**Principle:** `meta-core-systemic-thinking` — the forcing function was designed to address a specific failure mode (forgetting). Applying it to a different failure mode (premature action) is a category error.

---

### Session-End Deferral Bias (2026-04-15)

At the end of session-105, I brainstormed 10 potential hook-hardening follow-ups and bulk-logged all 10 to `BACKLOG #91` without classifying each against the CLAUDE.md Defer-vs-Fix rule (`CLAUDE.md:52-63`, implementing `rules-of-procedure §7.11`). User audit revealed 7 of the 10 were clearly **fix-now** category (≤1 file, unambiguous scope, no cascading discovery — stale-cross-ref / missing-entry / docstring-fix class), 1 was ambiguous-scope ("ask the user"), only 2 were legitimately defer. I defaulted to bulk-defer as the path of least resistance: symmetric to forward-continuation bias but inverted — at session *start* the bias is "keep going past the stopping point"; at session *end* the bias is "log everything to backlog and wrap up instead of finishing the small fixes." Per §7.11.3 this violated Durable Deferral Requirements — "I should fix that later" IS "silent loss with extra steps" when the fix met fix-now criteria.

**Rule:** When multiple small findings emerge from a review, brainstorm, or end-of-session audit, apply the Defer-vs-Fix criteria to EACH finding individually before logging. "Session is wrapping up" is not a valid reason to defer a ≤3-file fix. Session end is structurally the point where the fix-now tier is most often violated, because cognitive pressure is toward closure rather than completeness. The same proportional-rigor test applies: small fix + clear scope = fix now, even if it's the last thing before commit.

**Principle:** `meta-core-systemic-thinking` — the structural cause is cognitive pressure toward closure at session end. A completion-sequence checkpoint asking "which of these newly-found items meet fix-now criteria per CLAUDE.md §52-63?" would catch this structurally; advisory vigilance (this entry) is the interim mechanism. Also `meta-quality-verification-validation` — pre-close review must check whether small-fix items are being silently reclassified as "backlog."

---

### Test Side Effects, Not Just Return Values (2026-04-15)

During session-105's double-check pass, I wrote a `TestDenyLogSideEffect` test that verified the pre-test OOM gate's deny-log file was actually written to (not just that the hook returned the correct deny JSON). That test immediately caught a real bug: `printf '%q'` on bash 3.2 (macOS) was byte-escaping the unicode bullet character (`•`, 0xe2 0x80 0xa2) in the `SIGNALS` variable, producing a log file that was not valid UTF-8. The hook's return value was correct — the test of the return value passed — but the side effect was silently broken. The code-reviewer had flagged `%q` as a MEDIUM bashism earlier and I marked it "Accept — advisory log format." Only the side-effect test caught the corruption.

**Rule:** When code has a side effect (writes a file, updates a log, mutates shared state, emits a metric), test the side effect directly — not just the return value. The return value can be correct while the side effect is silently broken. Especially important for observability paths (logs, metrics, audit trails) where the side effect IS the point of the code and callers rarely check it. Graduated-pattern candidate: "side-effect tests for observability code paths."

**Principle:** `meta-quality-verification-validation` — verification must cover every observable output, not just the one the caller is looking at. The side effect is an output even if no caller reads it synchronously.

---

### Full-Suite pytest + Stale Watcher Daemon = macOS OOM (2026-04-15)

An AI-initiated `pytest tests/ -v` run crashed a 64 GB macOS machine into a low-memory warning. Two contributing causes: (1) a stale Context Engine watcher daemon from a prior session holding a full torch + transformers + BGE model copy (~1.7 GB RSS); (2) no structural gate preventing the test Bash invocation from launching a second Python process that also imports torch. Subsequent investigation also revealed that `sentence-transformers`' `backend="onnx"` parameter does NOT avoid importing torch (`transformers` is a hard transitive dependency) — so the previous session's proposed ONNX-backend mitigation would have addressed ~2% of the 27 GB symptom (envelope math: BGE-small ≈130 MB + reranker ≈90 MB × 50% savings × 5 processes ≈ 550 MB). Two contrarian-reviewer passes rejected that mitigation under `meta-safety-transparent-limitations` — shipping a ~2% fix under a memory-ticket banner would have been forward-continuation bias dressed as pragmatism. Advisory "use `-m 'not slow'`" docs are the ~85% compliance failure mode this log already documents.

**Rule:** Pre-test OOM prevention is now STRUCTURAL via `.claude/hooks/pre-test-oom-gate.sh` — a Claude Code PreToolUse Bash hook that blocks bare `pytest tests/` invocations when the watcher daemon is alive OR other torch-holding Python processes are detected. Two distinct bypass env vars (`PYTEST_ALLOW_HEAVY=1` semantic, `PYTEST_SKIP_OOM_GATE=1` structural) cover intentional heavy runs and gate-is-broken emergencies respectively. Expected-workflow escape hatch: `pytest tests/ -v -m "not slow"` (matches CI, excludes real-model tests). **23 unit tests** at `tests/test_pre_test_oom_gate_hook.py` (10 classes, one parametrized). Cross-references: BACKLOG #49 "Status (2026-04-15)" for the envelope math + design-spike forcing function; `staging/onnx-backend-attempt-2026-04-15.md` for the investigation artifact.

**Principle:** `meta-core-systemic-thinking` — the root cause is architectural (torch duplication across N processes is #49's real symptom), but the OOM-during-testing recurrence is a separate structural gap that deserves its own structural fix. Follows precedent "Hard-Mode Hooks Prove Deterministic Enforcement Works" (2026-02-28). Second cause (advisory-compliance degradation on multi-step checklists) is already graduated, this lesson doesn't re-open it — it just confirms advisory docs would have failed again.

---

### Advisory Pruning Failed: Two Contributing Causes (2026-04-14)

SESSION-STATE.md grew to 1,441 lines (4.8x the 300-line target) despite 3 pruning instructions in the CFR. Two contributing causes: (1) **Wrong surface** — pruning instructions lived only in the CFR, not on always-loaded surfaces (CLAUDE.md, AGENTS.md). (2) **Incomplete instruction** — Completion Checklist item 16 WAS visible every session but said "Update" not "Prune." The AI complied with what it saw: it updated without pruning. Pruning requires destructive judgment (what to keep, what to route, what to delete) — a harder behavior for advisory compliance than additive actions.

**Rule:** Lifecycle instructions requiring destructive judgment (prune, compact, archive) need both correct surface placement AND explicit action verbs. "Update" does not imply "prune." The fix addresses cause #1 (surface placement). V-005 in COMPLIANCE-REVIEW tracks whether cause #2 (advisory compliance for destructive actions) also needs structural enforcement.

**Principle:** `meta-core-systemic-thinking` — two contributing causes, not one. The fix addresses the first; V-005 monitors whether the second requires escalation to hooks.

---

### File Renames Are Concept Replacement, Not String Replacement (2026-04-12)

During Phase 4 (14-file rename), initial grep for old filenames with `.md` extension found all literal filename references. But the context engine + extensionless grep found **17 additional operational references** that grep missed — cross-references using old document names without the file extension, paired with section numbers (e.g., `ai-coding-methods §5.3.6`, `storytelling-methods §15`, `multi-agent-methods, Title 4`). These are conceptual references to documents, not literal filenames. The pre-push hook regex was also missed because it contains a *pattern that matches* old filenames, not the filenames themselves.

**Rule:** When renaming files, use the context engine as the PRIMARY discovery tool (semantic search finds conceptual references), grep as SECONDARY verification (literal patterns). Search for old names both with AND without file extensions. Also search for regex patterns that match old names (hooks, CI scripts). The root cause of missed references is treating renames as string replacement when they're concept replacement.

**Principle:** `meta-core-systemic-thinking` — the root cause was the wrong mental model (filename strings vs. document concepts). The context engine operates at the concept level; grep operates at the string level. Both are needed, in that order.

---

### Dogfooding Catches What Reviews Miss (2026-04-12)

Applied the Admission Test to its own Q0 (Purpose Alignment). Q0 failed Q4 (Evidence — no concrete failure case). Three rounds of subagent review discussed Q0's value without applying the framework's own admission criteria to it. Only when explicitly prompted to "eat our own dogfood" did the failure become visible. Research then revealed the root cause: preambles are interpretive tiebreakers, not standalone filters — a well-established pattern across US constitutional law, EU treaty interpretation, and corporate governance.

**Rule:** When evaluating framework content, apply the framework's own quality gates to the content itself. If a new principle/method/gate can't pass the Admission Test, it shouldn't exist regardless of how well-reasoned the design rationale sounds. "Dogfooding" is not just using the tools — it's applying the standards.

**Principle:** `meta-quality-verification-validation` (define success criteria before execution — the Admission Test IS the success criteria for content admission).

---

### Metaphor-Driven Classification vs Operational Classification (2026-04-12)

Classified Unenumerated Rights and Reserved Powers as S-Series (Bill of Rights) because the US 9th and 10th Amendments are in the Bill of Rights. Contrarian review identified the error: the ai-governance S-Series has different selection criteria than the US Bill of Rights. S-Series = "immutable safety guardrails that prevent user harm." These two principles prevent framework misinterpretation — governance-structural, not safety-critical. Following the metaphor instead of the operational criteria is the same "pattern not analogy" mistake the plan itself warns about.

**Rule:** When the Constitutional pattern suggests a classification, verify against the operational criteria for that classification in THIS framework. The US Constitution is provenance and pedagogical anchor — it informs structure but doesn't determine classification. Ask "does this meet our criteria for X?" not "is this X in the US Constitution?"

**Principle:** `meta-core-systemic-thinking` — the root cause was following the metaphor (symptom-level reasoning) instead of the operational criteria (structural-level reasoning).

---

### Multi-Mechanism Context Degradation Model (2026-03-28, updated 2026-04-07) — CRITICAL

**Corrected framing (supersedes single-mechanism model):** When LLMs skip advisory verification steps, it is NOT a single-mechanism problem. Five distinct degradation mechanisms contribute, each requiring different interventions:

| Mechanism | Description | Addressed by | Research |
|-----------|-------------|-------------|----------|
| **Autoregressive forward-continuation bias** | Each completed step raises probability of continuing to completion rather than pausing to verify. Structural to token generation. | Surface 1 (check-questions interrupt forward trajectory) + few-shot examples | Agent Drift arxiv 2601.04170 |
| **Context position decay (lost-in-middle)** | U-shaped attention: high at start/end, low in middle. Instructions drift into neglect zone as context grows. | Surface 1 positioning (top of CLAUDE.md) + Surface 2 re-injection (recency at governance call) + reminder anchor (end of CLAUDE.md) | arxiv 2307.03172; arxiv 2508.05128 |
| **Context window pollution** | Older, irrelevant interactions dilute signal-to-noise ratio. Quality degrades well before technical limit. | Principles (60/80/32K thresholds in title-10-ai-coding:472-537) + multi-agent compression (§3.4) | Chroma context-rot research |
| **Intent alignment gap** | Progressive mismatch between how users express intent and how models interpret it over turns. Degradation is ~constant regardless of model size. | Multi-agent immutability rules (title-20-multi-agent-cfr:980-984). Gap: not named as degradation mode; no single-session coverage. | arxiv 2602.07338 (challenges Laban et al.) |
| **Distributional shift** | Agent encounters inputs increasingly divergent from training distribution over extended sessions. | Behavioral drift monitoring (coherence auditor). Gap: data distribution shift not tracked. | Agent Drift arxiv 2601.04170 |

**Why this matters:** The previous framing presented autoregressive bias as THE root cause. That's a useful simplification but creates a false ceiling — some degradation types (position decay, intent misalignment) require different interventions than structural gates. Each UBDA surface should know which mechanism it counters. (Validated by 3 independent external reviews, 2026-04-07.)

**Rule (retained):** Stop treating verification/review steps as advisory interruptions. Make them part of the expected generation flow. Three structural techniques: (1) Gate-token transitions, (2) Verification as control flow, (3) Schema enforcement. Advisory prompting ("please verify") has the lowest reliability.

**Rule (retained):** Advisory compliance is ~85%. For items that must be 100%, enforce structurally. COMPLETION-CHECKLIST tiered as ENFORCED vs BEST-EFFORT.

---

### Contrarian Review Is Skipped Under Task Focus Despite Advisory Mechanisms (2026-04-08)

AI attempted ExitPlanMode without contrarian review twice in one session, despite feedback memory (`feedback_plan_subagents.md`) explicitly stating "contrarian review is a GATE before ExitPlanMode." Both times required user correction. The plan template already had a Contrarian Review section — AI populated other sections and skipped it (forward-continuation bias). Advisory memory works for *remembering* the rule but not for *interrupting* the generation flow under cognitive load.

**Rule:** Plan template gate text strengthened to say "DO NOT populate Recommended Approach until this section has content from actual subagent invocation." This makes contrarian part of the generation flow (structural) rather than a memory to recall (advisory). If this fails in 2+ of next 3 sessions → escalate to PreToolUse hook for ExitPlanMode.

**Principle:** `meta-core-systemic-thinking` — advisory mechanisms degrade under cognitive load; structural positioning in the generation flow is the intervention.

---

### Analysis Tasks Are Not Read-Only (2026-04-08)

AI performed a documentation propagation analysis (checking which files needed updating) without calling `evaluate_governance()` or `query_project()`. Categorized it as a "read" task because it involved reading files. But the analysis determined what to write — making it a pre-write task, not a read task. The existing PreToolUse hook caught the governance gap at write time, but the analysis itself was done without governance context or the coherence-auditor subagent. The subagent subsequently found 5 required updates that the manual grep missed.

**Rule:** Analysis tasks that determine what to change are NOT read-only. Call governance before analysis, not just before the write. Skip list exempts "reading files" — not "analyzing what needs changing." Clarified in CLAUDE.md skip list (always-loaded surface).

**Principle:** `meta-core-systemic-thinking` — the skip list exemption was being interpreted at the symptom level (I'm reading files) rather than the structural level (this analysis leads to writes).

---

### Meta-Action Failure ≠ Item-Level Compliance (2026-04-07)

Session shipped code after code-review but before consulting COMPLETION-CHECKLIST.md. Three user-requested "double checks" caught security vulnerabilities, documentation drift, index staleness, test gaps — all covered by the existing checklist. The checklist was never opened. This is a **meta-action failure** (0% — never opened), not an item-level miss (85% — opened but skipped some items). Advisory memory works for single actions (#47: contrarian review 3/3 unprompted). Multi-step checklists need structural nudging because the cognitive load of "identify applicable section → work through sub-items" is categorically higher than "call one subagent."

**Rule:** The meta-action of opening the completion checklist is now ENFORCED (pre-push hook Check 4). Individual items within remain BEST-EFFORT (~85%). This separation — enforce the gate, not every step behind it — is proportional.

---

### Principle Count ≠ Governance Quality (2026-03-29)

Consolidating the constitution from 47 to 22 principles left retrieval quality flat (MRR 0.688, Recall 0.875 — identical before and after). Reducing principle count eliminated redundancy and improved clarity, but didn't measurably improve retrieval. The real quality drivers are: (1) principle text quality (how well-written), (2) retrieval algorithm (embedding model, reranking), and (3) proportional application (knowing when to apply which principle).

**Rule:** Principle consolidation is structural hygiene, not performance optimization. It makes the framework honest ("small set" claim now true) and maintainable, but don't expect retrieval metrics to move from content reorganization alone. Next gains require algorithm tuning or proportionality operationalization.

---

### Three-Agent Assessment Battery Is Non-Negotiable (2026-03-29)

Across 6 domain reviews, the 3-agent assessment battery (contrarian + validator + coherence) consistently outperformed any single agent. The contrarian catches conceptual overlap and wrong dispositions. The validator catches structural defects (stale citations, FM code collisions, template non-compliance). The coherence auditor catches cross-file contradictions and broken derivation chains. Running only the contrarian during KM&PD assessment would have rated 13/13 KEEP; adding all 3 caught 3 issues → 13→10.

**Rule:** Never skip the 3-agent assessment. Each agent catches a different class of issue. Running only one creates blind spots that the others fill. The 2.4x finding multiplier (3 agents vs 1) is consistent across domains.

---

### Shared Failure Mode Codes Are the Primary Consolidation Signal (2026-03-29)

In every domain where merges were warranted, the signal was shared failure mode codes — two principles claiming the same FM code as their primary concern. This was more reliable than subjective overlap assessment. KM&PD: TL3/QA1 shared KM-F2. AI Coding: Idempotency/Production-Ready shared C3. Storytelling: A2/ST2 shared ST-F1. Multi-Agent: CFS/RST shared MA-A1.

**Rule:** When evaluating domain principles, check FM code uniqueness first. Two principles sharing a primary FM code is the strongest merge signal. Shared secondary codes (like Validation Gates sharing B2/B3 with other principles) are legitimate cross-references, not merge signals.

---

### Skip Gate Prevents Over-Consolidation (2026-03-29)

UI/UX passed the skip gate at 100% KEEP — every principle had a distinct failure mode and added genuine domain value. The contrarian confirmed "the structural survey's claim of 'clean structure, each principle has distinct failure mode' is substantively correct." Without the skip gate, we would have wasted effort looking for problems that didn't exist.

**Rule:** Apply the skip gate honestly. >90% KEEP with no MERGE candidates = stop. Not every domain needs consolidation. Consolidation for consolidation's sake violates Resource Efficiency.

---

### False Positives That Train You to Ignore Alerts Are Worse Than No Alerts (2026-03-29)

The S-Series keyword scanner produced ~87% false positive rate during this session. Every "remove", "delete", "database", "security" in a content reorganization action triggered ESCALATE. The response: we silently dismissed every ESCALATE as a false positive without pausing for human review. This is the "boy who cried wolf" failure mode — the safety mechanism trained us to ignore it, which is worse than not having the mechanism at all.

**Rule:** When a safety mechanism's false positive rate exceeds ~50%, the mechanism is net-negative. Fix the detection, don't just ignore the alerts. The fix: separate critical keywords (always escalate) from advisory keywords (warn only when semantic retrieval doesn't confirm). Test empirically before weakening ANY safety path — our initial "pure dual-signal" approach would have created 3 false negatives on genuinely dangerous actions.

---

### Empirically Validate Safety Assumptions Before Implementing (2026-03-29)

The initial plan to reduce S-Series false positives assumed "the semantic retrieval path will catch everything the keywords catch." Empirical testing proved this wrong: 3 of 8 genuinely dangerous queries were NOT caught by semantic retrieval ("exfiltrate API tokens", "deploy to production without review", "drop production database"). Without testing, we would have shipped a safety regression.

**Rule:** Before weakening any safety mechanism, test the alternative path empirically with real dangerous queries. "The other path will catch it" is an assumption, not a fact, until you measure it.

---

### Demotion Decisions Require Constitutional Coverage Verification (2026-03-29)

"Rich but Not Verbose Communication" was demoted to methods as a "style guide" — but the underlying concept (calibrate communication to audience expertise and context) was not covered by any remaining constitutional principle. Resource Efficiency covers waste; Interaction Mode Adaptation covers task modes. Neither covers audience-appropriate communication. The demotion created a gap that required promoting it back as "Effective & Efficient Communication."

**Rule:** Before demoting a principle, verify that every distinct concept it covers is either (a) absorbed into a remaining principle or (b) genuinely methods-level. The constitutional test ("governs all domains?") is necessary but not sufficient — also check "is this concept covered elsewhere?"

---

### Hard-Mode Hooks Prove Deterministic Enforcement Works (2026-02-28)

During the implementation session itself, the recency window (200 lines) expired 3 times, blocking my own edits until I re-called `evaluate_governance()` and `query_project()`. This was not a bug — it proved the system works exactly as designed: even the implementing agent cannot bypass enforcement. Advisory instructions failed at 87%; structural blocking achieves near-100% by making non-compliance physically impossible rather than merely discouraged.

**Rule:** When enforcement is the goal, architecture beats instruction. A hook that returns `permissionDecision: "deny"` is infinitely more reliable than a reminder that says "please call this tool first." Design enforcement mechanisms that you yourself cannot bypass during normal work.

---

### Code Review Advisory Framing Prevents Both Rubber-Stamping and Dismissal (2026-02-28)

Applied the new advisory framing to evaluate the code-reviewer's findings on our own changes. Of 6 findings: accepted 2 (H1 ValueError fix, H2 mixed mode tests — genuine gaps), rejected 2 (M2 CLAUDE.md pointers — intentional removal, M4 debug inconsistency — acceptable). Ratio: 33% accept, 33% reject, 33% not applicable. The structured evaluation table forced explicit reasoning for each decision rather than blanket acceptance.

**Rule:** When receiving subagent findings, use the structured evaluation table (Finding | Agree/Modify/Reject | Reasoning). The exercise of writing a reason for each decision is more valuable than the table itself — it prevents both "implement everything" and "dismiss everything" failure modes.

---

### Multi-Path Methods Must Handle All Paths Uniformly (2026-02-28)

`get_or_create_index()` had 3 code paths but only path #3 (create new) started the watcher. Path #2 (load from storage) — the boot-time path — silently skipped it. Bug persisted across multiple sessions because manual `reindex_project()` (which has its own watcher start) always masked it. Similarly, `query_project()`'s lazy-reload path after LRU eviction had no watcher start.

**Rule:** When a method has N code paths that should all produce equivalent side effects, audit ALL paths — not just the obvious ones. Extract the shared side effect into a named helper (`_ensure_watcher`) and call it from every path. The boot-time path and the eviction-reload path are the easiest to miss because they're only exercised after restart or under memory pressure.

---

### External Framework Comparison: Start from Gaps, Not Borrowing (2026-02-28)

Evaluated Atlas framework against our ai-coding domain. Initial framing was "what can we borrow?" which anchored toward inclusion. Contrarian reviewer identified **intellectual generosity bias** — the desire to find value in external work to avoid appearing dismissive. Reframing to "does this reveal a genuine gap?" produced the correct conclusion: no gaps, no changes needed. All 5 candidate incorporations failed our framework's own quality bar (evidence-based, failure-mode-grounded, configurable thresholds).

**Rule:** When evaluating external frameworks, start from "does this reveal a gap in ours?" not "what can we incorporate?" Apply our own principle derivation test: what failure mode does it address? What evidence supports it? What constitutional basis? If it doesn't meet that bar, it doesn't belong — regardless of community popularity.

**Scope boundary (2026-04-05):** This rule applies to **principle-level admission** decisions (should we add a new principle?). It does not apply to method-level implementation quality. When principle-level coverage is confirmed, separately ask: "Did the external implementation suggest a method-level improvement — a more concrete threshold, a more actionable workflow, a better packaging of the same idea?" Method improvements don't require the Admission Test — they're content improvements to existing items, not new admissions. Without this distinction, "7/10 covered" becomes a false-confidence summary that filters out implementation-quality improvements. (Origin: Claude Code workflow video re-analysis, 2026-04-05.)

---

### MCP Server Path.cwd() Is Unsafe as Unconditional Fallback (2026-04-10) — SECOND OCCURRENCE

MCP servers run as separate host processes. `Path.cwd()` resolves to the SERVER's working directory, not the calling client's project. This caused bugs twice in 5 days: (1) governance server's `install_agent`/`scaffold_project` used `Path.cwd()` to find the caller's project → fixed with `_resolve_caller_project_path()` in #50. (2) Context Engine's `_resolve_project_path()` fell through to `Path.cwd()` unconditionally → when called from Claude.ai (where CWD is arbitrary), tried to auto-index a random directory → `[Errno 13] Permission denied`. The governance server's fix docstring explicitly warns "Any MCP tool that writes files to the CALLER'S project must use this resolver instead of Path.cwd()." The Context Engine, sitting in the same repo, was never updated.

**Rule:** Never use `Path.cwd()` as an unconditional fallback in MCP tool handlers. Always validate CWD is a valid project (check for `.git`, `pyproject.toml`, etc.) before using it. When CWD is invalid, return an actionable error telling the AI to call `list_projects` and pass `project_path` explicitly.

**Structural prevention needed:** The real fix is a shared resolver that both servers import — you can't have divergent implementations if there's only one. The LEARNING-LOG entry for `__file__` (below) didn't prevent this CWD bug. Documentation alone doesn't prevent code duplication bugs. Shared module + CI grep check for `Path.cwd()` in server files is the structural path. Tracked for future consolidation.

**Principle:** `meta-core-systemic-thinking` — the root cause is code duplication (two servers independently implementing path resolution), not missing documentation.

---

### __file__-Based Paths Break in Docker Non-Editable Installs (2026-02-19)

`_validate_log_path()` used `Path(__file__).parent.parent.parent` to find project root. Inside Docker with `pip install .` (non-editable), `__file__` resolves to site-packages (`/usr/local/lib/...`), not `/app`. Log writes to `/app/logs/` were rejected as "outside boundaries." Meanwhile, `config.py` already had a CWD-based `_find_project_root()` that worked correctly.

**Rule:** Never use `__file__`-based path traversal to find the project root in code that runs inside Docker containers with non-editable installs. Use CWD-based detection or env vars instead. When multiple modules need the project root, reuse the canonical function rather than reimplementing.

---

### Advisory Governance Instructions Are Probabilistic, Not Deterministic (2026-02-16) — CRITICAL — PARTIALLY GRADUATED

Research confirmed with hard data: AI models follow system prompt instructions 85-92% of the time on SHORT, SINGLE-TURN prompts (IFEval). In multi-turn conversations, performance degrades ~39% on average (Microsoft Research, 200K+ conversations). Anthropic's own data shows Opus 4 tool selection accuracy is **49% baseline** with large tool libraries (improving to 88% with mitigations). Models skip governance calls when they don't perceive a concern, prefer internal knowledge over tools, and silently abstain rather than calling incorrectly.

**Rule:** Never rely solely on MCP server instructions or CLAUDE.md for governance compliance. Structural enforcement (Claude Code hooks, MCP proxies) must complement advisory instructions. The model WILL skip governance calls — the question is how often, not whether. See ADR-13. Key references: anthropic.com/engineering/advanced-tool-use, arxiv.org/abs/2505.06120, research.trychroma.com/context-rot.

**Graduated (2026-02-28):** Hard-mode hooks implemented — PreToolUse blocks non-compliant tool calls. Still active because MCP proxy (cross-platform) enforcement is not yet built (Backlog #1 Part B).

---

### Passive MCP Instructions Don't Drive Tool Usage (2026-02-14)

The CE had well-built tools but passive instructions ("Use these tools to discover what exists"). The governance server achieves automatic usage via deny-by-default skip lists, per-response reminders, and redundant instruction surfaces. Applying the same pattern to the CE — enforcement-oriented trigger phrases ("Before creating...", "Before modifying..."), a nudge in the governance reminder, and a Required Actions cross-reference — bridges the gap without creating a parallel skip-list hierarchy.

**Rule:** When an MCP tool isn't being used naturally, check whether instructions are passive/advisory vs enforcement-oriented. Add trigger phrases that tell the AI WHEN to query, cross-reference from high-frequency surfaces (e.g., governance reminder), and unify enforcement in CLAUDE.md rather than creating parallel hierarchies.

---

### Tree-sitter Positional Children Are Fragile — Use Field Names (2026-02-13) — ACTIVE

`_get_imported_names` used `node.children[1]` to skip the module path in `from X import Y`. This broke for relative imports (`from .bar import baz`) where the module node sits at a different index due to the `.` prefix. Fixed by using `node.child_by_field_name("module_name")` for identity comparison.

**Rule:** When navigating tree-sitter AST nodes, prefer `child_by_field_name()` over positional `children[N]` indexing. Positional assumptions break across syntax variants of the same node type.

---

### Environment-Aware Tests for Optional Dependencies (2026-02-12) — ACTIVE

Tests for `_get_chunking_version()` failed because tree-sitter IS installed in dev but not CI. Hardcoded `"line-based-v1"` broke when the actual connector detected tree-sitter.

**Rule:** Tests that depend on optional package availability should either: (1) explicitly force the flag (`c._tree_sitter_available = False`), or (2) dynamically detect the actual value. Never hardcode expected values for environment-dependent behavior.

---

### Test Inputs Must Traverse the Full Validation Chain (2026-02-11) — ACTIVE

Two test bugs: (1) `"nonexistent00"` has non-hex chars — hit project_id hex validation before reaching the "not found" path we intended to test. (2) `cooldown_seconds=0.0` caused infinite retry cascade — each failed callback re-queued and the 0s timer fired immediately, chaining endlessly and spamming logs.

**Rule:** When writing tests for code with layered validation, trace the full call path to ensure your test input reaches the code path you intend to test. For timer-based retry tests, use a high cooldown (e.g., 60s) so the retry timer never fires during the test, and call `_running.clear()` in cleanup.

---

### Guard-Then-Load Pattern: Don't Undo Your Own Safety Checks (2026-02-10) — ACTIVE

`_load_project` correctly discarded incompatible embeddings on model mismatch. Then immediately called `_load_search_indexes` which reloaded them unconditionally — undoing the safety check. Similarly, `get_principle_by_id` used a prefix→domain map where "multi" (multi-agent) and "mult" (multimodal-rag) collided because Python dict lookup stops at the first prefix match.

**Rule:** When a function sets a safety state (discarding data, marking flags), audit all subsequent calls to verify they don't silently reverse that state. When mapping IDs to domains, prefer exhaustive search over prefix heuristics — domain count is small, correctness matters more than lookup speed.

---

### Bold Text Drives Method Retrieval Surfacing (2026-02-07) — ACTIVE

New method sections get generic chunk titles from the extractor (e.g., "Purpose", "Trigger Conditions"). The extractor picks up **bold text** as `trigger_phrases` (max 4 words, >5 chars). Without bold key terms, method chunks won't surface for natural-language queries.

Three additional extraction traps discovered during Part 4.3 tuning:
1. **Skip-list titles** — `"purpose"` is in `skip_method_titles` (extractor.py:1008). Sections titled "Purpose" get absorbed into the preceding chunk. Fix: use a descriptive title instead.
2. **Short bold terms** — Bold text ≤5 chars (e.g., `**Quick**`, `**Full**`, `**Note:**`) fails the `len(b) > 5` filter. Fix: bold multi-word phrases instead (e.g., `**Quick tier**`).
3. **`Applies To:` field** — The extractor parses `**Applies To:**` lines (extractor.py:1123-1136) into both BM25 and embedding text. Adding this field helps methods surface for `evaluate_governance()` queries.

**Rule:** When adding new method sections: (a) avoid skip-list titles ("purpose", "overview", etc.), (b) bold 2-3 distinctive phrases >5 chars, (c) add `**Applies To:**` with natural-language use cases. Verify after index rebuild (auto-reload picks up changes on next query).

---

### CI Must Install All Test-Relevant Extras (2026-02-07) — GRADUATED to Gotcha #23

CI installed `.[dev]` but context engine tests need `pathspec` (in `.[context-engine]` extras). All 200 CE tests failed with `ModuleNotFoundError`.

**Rule:** When adding optional dependency groups, update CI to install them if tests cover that code. See Gotcha #23.

---

### Version History Entries Can Be Silently Dropped (2026-02-08) — ACTIVE

Coherence audit found v3.7.0 missing from version history table and v3.7.0.1 orphaned at end of file. During edits, version history entries can be accidentally deleted or displaced without anyone noticing — the table is long and entries look similar.

**Rule:** Add a version-history-completeness check to pre-release audits: verify descending order, no gaps, and no orphaned entries outside the table. Grep for `### v` outside the table section.

---

### Cognitive Function Labels Must Be Distinct Across Agents (2026-02-08) — ACTIVE

Validator and code-reviewer both initially used "Analytical validation" as cognitive function label. Contrarian reviewer caught the collision — identical labels undermine the distinctness argument. Renamed validator to "Checklist verification."

**Rule:** When creating a new subagent, verify its cognitive function label is unique across all agent definitions. Same mental operation = extend existing agent; different operation = different label.

---

### Run Code Review + Coherence Audit After Content Expansions (2026-02-21) — GRADUATED to §5.1.7

After a 6-principle multimodal-RAG expansion, code review found 3 code issues (misleading comment, missing f-series mapping, r-series semantic mismatch) and coherence audit found 7 document issues (stale version headers/footers, missing evidence base refs, cross-file contradictions). None were caught by the test suite because tests validated extraction behavior, not document-level consistency.

**Rule:** After any content expansion that adds new series, principles, or methods: run both code-reviewer and coherence-auditor agents before considering the work complete. Tests catch extraction bugs; audits catch semantic drift.

---

### S-Series Keyword Trigger Produces False Positives on Negations (2026-02-22)

`evaluate_governance(planned_action="...no security implications — purely content expansion...")` returned ESCALATE because the S-Series keyword scanner matched "security" in the action description. No actual S-Series principles were returned (`principles: []`), confirming the trigger was the word itself, not a real safety concern. The action was a content-only document edit with no code, auth, or infrastructure changes.

**Rule:** When `s_series_check.triggered=true` but `s_series_check.principles=[]`, this is a keyword false positive. Proceed with documented override. When writing `planned_action` descriptions, avoid safety-adjacent keywords in negation phrases (e.g., say "purely content expansion" instead of "no security implications") to reduce false trigger noise.

---

### Version Validator Has Blind Spots — Title and Footer Not Checked (2026-02-21)

`validate_version_consistency()` only searches `content[:2000]` for the pattern `Version:? X.Y.Z`. Document titles (e.g., `# Framework v2.0.0`) use a different format that the regex doesn't match. Footers (e.g., `*Version 2.0.0*`) are beyond the 2000-char window. Both went stale when content was updated to v2.1.0 in-place without renaming files.

**Rule:** When updating document content versions in-place (per "Governance Docs In-Place" decision), manually update title, footer, and cross-reference version numbers. The automated validator won't catch these.

---

### Specification Documents Are Not Validated Requirements (2025-12-24) — CRITICAL

Implemented full server based on spec that said "~5% miss rate with keyword matching." PO review revealed this was unacceptable. Spec became a constraint instead of a starting point.

**Rule:** Run discovery questions with PO before implementing architectural decisions. Present options with tradeoffs. Wait for explicit approval.

---

### Claude Desktop and CLI Have Separate MCP Configs (2026-01-04) — CRITICAL

User reported "0 domains" — server connected but returned empty data. CLI config (`~/.claude.json`) didn't have env vars; Desktop config did. They are independent systems.

**Rule:** When building MCP servers that depend on file paths, require explicit paths via env vars. Fail loudly when index files are missing.

---

### ML Model Mocking: Patch at Source (2025-12-27) — CRITICAL

Mocking at `ai_governance_mcp.retrieval.SentenceTransformer` fails — models are lazy-loaded. Patch at `sentence_transformers.SentenceTransformer`. Use `side_effect` returning `np.random.rand(len(texts), 384)` for correct batch shapes. See Gotchas #5, #6.

---

### Multi-Pass Reviews Catch Different Issue Classes (2026-01-04) — CRITICAL — GRADUATED to §5.1.7

Second-pass contrarian review caught issues first-pass missed (S-Series penalty risk, min ratings threshold). First pass reviews original design; second pass reviews the fixes.

**Rule:** After fixing HIGH/CRITICAL findings, run second-pass review on the fixes themselves.

---

## Graduated Patterns

| Pattern | Graduated To | Date |
|---------|-------------|------|
| Process Map visualization | PO preference in PROJECT-MEMORY | 2025-12-26 |
| Communication Level calibration | PROJECT-MEMORY Patterns | 2025-12-26 |
| Portfolio-Ready README | PROJECT-MEMORY Patterns | 2025-12-26 |
| Spec completeness verification | Gotcha #17, CLAUDE.md workflow | 2025-12-22 |
| conftest.py fixtures | ARCHITECTURE.md Mocking Strategy | 2025-12-27 |
| CPU-only PyTorch in CI | ci.yml, Gotcha #9 | 2025-12-27 |
| Domain routing threshold tuning | retrieval.py implementation | 2025-12-28 |
| Constitution/Methods separation | ARCHITECTURE.md, document structure | 2025-12-28 |
| Index architecture verification | Gotcha #13, ARCHITECTURE.md | 2026-01-17 |
| Feedback score boost/penalty | retrieval.py, PROJECT-MEMORY decisions | 2026-01-04 |
| Governance enforcement research | PROJECT-MEMORY decisions | 2026-01-03 |
| Version sync discipline | Gotcha #16, PROJECT-MEMORY | 2026-02-10 |
| MCP server index caching | Gotcha #15 (resolved by auto-reload) | 2026-02-10 |
| Security hardening is layers | ARCHITECTURE.md Security Features | 2026-02-10 |
| Research ≠ governance test | PROJECT-MEMORY decisions | 2026-02-10 |
| Anchor bias in document review | meta-methods Part 7.10 | 2026-02-10 |
| Instruction vs content surfaces | Gotcha #17 | 2026-02-12 |
| Embedding model token limits | ADR-2 in PROJECT-MEMORY | 2026-02-12 |
| Docker multi-arch ML | ADR-9 in PROJECT-MEMORY | 2026-02-12 |
| External eval depth | General knowledge (active since Jan) | 2026-02-12 |
| Custom subagent files not invokable | CLAUDE.md subagents note | 2026-02-12 |
| MCP stdio immediate exit | server.py implementation | 2026-02-12 |
| Per-response reminder prevents drift | server.py implementation | 2026-02-12 |
| Framework bootstrap activation layer | CLAUDE.md + ai-instructions | 2026-02-12 |
| Context Engine hardening (defense-in-depth) | Methods §5.9/§5.10 | 2026-02-22 |
| BM25Okapi negative score clamping | Code implementation + §5.10 | 2026-02-22 |
| Go type_declaration tree-sitter names | Code implementation | 2026-02-22 |
| Editable install vs running MCP server | Gotcha #27 | 2026-02-22 |
| Transitive dependency drift in Docker | Gotcha #19 | 2026-02-22 |
| Substring collision comment verification | Code review finding, implemented | 2026-02-22 |
| IDE plug-in API vs subscription pricing | General knowledge (not project-specific) | 2026-02-22 |
| Standalone MCP config files | Redundant with CRITICAL lesson #24 | 2026-02-22 |
| Code review + coherence audit after expansions | ai-coding methods §5.1.7 + §9.3.11 | 2026-03-27 |
| Multi-pass reviews catch different issues | ai-coding methods §5.1.7 | 2026-03-27 |
| CI must install all test-relevant extras | Gotcha #23 | 2026-04-13 |
