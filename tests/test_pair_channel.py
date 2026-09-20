"""Hermetic tests for the pair-channel instrument (global-skills/pair-channel/channel.py).

The protocol's only concurrency guard is "the session named by TURN writes; the
other waits". The first written spec made that guard a rule and a naive grep,
and another project showed the grep matched forever from message #2 on because
every message carried its own frozen `TURN:` echo. These tests pin the
structural fix: one TURN location, a locked compare-and-append that refuses
the out-of-turn write, and a watch that reads STATE rather than the thread.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent / "global-skills" / "pair-channel"
SCRIPT = SKILL / "channel.py"
TEMPLATE = SKILL / "template.md"
PROCEDURE = SKILL / "procedure.md"

SETS = [
    "CHANNEL_NAME=tempcomT",
    "IMPLEMENTER_HOST=Codex CLI",
    "REVIEWER_HOST=Claude Code",
    "REVIEWER_WORKTREE=/tmp/rev",
    "REVIEWER_TRANSCRIPT=/tmp/rev.jsonl",
]


def run(*args: str, env: dict[str, str] | None = None, timeout: float = 30):
    full_env = os.environ.copy()
    full_env.update(env or {})
    return subprocess.run(  # nosec B603
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=full_env,
    )


def msg(tmp_path: Path, name: str, heading: str, body: str = "body\n") -> Path:
    p = tmp_path / name
    p.write_text(f"{heading}\n\n{body}", encoding="utf-8")
    return p


def append(
    channel: Path, role: str, m: Path, *extra: str, env=None, timeout: float = 30
):
    return run(
        "append",
        str(channel),
        "--role",
        role,
        "--message",
        str(m),
        *extra,
        env=env,
        timeout=timeout,
    )


@pytest.fixture
def channel(tmp_path: Path) -> Path:
    ch = tmp_path / "tempcomT.md"
    args = ["init", str(ch)]
    for s in SETS:
        args += ["--set", s]
    result = run(*args)
    assert result.returncode == 0, result.stderr
    return ch


def _first(channel: Path, tmp_path: Path, flip: str | None = None) -> None:
    m = msg(tmp_path, "m1.md", "## #1 REVIEWER PROPOSE P0 — channel test")
    extra = ("--flip-to", flip) if flip else ()
    result = append(channel, "REVIEWER", m, *extra)
    assert result.returncode == 0, result.stderr


# --- init / check ------------------------------------------------------------


def test_init_produces_a_valid_channel_and_reports_unfilled_placeholders(channel: Path):
    text = channel.read_text(encoding="utf-8")
    assert len(re.findall(r"^TURN:", text, re.M)) == 1
    assert "{{IMPLEMENTER_WORKTREE}}" in text  # left for the implementer (rule 1)
    result = run("check", str(channel))
    assert result.returncode == 0 and "no messages yet" in result.stdout


def test_init_refuses_to_overwrite(channel: Path):
    result = run("init", str(channel))
    assert result.returncode == 1 and "refusing to overwrite" in result.stderr


def test_missing_channel_is_exit_2_for_every_reader(tmp_path: Path):
    missing = str(tmp_path / "missing.md")
    m = msg(tmp_path, "m.md", "## #1 REVIEWER PROPOSE P0")
    for args in (
        ("state", missing),
        ("check", missing),
        ("append", missing, "--role", "REVIEWER", "--message", str(m)),
        ("fill", missing, "--role", "REVIEWER", "--set", "X=y"),
        ("watch", missing, "--role", "REVIEWER", "--timeout", "1"),
    ):
        result = run(*args)
        assert result.returncode == 2, (args, result.stderr)


# --- append: the compare-and-append guard ------------------------------------


def test_append_in_turn_stamps_bumps_and_flips(channel: Path, tmp_path: Path):
    m = msg(tmp_path, "m1.md", "## #1 REVIEWER PROPOSE P0 — channel test")
    result = append(
        channel,
        "REVIEWER",
        m,
        "--flip-to",
        "IMPLEMENTER",
        "--set-open",
        "P0",
        "--tz",
        "UTC",
    )
    assert result.returncode == 0, result.stderr
    text = channel.read_text(encoding="utf-8")
    assert "TURN: IMPLEMENTER" in text and "NEXT_SEQ: 2" in text and "OPEN: P0" in text
    last = text.rstrip().splitlines()[-1]
    assert last.startswith("Reviewed: ") and "(UTC)" in last
    assert len(re.findall(r"^TURN:", text, re.M)) == 1


def test_append_refuses_out_of_turn_write(channel: Path, tmp_path: Path):
    m = msg(tmp_path, "m1.md", "## #1 IMPLEMENTER CONFIRM P0")
    result = append(channel, "IMPLEMENTER", m)
    assert result.returncode == 1 and "not your turn" in result.stderr
    assert "## #1" not in channel.read_text(encoding="utf-8")


def test_append_refuses_wrong_and_duplicate_sequence(channel: Path, tmp_path: Path):
    wrong = msg(tmp_path, "w.md", "## #2 REVIEWER PROPOSE P0")
    result = append(channel, "REVIEWER", wrong)
    assert result.returncode == 1 and "NEXT_SEQ is 1" in result.stderr
    _first(channel, tmp_path)
    again = msg(tmp_path, "m1.md", "## #1 REVIEWER PROPOSE P0")
    result = append(channel, "REVIEWER", again)
    assert result.returncode == 1 and "NEXT_SEQ is 2" in result.stderr


def test_append_refuses_a_second_turn_location_but_allows_a_fenced_quote(
    channel: Path, tmp_path: Path
):
    """The exact failure the other project hit: a per-message TURN echo."""
    bad = msg(
        tmp_path, "bad.md", "## #1 REVIEWER PROPOSE P0", "body\n\nTURN: IMPLEMENTER\n"
    )
    result = append(channel, "REVIEWER", bad)
    assert result.returncode == 1 and "TURN lives only in STATE" in result.stderr

    quoted = msg(
        tmp_path,
        "ok.md",
        "## #1 REVIEWER PROPOSE P0",
        "STATE should read:\n\n```\nTURN: IMPLEMENTER\n```\n\nand the next heading is `## #2 IMPLEMENTER CONFIRM P0`.\n",
    )
    result = append(channel, "REVIEWER", quoted)
    assert result.returncode == 0, result.stderr
    assert run("check", str(channel)).returncode == 0


def test_append_refuses_heading_role_mismatch_and_two_messages(
    channel: Path, tmp_path: Path
):
    m = msg(tmp_path, "m1.md", "## #1 IMPLEMENTER PROPOSE P0")
    result = append(channel, "REVIEWER", m)
    assert result.returncode == 1 and "names IMPLEMENTER" in result.stderr
    two = msg(
        tmp_path, "two.md", "## #1 REVIEWER PROPOSE P0", "x\n\n## #2 REVIEWER ANSWER\n"
    )
    result = append(channel, "REVIEWER", two)
    assert result.returncode == 1 and "one message per append" in result.stderr


def test_out_of_turn_relay_bumps_seq_but_cannot_flip(channel: Path, tmp_path: Path):
    _first(channel, tmp_path, flip="IMPLEMENTER")
    relay = msg(
        tmp_path,
        "m2.md",
        "## #2 REVIEWER ANSWER — directive (human-directed, written out of turn)",
    )
    result = append(
        channel, "REVIEWER", relay, "--out-of-turn", "--flip-to", "REVIEWER"
    )
    assert result.returncode == 1 and "may not flip" in result.stderr
    result = append(channel, "REVIEWER", relay, "--out-of-turn")
    assert result.returncode == 0, result.stderr
    text = channel.read_text(encoding="utf-8")
    assert "TURN: IMPLEMENTER" in text and "NEXT_SEQ: 3" in text
    unlabeled = msg(tmp_path, "m3.md", "## #3 REVIEWER ANSWER — quiet relay")
    result = append(channel, "REVIEWER", unlabeled, "--out-of-turn")
    assert result.returncode == 1 and "out of turn" in result.stderr


# --- the race: two writers, one lock -------------------------------------------


def test_two_concurrent_appends_produce_exactly_one_message(
    channel: Path, tmp_path: Path
):
    """Both writers pass every STATE check before either writes. Without the lock,
    the second os.replace silently discards the first message and both exit 0.
    PAIR_CHANNEL_HOLD_SECONDS widens the window deterministically."""
    _first(channel, tmp_path, flip="IMPLEMENTER")
    a = msg(tmp_path, "a.md", "## #2 IMPLEMENTER DONE P0", "implementer's message\n")
    b = msg(
        tmp_path,
        "b.md",
        "## #2 REVIEWER ANSWER — relay (human-directed, written out of turn)",
    )
    env = os.environ.copy()
    env["PAIR_CHANNEL_TESTING"] = "1"
    env["PAIR_CHANNEL_HOLD_SECONDS"] = "1.0"
    procs = [
        subprocess.Popen(  # nosec B603
            [
                sys.executable,
                str(SCRIPT),
                "append",
                str(channel),
                "--role",
                role,
                "--message",
                str(m),
                *extra,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        for role, m, extra in (
            ("IMPLEMENTER", a, ()),
            ("REVIEWER", b, ("--out-of-turn",)),
        )
    ]
    results = [p.communicate(timeout=30) for p in procs]
    codes = [p.returncode for p in procs]
    assert sorted(codes) == [0, 1], (codes, results)
    refused = results[codes.index(1)][1]
    # The loser waited on the lock, then saw the winner's STATE and was refused on sequence.
    assert "STATE NEXT_SEQ is 3" in refused or "lock" in refused, refused
    text = channel.read_text(encoding="utf-8")
    assert text.count("\n## #2 ") == 1
    assert "NEXT_SEQ: 3" in text
    assert run("check", str(channel)).returncode == 0


# --- fill / ledger: the rule-1 carve-outs go through the tool too ----------------


def test_fill_replaces_placeholders_only_for_the_turn_holder(
    channel: Path, tmp_path: Path
):
    result = run(
        "fill",
        str(channel),
        "--role",
        "IMPLEMENTER",
        "--set",
        "IMPLEMENTER_WORKTREE=/tmp/impl",
    )
    assert result.returncode == 1 and "not your turn" in result.stderr
    _first(channel, tmp_path, flip="IMPLEMENTER")
    result = run(
        "fill",
        str(channel),
        "--role",
        "IMPLEMENTER",
        "--set",
        "IMPLEMENTER_WORKTREE=/tmp/impl",
        "--set",
        "IMPLEMENTER_TRANSCRIPT=/tmp/impl.jsonl",
    )
    assert result.returncode == 0, result.stderr
    text = channel.read_text(encoding="utf-8")
    assert "`/tmp/impl`" in text and "{{" not in text
    result = run(
        "fill",
        str(channel),
        "--role",
        "IMPLEMENTER",
        "--set",
        "IMPLEMENTER_WORKTREE=/again",
    )
    assert result.returncode == 1 and "no placeholder" in result.stderr


def test_ledger_adds_rows_in_order_and_refuses_duplicates(
    channel: Path, tmp_path: Path
):
    _first(channel, tmp_path, flip="IMPLEMENTER")
    for i, d in (("P1", "first decision"), ("DEV-1", "a deviation")):
        result = run(
            "ledger",
            str(channel),
            "--role",
            "IMPLEMENTER",
            "--id",
            i,
            "--decision",
            d,
            "--commit",
            "abc123",
        )
        assert result.returncode == 0, result.stderr
    text = channel.read_text(encoding="utf-8")
    ledger = text[text.index("## Decisions ledger") : text.index("## Thread")]
    rows = [line for line in ledger.splitlines() if line.startswith("| ")]
    assert rows[-2].startswith("| P1 |") and rows[-1].startswith("| DEV-1 |")
    result = run(
        "ledger",
        str(channel),
        "--role",
        "IMPLEMENTER",
        "--id",
        "P1",
        "--decision",
        "again",
    )
    assert result.returncode == 1 and "already has a row" in result.stderr
    result = run(
        "ledger", str(channel), "--role", "REVIEWER", "--id", "P2", "--decision", "x"
    )
    assert result.returncode == 1 and "not your turn" in result.stderr
    result = run(
        "ledger",
        str(channel),
        "--role",
        "IMPLEMENTER",
        "--id",
        "P3",
        "--decision",
        "a | b",
    )
    assert result.returncode == 1 and "may not contain" in result.stderr
    assert run("check", str(channel)).returncode == 0


# --- check: the invariants a naive file can violate ---------------------------


def test_check_fails_a_file_with_a_stray_turn_line(channel: Path):
    text = (
        channel.read_text(encoding="utf-8")
        + "\n## #1 REVIEWER PROPOSE P0\n\nbody\n\nTURN: IMPLEMENTER\n"
    )
    channel.write_text(text.replace("NEXT_SEQ: 1", "NEXT_SEQ: 2"), encoding="utf-8")
    result = run("check", str(channel))
    assert result.returncode == 1 and "outside STATE" in result.stderr


def test_check_fails_a_duplicated_state_heading(channel: Path):
    text = channel.read_text(encoding="utf-8")
    channel.write_text(text + "\n## STATE — stray copy\n", encoding="utf-8")
    result = run("check", str(channel))
    assert result.returncode == 1 and "'## STATE' headings" in result.stderr


def test_check_fails_a_duplicated_or_gapped_sequence(channel: Path):
    base = channel.read_text(encoding="utf-8").replace("NEXT_SEQ: 1", "NEXT_SEQ: 3")
    channel.write_text(
        base + "\n## #1 REVIEWER PROPOSE P0\n\n## #1 IMPLEMENTER CONFIRM P0\n",
        encoding="utf-8",
    )
    result = run("check", str(channel))
    assert result.returncode == 1 and "not strictly increasing" in result.stderr
    channel.write_text(
        base + "\n## #1 REVIEWER PROPOSE P0\n\n## #3 IMPLEMENTER CONFIRM P0\n",
        encoding="utf-8",
    )
    result = run("check", str(channel))
    assert result.returncode == 1 and "gap" in result.stderr


# --- watch: reads STATE, never the thread -------------------------------------


def test_watch_returns_when_state_names_you_and_ignores_thread_text(
    channel: Path, tmp_path: Path
):
    m = msg(
        tmp_path,
        "m1.md",
        "## #1 REVIEWER PROPOSE P0",
        "the implementer's turn comes next\n",
    )
    assert append(channel, "REVIEWER", m).returncode == 0
    result = run(
        "watch",
        str(channel),
        "--role",
        "IMPLEMENTER",
        "--interval",
        "0.05",
        "--timeout",
        "0.3",
    )
    assert result.returncode == 3, "watch must time out while STATE still says REVIEWER"
    result = run(
        "watch",
        str(channel),
        "--role",
        "REVIEWER",
        "--interval",
        "0.05",
        "--timeout",
        "1",
    )
    assert result.returncode == 0 and "turn: REVIEWER" in result.stdout


def test_watch_exits_2_when_the_channel_is_gone(tmp_path: Path):
    result = run(
        "watch", str(tmp_path / "missing.md"), "--role", "REVIEWER", "--timeout", "1"
    )
    assert result.returncode == 2 and "gone" in result.stderr


# --- the rules live in two files and must not drift ---------------------------


def _rules_body(text: str) -> str:
    """Everything after the Rules heading line up to the next section."""
    start = text.index("\n1. **Append-only thread.**")
    end = text.index("\n## ", start)
    return text[start:end].strip()


def test_template_rules_are_byte_identical_to_procedure_rules():
    assert _rules_body(TEMPLATE.read_text(encoding="utf-8")) == _rules_body(
        PROCEDURE.read_text(encoding="utf-8")
    )


def test_skill_md_is_thin_and_user_only():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in text
    assert len(text.splitlines()) <= 120


def test_protocol_standing_authorizes_messages_but_keeps_effects_gated():
    texts = {
        path.name: path.read_text(encoding="utf-8")
        for path in (SKILL / "SKILL.md", PROCEDURE, TEMPLATE)
    }
    retired = (
        "waits for plain-language authorization",
        "wait for a plain-language yes",
        "after the human has authorized that handoff",
    )
    for name, text in texts.items():
        normalized = " ".join(text.split())
        for phrase in retired:
            assert phrase not in text, f"{name} retains retired gate: {phrase}"
        for field in ("Accomplished", "Current task", "Other AI", "Next"):
            assert field in text, f"{name} omits status field: {field}"
        assert "proceed" in text and "without waiting" in text
        assert (
            "irreversible or external effects remain separately human-authorized"
            in normalized
        )


# --- round-2 review: fences, fill scoping, ledger heading, env guard, template --


def test_append_refuses_an_unbalanced_fence_so_later_headings_cannot_hide(
    channel: Path, tmp_path: Path
):
    """One unclosed ``` would flip the parser for the rest of the file."""
    odd = msg(
        tmp_path, "odd.md", "## #1 REVIEWER PROPOSE P0", "quote:\n\n```\nunclosed\n"
    )
    result = append(channel, "REVIEWER", odd)
    assert result.returncode == 1 and "unbalanced code fence" in result.stderr
    assert "## #1" not in channel.read_text(encoding="utf-8")


