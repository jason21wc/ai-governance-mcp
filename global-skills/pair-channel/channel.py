#!/usr/bin/env python3
"""pair-channel helper — the instrument behind the paired-session protocol.

Two live sessions (IMPLEMENTER and REVIEWER) share ONE untracked channel file.
The protocol's concurrency guard is "only the session named by TURN may write".
This script makes that guard checkable instead of voluntary. Every write to
the channel goes through it:

  init    create a channel file from template.md with placeholders filled
  state   print the STATE block (TURN, NEXT_SEQ, OPEN, ESCALATED)
  append  add one message: refuses out-of-turn writes, wrong or duplicate
          sequence numbers, unbalanced code fences, and any thread line that
          would create a second `TURN:` location; stamps the timestamp;
          updates STATE; re-verifies
  fill    replace a {{PLACEHOLDER}} in the header tables above the Rules
          (rule 1 carve-out; the implementer fills its own rows in message #2)
  ledger  add one row to the Decisions ledger (rule 1 carve-out)
  watch   block until STATE says it is your turn (reads STATE only — never the
          thread — so frozen text cannot wake you); exits 2 if the file is gone
  check   verify every structural invariant of a channel file

WHY TURN LIVES IN ONE PLACE
---------------------------
The first written spec put a `TURN:` echo at the end of every message and told
the waiting session to `grep -q '^TURN: REVIEWER'`. Because the thread is
append-only, the file permanently contained both role strings from message #2
on, and the watch matched instantly for both sides, forever. Another project
hit it on a live channel. The fix is structural: TURN exists only in STATE,
`append` refuses any thread line beginning with `TURN:` (outside a fenced code
block, where protocol syntax may be quoted), `watch` parses STATE rather than
searching the file, and `check` fails a file that breaks the invariant.

WHY THERE IS A LOCK
-------------------
An out-of-turn human relay is the one moment two writers can be live at once,
and on the trial channel it produced a duplicate message number. A size check
before the write only narrows that window. Every mutating command therefore
holds an exclusive `flock` on `<channel>.lock` across its read, validation and
atomic replace, so a second writer either waits and then sees the new STATE
(and refuses on sequence) or times out with a clear reason. Cooperating
writers on one machine cannot lose an update; the size check stays as a belt
for a writer that bypasses this script.

WHY FENCES MUST BALANCE
-----------------------
Fence-aware scanning is what lets a message quote `TURN:` or a heading. It
also means one unclosed ``` would flip the parser for the rest of the file,
hiding every later heading. So `append` refuses a message with an odd number
of fence lines, `init` refuses an unbalanced template, and `verify` names an
unbalanced file instead of misreporting it as a sequence gap. The same hazard
is guarded on this repo's governance corpus (tests/test_repo_hygiene.py).

Exit codes: 0 ok · 1 precondition/invariant failed (reason printed) · 2 usage
or channel file missing · 3 watch timed out.
"""

from __future__ import annotations

import argparse
import fcntl
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

ROLES = ("IMPLEMENTER", "REVIEWER")
STATE_KEYS = ("TURN", "NEXT_SEQ", "OPEN", "ESCALATED")
HEADING_RE = re.compile(r"^## #(\d+) (IMPLEMENTER|REVIEWER) (\S.*)$")
STATE_HEAD_RE = re.compile(r"^## STATE\b.*$", re.M)
RULES_HEAD_RE = re.compile(r"^## (?:\d+\. )?Rules\b.*$", re.M)
LEDGER_HEAD_RE = re.compile(r"^## Decisions ledger\b.*$", re.M)
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")
TEMPLATE = Path(__file__).resolve().parent / "template.md"
LOCK_TIMEOUT = 15.0


class ChannelError(Exception):
    """A precondition or invariant failed. The message is the reason."""


class MissingChannel(ChannelError):
    """The channel file does not exist (exit 2, distinct from a refusal)."""


# --- parsing -----------------------------------------------------------------


def _read(path: Path) -> str:
    if not path.is_file():
        raise MissingChannel(f"channel file not found: {path}")
    return path.read_text(encoding="utf-8")


