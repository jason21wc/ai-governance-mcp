---
id: ref-ai-coding-mcp-server-testing
title: "MCP Server Tool Handler Testing Pattern"
domain: ai-coding
tags: [testing, mcp, asyncio, tool-handlers, integration-testing]
status: current
entry_type: direct
summary: "Pattern for testing MCP server tool handlers with async fixtures, mock managers, and TextContent parsing"
created: 2026-03-26
last_verified: 2026-03-26
maturity: budding
decay_class: framework
source: "ai-governance-mcp/tests/test_server.py — proven across governance and context engine servers"
related: [ref-ai-coding-pytest-fixture-patterns]
---

## Context

MCP servers expose tools via JSON-RPC. Testing these requires async test infrastructure, mock data managers, and parsing TextContent responses. This pattern handles the common case of a server with a retrieval engine that returns scored results.

## Artifact

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_server():
    """Create server with mocked retrieval engine."""
    engine = MagicMock()
    engine.retrieve.return_value = RetrievalResult(
        query="test",
        principles=[],
        methods=[],
        references=[],
        domain_scores={},
    )
    server = GovernanceServer(engine=engine)
    return server, engine

@pytest.mark.asyncio
async def test_query_governance(mock_server):
    server, engine = mock_server
    result = await server.call_tool("query_governance", {
        "query": "how should I test this?",
        "max_results": 5,
    })
    # MCP tools return list[TextContent]
    assert len(result) >= 1
    text = result[0].text
    # Structured responses are JSON
    if text.startswith("{"):
        data = json.loads(text)
        assert "query" in data
    # Engine was called with correct params
    engine.retrieve.assert_called_once()
```

## Lessons Learned

- MCP server `call_tool` is async — always use `@pytest.mark.asyncio`
- Tool responses are `list[TextContent]` not raw dicts — access `.text` attribute
- Mock the retrieval engine, not individual index files — test at the right abstraction level
- When server formats results as markdown (not JSON), test for string patterns rather than parsing
- Server-level tests are integration tests — they exercise the full tool handler → engine → formatter chain

## Cross-References

- Principles: coding-quality-testing-integration, coding-process-validation-gates
- Methods: §5.2 (Testing Integration), §5.2.7 (Test Framework Selection)
- See also: ref-ai-coding-pytest-fixture-patterns
