#!/usr/bin/env python3
"""Shared transcript scanner for governance and context engine compliance hooks.

Scans a Claude Code transcript (JSONL) for tool_use entries matching target
tool names. Supports a recency window to expire old calls.

Usage (governance mode):
    python3 scan_transcript.py <gov_tool_name> <ce_tool_name> <transcript_path> [window_size]
    Output: one of: both | gov_only | ce_only | neither

Usage (pattern mode):
    python3 scan_transcript.py --pattern <pattern> <transcript_path> [window_size]
    Output: true | false

Usage (subagent-dispatch mode, for the pre-push review checks):
    python3 scan_transcript.py --subagent <subagent_type> <transcript_path>
    Output: true | false   (anything else means malformed argv; the gate reads it as false)
      Requires an actual Task/Agent dispatch whose input.subagent_type matches. No
      recency window. Verifies a reviewer RAN, not that it saw the pushed diff.

Usage (contrarian-after-last-plan mode, for pre-exit-plan-mode-gate hook):
    python3 scan_transcript.py --contrarian-after-last-plan <transcript_path>
    Output: one of: allow | deny | bootstrap | error
      - allow: contrarian-reviewer tool_use found AFTER most recent prior ExitPlanMode
      - deny: prior ExitPlanMode exists but no contrarian invocation follows it
      - bootstrap: no prior ExitPlanMode in transcript (first plan of session)
      - error: read/parse failure (hook should treat as deny, fail-closed)

Usage (plan-action-atomicity mode, for pre-exit-plan-mode-gate hook WARN integration):
    python3 scan_transcript.py --plan-action-atomicity <plan_text_path>
    Output: one of: pass | warn | skip | error
      - pass: every Recommended Approach task entry names a single action category and has Files/Verification lines
      - warn: violations found (combined-action tasks, vague verbs, missing fields) — content emitted on stderr
      - skip: plan has no Recommended Approach section with detectable task entries (out of scope)
      - error: read/parse failure
    Plan text is read from the file at <plan_text_path>. Pass `-` to read from stdin.

Usage (tdd-test-existence mode, for pre-push-quality-gate hook WARN integration):
    python3 scan_transcript.py --tdd-test-existence <newline-separated-files-path>
    Output: one of: pass | warn | skip | error
      - pass: every new src/<dir>/<name>.py file has a paired tests/test_<name>.py
      - warn: at least one new src .py file lacks a paired test — pairs missing emitted on stderr
      - skip: no new src/*.py files in the input list (out of scope)
      - error: read/parse failure
    File list is read from the file at <files_path> (one path per line). Pass `-` to read from stdin.

Exit code: always 0 (decision encoded in stdout; hook interprets)
"""

import json
import os
import re
import sys
from collections import deque

# Action categories per plan-template Recommended Approach section
# (codified Commit 2 of Superpowers plan, session-126).
_ACTION_CATEGORIES = (
    "write failing test",
    "run test",
    "implement minimal code",
    "refactor",
    "verify",
)

# Vague verbs that disqualify a task heading as "atomic" — these signal
# the writer skipped the action-category discipline.
_VAGUE_VERBS = ("update", "improve", "handle", "fix up", "clean up", "address")


