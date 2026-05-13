# Compliance Review — Verification Items

> Verification items are time-bound experiments tracking whether recently-introduced mechanisms are working. Each has success/failure criteria and an expiration date. When confirmed or refuted, items move to Retired with a disposition.

## Active Verification Items

### [V-006] Pre-exit-plan-mode-gate hook-denial rate — OPEN

**Hypothesis:** Hook denial rate trends toward zero over the next N sessions as the paired CLAUDE.md + tiers.json `contrarian-before-exit-plan` directive internalizes. If denials stay flat (e.g., ≥1 per plan-mode session), the directive is not changing AI behavior — the hook is the sole enforcement mechanism and the advisory layer is decorative.

**Added:** 2026-04-23 (session-122 post-commit double-check)
**Confirm/Refute by:** 10 sessions with ≥1 plan-mode invocation from 2026-04-23.

**Process indicator:** Count of `deny` entries in `~/.context-engine/plan-contrarian-denies.log` per session (attribute via transcript session-id in log line). Normalized by number of plans attempted (deny-per-plan rate).

**Success (directive works):** Denial rate ≤ 20% (1/5 plans) by session 10. Interpretable as "AI invokes contrarian unprompted 4/5 times, hook catches the missed one."
**Failure (directive decorative):** Denial rate ≥ 40% after session 10 (2/5 plans or worse). Interpretable as "AI relies on hook deny as trigger, not CLAUDE.md directive." Escalation: strengthen the directive (more prominent placement, few-shot examples in plan-template, or move to a PreToolUse on `Write` to any plan file forcing contrarian first).

**Baseline:** 2 deny entries on 2026-04-22 during session-122's own implementation (the hook caught itself during dogfood — which is actually positive evidence that the mechanism works, per post-commit contrarian `ac0e663f80114248d`). Clean measurement starts session-123.

**Semantic-bypass signal:** `semantic-bypass` entries in the same log. If the AI routinely invokes `PLAN_CONTRARIAN_CONFIRMED=1` instead of actually invoking contrarian, the directive is also failing in a different way. Track separately.

| Session | Date | Plans | Denies | Semantic-bypasses | Notes |
|---------|------|-------|:---:|:---:|-------|
| pre-baseline | 2026-04-22 | 1 (session-122 T3) | 2 | 0 | Dogfood: hook caught itself during implementation. Captured for context, not counted. |
| 1 | 2026-04-25 | 0 (auto-mode this session, no plan mode) | 0 | 0 | First post-baseline session entry. Log filtering for real-session attribution (excluding test-fixture entries with `transcript=/var/folders/` or `<none>` paths) returned 0 real denies since 2026-04-25. Test-fixture writes from hook test runs do continue to land in the log; consider adding a test-mode marker to allow filtering. |
| 2 | 2026-05-02 | 1+ | 1 | 0 | Session fe982d05. Hook denied ExitPlanMode; contrarian subsequently invoked. |
| 3 | 2026-05-02 | 1+ | 2 | 0 | Session 09996585. Two denies suggest retry without contrarian. |
| 4 | 2026-05-05 | 1 (CE-First Search plan) | 0 | 0 | Session-149 (9cb3a822). Contrarian invoked unprompted — 0 denies, 0 semantic-bypasses. Plan exited cleanly via hook gate. |
| 5 | 2026-05-12 | 1 (SSOT + list_agents plan) | 2 | 0 | Session-168 (c1e8c837). Hook blocked ExitPlanMode twice; contrarian subsequently invoked (2 rounds). Deny rate across plan-mode sessions: 3/4 (75%) — above 40% failure threshold but only 5/10 sessions measured. |

---

### [V-007] Plan-action-atomicity WARN-mode firing rate — OPEN

**Hypothesis:** Plans approved via ExitPlanMode comply with the action-atomicity rule (plan-template Recommended Approach section, shipped Commit 2 of Superpowers plan). The WARN-mode hook gate (Commit 6 of same plan) catches violations advisory-only.

**Added:** 2026-04-25 (session-126, Commit 6 of Superpowers plan)
**Confirm/Refute by:** Event-driven — promote to BLOCK on first coherence-audit finding flagging WARN-mode pattern actually firing on real code (per plan HIGH-2 fold).

**Process indicator:** Count of stderr `[plan-action-atomicity] WARN` lines emitted by `pre-exit-plan-mode-gate.sh` per plan-mode session. Source: terminal stderr capture during ExitPlanMode (or hook debug log if instrumented).

**Promotion trigger (event-driven, no count required):** When a plan ships that subsequently produces a defect coherence-auditor would have caught had the WARN-mode plan-atomicity finding been a BLOCK, promote `_warn_action_atomicity` from WARN to deny. Mechanism: track in this section's table the session/finding-ID where the trigger fires.

