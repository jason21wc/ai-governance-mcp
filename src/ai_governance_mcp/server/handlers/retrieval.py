"""Retrieval-oriented tool handlers.

Handles: query_governance (T13), get_principle (T14), list_domains (T15),
get_domain_summary (T16), log_feedback (T17), get_metrics (T18),
search_references.
"""

import json
import re
from datetime import datetime, timezone

from mcp.types import TextContent

from ...models import (
    ConfidenceLevel,
    ErrorResponse,
    Feedback,
    QueryLog,
    RetrievalResult,
)
from ...retrieval import RetrievalEngine
from .._constants import (
    MAX_QUERY_LENGTH,
    PER_UNIT_CONTENT_MAX_CHARS,
    QUERY_ECHO_MAX_CHARS,
    QUERY_PRINCIPLE_CONTENT_BUDGET_CHARS,
    REFERENCE_SUMMARY_MAX_CHARS,
)
from .._content_budget import allocate_content
from .._logging import log_feedback_async, log_query_async
from .._security import _rate_limit_lock, _sanitize_for_logging
from .._state import get_metrics


_CONFIDENCE_RANK = {
    ConfidenceLevel.LOW: 0,
    ConfidenceLevel.MEDIUM: 1,
    ConfidenceLevel.HIGH: 2,
}


def _best_confidence(result: RetrievalResult) -> ConfidenceLevel | None:
    """Return the highest confidence across all result types."""
    levels = (
        [p.confidence for p in result.constitution_principles]
        + [p.confidence for p in result.domain_principles]
        + [m.confidence for m in result.methods]
    )
    if not levels:
        return None
    return max(levels, key=lambda c: _CONFIDENCE_RANK.get(c, 0))


def _best_raw_score(result: RetrievalResult) -> float | None:
    """Return the highest combined_score across principles and methods."""
    scores = (
        [p.combined_score for p in result.constitution_principles]
        + [p.combined_score for p in result.domain_principles]
        + [m.combined_score for m in result.methods]
    )
    return max(scores) if scores else None


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
    valid_domains = set(engine.index.domains.keys())
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
        references_returned=[sr.reference.id for sr in result.references],
        s_series_triggered=result.s_series_triggered,
        retrieval_time_ms=result.retrieval_time_ms,
        top_confidence=_best_confidence(result),
        best_score=_best_raw_score(result),
    )
    await log_query_async(query_log)

    output = _format_retrieval_result(result)
    return [TextContent(type="text", text=output)]


_WITHHELD_NOTE = (
    "*Body withheld to fit the response budget — "
    "call `get_principle('{uid}')` for the full text.*"
)

# A unit whose indexed body is empty. `Principle.content` is a plain `str` with no
# min_length, so "" is representable, and without this the render emitted a bare blank
# line — no marker, no id, no footer entry, indistinguishable from a complete short
# principle. That is precisely the silent class this whole change exists to remove, so
# it gets a visible statement rather than an accurate-but-invisible blank.
_EMPTY_BODY_NOTE = (
    "*This unit's indexed body is EMPTY — not withheld, not truncated. "
    "Suspect an extraction fault; check the source with `get_principle('{uid}')`.*"
)

# Methods render as a title line only. This is a TOKEN-BUDGET decision, not an
# application of §4.6.1 Assessment Responsibility Layers: that clause governs what
# `evaluate_governance` must hand the judgment layer, and it does not reach this tool.
#
# The argument is COUNT x TAIL, not typical size. An earlier version of this comment
# called methods "typically the longest units in the corpus", which is backwards: the
# median method is 908 chars against a median principle of 3,518. What makes them
# unaffordable here is that a query returns up to `max_results` of them alongside the
# principles, and their tail is heavy — ten methods at p90 is 27,930 chars, which
# exceeds this tool's entire body budget on its own. Figures: `_content_budget.py`.
_METHOD_FETCH_HINT = (
    "*Method bodies are not inlined — call `get_principle('<method-id>')` "
    "for the full procedure.*"
)


_STRUCTURE_CHARS = re.compile(r"[\r\n  \v\f\x85]+")


