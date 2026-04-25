# Post-Change Completion Checklist

> This checklist is a precursor to a structured workflow definition. It lives in `workflows/` as part of the AI-Optimized Project Structure standard.

Per §5.1.6, run this project's completion sequence after changes. Say "run the completion sequence" to trigger.

> **Enforcement Tiers:** Items marked ENFORCED are backed by hooks, CI, or structural gates —
> non-compliance is physically blocked. Items marked BEST-EFFORT are advisory with ~85% expected
> compliance. Occasional misses on best-effort items are acceptable; misses on enforced items
> indicate a system failure. Per LEARNING-LOG: "advisory fails at 87%; structural blocking
> achieves near-100%." (See: normative drift under agentic pressure, arxiv 2603.14975)

## Code changes

### ENFORCED (structurally blocked if skipped)

1. **Tests run before push** — pre-push quality gate hook blocks `git push` if `pytest` not found in session transcript
2. **Subagent review for risky changes** — pre-push quality gate hook blocks push if core code changed without code-reviewer or security-auditor invocation:
   - New MCP tool or handler → code-reviewer + security-auditor
   - Changes to server.py, extractor.py, retrieval.py, config.py → code-reviewer
   - New file-handling code path → security-auditor
   - Content expansion (new principles/methods) → coherence-auditor + validator
   - Changes >5 files → code-reviewer
   - See §5.1.7 for full trigger table
3. **Subagent review for governance content changes** — pre-push quality gate blocks push if governance principle files changed without contrarian-reviewer, coherence-auditor, or validator invocation:
   - Constitution: `constitution.md`
   - Domain principles: `title-*-*.md`
4. **Principle count ceiling** — `TestPrincipleCountCeiling` CI assertion fails if any domain exceeds 35 principles (consolidation pass Part 9.8.5 required before adding more)
5. **Governance evaluation before file modifications** — PreToolUse governance hook blocks Bash|Edit|Write until `evaluate_governance()` called
6. **Context Engine query before code changes** — PreToolUse governance hook blocks until `query_project()` called
7. **CI passes** — GitHub branch protection (when configured)
8. **README tool count matches actual** — `TestReadmePropagation` CI assertion
9. **New code path security check** (if adding code that reads files, parses external data, or handles user-controlled input) — enforced via pre-push requirement for security-auditor invocation on new src files:
    - [ ] Is the new code path included in `validate_content_security()` scan? (extractor.py)
    - [ ] Does it validate/sanitize file paths? (symlink protection, path traversal, size limits)
    - [ ] Does it use safe parsing? (`yaml.safe_load()`, not `yaml.load()`; `json.loads()`, not `eval()`)
    - [ ] Does it have dedicated tests? (NOT just passing through existing tests)
    - [ ] If it returns content to AI clients, is the content scanned for prompt injection?
10. **Completion checklist consulted** — pre-push quality gate blocks push if COMPLETION-CHECKLIST.md was not read during the session. The meta-action of opening the checklist is ENFORCED; individual items within remain BEST-EFFORT (~85%)

### BEST-EFFORT (advisory, ~85% compliance expected)

11. Tests written WITH implementation, not after (§5.2.2 — TDD recommended). Follow `workflows/TEST-AUTHORING-CHECKLIST.md` — name the failure mode, check `documents/failure-mode-registry.md` for existing entry, add `Covers: FM-<id>` to test docstring if applicable. Regenerate derived map (`python3 scripts/generate-test-failure-map.py`) if registry entries added/retired. **When adding a NEW registry entry** (advisory or must_cover), include ≥1 seeded `Covers:` annotation in the same commit — enforced structurally by `TestFailureModeCoverage::test_new_advisory_entries_have_annotation` for advisory entries introduced ≥ 2026-04-24.
12. SESSION-STATE updated progressively during session, not just at end (§7.1)
13. Benchmark baseline captured before index/retrieval changes
14. README/SPEC/ARCH propagation for domain counts, file trees, version references
15. Docker rebuild if `src/`, `pyproject.toml`, or `Dockerfile` changed
16. **New hook authoring** — when adding a new `.claude/hooks/*.sh`:
    1. Register matcher in `.claude/settings.json`.
    2. Author test file(s) in `tests/` following `tests/test_pre_test_oom_gate_hook.py` pattern.
    3. Add row AND narrative prose block to CFR §9.3.10 Layered Enforcement Stack (not just the table).
    4. If the hook enforces a behavioral rule, add paired directive to CLAUDE.md Behavioral Floor + `documents/tiers.json` `behavioral_floor.directives`.
    5. Follow CFR §9.3.10 Hook Implementation Prerequisites recipe (ERR trap + platform timeout detection + escape hatches + self-diagnosing fallback).
    6. If the hook affects adopter-facing governance OR takes >3 sessions to remediate, file a V-series verification item in `workflows/COMPLIANCE-REVIEW.md` measuring whether the enforcement changes behavior or just blocks it.

