"""Retrieval-oriented tool handlers.

Handles: query_governance (T13), get_principle (T14), list_domains (T15),
get_domain_summary (T16), log_feedback (T17), get_metrics (T18).
"""

import json
from datetime import datetime, timezone

from mcp.types import TextContent

from ...models import ErrorResponse, Feedback, QueryLog
from ...retrieval import RetrievalEngine
from .._constants import MAX_QUERY_LENGTH
from .._logging import log_feedback_async, log_query_async
from .._security import _rate_limit_lock, _sanitize_for_logging
from .._state import get_metrics


async def _handle_query_governance(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle query_governance tool (T13)."""
    query = args.get("query", "")
    if not query:
        return [TextContent(type="text", text="Error: query is required")]

    if len(query) > MAX_QUERY_LENGTH:
        return [
            TextContent(
                type="text",
                text=f"Error: query exceeds maximum length of {MAX_QUERY_LENGTH} characters",
            )
        ]

    domain = args.get("domain")
    valid_domains = {
        "constitution",
        "ai-coding",
        "multi-agent",
        "storytelling",
        "multimodal-rag",
        "ui-ux",
        "kmpd",
    }
    if domain is not None and domain not in valid_domains:
        return [
            TextContent(
                type="text",
                text=f"Error: Invalid domain '{domain}'. Valid: {', '.join(sorted(valid_domains))}",
            )
        ]

    max_results = args.get("max_results")
    if max_results is not None:
        try:
            max_results = min(max(int(max_results), 1), 50)
        except (ValueError, TypeError):
            max_results = 10

    result = engine.retrieve(
        query=query,
        domain=domain,
        include_constitution=args.get("include_constitution", True),
        include_methods=args.get("include_methods", True),
        max_results=max_results,
    )

    metrics = get_metrics()
    retrieval_ms = result.retrieval_time_ms or 0.0
    with _rate_limit_lock:
        metrics.total_queries += 1
        metrics.avg_retrieval_time_ms = (
            metrics.avg_retrieval_time_ms * (metrics.total_queries - 1) + retrieval_ms
        ) / metrics.total_queries
        if result.s_series_triggered:
            metrics.s_series_trigger_count += 1

        for detected_domain in result.domains_detected:
            metrics.domain_query_counts[detected_domain] = (
                metrics.domain_query_counts.get(detected_domain, 0) + 1
            )

        for sp in result.constitution_principles + result.domain_principles:
            level = sp.confidence.value
            metrics.confidence_distribution[level] = (
                metrics.confidence_distribution.get(level, 0) + 1
            )

    query_log = QueryLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        query=_sanitize_for_logging(query),
        domains_detected=result.domains_detected,
        principles_returned=[
            sp.principle.id
            for sp in result.constitution_principles + result.domain_principles
        ],
        methods_returned=[sm.method.id for sm in result.methods],
        s_series_triggered=result.s_series_triggered,
        retrieval_time_ms=result.retrieval_time_ms,
        top_confidence=result.constitution_principles[0].confidence
        if result.constitution_principles
        else None,
    )
    await log_query_async(query_log)

    output = _format_retrieval_result(result)
    return [TextContent(type="text", text=output)]


def _format_retrieval_result(result) -> str:
    """Format retrieval result as readable markdown."""
    lines = []

    if result.s_series_triggered:
        lines.append("## S-SERIES TRIGGERED - Safety/Ethics Principles Apply")
        lines.append("")

    lines.append(f"**Query:** {result.query}")
    lines.append(
        f"**Domains Detected:** {', '.join(result.domains_detected) or 'None (Constitution only)'}"
    )
    if result.domain_scores:
        scores = ", ".join(f"{d}: {s:.2f}" for d, s in result.domain_scores.items())
        lines.append(f"**Domain Scores:** {scores}")
    lines.append(f"**Retrieval Time:** {result.retrieval_time_ms:.1f}ms")
    lines.append("")

    if result.constitution_principles:
        lines.append("## Constitution Principles")
        for sp in result.constitution_principles:
            p = sp.principle
            ref_prefix = f"[{p.constitutional_ref}] " if p.constitutional_ref else ""
            lines.append(
                f"### [{sp.confidence.value.upper()}] {ref_prefix}{p.id}: {p.title}"
            )
            series_info = f"Series: {p.series_code} | " if p.series_code else ""
            lines.append(
                f"*{series_info}Scores: BM25={sp.keyword_score:.2f}, Semantic={sp.semantic_score:.2f}, Combined={sp.combined_score:.2f}*"
            )
            if sp.match_reasons:
                lines.append(f"*Match: {', '.join(sp.match_reasons)}*")
            lines.append("")
            content_preview = (
                p.content[:600] + "..." if len(p.content) > 600 else p.content
            )
            lines.append(content_preview)
            lines.append("")

    if result.domain_principles:
        lines.append("## Domain Principles")
        for sp in result.domain_principles:
            p = sp.principle
            lines.append(f"### [{sp.confidence.value.upper()}] {p.id}: {p.title}")
            series_info = f" | Series: {p.series_code}" if p.series_code else ""
            lines.append(
                f"*Domain: {p.domain}{series_info} | Combined: {sp.combined_score:.2f}*"
            )
            lines.append("")
            content_preview = (
                p.content[:600] + "..." if len(p.content) > 600 else p.content
            )
            lines.append(content_preview)
            lines.append("")

    if result.methods:
        lines.append("## Applicable Methods")
        for sm in result.methods:
            m = sm.method
            lines.append(f"- **{m.id}:** {m.title} (confidence: {sm.confidence.value})")
        lines.append("")

    if result.references:
        lines.append("## Relevant Precedent (Reference Library)")
        for sr in result.references:
            r = sr.reference
            status_icon = {
                "current": "🟢",
                "caution": "🟡",
                "deprecated": "🔴",
                "archived": "⬜",
            }
            icon = status_icon.get(r.status, "")
            lines.append(
                f"- {icon} **{r.id}:** {r.title} [{r.maturity}/{r.status}] "
                f"(confidence: {sr.confidence.value})"
            )
            if r.summary:
                lines.append(f"  {r.summary}")
        lines.append("")

    if not result.constitution_principles and not result.domain_principles:
        lines.append(
            "*No matching principles found. Try rephrasing your query or specifying a domain.*"
        )

    if result.constitution_principles or result.domain_principles:
        lines.append("---")
        lines.append(
            "*Help improve retrieval: Use `log_feedback(query, principle_id, rating)` "
            "to rate relevance (1-5). High-rated principles get boosted in future queries.*"
        )

    return "\n".join(lines)


async def _handle_get_principle(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle get_principle tool (T14).

    Retrieves both principles and methods by ID.
    Method IDs contain '-method-' (e.g., meta-method-header-hierarchy).
    """
    principle_id = args.get("principle_id", "")
    if not principle_id:
        return [TextContent(type="text", text="Error: principle_id is required")]

    principle = engine.get_principle_by_id(principle_id)
    if principle:
        output = {
            "id": principle.id,
            "type": "principle",
            "domain": principle.domain,
            "series": principle.series_code,
            "number": principle.number,
            "constitutional_ref": principle.constitutional_ref,
            "title": principle.title,
            "content": principle.content,
            "line_range": principle.line_range,
            "keywords": principle.metadata.keywords,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    method = engine.get_method_by_id(principle_id)
    if method:
        output = {
            "id": method.id,
            "type": "method",
            "domain": method.domain,
            "title": method.title,
            "content": method.content,
            "line_range": method.line_range,
            "keywords": method.keywords,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    error = ErrorResponse(
        error_code="PRINCIPLE_NOT_FOUND",
        message=f"Principle '{principle_id}' not found",
        suggestions=[
            "Use list_domains to see available domains",
            "Check ID format: meta-core-informational-readiness, coding-quality-testing",
        ],
    )
    return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_list_domains(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle list_domains tool (T15)."""
    domains = engine.list_domains()

    output = {
        "total_domains": len(domains),
        "domains": domains,
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_get_domain_summary(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle get_domain_summary tool (T16)."""
    domain = args.get("domain", "")
    if not domain:
        return [TextContent(type="text", text="Error: domain is required")]

    valid_domains = {
        "constitution",
        "ai-coding",
        "multi-agent",
        "storytelling",
        "multimodal-rag",
        "ui-ux",
        "kmpd",
    }
    if domain not in valid_domains:
        return [
            TextContent(
                type="text",
                text=f"Error: Invalid domain '{domain}'. Valid: {', '.join(sorted(valid_domains))}",
            )
        ]

    summary = engine.get_domain_summary(domain)
    if summary:
        return [TextContent(type="text", text=json.dumps(summary, indent=2))]

    error = ErrorResponse(
        error_code="DOMAIN_NOT_FOUND",
        message=f"Domain '{domain}' not found",
        suggestions=["Use list_domains to see available domains"],
    )
    return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_log_feedback(args: dict) -> list[TextContent]:
    """Handle log_feedback tool (T17)."""
    query = args.get("query", "")
    principle_id = args.get("principle_id", "")
    rating = args.get("rating", 0)

    if not query or not principle_id or not rating:
        return [
            TextContent(
                type="text", text="Error: query, principle_id, and rating are required"
            )
        ]

    if not 1 <= rating <= 5:
        return [TextContent(type="text", text="Error: rating must be 1-5")]

    feedback = Feedback(
        query=_sanitize_for_logging(query),
        principle_id=principle_id,
        rating=rating,
        comment=_sanitize_for_logging(args.get("comment", ""))
        if args.get("comment")
        else None,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    await log_feedback_async(feedback)

    metrics = get_metrics()
    with _rate_limit_lock:
        metrics.feedback_count += 1
        if metrics.avg_feedback_rating is None:
            metrics.avg_feedback_rating = float(rating)
        else:
            metrics.avg_feedback_rating = (
                metrics.avg_feedback_rating * (metrics.feedback_count - 1) + rating
            ) / metrics.feedback_count

    output = {
        "status": "logged",
        "feedback_id": feedback.timestamp,
        "message": "Thank you for your feedback!",
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_get_metrics(args: dict) -> list[TextContent]:
    """Handle get_metrics tool (T18)."""
    metrics = get_metrics()

    gov_overhead = metrics.governance_overhead
    governance_overhead_output = {
        "governance_evaluations": gov_overhead.governance_evaluations,
        "avg_governance_time_ms": round(gov_overhead.avg_governance_time_ms, 2),
        "total_governance_time_ms": round(gov_overhead.total_governance_time_ms, 2),
        "assessment_breakdown": {
            "proceed": gov_overhead.proceed_count,
            "proceed_with_modifications": gov_overhead.proceed_with_modifications_count,
            "escalate": gov_overhead.escalation_count,
        },
    }

    output = {
        "total_queries": metrics.total_queries,
        "avg_retrieval_time_ms": round(metrics.avg_retrieval_time_ms, 2),
        "s_series_trigger_count": metrics.s_series_trigger_count,
        "domain_query_counts": metrics.domain_query_counts,
        "confidence_distribution": metrics.confidence_distribution,
        "feedback_count": metrics.feedback_count,
        "avg_feedback_rating": round(metrics.avg_feedback_rating, 2)
        if metrics.avg_feedback_rating
        else None,
        "governance_overhead": governance_overhead_output,
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]
