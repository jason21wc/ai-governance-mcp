"""Evidence boundaries and public delivery of constitutional method context."""

import json
from unittest.mock import patch

from ai_governance_mcp.governance_context import (
    attach_context,
    compact_context,
    full_context,
    resolve_context,
)
from ai_governance_mcp.models import (
    DomainIndex,
    Method,
    Principle,
    RetrievalResult,
    ScoredMethod,
)


def method(**updates):
    return Method(
        id="coding-method-work",
        domain="ai-coding",
        title="Work",
        content="## 1 Work",
        line_range=(1, 1),
        **updates,
    )


def principle(
    pid="meta-core-readiness", title="Readiness", domain="constitution", **updates
):
    return Principle(
        id=pid, domain=domain, title=title, content="body", line_range=(1, 1), **updates
    )


def context_for(field):
    item = method()
    attach_context(
        [item],
        f"## 1 Work\n**Implements:** {field}",
        "documents/title-10-ai-coding-cfr.md",
    )
    # A fixture method must include the declaration in its actual body range.
    item.line_range = (1, 2)
    attach_context(
        [item],
        f"## 1 Work\n**Implements:** {field}",
        "documents/title-10-ai-coding-cfr.md",
    )
    return item


def test_legacy_index_deserializes_without_claiming_no_relationships():
    old = {
        "domain": "ai-coding",
        "last_extracted": "2026-01-01",
        "methods": [method().model_dump(exclude={"governance_context"})],
    }
    loaded = DomainIndex.model_validate(old).methods[0]
    assert loaded.governance_context is None
    assert compact_context(loaded)["availability"] == "unavailable"
    assert full_context(loaded) == {"availability": "unavailable"}


def test_ancestors_skipped_headings_and_code_examples_are_separate():
    source = """# Document
**Implements:** Root
## 1 Overview
**Constitutional Basis:**
- Parent (`meta-core-readiness`)

```markdown
**Implements:** Fake
### 1.1 Fake method
```
### 1.1 Work
An Implements: Incidental is prose.
**Implements:** Direct
#### Details
**Constitutional Basis:** Detail
### 1.2 Sibling
**Implements:** Sibling
"""
    item = method()
    item.line_range = (11, 15)
    original = item.model_dump()
    attach_context([item], source, "documents/rules-of-procedure.md")
    context = item.governance_context
    assert context.framework_layer == "rules_of_procedure"
    assert context.section == "1.1"
    assert [(h.title, h.line) for h in context.enclosing_headings] == [
        ("Document", 1),
        ("1 Overview", 3),
    ]
    assert [(d.origin, d.line_range) for d in context.declarations] == [
        ("ancestor", (2, 2)),
        ("ancestor", (4, 5)),
        ("method", (13, 13)),
        ("method", (15, 15)),
    ]
    assert "Fake" not in str(context.declarations)
    assert item.model_dump(exclude={"governance_context"}) == {
        k: v for k, v in original.items() if k != "governance_context"
    }


def test_exact_resolution_alias_scope_ambiguity_and_unresolved_evidence():
    item = context_for(
        "Readiness, old-readiness, Cross, other-core-cross, Duplicate, Missing, 1-3, coding-method-other, Bold (`other-core-cross`)"
    )
    other_method = method()
    other_method.id = "coding-method-other"
    principles = [
        principle(aliases=["old-readiness"]),
        principle("other-core-cross", "Cross", "other"),
        principle("meta-core-dup1", "Duplicate"),
        principle("meta-core-dup2", "Duplicate"),
    ]
    resolve_context([item, other_method], principles)
    refs = item.governance_context.declarations[0].references
    assert [r.principle_id for r in refs] == [
        "meta-core-readiness",
        "meta-core-readiness",
        None,
        "other-core-cross",
        None,
        None,
        None,
        None,
        "other-core-cross",
    ]
    assert [r.reason for r in refs[4:8]] == [
        "ambiguous",
        "not_found",
        "range",
        "method_target",
    ]
    assert refs[5].text == "Missing"
    resolve_context(
        [item],
        principles
        + [principle("meta-core-shadow", "Shadow", aliases=["old-readiness"])],
    )
    assert item.governance_context.declarations[0].references[1].reason == "ambiguous"


def test_parenthetic_commas_and_markup_do_not_split_references():
    item = context_for(
        "**Readiness** (Art. I, § 1), Missing (former principle) — explanation"
    )
    resolve_context([item], [principle()])
    refs = item.governance_context.declarations[0].references
    assert len(refs) == 2
    assert refs[0].principle_id == "meta-core-readiness"
    assert refs[1].status == "unresolved"


