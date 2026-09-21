"""Test-only, bounded memory-policy declaration checks (#369).

The lifecycle obligations are this project's assurance convention, derived from
CFR §7.0.4 and §§7.1–7.3; Appendix B.0 itself requires a lifecycle field, not
all these clauses. Supported English is defined by fixtures, not an interpreter.
Passing these checks does not establish that the complete header is consistent:
reviewers must still read it for contradictions and routing meaning.
"""

from __future__ import annotations

import re

HEADER_LINES = 40
MEMORY_NAMES = frozenset(
    {
        "SESSION-STATE.md",
        "PROJECT-MEMORY.md",
        "LEARNING-LOG.md",
        "BACKLOG.md",
        "OPERATIONS.md",
    }
)


def section(text: str, number: str) -> str:
    matches = list(re.finditer(rf"^### {re.escape(number)}\b[^\n]*\n", text, re.M))
    assert len(matches) == 1, f"CFR §{number}: expected one canonical section"
    start = matches[0].end()
    end = re.search(r"^#{1,3} ", text[start:], re.M)
    return text[start : start + end.start()] if end else text[start:]


def table_after(text: str, header: str, source: str) -> list[list[str]]:
    assert text.count(header) == 1, f"{source}: missing or ambiguous table header"
    tail = text.split(header, 1)[1]
    rows = []
    for line in tail.strip().splitlines():
        if not line.strip().startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
            continue
        assert len(cells) == header.count("|") - 1, (
            f"{source}: malformed table row {line!r}"
        )
        rows.append(cells)
    assert rows, f"{source}: empty table"
    return rows


def canonical_types(text: str) -> dict[str, str]:
    source = "CFR §7.0.2"
    rows = table_after(
        section(text, "7.0.2"),
        "| Cognitive Type | File | Purpose | Lifecycle |",
        source,
    )
    mapping: dict[str, str] = {}
    seen_types = set()
    for cells in rows:
        match = re.fullmatch(r"\*\*(\w+) Memory\*\*", cells[0])
        assert match, f"{source}: unparseable cognitive type {cells[0]!r}"
        kind = match[1]
        assert kind not in seen_types, f"{source}: duplicate type row {kind}"
        seen_types.add(kind)
        names = re.findall(r"`([A-Z][A-Z-]+\.md)`", cells[1])
        # A recognized mapping elsewhere must not hide a second, malformed
        # assignment in this cell (for example an unquoted LEARNING-LOG.md).
        mentions = re.findall(r"(?<![\w.-])([\w.-]+\.md)\b", cells[1], re.I)
        assert names == mentions, (
            f"{source}: unparseable filename mention in {cells[1]!r}"
        )
        for name in names:
            assert name not in mapping, f"{source}: ambiguous mapping for {name}"
            mapping[name] = kind
    assert mapping.keys() == MEMORY_NAMES, (
        f"{source}: incomplete/unparseable filename mapping: {mapping}; "
        f"expected {sorted(MEMORY_NAMES)}"
    )
    return mapping


def canonical_line_triggers(text: str) -> dict[str, int]:
    source = "CFR §7.0.4 Distillation Triggers"
    body = section(text, "7.0.4")
    assert body.count("**Distillation Triggers:**") == 1, (
        f"{source}: missing/ambiguous anchor"
    )
    rows = table_after(
        body.split("**Distillation Triggers:**", 1)[1],
        "| Memory File | Trigger | Action |",
        source,
    )
    triggers = {}
    for name, trigger, _action in rows:
        if name not in MEMORY_NAMES:
            continue  # source documents have their own policy
        match = re.fullmatch(r">\s*(\d+)\s+lines", trigger)
        if match:
            assert name not in triggers, f"{source}: duplicate line trigger for {name}"
            triggers[name] = int(match[1])
        else:
            assert "line" not in trigger.lower(), (
                f"{source}: unparseable line trigger {trigger!r}"
            )
    expected = MEMORY_NAMES - {"OPERATIONS.md"}
    assert triggers.keys() == expected, (
        f"{source}: missing line triggers: {expected - triggers.keys()}"
    )
    return triggers


def header(text: str) -> str:
    """First forty lines, excluding incidental table rows (Appendix B.0)."""
    return "\n".join(
        line
        for line in text.splitlines()[:HEADER_LINES]
        if not line.lstrip().startswith("|")
    )


def declared_field(text: str, name: str) -> str:
    """Read one field and adjacent wrapped continuation, never other prose blocks."""
    lines = header(text).splitlines()
    pattern = re.compile(rf"^\*\*{re.escape(name)}:\*\*\s*(.*)$")
    hits = [
        (i, pattern.match(line)) for i, line in enumerate(lines) if pattern.match(line)
    ]
    assert len(hits) == 1, f"Appendix B.0: expected exactly one **{name}:** declaration"
    i, match = hits[0]
    parts = [match[1]]
    for line in lines[i + 1 :]:
        if not line.strip() or re.match(r"^(?:\*\*[^*]+:\*\*|#|>|---|```|~~~)", line):
            break
        parts.append(line.strip())
    value = " ".join(parts).strip()
    assert value, f"Appendix B.0: empty **{name}:** declaration"
    return value