def _clip(text: str, limit: int) -> str:
    """Flatten ``text`` to one line and clip it to ``limit`` chars, marking the cut.

    FLATTENING IS THE SECURITY-RELEVANT HALF, and it was missing when this helper first
    shipped. Two independent reviewers found the same hole: bounding *length* while leaving
    *structure* intact lets a short caller-supplied string forge response sections. Measured
    — a 108-char `query`, far inside the 300-char cap so no clip marker even fires, rendered
    as a fake `**Assessment:** PROCEED` line, a fake `## Constitutional Principles` heading,
    and an unterminated fence that swallowed the rest of the response for any markdown
    consumer. The same shape in a hand-edited reference `summary` forged a section in 82
    chars.

    `query` is validated for length only (`MAX_QUERY_LENGTH`) and rendered raw, so the
    renderer is the only place this can be caught. U+2028/U+2029 are included because
    ``split("\\n")`` does not treat them as breaks but markdown renderers do — a mismatch
    that hides the payload from any line-oriented check upstream.

    The marked clip is retained: an unmarked cut is the 600-char defect this module was
    rewritten to remove, and re-introducing one on a different field would be the same bug
    in a new place. Note the return can exceed ``limit`` by the marker's width; the cap
    bounds the caller's contribution, not the final string.
    """
    flattened = _STRUCTURE_CHARS.sub(" ", text)
    if len(flattened) <= limit:
        return flattened
    return f"{flattened[:limit].rstrip()}… [clipped at {limit} chars]"


def _render_body(body: str | None, uid: str) -> str:
    """Render one principle's body, or a statement of why there isn't one.

    Three outcomes, and a caller must be able to tell them apart: the body arrived,
    the body was withheld to fit the budget, or the indexed body is empty. Only the
    first is a normal result; the other two used to be a bare `...` and a bare blank
    line respectively, which is how a partial answer passed for a complete one.
    """
    if body is None:
        return _WITHHELD_NOTE.format(uid=uid)
    if not body.strip():
        return _EMPTY_BODY_NOTE.format(uid=uid)
    return body


def _allocate_result_content(result) -> tuple[dict[int, str | None], list[str]]:
    """Allocate principle bodies for one rendered response, both lists sharing a budget.

    Constitution and domain principles are allocated TOGETHER because they are
    rendered into a single response answering to a single protocol cap; budgeting them
    separately would let the two lists sum past it.

    Indices are into the concatenation ``constitution_principles + domain_principles``
    — see ``_DOMAIN_INDEX_OFFSET`` at the render site.

    Priority uses the broad ``series_code == "S"`` flag so a safety principle keeps its
    body when the tail is being dropped. That is deliberately NOT
    ``evaluate_governance``'s veto-eligibility test (class gate + score gate +
    ``VETO_INELIGIBLE_S_SERIES_IDS``): here the question is "which body survives a
    budget squeeze?", not "does this principle carry veto authority?". Retrieval must
    not be read as ratifying either flag as the S-Series definition.

    WHAT PRIORITY COSTS, STATED PLAINLY. Priority sorts strictly ahead of score, so a
    low-scoring S-Series body can displace a higher-scoring one. A review flagged this
    against an earlier comment that claimed allocation was score-ordered and the top
    match always arrived whole; that claim was false and has been corrected. The bound,
    measured against the live corpus (3 S-Series principles, largest 4,922, total
    13,172, all constitution):

    - 1 S-Series retrieved: 4,922 + the largest possible principle 13,894 = 18,816,
      inside the 20,000 budget — so the top match provably always survives.
    - 2 or 3 retrieved: 9,709 or 13,172 spent first, and a top match above the
      remainder is withheld (named, with its fetch call — not silently dropped).

    So the displacement is real but needs two-plus safety matches AND a large top match.
    Kept rather than removed, with the alternative recorded so this reads as a decision:
    dropping priority here would make the score contract unconditional, but a fresh
    security audit independently verified that safety bodies never silently drop under
    the current rule and treated that as a property worth having. At 3 principles the
    cost is bounded and measurable; at a materially larger S-Series set, revisit — the
    bound above is the thing to re-measure, not a fact to re-quote.
    """
    scored = list(result.constitution_principles) + list(result.domain_principles)
    items = [
        (sp.principle, sp.combined_score, sp.principle.series_code == "S")
        for sp in scored
    ]
    # The corpus ceiling (24,000) is ABOVE this tool's budget (20,000). Passing it
    # unreconciled is a trap, and here is the mechanism precisely — an earlier version of
    # this comment described it wrongly, which a review caught:
    #   - body 20,001..24,000  ->  `len(body) > cap` is FALSE, so it is never truncated;
    #                              it then fails the budget check and is dropped whole.
    #   - body above 24,000    ->  truncated to ~23,800, THEN fails the budget check and
    #                              is dropped anyway.
    # Either way an oversized unit vanishes behind a pointer instead of arriving marked.
    #
    # Be honest about what the min() buys: it equals `budget` today, which is byte-for-byte
    # what omitting the argument already does (`cap` defaults to `budget`). So it is NOT a
    # behaviour fix — it is an explicit statement of the relationship, which keeps the
    # 24,000 ceiling binding if the budget is ever raised above it, and it makes the
    # dependency visible at the call site instead of hiding in a default.
    per_unit_max = min(PER_UNIT_CONTENT_MAX_CHARS, QUERY_PRINCIPLE_CONTENT_BUDGET_CHARS)
    return allocate_content(
        items,
        QUERY_PRINCIPLE_CONTENT_BUDGET_CHARS,
        fetch_tool="get_principle",
        per_unit_max=per_unit_max,
    )


