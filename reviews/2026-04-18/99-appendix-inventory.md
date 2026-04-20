# 99 — Appendix: Inventory

**Populated progressively.** §1 = Step 1 (derivation). §2 = Step 2 (artifact walk).

---

## §1 — US Constitution Framework (Step 1)

*Derived independently. No repo reads. One-sentence operational role per component.*

| # | Component | Operational role (one sentence) | Amendment/revision cadence | Authority vs. lower layers |
|---|-----------|---------------------------------|----------------------------|----------------------------|
| 1 | **Declaration of Independence** | Founding-intent statement that articulates *why* a separate governed system is being erected and whose consent legitimizes it — rhetorical/moral, not operational; cited when the framework's existence is challenged, not when day-to-day conduct is. | Historical artifact — not amended. | Pre-constitutional; treated as interpretive background, no binding force over subsequent statutes. |
| 2 | **Constitution Preamble** | One-paragraph enumeration of the governed subject ("We the People"), the granting authority, and the ordered ends ("establish Justice, insure domestic Tranquility, provide for the common defence, promote the general Welfare, secure the Blessings of Liberty") — ordering is load-bearing. | Historical artifact — not amended. | Interpretive tiebreaker only; does not itself grant or limit powers (*Jacobson v. Massachusetts*). |
| 3 | **Articles I–VII (Constitution body)** | Structural rules that allocate powers to branches, describe how statutes are made and amendments ratified, and fix jurisdictional boundaries — the system's architecture-diagram with binding force. | Amendable only via Article V (supermajority). | Supreme over statutes and regulations; any conflict voids the subordinate rule. |
| 4 | **Bill of Rights (first 10 Amendments)** | Pre-emptive *overrides* — enumerated protections that can veto any otherwise-valid statute or regulation when triggered; the only layer with explicit "shall not" veto language. | Amendable only via Article V. | Vetoes statutes, regulations, and executive action; judicially enforceable directly. |
| 5 | **Subsequent Amendments (11th +)** | Structural or rights-granting corrections that either (a) extend rights similar to BoR, (b) rewire Articles (e.g., 17th direct-election of senators), or (c) retract a prior amendment (21st repeals 18th) — demonstrates the framework can correct itself. | Article V. | Same supremacy tier as Articles. |
| 6 | **Federal Statutes (U.S. Code)** | Specific legal rules enacted by Congress under Article I authority — fill operational gaps the Constitution intentionally left to the legislature; statutes are where most actual binding conduct rules live. | Amendable by simple majority + President (or veto override). | Subordinate to Constitution; supreme over CFR and case law on statutory questions. |
| 7 | **Code of Federal Regulations (CFR)** | Agency-issued implementation regulations that translate a statute's general mandate into specific, actionable, auditable rules — statute says "protect air quality," CFR says "these NOx values at these stacks." | Amended by notice-and-comment rulemaking; faster than statute. | Must trace to a statute ("enabling authority"); invalid if it exceeds delegated authority. |
| 8 | **Judicial precedent / case law** | Binding interpretations of statute, CFR, and Constitution resolved case-by-case; *stare decisis* makes decisions prospectively binding on lower courts — fills the gap between general rules and specific fact patterns. | Grows with each decision; reversible only by higher-court ruling, statute, or amendment. | Binding within the judicial hierarchy; can void statutes/regulations for unconstitutionality or mis-application. |
| 9 | **Federalist Papers / design commentary** | Non-binding design documents written to explain the *why* behind the structural choices — used as interpretive aid when text is ambiguous. | Historical, not revised. | Persuasive, not binding. |
| 10 | **Congressional Record / legislative history** | Contemporaneous transcript of debates, committee reports, and statements of intent — persuasive evidence of legislative purpose, used when statute text is unclear. | Continuously appended; never edited retrospectively. | Persuasive, not binding; some interpretive schools reject entirely. |
| 11 | **Executive orders / administrative records** | Operational directives issued by the Executive within already-delegated authority — do not create new law but sequence, prioritize, or interpret existing statutes and CFR. | Issued, revised, or revoked by subsequent orders. | Subordinate to statute and CFR; judicially reviewable for exceeding authority. |
| 12 | **Subordinate jurisdictions (states)** | Lower-level governance systems that adopt the federal framework *and* maintain their own local rules where not pre-empted — the framework replicates at lower scale, with federal rules supreme where they apply. | Each jurisdiction sets its own. | Bound by federal law where applicable; otherwise sovereign within their domain. |
| 13 | **Judicial review mechanism** | The enforcement process by which (8) can void actions of (6), (7), (11) — the structural gate that makes the whole system binding rather than advisory; *Marbury v. Madison* established that unreviewable rules are aspirations, not law. | Implicit power, not a written artifact; exercised via case filings. | Meta-layer that validates all others. |