def test_check_names_an_unbalanced_file_instead_of_a_gap(channel: Path, tmp_path: Path):
    _first(channel, tmp_path)
    text = channel.read_text(encoding="utf-8")
    channel.write_text(text + "\n```\nraw edit left this open\n", encoding="utf-8")
    result = run("check", str(channel))
    assert result.returncode == 1 and "unbalanced code fence" in result.stderr


def test_fill_is_scoped_to_the_header_and_never_rewrites_thread_text(
    channel: Path, tmp_path: Path
):
    _first(channel, tmp_path, flip="IMPLEMENTER")
    quoted = msg(
        tmp_path,
        "q.md",
        "## #2 IMPLEMENTER CONFIRM P0",
        "the template still shows:\n\n```\n{{IMPLEMENTER_TRANSCRIPT}}\n```\n",
    )
    assert append(channel, "IMPLEMENTER", quoted).returncode == 0
    result = run(
        "fill",
        str(channel),
        "--role",
        "IMPLEMENTER",
        "--set",
        "IMPLEMENTER_TRANSCRIPT=/tmp/impl.jsonl",
    )
    assert result.returncode == 0, result.stderr
    text = channel.read_text(encoding="utf-8")
    header, thread = text.split("## Thread", 1)
    assert "/tmp/impl.jsonl" in header and "{{IMPLEMENTER_TRANSCRIPT}}" not in header
    assert "{{IMPLEMENTER_TRANSCRIPT}}" in thread  # history untouched (rule 1)


