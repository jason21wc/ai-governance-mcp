"""Security utilities: instruction validation, sanitization, rate limiting.

Rate-limit mutable state lives here alongside ``_check_rate_limit`` so the
``global`` keyword invariant holds.
"""

import re
import threading
import time

from ._constants import (
    MAX_LOG_CONTENT_LENGTH,
    RATE_LIMIT_REFILL_RATE,
    RATE_LIMIT_TOKENS,
    SECRET_PATTERNS,
)


class ServerInstructionsSecurityError(Exception):
    """Raised when SERVER_INSTRUCTIONS contains suspicious patterns.

    This is a critical security check - if SERVER_INSTRUCTIONS is compromised,
    ALL AI clients consuming this server would be affected.
    """

    pass


_CRITICAL_INSTRUCTION_PATTERNS = {
    "prompt_injection": re.compile(
        r"(?:^|[.!?]\s+)ignore\s+(?:previous|prior|above)\s+instructions|"
        r"(?:^|[.!?]\s+)you\s+are\s+now\s+|"
        r"(?:^|[.!?]\s+)disregard\s+(?:all|previous)|"
        r"(?:^|[.!?]\s+)forget\s+(?:everything|all|previous)|"
        r"(?:^|\*\s+)new\s+instructions:",
        re.IGNORECASE | re.MULTILINE,
    ),
    "role_override": re.compile(
        r"(?:^|[.!?]\s+)you\s+(?:must|should|will)\s+(?:always|never)\s+(?:obey|follow|listen)|"
        r"(?:^|[.!?]\s+)(?:override|replace|supersede)\s+(?:your|all)\s+(?:previous\s+)?instructions",
        re.IGNORECASE | re.MULTILINE,
    ),
}


def _validate_server_instructions(instructions: str) -> None:
    """Validate SERVER_INSTRUCTIONS contains no critical security patterns.

    This is called at module load time to ensure the instruction block
    that gets sent to ALL AI clients is clean.

    Args:
        instructions: The SERVER_INSTRUCTIONS string to validate

    Raises:
        ServerInstructionsSecurityError: If critical patterns are detected
    """
    for pattern_name, pattern in _CRITICAL_INSTRUCTION_PATTERNS.items():
        matches = pattern.findall(instructions)
        if matches:
            raise ServerInstructionsSecurityError(
                f"CRITICAL: SERVER_INSTRUCTIONS contains {pattern_name} pattern!\n"
                f"Match: {matches[0][:50]}...\n"
                f"This would compromise ALL AI clients. Blocking server start."
            )


# ---------------------------------------------------------------------------
# Rate limiting (token bucket)
# ---------------------------------------------------------------------------

_rate_limit_tokens = RATE_LIMIT_TOKENS
_rate_limit_last_refill = time.time()
_rate_limit_lock = threading.Lock()


def _check_rate_limit() -> bool:
    """Check if request is within rate limit using token bucket algorithm.

    H4 FIX: Prevents DoS by limiting request rate.
    Thread-safe via _rate_limit_lock (defense-in-depth for run_in_executor).

    Returns:
        True if request is allowed, False if rate limited.
    """
    global _rate_limit_tokens, _rate_limit_last_refill

    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _rate_limit_last_refill
        _rate_limit_last_refill = now

        _rate_limit_tokens = min(
            RATE_LIMIT_TOKENS, _rate_limit_tokens + (elapsed * RATE_LIMIT_REFILL_RATE)
        )

        if _rate_limit_tokens >= 1:
            _rate_limit_tokens -= 1
            return True
        return False


# ---------------------------------------------------------------------------
# Content sanitization
# ---------------------------------------------------------------------------


def _sanitize_for_logging(content: str) -> str:
    """Sanitize content before logging to prevent sensitive data exposure.

    M1 FIX: Truncates long content.
    M4 FIX: Redacts potential secrets.

    Args:
        content: The content to sanitize.

    Returns:
        Sanitized content safe for logging.
    """
    if not content:
        return content

    sanitized = content
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    if len(sanitized) > MAX_LOG_CONTENT_LENGTH:
        sanitized = sanitized[:MAX_LOG_CONTENT_LENGTH] + "...[TRUNCATED]"

    return sanitized


def _sanitize_error_message(error: Exception) -> str:
    """Sanitize error message to prevent information leakage.

    M6 FIX: Removes internal paths and sensitive information from error messages.
    M3 FIX: More aggressive sanitization for production deployments.

    Args:
        error: The exception to sanitize.

    Returns:
        Sanitized error message safe for external display.
    """
    message = str(error)

    message = re.sub(
        r'(?:[A-Za-z]:)?(?:[/\\][^/\\:*?"<>|\s]+)+[/\\]([^/\\:*?"<>|\s]+)',
        r"\1",
        message,
    )

    message = re.sub(r", line \d+", "", message)
    message = re.sub(r"0x[0-9a-fA-F]+", "0x***", message)
    message = re.sub(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*){2,}\b", "[module]", message)
    message = re.sub(r"\bin\s+\w+\s*\(", "in [func](", message)
    message = re.sub(r'File\s+["\'][^"\']+["\']', "File [redacted]", message)
    message = re.sub(
        r"(?:During handling of|The above exception was)",
        "[exception chain]",
        message,
    )

    max_error_length = 500
    if len(message) > max_error_length:
        message = message[:max_error_length] + "...[truncated]"

    return message