### §1.1 — Cross-cutting properties

- **Hierarchy with veto tiers:** (4) > (3)/(5) > (6) > (7) > (11) > (10)/(9)/(2). (8) traverses all levels via review.
- **Promotion/demotion pathways:** Case law accretes → sometimes codified into statute. Statute patterns accrete → sometimes constitutionalized via amendment. Regulation patterns accrete → sometimes elevated into statute. Informal directives (11) rarely graduate upward.
- **Drift/self-correction mechanisms:** Article V amendments, judicial review, Congressional override, sunset clauses on statute/regulation, CFR notice-and-comment.
- **Enforceability floor:** Only (8) makes the whole stack binding. Without judicial review the document is a preamble to wishes.

### §1.2 — Intent Engineering properties each component threatens if missing

| Component missing | Property threatened |
|---|---|
| Declaration | *effective* (system has no articulated purpose) |
| Preamble | *predictable* (ordering of ends undefined) |
| Articles | *reliable* (no structural rules → arbitrary operation) |
| Bill of Rights | *dependable* (no protection against abuse of delegated power) |
| Amendments-as-mechanism | *repeatable* (system cannot correct itself) |
| Statutes | *efficient* (all conduct rules bubble up to Constitution; gridlock) |
| CFR | *effective* (statute too abstract to operationalize) |
| Case law | *predictable* (rules not applied consistently to fact patterns) |
| Federalist/record | *reliable* in interpretation (ambiguity has no tiebreaker) |
| Executive orders | *efficient* (sequencing/prioritization stuck) |
| Subordinate jurisdictions | *effective* at local scale (one-size-fits-all) |
| Judicial review | *all six* (framework is unenforced therefore aspirational) |

---

## §2 — Artifact Inventory (Step 2)

**Read protocol:** filenames + YAML frontmatter `governance_level` + one grep for opening headings/purpose statements. Forbidden-set (README US-Constitution mapping, Legal System Analogy tables, `.claude/plans/project-constitutional-framework-alignment.md`, prior `reviews/`) not opened. Self-declared role column uses only what is visible in frontmatter / filename / explicit `Purpose:` lines.