def scan_transcript(
    gov_target: str, ce_target: str, transcript_path: str, window_size: int = 0
) -> str:
    """Scan transcript for governance and CE tool calls.

    Args:
        gov_target: Tool name to match for governance (e.g. mcp__ai-governance__evaluate_governance)
        ce_target: Tool name to match for CE (e.g. mcp__context-engine__query_project)
        transcript_path: Path to JSONL transcript file
        window_size: If >0, only scan the last N lines (recency window). 0 = scan all.

    Returns:
        "both", "gov_only", "ce_only", or "neither"
    """
    gov_found = False
    ce_found = False

    try:
        with open(transcript_path, "r") as f:
            if window_size > 0:
                lines = deque(f, maxlen=window_size)
            else:
                lines = f

            for line in lines:
                # Fast pre-filter: skip lines that contain neither target
                if gov_target not in line and ce_target not in line:
                    continue
                # Only parse lines that contain at least one target string
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                # Check assistant tool_use entries
                msg = entry.get("message", {})
                if not isinstance(msg, dict):
                    continue
                for block in msg.get("content", []):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        name = block.get("name", "")
                        if name == gov_target:
                            gov_found = True
                        elif name == ce_target:
                            ce_found = True
                # Early exit if both found
                if gov_found and ce_found:
                    break
    except Exception:
        pass

    if gov_found and ce_found:
        return "both"
    elif gov_found:
        return "gov_only"
    elif ce_found:
        return "ce_only"
    else:
        return "neither"


def scan_for_pattern(
    pattern: str, transcript_path: str, window_size: int = 500
) -> bool:
    """Scan transcript tool_use entries for a pattern string.

    Matches against the ``name`` and serialised ``input`` of assistant
    ``tool_use`` blocks ONLY — not against arbitrary transcript text.
    This prevents the hook's own deny message (which re-enters the
    transcript as a user/tool_result) from self-satisfying the check
    on retry (#231).

    Args:
        pattern: String to search for in tool_use name/input
        transcript_path: Path to JSONL transcript file
        window_size: Only scan last N lines (default 500)

    Returns:
        True if pattern found in a tool_use entry, False otherwise
    """
    try:
        with open(transcript_path, "r") as f:
            lines = deque(f, maxlen=window_size) if window_size > 0 else f
            for line in lines:
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                msg = entry.get("message", {})
                if msg.get("role") != "assistant":
                    continue
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if block.get("type") != "tool_use":
                        continue
                    name = block.get("name", "")
                    input_str = json.dumps(block.get("input", {}))
                    if pattern in name or pattern in input_str:
                        return True
    except Exception:
        pass
    return False


# Tool names that dispatch a subagent. Same tuple, same reason, as
# `scan_contrarian_after_last_plan` below — see its comment for the recorded
# rationale (contrarian MEDIUM-2, session-123). Measured over this project's whole
# transcript history: every dispatch uses `Agent`; `Task` has never appeared. The tuple
# is kept anyway — cheap insurance so a harness rename cannot silently blind the check,
# which would over-block rather than under-block.
_SUBAGENT_TOOL_NAMES = ("Task", "Agent")