def test_compact_budget_counts_escaped_unicode_and_whole_ids():
    from ai_governance_mcp.governance_context import _wire_size

    item = context_for(", ".join(f"meta-core-{i}-" + "x" * 70 for i in range(20)))
    principles = [principle(f"meta-core-{i}-" + "x" * 70) for i in range(20)]
    resolve_context([item], principles)
    item.governance_context.source_document = "文" * 600
    projected = compact_context(item)
    assert len(json.dumps(projected)) <= 512
    assert _wire_size(projected) <= 512
    assert projected["omitted"] > 0
    assert projected["principle_ids"]
    assert set(projected["principle_ids"]) <= {p.id for p in principles}
    assert projected["detail"] == "get_principle"
    assert projected["authority"] == "normative_not_enforcement"
    assert projected["rule"] == "Methods cannot override principles"


def test_query_normal_and_fallback_preserve_context_and_total_budget():
    from ai_governance_mcp.server.handlers.retrieval import _format_retrieval_result
    from ai_governance_mcp.server._constants import GOVERNANCE_REMINDER

    item = context_for("Readiness")
    resolve_context([item], [principle()])
    result = RetrievalResult(
        query="work",
        domains_detected=[],
        retrieval_time_ms=1,
        methods=[ScoredMethod(method=item, combined_score=0.8)],
    )
    normal = _format_retrieval_result(result)
    assert '"principle_ids": ["meta-core-readiness"]' in normal
    item.title = "x" * 40000
    compact = _format_retrieval_result(result)
    assert "Compact response" in compact
    assert len(compact + GOVERNANCE_REMINDER) <= 32000
    assert '"principle_ids": ["meta-core-readiness"]' in compact
    assert item.id in compact


async def test_get_full_and_evaluate_compact(
    reset_server_state, test_settings, monkeypatch
):
    from ai_governance_mcp.retrieval import RetrievalEngine
    from ai_governance_mcp.server.handlers import governance, retrieval

    item = context_for("Readiness, Stale")
    resolve_context([item], [principle()])
    engine = RetrievalEngine(test_settings)
    monkeypatch.setattr(
        engine,
        "retrieve",
        lambda *a, **kw: RetrievalResult(
            query="work",
            domains_detected=[],
            retrieval_time_ms=1,
            methods=[ScoredMethod(method=item, combined_score=0.8)],
        ),
    )
    output = await governance._handle_evaluate_governance(
        engine, {"planned_action": "Organize project notes"}
    )
    projected = json.loads(output[0].text)["relevant_methods"][0]["governance_context"]
    assert projected == compact_context(item)
    # Measure the actual nested pretty JSON, including its indentation.
    start = output[0].text.index("{", output[0].text.index('"governance_context"'))
    decoded, size = json.JSONDecoder().raw_decode(output[0].text[start:])
    assert decoded == projected
    assert size <= 512
    monkeypatch.setattr(engine, "get_principle_by_id", lambda _: None)
    monkeypatch.setattr(engine, "get_method_by_id", lambda _: item)
    detail = await retrieval._handle_get_principle(engine, {"principle_id": item.id})
    assert json.loads(detail[0].text)["governance_context"] == json.loads(
        json.dumps(full_context(item))
    )
    item.governance_context = None
    detail = await retrieval._handle_get_principle(engine, {"principle_id": item.id})
    assert json.loads(detail[0].text)["governance_context"] == {
        "availability": "unavailable"
    }


def test_extractor_attaches_metadata_without_changing_embedding_input(test_settings):
    from ai_governance_mcp.extractor import DocumentExtractor
    from ai_governance_mcp.models import DomainConfig

    with patch("ai_governance_mcp.extractor.load_domains_registry", return_value=[]):
        extractor = DocumentExtractor(test_settings)
    source = test_settings.documents_path / "rules-of-procedure.md"
    source.write_text(
        "# Document\n**Implements:** Readiness\n## 1 Work\nBody\n### 1.1 Child\nBody"
    )
    config = DomainConfig(
        name="constitution",
        display_name="Constitution",
        principles_file="constitution.md",
        methods_file=source.name,
    )
    with patch("ai_governance_mcp.extractor.attach_context"):
        before = extractor._extract_methods(config)
    after = extractor._extract_methods(config)
    resolve_context(after, [principle()])
    assert [m.model_dump(exclude={"governance_context"}) for m in before] == [
        m.model_dump(exclude={"governance_context"}) for m in after
    ]
    assert [extractor._get_method_embedding_text(m) for m in before] == [
        extractor._get_method_embedding_text(m) for m in after
    ]
    assert all(m.governance_context.declarations for m in after)