def _is_fence(line: str) -> bool:
    return line.lstrip().startswith("```")


def _fence_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if _is_fence(line))


def _lines_with_fence(text: str) -> Iterator[tuple[str, bool]]:
    """Yield (line, inside_fenced_code_block) for every line of text."""
    in_fence = False
    for line in text.splitlines():
        if _is_fence(line):
            in_fence = not in_fence
            yield line, True
            continue
        yield line, in_fence


class _Span:
    """Offsets of one matched line; mirrors the re.Match API the callers use."""

    def __init__(self, start: int, end: int) -> None:
        self._start, self._end = start, end

    def start(self) -> int:
        return self._start

    def end(self) -> int:
        return self._end


def _single(pattern: re.Pattern[str], text: str, what: str) -> _Span:
    """The one unfenced line matching pattern. A fenced quote of a heading is text."""
    found: list[_Span] = []
    offset = 0
    for line, fenced in _lines_with_fence(text):
        if not fenced and pattern.match(line):
            found.append(_Span(offset, offset + len(line)))
        offset += len(line) + 1
    if not found:
        raise ChannelError(f"no '{what}' heading")
    if len(found) > 1:
        raise ChannelError(f"{len(found)} '{what}' headings; exactly one is allowed")
    return found[0]


def _state_span(text: str) -> tuple[int, int]:
    """Return (start, end) offsets of the fenced block after the STATE heading."""
    head = _single(STATE_HEAD_RE, text, "## STATE")
    fence_open = text.find("```", head.end())
    if fence_open < 0:
        raise ChannelError("STATE heading has no fenced block")
    body_start = text.find("\n", fence_open) + 1
    fence_close = text.find("```", body_start)
    if fence_close < 0:
        raise ChannelError("STATE fenced block is not closed")
    return body_start, fence_close


def parse_state(text: str) -> dict[str, str]:
    start, end = _state_span(text)
    state: dict[str, str] = {}
    for line in text[start:end].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            state[key.strip()] = value.strip()
    missing = [k for k in STATE_KEYS if k not in state]
    if missing:
        raise ChannelError(f"STATE is missing {', '.join(missing)}")
    if state["TURN"] not in ROLES:
        raise ChannelError(f"STATE TURN is {state['TURN']!r}, not one of {ROLES}")
    if not state["NEXT_SEQ"].isdigit():
        raise ChannelError(f"STATE NEXT_SEQ is {state['NEXT_SEQ']!r}, not an integer")
    return state


def headings(text: str) -> list[tuple[int, str, str]]:
    """Message headings outside fenced code blocks, in file order."""
    out = []
    for line, fenced in _lines_with_fence(text):
        if fenced:
            continue
        m = HEADING_RE.match(line)
        if m:
            out.append((int(m.group(1)), m.group(2), m.group(3)))
    return out


def _stray_turn_lines(text: str) -> int:
    """Lines beginning 'TURN:' outside every fenced block (STATE is fenced)."""
    return sum(
        1
        for line, fenced in _lines_with_fence(text)
        if not fenced and line.startswith("TURN:")
    )


def _write_state(text: str, updates: dict[str, str]) -> str:
    start, end = _state_span(text)
    out = []
    for line in text[start:end].splitlines():
        key = line.partition(":")[0].strip()
        out.append(f"{key}: {updates[key]}" if key in updates else line)
    return text[:start] + "\n".join(out) + "\n" + text[end:]


# --- invariants --------------------------------------------------------------


