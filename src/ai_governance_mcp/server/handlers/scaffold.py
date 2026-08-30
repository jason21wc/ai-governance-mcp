"""Scaffold and reference library handlers."""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from mcp.types import TextContent

from ...config import load_settings
from ...path_resolution import _git_common_dir, is_within_allowed_scope
from ...content_patterns import (
    SUSPICIOUS_PATTERNS,
    matches_any,
    normalize_text_for_security,  # noqa: F401 — re-exported for existing callers
)
from ...models import ErrorResponse
from .._constants import (
    SCAFFOLD_CORE_FILES,
    SCAFFOLD_SAAS_OPS_EXTRAS,
    SCAFFOLD_STANDARD_EXTRAS,
    SCAFFOLD_STAMP_FORMAT,
    SCAFFOLD_TEMPLATE_CHANGELOG,
    SCAFFOLD_TEMPLATE_VERSION,
)
from .._security import _sanitize_error_message
from .. import _state
from .agents import _resolve_caller_project_path

logger = logging.getLogger(__name__)

# Credential patterns specific to reference library content scanning.
# These complement the extractor's SUSPICIOUS_PATTERNS (prompt injection,
# shell commands, etc.) with secret-detection patterns relevant to code
# snippets and configuration examples that appear in reference entries.
_CREDENTIAL_PATTERNS = {
    "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "generic_secret": re.compile(
        r"""(?:api[_-]?key|api[_-]?secret|secret[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key)"""
        r"""[\s]*[=:]\s*['"][A-Za-z0-9+/=_\-]{20,}['"]""",
        re.IGNORECASE,
    ),
    "jwt_token": re.compile(
        r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+"
    ),
    "pem_private_key": re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
    ),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
}


def _is_within(path: Path, root: Path) -> bool:
    """True when `path` sits under `root` (both resolved). Used to tell a caller whether
    a captured entry is somewhere the extractor will actually find it."""
    try:
        return path.resolve().is_relative_to(root.resolve())
    except (OSError, ValueError):
        return False


def scan_reference_content(text: str) -> list[dict]:
    """Scan reference entry content for security threats.

    Checks against both the extractor's SUSPICIOUS_PATTERNS (prompt injection,
    hidden instructions, shell commands, data exfiltration, base64 payloads)
    and credential-specific patterns for reference library entries.

    Returns a list of warning dicts with pattern_type and matched content.
    Empty list means clean.
    """
    warnings: list[dict] = []
    in_code_block = False

    for line_num, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        # Raw AND normalized. This is the `capture_reference` INGRESS — the point
        # where outside material enters a corpus that is later served to a model —
        # so losing a detection here is the most expensive place to lose one.
        # Normalizing alone drops payloads the raw line matches; see
        # `content_patterns.security_views`.
        for pattern_type, pattern in SUSPICIOUS_PATTERNS.items():
            if matches_any(pattern, line):
                if in_code_block and pattern_type not in (
                    "prompt_injection",
                    "hidden_instruction",
                ):
                    continue
                warnings.append(
                    {
                        "line": line_num,
                        "pattern_type": pattern_type,
                        "content": line.strip()[:100],
                    }
                )

        for pattern_type, pattern in _CREDENTIAL_PATTERNS.items():
            if pattern.search(line):
                warnings.append(
                    {
                        "line": line_num,
                        "pattern_type": pattern_type,
                        "content": line.strip()[:100],
                    }
                )

    return warnings


# Memory-file basenames that existed at the project ROOT under the
# pre-v2.62.0 code layout. A grandfathered project re-running the scaffold
# must not get _ai-context/ duplicates: the root original counts as
# "already exists". Scoped to these names only — a root README.md must NOT
# suppress _ai-context/README.md (the document loader).
_GRANDFATHERED_ROOT_BASENAMES = frozenset(
    {
        "SESSION-STATE.md",
        "PROJECT-MEMORY.md",
        "LEARNING-LOG.md",
        "BACKLOG.md",
        "OPERATIONS.md",
    }
)


def _grandfathered_root_counterpart(cwd: Path, relative_path: str) -> Path | None:
    """Return the legacy root-layout path that shadows an _ai-context/ memory file."""
    if not relative_path.startswith("_ai-context/"):
        return None
    basename = Path(relative_path).name
    if basename not in _GRANDFATHERED_ROOT_BASENAMES:
        return None
    return cwd / basename


# --- Template versioning / sync mode (BACKLOG #190) -------------------------

# Matches the birth stamp written as line 1 of every scaffolded file. Strict on
# purpose: sync must never echo an unparsed line from a project file back into a
# tool result an LLM reads (a `## Ignore all previous instructions` heading is
# valid markdown). Only the three captured groups ever leave this function.
_STAMP_RE = re.compile(
    r"^<!--\s*scaffold:\s*(?P<project_type>code|document)/(?P<kit_tier>core|standard|saas-ops)\s+"
    r"template-v(?P<template_version>\d+\.\d+\.\d+)\s+\d{4}-\d{2}-\d{2}\s*-->\s*$"
)

# How many bytes of a project file we are willing to read to find its stamp.
# The stamp is line 1; this is a hard ceiling, not a search window.
_STAMP_READ_LIMIT = 512


def _semver(version: str) -> tuple[int, int, int]:
    """Parse `X.Y.Z` into a comparable tuple. Returns (0, 0, 0) on garbage."""
    try:
        major, minor, patch = version.split(".")
        return (int(major), int(minor), int(patch))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _stamp_content(content: str, project_type: str, kit_tier: str, date: str) -> str:
    """Prepend the birth stamp to a rendered template."""
    stamp = SCAFFOLD_STAMP_FORMAT.format(
        project_type=project_type,
        kit_tier=kit_tier,
        template_version=SCAFFOLD_TEMPLATE_VERSION,
        date=date,
    )
    return f"{stamp}\n{content}"