def test_search_synonyms_are_not_cross_domain_id_aliases():
    from ai_governance_mcp.models import PrincipleMetadata

    item = context_for("Cross synonym")
    resolve_context(
        [item],
        [
            principle(
                "other-cross",
                "Other title",
                "other",
                metadata=PrincipleMetadata(aliases=["Cross synonym"]),
            )
        ],
    )
    ref = item.governance_context.declarations[0].references[0]
    assert ref.status == "unresolved"


def test_conflicting_exact_title_and_id_are_not_silently_resolved():
    item = context_for("Readiness (`meta-core-other`)")
    resolve_context([item], [principle(), principle("meta-core-other", "Other")])
    ref = item.governance_context.declarations[0].references[0]
    assert ref.status == "unresolved"
    assert ref.reason == "conflicting_evidence"
    assert ref.principle_id is None


def test_comma_title_single_mixed_and_ambiguous_segmentation():
    safety = principle(
        "meta-safety-non-maleficence", "Non-Maleficence, Privacy & Security"
    )
    for declaration, expected in [
        ("Non-Maleficence, Privacy & Security (Constitution)", [safety.id]),
        (
            "Readiness, Non-Maleficence, Privacy & Security (Constitution)",
            ["meta-core-readiness", safety.id],
        ),
    ]:
        item = context_for(declaration)
        resolve_context([item], [principle(), safety])
        assert [
            r.principle_id for r in item.governance_context.declarations[0].references
        ] == expected
    item = context_for("Alpha, Beta")
    resolve_context(
        [item],
        [
            principle("p-a", "Alpha"),
            principle("p-b", "Beta"),
            principle("p-ab", "Alpha, Beta"),
        ],
    )
    refs = item.governance_context.declarations[0].references
    assert len(refs) == 1
    assert refs[0].reason == "ambiguous_partition"


def test_bullet_declaration_stops_at_next_field_and_resolves_inheritance():
    source = """# Parent
**Implements:**
- Readiness
- **Applies To:** This is not a governing reference
## 1 Work
body
"""
    item = method()
    item.line_range = (5, 6)
    attach_context([item], source, "documents/rules-of-procedure.md")
    resolve_context([item], [principle()])
    declarations = item.governance_context.declarations
    assert len(declarations) == 1
    assert declarations[0].origin == "ancestor"
    assert declarations[0].raw == "**Implements:**\n- Readiness"
    assert declarations[0].references[0].principle_id == "meta-core-readiness"


def test_title_parentheses_and_plus_delimiter_are_preserved():
    item = context_for("Readiness + Bias Awareness & Fairness (Equal Protection)")
    bias = principle("meta-safety-bias", "Bias Awareness & Fairness (Equal Protection)")
    resolve_context([item], [principle(), bias])
    assert [
        r.principle_id for r in item.governance_context.declarations[0].references
    ] == [
        "meta-core-readiness",
        bias.id,
    ]


def test_explicit_ids_with_parenthetical_explanations_preserve_scope():
    item = context_for(
        "`meta-core-readiness` (targets the cause), "
        "`old-readiness` (former ID), `other-core-cross` (cross-domain evidence)"
    )
    resolve_context(
        [item],
        [
            principle(aliases=["old-readiness"]),
            principle("other-core-cross", "Cross", "other"),
        ],
    )
    assert [
        r.principle_id for r in item.governance_context.declarations[0].references
    ] == [
        "meta-core-readiness",
        "meta-core-readiness",
        "other-core-cross",
    ]


def test_multiple_complete_title_partitions_remain_unresolved():
    item = context_for("Alpha, Beta, Gamma")
    resolve_context(
        [item],
        [
            principle("p-abg", "Alpha, Beta, Gamma"),
            principle("p-ab", "Alpha, Beta"),
            principle("p-g", "Gamma"),
        ],
    )
    assert (
        item.governance_context.declarations[0].references[0].reason
        == "ambiguous_partition"
    )


def test_normalized_comma_title_keeps_and_variant_together():
    item = context_for("Non-Maleficence, Privacy and Security (Constitution)")
    safety = principle(
        "meta-safety-non-maleficence", "Non-Maleficence, Privacy & Security"
    )
    resolve_context([item], [safety])
    refs = item.governance_context.declarations[0].references
    assert len(refs) == 1
    assert refs[0].principle_id == safety.id


def test_conflicting_two_explicit_identities_remain_unresolved():
    item = context_for("`meta-core-readiness` (`meta-core-other`)")
    resolve_context([item], [principle(), principle("meta-core-other", "Other")])
    ref = item.governance_context.declarations[0].references[0]
    assert ref.status == "unresolved"
    assert ref.reason == "conflicting_evidence"