def _format_retrieval_result(result) -> str:
    """Format retrieval result as readable markdown.

    Principle bodies are returned in full within a shared char budget, with a named
    fetch path for anything withheld or truncated. Before session-302 every body was
    cut at 600 chars with a bare ``...`` — no marker, no id, no way for the caller to
    learn there was more or how to get it. That silent amputation is what BACKLOG #325
    identified as the blocker on the #313 migration's third layer.
    """
    lines = []
    bodies, fetch_ids = _allocate_result_content(result)
    # Domain principles occupy the tail of the shared index space. Named, because an
    # off-by-one here silently prints one principle's body under another's heading.
    _DOMAIN_INDEX_OFFSET = len(result.constitution_principles)

    if result.s_series_triggered:
        lines.append("## S-SERIES TRIGGERED - Safety/Ethics Principles Apply")
        lines.append("")

    # Announce a degraded retrieval mode BEFORE THE RESULTS (not literally first — the
    # S-Series header above precedes it, which is pre-existing and practically moot
    # since a missing index returns no principles for S-Series to trigger on). A caller
    # cannot see server logs, so without this a degraded result is indistinguishable
    # from a healthy one and reduced/zero recall silently reads as "nothing relevant
    # found" (the #216 failure mode).
    if not getattr(result, "index_loaded", True):
        lines.append("## GOVERNANCE INDEX MISSING — retrieval returns NOTHING")
        lines.append(
            "No index could be loaded. Every query returns an empty principle "
            "set, which looks identical to 'no principles apply.' "
            "Build it with `python -m ai_governance_mcp.extractor` "
            "(set AI_GOVERNANCE_INDEX_PATH if the index lives outside the repo)."
        )
        lines.append("")
    elif not getattr(result, "semantic_available", True):
        lines.append(
            "## DEGRADED — keyword-only retrieval (semantic search unavailable)"
        )
        lines.append(
            "Recall is reduced: paraphrased queries may return nothing. "
            "Rebuild the index and check server logs for the cause."
        )
        lines.append("")

    # Echo the query, but do not let the caller's own input be an unbounded slice of the
    # response. `query` accepts up to MAX_QUERY_LENGTH (10,000) chars, all of which used
    # to land here verbatim — outside the body budget, so invisible to it. The echo
    # exists so a caller can confirm what was searched; 300 chars does that.
    lines.append(f"**Query:** {_clip(result.query, QUERY_ECHO_MAX_CHARS)}")
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
        for i, sp in enumerate(result.constitution_principles):
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
            lines.append(_render_body(bodies.get(i), p.id))
            lines.append("")

    if result.domain_principles:
        lines.append("## Domain Principles")
        for j, sp in enumerate(result.domain_principles):
            p = sp.principle
            lines.append(f"### [{sp.confidence.value.upper()}] {p.id}: {p.title}")
            series_info = f" | Series: {p.series_code}" if p.series_code else ""
            lines.append(
                f"*Domain: {p.domain}{series_info} | Combined: {sp.combined_score:.2f}*"
            )
            lines.append("")
            lines.append(_render_body(bodies.get(_DOMAIN_INDEX_OFFSET + j), p.id))
            lines.append("")

    if result.methods:
        lines.append("## Applicable Methods")
        for sm in result.methods:
            m = sm.method
            lines.append(f"- **{m.id}:** {m.title} (confidence: {sm.confidence.value})")
        lines.append("")
        lines.append(_METHOD_FETCH_HINT)
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
                # Gated at RENDER time, not only at capture. `capture_reference` caps
                # summaries at 300 chars, but that cap binds only what this server
                # writes — entries already on disk are user data (the library is a
                # separate, hand-editable repo) and the live maximum is already 426.
                # Trusting the write-side cap to bound the read side is the same mistake
                # as trusting a build-time scan to bound egress.
                lines.append(f"  {_clip(r.summary, REFERENCE_SUMMARY_MAX_CHARS)}")
        lines.append("")

    if not result.constitution_principles and not result.domain_principles:
        lines.append(
            "*No matching principles found. Try rephrasing your query or specifying a domain.*"
        )

    if result.constitution_principles or result.domain_principles:
        lines.append("---")
        # One place the caller can see everything that did NOT arrive complete. The
        # inline markers say it per-principle; this says it once, so a caller reading
        # only the end of the response still learns the result is partial.
        if fetch_ids:
            lines.append(
                f"**Bodies omitted or truncated to fit the response budget "
                f"({QUERY_PRINCIPLE_CONTENT_BUDGET_CHARS:,} chars):** "
                + ", ".join(f"`{uid}`" for uid in fetch_ids)
                + ". Fetch any of them in full with `get_principle('<id>')`."
            )
            lines.append("")
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

    ref = engine.get_reference_by_id(principle_id)
    if ref:
        output = {
            "id": ref.id,
            "type": "reference",
            "domain": ref.domain,
            "title": ref.title,
            "summary": ref.summary,
            "content": ref.content,
            "tags": ref.tags,
            "status": ref.status,
            "maturity": ref.maturity,
            "source_path": ref.source_path,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    error = ErrorResponse(
        error_code="PRINCIPLE_NOT_FOUND",
        message=f"ID '{principle_id}' not found in principles, methods, or references",
        suggestions=[
            "Use list_domains to see available domains",
            "Principle IDs: meta-core-informational-readiness, coding-quality-testing",
            "Reference IDs: ref-ai-coding-playwright-auth",
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

    valid_domains = set(engine.index.domains.keys())
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


async def _handle_search_references(
    engine: RetrievalEngine, args: dict
) -> list[TextContent]:
    """Handle search_references tool — dedicated reference library search."""
    query = args.get("query", "")
    if not query:
        return [TextContent(type="text", text="Error: query is required")]

    if len(query) > MAX_QUERY_LENGTH:
        return [
            TextContent(
                type="text",
                text=f"Error: query too long (max {MAX_QUERY_LENGTH} chars)",
            )
        ]

    domain = args.get("domain")
    tags = args.get("tags")
    # Defensively normalize the (untrusted) stack arg at the ingress boundary:
    # tolerate a scalar, coerce elements to lowercase strings, drop empties,
    # cap length. Prevents a malformed payload from crashing the set-comprehension
    # in search_references. (`tags` has a pre-existing equivalent gap — out of scope.)
    stack_raw = args.get("stack")
    if isinstance(stack_raw, str):
        stack_raw = [stack_raw]
    stack = (
        [str(s).strip().lower() for s in stack_raw[:10] if str(s).strip()]
        if isinstance(stack_raw, list)
        else None
    )
    max_results = args.get("max_results")
    if max_results is not None:
        try:
            max_results = min(max(int(max_results), 1), 20)
        except (ValueError, TypeError):
            max_results = 5
    else:
        max_results = 5

    results = engine.search_references(
        query=query, domain=domain, tags=tags, max_results=max_results, stack=stack
    )

    output = {
        # Same bound as query_governance's echo, for the same reason — an audit noted this
        # sibling path was left uncapped while the stated rationale ("do not let the
        # caller's own input be an unbounded slice of the response") applied verbatim.
        # This response is JSON-encoded, so there is no markdown-structure risk here; the
        # cap is about volume only.
        "query": _clip(query, QUERY_ECHO_MAX_CHARS),
        "domain_filter": domain,
        "tag_filter": tags,
        "stack_filter": stack,
        "result_count": len(results),
        "results": [
            {
                "id": r.reference.id,
                "title": r.reference.title,
                "summary": _clip(
                    r.reference.summary or "", REFERENCE_SUMMARY_MAX_CHARS
                ),
                "domain": r.reference.domain,
                "tags": r.reference.tags,
                "applies_to": r.reference.applies_to,
                "status": r.reference.status,
                "maturity": r.reference.maturity,
                "confidence": r.confidence.value,
                "score": round(r.combined_score, 3),
            }
            for r in results
        ],
        "hint": "Use get_principle(principle_id) to retrieve full reference content.",
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


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
            "review": gov_overhead.review_count,
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
