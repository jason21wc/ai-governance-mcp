---
id: ref-ai-coding-pytest-fixture-patterns
title: "Pytest Fixture Patterns for MCP Server Testing"
domain: ai-coding
tags: [testing, pytest, fixtures, mocking, mcp, sentence-transformers]
status: current
entry_type: direct
summary: "Proven fixture patterns for testing MCP servers with sentence-transformers mocking and sample governance data"
created: 2026-03-26
last_verified: 2026-04-24
maturity: evergreen
decay_class: framework
source: "ai-governance-mcp/tests/conftest.py — battle-tested across 1000+ tests"
related: [ref-ai-coding-mcp-server-testing, ref-ai-coding-vitest-hoisted-mocks]
---

## Context

When building an MCP server that uses sentence-transformers for semantic search, you need fixtures that mock the embedding model (to avoid downloading 90MB+ models in CI), provide sample governance data structures, and handle async test patterns. These patterns were developed through 1000+ tests and multiple CI environments.

## Artifact

```python
# Mock SentenceTransformer to avoid model downloads in tests.
# Patch at the source library, NOT the user-site import path: for lazy-loaded
# models (imported inside property accessors), the user module's namespace
# doesn't have the name bound yet at patch time — only the source library
# binding survives the lazy resolution.
@pytest.fixture
def mock_embedding_model():
    """Mock that returns deterministic embeddings."""
    with patch("sentence_transformers.SentenceTransformer") as mock_cls:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(10, 384).astype(np.float32)
        mock_cls.return_value = mock_model
        yield mock_model

# Sample domains.json for testing domain discovery
@pytest.fixture
def sample_domains_json(tmp_path):
    """Create a minimal domains.json for extraction tests."""
    docs = tmp_path / "documents"
    docs.mkdir()
    domains = {
        "domains": [{
            "name": "test-domain",
            "description": "Test domain",
            "principles_file": "test-principles-v1.0.0.md",
            "methods_file": "test-methods-v1.0.0.md",
            "priority": 50
        }]
    }
    (docs / "domains.json").write_text(json.dumps(domains))
    return tmp_path

# Async MCP tool handler testing pattern
@pytest.mark.asyncio
async def test_tool_handler():
    """Pattern for testing MCP server tool calls."""
    result = await server.call_tool("tool_name", {"param": "value"})
    assert len(result) == 1
    content = json.loads(result[0].text)
    assert "expected_key" in content
```

## Lessons Learned

- Always mock SentenceTransformer at the **source library** (`sentence_transformers.SentenceTransformer`), not at the user-site import path — lazy-loaded models defer the import to first-access, and the source library is where the binding gets resolved at call time
- Use `np.random.rand()` with fixed dimensions matching your model (384 for BGE-small-en-v1.5 / all-MiniLM-L6-v2)
- MCP tool handlers return `list[TextContent]` — parse `.text` as JSON for structured responses
- Use `tmp_path` fixture for file-based tests to avoid polluting the real filesystem
- Add `readonly=False` and `readonly_message=None` to mock managers that get serialized to JSON

## Do / Don't

**Do:** Mock `SentenceTransformer` at the source library: `patch("sentence_transformers.SentenceTransformer")`. This is the correct pattern for lazy-loaded models — models are imported inside property accessors or first-use methods, so the user-site namespace doesn't hold the binding at patch time; only the source library does. Use `np.random.rand(len(texts), 384)` with `side_effect` to return correct batch shapes matching your embedding model dimensions. Confirmed across 1000+ tests in this project; authoritative references: `documents/title-10-ai-coding-cfr.md` §5.2.8 (CORRECT pattern block), LEARNING-LOG 2025-12-27.

**Don't:** Mock at the user-site import path `patch("ai_governance_mcp.retrieval.SentenceTransformer")` for lazy-loaded models — the name isn't bound in the user module's namespace until first access, so the mock doesn't intercept. (Corrected 2026-04-24: earlier versions of this file had Do/Don't inverted; project tests + CFR + LEARNING-LOG all use source-library patching.)

## Cross-References

- Principles: coding-quality-testing-integration
- Methods: §5.2 (Testing Integration), §5.2.5 (Test Organization Patterns)
- See also: ref-ai-coding-mcp-server-testing
