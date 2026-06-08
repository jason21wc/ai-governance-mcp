"""Agent install/uninstall handlers and helper functions."""

import asyncio
import json
import logging
import os
import urllib.parse
from pathlib import Path

from mcp.types import TextContent

from ...config import load_settings
from ...models import ErrorResponse
from ...path_resolution import is_within_allowed_scope, looks_like_project
from .._constants import (
    AGENT_METADATA,
    AGENT_TEMPLATE_HASHES,
    AVAILABLE_AGENTS,
    SUBAGENT_EXPLANATION,
)
from .._security import _sanitize_error_message
from .. import _state

logger = logging.getLogger(__name__)


def _verify_template_hash(template_content: str, agent_name: str) -> tuple[bool, str]:
    """Verify agent template content against known-good hash.

    Args:
        template_content: The content of the template file.
        agent_name: Name of the agent to verify.

    Returns:
        Tuple of (is_valid, actual_hash).
        is_valid is True if hash matches or no hash is registered.
    """
    import hashlib

    actual_hash = hashlib.sha256(template_content.encode("utf-8")).hexdigest()
    expected_hash = AGENT_TEMPLATE_HASHES.get(agent_name)

    if expected_hash is None:
        # No hash registered - allow but warn
        return True, actual_hash

    return actual_hash == expected_hash, actual_hash


def _parse_applicable_domains(template_content: str) -> list[str]:
    """Extract applicable_domains list from an agent template's YAML frontmatter.

    F-C-04 Phase-1 implementation (v5.0.6). Uses yaml.safe_load for the
    frontmatter so both inline flow form (`["*"]`) and block form
    (`- "ai-coding"\n  - "ui-ux"`) are handled correctly, and trailing
    comments on the list line are stripped by the YAML parser.

    Returns:
        List of domain keys the agent is marked for. Defaults to ["*"]
        (domain-agnostic) when the field is absent — backward-compatible with
        pre-v5.0.6 templates.

    Edge-case behavior (Phase-1, v5.0.6):
    - Missing field → ["*"] (treat as domain-agnostic; preserves prior behavior)
    - Malformed YAML or parse failure → ["*"] (fail open; WARN+allow semantics)
    - Empty list `[]` → ["*"] (treat as domain-agnostic per convention)
    - Scalar string (e.g., `applicable_domains: ai-coding`) → wrap as
      single-element list `["ai-coding"]` for ergonomic tolerance
    - Block-form YAML list (hyphen-prefixed lines) → parsed correctly by yaml
    - Trailing comment on list line → stripped by yaml
    - Multiple overlapping domains (e.g., `["ai-coding", "ui-ux"]`) → list
      preserved; _check_domain_fit treats project domain as match if any
      overlap exists
    - Invalid domain keys (typo/not in domains.json) → preserved as-is;
      project-domain check simply won't match, triggering WARN. No validation
      against domains.json at Phase-1 — defer strictness to escalation.
    """
    import re

    import yaml

    match = re.match(r"^---\n(.*?)\n---", template_content, re.DOTALL)
    if not match:
        return ["*"]
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return ["*"]
    if not isinstance(fm, dict):
        return ["*"]
    value = fm.get("applicable_domains")
    if value is None:
        return ["*"]
    if isinstance(value, str):
        # Scalar form: wrap single domain name as one-element list
        return [value] if value else ["*"]
    if not isinstance(value, list):
        return ["*"]
    # List form (flow or block): filter to non-empty strings
    domains = [str(d) for d in value if isinstance(d, str) and d]
    return domains if domains else ["*"]