**In-band reminder mechanism (per post-ship contrarian battery, audit `a62e96c04a3f91721`):** The WARN message itself includes a pointer to V-007 ("if this WARN ever pre-figures a real bug, file the trigger event in V-007 row of `.claude/skills/compliance-review/verification.md`") so the trigger isn't dependent on humans remembering this V-series exists. Closes the human-memory failure mode the contrarian flagged: "event-driven trigger has the same human-memory problem as count-based, just hidden behind 'event-driven' framing." The in-band reminder makes the trigger structurally visible at the moment the WARN fires.

**Bypass:** `PLAN_ACTION_ATOMICITY_SKIP=1` (un-audited; non-load-bearing while WARN-only). Add audit-logging if/when promoted to BLOCK.

**Baseline:** First WARN scan ships session-126 with this hook integration. Plan `~/.claude/plans/federated-plotting-karp.md` (current session) is the dogfood test — if `_warn_action_atomicity` fires on this plan's own task entries, document below.

| Session | Date | Plans | WARN fires | Promoted? | Notes |
|---------|------|-------|:---:|:---:|-------|
| 126 (baseline) | 2026-04-25 | 0 (no plan-mode this session post-Commit 6) | 0 | N | First instrumentation. |
| | | | | | |

---

### [V-008] TDD test-existence WARN-mode firing rate — OPEN

**Hypothesis:** New `src/*.py` files ship with paired `tests/test_*.py` files in the same change. The WARN-mode pre-push hook gate (Commit 6 of Superpowers plan) catches missing pairs advisory-only.

**Added:** 2026-04-25 (session-126, Commit 6 of Superpowers plan)
**Confirm/Refute by:** Event-driven — promote to BLOCK on first coherence-audit finding (or production defect) where missing test pair on a new src file caused a regression that paired tests would have caught.

**Process indicator:** Count of stderr `[tdd-test-existence] WARN` lines emitted by `pre-push-quality-gate.sh` per push that touches `src/*.py`. Source: terminal stderr capture during `git push` (or hook debug log).

**Promotion trigger (event-driven, no count required):** When a regression ships that paired tests would have caught and the WARN scan flagged the missing pair pre-push, promote from WARN to deny. Mechanism: track in this section's table the regression session-ID.

**In-band reminder mechanism (per post-ship contrarian battery, audit `a62e96c04a3f91721`):** The WARN message itself includes a pointer to V-008 ("if this WARN ever pre-figures a real bug, file the trigger event in V-008 row of `.claude/skills/compliance-review/verification.md`") so the trigger isn't dependent on humans remembering this V-series exists. Same rationale as V-007 above — closes the human-memory failure mode in the event-driven trigger framing.