def test_check_fails_a_duplicated_ledger_heading(channel: Path):
    text = channel.read_text(encoding="utf-8")
    channel.write_text(text + "\n## Decisions ledger — stray copy\n", encoding="utf-8")
    result = run("check", str(channel))
    assert result.returncode == 1 and "'## Decisions ledger' headings" in result.stderr


def test_missing_channel_leaves_no_orphan_lock_and_missing_template_is_refused(
    tmp_path: Path,
):
    missing = tmp_path / "missing.md"
    m = msg(tmp_path, "m.md", "## #1 REVIEWER PROPOSE P0")
    assert append(missing, "REVIEWER", m).returncode == 2
    assert not (tmp_path / "missing.md.lock").exists()
    result = run(
        "init", str(tmp_path / "new.md"), "--template", str(tmp_path / "nope.md")
    )
    assert result.returncode == 1 and "template not found" in result.stderr


def test_hold_env_var_is_inert_without_the_testing_flag(channel: Path, tmp_path: Path):
    m = msg(tmp_path, "m1.md", "## #1 REVIEWER PROPOSE P0")
    env = {"PAIR_CHANNEL_HOLD_SECONDS": "30"}
    if "PAIR_CHANNEL_TESTING" in os.environ:
        env["PAIR_CHANNEL_TESTING"] = "0"
    result = append(channel, "REVIEWER", m, env=env, timeout=10)
    assert result.returncode == 0, result.stderr


def test_section_headings_may_be_quoted_inside_a_fence(channel: Path, tmp_path: Path):
    """The duplicate-heading guard must be fence-aware like every other check."""
    layout = msg(
        tmp_path,
        "layout.md",
        "## #1 REVIEWER ANSWER — explaining the layout",
        "The sections run in order:\n\n```\n## STATE\n## Rules\n## Decisions ledger\n## Thread\n```\n",
    )
    result = append(channel, "REVIEWER", layout, "--flip-to", "IMPLEMENTER")
    assert result.returncode == 0, result.stderr
    assert run("check", str(channel)).returncode == 0
    # And the real headings are still found where they belong.
    result = run(
        "ledger", str(channel), "--role", "IMPLEMENTER", "--id", "P1", "--decision", "x"
    )
    assert result.returncode == 0, result.stderr
    result = run(
        "fill",
        str(channel),
        "--role",
        "IMPLEMENTER",
        "--set",
        "IMPLEMENTER_WORKTREE=/w",
    )
    assert result.returncode == 0, result.stderr