def _check_domain_fit(
    agent_domains: list[str], project_domain: str | None
) -> tuple[bool, str | None]:
    """Check whether an agent applies to a project's active governance domain.

    F-C-04 Phase-1 (v5.0.6): WARN + allow semantics. This function returns
    (fits: bool, warning: str | None). Callers ALWAYS proceed with install;
    the warning is surfaced in the output for visibility. Escalation to
    block-mode requires a `strict_domain_check` flag (not implemented Phase-1).

    Args:
        agent_domains: List from _parse_applicable_domains() — agent's
            declared applicable domains.
        project_domain: Caller-supplied domain string or None when not
            provided (in which case no check is performed).

    Returns:
        (fits, warning). `fits` is True when: (a) no project_domain given,
        (b) agent declares ["*"], or (c) project_domain is in agent_domains.
        `warning` is a human-readable message when fits is False, else None.
    """
    if project_domain is None or not agent_domains:
        return True, None
    if "*" in agent_domains:
        return True, None
    if project_domain in agent_domains:
        return True, None
    return False, (
        f"Agent is marked for domain(s) {agent_domains}; project domain is "
        f"'{project_domain}'. Proceeding anyway (Phase-1: WARN + allow). "
        f"Review agent applicability before relying on it for domain-specific "
        f"tasks."
    )


async def _resolve_caller_project_path(arguments: dict) -> tuple[Path | None, bool]:
    """Resolve the calling session's project path for file-writing tools.

    Any MCP tool that writes files to the CALLER'S project (not the server's
    own directory) must use this resolver instead of Path.cwd(). Path.cwd()
    resolves to the MCP server's working directory, not the calling session's.

    Priority: arguments['project_path'] > MCP roots > AI_GOVERNANCE_MCP_PROJECT > CWD.
    Explicit caller intent always wins over auto-detection. MCP roots may
    point to platform-internal directories (e.g., Cowork uploads folder)
    that differ from the user's actual project.

    Returns (resolved_path, used_cwd_fallback).
    Returns (None, False) if an explicit path is invalid or outside allowed scope.
    """
    # Tier 1: Explicit tool argument (caller intent — highest priority)
    raw = arguments.get("project_path")
    if raw and isinstance(raw, str):
        p = Path(raw).resolve()
        if not p.exists() or not p.is_dir():
            logger.debug(
                "project_path '%s' does not exist or is not a directory (resolved: %s)",
                raw,
                p,
            )
            return None, False
        if not is_within_allowed_scope(p):
            logger.debug("project_path '%s' is outside allowed scope", p)
            return None, False
        return p, False

    # Tier 2: MCP roots (protocol-level auto-detection)
    # Cached per-session to avoid 2s timeout on every call when client
    # doesn't support roots.
    if _state._cached_roots_path is None:
        try:
            import ai_governance_mcp.server as _server_module

            roots_result = await asyncio.wait_for(
                _server_module.server.request_context.session.list_roots(), timeout=2.0
            )
            if roots_result and roots_result.roots:
                if len(roots_result.roots) > 1:
                    logger.debug(
                        "Multiple MCP roots found (%d), using first: %s",
                        len(roots_result.roots),
                        roots_result.roots[0].uri,
                    )
                parsed = urllib.parse.urlparse(str(roots_result.roots[0].uri))
                if parsed.scheme == "file":
                    p = Path(urllib.parse.unquote(parsed.path)).resolve()
                    if p.exists() and p.is_dir() and is_within_allowed_scope(p):
                        _state._cached_roots_path = p
            if _state._cached_roots_path is None:
                _state._cached_roots_path = False  # Checked but no usable root
        except Exception as e:
            logger.debug("MCP list_roots() unavailable: %s", e)
            _state._cached_roots_path = False  # Don't retry

    if isinstance(_state._cached_roots_path, Path):
        return _state._cached_roots_path, False

    # Tier 3: Environment variable
    default = os.environ.get("AI_GOVERNANCE_MCP_PROJECT")
    if default:
        p = Path(default).resolve()
        if not p.exists() or not p.is_dir():
            return None, False
        if not is_within_allowed_scope(p):
            return None, False
        return p, False

    # Tier 4: CWD fallback — only when CWD looks like a project directory.
    # MCP servers run as separate processes; CWD is the SERVER's directory,
    # not the caller's project. Without marker validation, this returns
    # arbitrary directories (bug #50, #86).
    cwd = Path.cwd()
    if looks_like_project(cwd) and is_within_allowed_scope(cwd):
        return cwd, True  # Warning flag still set — callers show advisory
    return None, False  # Not a recognizable project — force explicit path


