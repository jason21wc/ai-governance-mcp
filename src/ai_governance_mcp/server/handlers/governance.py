"""Governance evaluation and compliance tool handlers.

Handles: evaluate_governance (Governance Agent), verify_governance_compliance
(Post-Action Audit), log_governance_reasoning (Audit Trail Enhancement).
Includes safety detection and confidence calculation helpers.
"""

import json
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
    ADVISORY_SAFETY_KEYWORDS,
    CRITICAL_SAFETY_KEYWORDS,
    MAX_QUERY_LENGTH,
    MAX_RELEVANT_METHODS,
    _IMPERATIVE_ACTION_VERBS,
    _SAFE_CONTEXT_LEADERS,
    _SENTENCE_BOUNDARY,
)
from .._logging import (
    get_audit_log,
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


def _is_keyword_in_safe_context(action_lower: str, keyword: str) -> bool:
    """True iff EVERY sentence containing `keyword` also contains a safe-context leader.

    Sentence-level granularity (vs. position-span envelope-coverage) handles
    multi-word keywords natively and is robust to leader-before-keyword OR
    leader-after-keyword phrasings. Default-deny: any sentence with the keyword
    but no leader means we treat the action as unsafe.

    Note: case-insensitive substring match for the keyword (mirrors the existing
    CRITICAL/ADVISORY scan semantics — does NOT add word boundaries, since the
    existing scan accepts plurals like "credentials" matching "credential").
    """
    sentences = _SENTENCE_BOUNDARY.split(action_lower)
    keyword_lower = keyword.lower()
    saw_keyword_anywhere = False
    for sentence in sentences:
        if keyword_lower in sentence:
            saw_keyword_anywhere = True
            if not _SAFE_CONTEXT_LEADERS.search(sentence):
                return False  # Keyword in a sentence with no leader → unsafe
    return saw_keyword_anywhere


def _detect_safety_concerns(action: str) -> tuple[list[str], list[str]]:
    """Detect potential safety concerns with two confidence levels.

    Returns (critical_concerns, advisory_concerns):
    - critical_concerns: keywords that ALWAYS force escalation
    - advisory_concerns: keywords that produce warnings only (escalate
      only when semantic retrieval also finds S-Series principles)

    Negation handling: this function DOES NOT parse negation directly
    ("not delete" still flags), because negation parsing creates bypass
    vectors. Instead, a closed allowlist of safe-context leader phrases
    demotes CRITICAL → ADVISORY when ALL of these hold:
      (a) every sentence containing the keyword also contains a leader, AND
      (b) no imperative-action verb appears anywhere in the action.
    Demotion preserves the audit trail via the resulting advisory message
    while removing the false positive. See FM-S-SERIES-KEYWORD-FALSE-POSITIVE
    (re-registered 2026-05-01 / BACKLOG #129).
    """
    action_lower = action.lower()
    critical: list[str] = []
    advisory: list[str] = []

    # Track (keyword, message) pairs for the demotion pass to avoid round-tripping
    # the keyword through string-parse — `msg.split("'")[1]` would crash on any
    # future keyword containing an apostrophe (e.g., "don't") or break under
    # localization. Per BACKLOG #129 post-arc contrarian audit a8e2e0926f756db45
    # HIGH #2.
    critical_kw_msgs: list[tuple[str, str]] = []
    for keyword in CRITICAL_SAFETY_KEYWORDS:
        if keyword in action_lower:
            critical_kw_msgs.append(
                (keyword, f"Action mentions '{keyword}' - requires safety review")
            )

    for keyword in ADVISORY_SAFETY_KEYWORDS:
        if keyword in action_lower:
            advisory.append(f"Action mentions '{keyword}' - may require safety review")

    # Demotion pass: CRITICAL keywords appearing only inside safe-context
    # sentences AND not paired with an imperative-action verb get demoted.
    if critical_kw_msgs:
        imperative_present = bool(_IMPERATIVE_ACTION_VERBS.search(action_lower))
        for kw, msg in critical_kw_msgs:
            if not imperative_present and _is_keyword_in_safe_context(action_lower, kw):
                advisory.append(
                    f"Action mentions '{kw}' in safe context - advisory only"
                )
            else:
                critical.append(msg)

    return critical, advisory


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

    for sp in all_principles[:10]:
        p = sp.principle
        score = sp.combined_score
        if score > best_score:
            best_score = score

        if p.series_code == "S" and score >= engine.settings.s_series_score_threshold:
            s_series_principles.append(p.id)

        relevance = (
            f"Matched via {', '.join(sp.match_reasons)}"
            if sp.match_reasons
            else "Semantic match"
        )
        relevant_principles.append(
            RelevantPrinciple(
                id=p.id,
                title=p.title,
                content=p.content,
                relevance=relevance,
                score=score,
                series_code=p.series_code,
                constitutional_ref=p.constitutional_ref,
                domain=p.domain,
            )
        )

        compliance_evaluations.append(
            ComplianceEvaluation(
                principle_id=p.id,
                principle_title=p.title,
                status=ComplianceStatus.COMPLIANT,
                finding=f"Review action against: {p.title}. Apply this principle before proceeding.",
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
    for field_text in (planned_action, context or "", concerns or ""):
        if not field_text:
            continue
        field_critical, field_advisory = _detect_safety_concerns(field_text)
        critical_concerns.extend(field_critical)
        advisory_concerns.extend(field_advisory)
    critical_concerns = list(dict.fromkeys(critical_concerns))
    advisory_concerns = list(dict.fromkeys(advisory_concerns))

    semantic_safety = len(s_series_principles) > 0
    critical_keyword = len(critical_concerns) > 0
    advisory_keyword = len(advisory_concerns) > 0

    s_series_triggered = semantic_safety or critical_keyword
    keyword_only_warning = advisory_keyword and not s_series_triggered

    s_series_check = SSeriesCheck(
        triggered=s_series_triggered,
        principles=s_series_principles,
        safety_concerns=critical_concerns,
        safety_warnings=advisory_concerns if keyword_only_warning else [],
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
        rationale = (
            "S-Series (safety) principles triggered. "
            "Human review required before proceeding. "
            f"Triggered by: {', '.join(trigger_details)}"
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

    tiers_config = _load_tiers_config()
    if tiers_config:
        output["universal_floor"] = _build_universal_floor(tiers_config)
        critical_5 = _build_critical_5(tiers_config)
        if critical_5:
            output["critical_5"] = critical_5
        domain_floor = _build_domain_floor(tiers_config, result.domains_detected)
        if domain_floor:
            output["domain_floor"] = domain_floor

    governance_time_ms = (time.time() - governance_start_time) * 1000
    with _rate_limit_lock:
        get_metrics().governance_overhead.record_evaluation(
            time_ms=governance_time_ms, assessment=output["assessment"]
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
        output = verification.model_dump()
        output["status"] = output["status"].value
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

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
        output = verification.model_dump()
        output["status"] = output["status"].value
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

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
            output = verification.model_dump()
            output["status"] = output["status"].value
            return [TextContent(type="text", text=json.dumps(output, indent=2))]

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
    output = verification.model_dump()
    output["status"] = output["status"].value
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


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
