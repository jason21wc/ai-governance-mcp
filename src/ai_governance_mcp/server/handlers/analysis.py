"""Handler for analyze_feedback_loop tool — thin reader of precomputed analysis."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mcp.types import TextContent

from .. import _state


def _get_analysis_path() -> Path:
    """Return path to precomputed analysis JSON."""
    import ai_governance_mcp.server as _srv

    settings = _state._settings or _srv.load_settings()
    return settings.logs_path / "feedback_loop_analysis.json"


_STALENESS_DAYS = 30


async def _handle_analyze_feedback_loop(args: dict) -> list[TextContent]:
    """Read precomputed feedback loop analysis and return formatted content."""
    path = _get_analysis_path()

    if not path.exists():
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "Analysis file not found",
                        "suggestion": (
                            "Run: python scripts/analyze_feedback_loop.py --print-summary"
                        ),
                        "path": str(path),
                    },
                    indent=2,
                ),
            )
        ]

    data = json.loads(path.read_text())

    section = args.get("section")
    if section:
        if section not in data:
            available = [k for k in data.keys()]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": f"Section '{section}' not found",
                            "available_sections": available,
                        },
                        indent=2,
                    ),
                )
            ]
        data = {"computed_at": data.get("computed_at"), section: data[section]}

    warning = ""
    computed_at = data.get("computed_at")
    if computed_at:
        try:
            computed = datetime.fromisoformat(computed_at)
            age = datetime.now(timezone.utc) - computed
            if age > timedelta(days=_STALENESS_DAYS):
                warning = (
                    f"\n\n**WARNING: Analysis is outdated ({age.days} days old).** "
                    f"Re-run: python scripts/analyze_feedback_loop.py --print-summary"
                )
        except (ValueError, TypeError):
            pass

    return [
        TextContent(
            type="text",
            text=json.dumps(data, indent=2) + warning,
        )
    ]