def _read_stamp(path: Path) -> dict | None:
    """Read a scaffolded file's birth stamp. Returns None if absent/unparseable.

    Never returns file content — only the validated fields from _STAMP_RE.
    """
    try:
        if path.is_symlink() or not path.is_file():
            return None
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            first_line = handle.read(_STAMP_READ_LIMIT).split("\n", 1)[0]
    except OSError:
        return None
    match = _STAMP_RE.match(first_line.strip())
    return match.groupdict() if match else None


def _changelog_since(template_version: str | None, project_type: str) -> list[dict]:
    """Template changelog entries newer than a file's birth stamp.

    `template_version=None` (an unstamped, pre-#190 project) returns every entry
    for this project type — we cannot know what it was born from, so we show the
    whole history and say so rather than guessing.
    """
    since = _semver(template_version) if template_version else (0, 0, 0)
    return [
        entry
        for entry in SCAFFOLD_TEMPLATE_CHANGELOG
        if project_type in entry["applies_to"] and _semver(entry["version"]) > since
    ]


def _assemble_kit_files(project_type: str, kit_tier: str) -> list[tuple[str, str]]:
    """Return the (relative_path, template) tuples for a project_type + kit_tier.

    Single source of tier-resolution logic. Both the show_manual branch and the
    manifest-build path call this — keeping them in sync structurally so a new tier
    cannot be added to one path and silently forgotten in the other (the duplicated
    tier-gating bug that would drop a tier's files in sandboxed/show_manual usage).

    Tier composition (additive):
    - core: the core memory files (in _ai-context/ for both types — unified
      layout v2.62.0) + the root loaders (code: AGENTS.md body + the CLAUDE.md and
      GEMINI.md overlays that import it, v2.63.0; document: README).
    - standard: core + the standard extras (code: CFR §1.5.2 kit — ARCHITECTURE,
      SPECIFICATION, checklist, _ai-context/BACKLOG.md; document: _ai-context/BACKLOG.md).
    - saas-ops: standard + the per-app SaaS-ops SOP stub (BACKLOG #71 Phase C2),
      code-only (document has no saas-ops extras, yielding document standard).
    """
    files = list(SCAFFOLD_CORE_FILES.get(project_type, []))
    if kit_tier in ("standard", "saas-ops"):
        files.extend(SCAFFOLD_STANDARD_EXTRAS.get(project_type, []))
    if kit_tier == "saas-ops":
        files.extend(SCAFFOLD_SAAS_OPS_EXTRAS.get(project_type, []))
    return files


# Memory files present in BOTH project types' core kits — the probe set used to
# locate a birth stamp before we know the project's type. Root paths cover the
# grandfathered pre-v2.62.0 layout.
_STAMP_PROBE_PATHS = (
    "_ai-context/SESSION-STATE.md",
    "_ai-context/PROJECT-MEMORY.md",
    "_ai-context/LEARNING-LOG.md",
    "SESSION-STATE.md",
    "PROJECT-MEMORY.md",
    "LEARNING-LOG.md",
)


def _discover_stamp(cwd: Path) -> dict | None:
    """Find this project's birth stamp by probing the type-agnostic memory files."""
    for relative_path in _STAMP_PROBE_PATHS:
        stamp = _read_stamp(cwd / relative_path)
        if stamp:
            return stamp
    return None


