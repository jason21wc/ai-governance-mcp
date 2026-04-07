# AI Governance MCP - Learning Log

**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> **Entry rules:** Each entry ≤5 lines. State what happened, then the actionable rule.
> Record conclusions, not evidence. If it wouldn't change future behavior, it doesn't belong here.
> When lesson graduates: Add to methods doc, mark "Graduated to §X.Y"
> Route other content: decisions → PROJECT-MEMORY, architecture → ARCHITECTURE.md

---

## Active Lessons

### Autoregressive Forward-Continuation Bias (2026-03-28) — CRITICAL

**Corrected root cause (supersedes "velocity pressure" framing):** When LLMs skip advisory verification steps, it is NOT because of "velocity pressure" or "being rushed." LLMs don't experience pressure. The actual mechanism is **autoregressive forward-continuation bias**: each completed step raises the probability that the next token continues toward task completion rather than pausing to verify. Verification steps are lower-probability generations that break the forward trajectory. This is structural to how LLMs generate tokens, not a motivational failure. Citing "velocity pressure" is the AI rationalizing a generation pattern as an emotional state. (Research: Agent Drift arxiv 2601.04170; LLMs Get Lost arxiv 2505.06120 — 39% multi-turn performance drop, premature solution generation.)

**Rule:** Stop treating verification/review steps as advisory interruptions. Make them part of the expected generation flow — the path of least resistance should run THROUGH verification, not around it. Three structural techniques: (1) Gate-token transitions — require specific output before phase transition; (2) Verification as control flow — the review determines what happens next; (3) Schema enforcement — required fields before result field. Advisory prompting ("please verify") has the lowest reliability of any technique.

**Rule (retained):** Advisory compliance is ~85%. For items that must be 100%, enforce structurally. COMPLETION-CHECKLIST tiered as ENFORCED vs BEST-EFFORT.

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

### Tree-sitter Positional Children Are Fragile — Use Field Names (2026-02-13)

`_get_imported_names` used `node.children[1]` to skip the module path in `from X import Y`. This broke for relative imports (`from .bar import baz`) where the module node sits at a different index due to the `.` prefix. Fixed by using `node.child_by_field_name("module_name")` for identity comparison.

**Rule:** When navigating tree-sitter AST nodes, prefer `child_by_field_name()` over positional `children[N]` indexing. Positional assumptions break across syntax variants of the same node type.

---

### Environment-Aware Tests for Optional Dependencies (2026-02-12)

Tests for `_get_chunking_version()` failed because tree-sitter IS installed in dev but not CI. Hardcoded `"line-based-v1"` broke when the actual connector detected tree-sitter.

**Rule:** Tests that depend on optional package availability should either: (1) explicitly force the flag (`c._tree_sitter_available = False`), or (2) dynamically detect the actual value. Never hardcode expected values for environment-dependent behavior.

---

### Test Inputs Must Traverse the Full Validation Chain (2026-02-11)

Two test bugs: (1) `"nonexistent00"` has non-hex chars — hit project_id hex validation before reaching the "not found" path we intended to test. (2) `cooldown_seconds=0.0` caused infinite retry cascade — each failed callback re-queued and the 0s timer fired immediately, chaining endlessly and spamming logs.

**Rule:** When writing tests for code with layered validation, trace the full call path to ensure your test input reaches the code path you intend to test. For timer-based retry tests, use a high cooldown (e.g., 60s) so the retry timer never fires during the test, and call `_running.clear()` in cleanup.

---

### Guard-Then-Load Pattern: Don't Undo Your Own Safety Checks (2026-02-10)

`_load_project` correctly discarded incompatible embeddings on model mismatch. Then immediately called `_load_search_indexes` which reloaded them unconditionally — undoing the safety check. Similarly, `get_principle_by_id` used a prefix→domain map where "multi" (multi-agent) and "mult" (multimodal-rag) collided because Python dict lookup stops at the first prefix match.

**Rule:** When a function sets a safety state (discarding data, marking flags), audit all subsequent calls to verify they don't silently reverse that state. When mapping IDs to domains, prefer exhaustive search over prefix heuristics — domain count is small, correctness matters more than lookup speed.

---

### Bold Text Drives Method Retrieval Surfacing (2026-02-07)

New method sections get generic chunk titles from the extractor (e.g., "Purpose", "Trigger Conditions"). The extractor picks up **bold text** as `trigger_phrases` (max 4 words, >5 chars). Without bold key terms, method chunks won't surface for natural-language queries.

Three additional extraction traps discovered during Part 4.3 tuning:
1. **Skip-list titles** — `"purpose"` is in `skip_method_titles` (extractor.py:1008). Sections titled "Purpose" get absorbed into the preceding chunk. Fix: use a descriptive title instead.
2. **Short bold terms** — Bold text ≤5 chars (e.g., `**Quick**`, `**Full**`, `**Note:**`) fails the `len(b) > 5` filter. Fix: bold multi-word phrases instead (e.g., `**Quick tier**`).
3. **`Applies To:` field** — The extractor parses `**Applies To:**` lines (extractor.py:1123-1136) into both BM25 and embedding text. Adding this field helps methods surface for `evaluate_governance()` queries.

**Rule:** When adding new method sections: (a) avoid skip-list titles ("purpose", "overview", etc.), (b) bold 2-3 distinctive phrases >5 chars, (c) add `**Applies To:**` with natural-language use cases. Verify after index rebuild (auto-reload picks up changes on next query).

---

### CI Must Install All Test-Relevant Extras (2026-02-07)

CI installed `.[dev]` but context engine tests need `pathspec` (in `.[context-engine]` extras). All 200 CE tests failed with `ModuleNotFoundError`.

**Rule:** When adding optional dependency groups, update CI to install them if tests cover that code. See Gotcha #23.

---

### Version History Entries Can Be Silently Dropped (2026-02-08)

Coherence audit found v3.7.0 missing from version history table and v3.7.0.1 orphaned at end of file. During edits, version history entries can be accidentally deleted or displaced without anyone noticing — the table is long and entries look similar.

**Rule:** Add a version-history-completeness check to pre-release audits: verify descending order, no gaps, and no orphaned entries outside the table. Grep for `### v` outside the table section.

---

### Cognitive Function Labels Must Be Distinct Across Agents (2026-02-08)

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
