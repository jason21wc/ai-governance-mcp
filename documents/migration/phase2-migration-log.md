# Phase 2 Migration Log — Articles/Amendments Restructuring

**Started:** 2026-04-12
**Completed:** 2026-04-12
**Gate tags:** `const/gate-2` (Phase 2), `const/gate-3` (Phase 3)
**Gate tag (entry):** `const/gate-1`
**Baseline tests:** 1098 passing → **1145 passing** (final)
**Baseline principles:** 22 (C:6, Q:4, O:6, G:3, S:3) → **24 (C:6, Q:4, O:6, G:5, S:3)** (final)

## Technique Stack

| Technique | Purpose | Artifact |
|-----------|---------|----------|
| Golden File Snapshot | Regression detection — any ID change = bug | `golden-baseline-phase2.json` |
| Transformation Map | Spec + test oracle + audit trail | Embedded in golden baseline (`new_header`, `constitutional_ref` fields) |
| Parallel Document | Build v4.0.0 alongside v3.0.0, diff before swapping | `ai-interaction-principles-v4.0.0.md` |
| Dual-Mode Extractor | Parse both old and new formats during migration | Extractor handles both, verified by test |
| Atomic Steps | One section at a time, verify after each | This log |

## Step Log

### Step 1: Safety Artifacts (Task 1)
- **Status:** COMPLETE
- **Created:** `golden-baseline-phase2.json` (22 principles, all IDs captured)
- **Created:** This migration log
- **Verification:** Extractor output matches subagent's manual extraction (22/22 IDs confirmed)

### Step 2: Model Change — constitutional_ref (Task 2)
- **Status:** COMPLETE
- **Change:** Added `constitutional_ref: Optional[str] = None` to Principle model in models.py
- **Verification:** Backward compatibility confirmed — old Principle objects default to None

### Step 3: Extractor Dual-Mode (Task 3)
- **Status:** COMPLETE
- **Changes:**
  - Added `CONSTITUTIONAL_PREFIX_RE` class constant — strips `Section N:` and `Amendment N:` prefixes with colon-anchored lookahead (contrarian F2 fix)
  - Added `ARTICLE_HEADER_RE` and `_ROMAN_TO_INT` for constitutional context tracking
  - Added 6 category mappings: `article iv/iii/ii/i` (ordered longest-first to prevent substring collision), `bill of rights`, `amendment`
  - Added constitutional context tracking in `_extract_principles`: tracks current Article and section/amendment counter
  - Title stripping applied after `new_header_pattern` capture, before skip/indicator checks
  - `_build_principle` passes `constitutional_ref` to Principle constructor
- **Tests written BEFORE code (41 new):**
  - `TestConstitutionalTitleStripping`: 22 parametrized (one per principle) + 5 bare title safety + 1 count check + 5 future-proofing
  - `TestConstitutionalCategoryMapping`: 8 tests (4 Articles, Bill of Rights, Amendment, substring collision, old format backward compat)
- **Issue found:** Article substring collision (article i ⊂ article ii/iii/iv). Fixed with longest-first ordering.
- **Verification:** Golden baseline comparison — all 22 IDs match, all titles match, no constitutional_ref on old format
- **Tests:** 1139 passing (41 new, 0 failures)

### Step 4: Parallel Document (Task 4)
- **Status:** COMPLETE
- **Created:** `ai-interaction-principles-v4.0.0.md` — parallel file with restructured headers
- **Changes:** 28 header transformations (5 section + 22 principle + 1 overview), Framework Overview rewritten to Article/Amendment language, version bumped to 4.0.0
- **Golden file regression:** PASS — all 22 IDs, titles, series codes match baseline
- **Constitutional refs:** All 22 generated correctly (Art. I § 1-6, Art. II § 1-6, Art. III § 1-4, Art. IV § 1-3, Amend. I-III)
- **Diff verification:** Only headers and overview changed — all principle content preserved byte-for-byte

### Step 5: Retrieval + Server (Task 5)
- **Status:** COMPLETE
- **Changes:**
  - `retrieval.py`: Updated `_CONSTITUTION_HIERARCHY` comments with Article/Amendment names
  - `server.py`: Added `constitutional_ref` to `get_principle` output, `evaluate_governance` output, and `query_governance` display format (shows `[Art. I, § 1]` prefix)
  - `models.py`: Added `constitutional_ref` to `RelevantPrinciple` model for evaluate_governance responses
  - `tiers.json`: Verified — all references use slug IDs (unchanged), no modifications needed