def _detect_claude_code_environment(project_path: Path | None = None) -> bool:
    """Detect if we're running in a Claude Code environment.

    Checks for indicators that suggest Claude Code is the client:
    1. Presence of .claude/ directory in the project directory
    2. Presence of CLAUDE.md file
    3. Environment variable set by Claude Code

    Args:
        project_path: Explicit project directory to check. Falls back to CWD.

    Returns True if Claude Code environment is detected.
    """
    cwd = project_path if project_path is not None else Path.cwd()

    # Check for .claude directory
    if (cwd / ".claude").is_dir():
        return True

    # Check for CLAUDE.md file
    if (cwd / "CLAUDE.md").is_file():
        return True

    # Check parent directories (up to 3 levels) for .claude or CLAUDE.md
    current = cwd
    for _ in range(3):
        parent = current.parent
        if parent == current:  # Reached root
            break
        if (parent / ".claude").is_dir() or (parent / "CLAUDE.md").is_file():
            return True
        current = parent

    return False


def _get_agent_template_path(agent_name: str) -> Path | None:
    """Get the path to an agent template file.

    Agent templates are stored in documents/agents/ within the package.
    """
    if _state._settings is None:
        _state._settings = load_settings()

    template_path = _state._settings.documents_path / "agents" / f"{agent_name}.md"
    if template_path.is_file():
        return template_path
    return None


def _get_agent_install_path(
    agent_name: str, scope: str = "project", project_path: Path | None = None
) -> Path:
    """Get the installation path for an agent.

    Args:
        agent_name: Name of the agent (e.g., 'orchestrator')
        scope: 'project' for .claude/agents/ or 'user' for ~/.claude/agents/
        project_path: Explicit project directory for scope='project'. Falls back to CWD.

    Returns:
        Path where the agent file should be installed.

    Raises:
        ValueError: If agent_name is not in AVAILABLE_AGENTS or path traversal detected.
    """
    # C2 FIX: Validate agent name against allowlist before path construction
    if agent_name not in AVAILABLE_AGENTS:
        raise ValueError(f"Invalid agent: {agent_name}")

    if scope == "user":
        base_path = Path.home() / ".claude" / "agents"
    else:
        base_path = (
            (project_path if project_path is not None else Path.cwd())
            / ".claude"
            / "agents"
        )

    # C2 FIX: Path containment check prevents path traversal attacks
    final_path = (base_path / f"{agent_name}.md").resolve()
    if not final_path.is_relative_to(base_path.resolve()):
        raise ValueError("Path traversal detected")

    return final_path


