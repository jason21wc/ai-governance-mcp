"""Shared test helpers for AI Governance MCP Server tests."""


def extract_json_from_response(text: str) -> str:
    """Extract JSON portion from response, stripping governance reminder.

    Tool responses include a governance reminder footer after the JSON/markdown content.
    This helper extracts just the primary content for JSON parsing in tests.
    """
    separator = "\n\n---\n⚖️"
    if separator in text:
        return text.split(separator)[0]
    return text
