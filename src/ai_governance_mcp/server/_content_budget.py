"""Size-bounded content allocation shared by the two governance retrieval tools.

WHY THIS IS A LEAF MODULE. It imports nothing from the package, so both
``handlers/governance.py`` and ``handlers/retrieval.py`` can use it without either
depending on the other. A direct handler-to-handler import would work today
(neither imports the other) but inverts the dependency and drags the safety-scan
and keyword-adjudicator chains into the light retrieval path — and one future
import in the other direction makes it a cycle.

WHY BOUNDING IS NOT OPTIONAL. Returning full bodies unbounded is a documented
outage, not a hypothetical cost: ``evaluate_governance`` once embedded every
matched principle's full markdown for up to 10 principles and produced 60-112 KB
results that exceeded the MCP per-tool-result cap and hard-errored with no inline
verdict (commit 4f49e7a, Cowork report + 3 reproductions). NOTE ON THAT CAP: the
outage is observed fact, but this repo does not pin the cap's numeric value
anywhere, so treat "~25,000 tokens" below as the working estimate it is, not as a
figure verified against the MCP spec. The budgets are sized well under it either
way.

CORPUS MEASUREMENTS — measured once here, and this is where to re-measure.

SCOPE OF THAT CLAIM, stated precisely because the first version overstated it. A
coherence audit checked and found the raw figures still restated in six other
surfaces (``handlers/retrieval.py``, ``API.md``, a test, and three memory files),
so "the single source for them" was an aspiration, not a fact. What this docstring
actually governs is narrower and true: **the three budget constants in
``_constants.py`` derive from these numbers and do not restate them.** Elsewhere the
figures appear as explanation, and a re-measure means grepping for them — the
numbers to grep are 3,518 / 6,876 / 13,894 / 908 / 2,793 / 21,270 / 13,172 / 4,922.
Do not add a seventh copy (``meta-core-single-source-of-truth``, Art. I §2).

Measured 2026-08-11 against the live index, AFTER the extractor boundary fix
(5802cf8) shrank oversized bodies:

    principles  n=156   median 3,518   p90 6,876   max 13,894
    methods     n=957   median   908   p90 2,793   max 21,270
    S-Series    n=3 (constitution only)  total 13,172   largest 4,922

- 10 principles at MEDIAN  ->  35,180 chars (~8,800 tok)   comfortable
- 10 LARGEST principles    -> 100,079 chars (~25,000 tok)  at the working cap

That second line is why a budget is required at the DEFAULT ``max_results`` of 10,
not merely at the 50 ceiling. Reasoning from the median alone says full text is
free; the tail says otherwise, and the tail is what takes the server down.

Note what the method row says, because an earlier comment here got it backwards:
methods are NOT typically the longest units — the median method (908) is roughly a
quarter of the median principle (3,518). Only the single largest unit in the corpus
is a method. The case for keeping method bodies out of ``query_governance`` rests
on count × tail, not on typical size: ten methods at p90 is 27,930 chars, which
exceeds that tool's entire budget on its own.
"""

_TRUNCATION_NOTE = (
    "…[truncated to fit response size — call {tool}('{uid}') for full text]"
)


def allocate_content(
    items,
    budget: int,
    *,
    fetch_tool: str = "get_principle",
    per_unit_max: int | None = None,
) -> tuple[dict[int, str | None], list[str]]:
    """Allocate full bodies within ``budget`` chars, priority class first then by score.

    ``items`` are ``(unit, score, priority)`` where ``unit`` needs only ``.id`` and
    ``.content``. Both ``Principle`` and ``Method`` satisfy that, which is the point
    of the tuple shape — the previous 4-tuple carried a ``relevance`` field the
    allocator never read, and that unread field was the only reason this could not
    already be shared.

    Order: ``priority`` first, then highest score. Priority exists so triggered
    S-Series bodies stay visible on ESCALATE even when they do not top the score
    ranking (``all_principles`` is hierarchy-ordered, not score-ordered).

    A body over ``per_unit_max`` (or over ``budget`` when unset) is truncated at a
    paragraph boundary with an inline marker naming the exact fetch call. A body
    that would overflow the REMAINING budget is reference-only (``None``).

    ``per_unit_max`` closes a real hole **only when it is set BELOW ``budget``**:
    without it, a single oversized unit is truncated to ``budget - 200`` and then
    consumes ~99.5% of the budget, starving every other unit of content. That is not
    theoretical — before 5802cf8 a 74,441-char principle did exactly this, or fell to
    ``None`` depending on allocation order.

    Read that condition literally, because one caller does not meet it.
    ``query_governance`` passes ``min(corpus_ceiling, budget)``, which equals
    ``budget`` today, so ``cap == budget`` and the starvation case above is NOT
    prevented on that path — measured: a 25,000-char body truncates to 19,877 and
    takes 99.4% of a 20,000 budget, withholding everything else. It is unreachable
    with the current corpus (largest principle 13,894, so no body can exceed the
    budget and the truncation branch is dead there), and any body near the budget
    starves the tail whether or not it was truncated. Do not read the parameter's
    presence at a call site as proof the protection is active; check the two numbers.

    Returns ``(content_by_index, fetch_ids)``; ``fetch_ids`` names every unit whose
    body was omitted or truncated, in allocation order, so a caller can always tell
    the difference between "this is the whole thing" and "there is more".
    """
    alloc_order = sorted(
        range(len(items)),
        key=lambda i: (
            0 if items[i][2] else 1,  # priority first
            -items[i][1],  # then highest score
        ),
    )
    content_by_index: dict[int, str | None] = {}
    fetch_ids: list[str] = []
    used = 0
    cap = per_unit_max if per_unit_max is not None else budget

    for i in alloc_order:
        unit = items[i][0]
        body = unit.content
        if len(body) > cap:
            # The 200-char reserve holds the truncation marker. It currently renders
            # to 117 chars with a 45-char id, leaving ~83 chars of headroom — pinned
            # by a test, because overflowing the reserve silently downgrades this unit
            # from "truncated and inlined" to "withheld behind a pointer".
            limit = cap - 200
            cut = body.rfind("\n\n", 0, limit)
            if cut < limit // 2:
                # Prefer a paragraph boundary (the rfind above) — that is why we look
                # for one. Here there is none in the back half, so take the hard cut:
                # a body with no blank line to break on leaves nothing better to do,
                # and cutting at limit//2 would throw away half the allowance.
                cut = limit
            # A cut inside a ``` fence leaves it unterminated, so a markdown viewer
            # renders the marker and everything after it as one code block. Needs a
            # body over the budget to happen at all, which the current corpus cannot
            # produce (max 13,894); harmless to a caller reading raw text.
            body = (
                body[:cut].rstrip()
                + "\n\n"
                + _TRUNCATION_NOTE.format(tool=fetch_tool, uid=unit.id)
            )
        if used + len(body) <= budget:
            content_by_index[i] = body
            used += len(body)
            if body is not unit.content:  # was truncated
                fetch_ids.append(unit.id)
        else:
            content_by_index[i] = None
            fetch_ids.append(unit.id)
    return content_by_index, fetch_ids