| # | Artifact class | Path pattern | Files (count) | Self-claimed role (frontmatter/filename/purpose line only) | Operational content (sample) | Producer | Consumer |
|---|---|---|---|---|---|---|---|
| A | Meta-principles | `documents/constitution.md` | 1 (1245 lines, v4.1.0) | `governance_level: constitution`; subtitle "Meta-Principles" | 24 principles (C:6, O:6, Q:4, G:5, S:3) | Human author; reviewed by subagents | MCP retrieval → AI agents |
| B | Meta-methods / procedure | `documents/rules-of-procedure.md` | 1 (5256 lines, v3.26.8) | `governance_level: rules-of-procedure`; subtitle "Operational Procedures for Framework Maintenance" | Framework authoring rules, amendment process, appendices | Human author | MCP retrieval; AI during framework maintenance |
| C | Domain principles (5 domains) | `documents/title-{10,15,20,25,30,40}-*.md` | 5 (734–1939 lines ea., v1.2.0–v2.7.1) | `governance_level: federal-statute`; "Federal Statutes (Domain Principles)" | Domain-specific principles — ai-coding, ui-ux, multi-agent, kmpd, storytelling, multimodal-rag | Human author | MCP retrieval → domain-auto-routed to AI |
| D | Domain methods (CFR) | `documents/title-{10,15,20,25,30,40}-*-cfr.md` | 5 (778–9000 lines ea., v1.0.1–v2.38.2) | `governance_level: federal-regulations`; "Methods (Code of Federal Regulations equivalent)" | Method sections with Applies-To trigger phrases | Human author | MCP retrieval → AI (proc. guidance) |
| E | Framework activator | `documents/ai-instructions.md` | 1 (213 lines, v2.6) | `governance_level: framework-activation`; "Loader document that activates the governance framework for AI sessions" | Boot-time instructions read on session start | Human author | AI (session start) |
| F | Domain registry | `documents/domains.json` | 1 (v1.4.0 via _version) | Maps domain → principles_file + methods_file + priority | 7 domain entries | Human author | MCP server at index build |
| G | Universal floor config | `documents/tiers.json` | 1 | "Tiered Governance Principle Activation — universal floor items prepended to every evaluate_governance response" | 4 principles + 6 methods + behavioral checks always returned | Human author | MCP server at each evaluate_governance call |
| H | Subagent definitions (canonical) | `documents/agents/*.md` | 10 | Imperative agent descriptions (role, tools, protocol) | code-reviewer, coherence-auditor, continuity-auditor, contrarian-reviewer, documentation-writer, orchestrator, security-auditor, test-generator, validator, voice-coach | Human author | Byte-matched into `.claude/agents/` + `install_agent` MCP tool |
| I | Subagent installations (deployed) | `.claude/agents/*.md` | 10 (mirror of H) | Same content as H — operational copies for Claude Code | Same | `install_agent` MCP tool; byte-checked by CI | Claude Code runtime (agent spawn) |
| J | Post-change workflow | `workflows/COMPLETION-CHECKLIST.md` | 1 (186 lines) | "Post-Change Completion Checklist — precursor to a structured workflow definition"; ENFORCED/BEST-EFFORT tiering | Checklist items per change type | Human author | AI when "run completion sequence" triggered; pre-push hook verifies |
| K | Governance-health review | `workflows/COMPLIANCE-REVIEW.md` | 1 (381 lines) | "Governance Compliance Review" — periodic health audit every 10–15 days | 10 checks + canary prompts | Human author | AI when "run compliance review" triggered |
| L | Reference library entries | `reference-library/ai-coding/ref-*.md` | 13 (populated only in ai-coding domain) | Frontmatter: `id`, `domain`, `tags`, `status`, `entry_type`, `summary`, `maturity`, `decay_class`, `source`, `related` | Battle-tested patterns (pytest fixtures, supabase-jwt, willison-hoard-pattern, etc.) | Human + AI | Human (dev) + AI retrieval |
| L' | Reference library criteria | `reference-library/_criteria.yaml` | **MISSING** (referenced by `ls` but file not present) | *Expected to define admission/maturity criteria* | — | — | — |
| M | Scaffold templates (embedded) | `src/ai_governance_mcp/server.py:846–867` + backing template strings | 2 × (4+2) templates (code) + 1 × 4 templates (document) | `SCAFFOLD_CORE_FILES` + `SCAFFOLD_STANDARD_EXTRAS`; `kit_tier ∈ {core, standard}`; `project_type ∈ {code, document}` | Memory-file skeletons emitted by `scaffold_project` MCP tool | Hard-coded in server source | `scaffold_project` MCP tool → downstream user projects |
| N | In-repo memory files (instances, not templates) | `SESSION-STATE.md`, `PROJECT-MEMORY.md`, `LEARNING-LOG.md`, `BACKLOG.md` (root) | 4 | Project's own session/decision/lesson/backlog state | — | AI during work | AI next session start |
| O | User-facing AI instructions | `CLAUDE.md`, `AGENTS.md` (root) | 2 | "Behavioral Floor — Always Active"; session-start instructions | Behavioral floor checks, governance-hook rule, skip list, subagent list | Human author | AI each session |
| P | Product / project docs | `README.md`, `ARCHITECTURE.md`, `API.md`, `SPECIFICATION.md`, `SBOM.md`, `SECURITY.md` | 6 (1006/692/549/131/?/? lines) | Explains system to external readers | Problem statement, data flow, API reference, spec, SBOM, security threat model | Human author | GitHub readers, ops teams, security reviewers |
| Q | Licenses | `LICENSE` (Apache-2.0), `LICENSE-CONTENT` (CC-BY-NC-ND-4.0) | 2 | Dual license: code vs framework content | Standard license text + commercial-inquiry pointer | Human author (legal) | Downstream consumers |
| R | Enforcement hooks | `.claude/hooks/*.sh` + `scan_transcript.py` | 6 (pre-tool-governance-check, user-prompt-governance-inject, pre-push-quality-gate, pre-test-oom-gate, post-push-ci-check, scan_transcript) | Shell scripts enforcing governance + quality at tool-call boundaries | Pre-bash-write hook blocks if evaluate_governance + query_project not called recently | Human author | Claude Code runtime |
| S | Operational scripts | `scripts/*` | 4 (analyze_compliance.py, evaluate_embeddings.py, measure-watcher-footprint.sh, verify_mcp.py) | Ad-hoc analysis and verification tools | — | Human author | Human operator (ad hoc) |
| T | MCP server source | `src/ai_governance_mcp/` | 12 modules (config, retrieval, server, validator, enforcement, extractor, embedding_ipc, context_engine/, models, path_resolution, config_generator) | Python MCP server implementing 17 tools | Pydantic models + FastMCP tool dispatch | Human + AI | MCP clients |
| U | Test suite | `tests/*.py` + `tests/benchmarks/baseline_*.json` | 29 test modules + 20+ daily benchmark files | pytest suite covering retrieval, hooks, enforcement, extractor, etc. | 1308 tests passing (safe subset) | Human + AI | CI + pre-push |
| V | Drift baselines | `tests/benchmarks/baseline_*.json` | 20+ daily files | Governance server retrieval MRR/Recall per query set | Per-day MRR+Recall for principle and method retrieval | pytest benchmark run | Drift detection (manual + plist) |
| W | CI workflows | `.github/workflows/` | (count n/a — not enumerated) | Standard pytest + lint + docker | — | Human author | GitHub Actions |
| X | Archive (superseded versions) | `documents/archive/` | 3 (`ai-governance-methods-v3.23.2.md`, `ai-interaction-principles-v3.0.0.md`, `v4.0.0.md`) | Prior-version snapshots | Pre-consolidation principle/method files | Human (during amendment) | Historical lookup |
| Y | Migration artifacts | `documents/migration/` | 4 (`constitutional-alignment.md`, `golden-baseline-phase{2,4}.json`, `phase2-migration-log.md`) | One-time-migration supporting files | — | Human (during migration) | Human (audit/verification) |
| Z | Examples | `examples/github-governance.yaml` | 1 | Example governance config for GitHub | — | Human author | Example-adopters |
| AA | Staging / scratch | `staging/` | 8 untracked (benchmark A/B, onnx-backend-attempt, happy-requesttimeout, backfill scripts) | Working directory for in-progress investigations | — | Human + AI | Transient |
| AB | Reviews (this artifact class) | `reviews/YYYY-MM-DD/` | 1 (this review) | Self-review outputs | — | AI (self-review) | Human reviewer; future AI |