**Bypass:** `TDD_TEST_EXISTENCE_SKIP=1` (audit-logged via shared `audit_bypass()` helper as of session-153 / BACKLOG #135).

**Baseline:** First WARN scan ships session-126 with this hook integration. No new src files in this commit (scanner self-test is in `tests/test_hooks.py::TestTddTestExistence`, not a real src addition).

| Session | Date | Pushes with new src/*.py | WARN fires | Promoted? | Notes |
|---------|------|-------|:---:|:---:|-------|
| 126 (baseline) | 2026-04-25 | 0 | 0 | N | First instrumentation. Scanner integration only; no src additions. |
| | | | | | |

---

---

## Retired Verification Items

### [V-009] Bypass audit-log coverage — CONFIRMED (2026-05-12)

**Disposition:** CONFIRMED at Compliance Review #8 (2026-05-12). `grep -c audit_bypass .claude/hooks/*.sh` = 5 files (all hooks with bypass envvars). 9/9 bypass envvars produce audit-log entries. Test coverage: `tests/test_hooks.py::TestBypassAuditLog`, `test_pre_exit_plan_mode_gate_hook.py::TestUnifiedBypassAuditLog`, `test_pre_test_oom_gate_hook.py::TestBypassAuditLog`, `test_content_security_hook.py::TestBypass::test_bypass_writes_audit_log`. No silent bypasses remain.

**Hypothesis:** All 9 hook bypass envvars write to the unified audit log via shared `audit_bypass()` helper.
**Added:** 2026-05-07 | **Confirmed:** 2026-05-12 (Compliance Review #8)

### [V-001] UBDA few-shot examples improve behavioral floor compliance — RETIRED → REPLACED-BY-SESSION-AUDIT (2026-04-25)

**Disposition:** RETIRED at Compliance Review #5 (2026-04-25). Canary-prompt measurement vehicle (Item 5a-c) replaced by session-audit (Item 5d) via validator subagent per `meta-method-proportional-rigor` and `multi-quality-validation-independence`. Few-shot examples in CLAUDE.md remain in place — the process indicator (binary "examples present") is structurally satisfied. The behavioral question ("do the examples reduce failure modes?") is now measured by validator subagent during session audit (4 consecutive reviews — #2/#3/#4/#5 — returned PASS or PASS_WITH_NOTES on the relevant pattern checks: option-list use, ranked recommendations, principle citations). Retained below for audit trail.

**Rationale for retirement (n=3 deferral + structural superiority of session audit):**
- Canary prompts deferred 3 consecutive reviews (#3/#4/#5) per execution-only precedent.
- Canary prompts have a known structural limitation per Item 5 itself: *"The AI knows it's being tested — canary results represent best-case behavior, not typical."*
- Session-audit via validator subagent measures the same behaviors against actual session output, not synthetic prompts. Independence guarantee per `multi-quality-validation-independence` is stronger.
- Retaining the canary measurement arm without running it generates audit-table noise (3 deferral rows in 3 reviews) without adding signal.

**Hypothesis (preserved for audit trail):** The WRONG/RIGHT examples added to CLAUDE.md in task #77 reduce instances of option-list presentation, question-instead-of-recommendation, and missing principle citations.

**Added:** 2026-04-07 | **Retired:** 2026-04-25 (Compliance Review #5)

**Process indicator:** CLAUDE.md contains few-shot examples (binary — present or not). **Status: still satisfied.**
**Behavioral indicator (retired):** Canary prompt results from Item 5 (0 violations = session pass).
**Behavioral indicator (replacement):** Session-audit via validator subagent (Item 5d) — pattern checks 5, 6, 7 cover the same behavioral surfaces.

| Session | Date | Canary Pass? | Notes |
|---------|------|:---:|-------|
| 1 | 2026-04-07 | Y | Behavioral regression test — 5/5 behaviors exhibited |
| 2 | 2026-04-14 | Y | Canary prompts run. Ranked recommendation (a), conversational prose (b), principle citations (c). Awaiting user confirmation. |
| 3-5 | n/a | RETIRED | Canary arm retired before reaching 5-session window. Session-audit (5d) PASS/PASS_WITH_NOTES across Reviews #2/#3/#4/#5 functions as the replacement measurement; no session-audit failure on the relevant pattern checks observed. |

**Future restoration trigger:** If session-audit (5d) ever fails on a pattern check that canary prompts would have caught (option-list format, missing citation, unranked options) AND the validator subagent cannot diagnose source, re-instate canary measurement as supplementary diagnostic. Track here.

---

### [V-004] Contrarian review compliance before ExitPlanMode — REFUTED → ESCALATED → IMPLEMENTED (2026-04-23)

**Disposition:** Hypothesis REFUTED at Review #4 (2026-04-22): 3 sessions required user reminder (baseline, session 3, session 121) exceeding 2-session FAILURE threshold. Escalated to PreToolUse hook on ExitPlanMode per disposition. Hook shipped session-122 (2026-04-23, `.claude/hooks/pre-exit-plan-mode-gate.sh`) with CLAUDE.md Behavioral Floor + tiers.json pairing (contrarian-before-exit-plan directive). 17 unit tests cover scanner + hook contract. See BACKLOG #116 (closed) + LEARNING-LOG 2026-02-28 "Hard-Mode Hooks Prove Deterministic Enforcement Works." Retained below for audit trail.

**Hypothesis:** Strengthened plan template gate text ("DO NOT populate Recommended Approach until contrarian section has content") reduces contrarian-skip failures.

**Added:** 2026-04-08
**Confirm/Refute by:** 3 sessions with plan mode from 2026-04-08

**Process indicator:** Was contrarian-reviewer invoked before ExitPlanMode without user prompting? (Evaluated by **validator subagent** during compliance review, not self-reported — per `multi-quality-validation-independence`.)

**Success:** 3/3 sessions invoke contrarian unprompted.
**Failure:** 2+ sessions require user reminder → escalate to PreToolUse hook for ExitPlanMode.

**Baseline:** This session: 2/4 plans needed user reminder (50% unprompted compliance).

| Session | Date | Plans | Contrarian Unprompted? | Notes |
|---------|------|-------|:---:|-------|
| 1 (baseline) | 2026-04-08 | 4 | 2/4 (50%) | 2 skipped, user corrected both |
| 2 | 2026-04-10 | 1 | 1/1 (100%) | Contrarian invoked before writing Recommended Approach, per template gate. REVISIT verdict accepted — plan revised. |
| 3 | 2026-04-13 | 2 | 1/2 (50%) | Plan 1 (audit fixes): contrarian invoked after user reminder. Plan 2 (compliance): contrarian invoked after user reminder. |
| 4 | 2026-04-14 | 1 | 1/1 (100%) | CE tool selection plan: contrarian invoked before Recommended Approach, unprompted. |
| 5 | 2026-04-21 (session-121) | 2 | 1/2 (50%) | Plan 1 (Task 4, BACKLOG #91 sub-item 3): ExitPlanMode called WITHOUT Plan+contrarian; user rejected with "Did you follow ai-governance... Did you take advantage of subagents" → contrarian invoked only after reminder. Plan 2 (Task 5, CFR §9.3.10 recipe): contrarian invoked unprompted as part of pre-edit 3-agent battery alongside Plan + coherence. **V-004 FAILURE THRESHOLD MET** (3 sessions with reminders required: baseline, session 3, session 121). Escalation path: PreToolUse hook on ExitPlanMode that requires contrarian-reviewer transcript match. Filed as BACKLOG #116. |

---

### [V-005] SESSION-STATE pruning compliance — CONFIRMED (2026-05-05)

**Disposition:** CONFIRMED at Compliance Review #7 (2026-05-05). 5/5 sessions ended under 300 lines (range 54–292, mean ~164). Advisory pruning instructions on CLAUDE.md §Session Lifecycle + AGENTS.md + MEMORY.md are sufficient. No escalation to pre-push hook needed. §7.0.4 distillation protocol is the active enforcement mechanism. Keep advisory instructions in place. Retained below for audit trail.

**Hypothesis:** Advisory pruning instructions on always-loaded surfaces (CLAUDE.md, AGENTS.md, MEMORY.md) keep SESSION-STATE.md under 300 lines across sessions.

**Added:** 2026-04-14 | **Confirmed:** 2026-05-05 (Compliance Review #7)
**Confirm/Refute by:** 5 sessions from 2026-04-14

**Process indicator:** `wc -l SESSION-STATE.md` at session end.

**Success:** 5/5 sessions end with SESSION-STATE under 300 lines.
**Failure:** 2+ sessions exceed 300 lines at session end → escalate to pre-push hook warning (not block) for SESSION-STATE line count.

**Baseline:** This session: 54 lines (post-cleanup).

| Session | Date | Lines | Under 300? | Notes |
|---------|------|-------|:---:|-------|
| 1 (baseline) | 2026-04-14 | 54 | Y | Post-cleanup. First session with pruning instructions on loaded surfaces. |
| 2 | 2026-04-17 | 79 | Y | Session-109 end; grew 54→79 with session-109 entry + V-005 update, comfortably under target. |
| 3 | 2026-04-22 | 283 | Y | Session-121 end (pre-prune). 4 tasks shipped: #114 + #90 closure + #103 closure + #91 sub-item 3 + CFR §9.3.10 recipe. Comfortably under 300. V-005 confirmed at N=3 sessions. 2 more to confirm hypothesis. |
| 4 | 2026-04-25 | 292 | Y | Session-130 mid-review reading. Approaching threshold; this compliance review row-update arc adds ~10 additional lines via SESSION-STATE entry → final close-state will likely be ~310 absent prune. §7.0.4 prune required at session-end before commit. |
| 5 | 2026-05-05 | 112 | Y | Session-149 end. **5/5 sessions under 300 lines. HYPOTHESIS CONFIRMED.** Advisory pruning instructions on always-loaded surfaces (CLAUDE.md, AGENTS.md, MEMORY.md) keep SESSION-STATE.md under 300 lines. Range across 5 sessions: 54–292 lines (mean ~164). Session-149 is the lowest since the baseline, reflecting aggressive §7.0.4 pruning of sessions 101-143. |

---

### [V-002] Completion checklist hook effectiveness — CONFIRMED

**Hypothesis:** Pre-push hook Check 4 achieves ≥80% checklist consultation rate.
**Period:** 2026-04-07 to 2026-04-13 (5 sessions)
**Result:** CONFIRMED. 4/4 applicable sessions consulted (1 N/A — no code changes). 0/5 hook-triggered. 100% proactive consultation.
**Disposition:** Keep pre-push hook Check 4 as passive safety net. No escalation needed.

---

### [V-003] Session startup read compliance — CONFIRMED

**Hypothesis:** Reading all 3 memory files at session start improves session quality.
**Period:** 2026-04-07 to 2026-04-13 (5 sessions)
**Result:** CONFIRMED. 3/5 sessions where PM/LL reads changed behavior. Sessions 1-2 (pre-hook) missed reads. Sessions 3-6 (post-hook advisory) all compliant.
**Disposition:** Keep Layer 2 advisory enforcement (UserPromptSubmit hook). Do NOT escalate to Layer 3 blocking — startup reads are context quality improvements, not safety gates. Advisory hook working: 4/4 post-hook sessions compliant.
