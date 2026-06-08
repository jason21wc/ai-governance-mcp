"""Scaffold and reference library handlers."""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from mcp.types import TextContent

from ...config import load_settings
from ...path_resolution import _git_common_dir, is_within_allowed_scope
from ...extractor import SUSPICIOUS_PATTERNS, normalize_text_for_security
from ...models import ErrorResponse
from .._constants import SCAFFOLD_CORE_FILES, SCAFFOLD_STANDARD_EXTRAS
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

        normalized = normalize_text_for_security(line)

        for pattern_type, pattern in SUSPICIOUS_PATTERNS.items():
            if pattern.search(normalized):
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


async def _handle_scaffold_project(args: dict) -> list[TextContent]:
    """Handle scaffold_project tool — initialize governance memory files for a new project.

    Two-step flow: preview (no confirmed) → create (confirmed=true).
    Follows install_agent pattern for safety and UX consistency.
    """
    show_manual = args.get("show_manual", False)
    project_type = args.get("project_type", "code")
    kit_tier = args.get("kit_tier", "core")
    confirmed = args.get("confirmed", False)

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

    if kit_tier not in ("core", "standard"):
        error = ErrorResponse(
            error_code="INVALID_KIT_TIER",
            message=f"Invalid kit_tier: '{kit_tier}'. Must be 'core' or 'standard'.",
            suggestions=[
                "Use kit_tier='core' for 4 essential files",
                "Use kit_tier='standard' for 9 files (adds CLAUDE.md + ARCHITECTURE.md + SPECIFICATION.md + .claude/skills/completion-sequence-aigov/checklist.md + BACKLOG.md)",
            ],
        )
        return [TextContent(type="text", text=error.model_dump_json(indent=2))]

    # show_manual mode — return file contents for manual creation
    # Used in sandboxed environments (Cowork) where the MCP server
    # cannot write to the project directory.
    if show_manual:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        files = list(SCAFFOLD_CORE_FILES.get(project_type, []))
        if kit_tier == "standard":
            files.extend(SCAFFOLD_STANDARD_EXTRAS.get(project_type, []))

        file_contents = []
        for relative_path, template in files:
            content = template.format(project_name=safe_project_name, date=date_str)
            file_contents.append({"path": relative_path, "content": content})

        output = {
            "status": "manual_instructions",
            "project_name": project_name,
            "project_type": project_type,
            "kit_tier": kit_tier,
            "instructions": (
                "Create these files in your project directory. "
                "For document projects, all files go inside _ai-context/.\n\n"
                "The 'files' array below contains the path and full content "
                "for each file. Create them using your file-writing tools."
            ),
            "files": file_contents,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    # Build file manifest
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cwd = project_path.resolve()

    files = list(SCAFFOLD_CORE_FILES.get(project_type, []))
    if kit_tier == "standard":
        files.extend(SCAFFOLD_STANDARD_EXTRAS.get(project_type, []))

    manifest = []
    for relative_path, template in files:
        full_path = (cwd / relative_path).resolve()

        # Path validation — reject traversal attempts
        if not full_path.is_relative_to(cwd):
            logger.warning("Path traversal rejected: %s", relative_path)
            continue

        content = template.format(project_name=safe_project_name, date=date_str)
        exists = full_path.is_file()
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
                "2. Run install_agent(agent_name='orchestrator') for governance orchestration\n"
                "3. Start working — the AI will read these files at session start"
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

            # Re-verify existence at write time (don't trust cached manifest)
            if full_path.is_file():
                skipped.append(
                    {
                        "path": f["relative_path"],
                        "resolved_path": f["full_path"],
                        "reason": "already exists",
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
            "2. Run install_agent(agent_name='orchestrator') to add governance orchestration\n"
            "3. Begin work — the AI will read these files at session start"
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
    else:
        project_root = corpus_root

    ref_dir = project_root / "reference-library" / domain
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
        "message": f"Reference entry '{title}' captured successfully.",
        "next_steps": (
            "Entry created. To make it searchable:\n"
            "1. Run `python -m ai_governance_mcp.extractor` to rebuild the index\n"
            "2. Verify with `query_governance` that the entry surfaces for relevant queries"
        ),
    }
    if security_warnings:
        output["security_warnings"] = security_warnings
        output["message"] += (
            f" WARNING: {len(security_warnings)} security pattern(s) detected"
            " — review the entry for potential threats."
        )
    return [TextContent(type="text", text=json.dumps(output, indent=2))]
