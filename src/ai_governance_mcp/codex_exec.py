"""Shared keyless ``codex exec`` helper — the ONE cross-vendor Codex invocation point.

Two callers run a self-contained prompt through a fresh, keyless Codex (gpt) exec:
``scripts/codex_review.py`` (cross-vendor peer review) and
``scripts/measure_plain_language.py`` (fresh-context plain-language judge). This module is
that single call site, so the invocation gotchas and the security hardening live in ONE
place instead of drifting across two copies:

  * stdin closed on EOF (``input=`` → subprocess closes it) avoids the ``codex exec``
    "reading additional input from stdin" hang;
  * ``--sandbox read-only`` — the judge/reviewer can mutate nothing;
  * ``-o <file>`` captures the clean final message (no session preamble to parse);
  * MINIMAL child env — the prompt content (a diff / a transcript) is UNTRUSTED, and a
    prompt-injection payload could induce the sandboxed model to read and echo a
    parent-env secret back through its output. Codex is keyless (it authenticates via
    ``~/.codex``, reachable through ``HOME`` / ``CODEX_*``), so API keys / cloud creds /
    tokens are never handed to the child. (Found by the Codex peer reviewing the harness,
    session-238; extracting here propagates the fix to the plain-language judge too.)

Keyless: rides the logged-in Codex session (no API key). The prompt must call NO MCP tools
— the exec-mode MCP-cancel bug (openai/codex #16685/#24135) cancels them; a review/judge
prompt is self-contained, so it does not apply. See ref-ai-coding-codex-cli-mcp-integration.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 — fixed argv-list codex invocation, no shell, minimal env
import tempfile
from typing import Mapping, Optional

DEFAULT_TIMEOUT = 300

# Only what codex itself needs — never secret-bearing vars. See the module docstring.
_ENV_ALLOWLIST = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "LANG",
    "LC_ALL",
    "TERM",
    "TMPDIR",
)

# CODEX_* config vars pass through (codex needs its own namespace, e.g. CODEX_HOME), EXCEPT
# any whose name looks secret-bearing — defense-in-depth so a hypothetical CODEX_AUTH_TOKEN
# can't ride along to the untrusted-prompt child. (Found by the Codex peer on this helper.)
_SECRETISH_SUBSTRINGS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CRED", "AUTH")


def _is_secretish(name: str) -> bool:
    upper = name.upper()
    return any(s in upper for s in _SECRETISH_SUBSTRINGS)


def codex_available() -> bool:
    """True when the `codex` CLI is on PATH (necessary, not sufficient — still needs login)."""
    return shutil.which("codex") is not None


def minimal_env(extra: Optional[Mapping[str, str]] = None) -> dict:
    """Allowlisted env for the Codex child: infra vars + CODEX_* (+ optional `extra`)."""
    env = {k: os.environ[k] for k in _ENV_ALLOWLIST if k in os.environ}
    env.update(
        {
            k: v
            for k, v in os.environ.items()
            if k.startswith("CODEX_") and not _is_secretish(k)
        }
    )
    if extra:
        env.update(extra)
    return env


def run_codex_exec(
    prompt: str,
    *,
    model: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    extra_env: Optional[Mapping[str, str]] = None,
) -> str:
    """Run `prompt` through a fresh keyless Codex exec; return its final message text.

    `extra_env` adds caller-specific vars to the minimal child env (e.g. a recursion
    sentinel). Never raises on Codex's own exit code (`check=False`); the caller decides
    what an empty / unparseable result means.
    """
    out_fd, out_path = tempfile.mkstemp(suffix=".txt")
    os.close(out_fd)
    try:
        cmd = ["codex", "exec", "--sandbox", "read-only", "-o", out_path]
        if model:
            cmd += ["-m", model]
        subprocess.run(  # nosec B603 — argv list (no shell); prompt via stdin, not the command line
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=minimal_env(extra_env),
        )
        with open(out_path, encoding="utf-8") as f:
            return f.read().strip()
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass
