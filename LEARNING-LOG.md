# AI Governance MCP - Learning Log

**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> **Entry rules:** Each entry ≤5 lines. State what happened, then the actionable rule.
> Record conclusions, not evidence. If it wouldn't change future behavior, it doesn't belong here.
> When lesson graduates: Add to methods doc, mark "Graduated to §X.Y"
> Route other content: decisions → PROJECT-MEMORY, architecture → ARCHITECTURE.md

---

## Active Lessons

### BASH_COMMAND Is a Reserved Variable — Never Use It for Application State (2026-05-07)

Session-152 named a shell variable `BASH_COMMAND` to hold the Bash command extracted from hook input JSON. Bash automatically overwrites this built-in with the currently-executing command on every simple command execution, so the variable silently held the debug line itself instead of the extracted command. All downstream logic (read-only detection) received the wrong value. Fixed by renaming to `TOOL_CMD`.

**Rule:** Never use `BASH_COMMAND`, `BASH_SOURCE`, `BASH_LINENO`, `BASH_REMATCH`, `FUNCNAME`, `LINENO`, `RANDOM`, `SECONDS`, `PIPESTATUS`, or other Bash special variables for application state. These are managed by the shell and will be overwritten silently. Use descriptive application-specific names (e.g., `TOOL_CMD` instead of `BASH_COMMAND`).

**How to apply:** When writing shell scripts that extract values from JSON input, name variables after their semantic role (`TOOL_CMD`, `TOOL_NAME`, `HOOK_INPUT`), not after what they contain (`BASH_COMMAND`, `SHELL_CMD`). If unsure whether a name is reserved, check `man bash` under "Shell Variables."

---

### Behavioral Compliance ≠ Structural Compliance — Hook Enforcement Has a Blind Spot (2026-05-07)

Session-152's 10-agent governance test proved that 100% behavioral compliance (all subagents called `evaluate_governance` + `query_project` unprompted) can coexist with 100% structural denial (all blocked by hook). The hook verified compliance against the wrong file (parent transcript vs subagent transcript). This is not a scanner bug — the scanner works correctly on the file it's given. It's a routing gap: the hook input provides only `transcript_path` (parent's), with no `agentId` or subagent indicator.

**Rule:** When testing enforcement mechanisms, verify that the mechanism can observe the behavior it's supposed to enforce. A correct enforcement algorithm applied to the wrong data produces false negatives (under-enforcement) or false positives (over-enforcement) that look like algorithm bugs but are data-routing bugs.

**How to apply:** Before claiming an enforcement mechanism "works," trace the data path: what file/source does the enforcer read? Does that source contain the events the enforcer needs to see? For hooks specifically: does `transcript_path` point to the transcript where the relevant tool calls actually appear?

---

### Pressure-Test the BACKLOG Entry's Framing, Not Just the Implementation Plan (2026-04-28)

Session-138 picked up BACKLOG #144 as filed: a *detector* for bare `<file>.md:<line>` citations that checks each cited line against a stable-anchor pattern set. Plan v1 absorbed that framing and proposed ~150 lines of detection code + ~250 lines of test fixtures + a maintained anchor-pattern set. Contrarian-reviewer (run against plan v1 before ExitPlanMode per project hook) surfaced that the *framing itself* was wrong: the detector defends a citation form §9.8.9 v3.31.3 already recommends against, has fundamental coverage gaps (English-prose `(line N)` bypasses any `\.md:\d+` regex; range end-drift slips past start-line check; the 6-pattern anchor set is necessarily incomplete), and at 28 verified live citations the migration alternative (forbid the form + rewrite to §-anchor) is smaller AND ends the failure class. Plan v2 pivoted: **Forbid + Migrate** instead of Detect. Final shape: ~140 lines script + 14 tests + 21 live citation migrations + CI + pre-commit. The detector approach moved to "Simpler Alternatives Evaluated" as the rejected option. Result: structural prevention rather than leaky detection of a deprecated pattern.

**Rule:** When a BACKLOG entry prescribes a specific solution shape ("a CI check that does X by parsing Y and asserting Z"), run the contrarian-reviewer's first pass against the *solution shape* — not against the implementation correctness. Pressure-test "should this be a detector at all?" before pressure-testing "does the detector correctly handle multi-cite forms?" The former question can pivot the entire plan; the latter only refines it.

**How to apply:** Before drafting the "Recommended Approach" section of a plan based on a BACKLOG entry, ask: (1) Does §9.8.9 / §X.Y.Z already declare the position the BACKLOG entry's solution implicitly takes? (2) Did the BACKLOG entry's framing assume a count or scope (e.g., "~50 citations") — if so, verify the count empirically before letting it drive the solution shape. (3) Is the proposed solution defending a deprecated form or eliminating it? Defending = legitimizing; eliminating = ending the failure class. Run contrarian-reviewer on the plan-v1 framing explicitly: "Is this defending the wrong invariant?" — and let it pivot the plan if so.

**Why this prevents recurrence:** BACKLOG entries get filed under specific framings — often the framing the filer happened to be holding when they recorded the item. Months later, when a session picks the entry up, the framing has crystallized into "the spec." But a session can rewrite the framing if the contrarian step questions it BEFORE the plan locks in. Once "Recommended Approach" has 10 task entries with TDD action atomicity, the plan inherits the framing's gravity; reframing then requires throwing away substantive structure. Pre-plan-mode contrarian framing-check is cheap; post-plan-mode reframing is expensive.

**Principle:** `meta-core-systemic-thinking` (root cause = framing → solution shape → fundamental coverage limits; structural fix = pivot framing before plan locks); `meta-quality-verification-validation` (verify the entry's count/premise empirically before solution-sizing); `coding-method-defer-vs-fix-now` (the contrarian is what makes "fix now within scope" defensible — without it, plan-mode just executes whatever framing the entry was filed under).

**Cross-ref:** Session-138 commit `6b01279` (BACKLOG #144 close, plan-v2 Forbid + Migrate); plan files `~/.claude/plans/async-bouncing-reddy.md` (v1 → v2 rewrite); contrarian-reviewer in-session output (10 findings, 5 verdict-changing items absorbed). Pair-watches with 2026-04-26 "Agent Convergence Doesn't Validate Premises" — same lesson at a different timing layer (that lesson was about verifying the *factual* premise; this one is about verifying the *framing* premise). Pair-watches with the auto-memory "Decide, don't defer — apply 80/20 first" feedback rule: the 80/20 here was the contrarian's strongest point (28 ≠ 50 → migration tractable → framing flips).

---

### IPC Daemon Silently Intercepts Model Loading in Benchmarks (2026-05-05)

Session-148 Phase 4 (embedding model evaluation) produced identical MRR/R@5/R@10 for all three candidate models — a result that was technically impossible. Root cause: the IPC embedding daemon intercepts model loading in the indexer's lazy-load path (checks socket existence before falling back to local `SentenceTransformer`). All three evaluation runs used the daemon's single loaded model (BGE-small) regardless of which model was requested.

**Rule:** When benchmarking embedding models, set `AI_CONTEXT_ENGINE_EMBED_SOCKET=none` to force local model loading. The `evaluate_embeddings.py` script now does this automatically. More broadly: when comparing alternatives against a shared-resource architecture, verify the alternatives are actually being isolated — shared caches, singletons, and IPC services can silently eliminate the variation you're trying to measure.

**How to apply:** Before trusting A/B benchmark results, check that per-model dimensions match expectations (BGE-small=384, BGE-base=768). Identical dimensions across models of different architectures is a signal that model loading was intercepted.

---

### Apply Newly-Shipped Specs to Host Files in Same Arc (2026-04-28)

Session-137 BACKLOG #100 arc shipped §9.8.9 (Legal System Analogy Authoring) in Commit 1 — the spec declared method-level surfaces ineligible for italicized analogy blocks. Subsequent commits cleaned up 15 misplaced principle-level analogies in constitution + title-10. User then requested a thorough double-check audit. Two parallel subagents (contrarian `a7a951cb33f490ada` + coherence-auditor `aa443ab0670fe55a8`) caught what 5+ prior subagent rounds missed: rules-of-procedure.md itself (the spec's host file) contained 6 method-level "Legal Analogy:" blocks at §7.2/7.3/7.4.4/7.5/7.7/7.8. The §7.4.4 block invoked "Stare Decisis" as a positive structural analogy, **directly contradicting §9.7.7 register's `considered-and-rejected` classification of the same concept** — the framework asserted X at one location and not-X at another. Pre-shipping batteries didn't catch this because they scanned the diff (the new §9.8.9 spec section), not the host file's pre-existing content. Compliance Review #6 would have caught it. Commit 5 (`8957179`) folded all 5 audit findings into a PATCH.

**Rule:** When an arc ships a NEW spec defining what content is or isn't allowed in some class of surface, **grep the spec's own host file for instances of the now-disallowed pattern as part of the spec-shipping commit**, not as deferred follow-up. Treat host-file self-application as part of the spec-shipping work, not a separate cleanup task.

**How to apply:** During spec authoring for ineligibility/eligibility/anti-pattern rules, before committing the new spec section, run: `grep -nE '<pattern-the-spec-disallows>' <host-file>`. If the host file contains instances of the now-disallowed pattern, fold the cleanup into the same commit (per Defer-vs-Fix-Now: ≤3 files, no cascading discovery, known fix). Do NOT defer to a separate "spec-application" commit — the gap between spec-ship and spec-apply is exactly the window in which internal contradictions silently survive subagent batteries.

**Why this prevents recurrence:** Pre-shipping batteries (contrarian, validator, coherence-auditor) primarily scan the diff — the new content being introduced. They are less likely to detect pre-existing host-file content that becomes newly non-compliant under the spec being introduced in the same diff. Post-shipping, that gap closes (subsequent audits scan the file, not the diff). The structural cause is treating spec-creation and spec-application as separate tasks; the structural fix is recognizing them as the same task at ship time.

**Principle:** `meta-core-systemic-thinking` (root cause = task decomposition mistake — spec-ship and spec-apply are the same task, not two tasks); `meta-method-single-source-of-truth` (one canonical home; host file shouldn't contradict the spec it hosts); `meta-quality-verification-validation` (post-arc audit caught what pre-ship batteries missed; closing the gap requires self-grep at ship time).

**Cross-ref:** Session-137 commit `8957179` (Commit 5 post-arc remediation); paired with the 2026-04-26 "Update SESSION-STATE Once, Post-Arc" lesson — both are *task-decomposition* failures where treating one logical task as two created drift between the parts.

---

### Update SESSION-STATE Once, Post-Arc — Interleaved Updates Generate Drift Cascades (2026-04-26)

Session-135 shipped 3 work commits (#141 close + harmonization fold-in + #142 close) but interleaved SESSION-STATE.md updates within each commit. Result: 2 successive narrative-drift fix commits (`641d4ac`, `4f25af6`) needed to repair count-claim drift ("3 commits" stale post-fix-commit), "forthcoming" framing stale post-`e71b708`, and last-push hash drift (`f1ecd08` → actual `b23cdab`). Each fix-commit only caught some drift; the next had to fix what the prior missed, because each interleaved SESSION-STATE update describes the state at THAT moment but cannot anticipate subsequent commits. Final shape: 5 commits ahead of origin (3 work + 2 narrative-drift fold-ins) for what should have been a 4-commit arc (3 work + 1 SESSION-STATE update). Cumulative-arc pre-push double-check (`aed69b709923a091b` contrarian + `a20b052b70e903339` coherence) caught the first wave; final pre-push double-check (`a62ae4a357cb78cc4` contrarian + `a5911082fc45e6e94` coherence) caught the second wave including the pre-existing `f1ecd08` last-push drift inherited from session-134.

**Rule:** When closing a multi-commit session arc, update SESSION-STATE.md ONCE in a final commit AFTER all work commits ship. Each work commit edits BACKLOG.md (item removal), version bumps, content edits — but NOT SESSION-STATE.md. Pre-push double-check then verifies the SESSION-STATE narrative against actual git log.

**How to apply:** For multi-commit arcs (≥2 work commits): (1) Ship work commits without touching SESSION-STATE.md. (2) After the last work commit lands, do ONE final SESSION-STATE update commit naming all work-commit hashes + their cumulative effects. (3) Pre-push double-check the SESSION-STATE narrative against `git log origin/main..HEAD`. For single-commit arcs (D1 trunk-direct), the existing pattern of folding SESSION-STATE into the same commit remains correct — no interleaving exposure.

**Why this prevents recurrence:** SESSION-STATE is descriptive of the arc, not part of the arc. Updating it during the arc means describing a partial state. Updating it after the arc means describing a complete state. The structural cause of session-135's 5-commit shape was treating SESSION-STATE as part of every work commit; the structural fix is recognizing it as a post-arc summary that requires the arc to be complete before authoring.

**Principle:** `meta-quality-verification-validation` (verify before claim — the "claim" here is "the arc looks like X" which can only be verified post-arc); `meta-method-single-source-of-truth` (git log is the SOT for what shipped; SESSION-STATE narrative must match SOT, which can only happen post-shipping); `meta-core-systemic-thinking` (structural cause = interleaved-update timing; structural fix = post-arc-only update timing).

**Cross-ref:** Session-135 commits `2e4533c` / `c3b8e59` / `e71b708` / `641d4ac` / `4f25af6`; cumulative-arc + final pre-push double-checks. Pair-watches with the 2026-04-26 "Agent Convergence Doesn't Validate Premises" entry — same root-cause discipline applied at the workflow-timing layer rather than the factual-claim layer.

---

### Agent Convergence Doesn't Validate Premises — §8.3.4 Discovered Factual Error (2026-04-26)

Session-127 had triple-agent convergence (contrarian + security-auditor + coherence-auditor) on the §8.3.4 routing rule, including the assertion "AI cannot auto-push to main is a structural invariant; the harness default-branch-protection block stays in place." Session-134 BACKLOG #140 investigation revealed the harness block doesn't exist as a hard mechanism — what we observed was Layer 1 (Claude-the-model conservative on policy) + Layer 2 (project's pre-push hook) + Layer 3 (this same document reinforcing Layer 1) circularly self-validating. The session-127 *conclusion* was correct (don't add PR-required-by-class for solo work) but the *premise* was false. Three reviewers agreed on the conclusion without catching the premise — **agent convergence does not validate premises**. The §8.3.4 amendment (commit `f1ecd08`) re-derived the conclusion from the corrected premise; conclusion held independently via the four-reason rationale (combined-gate rule, no defect-class delta, prompt-injection surface, hypothesized-adopter overreach), but the structural-safety claim shifted from "harness block" (false) to "pre-push hook with 7 gates + 4-layer defense-in-depth" (true).

**Rule:** When multiple subagents converge on a recommendation, validate that the convergence is on the *same true premise*, not on different agents accepting the same false premise. Three different reviews can produce three "APPROVE" verdicts on a wrong-because-built-on-fiction conclusion. Treat factual claims in source material (especially "structural invariant" or "X cannot happen because Y enforces it") as load-bearing — verify them empirically before letting them ride along on agent agreement.

**How to apply:** When writing a plan or amendment, identify which factual claims in the cited source are load-bearing for the conclusion. For each, ask: "Have we verified this claim empirically, or are we trusting it because session-N said so?" If the latter, run a verification step — read the underlying mechanism (settings.json schema, hook source, harness behavior across sessions). Cross-session diagnostics are gold for this: a different Claude session in a different project with different settings will exercise different code paths and surface what's actually load-bearing. Pair-watches with the 2026-04-25 entry "Verify Source-of-Truth Files Before Anchoring on Review Notes" — same lesson at the document layer, this entry extends it to the mechanism layer.

**Principle:** `meta-core-systemic-thinking` (root cause discipline — false premise is structural cause, not just per-finding noise); `meta-quality-verification-validation` (verify before action; review-note convergence is not verification); `meta-safety-transparent-limitations` (epistemic honesty about what's verified vs assumed).

**Cross-ref:** PROJECT-MEMORY.md ADR §8.3.4 amendment 2026-04-26; commit `f1ecd08`; pre-edit contrarian audit `adf19d07b51fc2f3b` (named the "agent convergence does not validate premises" insight directly); BACKLOG #140 close commit; cross-session diagnostics from stats4roi-python project (different settings.json + no project hook = empirical refutation of the harness-block claim).

---

### Don't Generalize Case-Specific Deviations as New Defaults (2026-04-26)

Session-133 v3.30.0 ai-instructions pin draft attempted PATCH-on-MINOR justified via "v2.9.1's alias-preserved subset pattern" — except v2.9.1 deviated for a MAJOR rename where alias preservation made the cross-doc effect non-breaking, while v3.30.0 is a *tightening* (Close newly required = v3.29.0-form briefs FAIL v3.30.0 validation, not subset). Contrarian HIGH-2 (`a8648ee322443f496`) caught the cargo-cult: case-specific deviations remain case-specific; the canonical MINOR-on-MINOR rule (BACKLOG #130 close, COMPLETION-CHECKLIST item 7c) re-applies until explicitly re-canonicalized. Re-bumped v2.9.2 → v2.10.0 + struck "subset" framing from both v3.30.0 and v2.10.0 changelog entries.

**Rule:** A precedent's deviation rationale is scope-bounded to that case. Don't treat one deviation as license for the next; confirm the canonical rule still applies on the *current* case's facts. The wrong question is "did someone deviate before?" The right question is "does the case-specific reason for the prior deviation apply HERE?"

**How to apply:** When citing a prior deviation as rationale for a current bump, name the prior case's specific justification and verify it applies to the present case. If it doesn't, follow the canonical rule and document why the prior deviation's reason doesn't transfer. Recursive application of `meta-core-systemic-thinking`: "address the structural cause" (the canonical rule) rather than "patch per-incident" (cite-the-deviation). Pair-watches with the 2026-04-25 entry "AI-Fabricated Authority Chains" — that entry is about misreading bundled citations; this entry is about over-generalizing valid case-specific reads.

**Principle:** `meta-core-systemic-thinking` (root cause is the rule, not the precedent); `meta-method-single-source-of-truth` (canonical home > Changelog precedent — same lesson 2026-04-25 entry shipped, applied here at the application layer not the citation layer); `coding-method-defer-vs-fix-now` (caught and folded inline before commit, not deferred).

**Cross-ref:** rules-of-procedure v3.30.0 + ai-instructions v2.10.0 changelog entries (the corrected versions); contrarian audit `a8648ee322443f496` HIGH-2; commit `75e75b9`; LEARNING-LOG 2026-04-25 "AI-Fabricated Authority Chains in Changelog Precedents" (parent rule about canonical-home discipline).

---

### Generalize Existing Principle Before Minting a New One (2026-04-26)

User proposed adding "Elegance Equation" as a new constitutional meta-principle. Initial contrarian-reviewer flagged 5 of 7 Admission Test FAILs and recommended decline. Continued dialogue surfaced that the contrarian (and I) had treated `meta-quality-effective-efficient-communication` as encoding the same concept generalized — but it was explicitly **scoped to communication only**. The user's actual gap was scope (rule doesn't bind on code/plans/reports), not concept. Reframe: not a new principle, but rename + rescope the existing one to "Effective & Efficient Outputs" with form-specific cross-references. Plus the Elegance Equation as a method (§16.7) for the comparison case. Result: principle count stays flat (ADR-15 alignment), real failure mode addressed, alias preserves backwards compat.

**Rule:** When a user proposes a new principle, run the Duplication Check decision tree first (`meta-method-the-duplication-check`). The "YES, partially → absorb / generalize existing" branch is structurally cleaner than minting parallel content. Test specifically: does an existing principle encode the *concept* but with artificial scope? If yes, generalize. The right question for the Admission Test Q1 (Coverage) is "does an existing rule BIND on this case?" — not "does an existing rule mention this concept?" Concept-mention without binding is a coverage gap.

**How to apply:** Before approving any new constitutional principle, list every existing principle that mentions the concept. For each, check whether its operational guidance binds on the proposed case. If a near-fit exists with artificial scope, propose rescoping (with alias-preserved rename) before proposing addition. The contrarian-reviewer is most useful when given the principle/method split as a hypothesis to pressure-test — running it on the original "add as principle" framing produced a FAIL but missed the rescope alternative.

**Q7 lesson within this lesson:** The user's proposed label was "Elegance Equation." Q7 (Semantic-Label Risk) flagged it (aesthetic-philosophical baggage the multiplicative formula doesn't enforce). The fix wasn't to drop the work — it was to rename the *method* to operational language ("Solution Comparison via Effectiveness × Efficiency Product") while preserving the source paper as a Reference Library citation. Q7 is a label question, not a content question; rename solves it without losing the contribution.

**Principle:** `meta-method-the-duplication-check` (decision tree governs this); `meta-core-systemic-thinking` (root cause was scope-of-binding gap, not missing-concept gap); `meta-quality-effective-efficient-outputs` (the renamed/rescoped principle this lesson produced); ADR-15 (consolidation philosophy preserved).

**Cross-ref:** `~/.claude/plans/this-is-back-and-tidy-crescent.md` (the plan that shipped this); v6.0.0 constitution amendment (originally planned and audit-logged as v5.0.0; bumped to v6.0.0 per pre-ExitPlanMode contrarian — see ADR-17); rules-of-procedure §16.7 (the method downstream); `reference-library/ai-coding/ref-ai-coding-collier-elegance-equation.md` (paper citation); contrarian-reviewer's `APPROVE_WITH_REQUIRED_CHANGES` verdict (8 modifications baked into plan before ship).

---

### Verify Source-of-Truth Files Before Anchoring on Review Notes (2026-04-25)

During Compliance Review #5 (Check 6b.2), the PHASE2_TRIGGERED marker had FIRED — cross-process total 11.5 GB vs. session-108 verified 4.0 GB. My initial cause-analysis claimed the baseline was still pre-Phase-2 (citing Review #4's note "Post-Phase-2 baseline capture still pending — deferred structural task"). I drafted a "rebase the baseline" recommendation and the user approved it ("Go with your recommendation"). **Then** I read `~/.context-engine/logs/phase0-baseline.txt` directly to do the rebase — and the file said: "POST-PHASE-2 BASELINE (2026-04-17, watcher at 9h49m uptime, pre-12h-restart) ... baseline_steady_mb=5800 ... # Trigger 3 (script constant) updated from 3072→7500." The recalibration HAD shipped (between Review #3 and Review #4). Review #4's "still pending" note staled out — the action shipped, the row didn't get updated. My recommendation was about to act on a wrong premise.

Caught the error before action; corrected the row + #49 status block + revised the recommendation (workload-variance hypothesis + 7-day monitor) before commit.

**Rule:** When a review note or status table claims an action is "deferred" or "pending," verify against the source-of-truth file (the actual config / baseline / measurement file the action would have written to) before anchoring on the note. Related-document notes can describe future intent but stale once the action ships if no one updates the note. The SOT file is the truth.

**Operational corollary:** when an automated forcing function fires (PHASE2_TRIGGERED, deny logs, etc.), read the underlying mechanism's SOT files BEFORE building a cause-and-action analysis around what other docs say about the mechanism's state. The mechanism's own state is authoritative.

**Why structural, not just personal:** review tables are a known stale-by-design artifact (they snapshot a moment + don't have CI-enforced freshness). Multiple docs encode the same underlying state. When they disagree, prefer the SOT. This is `meta-method-single-source-of-truth` applied to verification: there's one canonical home for "is this baseline calibrated?" — the baseline file. Everything else is a pointer.

---

### Auto-Defer to BACKLOG Is the AI's Default Failure Mode for Hard Calls (2026-04-25)

Session-128 mid-stream user pushback: *"No on sequential thinking defer. This is a bad habit of yours putting things off. This is not that hard."* Pattern: when given a multi-part judgment call (a/b/c question with the user's framing already supplied), AI reflexively classified one item — Sequential Thinking MCP placement — as "needs separate evaluation, file as BACKLOG" even though user had already supplied the deciding frame (80/20 + named precedent + "you're the AI-governance expert"). Defer-to-BACKLOG was presented internally as proportional rigor; was actually forward-continuation bias dressed up. Fix shipped inline (M.2 Sequential Thinking with verdict in body — *complements, does not conflict* with Plan Mode — NOT a follow-up BACKLOG to-evaluate item).

**Rule:** Before drafting "defer to BACKLOG / file as separate evaluation / circle back," check three conditions: (1) Did the user supply a deciding frame ("apply 80/20", "wrap it up", named precedent, "you're the expert")? (2) Does the verdict write itself in 1-2 sentences? (3) Is the candidate clearly best-of-best in its slot (Anthropic-official reference impl, this-project's existing precedent, named winner)? Any "yes" → ship the call inline. The 80/20 rule applies to the *defer decision itself*: most items I reflexively defer fail "is this an edge case that doesn't really matter or come up that often?" — they DO matter and they DO come up; the defer is just AI deferral, not user-protective rigor.

**How to apply:** Codified as feedback memory `feedback_decide_dont_defer.md` (saved 2026-04-25, indexed in `~/.claude/projects/-Users-jasoncollier-Developer-ai-governance-mcp/memory/MEMORY.md`). Cited inline in title-10 v2.43.0 Version History entry's Constitutional Basis as the rule that produced the verdict-shipped-inline outcome for M.2 Sequential Thinking. Anti-pattern explicitly named: *"Backlogging an edge case that doesn't really matter or come up that often"* — apply 80/20 to that classification, not just to the work. Per `coding-method-defer-vs-fix-now` (§7.11): defer is the table's third cell, not the default.

**Principle:** `meta-core-systemic-thinking` (defer-as-default IS the structural pattern; fix the disposition reflex, not per-item); `meta-core-discovery-before-commitment` Anchor Bias Mitigation (defer is the AI's anchor when uncertain — challenge it the same way other anchors are challenged); `coding-method-defer-vs-fix-now` (the framework rule the new feedback memory operationalizes); `meta-quality-effective-efficient-communication` (decide once, not "evaluate later → evaluate later → evaluate later").

**Cross-ref:** `~/.claude/projects/.../memory/feedback_decide_dont_defer.md`; title-10-cfr v2.43.0 Version History entry (Constitutional Basis bullet citing this rule); session-128 close commit `56a9dee`; the meta-loop (rule's first invocation was the very session that named it — the AI deferred Sequential Thinking, user caught it, the fix is the rule that prevents deferring next time).

---

### Codified Rules Need Structural Anti-Theater Gates Against AI Self-Application (2026-04-25)

Session-126 shipped §5.1.8 Mid-Execution Checkpoint Protocol (title-10 v2.42.0) explicitly naming "checkpoint theater" as an anti-pattern: re-reading the plan and declaring "no drift" without a delivered-vs-planned table. **On the rule's first invocation — by us, on the plan that codifies it — we performed exactly this anti-pattern.** The session-126 MIDPOINT CHECKPOINT entry was a single line: "DONE (session-126, between Commits 4 and 5). No drift; PROCEED to Commit 5." Post-ship contrarian battery (audit `a62e96c04a3f91721`) caught it. v2.42.1 PATCH (Commit 9) shipped the structural fix: §5.1.8 step 3 now REQUIRES a written delivered-vs-planned table; bare "no drift" assertions = "checkpoint did not happen." Step 4 external-evaluator pass promoted from optional to REQUIRED-when-step-3-flags-drift.

**Rule:** When codifying a rule whose anti-pattern is named, ship a structural gate that prevents the AI from performing the anti-pattern itself — not just an advisory naming. The author of the rule is the most-anchored party; "do not theater" without an artifact requirement collapses to vibes-on-first-use. Rules that name an anti-pattern but rely on the author noticing they're doing it = ~85% advisory ceiling, with the author specifically below that ceiling per anchor bias.

**How to apply:** Before approving a rule that names an anti-pattern, ask: "What's the structural artifact that proves the rule was followed (not just claimed)?" If the answer is "the author's good faith," ship a structural requirement (written table, named output file, lint check). Pair with a self-application check: would the author's first invocation produce the artifact, or would they short-circuit to assertion? If the latter, the rule is theater-prone.

**Principle:** `meta-core-systemic-thinking` (close the structural loop, not patch per-incident); `meta-quality-verification-validation` (written artifact = verifiable; bare assertion = unverifiable); `coding-process-validation-gates` ("validation requires evidence, not just declaration"); `meta-safety-transparent-limitations` (admit AI authors are anchored on their own rules' first use).

**Cross-ref:** title-10-cfr §5.1.8 step 3 v2.42.1; SESSION-STATE.md "Post-Hoc MIDPOINT CHECKPOINT Artifact" section (the dogfood: writes the artifact §5.1.8 just made REQUIRED, with honest provenance disclaimer); plan `~/.claude/plans/federated-plotting-karp.md` Commit 9 (`61b0058`); post-ship contrarian audit `a62e96c04a3f91721`.

---

### AI-Fabricated Authority Chains in Changelog Precedents (2026-04-25)

Session-126 BACKLOG #130 investigation: ai-instructions Changelog entries v2.8.1, v2.8.2, v2.8.3, v2.8.4 cited "session-121 canonicalization" as authority for PATCH-on-MINOR pin-discipline rule. Investigation (`git log` + commit reads) found: **session-121 actually canonicalized pin-sync MECHANICS** (BACKLOG #115 → COMPLETION-CHECKLIST item #7 body-header + pin sync), **not** semver direction. The semver-direction authority was round-2 contrarian HIGH-2 on test-suite-optimization plan (commit `c22e35c`), prescribing **MINOR-on-MINOR**. v2.8.0 entry bundled BOTH citations correctly; v2.8.1 author misread the bundle and cited the wrong authority for the wrong rule. v2.8.2-v2.8.4 inherited the misread, propagating the fabricated chain. v2.8.5 was correct (PATCH-on-PATCH, target was PATCH source) but for unrelated reasons. Each entry's author was reverse-engineering "what's the right pin discipline?" from prior Changelog precedents instead of from a canonical home.

**Rule:** Codify rules in canonical homes (a binding document section), not in Changelog precedents. A Changelog rationalization that cites another Changelog entry as authority is structurally dependent on the authoring sessions reading that entry correctly — and AI authors routinely misread bundled citations. When you find yourself writing "per [session-X canonicalization]" in a Changelog rationale, stop and ask: "where is the canonical rule? if it's not in a binding section, codify it there first, then cite the section."

**How to apply:** Before relying on a Changelog precedent for a future bump's rationale, locate the binding-section citation that precedent cites. If the precedent cites only other Changelog entries (or "session-X" without an audit-trailed authority), the chain may be fabricated — investigate the original commit + audit trail. Mitigation shipped: COMPLETION-CHECKLIST item 7c is now the canonical home for pin-discipline semver-direction rule; v2.8.6+ entries cite item 7c directly, not Changelog precedent.

**Principle:** `meta-method-single-source-of-truth` (rule has ONE canonical home; precedents reference it, not each other); `meta-quality-visible-reasoning-traceability` (citation must trace to an audit-trailed source, not "vibes from prior entries"); `meta-core-systemic-thinking` (the structural fix is canonical-home, not per-Changelog-entry correction).

**Cross-ref:** workflows/COMPLETION-CHECKLIST.md item 7c (canonical home, post-Commit 11); ai-instructions.md Changelog v2.8.1 [CORRECTION] note (the inline acknowledgment of the misread chain); BACKLOG #130 (closed Commit 11 `4762962`); commit `c22e35c` (the real round-2 contrarian HIGH-2 authority for MINOR-on-MINOR); plan `~/.claude/plans/federated-plotting-karp.md`.

---

### Open-Textured Exception Clauses Absorb Violations They Should Repel (2026-04-25)

Session-126 §7.12.1 v3.28.1 added a 5th exception "Research-anchored operational thresholds" so title-10 §5.1.8's `>30 min runtime` Agent Drift trigger could cite it directly (closes the by-analogy citation chain). Post-ship contrarian battery (audit `abd327fd5e8174348`) flagged the new exception text as **open-textured**: distinguishing terms ("process gate vs effort estimate", "the AI is producing") didn't draw a sharp line. Risk: when BACKLOG #131 sweep starts, an author could classify §3.1.2's `Estimate: 2-8 hours` as "research-anchored mode-selection process gate" and tag it scope-excluded under the new exception. **The exception just made #131 potentially unactionable.** v3.28.2 PATCH (Commit 13) shipped the structural fix: explicit anti-example (planning bands NOT covered) + distinguishing test (covered = external-paper citation with verbatim threshold value AND functions as automated trigger).

**Rule:** Tight scope carve-outs in rule clauses need (a) a positive example demonstrating coverage, (b) an explicit anti-example demonstrating non-coverage from the most-likely-confused class, AND (c) a distinguishing test that names the discriminating feature. Open-textured exceptions absorb exactly the violations they should repel — adopters reading the principle name + positive example without an anti-example default to "broad scope" interpretations.

**How to apply:** When authoring an exception/carve-out clause, before shipping ask: "What's the most-likely-confused class of OTHER rules that adopters might try to fit under this exception?" Name that class explicitly as anti-example. Add a 2-condition distinguishing test (e.g., "covered requires X AND Y; either alone is not enough"). Pre-edit contrarian-reviewer should check exception clauses for "what would an adopter wrongly include?"

**Principle:** `meta-method-single-source-of-truth` (boundary has one canonical home with anti-example, not adopter interpretation); `meta-quality-visible-reasoning-traceability` (distinguishing test makes the boundary verifiable); `meta-core-systemic-thinking` (close the structural ambiguity BEFORE downstream consumers inherit it, not patch case-by-case).

**Cross-ref:** rules-of-procedure §7.12.1 5th exception (v3.28.2 with anti-example + distinguishing test); BACKLOG #132 (closed Commit 12 `e6e7cca`); post-ship contrarian audit `abd327fd5e8174348`; plan Commit 13.

---

### AI Time Estimates Miscalibrate 50-100×; Use Effort Indicators Instead (2026-04-25)

User observation across multiple sessions: AI time estimates ("this will take 2-3 hours", "needs its own session", "M-tier ~30-60 min") routinely overrun ground truth by 50× to 100×. Pattern produces false-deferral — AI rationalizes putting off work because "it'll take too long," when ground-truth effort is actually small (file count low, no infrastructure, known patterns). Pre-edit Plan agent + contrarian-reviewer flagged my own plan v2 deferring 4 backlog items based on "M-tier" / "needs plan mode" reasoning that resolved to D1 (single-file extension of 234-line script) on inspection. Web research validates: Alaswad et al. "Toward LLM-aware software effort estimation" (Frontiers AI 2026) and Kahneman/Lovallo Reference-Class Forecasting (PMI 2026) both confirm AI/human inside-view estimation has <20% hit rate; observable-indicator + reference-class hybrid achieves 70-80%.

**Rule:** AI must not estimate future work in time units. Use observable effort indicators (file count, infrastructure changes, dependency count, D1/D2/D3 tier, token budget). When sizing a backlog item or scoping a session, name the *shape* of effort (surfaces, complexity tier, discovery depth), never the *duration*. Calibrate by tracking actual effort dimensions across completed tasks of the same class; recalibrate after every N completions per Reference-Class Forecasting.

**How to apply:** Before stating any time estimate, check: would this estimate be calendar/cadence (allowed), historical (allowed), timeout-value-in-code (allowed), or explicit user request (allowed)? If none, switch to effort indicators. Codified structurally as `meta-method-effort-not-time-estimation` (rules-of-procedure §7.12) + CLAUDE.md Behavioral Floor directive + tiers.json `behavioral_floor.directives` reinforcement + BACKLOG.md D1/D2/D3 cleanup (stripped time language).

**Principle:** `meta-safety-transparent-limitations` — if I'm bad at calibrating something, honest behavior is refusing to estimate. `meta-core-systemic-thinking` — root cause is calibration error, not "try harder." Structural rule prevents recurrence; advisory ("be careful with time estimates") would hit ~85% ceiling.

**Cross-ref:** rules-of-procedure §7.12 (canonical method); session-125 plan `~/.claude/plans/federated-plotting-karp.md` Commit 1 (`7e7ce95`); Alaswad et al. Frontiers AI 2026 Hybrid Intelligence Effort framework; Kahneman/Lovallo Reference-Class Forecasting (70-80% hit rate).

---

### Lead with BLUF for User-Facing Decision Briefs (2026-04-25)

User pushback after multiple long technical responses: "I need an executive brief that tells me what you are suggesting without the extra technical jargon like you might give a manager. What does each thing do, why is that important, and what do you recommend if there are more than one option on the table and why." Pattern: AI defaults to information-dumping (long-form, exhaustive, recommendation buried in section 4 of 6). Web research validates BLUF (Bottom Line Up Front) + Minto Pyramid Principle as 2026 best-in-class for decision briefs to non-specialist managers. Empirical sweet spot: 4-5 sections, 3-5 bullets per, 10-20 words per bullet, 2-3 alternatives max (Hick's Law — 4+ creates choice paralysis), risk embedded per option (not as separate dump), 300-500 words for 1-pager / 800-1200 for 2-pager.

**Rule:** When presenting a technical decision or analysis to a non-specialist technical manager, structure the response so the audience can decide effectively (understand the call) AND efficiently (no walls of text). Lead with 2-3 sentence BLUF stating the recommendation + key rationale. For each non-trivial option: state Why care / Impact / Risk / Recommendation+Source. Embed risk per option, not separately. Cap at 3 alternatives.

**How to apply:** Codified as `meta-method-bluf-pyramid-briefing` (rules-of-procedure §7.13) + CLAUDE.md Behavioral Floor directive + tiers.json `behavioral_floor.directives` reinforcement. Scope boundary excludes internal technical artifacts (plan files, ADRs, spec documents, audit logs) — those follow their own templates.

**Principle:** `meta-quality-effective-efficient-communication` (Article III §4) — operationalized as BLUF format. `meta-core-systemic-thinking` — fix the format structurally, not advisory "try to be concise."

**Cross-ref:** rules-of-procedure §7.13 (canonical method); session-125 plan Commit 1 (`7e7ce95`); Animalz on BLUF; BetterUp on Minto Pyramid; Laws of UX on Hick's Law; HBR 2026 "Trendslop" research; ACM CHI 2026 LLM Cognitive Biases.

---

### Verify Runtime Semantics Before Scoping a Test from BACKLOG Framing (2026-04-24)

BACKLOG #120 proposed a test for "nested Task" contrarian detection — premised on the assumption that a Plan sub-agent's internal `Task(contrarian-reviewer)` invocation surfaces in the root transcript. Pre-edit Plan-agent + contrarian review on the closure plan revealed the premise is wrong: Claude Code root transcripts contain only the top-level `Task` tool_use block; sub-agent internal tool calls live in their own transcript files. The actually-observable variant — a top-level Plan Task followed by a top-level contrarian Task with intervening filler — exercises only the `"contrarian" not in line` pre-filter at `.claude/hooks/scan_transcript.py:170`, which is already covered by `test_deny_when_prior_exit_plan_but_no_contrarian_after` (filler-skipped → deny) + `test_corrupt_jsonl_skipped_gracefully` (corrupt-lines-skipped → allow). Synthesizing a new test would assert already-covered behavior — green-on-day-one noise that would pass even if a real-world regression occurred. #120 closed as invalid-framing 2026-04-24; closure deliverable is this entry, not a new test.

**Rule:** Before scoping a test from a BACKLOG item, read the relevant runtime code (scanner, hook, parser) and identify the specific code path the test would exercise. If that path is already covered by ≥1 existing test, the new test is redundant — close the BACKLOG item via LEARNING-LOG (or by updating the original entry's framing) instead of synthesizing a passing-on-day-one assertion. Coverage gaps must be named at the line level, not the scenario level.

**How to apply:** When triaging a "add a test for X" BACKLOG item, the planning step is (1) read the runtime code path, (2) name the single line / branch / failure mode the test would exercise, (3) grep existing tests for coverage of that line / branch / failure mode. If no unique uncovered line surfaces in step 2, escalate to scope review before writing the test.

**Principle:** `meta-core-systemic-thinking` — close the item via the load-bearing lesson, not the ceremonial test. Also `meta-quality-verification-validation` — "the test exists" is not "the test asserts new behavior." Also extends LEARNING-LOG 2026-04-20 "Re-severity Review Findings Against Ground Truth Before Remediation Planning" — same Ground-Truth-before-execution discipline, applied to BACKLOG items rather than review findings.

**Cross-ref:** `.claude/hooks/scan_transcript.py:120-200` (`scan_contrarian_after_last_plan` function — the runtime code whose semantics drove this re-scoping). `tests/test_hooks.py::TestContrarianAfterLastPlan` (existing test class — 11 tests covering 5 distinct scanner branches; #120's proposed test would have been a 12th asserting branch already covered by tests #2 + #8).

---

### Registry Entries Must Be Binary-Checkable via Assertion Presence (2026-04-24)

Session-124 BACKLOG #121 sweep surfaced 4 advisory FMs that stayed at zero annotations for 1-4 months even after the seed-at-creation lint gate shipped. Root cause: 3 of 4 describe anti-pattern disciplines ("don't bypass validation" — FM-TEST-FULL-VALIDATION-CHAIN), known production limitations ("S-Series scanner triggers on negations" — FM-S-SERIES-KEYWORD-FALSE-POSITIVE), or authoring conventions ("patch at source for lazy-loaded models" — FM-ML-MODEL-MOCK-AT-SOURCE). None are binary-checkable: compliant tests just silently don't do the bad thing, with no positive assertion to annotate. The 4th (FM-TEST-ENVIRONMENT-AWARE) DID have a concrete mechanism — `@pytest.mark.slow` presence — and was annotated successfully. Contrast: FM-TEST-SIDE-EFFECTS (file-exists assertion), FM-TEST-ECHO-CHAMBER (threshold assertion) — all binary-checkable, all annotated. The 3 non-annotatable FMs were retired 2026-04-24.

**Rule:** Before adding an advisory FM, ask *"what specific assertion would fail if this FM's invariant broke?"* If the answer is "any test that doesn't do X" (anti-pattern), "fixing a known bug" (production limitation), or "tests that set up X this way" (authoring convention), the entry belongs in LEARNING-LOG / BACKLOG / reference-library — NOT the registry. The seed-at-creation lint gate (FM-REGISTRY-ADVISORY-SEED-AT-CREATION) catches missing-seed commits but can't catch category mismatches; this filter is the human complement. Codified in registry.md step 3 post-session-124.

### Bash ERR Trap Does Not Cover SIGKILL / Hook Timeout (2026-04-21)

BACKLOG #91 sub-item 3 asked what Claude Code does when a PreToolUse hook exceeds its configured `timeout` (10s in `.claude/settings.json` for the OOM-prevention gate). Official docs (code.claude.com/docs/en/hooks) confirm: **timeout is treated as non-blocking allow** (same semantics as `exit 1`), regardless of any ERR trap in the hook. Claude Code terminates the timed-out hook via SIGKILL, which bash CANNOT intercept — `trap ... ERR` only fires on command failures (errexit), not kernel-level process termination. Phase-1 research source quoted: *"For events that can block actions (like PreToolUse), a timeout is treated as a non-blocking error, so the tool call proceeds unless the hook actively returns a blocking decision before timing out."* Pre-edit 3-agent battery (Plan agent + contrarian) caught a correlation not obvious in the narrow "document semantics" framing: the gate's slowest step (`ps -ax`) runs slowest when the gate is MOST needed (memory pressure), so fail-open-on-timeout is positively correlated with the threat condition — making it a structural safety gap, not a theoretical concern.

**Rule:** For safety-critical hooks, `trap 'exit 2' ERR` is necessary but NOT sufficient. Every slow decision step must be wrapped with an internal `timeout N` guard (N < platform-configured hook timeout) so the hook exits 2 deliberately before the platform's kill-switch can fire. Fail-closed on timeout is a property of the hook's internal structure, not the platform's enforcement.

**How to apply:** For each slow step, wrap with `timeout $((HOOK_TIMEOUT - 3)) <command>`. On macOS without coreutils, fall back to `gtimeout` or unguarded (graceful degradation to pre-existing behavior). Detect timeout exit code (`124`) and convert to `exit 2` with a stderr diagnostic. Reference implementation: `.claude/hooks/pre-test-oom-gate.sh` (pattern established v2.38.3, session-121, 2026-04-21). **Canonical recipe:** `documents/title-10-ai-coding-cfr.md` §9.3.10 sub-subsection "Hook Implementation Prerequisites & Fail-Closed Recipe" (v2.38.4) — the 6-step recipe + platform prerequisites + testing pattern live there for adopter AI agents to retrieve via `query_governance`.

**Principle:** `meta-core-systemic-thinking` — the structural fix is time-bounded decision logic inside the hook, not a trap that cannot fire on SIGKILL. Also `meta-quality-verification-validation` — behavioral research closed the "unknown semantics" gap with authoritative docs. Also `meta-safety-transparent-limitations` — CFR correction is transparent about fail-open-on-timeout rather than implying unconditional fail-closed.

**Cross-ref:** LEARNING-LOG 2026-04-16 "Claude Code Hook Exit 1 = Fail-Open, Not Fail-Closed" covers the exit-code side of the same fail-open family. This entry covers the timeout side with a distinct actionable rule; neither alone captures the full fail-closed-conditional story. Cohort applies to all adopter-facing hook patterns, per §9.3.10 guidance.

---

### Heading-Based Audits Must Exclude Fenced Code Blocks (2026-04-20)

BACKLOG #105 was filed by a Cohort 4 Phase 4a coherence-audit (agent `a7ed2fe1124998854`) claiming `documents/title-30-storytelling-cfr.md` had duplicate version-history sections: `## Version History` at line 1028 + `## Changelog` at line 1982. Planning investigation found line 1028 is *inside* a ` ```markdown ` fenced code block opened at line 1025 and closed at line 1067 — an instructional template showing storytelling users what their own `REVISION-LOG.md` should look like. It renders as literal code text, not an H2 heading. The only real version-history section is `## Changelog` at line 1982. No duplicate existed. BACKLOG #105 closed as grep false positive; no file edits to title-30 CFR. Pre-edit 3-agent battery (contrarian `a678ce147ad6419ec` ACCEPT, coherence `aebedd54bb439db7d` COHERENT_WITH_ADDITIONAL_EDITS, validator `a18405166291ce50d` PASS_WITH_NOTES) convergent on the false-positive call.

**Rule:** Grep patterns like `^## Heading` will match inside ` ```markdown ` fenced blocks and produce false positives against documents that use fenced code as instructional template examples (CFRs with §12-style template sections, storytelling REVISION-LOG examples, etc.). Rendered markdown treats fenced content as literal text; source-layer grep conflates rendering and source.

**How to apply:** Heading-level audits should (a) strip fenced blocks before grepping, (b) use a multi-line-aware markdown parser, OR (c) scan backward from each grep hit to the nearest unmatched ` ``` ` fence delimiter — if an opener precedes without a closer, the hit is inside a code block; reclassify as non-finding. Coherence-auditor and validator agent prompts were amended in this commit to include the fence-check step (see `documents/agents/coherence-auditor.md` Step 4 + `documents/agents/validator.md` Step 1 Classify cross-ref). Note: naive "±N lines" backscans are unsafe — real code fences can exceed N (the title-30 REVISION-LOG fence is 42 lines); scan to unmatched delimiter, not a fixed window.

**Principle:** `meta-core-systemic-thinking` — fix the audit methodology (grep-over-source-layer), not the symptom (delete the "duplicate"). Also `meta-governance-continuous-learning-adaptation` (Art. IV §2) — capturing the methodology lesson so the same grep-fence pattern doesn't recur across future heading-level audits.

---

### Re-severity Review Findings Against Ground Truth Before Remediation Planning (2026-04-20) — GRADUATED from candidate (3 clean instances)

Review findings with "load-bearing" programmatic-consumer framing often collapse when Ground Truth is checked. Autoregressive forward-continuation bias makes it cheap to escalate findings during review and expensive to de-escalate them during remediation. Ground-Truth check at the planning gate is the cheapest intervention point.

**Three clean instances now on record:**

1. **Session-117 Cohort 4 Phase 4a F-P1-04 scope collapse.** Review's "200+ new fields needed" → Ground Truth: field already exists; only partial backfill (49/455 = 11%) with no consumer. Phase 4a reframed; Phase 4b deferred.
2. **Session-118 Cohort 4 Phase 4b F-P1-04 Q7 FAIL.** Planned 406-method `Implements:` backfill. Ground Truth: extractor (`src/ai_governance_mcp/extractor.py:1686-1699`) parses `Applies To` only — zero `Implements:` references in tests or code. F-P1-04 HIGH severity sized on presumed consumer that doesn't exist; collapses to MEDIUM-at-most. Deferred at BACKLOG #106 with Q7 remediation + consumer as hard prereqs.
3. **Session-119 BACKLOG #105.** Claimed duplicate version-history sections in title-30 CFR. Ground Truth: one of the "duplicates" is inside a ` ```markdown ` fenced code block (instructional template); not a real H2. Closed as grep false positive with no edits.

**Rule:** Before approving any plan to remediate a review finding, perform at least one of:
- (a) Grep the codebase for the presumed consumer (extractor regex, test references, query surface, CI hook).
- (b) Read the specific lines the finding references with full surrounding context (±10 lines minimum), not just grep snippets.
- (c) Verify the field/section/signal is actually parsed or enforced by code or agent behavior.

If Ground Truth contradicts the finding's framing, re-severity or close the finding *before* planning. Do not let severity rhetoric in the review text override the absence of operational evidence.

**How to apply:** At planning-stage-gate for any review-derived remediation, add a "Ground Truth verification" step that explicitly names the presumed consumer and checks it exists. Make this step blocking: no plan exits drafting without it.

**Principle:** `meta-core-systemic-thinking` — address presumed-consumer assumptions structurally, not after the remediation has consumed effort. Also `meta-safety-transparent-limitations` — re-severity based on evidence rather than carrying review framing forward unchecked. Also `meta-quality-verification-validation` — "finding severity claim" is not "operational evidence."

**Graduation trigger met:** 3 clean instances in 3 sessions. Pattern is canonical. Integration into `workflows/COMPLETION-CHECKLIST.md` review-triage step tracked at BACKLOG #114 (trigger: next review-methodology change OR Cohort-5+ plan drafting, whichever first).

---

### Review Protocol — Don't Count Principles Per Preamble Purpose (2026-04-19)

F-P2-13 in the 2026-04-18 self-review flagged "Relations purpose thinly operationalized — only 2 principles" as a Medium-severity finding. Cohort 3 planning rejected the framing: the review applied operative-claim logic (counting principles per purpose) to the Preamble, which is a class (b) interpretive-tiebreaker surface per LEARNING-LOG 2026-04-18 "Declaration and Preamble Are Purpose Surfaces." This is the same category error that produced F-P2-01 in Cohort 1 (evidence-checking an aspirational Declaration claim) — just at a different surface.

**Rule:** Review methodology must not flag Preamble purpose under-coverage as a finding based on principle-count alone. Preamble purposes operationalize through distributed coverage — multiple domain principles, methods, and cross-references contribute to any given purpose. Counting dedicated principles per purpose measures the wrong thing. Flag Preamble purpose gaps as findings ONLY when actual governance decisions are failing on that purpose (evidence-gated, not count-gated). Example: if contested interpretations on cross-domain output recognition (Relations) keep producing conflicts the framework can't resolve, THAT'S evidence of a Relations gap worth filing. "Relations has only 2 principles" is not.

**Rule corollary — F-P2-13 class for future reviews:** when a finding is "X purpose is thinly operationalized, add a principle," apply the textual-function classification gate first. If X is a Preamble purpose (class b), the finding must name a specific governance decision failure, not a count. Otherwise, it's reframed to "review methodology error" — same class as F-P2-01.

**Principle:** `meta-core-systemic-thinking` — fix the review protocol, not the content. Extends LEARNING-LOG 2026-04-18 "Declaration and Preamble Are Purpose Surfaces" with the corollary that Preamble purposes don't have per-purpose principle-count quotas. Also `meta-safety-transparent-limitations` — this lesson is transparent about a review methodology error; the fix is documented, not silently absorbed.

**BACKLOG #34 (Epistemic Integrity draft) disposition:** Parent plan swift-hopping-corbato bound F-P2-13 + F-P2-09 both to #34. Both resolved via Path B in Cohorts 2 and 3 respectively; neither produced an Epistemic Integrity gap requiring a new principle. #34 closes as resolved-in-place with cross-reference to the two Path B PROJECT-MEMORY entries.

---

### Post-Commit Double-Check Catches Surface Drift Pre/Post Batteries Miss (2026-04-19, EXTENDED 2026-04-23 with mechanism + session-123 confirmation, EXTENDED 2026-04-25 with session-126 5th instance + meta-pattern observation)

Cohort 2 v5.0.0 ran pre-edit + post-edit 3-agent batteries. Both passed. User requested an additional post-commit double-check with 3 more subagents. It found:

- **H1 (BLOCKING):** `rules-of-procedure.md:4370` `TITLE 15: REFERENCE LIBRARY (CASE LAW)` — the root section heading still carried the old label. Both batteries missed because they audited the *inline prose* (lines 4380/4387/4395) without looking at the section's `#` heading.
- **M1 (surface drift):** 6 CFR Legal System Analogy tables said "Informative artifacts from real application" — missing the `(non-overriding)` parenthetical that post-edit contrarian had added to constitution + ai-instructions for soft-binding protection. The fix was applied to 2 of 8 parallel surfaces. Batteries were scoped to specific named files, not "all parallel surfaces carrying the same claim."
- **M2 (same-file inconsistency):** `rules-of-procedure.md:2112` Truth Source Hierarchy row used pre-rename "precedent" wording while §15.1 in the SAME file used new wording.

**Rule:** For wide-propagation changes (label renames, claim updates with multiple surface instances), run a post-commit double-check whose specific brief is "audit surfaces NOT in the plan's propagation list + verify cross-surface consistency of any post-edit fixes." The double-check is 3 agents with distinct blind-spot coverage: (a) coherence on files outside original scope; (b) contrarian on internal consistency + hidden downstream consumers; (c) validator on runtime state. Different angle than pre/post-edit batteries, which are scoped to plan artifacts.

**Rule corollary for post-edit fixes:** when a post-edit battery finding produces a fix (e.g., "add `(non-overriding)` to Authority column"), apply the fix to ALL parallel surfaces immediately, not just the one the agent flagged. Batteries flag instances; drift accumulates when fixes are applied instance-wise instead of class-wise. The grep that catches the instance will catch the class if you run it.

**Principle:** `meta-method-single-source-of-truth` extended to "single-source-the-claim-text, not just the canonical source." Also `meta-core-systemic-thinking`: the root cause of M1 surface drift is that 8 parallel surfaces paraphrase the Authority text independently; a CI assertion that Authority-column strings match across the 6 CFR tables would prevent this class. Filed as BACKLOG candidate for structural remediation.

**Also extends LEARNING-LOG 2026-04-18 "Verify Cited Files in Reviews":** the v5.0.0 commit message itself claimed "20+ files" — actual was 11. Rhetorical inflation by a factor of ~2×. Double-check caught it; pre/post batteries focused on content didn't.

**2026-04-23 update — session-123 confirmation (4th instance) + MECHANISM IDENTIFIED.** Session-123 shipped Commit D (first-battery fixes) then Commit E (second-battery fixes); the second battery caught 2 HIGH (rot-immunity claim false, `must_cover` demotion ungated) + 4 MEDIUM the first battery missed despite a 10-minute gap. Internal pattern analysis across sessions 120/121/122/123 (~18 findings): 6 of ~10 dominant-category catches are cross-file propagation gaps (version pins, body-header drift, parallel-surface inconsistencies). Cross-referenced with external research (MIT 2025 position bias, ACM ICER 2025 rubric prompting, NeurIPS 2024 LLM-as-judge biases) confirms:

- **The mechanism is SCOPE ASYMMETRY, not time-gap or fresh-eyes.** Pre-battery reads the plan's propagation list (whitelist). Post-battery reads the whole repo for instances of the claim/pin/label class (grep-for-class). 10-minute gap isn't doing the work; scope rotation + agent-type rotation are.
- **Unavoidable residual ~10-20%** per LLM-as-judge literature (position bias, verbosity bias, same-model confabulation consensus); cannot drive post-battery catches to zero.
- **Compressible portion ~80%** addressable via: (a) rebriefing pre-battery coherence-auditor with explicit grep-for-class step (shipped session-123 as structural fix — anti-whitelist rule in `documents/agents/coherence-auditor.md` Step 4); (b) closing recurring classes at source (BACKLOG #115 pin-sync checklist, #123 CI regen enforcement, #124 demotion rationale gate).

**Graduated rule (session-123):** Pre-battery coherence-auditor prompt MUST include the anti-whitelist instruction — "the brief's file list is a starting point, NOT the scope; sweep the whole repo for every surface carrying this claim/pin/label class before concluding." Hash-locked via `TestMultiAgentConsistency::test_template_hashes_match_files` so the instruction can't silently regress.

**Target metric:** compress pre→post HIGH/BLOCKER catch delta from current ~30-50% of total shipping effort to <10% within 3 sessions post-ship.

**2026-04-25 update — session-126 5th instance + META-PATTERN.** Session-126 ran TWO post-ship contrarian batteries on the Superpowers plan + remediation arc; combined they caught 14 distinct findings that the pre-push batteries (also 3-agent, also fresh-context per commit) missed. Battery 1 (after Commits 2-8) found: checkpoint theater on the rule that codifies it (HIGH), fabricated-authority chain across 4 Changelog entries (HIGH), §1.3.5 ENHANCED-only under-calibration risk, V-007/V-008 human-memory failure mode, Pattern G missing failure-mode equivalence, SESSION-STATE staleness. Battery 2 (after remediation Commits 9-12) found: open-textured §7.12.1 5th exception (HIGH), 3 SESSION-STATE narrative-stale findings, ai-instructions v2.8.5 stale "until #130 ships" note, test-count baseline drift. The pre-push coherence-auditor on each individual commit ran Step 4 anti-whitelist sweep correctly; it caught the cross-file propagation drift IN-COMMIT. What it could NOT catch: the META-CLASS findings that emerge only when looking at the work in aggregate (does the rule apply to itself? does the chain of citations trace back to real authority? does the new exception accidentally absorb its own anti-pattern's class?). **The post-ship double-check's load-bearing role isn't catching what pre-push missed in the same scope; it's catching what is invisible at the per-commit scope but visible at the arc scope.**

**Refined rule (session-126):** Post-ship double-check on a multi-commit arc isn't redundant with per-commit pre-push batteries — it's checking a different scope. Per-commit pre-push checks "did this commit ship correctly per its plan?" Arc-level post-ship checks "do the shipped commits, considered together, exhibit a class of drift that no individual commit's review could see?" Both are required for rule-codification arcs (where the work IS the rules' first invocation). Schedule arc-level reviews after natural batch boundaries (plan close, 5-commit threshold, anti-pattern shipped that the work itself might exhibit).

**Cross-ref:** post-ship audits `a62e96c04a3f91721` (battery 1), `aa9558e699a8fd3d3` + `a44d19b0be2f3107c` + `abd327fd5e8174348` (battery 2); session-126 plan + remediation Commits 9-13.

---

### Pre-Edit Battery Is Cheaper Than Post-Edit Rework for Constitutional Amendments (2026-04-19)

Cohort 2 ran the 3-agent battery (contrarian-reviewer xhigh + coherence-auditor high + validator high) at BOTH plan-stage and post-edit-stage. Pre-edit battery surfaced three blockers: (1) contrarian steel-manned a Path-B alternative (de-duplicate-in-place) to the merge approach the v1 plan had adopted — pre-edit catch saved series-crossing + test breakage + cross-ref churn; (2) coherence found 7 propagation-list gaps (rules-of-procedure line misses, server.py:2052, README line 42 vs actual 60) — pre-edit catch meant the edit sweep was complete first pass; (3) contrarian flagged "Informative Only" as a downgrade — reworded to "Informative (non-overriding)" post-battery. Post-edit battery then caught one additional issue (§9.6.1 vs §9.6.3 citation) — surgical fix.

**Rule:** For constitutional amendments (or any amendment-workflow change with wide propagation), run the 3-agent battery at plan-stage AND post-edit-stage. `coding-method-three-agent-assessment-battery` mandates post-edit; extending to pre-edit is defense-in-depth. Cost is proportional: plan-stage battery catches issues when the edit surface is zero and iteration is cheap; post-edit battery catches issues when the edit is done but before commit. Skipping pre-edit concentrates all catch-and-fix into post-edit, which costs more because the edit may need substantial rework.

**Principle:** `meta-quality-verification-validation` extended to verification-before-edit, not just verification-of-edit. Also proportional rigor per `meta-methods §7.8`: the cost of a pre-edit battery (~30-50K tokens for 3 agents) is small compared to the cost of a post-edit re-work cycle on a 15-file propagation sweep. Graduated-pattern candidate after 2nd use.

---

### Structural Enforcement Is Cross-Cutting, Not a Hierarchy Row (2026-04-19)

F-P1-02 flagged that the declared 7-layer hierarchy omits the mechanisms that bind (hooks, CI, subagents, scaffold, Admission Test). Swift-hopping-corbato plan initially proposed adding an 8th row. Pre-edit systemic-thinking reframe rejected that: normative layers answer "what is the rule?" — enforcement mechanisms answer "how is the rule made sticky?" These are different questions; a hierarchy that conflates them hides the answer to either. US Constitutional analog preserves this distinction: Judicial/Executive branches are *mechanisms applied to* the sources of law, not sources themselves. Framework v5.0.0 added a "Structural Enforcement (Cross-Cutting)" subsection instead of a row. Post-edit contrarian + coherence + validator all PASS on the cross-cutting framing.

**Rule:** When a review flags "hierarchy missing X," check whether X is *content* (answers "what is the rule?") or *mechanism* (answers "how is it enforced?"). If mechanism, add a cross-cutting dimension, not a row. Conflating content with mechanism in one table hides the content-vs-mechanism distinction going forward. The "add a row" response is appropriate only when X is genuinely a new normative content layer.

**Principle:** `meta-core-systemic-thinking` — fix the factoring, not just the symptom. Extends LEARNING-LOG 2026-04-18 "Declaration and Preamble Are Purpose Surfaces" pattern: before applying a reflex fix (add row / evidence-check), classify the element correctly first.

---

### Verify Cited Files in Reviews (2026-04-18)

During the 12-step self-review, `05-remediation-plan.md:R-01` cited `staging/benchmark_ab_test.py` as an "outcome-benchmark skeleton" ready to wire up. Subsequent plan-drafting read the file and found it is a **BM25 template-metadata A/B test** — retrieval-quality family (same as `tests/benchmarks/baseline_*.json`), not governed-vs-unguided output quality. The R-01 recommendation was factually wrong because the reviewer named a file without reading it. Step 10 post-hoc miss-check did not catch this either (it only cross-checked LEARNING-LOG / PROJECT-MEMORY / BACKLOG for contradictions, not file-citation accuracy).

**Rule:** When a review cites a specific file as evidence or as a ready-to-use artifact, the miss-check protocol must include "read the cited file and verify it matches the claim." Name-matching alone is unreliable (`benchmark` matched the claim; the file's actual purpose did not). Add to Step 10 miss-check: for each cited artifact, confirm the claim matches the artifact's content, not just its filename.

**Principle:** `meta-quality-verification-validation` — "cited file exists" is not "cited file says what I claim." Also `meta-safety-transparent-limitations`: a review that misidentifies evidence undermines its own recommendations and must log the correction transparently (captured in `~/.claude/plans/swift-hopping-corbato.md` Notes #4 and referenced here so future reviewers know the pattern).

---

### Declaration and Preamble Are Purpose Surfaces, Not Claim Surfaces (2026-04-18)

During the Cohort 1 self-review remediation, F-P2-01 ("Declaration's value-proposition claim is unfalsifiable") was filed against `constitution.md:38` and triggered a battery of proposed edits. User review rejected the diagnosis: the Declaration's text ("I wanted what I think everyone who works with AI wants — consistent, reliable results") is a purpose statement in the author's voice, structurally analogous to the US Declaration of Independence. Purposes are not assertions. Evidence-checks and Admission Test Q4 do not apply. No edit needed. The same protection extends to the Preamble (`constitution.md:56-62`), which functions like the US Constitution Preamble — AI-first operative surface (invoked at Admission Test borderline decisions per `constitution.md:80`), human-second contextual reading. The Supreme Court analog — *Jacobson v. Massachusetts* uses the US Preamble as interpretive tiebreaker, not freestanding authority — already documented at PROJECT-MEMORY 2026-04-12 "Preamble as Interpretive Tiebreaker." F-P2-01's scope error: it applied an operative-claim evidence-check to both contextual surfaces, mistaking aspirational purpose for asserted outcome.

**Rule:** Before running an evidence-check, Admission Test Q4, or falsifiability-pressure on any framework text, classify its textual function: (a) Declaration / aspirational purpose in human voice — purposes are not assertions; evidence-check does not apply; (b) Preamble / distilled binding purpose for AI interpretive use — same protection as (a); informs tiebreaker decisions but does not carry operative-claim weight; (c) README / runtime / CFR / product-facing declarative text — operative claim surface; evidence-check applies. Real F-P2-01-class problems live in (c). When Declaration or Preamble get pattern-matched into (c), the review has made a category error. Fix the review classification before fixing the text.

**Principle:** `meta-core-systemic-thinking` — the root cause was misapplied check, not deficient Declaration. Extends LEARNING-LOG 2026-04-12 "Metaphor-Driven Classification" pattern: check *textual function* before applying *content tests*, just as that earlier lesson teaches to check *operational criteria* before applying *classification labels*. Also scopes `meta-safety-transparent-limitations`: purposes don't need measurement; claims do.

---

### Dual 300s Defaults — Same Cadence on Both Sides of a Connection (2026-04-18) — CORRECTS prior session-112 diagnosis

Session-112 applied `server.requestTimeout = 0` to Happy's bundle under the hypothesis that Node's default 300000 ms server-side `requestTimeout` was killing the SSE stream. Session-113 verified the patch was on disk ~23h before the current wrapper process started, then observed drops STILL occurring at N × 300s on that patched wrapper. Real cause: **client-side undici `bodyTimeout`** (default 300000 ms) firing on an SSE stream the MCP SDK's `WebStandardStreamableHTTPServerTransport` never keeps alive (no heartbeat emission, grep-confirmed). Two 300s timers, opposite sides of the connection, identical observed cadence — we localized to the wrong one. Patch reverted 2026-04-18; bundles back to vanilla.

**Rule:** When a client/server protocol has the same-valued default timeout on both sides (300000 ms is common — Node `http.Server.requestTimeout`, undici `bodyTimeout`, many HTTP proxies), observed cadence alone cannot disambiguate. File-level patch verification (`mtime < wrapper_start`) is necessary but not sufficient — it confirms the file was modified, not that the fix works. Always behaviorally verify post-activation: observe at least one full timeout interval on the patched process and confirm absence of the drop. If drops persist, the timer is elsewhere (other side of the connection, a different timer, or in library code).

**Principle:** `meta-quality-verification-validation` — "did the patch change observable behavior?" is the only question that closes a fix-verification loop; file edit confirmation is not behavioral verification. Also `meta-safety-transparent-limitations` — the session-112 LEARNING-LOG entries below were written in advance of behavioral verification and were factually wrong about root cause. They are corrected here and in `staging/happy-requesttimeout-2026-04-17.md` (primary investigation record). Graduated-pattern candidate if a 3rd instance of same-value dual-timer mis-localization appears.

---

### Patching a File Does Not Patch the Running Process (2026-04-17)

Applied `server.requestTimeout = 0` to Happy's on-disk bundle during session 112 to fix a verified 5-min MCP SSE drop. Restarted the Happy *daemon* to activate the patch. Drops continued. `lsof` showed the MCP port 60772 was hosted by the per-session `happy` *wrapper* process (PID 93357, parent chain `happy` CLI → `dist/index.mjs`), NOT the daemon (separate process tree entirely, PID 92038 → 99688). The wrapper had loaded the bundle into memory at its own startup, before the patch existed. Daemon restart was irrelevant — only ending the Claude Code session and re-invoking `happy` would reload the patched bundle.

**Rule:** Before restarting "the" process to activate a file patch, verify *which* process hosts the code path under test. `lsof -nP -iTCP:<port>` and `ps -o pid,ppid,command` localize the actual owner. Restarting the wrong process produces a false-negative verification. Corollary: for an Node.js/Electron tool with a CLI wrapper + daemon split, the wrapper is almost always a long-lived parent of the current terminal session and cannot be restarted without ending that session.

**Principle:** `meta-core-systemic-thinking` — the assumed causal chain (edit file → restart daemon → new code runs) had a hidden link (which process loads the file?) that wasn't verified before acting. Symptom-level thinking (drops continue → patch must not work) would have led to reverting the patch. Structural check (which PID owns the port?) revealed the patch is correct but the activation step was wrong. Graduated-pattern candidate after 2nd use.

---

### Localize an MCP Disconnect by Cross-Server Drop Comparison (2026-04-17)

Observed recurring 5-min SSE drops on the Happy MCP transport. Initial instinct was to blame Claude Code CLI's transport layer. The structural diagnostic: counted "connection dropped" events across all 7 MCP servers wired into the same CLI (happy=888, every other server=0). Same CLI, same window → CLI ruled out, cause is happy-local. Verified further: Happy wraps `http.createServer()` with no `server.requestTimeout` override; Node 22 default is exactly 300000 ms (Slowloris mitigation). Matched drop cadence precisely.

**Rule:** When a single tool exhibits a recurring timing-based failure through a shared client (MCP CLI, shell, proxy), count the same failure signature across siblings of that tool before blaming the client. If N=0 on siblings and N>>0 on suspect, the cause is local to suspect. Advisory "check logs" without this comparison has ~50% false-target rate on client-vs-server localization.

**Principle:** `meta-core-systemic-thinking` — the symptom ("my session keeps dropping") is observed at the CLI, but the cause could live anywhere in the stack. Cross-sibling comparison is the structural diagnostic that localizes the cause in one shot instead of recursively chasing logs at each layer. Graduated-pattern candidate after 2nd use.

**Correction (2026-04-18, session 113):** The cross-server drop count (happy=888, every other MCP=0) localized the cause to Happy *specifically*, but the siblings being compared (context-engine, ai-governance) are **stdio** transport — no HTTP, no SSE, no undici `bodyTimeout` exposure at all. The comparison actually proved "HTTP-SSE MCP transport without heartbeat has this issue on this CLI," NOT "Happy's application code has this issue." Refined rule: before trusting cross-sibling drop comparison for localization, confirm siblings share the same transport/IO path as the suspect. If only the suspect uses HTTP/SSE and siblings are stdio, N=0 on siblings cannot rule out the shared HTTP library (undici, MCP SDK transport); it can only rule out portions above the HTTP layer (CLI application logic). The localization still pointed correctly at "this transport path is problematic" — it just narrowed to Happy when Happy was merely the only instance of that path.

---

### Thresholds Are Signal Detectors, Not Count Gates (2026-04-17)

CFR §A.5.5 set a fixed 50-entry trigger for permission-list review. Across two consecutive compliance reviews, it fired on legitimate growth (new MCP tools, new memory-file Edit/Write rules) with the same "category-legitimate, not accretion" disposition. The threshold was measuring the wrong thing: entry count is a proxy for accretion, but proxies drift as the ecosystem grows. Fix (v2.38.1): `post_cleanup_baseline + 20` — relative to the last-reviewed legitimate state, resets after each cleanup. Added one-shots-found as a second-order signal to distinguish calibrated baseline from contaminated baseline.

**Rule:** When designing any numeric threshold, specify the signal it is meant to detect (not just the unit it counts). If the signal is drift from a moving reference (usage, baseline, ecosystem state), make the threshold relative to that reference and re-baseline after corrective action. Static thresholds on moving targets produce false positives that erode signal-to-noise until the threshold is ignored.

**Principle:** `meta-core-systemic-thinking` — the recurring "over threshold, not accretion" disposition was a symptom that the threshold and the phenomenon had decoupled; fixing the count (pruning to get under 50) would have been a patch. Borrowed structural pattern: multi-agent §6.4 (Autonomous Drift Monitoring) + multimodal-rag §6.3 (Drift Detection) — both establish baseline, detect delta, re-baseline after intervention.

---

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

### Code Review Advisory Framing Prevents Both Rubber-Stamping and Dismissal (2026-02-28) — ACTIVE

Applied the new advisory framing to evaluate the code-reviewer's findings on our own changes. Of 6 findings: accepted 2 (H1 ValueError fix, H2 mixed mode tests — genuine gaps), rejected 2 (M2 CLAUDE.md pointers — intentional removal, M4 debug inconsistency — acceptable). Ratio: 33% accept, 33% reject, 33% not applicable. The structured evaluation table forced explicit reasoning for each decision rather than blanket acceptance.

**Rule:** When receiving subagent findings, use the structured evaluation table (Finding | Agree/Modify/Reject | Reasoning). The exercise of writing a reason for each decision is more valuable than the table itself — it prevents both "implement everything" and "dismiss everything" failure modes.

---

### Multi-Path Methods Must Handle All Paths Uniformly (2026-02-28) — ACTIVE

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

### __file__-Based Paths Break in Docker Non-Editable Installs (2026-02-19) — ACTIVE

`_validate_log_path()` used `Path(__file__).parent.parent.parent` to find project root. Inside Docker with `pip install .` (non-editable), `__file__` resolves to site-packages (`/usr/local/lib/...`), not `/app`. Log writes to `/app/logs/` were rejected as "outside boundaries." Meanwhile, `config.py` already had a CWD-based `_find_project_root()` that worked correctly.

**Rule:** Never use `__file__`-based path traversal to find the project root in code that runs inside Docker containers with non-editable installs. Use CWD-based detection or env vars instead. When multiple modules need the project root, reuse the canonical function rather than reimplementing.

---

### Advisory Governance Instructions Are Probabilistic, Not Deterministic (2026-02-16) — CRITICAL — PARTIALLY GRADUATED

Research confirmed with hard data: AI models follow system prompt instructions 85-92% of the time on SHORT, SINGLE-TURN prompts (IFEval). In multi-turn conversations, performance degrades ~39% on average (Microsoft Research, 200K+ conversations). Anthropic's own data shows Opus 4 tool selection accuracy is **49% baseline** with large tool libraries (improving to 88% with mitigations). Models skip governance calls when they don't perceive a concern, prefer internal knowledge over tools, and silently abstain rather than calling incorrectly.

**Rule:** Never rely solely on MCP server instructions or CLAUDE.md for governance compliance. Structural enforcement (Claude Code hooks, MCP proxies) must complement advisory instructions. The model WILL skip governance calls — the question is how often, not whether. See ADR-13. Key references: anthropic.com/engineering/advanced-tool-use, arxiv.org/abs/2505.06120, research.trychroma.com/context-rot.

**Graduated (2026-02-28):** Hard-mode hooks implemented — PreToolUse blocks non-compliant tool calls. Still active because MCP proxy (cross-platform) enforcement is not yet built (Backlog #1 Part B).

---

### Passive MCP Instructions Don't Drive Tool Usage (2026-02-14) — ACTIVE

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

**Resolved 2026-05-01 (BACKLOG #129 close):** Sentence-level safe-context allowlist shipped in `_detect_safety_concerns` (`server.py::_is_keyword_in_safe_context`). FM-S-SERIES-KEYWORD-FALSE-POSITIVE re-registered with `must_cover: true` and 9 new tests covering negation-context, meta-description, multi-word CRITICAL keywords, em-dash separation, partial-wrap per-sentence rule, imperative-action override (bypass guard), and per-field call (no leader-bridging across `planned_action` / `context` / `concerns`). The original rule about avoiding safety-adjacent keywords in negation phrases is **no longer required** for the keyword scanner path. **Rule retained for Path B** (semantic retrieval FP — `meta-safety-transparent-limitations` matches housekeeping action text on rule-citation language) until that fix ships — see new BACKLOG entry filed in same commit. Three contrarian rounds during plan mode (`a9b708b023588ef2f`, `a044f06182de62945`, `acac60285fe89885d`) iteratively surfaced and folded multi-word-keyword bug, allowlist breadth gap, sentence-boundary evasion, field-bridging, and audit-trail dedup. n=6 governance trips during plan-mode authoring (sessions 111/114/121/142/142/142) confirm proactive-class scope per `rules-of-procedure §7.8.1`.

---

### Version Validator Has Blind Spots — Title and Footer Not Checked (2026-02-21) — ACTIVE

`validate_version_consistency()` only searches `content[:2000]` for the pattern `Version:? X.Y.Z`. Document titles (e.g., `# Framework v2.0.0`) use a different format that the regex doesn't match. Footers (e.g., `*Version 2.0.0*`) are beyond the 2000-char window. Both went stale when content was updated to v2.1.0 in-place without renaming files.

**Rule:** When updating document content versions in-place (per "Governance Docs In-Place" decision), manually update title, footer, and cross-reference version numbers. The automated validator won't catch these.

---

### Specification Documents Are Not Validated Requirements (2025-12-24) — CRITICAL — ACTIVE

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