### §2.1 — Frontmatter-declared `governance_level` enumeration

All values present:
- `constitution` (1 file: `constitution.md`)
- `rules-of-procedure` (1 file: `rules-of-procedure.md`)
- `federal-statute` (5 files: all `title-*-*.md` except `-cfr`)
- `federal-regulations` (5 files: all `title-*-*-cfr.md`)
- `framework-activation` (1 file: `ai-instructions.md`)

**Observations for later steps (not yet findings):**
- *(O1)* The frontmatter uses US-statutory labels (`federal-statute`, `federal-regulations`). Name-choice itself is a self-declared mapping; operational-criteria check deferred to Step 5.
- *(O2)* No `CHANGELOG.md` file exists at root. Spec Step 7 calls for "CHANGELOG amendments traceable to invocations of the process." This is a structural absence to evaluate in Phase 2.
- *(O3)* Reference library is populated only in `ai-coding/`. The other 5 domains have no reference entries. Promotion pathway (LEARNING-LOG → reference-library → principle) therefore exists only for one domain.
- *(O4)* `reference-library/_criteria.yaml` is referenced in `ls` (the listing `_criteria.yaml` came through `ls`, not `cat`; the prior `head` attempt returned "No such file or directory" — the filename is in directory but may be an empty placeholder or was removed after listing; needs confirmation in Step 7).
- *(O5)* Subagents live in both `documents/agents/` (canonical) and `.claude/agents/` (installed); CI byte-matches. Two of them (`continuity-auditor`, `voice-coach`) are storytelling-domain-specific; they ship with the code package regardless of the consumer project's domain.
- *(O6)* The `ai-instructions.md` governance_level `framework-activation` has no analog in §1 — it's a boot-loader, not a rule-bearing layer. Corresponds to what `CLAUDE.md` does in a Claude Code consumer project.
- *(O7)* Constitution `v4.1.0` and `rules-of-procedure v3.26.8` differ in version cadence — methods churn far more than principles (expected given methods = CFR analog per §1, but should be named explicitly when compared to §1).

