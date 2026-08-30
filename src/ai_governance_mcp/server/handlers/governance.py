"""Governance evaluation and compliance tool handlers.

Handles: evaluate_governance (Governance Agent), verify_governance_compliance
(Post-Action Audit), log_governance_reasoning (Audit Trail Enhancement).
Includes safety detection and confidence calculation helpers.
"""

import asyncio
import json
import logging
import time

from mcp.types import TextContent

from ...models import (
    AssessmentStatus,
    ComplianceEvaluation,
    ComplianceStatus,
    ConfidenceLevel,
    ErrorResponse,
    GovernanceAssessment,
    GovernanceAuditLog,
    GovernanceReasoningLog,
    ReasoningEntry,
    RelevantMethod,
    RelevantPrinciple,
    SSeriesCheck,
    VerificationResult,
    VerificationStatus,
)
from ...retrieval import RetrievalEngine
from .._constants import (
    MAX_QUERY_LENGTH,
    MAX_RELEVANT_METHODS,
    PER_UNIT_CONTENT_MAX_CHARS,
    PRINCIPLE_CONTENT_BUDGET_CHARS,
    VETO_INELIGIBLE_S_SERIES_IDS,
)
from .._content_budget import allocate_content

# Safety scanner moved to the dep-light top-level module; re-bound here (the
# redundant `X as X` form marks an intentional re-export so the linter won't
# drop the unused one) so `server/__init__.py` can keep re-exporting both names.
from ...safety_scan import (
    _detect_safety_concerns as _detect_safety_concerns,
    _is_keyword_in_safe_context as _is_keyword_in_safe_context,
    detect_critical_keywords,
    detect_insecure_persistence,
)
from ...keyword_adjudicator import adjudicate_keyword_trigger
from .._logging import (
    get_audit_log,
    get_telemetry_failures,
    log_governance_audit_async,
    log_reasoning_async,
)
from .._security import _rate_limit_lock, _sanitize_for_logging
from .._state import (
    _build_critical_5,
    _build_domain_floor,
    _build_universal_floor,
    _load_tiers_config,
    get_metrics,
)

logger = logging.getLogger(__name__)

# _is_keyword_in_safe_context + _detect_safety_concerns moved to
# ai_governance_mcp.safety_scan (dep-light) and imported above; re-exported by
# server/__init__.py from this module for back-compat.


def _determine_confidence(
    best_score: float, s_series_triggered: bool
) -> ConfidenceLevel:
    """Determine assessment confidence based on retrieval quality and S-Series.

    Per design decision: S-Series = HIGH (safety is not uncertain).
    Otherwise based on retrieval match quality.
    """
    if s_series_triggered:
        return ConfidenceLevel.HIGH  # Safety concerns are not uncertain
    if best_score >= 0.7:
        return ConfidenceLevel.HIGH
    if best_score >= 0.4:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


# Moved to server/_content_budget.py so query_governance can share it (session-302).
# Re-exported here: server/__init__.py and the existing tests import this name, and a
# behaviour-preserving move should not also be an import-surface change.
def _allocate_principle_content(
    principle_entries: list[tuple], budget: int
) -> tuple[dict[int, str | None], list[str]]:
    """Adapter over :func:`allocate_content` for this handler's 4-tuple entries.

    Entries here are ``(principle, score, relevance, is_s_series)``. ``relevance`` is
    never read by the allocator — it was the only reason this logic could not already
    be shared with the retrieval handler.
    """
    # `min()` for the same reason the retrieval path takes it: a per-unit cap ABOVE the
    # budget is dead, and turns marked truncation into silent deletion. Production callers
    # pass 40,000 here so the corpus ceiling binds and this is a no-op — but a cross-vendor
    # review reproduced the failure by calling this adapter with a 20,000 budget, where a
    # 21,000-char body was DROPPED instead of truncated. `budget` is a parameter, so the
    # relationship has to hold for whatever a caller passes, not just for today's constant.
    # Second occurrence of the same trap; the first fix reached only one of the two callers.
    return allocate_content(
        [(p, score, is_s) for p, score, _relevance, is_s in principle_entries],
        budget,
        fetch_tool="get_principle",
        per_unit_max=min(PER_UNIT_CONTENT_MAX_CHARS, budget),
    )


