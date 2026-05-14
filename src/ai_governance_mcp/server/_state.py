"""Mutable server state and accessor functions.

All module-level mutable variables live here. Functions using ``global``
for these variables are co-located so the keyword invariant holds.
Other submodules access state via ``from . import _state`` and read
``_state._settings`` etc. at call time (never re-export bindings).
"""

import json
import logging
from pathlib import Path

from ..config import Settings, ensure_directories, load_domains_registry
from ..models import Metrics
from ..retrieval import RetrievalEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mutable globals
# ---------------------------------------------------------------------------

_settings: Settings | None = None
_engine: RetrievalEngine | None = None
_metrics: Metrics | None = None
_tiers_config: dict | None = None
_tiers_loaded: bool = False
_cached_roots_path: Path | None | bool = None


# ---------------------------------------------------------------------------
# Accessors (these ASSIGN to globals, so they must live here)
# ---------------------------------------------------------------------------


def get_engine() -> RetrievalEngine:
    """Get or create the retrieval engine."""
    global _settings, _engine, _metrics
    if _engine is None:
        import ai_governance_mcp.server as _srv

        _settings = _srv.load_settings()
        ensure_directories(_settings)
        _engine = RetrievalEngine(_settings)
        _metrics = Metrics()
    return _engine


def get_domain_names() -> list[str]:
    """Get sorted list of available domain names.

    Uses engine index if loaded, otherwise reads from domain registry
    without triggering full engine initialization.
    """
    if _engine is not None:
        return sorted(_engine.index.domains.keys())

    import ai_governance_mcp.server as _srv

    settings = _settings or _srv.load_settings()
    domains = load_domains_registry(settings)
    return sorted(d.name for d in domains)


def get_metrics() -> Metrics:
    """Get metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics


# ---------------------------------------------------------------------------
# Tiers configuration
# ---------------------------------------------------------------------------


def _load_tiers_config() -> dict | None:
    """Load tiers.json configuration for universal floor injection.

    Returns the parsed config, or None if the file doesn't exist.
    Cached in module-level _tiers_config after first load.
    Uses _tiers_loaded flag to distinguish "never attempted" from "absent/failed".
    """
    global _tiers_config, _tiers_loaded
    if _tiers_loaded:
        return _tiers_config

    import ai_governance_mcp.server as _srv

    settings = _settings or _srv.load_settings()
    tiers_path = settings.documents_path / "tiers.json"
    if not tiers_path.exists():
        logger.debug(
            "tiers.json not found at %s — universal floor disabled", tiers_path
        )
        _tiers_loaded = True
        return None

    try:
        with open(tiers_path) as f:
            _tiers_config = json.load(f)
        logger.info("Loaded tiers config from %s", tiers_path)
        _tiers_loaded = True
        return _tiers_config
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load tiers.json: %s", e)
        _tiers_loaded = True
        return None


def _build_universal_floor(tiers_config: dict) -> list[dict]:
    """Build compact floor items from tiers config (universal + behavioral).

    Returns a list of check items in compact format:
    {"type": "principle"|"method"|"subagent_check"|"behavioral", "id": str|null, "check": str}
    """
    floor_section = tiers_config.get("universal_floor", {})
    items: list[dict] = []

    for p in floor_section.get("principles", []):
        items.append(
            {
                "type": "principle",
                "id": p.get("id"),
                "check": p.get("check", ""),
            }
        )

    for m in floor_section.get("methods", []):
        items.append(
            {
                "type": "method",
                "ref": m.get("ref"),
                "id": m.get("id"),
                "check": m.get("check", ""),
            }
        )

    subagent = floor_section.get("subagent_check")
    if subagent:
        items.append(
            {
                "type": "subagent_check",
                "check": subagent.get("check", ""),
            }
        )

    # Behavioral floor — interaction-style directives (additive reinforcement)
    behavioral = tiers_config.get("behavioral_floor", {})
    for d in behavioral.get("directives", []):
        items.append(
            {
                "type": "behavioral",
                "id": d.get("id"),
                "check": d.get("check", ""),
            }
        )

    return items


def _build_critical_5(tiers_config: dict) -> list[dict]:
    """Build scaffold-format reasoning items from the critical_5 tier.

    Returns items with keys: type="critical", id, principle_ref, label, scaffold.
    """
    section = tiers_config.get("critical_5", {})
    items: list[dict] = []
    for item in section.get("items", []):
        items.append(
            {
                "type": "critical",
                "id": item.get("id", ""),
                "principle_ref": item.get("principle_ref", ""),
                "label": item.get("label", ""),
                "scaffold": item.get("scaffold", ""),
            }
        )
    return items


def _build_domain_floor(tiers_config: dict, domains_detected: list[str]) -> list[dict]:
    """Build domain-specific floor items activated by domain detection.

    Returns items only for detected domains that have floor entries in tiers config.
    """
    domain_floors = tiers_config.get("domain_floors", {})
    if not domain_floors:
        return []

    items: list[dict] = []
    for domain_name in domains_detected:
        floor = domain_floors.get(domain_name)
        if not isinstance(floor, dict):
            continue

        for p in floor.get("principles", []):
            items.append(
                {
                    "type": "domain_principle",
                    "id": p.get("id"),
                    "check": p.get("check", ""),
                    "domain": domain_name,
                }
            )

        for m in floor.get("methods", []):
            item: dict = {
                "type": "domain_method",
                "id": m.get("id"),
                "check": m.get("check", ""),
                "domain": domain_name,
            }
            if m.get("ref"):
                item["ref"] = m["ref"]
            items.append(item)

    return items


# ---------------------------------------------------------------------------
# Test helper
# ---------------------------------------------------------------------------


def reset() -> None:
    """Reset all mutable state — for test fixtures only."""
    global \
        _settings, \
        _engine, \
        _metrics, \
        _tiers_config, \
        _tiers_loaded, \
        _cached_roots_path
    _settings = None
    _engine = None
    _metrics = None
    _tiers_config = None
    _tiers_loaded = False
    _cached_roots_path = None