### ALWAYS (regardless of enforcement tier)

17. Update and prune SESSION-STATE.md (version, counts, summary; remove old session summaries; target <300 lines per §7.0.4) — at minimum at session end
18. Run **Branch Completion** below — pick A / B / C / D / E based on whether work is complete and whether human review is required.

## Content changes (governance documents)

### BEFORE PLANNING (review-triage)

> Applies when the change is being done in response to a review finding (self-review, subagent review, external audit). Skip if the change is user-initiated or responding to a direct observation.

0. **Ground-Truth verification** — Before approving remediation for any review-derived finding, verify the finding's presumed consumer actually exists. At least one of:
   - (a) Grep the codebase for the presumed consumer (extractor regex, test references, query surface, CI hook).
   - (b) Read the specific lines the finding references with ±10 lines surrounding context (not just grep snippets).
   - (c) Verify the field/section/signal is actually parsed or enforced by code or agent behavior.

   If Ground Truth contradicts the finding's framing, re-severity or close the finding **before** planning remediation. Do not let severity rhetoric in the review text override the absence of operational evidence. Rationale + 3 precedent instances: LEARNING-LOG 2026-04-20 "Re-severity Review Findings Against Ground Truth Before Remediation Planning."

### ENFORCED

1. `python -m ai_governance_mcp.extractor` — rebuild index
2. `pytest tests/ -v` — full test suite

### BEST-EFFORT

3. Spot-check: `query_governance("new content topic")` → verify it surfaces
4. Reference doc staleness check per §14.2
5. README check: if principle/method counts or domains changed → update README domain table
6. **Version-history entry authored** per `rules-of-procedure §2.1.1` Step 3 — every normative document MUST have a version-history section (Historical Amendments / Version History / Changelog / Appendix C naming all accepted); add an entry for this PATCH/MINOR/MAJOR.
7. **CFR version bump — four-surface sync** — when bumping a CFR frontmatter `version`, update all four surfaces together before commit:
   - (a) body-header `**Version:**` + `**Effective Date:**` lines in the same CFR
   - (b) `documents/ai-instructions.md` `<document_versions>` pin for that CFR
   - (c) `documents/ai-instructions.md` frontmatter + body header + Changelog entry (pin update triggers ai-instructions PATCH bump)
   - (d) `SESSION-STATE.md` Quick Reference Content row

   Catches the recurring pin-lag / body-header drift class documented across ai-instructions Changelog v2.7.1/v2.7.2/v2.7.3/v2.7.4. Verify with `grep -n "v2\.[0-9]" documents/<cfr> documents/ai-instructions.md SESSION-STATE.md` before commit — all four surfaces should show the new version.
8. **Audit-ID citation** per `rules-of-procedure §2.1.1` Notes — if the amendment references a governance consultation, cite the `audit_id` (e.g., `gov-abc123`) that authorized the change. Forward-going from 2026-04-19; historical entries grandfathered.
9. Update and prune SESSION-STATE.md (target <300 lines per §7.0.4)
10. Docker check: if content significantly changed or code also changed → rebuild and push
11. Run **Branch Completion** below.

## Domain changes (adding/removing/renaming domains)

> **Renames change principle ID prefixes** — this is a breaking change.
> Downstream consumers keyed on IDs (tiers.json, benchmarks, feedback logs) will break.
> Prefer add-then-deprecate over in-place rename.
> If rename is necessary, update tiers.json, benchmarks, and feedback logs to use the new prefix before deploying.

> **`TestDomainConsistency` catches source-of-truth and enum/prefix consistency (items 1-5) at CI time.**
> Items 6-20 require manual verification.

