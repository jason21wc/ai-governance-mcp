#!/usr/bin/env python3
"""Describe the largest Learning Log bodies; never impose a size ceiling.

Usage: python3 memory-entry-size.py /explicit/path/to/LEARNING-LOG.md
Counts include Markdown and URLs, with whitespace runs collapsed to one space.
Only level-three ATX headings outside fenced code start entries. Higher headings
end them; deeper headings and fenced code remain part of the body.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?)|[ \t]*)$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
LABEL_LIMIT = 100


def visible_label(label: str) -> str:
    """Keep Unicode prose while making terminal/format controls visible."""
    parts = []
    for char in label:
        if unicodedata.category(char).startswith("C") or char in "\t\r\n":
            code = ord(char)
            parts.append(f"\\x{code:02x}" if code <= 0xFF else f"\\u{code:04x}")
        else:
            parts.append(char)
    label = "".join(parts)
    return label if len(label) <= LABEL_LIMIT else label[: LABEL_LIMIT - 1] + "…"


def largest_entries(text: str) -> list[tuple[int, int, str]]:
    """Return (normalized characters, heading line, visible label), largest first."""
    entries = []
    current: tuple[int, str] | None = None
    body: list[str] = []
    fence_char = ""
    fence_length = 0

    def finish() -> None:
        if current:
            count = len(re.sub(r"\s+", " ", "\n".join(body)).strip())
            if count:
                entries.append((count, current[0], visible_label(current[1])))

    # Split only actual source newlines: str.splitlines() would let control
    # characters inside a malicious title manufacture apparent Markdown lines.
    for line_number, line in enumerate(text.split("\n"), 1):
        line = line.removesuffix("\r")
        fence = FENCE.match(line)
        if fence_char:
            if current:
                body.append(line)
            if (
                fence
                and fence[1][0] == fence_char
                and len(fence[1]) >= fence_length
                and not fence[2].strip()
            ):
                fence_char = ""
            continue
        if fence and not (fence[1][0] == "`" and "`" in fence[2]):
            fence_char, fence_length = fence[1][0], len(fence[1])
            if current:
                body.append(line)
            continue
        heading = HEADING.match(line)
        if heading and len(heading[1]) <= 3:
            finish()
            body = []
            label = (heading[2] or "").strip(" \t")
            # Linear suffix trimming: an unanchored whitespace regex retries
            # long internal runs at each character in an untrusted heading.
            before_hashes = label.rstrip("#")
            if before_hashes != label and before_hashes.endswith((" ", "\t")):
                label = before_hashes.rstrip(" \t")
            current = (line_number, label) if len(heading[1]) == 3 else None
        elif current:
            body.append(line)
    finish()
    return sorted(entries, key=lambda entry: (-entry[0], entry[1]))[:3]


def main() -> int:
    if len(sys.argv) != 2:
        print("entry report unavailable: supply one Learning Log path", file=sys.stderr)
        return 1
    try:
        # Preserve embedded carriage returns; universal-newline decoding could
        # otherwise let a title inject a new apparent Markdown heading.
        text = Path(sys.argv[1]).read_bytes().decode("utf-8")
    except FileNotFoundError:
        return 0
    except (OSError, UnicodeError):
        print("entry report unavailable: cannot read Learning Log", file=sys.stderr)
        return 1
    entries = largest_entries(text)
    if entries:
        print(
            "Largest Learning Log entries (normalized body characters; descriptive only):"
        )
        for count, line, label in entries:
            print(f"  - line {line}: {label} — {count} characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