def verify(text: str) -> dict[str, str]:
    """Raise ChannelError on the first broken invariant; return STATE if clean."""
    if _fence_count(text) % 2:
        raise ChannelError(
            "unbalanced code fence (odd number of ``` lines); every later heading "
            "would be hidden. Find the unclosed fence before writing anything."
        )
    state = parse_state(text)
    _single(RULES_HEAD_RE, text, "## Rules")
    _single(LEDGER_HEAD_RE, text, "## Decisions ledger")
    stray = _stray_turn_lines(text)
    if stray:
        raise ChannelError(
            f"{stray} line(s) begin with 'TURN:' outside STATE; TURN lives only in "
            "STATE. Quote protocol syntax inside a fenced code block."
        )
    nums = [n for n, _, _ in headings(text)]
    if nums != sorted(nums) or len(set(nums)) != len(nums):
        raise ChannelError(f"message sequence is not strictly increasing: {nums}")
    if nums and nums != list(range(1, nums[-1] + 1)):
        raise ChannelError(f"message sequence has a gap: {nums}")
    expected_next = (nums[-1] + 1) if nums else 1
    if int(state["NEXT_SEQ"]) != expected_next:
        last = nums[-1] if nums else 0
        raise ChannelError(
            f"NEXT_SEQ is {state['NEXT_SEQ']} but the thread ends at #{last}; "
            f"expected {expected_next}"
        )
    return state


# --- timestamp ---------------------------------------------------------------


def stamp(tz_name: str | None) -> str:
    if tz_name:
        from zoneinfo import ZoneInfo  # stdlib, 3.9+

        now = datetime.now(ZoneInfo(tz_name))
        return f"Reviewed: {now:%Y-%m-%d %H:%M:%S %Z} ({tz_name})"
    now = datetime.now().astimezone()
    return f"Reviewed: {now:%Y-%m-%d %H:%M:%S %Z}"


# --- locking and atomic write --------------------------------------------------


