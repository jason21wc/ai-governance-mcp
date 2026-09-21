"""Source-backed method relationships, independent of ranking and enforcement.

Parse a document's heading tree separately from extraction boundaries so skipped
structural headings can still supply explicit governing declarations.
"""

import json
import re
from pathlib import PurePosixPath

from .models import (
    GovernanceDeclaration,
    GovernanceHeading,
    GovernanceReference,
    Method,
    MethodGovernanceContext,
    Principle,
)

_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_FIELD = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*)?(Implements|Constitutional Basis)"
    r"(?:\*\*)?\s*:(?:\*\*)?\s*(.*)$",
    re.IGNORECASE,
)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LABELED_FIELD = re.compile(r"^\s*(?:[-*+]\s+)?\*\*[^*\n]+(?::\*\*|\*\*\s*:)")


def attach_context(methods: list[Method], source: str, source_document: str) -> None:
    """Attach declarations without changing any extracted body or boundary."""
    lines = source.splitlines()
    headings: list[dict] = []
    stack: list[int] = []
    declarations: list[tuple[list[int], GovernanceDeclaration]] = []
    fence = None
    i = 0
    while i < len(lines):
        line = lines[i]
        match = _FENCE.match(line)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif (
                token[0] == fence[0]
                and len(token) >= len(fence)
                and not line[match.end() :].strip()
            ):
                fence = None
            i += 1
            continue
        if fence:
            i += 1
            continue
        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            while stack and headings[stack[-1]]["level"] >= level:
                stack.pop()
            headings.append(
                {
                    "level": level,
                    "title": heading.group(2),
                    "line": i + 1,
                    "parents": stack[:],
                }
            )
            stack.append(len(headings) - 1)
        field = _FIELD.match(line)
        if field:
            start = i
            # Continuation is only a contiguous bullet list, optionally after one
            # blank line. Ordinary prose is never promoted into a declaration.
            end = i + 1
            if end < len(lines) and not lines[end].strip():
                end += 1
            while (
                end < len(lines)
                and re.match(r"^\s*[-*+]\s+", lines[end])
                and not _LABELED_FIELD.match(lines[end])
                and not _FIELD.match(lines[end])
            ):
                end += 1
            if not any(re.match(r"^\s*[-*+]\s+", x) for x in lines[i + 1 : end]):
                end = i + 1
            raw = "\n".join(lines[start:end])
            declarations.append(
                (
                    stack[:],
                    GovernanceDeclaration(
                        label="Implements"
                        if field.group(1).lower() == "implements"
                        else "Constitutional Basis",
                        raw=raw,
                        line_range=(start + 1, end),
                        origin="method",
                        heading=headings[stack[-1]]["title"] if stack else "",
                    ),
                )
            )
            i = end
            continue
        i += 1

    basename = PurePosixPath(source_document).name
    layer = (
        "rules_of_procedure"
        if basename == "rules-of-procedure.md"
        else "federal_regulations"
        if re.fullmatch(r"title-\d+-.+-cfr\.md", basename)
        else "unknown"
    )
    by_line = {h["line"]: n for n, h in enumerate(headings)}
    for method in methods:
        own = by_line.get(method.line_range[0])
        parents = headings[own]["parents"] if own is not None else []
        records = []
        for owners, declaration in declarations:
            direct = (
                method.line_range[0]
                <= declaration.line_range[0]
                <= method.line_range[1]
            )
            # An ancestor declaration belongs to that ancestor's own introductory
            # section, not a sibling subtree or a later section after this method.
            inherited = (
                not owners or owners[-1] in parents
            ) and declaration.line_range[0] < method.line_range[0]
            if direct or inherited:
                records.append(
                    declaration.model_copy(
                        update={"origin": "method" if direct else "ancestor"}, deep=True
                    )
                )
        title = headings[own]["title"] if own is not None else method.title
        section = re.match(r"(?:Part\s+)?(\d+(?:\.\d+)*)", title)
        method.governance_context = MethodGovernanceContext(
            source_document=source_document,
            section=section.group(1) if section else "",
            enclosing_headings=[
                GovernanceHeading(title=headings[n]["title"], line=headings[n]["line"])
                for n in parents
            ],
            framework_layer=layer,
            declarations=records,
        )


def _normalized(text: str) -> str:
    return " ".join(text.casefold().replace("&", " and ").split())


def _references(raw: str, protected_titles: list[str] | None = None) -> list[str]:
    """Split an explicit field, preserving unsplittable wording as unresolved."""
    first, *rest = raw.splitlines()
    match = _FIELD.match(first)
    body = match.group(2) if match else first
    body += "\n" + "\n".join(re.sub(r"^\s*[-*+]\s+", "", line) for line in rest)
    # A delimiter in an exact canonical title is evidence, not a list separator.
    # Keep the original text; only mark delimiters that must remain in that title.
    protected = set()
    for title in protected_titles or []:
        if not any(c in title for c in ",;·+"):
            continue
        pattern = r"\s+".join(
            r"(?:&|and)" if word.casefold() in {"&", "and"} else re.escape(word)
            for word in title.split()
        )
        for match in re.finditer(r"(?<!\w)" + pattern + r"(?!\w)", body, re.I):
            protected.update(range(match.start(), match.end()))
    # Commas/semicolons in parenthetic explanations aren't reference separators.
    parts, current, depth = [], [], 0
    for position, char in enumerate(body):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if depth == 0 and char in ",;·+\n" and position not in protected:
            if "".join(current).strip():
                parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if "".join(current).strip():
        parts.append("".join(current).strip())
    return parts


def resolve_context(methods: list[Method], principles: list[Principle]) -> None:
    """Second pass: exact evidence only, with domain-scoped bare titles."""
    ids: dict[str, list[Principle]] = {}
    titles: dict[str, list[Principle]] = {}
    for principle in principles:
        # Matching metadata aliases are search synonyms, not ID redirects.
        for key in {principle.id, *principle.aliases}:
            ids.setdefault(key, []).append(principle)
        titles.setdefault(_normalized(principle.title), []).append(principle)
    method_ids = {key for method in methods for key in [method.id, *method.aliases]}

    def clean(text: str) -> str:
        text = re.split(r"\s+[—–]\s+|\.\s+See also\b", text, maxsplit=1)[0]
        return re.sub(r"^Derived from\s+", "", text.strip("`* ."), flags=re.I)

    def exact_title(text: str, domains: set[str] | None) -> list[Principle]:
        name = clean(text)
        # Try the complete title first: parentheses may belong to its name.
        for candidate in (name, re.sub(r"\s*\([^()]*\)", "", name).strip("`* .")):
            found = [
                p
                for p in titles.get(_normalized(candidate), [])
                if domains is None or p.domain in domains
            ]
            if found:
                return found
        return []

    def alternate_partition(text: str, scope: set[str]) -> bool:
        # Consider every complete partition, not just single-word atoms.
        cuts, depth = [0], 0
        for position, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)
            elif depth == 0 and char in ",;·+":
                cuts.append(position + 1)
        cuts.append(len(text) + 1)
        if len(cuts) <= 2:
            return False
        # Leave pathological source titles unresolved rather than spend
        # unbounded work choosing an interpretation.
        if len(cuts) > 64:
            return True
        pieces = {0: 0}
        for end in cuts[1:]:
            for start in cuts:
                if start >= end or start not in pieces:
                    continue
                part = text[start : end - 1].strip()
                found = ids.get(clean(part), []) or exact_title(part, scope)
                if len(found) == 1:
                    pieces[end] = max(pieces.get(end, 0), pieces[start] + 1)
        return pieces.get(cuts[-1], 0) > 1

    for method in methods:
        if method.governance_context is None:
            continue
        scope = {method.domain, "constitution"}
        protected_titles = [p.title for p in principles if p.domain in scope]
        for declaration in method.governance_context.declarations:
            declaration.references = []
            for text in _references(declaration.raw, protected_titles):
                # Strip markup and explanatory suffixes, never search arbitrary
                # prose for a title or ID (which would manufacture a relation).
                name = clean(text)
                explicit = re.findall(r"\(\s*`([a-z][a-z0-9-]+)`\s*\)", name)
                evidence_conflict = False
                if len(explicit) == 1:
                    label = clean(re.sub(r"\(\s*`[^`]+`\s*\)", "", name))
                    named = ids.get(label, []) or exact_title(label, None)
                    identified = ids.get(explicit[0], [])
                    evidence_conflict = bool(named) and (
                        len(named) != 1
                        or len(identified) != 1
                        or named[0].id != identified[0].id
                    )
                    name = explicit[0]
                elif len(explicit) > 1:
                    evidence_conflict = True
                else:
                    name = name.strip("`* .")
                candidates = ids.get(name, [])
                if not candidates:
                    # Canonical IDs and explicit redirect aliases may carry a
                    # parenthetical explanation just like human-readable titles.
                    id_name = re.sub(r"\s*\([^()]*\)", "", name).strip("`* .")
                    candidates = ids.get(id_name, [])
                if not candidates:
                    candidates = exact_title(name, scope)
                ambiguous_partition = (
                    not explicit
                    and len(candidates) == 1
                    and alternate_partition(text, scope)
                )
                if evidence_conflict:
                    reason = "conflicting_evidence"
                elif ambiguous_partition:
                    reason = "ambiguous_partition"
                elif name in method_ids or "-method-" in name:
                    reason = "method_target"
                elif re.search(
                    r"\b\d+\s*[-–]\s*\d+\b|\b[A-Z]\d+\s*[-–]\s*(?:[A-Z])?\d+\b", name
                ):
                    reason = "range"
                elif len(candidates) == 1:
                    declaration.references.append(
                        GovernanceReference(
                            text=text, status="resolved", principle_id=candidates[0].id
                        )
                    )
                    continue
                else:
                    reason = "ambiguous" if candidates else "not_found"
                declaration.references.append(
                    GovernanceReference(text=text, reason=reason)
                )