async def _handle_evaluate_governance(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle evaluate_governance tool (Governance Agent).

    Per multi-method-governance-agent-pattern (§4.3):
    - Evaluates planned actions against governance principles
    - Uses existing query_governance for retrieval
    - Auto-detects S-Series concerns with keyword scanning
    - Returns assessment with compliance status per principle
    """
    planned_action = args.get("planned_action", "")
    context = args.get("context", "")
    concerns = args.get("concerns", "")

    if not planned_action:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="planned_action is required",
            suggestions=["Provide a description of the action you plan to take"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    total_length = len(planned_action) + len(context) + len(concerns)
    if total_length > MAX_QUERY_LENGTH:
        error = ErrorResponse(
            error_code="INPUT_TOO_LONG",
            message=f"Combined input exceeds maximum length of {MAX_QUERY_LENGTH} characters",
            suggestions=["Reduce the length of planned_action, context, or concerns"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    governance_start_time = time.time()

    query_parts = [planned_action]
    if context:
        query_parts.append(f"Context: {context}")
    if concerns:
        query_parts.append(f"Concerns: {concerns}")
    composite_query = " ".join(query_parts)

    result = engine.retrieve(composite_query, max_results=10)

    all_principles = result.constitution_principles + result.domain_principles
    relevant_principles: list[RelevantPrinciple] = []
    compliance_evaluations: list[ComplianceEvaluation] = []
    s_series_principles: list[str] = []

    best_score = 0.0

    # First pass: identify S-Series triggers, best score, compliance evals.
    # Output order preserved (hierarchy: S-Series/Constitution first, then domain).
    principle_entries: list[tuple] = []  # (principle, score, relevance, is_s_series)
    for sp in all_principles[:10]:
        p = sp.principle
        score = sp.combined_score
        if score > best_score:
            best_score = score

        # Class gate (does this principle carry veto authority?) AND score gate (is
        # the match strong enough?). R3a / BACKLOG #73 Path B: reasoning-discipline
        # S-Series amendments (Bias Awareness, Transparent Limitations) are in
        # VETO_INELIGIBLE_S_SERIES_IDS — they still surface for REVIEW but never
        # auto-ESCALATE on semantic proximity. Amendment I (action-gate) stays
        # veto-eligible. Removing the auto-veto is NOT bumping the score threshold:
        # the threshold change would also weaken Amendment I in the 0.5-0.75 band.
        is_s_series = (
            p.series_code == "S"
            and p.id not in VETO_INELIGIBLE_S_SERIES_IDS
            and score >= engine.settings.s_series_score_threshold
        )
        if is_s_series:
            s_series_principles.append(p.id)

        relevance = (
            f"Matched via {', '.join(sp.match_reasons)}"
            if sp.match_reasons
            else "Semantic match"
        )
        principle_entries.append((p, score, relevance, is_s_series))

        compliance_evaluations.append(
            ComplianceEvaluation(
                principle_id=p.id,
                principle_title=p.title,
                status=ComplianceStatus.COMPLIANT,
                finding=f"Review action against: {p.title}. Apply this principle before proceeding.",
            )
        )

    # Bound the principle-body payload so the response never exceeds the MCP
    # per-tool-result token cap when many principles match (the 112 KB hard-error
    # class). Triggered S-Series bodies are allocated first (safety must stay
    # visible on ESCALATE), then highest score, within the char budget;
    # principles beyond it are reference-only (content=None — fetch via
    # get_principle). The compact verdict header is always present, so the
    # verdict survives even a many-principle ESCALATE.
    content_by_index, content_fetch_ids = _allocate_principle_content(
        principle_entries, PRINCIPLE_CONTENT_BUDGET_CHARS
    )

    for i, (p, score, relevance, _is_s) in enumerate(principle_entries):
        relevant_principles.append(
            RelevantPrinciple(
                id=p.id,
                title=p.title,
                content=content_by_index[i],
                relevance=relevance,
                score=score,
                series_code=p.series_code,
                constitutional_ref=p.constitutional_ref,
                domain=p.domain,
            )
        )

    relevant_methods: list[RelevantMethod] = []
    for sm in result.methods[:MAX_RELEVANT_METHODS]:
        m = sm.method
        relevant_methods.append(
            RelevantMethod(
                id=m.id,
                title=m.title,
                domain=m.domain,
                score=sm.combined_score,
                confidence=sm.confidence.value,
            )
        )

    # S-Series keyword detection (dual-path: critical + advisory).
    # Per-field calls (NOT joined composite) so safe-context leaders in `context`
    # do not silently cover CRITICAL keywords in `planned_action`. Per BACKLOG
    # #129 round-2 contrarian audit a044f06182de62945 HIGH #1.
    critical_concerns: list[str] = []
    advisory_concerns: list[str] = []
    # Keyword scan scoped to planned_action only (#199): a hazard word in
    # context/concerns is the caller reasoning about risk, not the caller
    # acting — scanning those fields created a perverse incentive where careful
    # callers manufactured their own false ESCALATEs. The adjudicator (Layer-1
    # judge) still receives all fields via fields_by_name for semantic reasoning.
    fields_by_name = {
        "planned_action": planned_action,
        "context": context or "",
        "concerns": concerns or "",
    }
    keywords_by_field: dict[str, list[str]] = {}
    # Only scan planned_action for keyword triggers
    if planned_action:
        field_critical, field_advisory = _detect_safety_concerns(planned_action)
        critical_concerns.extend(field_critical)
        advisory_concerns.extend(field_advisory)
        field_keywords = detect_critical_keywords(planned_action)
        if field_keywords:
            keywords_by_field["planned_action"] = field_keywords
    critical_concerns = list(dict.fromkeys(critical_concerns))
    advisory_concerns = list(dict.fromkeys(advisory_concerns))

    semantic_safety = len(s_series_principles) > 0
    critical_keyword = len(critical_concerns) > 0
    advisory_keyword = len(advisory_concerns) > 0

    # Keyword-only adjudication layer (BACKLOG #73, plan async-giggling-wren).
    # Only the keyword-only class is adjudicated: a CRITICAL keyword matched AND
    # no S-Series principle was retrieved. The semantic veto and the combined
    # path are never second-guessed. Layer 0 (deterministic insecure-persistence
    # floor) escalates without consulting the judge; the judge classifies the
    # rest benign-vs-genuine; any judge failure is 'unavailable' → fail-safe
    # ESCALATE. Mode: off (skip), shadow (run + record, route unchanged),
    # active (route on the verdict).
    keyword_only = critical_keyword and not semantic_safety
    keyword_adjudication: str | None = None
    adjudication_ms: float | None = None
    adjudication_reason: str | None = None
    judged_benign = False
    judge_mode = getattr(engine.settings, "keyword_judge_mode", "shadow")

    if keyword_only and judge_mode != "off":
        floor_hits = detect_insecure_persistence(planned_action)
        if floor_hits:
            keyword_adjudication = "floor"
            # Safe by construction (regex token + static keyword), but sanitize
            # unconditionally to future-proof if the hit message ever grows text.
            adjudication_reason = _sanitize_for_logging(floor_hits[0])
        else:
            adj_start = time.time()
            verdict = await asyncio.to_thread(
                adjudicate_keyword_trigger,
                fields_by_name,
                keywords_by_field,
                model=getattr(engine.settings, "keyword_judge_model", None),
                timeout=getattr(engine.settings, "keyword_judge_timeout", 45),
            )
            adjudication_ms = (time.time() - adj_start) * 1000
            keyword_adjudication = verdict["verdict"]  # genuine | benign | unavailable
            # The reason is model-authored under possible prompt injection — redact
            # any secret shape before it reaches the persisted audit log (security
            # MEDIUM-1). _sanitize_for_logging also length-truncates.
            adjudication_reason = _sanitize_for_logging(verdict.get("reason", ""))
        # Only ACTIVE mode routes on the verdict; SHADOW records but keeps
        # today's ESCALATE (verify-then-trust rollout).
        if judge_mode == "active" and keyword_adjudication == "benign":
            judged_benign = True

    s_series_triggered = (semantic_safety or critical_keyword) and not judged_benign
    keyword_only_warning = advisory_keyword and not s_series_triggered

    s_series_check = SSeriesCheck(
        triggered=s_series_triggered,
        principles=s_series_principles,
        safety_concerns=critical_concerns,
        safety_warnings=advisory_concerns if keyword_only_warning else [],
        keyword_adjudication=keyword_adjudication,
    )

    required_modifications: list[str] = []
    requires_ai_judgment = False
    ai_judgment_guidance: str | None = None

    if s_series_triggered:
        assessment = AssessmentStatus.ESCALATE
        requires_ai_judgment = False
        trigger_details = s_series_principles + critical_concerns
        if semantic_safety and advisory_keyword:
            trigger_details.extend(advisory_concerns)
        if semantic_safety:
            # A real S-Series principle was retrieved above threshold — a genuine veto.
            rationale = (
                "S-Series (safety) principle(s) triggered. "
                "Human review required before proceeding. "
                f"Triggered by: {', '.join(trigger_details)}"
            )
        elif keyword_adjudication == "floor":
            # Layer-0 deterministic net: a persistence signal (store/save/hardcode/
            # plaintext) co-located with a CRITICAL keyword — insecure-persistence
            # phrasing that escalates without consulting the judge.
            rationale = (
                "Insecure-persistence floor triggered (deterministic): a "
                "persistence signal is co-located with a sensitive keyword. "
                f"Triggered by: {', '.join(trigger_details)}"
            )
        elif keyword_adjudication == "genuine":
            # The fresh-context adjudicator ruled the keyword-only trigger a
            # genuine concern (not a mere topic mention).
            rationale = (
                "Safety keyword match adjudicated GENUINE by the fresh-context "
                "judge — human review required before proceeding. "
                f"Triggered by: {', '.join(trigger_details)}"
            )
        else:
            # Keyword-only trigger: a CRITICAL safety KEYWORD matched but NO S-Series
            # principle was retrieved (principles == []). This is a heuristic topic
            # match, not a principle veto — label it honestly so the consumer can
            # calibrate. Known keyword false-positive class (M-004): a benign or
            # user-authorized action that merely mentions a sensitive term should be
            # surfaced and proceeded with judgment, not treated as an absolute veto.
            # In ACTIVE mode with keyword_adjudication == "unavailable" the judge
            # was unreachable, so we failed safe to ESCALATE (noted below).
            unavailable_note = (
                " (adjudicator unavailable — failed safe to ESCALATE)"
                if keyword_adjudication == "unavailable"
                else ""
            )
            rationale = (
                "Safety keyword match (heuristic; no S-Series principle retrieved) — "
                f"escalated for visibility{unavailable_note}. "
                f"Triggered by: {', '.join(trigger_details)}. "
                "If this action is benign or user-authorized, this is a known keyword "
                "false-positive pattern (M-004) — surface it and proceed with judgment."
            )
    elif judged_benign:
        # ACTIVE mode, judge ruled the keyword-only trigger a benign topic
        # mention. Route to REVIEW (surface the concern for a human note) rather
        # than PROCEED — a bare keyword is not a veto, but the mention is worth
        # showing. triggered=False keeps the M-004 honesty (no false veto claim).
        assessment = AssessmentStatus.REVIEW
        requires_ai_judgment = True
        ai_judgment_guidance = (
            "A CRITICAL safety keyword matched but the fresh-context adjudicator "
            "ruled it a benign topic mention (not a genuine concern). Proceed with "
            "normal judgment; the mention is surfaced for visibility, not as a veto."
        )
        rationale = (
            "Safety keyword match adjudicated BENIGN by the fresh-context judge "
            "(topic mention, not a veto). Surfaced for review. "
            f"Keyword(s): {', '.join(critical_concerns)}."
        )
    elif not relevant_principles or best_score < engine.settings.review_score_threshold:
        assessment = AssessmentStatus.PROCEED
        requires_ai_judgment = False
        if relevant_principles:
            rationale = (
                f"Principles surfaced but below REVIEW threshold "
                f"(best score {best_score:.2f} < {engine.settings.review_score_threshold}). "
                "Principles included for reference. Action may proceed."
            )
        else:
            rationale = (
                "No strongly relevant governance principles found. "
                "Action may proceed but consider querying with more specific terms."
            )
    else:
        assessment = AssessmentStatus.REVIEW
        requires_ai_judgment = True
        ai_judgment_guidance = (
            "Governance principles were surfaced. Read each principle's content against "
            "your planned action. If conflicts exist and modifications can resolve them, "
            "apply them and log via log_governance_reasoning() with final_decision=REVIEW. "
            "If fully compliant, confirm PROCEED."
        )
        if relevant_methods:
            ai_judgment_guidance += (
                " Relevant methods are included as references — use get_principle(id) "
                "to retrieve full procedural content for any method that would help "
                "determine compliance."
            )
        if content_fetch_ids:
            ai_judgment_guidance += (
                " Some lower-ranked principle bodies were omitted to fit size limits "
                "(see principle_content_note) — use get_principle(id) for their full text."
            )
        top_principle = relevant_principles[0]
        rationale = (
            f"AI judgment required for {len(relevant_principles)} relevant principles. "
            f"Primary principle: {top_principle.title} (score: {top_principle.score:.2f}). "
            "Read principle content and determine if modifications are needed."
        )

    confidence = _determine_confidence(best_score, s_series_triggered)

    governance_assessment = GovernanceAssessment(
        action_reviewed=planned_action,
        assessment=assessment,
        confidence=confidence,
        relevant_principles=relevant_principles,
        relevant_methods=relevant_methods,
        compliance_evaluation=compliance_evaluations,
        required_modifications=required_modifications,
        s_series_check=s_series_check,
        rationale=rationale,
        requires_ai_judgment=requires_ai_judgment,
        ai_judgment_guidance=ai_judgment_guidance,
    )

    audit_entry = GovernanceAuditLog(
        audit_id=governance_assessment.audit_id,
        timestamp=governance_assessment.timestamp,
        action=_sanitize_for_logging(planned_action),
        assessment=assessment,
        principles_consulted=[rp.id for rp in relevant_principles],
        methods_surfaced=[rm.id for rm in relevant_methods],
        s_series_triggered=s_series_triggered,
        modifications=required_modifications if required_modifications else None,
        escalation_reason=rationale
        if assessment == AssessmentStatus.ESCALATE
        else None,
        confidence=confidence,
        best_score=round(best_score, 4) if all_principles else None,
        keyword_adjudication=keyword_adjudication,
        adjudication_ms=(
            round(adjudication_ms, 1) if adjudication_ms is not None else None
        ),
        adjudication_reason=adjudication_reason,
    )
    await log_governance_audit_async(audit_entry)

    auto_reasoning_entries = [
        ReasoningEntry(
            principle_id=rp.id,
            status="EVALUATED",
            reasoning=f"Surfaced by governance evaluation (score: {rp.score:.2f})",
        )
        for rp in relevant_principles
    ]
    for rm in relevant_methods:
        auto_reasoning_entries.append(
            ReasoningEntry(
                principle_id=rm.id,
                status="EVALUATED",
                reasoning=f"Method surfaced (score: {rm.score:.2f}, "
                f"confidence: {rm.confidence})",
            )
        )
    auto_reasoning = GovernanceReasoningLog(
        audit_id=governance_assessment.audit_id,
        reasoning_entries=auto_reasoning_entries
        if auto_reasoning_entries
        else [
            ReasoningEntry(
                principle_id="none",
                status="EVALUATED",
                reasoning="No strongly relevant principles found for this action",
            )
        ],
        final_decision=assessment.value,
        modifications_applied=required_modifications or [],
        auto_generated=True,
    )
    await log_reasoning_async(auto_reasoning)

    output = governance_assessment.model_dump()
    output["assessment"] = output["assessment"].value
    output["confidence"] = output["confidence"].value
    for ce in output["compliance_evaluation"]:
        ce["status"] = ce["status"].value

    # Path-independent recovery pointer: present on EVERY assessment (ESCALATE /
    # PROCEED / REVIEW), not just where ai_judgment_guidance is set, so a caller
    # always knows which principle bodies to fetch via get_principle.
    if content_fetch_ids:
        fetch_ids = list(dict.fromkeys(content_fetch_ids))
        output["principle_content_note"] = (
            f"{len(fetch_ids)} principle "
            f"{'body was' if len(fetch_ids) == 1 else 'bodies were'} omitted or "
            "truncated to keep this response within MCP size limits. Call "
            "get_principle('<id>') for full text. "
            f"Needs fetch: {', '.join(fetch_ids)}"
        )

    tiers_config = _load_tiers_config()
    if tiers_config:
        try:
            output["universal_floor"] = _build_universal_floor(tiers_config)
            critical_5 = _build_critical_5(tiers_config)
            if critical_5:
                output["critical_5"] = critical_5
            domain_floor = _build_domain_floor(tiers_config, result.domains_detected)
            if domain_floor:
                output["domain_floor"] = domain_floor
        except (TypeError, AttributeError):
            logger.warning(
                "Floor decoration failed — returning assessment without floor data",
                exc_info=True,
            )

    governance_time_ms = (time.time() - governance_start_time) * 1000
    with _rate_limit_lock:
        get_metrics().governance_overhead.record_evaluation(
            time_ms=governance_time_ms, assessment=output["assessment"]
        )

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _verification_response(verification: VerificationResult) -> list[TextContent]:
    """Serialize a verification result, annotating any durable-telemetry gap.

    SINGLE EXIT ON PURPOSE. This handler had four identical dump-and-return tails,
    and a field that must appear on all four is a field that will be missing from
    one of them after the next edit.

    WHY THE GAP BELONGS HERE SPECIFICALLY. This is the tool whose job is "was
    governance actually recorded?", and it answers from the IN-MEMORY audit deque.
    When a durable write has failed, the in-memory answer is still correct while
    ``logs/*.jsonl`` — what ``/compliance-review`` and
    ``scripts/analyze_compliance.py`` read — has holes. In a log-derived metric an
    absent record is indistinguishable from "this never happened", so a caller
    told COMPLIANT here could later be told NON_COMPLIANT there with neither
    answer being wrong. Naming the gap is what makes those two reconcilable.

    Not added to ``evaluate_governance`` (hottest response, already size-budgeted,
    and empty on virtually every call) nor to ``get_metrics`` (a volume/latency
    report nobody opens mid-incident).
    """
    output = verification.model_dump()
    output["status"] = output["status"].value
    gaps = get_telemetry_failures()
    if gaps:
        output["durable_telemetry_gaps"] = gaps
        output["finding"] = (
            f"{output['finding']} NOTE: {sum(gaps.values())} durable telemetry "
            f"write(s) failed in this process ({', '.join(sorted(gaps))}); the "
            "in-memory trail above is intact but log-derived compliance metrics "
            "will undercount."
        )
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_verify_governance(args: dict) -> list[TextContent]:
    """Handle verify_governance_compliance tool (Post-Action Audit).

    Per §4.6 Governance Enforcement Architecture, Layer 3:
    - Checks whether governance was consulted for a completed action
    - Returns COMPLIANT, NON_COMPLIANT, or PARTIAL
    - Enables detection of bypassed governance checks after the fact
    """
    action_description = args.get("action_description", "")
    expected_principles = args.get("expected_principles", [])

    if not action_description:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="action_description is required",
            suggestions=["Describe the action that was completed"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    audit_log = get_audit_log()

    if not audit_log:
        verification = VerificationResult(
            action_description=action_description,
            status=VerificationStatus.NON_COMPLIANT,
            matching_audit_id=None,
            finding=(
                "No governance checks have been performed in this session. "
                "All actions except reads, non-sensitive questions, and trivial formatting should be preceded by evaluate_governance()."
            ),
        )
        return _verification_response(verification)

    action_words = set(action_description.lower().split())
    best_match: GovernanceAuditLog | None = None
    best_overlap = 0

    for entry in reversed(audit_log):
        entry_words = set(entry.action.lower().split())
        overlap = len(action_words & entry_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = entry

    if not best_match or best_overlap < 2:
        verification = VerificationResult(
            action_description=action_description,
            status=VerificationStatus.NON_COMPLIANT,
            matching_audit_id=None,
            finding=(
                f"No governance check found matching this action. "
                f"Found {len(audit_log)} audit entries, but none matched. "
                "Action may have bypassed governance. Consider retroactive review."
            ),
        )
        return _verification_response(verification)

    if expected_principles:
        consulted = set(best_match.principles_consulted)
        expected = set(expected_principles)
        missing = expected - consulted

        if missing:
            verification = VerificationResult(
                action_description=action_description,
                status=VerificationStatus.PARTIAL,
                matching_audit_id=best_match.audit_id,
                finding=(
                    f"Governance was consulted (audit_id: {best_match.audit_id}), "
                    f"but expected principles were not all checked. "
                    f"Missing: {', '.join(missing)}. "
                    f"Assessment was: {best_match.assessment.value}."
                ),
            )
            return _verification_response(verification)

    verification = VerificationResult(
        action_description=action_description,
        status=VerificationStatus.COMPLIANT,
        matching_audit_id=best_match.audit_id,
        finding=(
            f"Governance was consulted before this action. "
            f"Audit ID: {best_match.audit_id}. "
            f"Assessment: {best_match.assessment.value}. "
            f"Principles consulted: {len(best_match.principles_consulted)}."
        ),
    )
    return _verification_response(verification)


async def _handle_log_governance_reasoning(args: dict) -> list[TextContent]:
    """Handle log_governance_reasoning tool (Audit Trail Enhancement).

    Records AI's governance reasoning trace linked to an audit entry.
    Part of Governance Reasoning Externalization feature.
    Enables observability and audit trail completeness.
    """
    audit_id = args.get("audit_id", "")
    reasoning = args.get("reasoning", [])
    final_decision = args.get("final_decision", "")
    modifications_applied = args.get("modifications_applied", [])

    if not audit_id:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="audit_id is required",
            suggestions=["Provide the audit_id from evaluate_governance response"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    if not reasoning:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="reasoning array is required and cannot be empty",
            suggestions=[
                "Provide at least one reasoning entry",
                "Each entry needs: principle_id, status, reasoning",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    if not final_decision:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELD",
            message="final_decision is required",
            suggestions=["Provide PROCEED, REVIEW, or ESCALATE"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    audit_log = get_audit_log()
    matching_audit = None
    for entry in audit_log:
        if entry.audit_id == audit_id:
            matching_audit = entry
            break

    if not matching_audit:
        error = ErrorResponse(
            error_code="AUDIT_NOT_FOUND",
            message=f"No audit entry found with id: {audit_id}",
            suggestions=[
                "Ensure evaluate_governance was called first",
                "Use the audit_id from the evaluate_governance response",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    reasoning_entries = []
    for entry in reasoning[:20]:
        reasoning_entries.append(
            ReasoningEntry(
                principle_id=str(entry.get("principle_id", ""))[:100],
                status=str(entry.get("status", "COMPLIES"))[:30],
                reasoning=_sanitize_for_logging(str(entry.get("reasoning", "")))[:1000],
            )
        )

    reasoning_log_entry = GovernanceReasoningLog(
        audit_id=audit_id,
        reasoning_entries=reasoning_entries,
        final_decision=final_decision,
        modifications_applied=[
            _sanitize_for_logging(str(m))[:500] for m in modifications_applied[:10]
        ],
    )

    await log_reasoning_async(reasoning_log_entry)

    output = {
        "status": "logged",
        "audit_id": audit_id,
        "entries_logged": len(reasoning_entries),
        "final_decision": final_decision,
        "modifications_count": len(modifications_applied),
        "message": "Governance reasoning trace recorded successfully.",
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]
