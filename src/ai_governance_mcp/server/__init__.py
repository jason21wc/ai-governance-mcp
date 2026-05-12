"""MCP Server for AI Governance document retrieval.

MCP server with 15 tools for hybrid retrieval of governance principles.

This package re-exports the public API. Application logic lives in _app.py;
handler logic in handlers/; state, logging, security, constants in their
respective _ modules.
"""

# -- Submodules importable as package attributes (e.g. server._state) --------
from . import _state as _state  # noqa: F401 — tests access server._state
from . import _security as _security  # noqa: F401 — tests access server._security

# -- App core (server instance, dispatch, entry points) ----------------------
from ._app import (
    call_tool as call_tool,
    list_tools as list_tools,
    main as main,
    run_server as run_server,
    server as server,
)

# -- Config re-exports (patch targets) ---------------------------------------
from ..config import (
    Settings as Settings,
    _find_project_root as _find_project_root,
    load_settings as load_settings,
)
from ..path_resolution import (
    is_within_allowed_scope as is_within_allowed_scope,
    looks_like_project as looks_like_project,
)
from ..models import Metrics as Metrics

# -- Constants ---------------------------------------------------------------
from ._constants import (
    AGENT_METADATA as AGENT_METADATA,
    AGENT_TEMPLATE_HASHES as AGENT_TEMPLATE_HASHES,
    AUDIT_LOG_MAX_SIZE as AUDIT_LOG_MAX_SIZE,
    AVAILABLE_AGENTS as AVAILABLE_AGENTS,
    CRITICAL_SAFETY_KEYWORDS as CRITICAL_SAFETY_KEYWORDS,
    GOVERNANCE_REMINDER as GOVERNANCE_REMINDER,
    MAX_LOG_CONTENT_LENGTH as MAX_LOG_CONTENT_LENGTH,
    MAX_QUERY_LENGTH as MAX_QUERY_LENGTH,
    RATE_LIMIT_TOKENS as RATE_LIMIT_TOKENS,
    SCAFFOLD_STANDARD_EXTRAS as SCAFFOLD_STANDARD_EXTRAS,
    SERVER_INSTRUCTIONS as SERVER_INSTRUCTIONS,
    _IMPERATIVE_ACTION_VERBS as _IMPERATIVE_ACTION_VERBS,
)

# -- Logging -----------------------------------------------------------------
from ._logging import (
    _audit_log as _audit_log,
    _reasoning_log as _reasoning_log,
    _validate_log_path as _validate_log_path,
    _write_log_sync as _write_log_sync,
    get_audit_log as get_audit_log,
    get_reasoning_log as get_reasoning_log,
    log_feedback_entry as log_feedback_entry,
    log_governance_audit as log_governance_audit,
    log_query as log_query,
    log_reasoning_sync as log_reasoning_sync,
)

# -- Security ----------------------------------------------------------------
from ._security import (
    ServerInstructionsSecurityError as ServerInstructionsSecurityError,
    _check_rate_limit as _check_rate_limit,
    _sanitize_error_message as _sanitize_error_message,
    _sanitize_for_logging as _sanitize_for_logging,
    _validate_server_instructions as _validate_server_instructions,
)

# -- State -------------------------------------------------------------------
from ._state import (
    _build_critical_5 as _build_critical_5,
    _build_domain_floor as _build_domain_floor,
    _build_universal_floor as _build_universal_floor,
    _load_tiers_config as _load_tiers_config,
    get_engine as get_engine,
    get_metrics as get_metrics,
)

# -- Handlers: governance ----------------------------------------------------
from .handlers.governance import (
    _detect_safety_concerns as _detect_safety_concerns,
    _determine_confidence as _determine_confidence,
    _handle_evaluate_governance as _handle_evaluate_governance,
    _handle_log_governance_reasoning as _handle_log_governance_reasoning,
    _handle_verify_governance as _handle_verify_governance,
    _is_keyword_in_safe_context as _is_keyword_in_safe_context,
)

# -- Handlers: retrieval -----------------------------------------------------
from .handlers.retrieval import (
    _format_retrieval_result as _format_retrieval_result,
    _handle_get_domain_summary as _handle_get_domain_summary,
    _handle_get_metrics as _handle_get_metrics,
    _handle_get_principle as _handle_get_principle,
    _handle_list_domains as _handle_list_domains,
    _handle_log_feedback as _handle_log_feedback,
    _handle_query_governance as _handle_query_governance,
)

# -- Handlers: agents --------------------------------------------------------
from .handlers.agents import (
    _check_domain_fit as _check_domain_fit,
    _detect_claude_code_environment as _detect_claude_code_environment,
    _get_agent_install_path as _get_agent_install_path,
    _get_agent_template_path as _get_agent_template_path,
    _handle_install_agent as _handle_install_agent,
    _handle_uninstall_agent as _handle_uninstall_agent,
    _parse_applicable_domains as _parse_applicable_domains,
    _resolve_caller_project_path as _resolve_caller_project_path,
    _verify_template_hash as _verify_template_hash,
)

# -- Handlers: analysis ------------------------------------------------------
from .handlers.analysis import (
    _handle_analyze_feedback_loop as _handle_analyze_feedback_loop,
)

# -- Handlers: scaffold ------------------------------------------------------
from .handlers.scaffold import (
    _escape_yaml_value as _escape_yaml_value,
    _handle_capture_reference as _handle_capture_reference,
    _handle_scaffold_project as _handle_scaffold_project,
)