**Source of truth:**
1. Update `documents/domains.json` (name, display_name, files, description, priority)

**Code surfaces:**
2. `src/ai_governance_mcp/config.py` — `_default_domains()` fallback
3. `src/ai_governance_mcp/server.py` — tool schema enums (`query_governance` + `get_domain_summary`)
4. `src/ai_governance_mcp/server.py` — handler-level `valid_domains` sets (separate from enums)
5. `src/ai_governance_mcp/extractor.py` — `DOMAIN_PREFIXES` class constant
6. `src/ai_governance_mcp/extractor.py` — `CATEGORY_SERIES_MAP` entries for new domain's categories
7. `src/ai_governance_mcp/extractor.py` — `is_series_header` keyword list in `_extract_principles_from_domain()` (if domain uses series headers)
8. `src/ai_governance_mcp/extractor.py` — `category_mapping` dict in `_get_category_from_section()` (if domain has category keywords). **IMPORTANT: Check for substring collisions** — longer series names MUST come before shorter ones in dict insertion order (e.g., `ka-series` before `a-series`). See Gotcha #33 in PROJECT-MEMORY.md.

**Test surfaces:**
9. `tests/test_config.py` — `TestDefaultDomains` count and name list
10. `tests/test_extractor.py` — `TestGetDomainPrefix` for new domain
11. `tests/test_extractor.py` — `TestCategorySeriesMap` assertions for new domain
12. `tests/test_server.py` — domain integration test class (follow `TestUiUxDomainIntegration`)
13. `tests/benchmarks/retrieval_quality.json` — benchmark queries for new domain

**Documentation:**
14. `SPECIFICATION.md` — domain count and table
15. `ARCHITECTURE.md` — domain count references and benchmark methodology
16. `README.md` — footer domain list
17. `PROJECT-MEMORY.md` — domain decisions section

**Verification:**
18. `python -m ai_governance_mcp.extractor` — rebuild index
19. Spot-check: verify new domain principles have correct `series_code` values (not null) in index
20. `pytest tests/ -v` — full test suite (includes `TestDomainConsistency`)
21. Update `SESSION-STATE.md` domain count

## Principle changes (adding/modifying constitutional or domain principles)