- **Tests:** 1139 passing (no changes to test count)

### Step 6: Review Battery (Task 6)
- **Status:** COMPLETE
- **Contrarian review:** PROCEED WITH CAUTION (HIGH confidence)
- **Code review:** PASS WITH NOTES (HIGH confidence)
- **Findings actioned (7 of 9 fixed):**
  1. Imported production regex in tests (no more duplicated copy)
  2. Added 4 integration tests for constitutional_ref (end-to-end through _extract_principles)
  3. Added `else` reset for `in_bill_of_rights`/`current_article_roman` in non-tracked sections
  4. Added `"historical amendments": "general"` before `"amendment"` (substring collision fix)
  5. Named boolean `has_constitutional_prefix = raw_title != title` for clarity
  6. Made `_INT_TO_ROMAN` a class constant (no more per-amendment dict rebuild)
  7. Changed `.search()` to `.match()` for ARTICLE_HEADER_RE (more precise)
- **Deferred (with comment):** Counter-based amendment numbering vs header parsing. Added docstring explaining assumption + future fix path.
- **Rejected:** Retrieval.py comment ordering "discrepancy" — priority order is intentional.
- **Tests:** 1144 passing (46 new total, 0 failures)
- **Golden baseline:** PASS — all 22 IDs match (old format, post-review-fixes)

### Step 7: Double-Check + Swap
- **Status:** COMPLETE
- **Double-check (3-pronged):**
  - Content integrity (byte-level): PASS — 22/22 principle bodies identical between v3 and v4
  - Coherence audit (opus, HIGH confidence): 1 ERROR (Article ordering non-sequential — user decision, deferred to Gate 2), 3 WARNING (missing history entries, old names in history — deferred to Phase 5), 3 INFO (version consistent, content clean, no stale refs)
  - Validator (opus, HIGH confidence): PASS WITH NOTES — 6/7 criteria pass, runtime query_governance tested post-swap
- **Pre-swap fix:** Added v4.0.0 history entry to Historical Amendments section
- **Swap:** v4.0.0 copied to ai-interaction-principles.md, v3.0.0 preserved as ai-interaction-principles-v3.0.0.md
- **Post-swap verification:**
  - Golden baseline regression: PASS — all 22 IDs, titles, refs match
  - Full test suite: 1144 passed, 0 failed
  - Runtime query_governance: Works correctly, returns v4 content. Citation prefix display requires server restart (code hot-reload limitation — expected).
  - Context engine re-indexed: 4739 chunks, 206 files

## Decisions Made During Migration

1. **Article ordering (I, III, II, IV):** Preserved original document section ordering rather than renumbering. Quality preceded Operational in all prior versions. Renumbering would change established references. Deferred to user decision at Gate 2.
2. **Counter-based amendment numbering:** Deferred header-parsing alternative per contrarian review. Added comment documenting sequential-ordering assumption.
3. **Missing v3.0.0 history entry (Q:3→Q:4):** Pre-existing issue, not introduced by Phase 2. Deferred to Phase 5 polish.
4. **Old section names in Historical Amendments:** Non-normative section, defensible as historical record. Mapping note deferred to Phase 5.

## Issues Found

1. **Article substring collision** (Step 3): `"article i"` is substring of `"article ii/iii/iv"`. Fixed with longest-first ordering in category_mapping.
2. **`in_bill_of_rights` never reset** (Step 6, code-reviewer): Non-tracked sections after Bill of Rights would inherit stale state. Fixed with `else` reset clause.
3. **"Historical Amendments" substring collision** (Step 6, code-reviewer): `"amendment"` matched "Historical Amendments" → false safety mapping. Fixed with `"historical amendments": "general"` before `"amendment"`.
4. **DomainConfig missing `display_name`** (Step 6): Integration test fixtures missing required field. Fixed.
5. **Duplicated test in wrong class** (Step 6): `test_old_format_still_works` accidentally landed in RefIntegration class. Fixed.