def assert_declared_type(name: str, text: str, mapping: dict[str, str]) -> None:
    value = declared_field(text, "Memory Type")
    match = re.fullmatch(r"(\w+)(?:\s+\([^\n]*\))?", value)
    assert match and match[1] == mapping[name], (
        f"{name}: Memory Type {value!r} must be {mapping[name]} per CFR §7.0.2"
    )


# Each tuple is one obligation; alternatives within a regex support grammatical
# variation. These deliberately do not try to understand arbitrary English.
LIFECYCLE_OBLIGATIONS = {
    "SESSION-STATE.md": (
        (
            r"(?:overwrit\w*|replac\w*).{0,65}(?:each|every) session",
            "overwrite each session",
        ),
        (
            r"(?:no|never|not|without).{0,45}(?:history|historical|stack|log)|snapshot only",
            "no session-history stack",
        ),
    ),
    "PROJECT-MEMORY.md": (
        (
            r"(?:never|do not|don't) delete.{0,30}decision|(?:preserv\w*|retain\w*|keep) (?:all |the )?(?:superseded )?decision",
            "preserve decisions",
        ),
        (
            r"(?:condens\w*|summari[sz]\w*).{0,35}(?:supporting detail|supporting material)",
            "condense supporting detail",
        ),
        (r"supersed\w*.{0,65}date|dated.{0,30}supersess", "date supersession"),
        (
            r"supersed\w*.{0,100}(?:replacement link|link to (?:the )?(?:new|replacement)|link to what replaced)",
            "link replacement on supersession",
        ),
    ),
    "LEARNING-LOG.md": (
        (
            r"(?:graduat\w*|distill\w*).{0,65}(?:methods|procedures|standing guidance)",
            "graduate into procedures",
        ),
        (
            r"(?:when |as )?(?:patterns? emerg\w*|recurring lessons)",
            "graduate when patterns emerge",
        ),
        (
            r"(?:remov\w*|delet\w*|prun\w*).{0,110}§7\.3\.4|§7\.3\.4.{0,70}(?:remov\w*|delet\w*|prun\w*)",
            "removal follows §7.3.4",
        ),
        (
            r"(?:never|do not|don't).{0,20}(?:prun\w*|remov\w*|delet\w*).{0,30}size alone|no size-only pruning",
            "no size-only pruning",
        ),
    ),
    "BACKLOG.md": (
        (
            r"(?:remov\w*|delet\w*).{0,80}(?:done\b|complet\w*|implement\w*|closed|migrat\w*)",
            "remove completed/closed work",
        ),
        (r"(?:remov\w*|delet\w*).{0,100}abandon\w*", "remove abandoned work"),
    ),
    "OPERATIONS.md": (
        (
            r"retir\w*.{0,45}documented (?:reason|rationale)",
            "document retirement reason",
        ),
        (
            r"never done|(?:completion|done).{0,35}(?:not|isn't).{0,25}(?:retir|prun)|(?:not|never) retir\w*.{0,30}(?:done|complet)",
            "completion alone is not retirement",
        ),
    ),
}

# Explicit conflicting clauses exercised by fixtures. This is a small regression
# net, not proof that all contradictory English can be recognized.
LIFECYCLE_CONFLICTS = {
    "SESSION-STATE.md": r"(?:append|retain|keep) (?:a |the )?(?:session-history stack|session history)",
    "PROJECT-MEMORY.md": r"(?:delete|discard) (?:all )?superseded decisions",
    "LEARNING-LOG.md": r"delete every lesson after one session|(?:prune|delete|remove) (?:lessons|entries) (?:solely )?for size",
    "BACKLOG.md": r"(?:keep|retain) (?:all )?(?:completed|abandoned) (?:items|work) forever",
    "OPERATIONS.md": r"(?:delete|remove|retire) (?:items )?when (?:done|completed)",
}


def assert_lifecycle(name: str, text: str) -> None:
    value = declared_field(text, "Lifecycle")
    value = re.sub(r"[*`\"“”]", "", value).lower()
    value = re.sub(r"\s+", " ", value)
    missing = [
        label
        for pattern, label in LIFECYCLE_OBLIGATIONS[name]
        if not re.search(pattern, value)
    ]
    assert not missing, (
        f"{name}: lifecycle must state {missing} (CFR §7.0.4, §§7.1–7.3; local header assurance convention)"
    )
    assert not re.search(
        r"(?:^|[.;]\s*|\bbut\s+)" + LIFECYCLE_CONFLICTS[name], value
    ), f"{name}: explicitly conflicting lifecycle clause (CFR §7.0.4, §§7.1–7.3)"


def assert_header_line_claims(name: str, text: str, triggers: dict[str, int]) -> None:
    """Bounded current trigger claims; ignore explicitly historical/quoted lines.

    Entry-length guidance such as ≤5 lines is not a whole-file trigger. This does
    not scan body incidents or version history for numbers and rewrite history.
    """
    for line in header(text).splitlines():
        if re.search(
            r"previously|historically|formerly|used to|stale, do not cite|^\s*>\s*quoted",
            line,
            re.I,
        ):
            continue
        claims = re.findall(
            r">\s*(\d+)\s+lines|(?:trigger|target|threshold)\s*:\s*(\d+)\s+lines",
            line,
            re.I,
        )
        for pair in claims:
            value = int(next(n for n in pair if n))
            assert name in triggers and value == triggers[name], (
                f"{name}: current line trigger {value} disagrees with CFR §7.0.4: {triggers.get(name)}"
            )