> **Per Systemic Thinking (Constitution):** Before adding a new principle, verify the frame.
> A new principle is justified only when an actual behavioral gap exists that existing principles
> and methods cannot cover. If the gap is discoverability (how principles relate to each other),
> the fix is cross-references, not a new principle. If the gap is enforcement (principles exist
> but aren't applied), the fix is hooks/enforcement, not more principles.

> **Structural enforcement:** The pre-push quality gate requires subagent review
> (contrarian-reviewer, coherence-auditor, or validator) for governance principle file
> changes. The CI principle count ceiling (35/domain) catches accretion. The checklist
> below remains BEST-EFFORT for *which* checks to run and *what* to verify, but pushing
> principle changes without *any* review is now structurally blocked.

### BEST-EFFORT (advisory)

**Before writing the principle (see Part 9.8 Content Quality Framework for full procedure):**
1. **Admission Test (§9.8.1):** Pass all 7 questions — coverage, placement, derivation, evidence, enforceability, stability, semantic-label risk. (Preamble purposes serve as interpretive tiebreaker on borderline questions, not a standalone gate.)
   - [ ] New principle file uses canonical field name "Constitutional Basis" (not "Constitutional Derivation" — v3.26.8 alias row removed in v3.27.0 after title-40 sweep normalized variant usage).
2. **Duplication Check (§9.8.2):** Query `query_governance()` and `query_project()` — does something already cover this at any level?
3. **Structural Requirements (§9.8.3):** Use the correct template for the content type.
4. **Concept Loss Prevention (§9.8.6):** If modifying/removing existing content, verify every concept has a home.

**After writing the principle:**
6. **S-Series compliance check:** Does the new/modified principle comply with all S-Series (safety) principles? Amendments that weaken safety constraints require heightened scrutiny: contrarian review + coherence audit + human sign-off.
7. **Contrarian review:** Mandatory for constitutional amendments. Apply the principle to its own creation — does it pass its own tests?
8. **Coherence audit:** Template compliance, voice consistency, legal analogy fits framework pattern, no contradictions with existing principles.
9. **Federal preemption cleanup:** If the new principle covers ground already partially stated in domain methods, add references up and trim duplication. Use Context Engine to find all scattered references.
10. **Version propagation:** Update `version` and `effective_date` in YAML frontmatter. Add version history entry.
11. **Index rebuild + spot-check:** `python -m ai_governance_mcp.extractor`, then verify the principle surfaces via `query_governance`.

## Plan-mode architecture decisions

> **Schema enforcement via template:** Advisory checklists are skipped ~15% of the time due to
> autoregressive forward-continuation bias (LEARNING-LOG 2026-03-28). The plan template addresses
> this structurally: required sections before the recommended approach make verification part of
> the generation flow rather than an optional interruption.

For architecture decisions, use the plan template at **`.claude/plan-template.md`**. The template puts contrarian review, research verification, and simpler-alternatives evaluation BEFORE the recommended approach — making them part of the forward generation path, not afterthoughts.

**Origin:** CE Phase 4 planning skipped contrarian review and research, leading to a plan that would have built RRF + cross-encoder reranking to fix a benchmark specification error. The contrarian then caught the original fix (rewriting 9 advisory sections) as itself being the Shifting the Burden pattern — better advisory language when the fix should be structural.

## Propagation awareness

When modifying shared project context, check whether changes need to propagate:
- **AGENTS.md** ↔ **CLAUDE.md**: shared content lives in AGENTS.md; Claude-specific content in CLAUDE.md. If you change project context (commands, structure, memory files), update AGENTS.md. If you change governance enforcement or subagent registry, update CLAUDE.md.
- **PROJECT-MEMORY.md**: If architectural decisions, enforcement roadmap, or structural patterns changed, update the relevant sections. Check for stale "Phase X — future/deferred" descriptions that now describe implemented features.
- **COMPLIANCE-REVIEW.md**: If hooks, behavioral floor (CLAUDE.md), or tiers.json changed, check whether ongoing checks or verification items need updating.

## Adding new persistent behavioral directives

When you discover a new behavior the AI should consistently exhibit:

1. **Save immediately** as feedback memory (staging — works now, evaluated later)

2. **Identify degradation mechanism:** Which mechanism does this directive counter? (See LEARNING-LOG "Multi-Mechanism Context Degradation Model" for the 5-mechanism taxonomy.) This prevents local optimization — classifying based only on the observed failure rather than the underlying mechanism.

3. **Classify:**
   - **Always-active** (shapes every interaction) → Add to CLAUDE.md Behavioral Floor
     - Selection test: "Would this apply even when answering a simple question with no file modifications?"
     - If yes → behavioral floor. If no → situation-triggered.
   - **Situation-triggered** (activated by context) → Add to the appropriate mechanism:
     - Mechanical check → hook (pre-push, pre-tool)
     - Multi-step process → completion checklist
     - Specific task type → subagent trigger table (§5.1.7)

4. **Reinforce (if always-active):** Also add to `documents/tiers.json` `behavioral_floor` for governance-call reinforcement

5. **Retire staging:** After promotion, remove the feedback memory (or keep if the detailed narrative adds value beyond the compact check)

## Documentation-only changes (memory files, README)

1. Update SESSION-STATE.md if applicable
2. If plan-mode led to committed action, promote plan reasoning inline into BACKLOG / LEARNING-LOG / SESSION-STATE / PROJECT-MEMORY before session end (per rules-of-procedure Appendix G.5.1). Framework files must not cite `~/.claude/plans/*.md` paths as load-bearing — platform plan files are session-scoped working memory.
3. Run **Branch Completion** below.

## Branch Completion

> Final stage for any work session: decide what happens to the branch you're on. The four options below are mutually exclusive — pick one, run its checklist, then stop. The decision tree exists because end-of-session ambiguity ("did we ship?", "is this PR-ready?", "should we keep going?") is the most common cause of incomplete handoffs.

**Decision tree:**

```
Is the work complete (acceptance criteria met, tests green)?
├─ YES → Is this branch the trunk (main/master)?
│        ├─ YES → Option A: COMMIT-AND-PUSH (no merge needed)
│        └─ NO  → Is human review required before this lands on trunk?
│                 ├─ YES → Option B: OPEN PR
│                 └─ NO  → Option C: MERGE (delete branch after)
└─ NO  → Is the work salvageable (worth resuming next session)?
         ├─ YES → Option D: KEEP OPEN (commit checkpoint, push, leave branch)
         └─ NO  → Option E: DISCARD (commit nothing, clean up local, document why)
```

(Five options total — A and C collapse to one when the branch IS trunk.)

### Option A — COMMIT-AND-PUSH (working on trunk, no merge needed)

Use when working directly on `main`/`master` and the work is complete.

- [ ] All change-type checklists above are satisfied for the work done (Code / Content / Domain / Principle / Plan-mode / Docs)
- [ ] `git status` shows no unintended files staged (no `.env`, no credentials, no large binaries)
- [ ] Commit message follows project convention (subject ≤72 chars; body explains the WHY)
- [ ] `git push origin main` (or push branch and verify it lands on trunk)
- [ ] `gh run watch` — verify CI green; if red, fix-forward in a follow-up commit OR `git revert` if regression class

### Option B — OPEN PR (human review required before merge)

Use when the branch needs review (CODEOWNERS, sensitive change, external collaborator).

- [ ] All change-type checklists above are satisfied
- [ ] `git push -u origin <branch>` — push the branch with upstream tracking
- [ ] `gh pr create --title "<short>" --body "$(cat <<EOF...)"` — see CLAUDE.md / built-in PR template for full body convention. Include Summary + Test plan.
- [ ] Self-review the diff in the PR view — would a reviewer be able to follow the change without asking 3 clarifying questions?
- [ ] Tag reviewers if non-default reviewers are needed
- [ ] Do NOT merge yourself unless explicitly authorized (Auto-merge respects branch protection)

### Option C — MERGE (work complete on a feature branch, no review needed)

Use when work is complete on a non-trunk branch and you have authority to merge directly.

- [ ] All change-type checklists above are satisfied
- [ ] `git push -u origin <branch>` — push branch
- [ ] `gh run watch` — wait for CI green BEFORE merging (don't merge red)
- [ ] Merge via `gh pr merge --squash --delete-branch` (or project's preferred merge style — squash/merge/rebase per repo convention)
- [ ] Verify trunk CI green after merge (`git checkout main && git pull && gh run watch`)
- [ ] Delete local branch (`git branch -d <branch>`)

### Option D — KEEP OPEN (work continues next session)

Use when work is incomplete but salvageable; commit a checkpoint so the next session can resume.

- [ ] Tests pass for the partial work (no broken-state checkpoint pushed)
- [ ] Commit message starts with `wip:` or `checkpoint:` so it's visible as not-shippable
- [ ] `git push -u origin <branch>` — push the checkpoint
- [ ] Update SESSION-STATE.md RESUMPTION block with: branch name, what's done, what's next, where the next session should pick up
- [ ] Do NOT open a PR for a checkpoint commit (signals false readiness)

### Option E — DISCARD (work didn't pan out)

Use when the approach was wrong and won't be resumed; discard local work, document the lesson.

- [ ] Add a LEARNING-LOG.md entry capturing what was tried + why it didn't work + what to do differently next time (≥1 paragraph; this is the value extracted from the failed attempt)
- [ ] If any artifacts are worth keeping (notes, partial design docs), commit them to a separate `docs/abandoned-attempts/` location FIRST
- [ ] `git stash drop` (if changes stashed) OR `git checkout . && git clean -fd` (if uncommitted) — destructive, confirm with user before running
- [ ] If a feature branch exists with unmergeable work: `git push origin --delete <branch>` (destructive — confirm) OR rename to `abandoned/<branch>` and push (preserves history)
- [ ] Update SESSION-STATE.md to remove the abandoned work from active state

### Source

Adopted from Superpowers v5.0.7 `finishing-a-development-branch` skill, with the 4-option decision tree (merge / PR / keep / discard) extended to 5 by splitting the "merge" option for trunk-direct work (Option A). The split makes the trunk vs feature-branch case explicit — most repos have both flows, and conflating them produces "merge" steps that don't apply on trunk. See also: [GitHub Agentic Workflows](https://github.blog/ai-and-ml/automate-repository-tasks-with-github-agentic-workflows/) (read-only default + human-approves-merge).