@contextmanager
def _locked(path: Path, timeout: float = LOCK_TIMEOUT) -> Iterator[None]:
    """Hold an exclusive flock on <channel>.lock for the whole read-validate-write."""
    if not path.is_file():
        raise MissingChannel(f"channel file not found: {path}")
    lock_path = path.with_name(path.name + ".lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise ChannelError(
                        "another writer holds the channel lock; wait, re-read STATE, retry"
                    ) from None
                time.sleep(0.05)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _replace(path: Path, expected_size: int, new_text: str) -> None:
    """Atomically replace path, refusing if its size changed since it was read."""
    if path.stat().st_size != expected_size:
        raise ChannelError(
            "channel file changed while composing; re-read STATE and retry"
        )
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(new_text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _test_hold() -> None:
    """Deterministic race window for tests only.

    Requires BOTH PAIR_CHANNEL_TESTING=1 and PAIR_CHANNEL_HOLD_SECONDS, so an
    inherited variable cannot slow real writes toward the lock timeout.
    """
    if os.environ.get("PAIR_CHANNEL_TESTING") != "1":
        return
    hold = float(os.environ.get("PAIR_CHANNEL_HOLD_SECONDS", "0") or 0)
    if hold > 0:
        time.sleep(hold)


def _require_turn(state: dict[str, str], role: str) -> None:
    if state["TURN"] != role:
        raise ChannelError(
            f"not your turn: STATE says TURN: {state['TURN']}, you are {role}. "
            "A watch that woke you is a signal, not authorization."
        )


# --- commands ----------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.file)
    if target.exists():
        raise ChannelError(f"refusing to overwrite existing channel: {target}")
    template = Path(args.template) if args.template else TEMPLATE
    if not template.is_file():
        raise ChannelError(f"template not found: {template}")
    text = template.read_text(encoding="utf-8")
    for pair in args.set or []:
        key, sep, value = pair.partition("=")
        if not sep:
            raise ChannelError(f"--set expects key=value, got {pair!r}")
        text = text.replace("{{" + key + "}}", value)
    verify(text)
    target.write_text(text, encoding="utf-8")
    left = sorted(set(PLACEHOLDER_RE.findall(text)))
    print(f"created {target}")
    if left:
        print("placeholders still to fill (channel.py fill): " + ", ".join(left))
    return 0


def cmd_state(args: argparse.Namespace) -> int:
    state = parse_state(_read(Path(args.file)))
    for key in STATE_KEYS:
        print(f"{key}: {state[key]}")
    return 0


def cmd_append(args: argparse.Namespace) -> int:
    path = Path(args.file)
    role = args.role
    if args.out_of_turn and args.flip_to:
        raise ChannelError("an out-of-turn message may not flip TURN")

    message = Path(args.message).read_text(encoding="utf-8").strip("\n")
    lines = message.splitlines()
    if not lines:
        raise ChannelError("message file is empty")
    match = HEADING_RE.match(lines[0])
    if not match:
        raise ChannelError(
            "message must begin with '## #<n> <ROLE> <TYPE …>'; got: " + lines[0][:80]
        )
    num, heading_role = int(match.group(1)), match.group(2)
    if heading_role != role:
        raise ChannelError(f"heading names {heading_role} but --role is {role}")
    if args.out_of_turn and "out of turn" not in lines[0].lower():
        raise ChannelError(
            "an out-of-turn message must say 'out of turn' in its heading"
        )
    if _fence_count(message) % 2:
        raise ChannelError(
            "message has an unbalanced code fence (odd number of ``` lines); close it"
        )
    body = "\n".join(lines[1:])
    if headings(body):
        raise ChannelError("one message per append; a second '## #' heading was found")
    if _stray_turn_lines(body) or lines[0].startswith("TURN:"):
        raise ChannelError(
            "message contains a line beginning with 'TURN:'; TURN lives only in STATE "
            "(quote protocol syntax inside a fenced code block)"
        )

    with _locked(path):
        text = _read(path)
        size = path.stat().st_size
        state = verify(text)
        if not args.out_of_turn:
            _require_turn(state, role)
        expected = int(state["NEXT_SEQ"])
        if num != expected:
            raise ChannelError(f"message is #{num} but STATE NEXT_SEQ is {expected}")

        updates = {"NEXT_SEQ": str(expected + 1)}
        if args.flip_to:
            updates["TURN"] = args.flip_to
        if args.set_open is not None:
            updates["OPEN"] = args.set_open
        if args.set_escalated is not None:
            updates["ESCALATED"] = args.set_escalated

        new_text = text.rstrip("\n") + "\n\n" + message + "\n\n" + stamp(args.tz) + "\n"
        new_text = _write_state(new_text, updates)
        verify(new_text)
        _test_hold()
        _replace(path, size, new_text)
        final = verify(_read(path))
    print(
        f"appended #{num} {role}; TURN: {final['TURN']}; NEXT_SEQ: {final['NEXT_SEQ']}"
    )
    return 0


def cmd_fill(args: argparse.Namespace) -> int:
    """Fill placeholders in the header region only (above the Rules heading)."""
    path = Path(args.file)
    with _locked(path):
        text = _read(path)
        size = path.stat().st_size
        state = verify(text)
        _require_turn(state, args.role)
        cut = _single(RULES_HEAD_RE, text, "## Rules").start()
        header, rest = text[:cut], text[cut:]
        for pair in args.set:
            key, sep, value = pair.partition("=")
            if not sep:
                raise ChannelError(f"--set expects key=value, got {pair!r}")
            token = "{{" + key + "}}"
            if token not in header:
                raise ChannelError(
                    f"no placeholder {token} left to fill above the Rules"
                )
            header = header.replace(token, value)
        new_text = header + rest
        verify(new_text)
        _test_hold()
        _replace(path, size, new_text)
        verify(_read(path))
    left = sorted(set(PLACEHOLDER_RE.findall(header)))
    print("filled " + ", ".join(p.partition("=")[0] for p in args.set))
    if left:
        print("placeholders still to fill: " + ", ".join(left))
    return 0


def cmd_ledger(args: argparse.Namespace) -> int:
    path = Path(args.file)
    for field in (args.id, args.decision, args.commit):
        if "|" in field or "\n" in field:
            raise ChannelError("ledger fields may not contain '|' or newlines")
    row = f"| {args.id} | {args.decision} | {args.commit} |"
    with _locked(path):
        text = _read(path)
        size = path.stat().st_size
        state = verify(text)
        _require_turn(state, args.role)
        head = _single(LEDGER_HEAD_RE, text, "## Decisions ledger")
        lines = text.splitlines(keepends=True)
        start = text[: head.start()].count("\n")
        end = len(lines)
        for i in range(start + 1, len(lines)):
            if lines[i].startswith("## "):
                end = i
                break
        table_rows = [i for i in range(start + 1, end) if lines[i].startswith("|")]
        if len(table_rows) < 2:
            raise ChannelError("Decisions ledger has no table header")
        if any(lines[i].startswith("| " + args.id + " |") for i in table_rows[2:]):
            raise ChannelError(f"ledger already has a row for id {args.id!r}")
        lines.insert(table_rows[-1] + 1, row + "\n")
        new_text = "".join(lines)
        verify(new_text)
        _test_hold()
        _replace(path, size, new_text)
        verify(_read(path))
    print(f"ledger row added: {args.id}")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    path = Path(args.file)
    deadline = time.monotonic() + args.timeout if args.timeout else None
    while True:
        if not path.is_file():
            print(f"channel file gone: {path}", file=sys.stderr)
            return 2
        state = parse_state(path.read_text(encoding="utf-8"))
        if state["TURN"] == args.role:
            print(
                f"turn: {args.role} (NEXT_SEQ {state['NEXT_SEQ']}; OPEN {state['OPEN']})"
            )
            return 0
        if deadline is not None and time.monotonic() >= deadline:
            print(f"timeout: TURN is still {state['TURN']}", file=sys.stderr)
            return 3
        time.sleep(args.interval)


def cmd_check(args: argparse.Namespace) -> int:
    text = _read(Path(args.file))
    state = verify(text)
    nums = [n for n, _, _ in headings(text)]
    span = f"sequence 1..{nums[-1]}" if nums else "no messages yet"
    print(
        f"ok: {len(nums)} message(s), {span}, TURN only in STATE, "
        f"TURN: {state['TURN']}, NEXT_SEQ: {state['NEXT_SEQ']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="channel.py", description=__doc__.split("\n\n")[0]
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create a channel file from the template")
    p.add_argument("file")
    p.add_argument(
        "--set", action="append", metavar="KEY=VALUE", help="fill a {{KEY}} placeholder"
    )
    p.add_argument("--template", help="alternate template path")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("state", help="print the STATE block")
    p.add_argument("file")
    p.set_defaults(func=cmd_state)

    p = sub.add_parser(
        "append", help="add one message (compare-and-append under a lock)"
    )
    p.add_argument("file")
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument(
        "--message",
        required=True,
        help="file whose first line is '## #<n> <ROLE> <TYPE>'",
    )
    p.add_argument("--flip-to", choices=ROLES, help="hand the turn to this role")
    p.add_argument("--set-open", metavar="TEXT", help="replace STATE OPEN")
    p.add_argument("--set-escalated", metavar="TEXT", help="replace STATE ESCALATED")
    p.add_argument(
        "--out-of-turn",
        action="store_true",
        help="human-directed relay written while TURN is the other role",
    )
    p.add_argument("--tz", help="IANA zone for the timestamp, e.g. America/Denver")
    p.set_defaults(func=cmd_append)

    p = sub.add_parser(
        "fill", help="fill {{PLACEHOLDER}} cells above the Rules (turn holder only)"
    )
    p.add_argument("file")
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument("--set", action="append", required=True, metavar="KEY=VALUE")
    p.set_defaults(func=cmd_fill)

    p = sub.add_parser("ledger", help="add a Decisions-ledger row (turn holder only)")
    p.add_argument("file")
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument("--id", required=True, help="e.g. P3, DEV-2, LESSON-1")
    p.add_argument("--decision", required=True)
    p.add_argument("--commit", default="none")
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("watch", help="block until STATE names your role")
    p.add_argument("file")
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument("--interval", type=float, default=3.0)
    p.add_argument("--timeout", type=float, default=0.0, help="seconds; 0 = forever")
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("check", help="verify channel invariants")
    p.add_argument("file")
    p.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MissingChannel as exc:
        print(f"MISSING: {exc}", file=sys.stderr)
        return 2
    except ChannelError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