def _wire_size(value: dict) -> int:
    """Largest projection on the wire: evaluation nests pretty JSON at depth 3."""
    pretty = json.dumps(value, indent=2)
    return max(len(json.dumps(value)), len(pretty) + 6 * pretty.count("\n"))


def compact_context(method: Method) -> dict:
    """At most 512 wire characters; omit whole values, never cut IDs.

    get_principle uses the exact method ID already present on its enclosing entry.
    The projection is advisory normative context, not an enforcement receipt.
    """
    context = method.governance_context
    if context is None:
        return {"availability": "unavailable", "detail": "get_principle"}
    resolved = list(
        dict.fromkeys(
            r.principle_id
            for d in context.declarations
            for r in d.references
            if r.status == "resolved" and r.principle_id
        )
    )
    unresolved = sum(
        r.status == "unresolved" for d in context.declarations for r in d.references
    )
    result = {
        "availability": "available",
        "authority": context.authority,
        "rule": "Methods cannot override principles",
        "layer": context.framework_layer,
        "principle_ids": [],
        "unresolved": unresolved,
        "omitted": len(resolved) + 2,
        "detail": "get_principle",
    }
    for key, value in [
        ("source", context.source_document),
        ("section", context.section),
    ]:
        candidate = {**result, key: value, "omitted": result["omitted"] - 1}
        if _wire_size(candidate) <= 512:
            result = candidate
    for principle_id in resolved:
        candidate = {
            **result,
            "principle_ids": [*result["principle_ids"], principle_id],
            "omitted": result["omitted"] - 1,
        }
        if _wire_size(candidate) <= 512:
            result = candidate
    return result


def full_context(method: Method) -> dict:
    if method.governance_context is None:
        return {"availability": "unavailable"}
    return {
        "availability": "available",
        "rule": "Methods cannot override principles",
        **method.governance_context.model_dump(),
    }