async def _handle_scaffold_sync(
    args: dict, cwd: Path, project_name: str, used_cwd_fallback: bool
) -> list[TextContent]:
    """mode='sync' — report kit staleness for an ALREADY-scaffolded project.

    Report-only. Never writes, never diffs file content against a template, and
    never echoes a line of project content into the result. See the design note
    on SCAFFOLD_TEMPLATE_CHANGELOG in _constants.py for why a structural diff was
    rejected (measured 23 false positives / 0 true positives on this very repo).

    Two findings only:
      1. file-set drift  — kit files added to the template since this project was
         scaffolded and never created here (exact; zero false positives).
      2. template changelog — maintainer-written entries newer than the file's
         birth stamp, carrying the INTENT behind each change.
    """
    stamp = _discover_stamp(cwd)

    if stamp:
        # The stamp is authoritative — it records how this project was ACTUALLY
        # scaffolded. Never let a caller's guess override it.
        project_type = stamp["project_type"]
        kit_tier = stamp["kit_tier"]
        born_at = stamp["template_version"]
    else:
        # No stamp (scaffolded before #190, or hand-made). We must NOT guess the
        # type: reporting the code kit's changes into a document project would
        # tell an AI to add a software-delivery frame to a hotel folder — the
        # exact harm the v2.61.0 neutral templates fixed.
        if "project_type" not in args:
            error = ErrorResponse(
                error_code="SYNC_PROJECT_TYPE_UNKNOWN",
                message=(
                    "This project has no scaffold stamp (it predates template "
                    "versioning, or was created by hand), so its project_type cannot "
                    "be determined. Pass project_type explicitly to sync it."
                ),
                suggestions=[
                    "Re-run with project_type='code' for a software repository",
                    "Re-run with project_type='document' for a folder-based project "
                    "(research, deals, operations) — passing 'code' by mistake would "
                    "report software-delivery sections as missing",
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]
        project_type = args["project_type"]
        kit_tier = args.get("kit_tier", "core")
        born_at = None

    # 1. File-set drift — kit files that do not exist here, in either layout.
    missing_files = []
    for relative_path, _template in _assemble_kit_files(project_type, kit_tier):
        full_path = (cwd / relative_path).resolve()
        if not full_path.is_relative_to(cwd):
            continue
        legacy = _grandfathered_root_counterpart(cwd, relative_path)
        if full_path.is_file() or (legacy is not None and legacy.is_file()):
            continue
        missing_files.append(relative_path)

    # 2. Template changes this project was born before.
    pending = _changelog_since(born_at, project_type)

    output = {
        "status": "sync_report",
        "mode": "sync",
        "project_name": project_name,
        "project_root": str(cwd),
        "project_type": project_type,
        "kit_tier": kit_tier,
        "project_born_at_template": born_at,
        "current_template_version": SCAFFOLD_TEMPLATE_VERSION,
        "stamp_found": stamp is not None,
        "report_only": (
            "This is a REPORT. Nothing was written and nothing will be. These files "
            "hold real project content — the human decides what, if anything, to adopt."
        ),
        "missing_kit_files": missing_files,
        "pending_template_changes": pending,
    }

    if not stamp:
        output["unstamped_warning"] = (
            "No scaffold stamp found, so the template version this project was born "
            f"from is unknown. Every '{project_type}' template change is listed below — "
            "some may already be reflected in your files. Review, do not apply blindly. "
            "Newly scaffolded files carry a stamp, so future syncs will be exact."
        )

    if not missing_files and not pending:
        output["summary"] = (
            f"Up to date. The kit is complete and no template changes have landed "
            f"since this project was scaffolded (template v{born_at})."
        )
    else:
        parts = []
        if missing_files:
            parts.append(
                f"{len(missing_files)} kit file(s) added to the template since this "
                "project was scaffolded and not present here"
            )
        if pending:
            parts.append(f"{len(pending)} template change(s) this project predates")
        output["summary"] = "; ".join(parts).capitalize() + "."
        output["next_steps"] = (
            "Review each item. To create the missing kit files (existing files are "
            "never touched): scaffold_project(confirmed=true). Template changes are "
            "advisory — apply the 'action' only where it fits this project."
        )

    if used_cwd_fallback:
        output["cwd_fallback_warning"] = (
            "Using CWD as the project directory (no MCP roots, project_path argument, "
            "or AI_GOVERNANCE_MCP_PROJECT env var detected). Verify the project_root "
            "above is the project you meant to sync."
        )

    return [TextContent(type="text", text=json.dumps(output, indent=2))]


async def _handle_scaffold_project(args: dict) -> list[TextContent]:
    """Handle scaffold_project tool — initialize governance memory files for a new project.

    Two-step flow: preview (no confirmed) → create (confirmed=true).
    Follows install_agent pattern for safety and UX consistency.

    mode='sync' (BACKLOG #190) reports staleness for an already-scaffolded project
    instead of creating anything — see _handle_scaffold_sync.
    """
    show_manual = args.get("show_manual", False)
    project_type = args.get("project_type", "code")
    kit_tier = args.get("kit_tier", "core")
    confirmed = args.get("confirmed", False)
    mode = args.get("mode", "create")

    if mode not in ("create", "sync"):
        error = ErrorResponse(
            error_code="INVALID_MODE",
            message=f"Invalid mode: '{str(mode)[:20]}'. Must be 'create' or 'sync'.",
            suggestions=[
                "Use mode='create' (default) to initialize a new project",
                "Use mode='sync' to report template staleness for an existing one",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Sync is report-only. Reject the write/manual combinations explicitly rather
    # than ignoring them silently — a silent ignore is how someone wires a write
    # into a read-only mode six months from now.
    if mode == "sync" and (confirmed or show_manual):
        offending = "confirmed" if confirmed else "show_manual"
        error = ErrorResponse(
            error_code="INVALID_MODE_COMBINATION",
            message=(
                f"mode='sync' cannot be combined with {offending}. Sync is report-only: "
                "it never writes files and has no confirm step."
            ),
            suggestions=[
                "Call scaffold_project(mode='sync') alone to get the report",
                "Use mode='create' with confirmed=true to create missing files",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Resolve caller's project path (not server CWD)
    project_path, used_cwd_fallback = await _resolve_caller_project_path(args)
    if project_path is None and not show_manual:
        error = ErrorResponse(
            error_code="INVALID_PROJECT_PATH",
            message="Specified project_path does not exist or is outside allowed scope",
            suggestions=[
                "Provide an absolute path to an existing directory within your home directory",
                "Use show_manual=true to get file contents for manual creation (recommended for Cowork/sandboxed environments)",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    project_name = str(
        args.get("project_name", "")
        or (project_path.name if project_path else "my-project")
    ).strip()[:100]
    if not project_name:
        project_name = project_path.name if project_path else "my-project"
    # Escape curly braces to prevent str.format() injection
    safe_project_name = project_name.replace("{", "{{").replace("}", "}}")

    # Validate parameters
    if project_type not in ("code", "document"):
        error = ErrorResponse(
            error_code="INVALID_PROJECT_TYPE",
            message=f"Invalid project_type: '{project_type}'. Must be 'code' or 'document'.",
            suggestions=[
                "Use project_type='code' for repositories",
                "Use project_type='document' for folder-based projects",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    if kit_tier not in ("core", "standard", "saas-ops"):
        error = ErrorResponse(
            error_code="INVALID_KIT_TIER",
            message=f"Invalid kit_tier: '{kit_tier}'. Must be 'core', 'standard', or 'saas-ops'.",
            suggestions=[
                "Use kit_tier='core' for the essential kit (code: 6 files — memory + AGENTS.md/CLAUDE.md/GEMINI.md loaders; document: 4 files — memory + README)",
                "Use kit_tier='standard' for 10 files on code projects (adds ARCHITECTURE.md + SPECIFICATION.md + .claude/skills/completion-sequence-aigov/checklist.md + _ai-context/BACKLOG.md) or 5 on document projects (adds _ai-context/BACKLOG.md)",
                "Use kit_tier='saas-ops' for 12 files (standard + SAAS-OPS-SOP.md, a per-app SaaS production-operations SOP for a money-taking SaaS; code projects only)",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # mode='sync' — report template staleness for an already-scaffolded project.
    # Runs after validation so it inherits the same path/type/tier guarantees;
    # project_path is non-None here (the None case errored above, and sync cannot
    # be combined with show_manual).
    if mode == "sync":
        return await _handle_scaffold_sync(
            args, project_path.resolve(), project_name, used_cwd_fallback
        )

    # show_manual mode — return file contents for manual creation
    # Used in sandboxed environments (Cowork) where the MCP server
    # cannot write to the project directory.
    if show_manual:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        files = _assemble_kit_files(project_type, kit_tier)

        file_contents = []
        for relative_path, template in files:
            content = template.format(project_name=safe_project_name, date=date_str)
            content = _stamp_content(content, project_type, kit_tier, date_str)
            file_contents.append({"path": relative_path, "content": content})

        output = {
            "status": "manual_instructions",
            "project_name": project_name,
            "project_type": project_type,
            "kit_tier": kit_tier,
            "instructions": (
                "Create these files in your project directory. "
                "Memory files go inside _ai-context/ for ALL project types "
                "(unified layout); loaders and project docs use the paths shown.\n\n"
                "The 'files' array below contains the path and full content "
                "for each file. Create them using your file-writing tools."
            ),
            "files": file_contents,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Build file manifest
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cwd = project_path.resolve()

    files = _assemble_kit_files(project_type, kit_tier)

    manifest = []
    for relative_path, template in files:
        full_path = (cwd / relative_path).resolve()

        # Path validation — reject traversal attempts
        if not full_path.is_relative_to(cwd):
            logger.warning("Path traversal rejected: %s", relative_path)
            continue

        content = template.format(project_name=safe_project_name, date=date_str)
        # Birth stamp (#190): records the template version this file was created
        # from, so a later mode='sync' can report exactly which template changes
        # this project predates instead of guessing from a content diff.
        content = _stamp_content(content, project_type, kit_tier, date_str)
        legacy = _grandfathered_root_counterpart(cwd, relative_path)
        exists = full_path.is_file() or (legacy is not None and legacy.is_file())
        if exists:
            logger.info(
                "scaffold_project: file exists at %s (parent exists: %s, parent is_dir: %s)",
                full_path,
                full_path.parent.exists(),
                full_path.parent.is_dir(),
            )

        manifest.append(
            {
                "relative_path": relative_path,
                "full_path": str(full_path),
                "exists": exists,
                "action": "skip (already exists)" if exists else "create",
                "content_preview": content[:200] + "..."
                if len(content) > 200
                else content,
                "content": content,
            }
        )

    files_to_create = [f for f in manifest if not f["exists"]]
    files_to_skip = [f for f in manifest if f["exists"]]

    # Preview mode
    if not confirmed:
        output = {
            "status": "preview",
            "project_name": project_name,
            "project_type": project_type,
            "kit_tier": kit_tier,
            "project_root": str(cwd),
            "files": [
                {
                    "path": f["relative_path"],
                    "resolved_path": f["full_path"],
                    "action": f["action"],
                    "preview": f["content_preview"],
                }
                for f in manifest
            ],
            "files_to_create": len(files_to_create),
            "files_to_skip": len(files_to_skip),
            "options": {
                "create": "Call scaffold_project with confirmed=true to create files",
                "cancel": "Take no action to cancel",
            },
        }
        if not files_to_create:
            output["warning"] = (
                "All governance files already exist. No files will be created."
            )
        else:
            output["next_steps"] = (
                "After scaffolding:\n"
                "1. Fill in [bracketed placeholders] in the created files\n"
                "2. Tell the AI your use case — what kind of work this project is — "
                "and it will propose specialized memory files to add alongside the core kit\n"
                "3. Run install_agent(agent_name='orchestrator') for governance orchestration\n"
                "4. Start working — the AI will read these files at session start"
            )
        if used_cwd_fallback:
            output["cwd_fallback_warning"] = (
                "Using CWD as project directory (no MCP roots, project_path argument, "
                "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
                "Verify file paths above are correct before confirming."
            )
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Confirmed mode — create files
    created = []
    skipped = []

    try:
        for f in manifest:
            full_path = Path(f["full_path"])

            # Symlink check FIRST (is_file() follows symlinks, so a symlink
            # to an existing file would be skipped as "already exists")
            if full_path.is_symlink():
                skipped.append(
                    {
                        "path": f["relative_path"],
                        "resolved_path": f["full_path"],
                        "reason": "symlink detected",
                    }
                )
                continue

            # Re-verify existence at write time (don't trust cached manifest);
            # a grandfathered root-layout original also counts (v2.62.0).
            legacy = _grandfathered_root_counterpart(cwd, f["relative_path"])
            if full_path.is_file() or (legacy is not None and legacy.is_file()):
                skipped.append(
                    {
                        "path": f["relative_path"],
                        "resolved_path": f["full_path"],
                        "reason": "already exists"
                        if full_path.is_file()
                        else "root-layout original exists (grandfathered)",
                    }
                )
                continue

            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f["content"])
            created.append(
                {
                    "path": f["relative_path"],
                    "resolved_path": f["full_path"],
                }
            )

    except PermissionError as e:
        error = ErrorResponse(
            error_code="PERMISSION_ERROR",
            message=f"Cannot write files: {_sanitize_error_message(e)}. Files created before error: {created}",
            suggestions=["Check directory permissions", "Try a different directory"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]
    except Exception as e:
        error = ErrorResponse(
            error_code="SCAFFOLD_ERROR",
            message=f"{_sanitize_error_message(e)}. Files created before error: {created}",
            suggestions=["Check file system permissions"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    output = {
        "status": "scaffolded",
        "project_name": project_name,
        "project_type": project_type,
        "kit_tier": kit_tier,
        "project_root": str(cwd),
        "files_created": created,
        "files_skipped": skipped,
        "message": f"Successfully initialized governance memory for '{project_name}'.",
        "next_steps": (
            "Your project is set up! Next:\n"
            "1. Fill in [bracketed placeholders] in the created files\n"
            "2. Tell the AI your use case — what kind of work this project is — "
            "and it will propose specialized memory files to add alongside the core kit\n"
            "3. Run install_agent(agent_name='orchestrator') to add governance orchestration\n"
            "4. Begin work — the AI will read these files at session start"
        ),
    }
    if used_cwd_fallback:
        output["cwd_fallback_warning"] = (
            "Used CWD as project directory (no MCP roots, project_path argument, "
            "or AI_GOVERNANCE_MCP_PROJECT env var detected). "
            "If files were created in the wrong project, re-run with "
            "project_path='/path/to/your/project'."
        )
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _escape_yaml_value(value: str) -> str:
    """Escape a string for safe inclusion in double-quoted YAML values.

    Handles quotes, newlines, and other YAML-special characters.
    Applied uniformly to all user-supplied fields in YAML frontmatter.
    """
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", "")
    )


def _near_duplicate_check(title: str, summary: str, tags: list, domain: str) -> dict:
    """Look for an existing entry that already says this.

    The exact-path check below catches a repeated ID. This catches the harder
    case: a DIFFERENT id carrying the same content. That is the real risk when
    captures stop being human-gated — not destruction (every entry is a git-
    tracked file) but corpus dilution, which degrades search for every project
    that reads this library.

    **The discriminator is the GAP, not an absolute score, and that is measured
    across the whole corpus (n=70, 2026-07-25) rather than from a few probes.**
    Querying every entry with its own title+summary:

        self-match top score : 0.872-1.000  (mean 0.946)
        runner-up            : 0.485-0.769  (mean 0.578)
        separation           : 0.164-0.489  (mean 0.368)

    An absolute threshold fails here. A deliberately unrelated control query
    scores in the high 0.6s-0.7s — above the runner-up of many genuine matches —
    because with no keyword hits, fusion renormalizes onto the semantic arm alone
    (BACKLOG #52), so `combined_score` is not comparable across queries. What IS
    comparable within one query is the separation between best and next.

    **Measured limits, stated rather than implied:**

    - **False negatives: 3 of 70 (4%) at the 0.25 cut.** Three entries queried
      with their own summary separate by only 0.164-0.242 and are reported
      `distinct`. That is the miss rate on the EASIEST possible input.
    - **The false-positive rate is unmeasured.** Lowering the cut to 0.15 would
      catch all 70, but trading a measured miss rate for an unmeasured false-alarm
      rate is not an improvement — so the cut stays at 0.25 until the other half
      is measured.
    - **Same-session blind spot:** a newly captured entry is not in the index
      until a rebuild, so two captures of the same content in one session both
      report `distinct`.

    An earlier version of this docstring published narrower ranges (0.79-0.89 /
    0.32-0.44) derived from four probes and stated as if they were bounds. They
    were not. Recorded here because publishing false precision is the defect this
    check exists inside a session about.

    Reported, never enforced: a check that has not earned denial authority does
    not get it. The caller and the review pass act on this; the tool does not block.
    """
    # Use the engine only if it is ALREADY loaded. Calling get_engine() here
    # would make a WRITE path initialize the retrieval stack as a side effect —
    # wrong dependency direction, and it leaked across the test suite when first
    # written this way. In production `_app.call_tool` loads the engine on every
    # dispatch, so the check runs; anywhere else it degrades to "unavailable",
    # which is reported as its own state rather than as "no duplicates found".
    engine = getattr(_state, "_engine", None)
    if engine is None or getattr(engine, "index", None) is None:
        return {"verdict": "unavailable", "candidates": [], "note": "engine not loaded"}
    # `search_references` returns [] when EITHER index or bm25_index is falsy, so
    # checking `index` alone lets a half-loaded engine produce an empty result set
    # that reads as a clean bill of health. Both are required.
    if not getattr(engine, "bm25_index", None):
        return {
            "verdict": "unavailable",
            "candidates": [],
            "note": "keyword index not built — search would return nothing",
        }
    try:
        query = f"{title} {summary} {' '.join(str(t) for t in tags[:8])}".strip()
        # `domain` scopes the search. Passing it was the whole point of taking the
        # parameter, and it was previously accepted and ignored — a signature that
        # implied scoping which did not happen.
        hits = engine.search_references(query=query, domain=domain, max_results=3)
        corpus = sum(
            len(getattr(d, "references", []) or [])
            for d in getattr(engine.index, "domains", {}).values()
        )
        if not hits:
            # Zero hits over a NON-EMPTY corpus is suspicious, not clean: it is what
            # a silently-degraded semantic arm looks like. Report the corpus size so
            # the caller can tell "nothing to match against" from "matched nothing".
            return {
                "verdict": "no_matches" if corpus == 0 else "no_matches_suspicious",
                "candidates": [],
                "corpus_entries": corpus,
                "note": (
                    "the library is empty — nothing to duplicate"
                    if corpus == 0
                    else f"zero matches against {corpus} existing entries. That is "
                    "what a degraded retrieval arm looks like as well as a genuinely "
                    "novel entry — do not read it as 'nothing similar exists'."
                ),
            }
        cands = [
            {
                "id": h.reference.id,
                "domain": getattr(h.reference, "domain", "?"),
                "score": round(h.combined_score, 3),
            }
            for h in hits
        ]
        if len(hits) < 2:
            # No runner-up means no separation to measure. The previous code put
            # 1.0 in a field named after a measurement and forced likely_duplicate,
            # so on a one-entry corpus every capture was flagged. (96c2b70's message
            # claimed this was already fixed; it was not — the edit never landed.)
            return {
                "verdict": "insufficient_candidates",
                "top_minus_runner_up": None,
                "candidates": cands,
                "corpus_entries": corpus,
                "note": "fewer than two candidates — the gap test needs a runner-up",
            }
        gap = round(hits[0].combined_score - hits[1].combined_score, 3)
        verdict = "likely_duplicate" if gap >= 0.25 else "distinct"
        return {
            "verdict": verdict,
            "top_minus_runner_up": gap,
            "candidates": cands,
            "corpus_entries": corpus,
            "note": (
                "GAP >= 0.25 means this query singled out one existing entry — read it "
                "before capturing. Below that, no single entry stands out. Measured "
                "across the full corpus (n=70): true self-matches separate by "
                "0.164-0.489, and 3 of 70 (4%) fall under the 0.25 cut, so a "
                "`distinct` verdict is not proof of novelty. Advisory, never blocks."
            ),
        }
    except Exception as exc:  # pragma: no cover - never fail a capture on this
        logger.debug("Near-duplicate check unavailable: %s", exc)
        return {
            "verdict": "unavailable",
            "candidates": [],
            "note": _sanitize_error_message(exc)[:120],
        }


def _registered_domain_names() -> set[str]:
    """Domain names from the registry — what the extractor will actually scan.

    Never raises: a missing or malformed registry must not take down a capture,
    so an unreadable registry contributes nothing and the index-derived set
    still applies.
    """
    try:
        from ...config import load_domains_registry

        settings = _state._settings or load_settings()
        return {d.name for d in load_domains_registry(settings)}
    except Exception:  # pragma: no cover - defensive; registry is optional
        logger.debug("Domain registry unreadable; falling back to index domains")
        return set()


async def _handle_capture_reference(args: dict) -> list[TextContent]:
    """Handle capture_reference tool — create a Reference Library entry file.

    Creates a markdown file with YAML frontmatter in reference-library/{domain}/.
    """
    # Extract and validate required fields
    entry_id = str(args.get("id", ""))[:100].strip()
    title = str(args.get("title", ""))[:200].strip()
    domain = str(args.get("domain", ""))[:50].strip()
    tags = args.get("tags", [])
    entry_type = args.get("entry_type", "direct")
    artifact = str(args.get("artifact", ""))[:10000]

    if not entry_id or not title or not domain or not tags or not artifact:
        error = ErrorResponse(
            error_code="MISSING_REQUIRED_FIELDS",
            message="Required fields: id, title, domain, tags, entry_type, artifact",
            suggestions=["Provide all required fields"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Validate domain format (safe directory name)
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", domain):
        error = ErrorResponse(
            error_code="INVALID_DOMAIN",
            message=f"Domain must be lowercase alphanumeric with hyphens: '{domain[:50]}'",
            suggestions=["Example: ai-coding, kmpd, storytelling"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Validate domain against the REGISTERED domains (BACKLOG #220).
    # A well-formed but unregistered domain is the silent-failure case: the file
    # is written and reported as success, but `_extract_references` only walks
    # `reference-library/{registered_domain}/`, so the entry never enters the
    # governance index and is permanently invisible to search_references /
    # query_governance. Distinct error code from INVALID_DOMAIN because the two
    # have different remediations: fix the spelling vs. register the domain.
    # Source of truth is the REGISTRY, not the built index: `_extract_references`
    # walks the registry's domains, so a domain that is registered but not yet
    # rebuilt into the index WILL be scanned on the next build and must be
    # accepted. Union of both, so neither a stale index nor a stale registry
    # produces a wrong refusal.
    known_domains = sorted(set(_state.get_domain_names()) | _registered_domain_names())
    if domain not in known_domains:
        error = ErrorResponse(
            error_code="DOMAIN_NOT_FOUND",
            message=(
                f"Domain '{domain[:50]}' is not a registered governance domain. "
                "The reference would be written to a folder the extractor never "
                "scans, making it permanently unretrievable."
            ),
            suggestions=[
                "Use list_domains to see available domains",
                f"Registered domains: {', '.join(known_domains)}",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Validate ID format
    if not re.match(r"^ref-[a-z0-9][a-z0-9-]*$", entry_id):
        error = ErrorResponse(
            error_code="INVALID_ID_FORMAT",
            message=f"ID must start with 'ref-' and contain only lowercase letters, numbers, hyphens: '{entry_id[:50]}'",
            suggestions=["Example: ref-ai-coding-my-pattern"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    if entry_type not in ("direct", "reference"):
        error = ErrorResponse(
            error_code="INVALID_ENTRY_TYPE",
            message=f"entry_type must be 'direct' or 'reference': '{entry_type[:20]}'",
            suggestions=[
                "Use 'direct' for artifacts in the library",
                "Use 'reference' for external pointers",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Build file path — use settings-derived path (same as extractor),
    # not CWD or _find_project_root() directly. Settings respects
    # AI_GOVERNANCE_DOCUMENTS_PATH env var overrides.
    settings = _state._settings or load_settings()
    corpus_root = settings.documents_path.parent.resolve()

    # BACKLOG #49: an optional target_root lets a maintainer redirect the write
    # into a worktree/checkout of THIS corpus (e.g. when self-developing in a git
    # worktree). Validate by git IDENTITY — same git common dir — NOT directory
    # shape: every clone/fork/worktree looks corpus-shaped, so a shape check would
    # silently accept a look-alike and reproduce the original misplacement bug.
    # Resolve before validating (a symlink/`..` must be checked at its real target).
    target_root_arg = args.get("target_root")
    if target_root_arg:
        target_root = Path(str(target_root_arg)).resolve()
        if not target_root.is_dir() or not is_within_allowed_scope(target_root):
            error = ErrorResponse(
                error_code="INVALID_TARGET_ROOT",
                message=(
                    "target_root is not an accessible directory within allowed "
                    f"scope (home, CWD, or temp): {target_root}"
                ),
                suggestions=[
                    "Pass a path under your home, CWD, or temp dir",
                    "Omit target_root to write to the configured corpus root",
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]
        corpus_common = _git_common_dir(corpus_root)
        target_common = _git_common_dir(target_root)
        if (
            corpus_common is None
            or target_common is None
            or corpus_common != target_common
        ):
            error = ErrorResponse(
                error_code="INVALID_TARGET_ROOT",
                message=(
                    "target_root must be a worktree/checkout of the SAME git "
                    f"repository as the corpus (git-identity check failed): {target_root}"
                ),
                suggestions=[
                    "Pass the root of a git worktree of THIS repository",
                    "Omit target_root to write to the configured corpus root",
                    "If the corpus is not a git checkout, target_root redirection is unavailable",
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]
        project_root = target_root
        ref_dir = project_root / "reference-library" / domain
    else:
        # DEFAULT WRITE TARGET IS THE CONFIGURED LIBRARY, NOT THE CORPUS CHECKOUT
        # (session-268). Writing beside `documents/` is what put one project's capture
        # into another project's working tree and would put a downloader's captures
        # inside their clone of our repo. `target_root` keeps its old meaning — an
        # explicit, git-identity-validated redirect for the in-repo case — but it is no
        # longer the only way to avoid polluting a checkout, because the default no
        # longer points at one.
        # RESOLVE BOTH SIDES. `file_path` below is .resolve()d, so an unresolved anchor
        # makes the is_relative_to check compare across two namespaces: on macOS a
        # library reached through a symlink (/tmp -> /private/tmp, or a compatibility
        # symlink at the old location) fails the check and every capture returns
        # PATH_TRAVERSAL blaming the user's domain/id. Fails closed, so not a bypass —
        # but it bricks capture and misdiagnoses it. The previous default (corpus_root)
        # WAS resolved; this was a regression. pytest resolves tmp_path, so fixtures
        # structurally cannot catch it.
        ref_dir = settings.reference_library_path.resolve() / domain
        project_root = settings.reference_library_path.resolve()
    file_path = (ref_dir / f"{entry_id}.md").resolve()

    # Path validation
    if not file_path.is_relative_to(project_root):
        error = ErrorResponse(
            error_code="PATH_TRAVERSAL",
            message="Invalid domain or ID — path traversal detected",
            suggestions=["Use simple domain names and IDs without path separators"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Check if file already exists
    if file_path.is_file():
        error = ErrorResponse(
            error_code="ENTRY_EXISTS",
            message=f"Reference entry already exists: {entry_id} at {file_path}",
            suggestions=["Use a different ID", "Edit the existing file directly"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # Build YAML frontmatter
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = str(args.get("summary", ""))[:300]
    context = str(args.get("context", ""))[:2000]
    lessons = str(args.get("lessons", ""))[:2000]
    maturity = args.get("maturity", "seedling")
    external_url = str(args.get("external_url", ""))[:500]
    external_author = str(args.get("external_author", ""))[:100]

    # Escape all user-supplied fields uniformly for YAML safety
    safe_title = _escape_yaml_value(title)
    tags_yaml = ", ".join(f'"{_escape_yaml_value(t[:50])}"' for t in tags[:10])

    # Optional stack/platform applicability (BACKLOG #46). Normalize to
    # lowercase; tolerate a scalar or a list.
    applies_to_raw = args.get("applies_to", [])
    if isinstance(applies_to_raw, str):
        applies_to_raw = [applies_to_raw]
    applies_to = [str(s).strip().lower() for s in applies_to_raw[:10] if str(s).strip()]

    lines = [
        "---",
        f"id: {entry_id}",
        f'title: "{safe_title}"',
        f"domain: {domain}",
        f"tags: [{tags_yaml}]",
        "status: current",
        f"entry_type: {entry_type}",
    ]
    if applies_to:
        applies_yaml = ", ".join(f'"{_escape_yaml_value(s[:50])}"' for s in applies_to)
        lines.append(f"applies_to: [{applies_yaml}]")
    if summary:
        lines.append(f'summary: "{_escape_yaml_value(summary)}"')
    lines.extend(
        [
            f"created: {date_str}",
            f"last_verified: {date_str}",
            f"maturity: {maturity if maturity in ('seedling', 'budding', 'evergreen') else 'seedling'}",
            "decay_class: framework",
            'source: "Captured via capture_reference tool"',
        ]
    )
    if entry_type == "reference" and external_url:
        lines.append(f'external_url: "{_escape_yaml_value(external_url)}"')
        if external_author:
            lines.append(f'external_author: "{_escape_yaml_value(external_author)}"')
        lines.append(f"accessed_date: {date_str}")
    lines.append("---")
    lines.append("")
    lines.append("## Context")
    lines.append("")
    lines.append(context if context else "[When to use this and why it exists]")
    lines.append("")
    lines.append("## Artifact")
    lines.append("")
    lines.append(artifact)
    lines.append("")
    lines.append("## Lessons Learned")
    lines.append("")
    lines.append(lessons if lessons else "[What worked, what didn't, edge cases]")
    lines.append("")
    lines.append("## Cross-References")
    lines.append("")
    lines.append("- Principles: [relevant principle IDs]")
    lines.append("- Methods: [relevant method section refs]")
    lines.append("- See also: [related entry IDs]")
    lines.append("")

    content = "\n".join(lines)

    # Does the library already say this? Reported in the response, never
    # blocking — see _near_duplicate_check for why the discriminator is a
    # score GAP rather than an absolute threshold.
    dup_check = _near_duplicate_check(title, str(args.get("summary", "")), tags, domain)

    # Content security scan — warn on threats, don't block
    security_warnings = scan_reference_content(
        artifact + "\n" + context + "\n" + lessons
    )

    # Create file
    try:
        ref_dir.mkdir(parents=True, exist_ok=True)
        if file_path.is_symlink():
            error = ErrorResponse(
                error_code="SYMLINK_DETECTED",
                message="Target path is a symlink — refusing to write",
                suggestions=["Remove the symlink and try again"],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]
        file_path.write_text(content)
        # Post-write verification — confirm the file actually landed on disk
        if not file_path.is_file():
            error = ErrorResponse(
                error_code="WRITE_VERIFICATION_FAILED",
                message=f"File write appeared to succeed but file not found at: {file_path}",
                suggestions=[
                    "Check filesystem permissions",
                    "Check if path is on a read-only mount",
                ],
            )
            return [TextContent(type="text", text=error.model_dump_json(indent=2))]
    except PermissionError as e:
        error = ErrorResponse(
            error_code="PERMISSION_ERROR",
            message=f"Cannot write file: {_sanitize_error_message(e)}",
            suggestions=["Check directory permissions"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]
    except Exception as e:
        error = ErrorResponse(
            error_code="CAPTURE_ERROR",
            message=_sanitize_error_message(e),
            suggestions=["Check file system permissions"],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    output = {
        "status": "captured",
        "entry_id": entry_id,
        "file_path": str(file_path.relative_to(project_root)),
        "absolute_path": str(file_path),
        "project_root": str(project_root),
        "domain": domain,
        "entry_type": entry_type,
        "maturity": maturity,
        "near_duplicate_check": dup_check,
        # WILL THIS ENTRY EVER BE FOUND? (#256, session-268). The extractor walks ONLY
        # `settings.reference_library_path` and its private sibling, so a `target_root`
        # write lands somewhere nothing indexes: "captured" would be true and useless —
        # written, readable, and permanently absent from search. That is exactly the
        # silent-success failure the DOMAIN_NOT_FOUND gate (#220) was built to end,
        # reintroduced at the path instead of the domain. Say so in the response rather
        # than letting `status: captured` imply retrievability.
        "indexed_location": _is_within(file_path, settings.reference_library_path),
        "message": (
            f"Reference entry '{title}' captured successfully."
            if _is_within(file_path, settings.reference_library_path)
            else (
                f"Reference entry '{title}' was WRITTEN but is OUTSIDE the indexed "
                f"library ({settings.reference_library_path}) — it will NOT be "
                f"retrievable by search_references or query_governance until it is "
                f"moved there. Captured is not the same as findable."
            )
        ),
        # Two different properties, and the second one used to be missing.
        # SEARCHABLE needs an index rebuild. DURABLE needs a commit — and this
        # tool writes a file and stops, so nothing ever said so. Measured
        # session-272: six entries sat untracked in the library repo, four of
        # them for up to four days, in a repo with no remote. Nothing was lost,
        # but they existed on exactly one disk with no history.
        "next_steps": (
            "Entry created. Two separate things still have to happen:\n"
            "SEARCHABLE — 1. Run `python -m ai_governance_mcp.extractor` to "
            "rebuild the index. 2. Verify with `query_governance` that the entry "
            "surfaces for relevant queries.\n"
            f"DURABLE — the file is written but NOT committed. Commit it in the "
            f"library repo ({settings.reference_library_path}); an uncommitted "
            f"entry lives on one disk with no history, and this tool cannot "
            f"commit for you because that repo is your data, not the product's."
        ),
    }
    if security_warnings:
        output["security_warnings"] = security_warnings
        output["message"] += (
            f" WARNING: {len(security_warnings)} security pattern(s) detected"
            " — review the entry for potential threats."
        )
    return [TextContent(type="text", text=json.dumps(output, indent=2))]