def scan_for_subagent(subagent_type: str, transcript_path: str) -> bool:
    """Was a subagent of ``subagent_type`` actually DISPATCHED in this transcript?

    WHY THIS EXISTS, and what it fixes. `scan_for_pattern` matches a string against
    the serialised input of ANY tool call, so *mentioning* a reviewer satisfied the
    pre-push review gate. Measured in one real session: 7 genuine dispatches against
    **29 non-dispatch tool calls** that each independently satisfied Check 2 — 10
    `Edit`, 10 `Bash`, 3 `Write`, and 6 `evaluate_governance` calls whose only sin was
    describing the intended work to the governance tool. That is a gate satisfied by
    talking about a review. BACKLOG #334.

    NO RECENCY WINDOW, DELIBERATELY, and this is load-bearing rather than a shortcut.
    `scan_for_pattern` defaults to the last 500 lines to expire stale *mentions*.
    Mentions are cheap and cluster right before a push, so they survive a trailing
    window; a real dispatch happens once, early, and scrolls out of it. So the window and
    the mention hole were load-bearing against each other, and narrowing the matcher
    without also removing the window would have flipped this gate to near-always-block —
    whose only escape is `QUALITY_GATE_SKIP`, which exits above the diff secret scanner,
    i.e. the "stricter" version would have traded a fake review check for a real
    credential leak. Stated as the RELATIONSHIP, which is stable, rather than counts, which are not: the transcript
    corpus is live host state and grows every session, so any number pasted here drifts —
    it already disagreed across four surfaces on first write. Narrowing the matcher while
    KEEPING the window passes only about a THIRD of eligible pushes. Narrowing it and
    removing the window together lands at parity with the old behaviour (a couple of
    events either way). That ~3x gap is the finding, and it is far too large to be
    reversed by measurement noise. Run `scripts/measure_review_gate.py` for current
    figures, including newly-blocked churn, which is the number that matters for bypass
    risk — a newly-passed push does not cancel a newly-blocked one.

    WHAT THIS DOES **NOT** PROVE, stated because the check it replaces claimed more
    than it measured:
      * NOT that the dispatch examined the diff being pushed — a dispatch from anywhere
        in the session counts, including many hours earlier. Sessions in this corpus
        routinely cross a calendar day; a security audit measured the median
        last-dispatch-to-push gap in hours, not minutes, and found cases where the
        review provably predated the code. Range-scoping needs a recorded receipt
        (#334) and cannot come from a transcript.
      * NOT that the review SUCCEEDED. A dispatch that errored, was interrupted, or was
        denied by the user still counts — the `tool_result` is not consulted. Measured
        as rare, but it is a known hole and tracked, not an oversight.
      * NOT that the review found anything, nor that its findings were read or acted
        on. That is judgment and stays with the human.
      * NOT that an untyped dispatch reviewed anything — a substantial minority of
        dispatches in this corpus carry no `subagent_type` and are invisible here. The
        deny message says so and names the remedy.
    Range-scoping needs a recorded receipt (the commit a reviewer examined), which a
    transcript cannot supply; that remains open on #334.

    Matches `tool_use` blocks only, never arbitrary transcript text, so the hook's own
    deny message cannot self-satisfy the check on retry (#231).

    Args:
        subagent_type: exact `subagent_type` to match, e.g. "code-reviewer"
        transcript_path: path to the JSONL transcript

    Returns:
        True if such a dispatch appears anywhere in the transcript, else False.
        Any read/parse failure returns False — the gate then blocks, which is the
        safe direction.
    """
    try:
        with open(transcript_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                # Guard entry/msg shapes, not just blocks. A line that is valid JSON but
                # not an object (`123`, `[...]`), or carries "message": null, otherwise
                # raises AttributeError into the OUTER handler — which abandons the whole
                # scan and returns False for the entire transcript. Removing the recency
                # window made that strictly worse: the scan now starts at line 1, so one
                # odd line early in a long session would hide every later dispatch, and
                # the only escape is QUALITY_GATE_SKIP, which disables the secret scanner.
                # `scan_transcript` and `scan_contrarian_after_last_plan` already guard
                # this; that this is the third site needing the same guard is the argument
                # for a shared block-extraction helper.
                if not isinstance(entry, dict):
                    continue
                msg = entry.get("message")
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "assistant":
                    continue
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue
                    if block.get("name") not in _SUBAGENT_TOOL_NAMES:
                        continue
                    block_input = block.get("input")
                    if not isinstance(block_input, dict):
                        continue
                    if block_input.get("subagent_type") == subagent_type:
                        return True
    except Exception:
        pass
    return False


def scan_contrarian_after_last_plan(transcript_path: str) -> str:
    """Check if contrarian-reviewer was invoked since the most recent prior ExitPlanMode.

    Fires in support of the pre-exit-plan-mode-gate hook. The hook runs BEFORE
    the current ExitPlanMode call, so the transcript contains PAST ExitPlanMode
    entries but not the one about to fire.

    Args:
        transcript_path: Path to JSONL transcript file.

    Returns:
        "allow"     — contrarian-reviewer tool_use found AFTER most recent prior
                      ExitPlanMode (or anywhere in bootstrap case).
        "deny"      — prior ExitPlanMode exists but no contrarian invocation since.
        "bootstrap" — no prior ExitPlanMode in transcript (first plan of session).
        "error"     — read/parse failure (hook should treat as deny per fail-closed).
    """
    contrarian_names = ("contrarian-reviewer", "contrarian_reviewer")

    try:
        with open(transcript_path, "r") as f:
            lines = f.readlines()
    except Exception:
        return "error"

    # Pass 1: find index of most recent ExitPlanMode tool_use
    last_exit_plan_idx = -1
    for idx, line in enumerate(lines):
        if "ExitPlanMode" not in line:
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            continue
        for block in msg.get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "ExitPlanMode":
                last_exit_plan_idx = idx

    # Bootstrap case: no prior ExitPlanMode means this is the session's first plan.
    if last_exit_plan_idx == -1:
        return "bootstrap"

    # Pass 2: search for contrarian Task/Agent tool_use AFTER the anchor.
    # Scans from (anchor + 1) to EOF — never matches the anchor itself or earlier.
    for line in lines[last_exit_plan_idx + 1 :]:
        if "contrarian" not in line:  # fast pre-filter
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            continue
        for block in msg.get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            # Task/Agent subagent_type form (Claude Code's Task + Agent tools
            # share this shape: name=Task|Agent, input.subagent_type=<agent>).
            # If a future Claude Code release adds a third subagent-invocation
            # tool name, extend this tuple — or reconsider keying on
            # input.subagent_type presence instead of enumerating names.
            # (Per contrarian MEDIUM-2, session-123.)
            if block.get("name") in ("Task", "Agent"):
                inp = block.get("input", {})
                if isinstance(inp, dict):
                    st = inp.get("subagent_type", "")
                    if st in contrarian_names:
                        return "allow"
            # Direct-name form (MCP subagent or future variants)
            elif block.get("name", "") in contrarian_names:
                return "allow"

    return "deny"


def scan_plan_action_atomicity(plan_text: str) -> tuple[str, list[str]]:
    """Scan a plan-mode artifact for action-atomicity violations.

    Per plan-template.md Recommended Approach section (Commit 2 of Superpowers
    plan, session-126): each task entry MUST name a single action category from
    {write failing test, run test, implement minimal code, refactor, verify}
    AND include **Files:** + **Verification:** lines. Combined tasks must split.
    Vague verbs (update/improve/handle) are not action categories.

    Returns:
        (status, findings) where:
          status: "pass" | "warn" | "skip" | "error"
          findings: list of human-readable violation strings (empty for pass/skip)

    Skip conditions (rule out-of-scope rather than failing the writer):
      - No `## Recommended Approach` heading found
      - Recommended Approach section has no task entries (## Task or ### Task headings)
    """
    if not plan_text:
        return ("error", ["empty plan text"])

    # Find Recommended Approach section. Accept # or ## or ### markdown level.
    # Stop at the next heading at the same level OR end of text.
    ra_match = re.search(
        r"^(#{1,3})\s+Recommended\s+Approach\b.*?$", plan_text, re.MULTILINE
    )
    if not ra_match:
        return ("skip", [])

    section_start = ra_match.end()
    heading_level = len(ra_match.group(1))
    # Find next heading at the same or higher level (i.e., fewer #s or equal).
    next_heading = re.search(
        r"^#{1," + str(heading_level) + r"}\s+",
        plan_text[section_start:],
        re.MULTILINE,
    )
    section_end = (
        section_start + next_heading.start() if next_heading else len(plan_text)
    )
    section = plan_text[section_start:section_end]

    # Find task entries — accept ### Task, ### Commit, ### Step, ### Phase, or
    # the same with **bold** prefix. Be lenient: the rule applies when the
    # writer chose to use task-style entries; free-form prose plans skip.
    task_pattern = re.compile(
        r"^#{2,4}\s+(Task|Commit|Step|Phase)\s*[\d.A-Z]*\s*[—:\-–]?\s*(.+)$",
        re.MULTILINE,
    )
    matches = list(task_pattern.finditer(section))
    if not matches:
        return ("skip", [])

    findings: list[str] = []

    for i, m in enumerate(matches):
        kind = m.group(1)
        title = m.group(2).strip().lower()
        # Determine the body of THIS task (between this heading and next, or end of section).
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
        body = section[body_start:body_end]
        title_and_body = (title + "\n" + body).lower()

        # Check 1: at least one action category mentioned in title or body
        categories_present = [
            cat for cat in _ACTION_CATEGORIES if cat in title_and_body
        ]
        if not categories_present:
            # Vague-verb fallback signal — useful in WARN message
            vague_hit = next((v for v in _VAGUE_VERBS if v in title), None)
            if vague_hit:
                findings.append(
                    f"{kind} '{m.group(2).strip()[:60]}': vague verb '{vague_hit}' — "
                    f"replace with a category from {_ACTION_CATEGORIES}"
                )
            else:
                findings.append(
                    f"{kind} '{m.group(2).strip()[:60]}': no action category from "
                    f"{_ACTION_CATEGORIES} found in title or body"
                )

        # Check 2: combined-action signal — multiple distinct categories in title
        # ("implement and test", "refactor and verify"). Body-level multi-category
        # is OK (a Refactor task may also Verify); we only flag the title.
        title_categories = [cat for cat in _ACTION_CATEGORIES if cat in title]
        if len(title_categories) >= 2:
            findings.append(
                f"{kind} '{m.group(2).strip()[:60]}': combines "
                f"{title_categories} — split into separate tasks"
            )

        # Check 3: Files: and Verification: lines present (case-insensitive)
        if not re.search(r"\*\*Files:\*\*", body, re.IGNORECASE):
            findings.append(
                f"{kind} '{m.group(2).strip()[:60]}': missing **Files:** line"
            )
        if not re.search(r"\*\*Verification:\*\*", body, re.IGNORECASE):
            findings.append(
                f"{kind} '{m.group(2).strip()[:60]}': missing **Verification:** line"
            )

    if findings:
        return ("warn", findings)
    return ("pass", [])


def scan_tdd_test_existence(file_list_text: str) -> tuple[str, list[str]]:
    """Scan a list of changed files for new src .py files lacking paired tests.

    Per Superpowers v5.0.7 test-driven-development skill + TDAD (arxiv 2603.17973):
    new src code paths should ship with paired tests in the same change. WARN
    mode (this scanner returns warnings; hook decides whether to BLOCK based on
    promotion trigger — currently advisory).

    Pair convention (project-specific): src/<package>/<name>.py paired with
    tests/test_<name>.py. Hook-script src counterpart: .claude/hooks/<name>.sh
    paired with tests/test_<name>_hook.py.

    Returns:
        (status, findings) where:
          status: "pass" | "warn" | "skip" | "error"
          findings: list of human-readable "missing pair: src/X.py → tests/test_X.py" strings
    """
    if not file_list_text:
        return ("skip", [])

    files = [
        ln.strip()
        for ln in file_list_text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]

    # Filter to new src/*.py files only — hook is expected to pre-filter to
    # added (status A) files via `git diff --diff-filter=A`. We additionally
    # restrict to .py under src/ since hook-test pairing is checked separately.
    new_src_pys = [
        f
        for f in files
        if f.startswith("src/") and f.endswith(".py") and "/__init__" not in f
    ]

    if not new_src_pys:
        return ("skip", [])

    # Project root = current working directory when called from hook context
    # (hook sets cwd to repo root via $CLAUDE_PROJECT_DIR convention).
    cwd = os.getcwd()
    findings: list[str] = []

    for src_path in new_src_pys:
        basename = os.path.basename(src_path)[:-3]  # strip .py
        expected_test = f"tests/test_{basename}.py"
        full_test_path = os.path.join(cwd, expected_test)
        if not os.path.exists(full_test_path):
            findings.append(f"missing test pair: {src_path} → {expected_test}")

    if findings:
        return ("warn", findings)
    return ("pass", [])


if __name__ == "__main__":
    # Contrarian-after-last-plan mode: --contrarian-after-last-plan <transcript>
    if len(sys.argv) >= 3 and sys.argv[1] == "--contrarian-after-last-plan":
        transcript = sys.argv[2]
        print(scan_contrarian_after_last_plan(transcript))
        sys.exit(0)

    # Plan-action-atomicity mode: --plan-action-atomicity <plan-text-path|->
    if len(sys.argv) >= 3 and sys.argv[1] == "--plan-action-atomicity":
        src = sys.argv[2]
        try:
            if src == "-":
                plan_text = sys.stdin.read()
            else:
                with open(src) as f:
                    plan_text = f.read()
        except Exception as e:
            print("error")
            print(f"plan-action-atomicity: read failure: {e}", file=sys.stderr)
            sys.exit(0)
        status, findings = scan_plan_action_atomicity(plan_text)
        print(status)
        for f in findings:
            print(f"plan-action-atomicity: {f}", file=sys.stderr)
        sys.exit(0)

    # TDD-test-existence mode: --tdd-test-existence <files-list-path|->
    if len(sys.argv) >= 3 and sys.argv[1] == "--tdd-test-existence":
        src = sys.argv[2]
        try:
            if src == "-":
                file_list_text = sys.stdin.read()
            else:
                with open(src) as f:
                    file_list_text = f.read()
        except Exception as e:
            print("error")
            print(f"tdd-test-existence: read failure: {e}", file=sys.stderr)
            sys.exit(0)
        status, findings = scan_tdd_test_existence(file_list_text)
        print(status)
        for f in findings:
            print(f"tdd-test-existence: {f}", file=sys.stderr)
        sys.exit(0)

    # Pattern mode: --pattern <pattern> <transcript> [window]
    if len(sys.argv) >= 4 and sys.argv[1] == "--pattern":
        pattern = sys.argv[2]
        transcript = sys.argv[3]
        try:
            window = int(sys.argv[4]) if len(sys.argv) > 4 else 500
        except (ValueError, TypeError):
            window = 500
        print("true" if scan_for_pattern(pattern, transcript, window) else "false")
        sys.exit(0)

    # Subagent-dispatch mode: --subagent <subagent_type> <transcript>
    #
    # Output contract: exactly "true" or "false". Anything else means the caller's argv
    # was malformed. The guard below stops it falling through to governance mode, which
    # prints "neither" — a value the review gate reads as false and blocks on. Both
    # outcomes block, so the guard buys diagnosability, not safety.
    #
    # AND BE HONEST ABOUT WHERE THAT LANDS: both production call sites redirect
    # `2>/dev/null` (pre-push-quality-gate.sh Checks 2 and 3), so this stderr line is
    # visible to a human invoking the scanner directly and NOT to anyone debugging a
    # mystery deny. Claiming it makes the failure "loud" in production would be the same
    # over-claim this mode exists to remove.
    if len(sys.argv) >= 2 and sys.argv[1] == "--subagent":
        if len(sys.argv) != 4:
            print(
                "error: --subagent takes exactly 2 args "
                "(<subagent_type> <transcript>), got "
                f"{len(sys.argv) - 2}",
                file=sys.stderr,
            )
            print("false")
            sys.exit(0)
        print("true" if scan_for_subagent(sys.argv[2], sys.argv[3]) else "false")
        sys.exit(0)

    # Governance mode: <gov_tool> <ce_tool> <transcript> [window]
    if len(sys.argv) < 4:
        print("neither")
        sys.exit(0)

    gov_tool = sys.argv[1]
    ce_tool = sys.argv[2]
    transcript = sys.argv[3]
    try:
        window = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    except (ValueError, TypeError):
        window = 0

    print(scan_transcript(gov_tool, ce_tool, transcript, window))