async def _handle_install_agent(args: dict) -> list[TextContent]:
    """Handle install_agent tool.

    Per Phase 2B LLM-Agnostic Agent Architecture:
    - Only installs for Claude Code environments
    - Other platforms skip (already have SERVER_INSTRUCTIONS)
    - Uses confirmation flow: preview -> user choice -> action
    """
    agent_name = args.get("agent_name", "")
    scope = args.get("scope", "project")
    confirmed = args.get("confirmed", False)
    show_manual = args.get("show_manual", False)
    project_domain = args.get("domain")  # F-C-04 Phase-1: optional domain fit check

    # Validate agent name
    if agent_name not in AVAILABLE_AGENTS:
        error = ErrorResponse(
            error_code="INVALID_AGENT",
            message=f"Unknown agent: {agent_name}",
            suggestions=[f"Available agents: {', '.join(AVAILABLE_AGENTS)}"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Resolve project path for scope="project"
    project_path = None
    used_cwd_fallback = False
    if scope == "project":
        project_path, used_cwd_fallback = await _resolve_caller_project_path(args)
        if project_path is None:
            error = ErrorResponse(
                error_code="INVALID_PROJECT_PATH",
                message="Specified project_path does not exist or is outside allowed scope",
                suggestions=[
                    "Provide an absolute path to an existing directory within your home directory"
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Check if Claude Code environment
    is_claude = _detect_claude_code_environment(project_path)

    if not is_claude:
        # Non-Claude platform: provide agent content as reference material
        template_path = _get_agent_template_path(agent_name)
        agent_content = ""
        agent_domains_nonclaude: list[str] = ["*"]
        if template_path:
            agent_content = template_path.read_text()
            # F-C-04 Phase-1 (v5.0.6 patch): surface applicable_domains on
            # non-Claude platforms too so adopters see domain-fit metadata
            # before adapting the agent for their harness.
            agent_domains_nonclaude = _parse_applicable_domains(agent_content)
        _, domain_warning_nonclaude = _check_domain_fit(
            agent_domains_nonclaude, project_domain
        )

        output = {
            "status": "not_applicable",
            "platform": "non-claude",
            "agent_name": agent_name,
            "message": (
                f"Subagent installation is only available for Claude Code. "
                f"However, here is the '{agent_name}' agent definition for reference. "
                f"You can adapt this for your platform."
            ),
            "agent_content": agent_content,
            "applicable_domains": agent_domains_nonclaude,
            "adaptation_guidance": (
                "To use this agent definition on other platforms:\n"
                "1. Extract the role and cognitive function from the content above\n"
                "2. Add the role description to your system prompt or agent configuration\n"
                "3. Adapt tool references to match your platform's available tools\n"
                "4. Follow the protocol and output format sections for structured behavior"
            ),
            "governance_guidance": (
                "To use governance effectively:\n"
                "1. Call evaluate_governance() before any action not on the skip list\n"
                "2. Call query_governance() when you need principles to inform decisions\n"
                "3. Follow the assessment (PROCEED/MODIFY/ESCALATE)\n"
                "4. S-Series principles have veto authority"
            ),
        }
        if domain_warning_nonclaude:
            output["domain_warning"] = domain_warning_nonclaude
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Get template path
    template_path = _get_agent_template_path(agent_name)
    if not template_path:
        error = ErrorResponse(
            error_code="TEMPLATE_NOT_FOUND",
            message=f"Subagent template not found: {agent_name}",
            suggestions=["Ensure the MCP server is properly installed"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Read template content
    template_content = template_path.read_text()

    # Verify template integrity
    hash_valid, actual_hash = _verify_template_hash(template_content, agent_name)
    expected_hash = AGENT_TEMPLATE_HASHES.get(agent_name)

    # F-C-04 Phase-1 (v5.0.6): Domain-fit check (WARN + allow)
    agent_domains = _parse_applicable_domains(template_content)
    domain_fits, domain_warning = _check_domain_fit(agent_domains, project_domain)

    # Get install path
    install_path = _get_agent_install_path(agent_name, scope, project_path)

    # Check if already installed and if content differs
    # M2 FIX: Warn user before overwriting existing file with different content
    already_installed = install_path.is_file()
    content_differs = False
    existing_content = None
    if already_installed:
        try:
            existing_content = install_path.read_text()
            content_differs = existing_content != template_content
        except (OSError, PermissionError):
            # Can't read existing file - treat as content differs for safety
            content_differs = True

    # Handle manual instructions request
    if show_manual:
        # Build clear, actionable instructions
        instructions = f"""To install the {agent_name} subagent manually:

1. Create the agents directory:
   mkdir -p {install_path.parent}

2. Save the content (from the "content" field below) to:
   {install_path}

3. Restart Claude Code to activate the subagent

**One-liner alternative** (copy/paste the content field into this command):
```bash
mkdir -p {install_path.parent} && cat > {install_path} << 'EOF'
[paste content here]
EOF
```"""

        output = {
            "status": "manual_instructions",
            "agent_name": agent_name,
            "install_path": str(install_path),
            "instructions": instructions,
            "content": template_content,
            "note": "The 'content' field above contains the exact file contents to save.",
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Handle confirmation flow
    if not confirmed:
        # Return preview with explanation
        scope_desc = (
            "this project" if scope == "project" else "all your projects (user-level)"
        )
        status = "update" if already_installed else "install"

        # M2 FIX: Build warning if overwriting with different content
        overwrite_warning = None
        if content_differs:
            overwrite_warning = (
                "WARNING: Existing file has different content and will be overwritten. "
                "Use show_manual=true to see new content before installing."
            )

        output = {
            "status": "preview",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "already_installed": already_installed,
            "content_differs": content_differs,  # M2 FIX: Expose content diff status
            "integrity": {
                "hash_verified": hash_valid,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
            },
            "explanation": SUBAGENT_EXPLANATION.strip(),
            "action_summary": (
                (f"⚠️  DOMAIN NOTE: {domain_warning}\n\n" if domain_warning else "")
                + f"Will {status} '{agent_name}' subagent for {scope_desc}.\n\n"
                + f"File: {install_path}\n\n"
                + "This subagent will:\n"
                + f"{AGENT_METADATA.get(agent_name, {}).get('action_summary', 'Provide specialized agent behavior')}"
            ),
            "options": {
                "install": "Call install_agent with confirmed=true to install",
                "manual": "Call install_agent with show_manual=true for manual instructions",
                "cancel": "Take no action to cancel",
            },
        }
        if overwrite_warning:
            output["warning"] = overwrite_warning  # M2 FIX: Add warning to output
        if not hash_valid:
            output["security_warning"] = (
                "SECURITY WARNING: Template hash does not match known-good value!\n"
                "The agent template may have been modified. This could indicate:\n"
                "1. An intentional update (maintainer should update AGENT_TEMPLATE_HASHES)\n"
                "2. A supply chain attack (template was tampered with)\n\n"
                "Use show_manual=true to review the content before installing."
            )
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Using CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "Verify install_path above is correct before confirming."
            )
        # F-C-04 Phase-1 (v5.0.6): surface domain-fit metadata + optional warning
        output["applicable_domains"] = agent_domains
        if domain_warning:
            output["domain_warning"] = domain_warning
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Confirmed: perform installation
    try:
        # Create directory if needed
        install_path.parent.mkdir(parents=True, exist_ok=True)

        # Write subagent file
        install_path.write_text(template_content)

        output = {
            "status": "installed",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "integrity": {
                "hash_verified": hash_valid,
                "installed_hash": actual_hash,
            },
            "message": (
                f"Successfully installed '{agent_name}' subagent.\n\n"
                + AGENT_METADATA.get(agent_name, {}).get(
                    "activation_message",
                    f"The '{agent_name}' subagent will activate on your next Claude Code session.\n\n"
                    f"To remove: Use uninstall_agent(agent_name='{agent_name}')",
                )
            ),
        }
        if not hash_valid:
            output["security_warning"] = (
                "Installed with UNVERIFIED hash. Review the installed content."
            )
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Used CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "If the install landed in the wrong project, re-run with "
                "project_path='/path/to/your/project'."
            )
        # F-C-04 Phase-1 (v5.0.6): surface domain-fit metadata on successful install
        output["applicable_domains"] = agent_domains
        if domain_warning:
            output["domain_warning"] = domain_warning
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    except PermissionError:
        output = {
            "status": "error",
            "error": "Permission denied",
            "install_path": str(install_path),
            "suggestion": (
                "Cannot write to the installation path. Try:\n"
                "1. Check directory permissions\n"
                "2. Use show_manual=true to get the content for manual installation\n"
                "3. Try scope='user' to install in your home directory"
            ),
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    except Exception as e:
        error = ErrorResponse(
            error_code="INSTALL_FAILED",
            message=f"Failed to install subagent: {_sanitize_error_message(e)}",
            suggestions=["Use show_manual=true for manual installation instructions"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_uninstall_agent(args: dict) -> list[TextContent]:
    """Handle uninstall_agent tool.

    Removes a previously installed governance agent.
    """
    agent_name = args.get("agent_name", "")
    scope = args.get("scope", "project")
    confirmed = args.get("confirmed", False)

    # Validate agent name
    if agent_name not in AVAILABLE_AGENTS:
        error = ErrorResponse(
            error_code="INVALID_AGENT",
            message=f"Unknown agent: {agent_name}",
            suggestions=[f"Available agents: {', '.join(AVAILABLE_AGENTS)}"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Resolve project path for scope="project"
    project_path = None
    used_cwd_fallback = False
    if scope == "project":
        project_path, used_cwd_fallback = await _resolve_caller_project_path(args)
        if project_path is None:
            error = ErrorResponse(
                error_code="INVALID_PROJECT_PATH",
                message="Specified project_path does not exist or is outside allowed scope",
                suggestions=[
                    "Provide an absolute path to an existing directory within your home directory"
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Get install path
    install_path = _get_agent_install_path(agent_name, scope, project_path)

    # Check if installed
    if not install_path.is_file():
        output = {
            "status": "not_installed",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "message": f"Subagent '{agent_name}' is not installed at {install_path}",
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Handle confirmation flow
    if not confirmed:
        output = {
            "status": "confirm_uninstall",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "warning": (
                f"This will remove the '{agent_name}' subagent "
                f"({AGENT_METADATA.get(agent_name, {}).get('short_description', 'specialized agent')}).\n\n"
                "After removal:\n"
                f"- The '{agent_name}' behavior will no longer be automatically available\n"
                "- You can reinstall at any time\n"
                "- SERVER_INSTRUCTIONS will still provide governance guidance\n\n"
                "To confirm: Call uninstall_agent with confirmed=true"
            ),
        }
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Using CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "Verify install_path above is correct before confirming."
            )
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Confirmed: perform uninstallation
    try:
        install_path.unlink()

        output = {
            "status": "uninstalled",
            "agent_name": agent_name,
            "scope": scope,
            "install_path": str(install_path),
            "message": (
                f"Successfully removed '{agent_name}' subagent.\n\n"
                "The subagent will no longer be active in new Claude Code sessions.\n"
                "Governance tools are still available via the MCP server.\n\n"
                f"To reinstall: Use install_agent(agent_name='{agent_name}')"
            ),
        }
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Used CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "If the uninstall targeted the wrong project, verify manually."
            )
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    except Exception as e:
        error = ErrorResponse(
            error_code="UNINSTALL_FAILED",
            message=f"Failed to uninstall subagent: {_sanitize_error_message(e)}",
            suggestions=["Manually delete the file", f"Path: {install_path}"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]


async def _handle_list_agents(args: dict) -> list[TextContent]:
    """Handle list_agents tool — pure data projection from AGENT_METADATA."""
    include_details = args.get("include_details", False)

    agents = []
    for name in sorted(AVAILABLE_AGENTS):
        meta = AGENT_METADATA.get(name)
        if not meta:
            continue
        entry = {
            "name": name,
            "short_description": meta["short_description"],
            "applicable_domains": meta["applicable_domains"],
            "canonical_source": meta["canonical_source"],
        }
        if include_details:
            entry["action_summary"] = meta["action_summary"]
        agents.append(entry)

    output = {
        "total_agents": len(agents),
        "agents": agents,
        "cross_platform_note": (
            "Use install_agent(agent_name='...') to retrieve the full agent "
            "definition with platform-specific adaptation guidance."
        ),
    }

    return [TextContent(type="text", text=json.dumps(output, indent=2))]
