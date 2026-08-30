#!/usr/bin/env python3
"""Compute the repo's standing close-out inventory (BACKLOG #200).

WHY THIS EXISTS
---------------
Across sessions 217-249 this repo silently accumulated 2 stale remote branches, an
orphan worktree, 2 unpushed tags, an open PR sitting 2 weeks, and 5 unpushed commits --
while SESSION-STATE.md read "ACTION ON RESUME: nothing pending". That line was a
HAND-WRITTEN CLAIM ABOUT DERIVABLE STATE, and it rotted the instant it was written.

The fix is not a better checklist. It is to stop writing the claim and compute it
instead -- the same discipline as #193 ("completeness derived from the filesystem,
never a hand-list") and #190 ("a file cannot be its own drift baseline").

TWO INVARIANTS, BOTH LOAD-BEARING
---------------------------------
1. THIS TOOL NEVER MUTATES ANYTHING. It prints commands; a human runs them. It has no
   code path that deletes a ref, pushes, or merges. Session-250 deliberately removed a
   standing `git push` grant to restore per-push authorization; a tool that auto-deletes
   remote refs would walk straight back through that door.

2. ANCESTRY LIES -- so we report EVIDENCE, never a verdict. `git branch --no-merged`
   called all 3 of session-250's branches "unmerged" when every file they touched was
   byte-identical on main (the work had been squash/rebase-landed). A tool that trusted
   ancestry would be either useless (refuses to clean anything) or DESTRUCTIVE (deletes
   real work when forced). So `stale_branch` never proposes `delete` -- it hands the
   human the per-file same/differs split, the churn-vs-substantive breakdown, and a
   recovery SHA, and lets them adjudicate. Ground truth for this is pinned by two real
   tags: `fixture/semantic-rank-landed` (all files same -> was safe) and
   `fixture/probe-diverged` (substantive differs -> was NOT mechanically safe; deleting
   it rested on a semantic-refactor judgment no tool should make).

ARCHITECTURE
------------
`collect_local_facts()` and `collect_remote_facts()` are the ONLY impure functions.
`classify()` is pure: it takes facts and returns findings, so every decision is
testable offline with zero mocking and zero network.

EXIT CODES (mirrors scripts/gen_quick_reference.py -- callers key on the split)
  0  clean -- no findings at or above --min-severity
  1  findings present  <- a RESULT, not an error
  2  tool/usage error
  3  not a git repo / unsupported layout
Never conflate 2/3 with 0. "The tool broke" must never read as "the repo is clean" --
that is the T-169 bug class (a real red CI job dismissed for days as expected noise).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess  # nosec B404 - fixed argv git/gh calls, no shell=True (see _git note)
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# --- Thresholds. Pinned here so they are falsifiable, not a matter of taste. -----------
# Observed session cadence in this repo is ~1.2/day; the residue incident ran 28 days.
STALE_BRANCH_DAYS = 14  # a non-default branch with no open PR, untouched this long
OPEN_PR_WARN_DAYS = 7
OPEN_PR_HIGH_DAYS = 14  # PR #14 sat exactly this long before anyone looked
STALE_TAG_DAYS = 1  # an unpushed tag is nearly always an oversight
FRESH_COMMIT_DAYS = 1  # per-push authorization makes "unpushed" the NORMAL steady state
KEEP_EXPIRY_DAYS = 30  # a keep older than this re-enters the alarm: "still?"

# `medium` sits between warn and high. It was MISSING while classify() already
# emitted it for unknown-ownership worktrees, so `SEVERITY_ORDER[f.severity]`
# raised KeyError and main() caught it as `internal error: 'medium'` — the tool
# printed ZERO findings for the WHOLE repo, not just that worktree. Reproduced
# on `git init` + one plain `git worktree add`. It mattered beyond the crash:
# the argument for cleanup.sh being permissive on no-evidence is "the advisory
# tool still surfaces it", and the advisory tool was dead in exactly that state.
SEVERITY_ORDER = {"info": 0, "warn": 1, "medium": 2, "high": 3}

# `keep:` markers live in BACKLOG next to the reason. Pin the schema HARD -- a prior
# revision of this design tried to scan memory-file prose for stale refs and measured
# ~260 false positives against 3 real ones (192 of them `gov-*` audit IDs, which the
# behavioral floor MANDATES writing). Exact-line match only. This is a tiny schema, not
# an NLP problem.
KEEP_LINE_RE = re.compile(r"^\s*keep:\s+(\S+)\s*$", re.MULTILINE)

# Cross-consumer contract. The shell consumers expose the same ordered marker;
# tests compare these declarations so a producer cannot evolve one reader at a time.
JOURNAL_V2_KEYS = (
    "version",
    "host",
    "lifecycle_owner",
    "path",
    "branch",
    "base_sha",
    "default_ref",
    "owner_pid",
    "session_id",
    "task_key",
    "parallel_task",
    "state",
    "updated_at",
)
TASK_KEY_RE = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,127}")
LEGACY_TASK_BRANCH_RE = re.compile(r"^wt/(.+)-[0-9a-f]{8}$")
JOURNAL_V2_STATES = {
    "attached",
    "created",
    "published",
    "locked",
    "ready",
    "setup-failed",
    "task-conflict",
}


@dataclass
class Finding:
    check: str
    ref: str
    severity: str
    title: str
    disposition: str  # investigate | push | merge | fix | decide | keep
    evidence: dict = field(default_factory=dict)
    command: str | None = None  # printed for the human; NEVER executed
    kept: bool = False
    kept_reason: str | None = None

    def __setattr__(self, name: str, value) -> None:
        """Every severity, however it arrives, must be one summarize() can rank.

        Centralised here because the alternatives all leak. `medium` reached
        production as a literal in a constructor call while `SEVERITY_ORDER` had
        no entry for it, so `summarize()` raised KeyError and the tool printed
        ZERO findings for the whole repo. The obvious guard — a test grepping
        for `severity="..."` literals — misses the two forms that also occur
        here: `severity=sev` from a variable, and `f.severity = "warn"`
        reassignment after construction. A `__setattr__` check sees all three,
        at construction AND at mutation, and cannot be outrun by a new call site.
        """
        if name == "severity" and value not in SEVERITY_ORDER:
            raise ValueError(
                f"severity {value!r} is not in SEVERITY_ORDER "
                f"({', '.join(SEVERITY_ORDER)}); summarize() could not rank it"
            )
        object.__setattr__(self, name, value)

    @property
    def id(self) -> str:
        return f"{self.check}:{self.ref}"

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "check": self.check,
            "ref": self.ref,
            "severity": self.severity,
            "title": self.title,
            "disposition": self.disposition,
            "evidence": self.evidence,
            "kept": self.kept,
        }
        if self.command:
            d["command"] = self.command
            d["requires_human"] = True
        if self.kept_reason:
            d["kept_reason"] = self.kept_reason
        return d


# ======================================================================================
# IMPURE LAYER -- the only code that touches git, the filesystem, or the network.
# ======================================================================================


def _git(repo: Path, *args: str, timeout: int = 15) -> tuple[int, str]:
    """Run a git command. Returns (returncode, stdout). Never raises on git failure.

    NO SHELL is involved, so shell metacharacters in git-derived values are inert. But
    "no user-controlled input" would be FALSE: refnames reach argv slots, and git parses
    leading-dash arguments as OPTIONS. A branch named `--output=<path>` turns a read-only
    `git log` into a file write. Callers passing a ref MUST pass the full `refs/heads/...`
    form (which cannot begin with `-`) plus a trailing `--`, never a short name.
    """
    try:
        r = subprocess.run(  # nosec B603 B607 - fixed argv, no shell; see argv note above
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            errors="replace",  # makes "never raises" true: strict decode would ValueError
            timeout=timeout,
            check=False,
        )
        return r.returncode, r.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return 1, ""


def is_git_repo(repo: Path) -> bool:
    rc, out = _git(repo, "rev-parse", "--is-inside-work-tree")
    return rc == 0 and out == "true"


def default_branch(repo: Path) -> str:
    rc, out = _git(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if rc == 0 and out:
        return out.rsplit("/", 1)[-1]
    return "main"


def resolve_base_ref(
    repo: Path, base: str, primary_ref: str | None = None
) -> str | None:
    """Resolve the default-branch NAME to a ref that EXISTS, or None. Never a bare name.

    Two defects meet here, and both were live.

    OPTION INJECTION. `default_branch()` returns a SHORT name taken from the
    `origin/HEAD` symref target, and a short name in an argv slot is the exact hazard
    the local_only_commits scan already armors against: a ref named `--output=<path>`
    turns a read-only `git rev-list` into a file WRITE, falsifying Invariant 1 in the
    module docstring. Reproduced end-to-end 2026-08-23 — `git symbolic-ref
    refs/remotes/origin/HEAD refs/remotes/origin/--output=PWNED` made
    `collect_local_facts` create `<repo>/PWNED`, and the swallowed `--not` also
    corrupted the count rather than failing safe. The trailing `--` does NOT help: it
    closes PATHSPEC parsing, not option parsing of an earlier argument. Every candidate
    below is prefixed with `refs/`, so none can begin with `-`.

    SILENT MUTING. `default_branch()` falls back to the literal string `"main"` when
    `origin/HEAD` is unset — true of any remote-less repo and of `master` repos. Feeding
    a name that resolves to nothing makes the landedness scan return -1 for EVERY
    worktree, so the gate stops discriminating and never says so: -1 reads like an
    ordinary safe outcome. The ladder below tries the remote-tracking form and then the
    primary checkout's own branch, which IS the integration point in a worktree layout.

    Returning None is the SAFE answer and stays the default. A wrongly-resolved base is
    the destructive direction — it could read unlanded work as landed and license a
    removal command — so this never falls back to a branch merely because it exists.
    """
    cands: list[str] = []
    if base:
        cands += [f"refs/heads/{base}", f"refs/remotes/origin/{base}"]
    if primary_ref and primary_ref.startswith("refs/") and primary_ref not in cands:
        cands.append(primary_ref)
    for c in cands:
        rc, _ = _git(repo, "rev-parse", "--verify", "--quiet", c)
        if rc == 0:
            return c
    return None


def _real(p) -> str:
    """Resolved absolute path as a string, for comparing two checkout paths.

    `/tmp` is a symlink to `/private/tmp` on macOS, and git reports worktree paths
    unresolved, so a plain string compare says two names for the same directory are
    different trees. That miscompare is exactly what would make a session fail to
    recognize its OWN worktree.
    """
    try:
        return str(Path(p).resolve())
    except OSError:
        return str(p)


LOCK_PID_RE = re.compile(r"\bpid[\s=]+(\d+)")


def _parse_lock_pid(reason: str) -> int | None:
    """The ONE place this process parses a pid out of a lock reason.

    `pid[\\s=]+`, not `pid\\s+`. Two producers write two shapes: Claude Code
    writes `pid 12345`, and prepare.sh's framework reason writes `pid=12345`.
    The whitespace-only form matched neither of the evidence sources this
    ownership decision depends on for framework worktrees — it returned None for
    every one of them, so "the Git lock reason" was a dead source while the
    docstring listed it as one of three.

    It is a named accessor rather than an inline regex so a test can exercise
    THIS code instead of restating the pattern. The first version of that test
    re-inlined the expression and would have stayed green through a full
    regression — the failure `ref-ai-coding-derive-guards-from-source-of-truth`
    describes, reintroduced by the guard written to prevent it.
    """
    matches = LOCK_PID_RE.findall(reason)
    if len(matches) != 1:
        # Zero is "no pid recorded". MORE than one is AMBIGUOUS, and the two
        # parsers disagreed about it: this one took the FIRST token while
        # cleanup.sh's greedy sed took the LAST, so one reason yielded two
        # different owners. Neither answer is defensible, so return neither.
        return None
    return int(matches[0])


def _parse_worktree_journal_text(text: str) -> dict:
    """Parse a lifecycle journal without guessing across schema versions.

    V2 is an exact, ordered record. A file that claims v2 -- including one with
    the v2-only task fields but a missing/reordered version line -- is either
    fully valid or explicitly malformed. Older journals remain readable through
    the conservative owner-pid compatibility path and never acquire a task key
    from free-form content.
    """
    lines = text.splitlines()
    is_v2_candidate = any(
        line == "version=2"
        or line.startswith("task_key=")
        or line.startswith("parallel_task=")
        for line in lines
    )
    if not is_v2_candidate:
        owner_fields = re.findall(r"^owner_pid=(.*)$", text, re.MULTILINE)
        if len(owner_fields) != 1:
            return {
                "format": "legacy",
                "valid": False,
                "error": "owner_pid must appear exactly once",
            }
        owner_value = owner_fields[0]
        lifecycle_fields = re.findall(r"^lifecycle_owner=(.*)$", text, re.MULTILINE)
        lifecycle_owner = lifecycle_fields[0] if len(lifecycle_fields) == 1 else None
        if lifecycle_owner == "codex-desktop" and owner_value == "":
            return {
                "format": "legacy",
                "valid": True,
                "owner_pid": None,
                "lifecycle_owner": lifecycle_owner,
            }
        if not owner_value.isdigit() or int(owner_value) <= 1:
            return {
                "format": "legacy",
                "valid": False,
                "error": "owner_pid is malformed",
            }
        owner_pid = int(owner_value)
        return {
            "format": "legacy",
            "valid": True,
            "owner_pid": owner_pid,
            "lifecycle_owner": lifecycle_owner,
        }

    if any((ord(ch) < 32 and ch != "\n") or ord(ch) == 127 for ch in text):
        return {
            "format": "v2",
            "valid": False,
            "error": "contains control characters",
        }

    pairs: list[tuple[str, str]] = []
    for line in lines:
        if "=" not in line:
            return {
                "format": "v2",
                "valid": False,
                "error": "contains a line without key=value",
            }
        key, value = line.split("=", 1)
        pairs.append((key, value))
    keys = tuple(key for key, _ in pairs)
    if keys != JOURNAL_V2_KEYS:
        return {
            "format": "v2",
            "valid": False,
            "error": "fields are missing, duplicated, unknown, or out of order",
        }

    data = dict(pairs)
    if data["version"] != "2":
        return {"format": "v2", "valid": False, "error": "version is not 2"}
    if data["host"] not in {"claude", "codex-cli", "codex-desktop"}:
        return {"format": "v2", "valid": False, "error": "host is malformed"}
    if data["lifecycle_owner"] not in {"framework", "codex-desktop"}:
        return {
            "format": "v2",
            "valid": False,
            "error": "lifecycle_owner is malformed",
        }
    if not data["path"].startswith("/"):
        return {"format": "v2", "valid": False, "error": "path is not absolute"}
    if not data["branch"] or not data["default_ref"]:
        return {
            "format": "v2",
            "valid": False,
            "error": "branch or default_ref is empty",
        }
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", data["base_sha"]):
        return {"format": "v2", "valid": False, "error": "base_sha is malformed"}
    owner_pid = data["owner_pid"]
    if owner_pid and (not owner_pid.isdigit() or int(owner_pid) <= 1):
        return {"format": "v2", "valid": False, "error": "owner_pid is malformed"}
    if not TASK_KEY_RE.fullmatch(data["task_key"]):
        return {"format": "v2", "valid": False, "error": "task_key is malformed"}
    if data["parallel_task"] not in {"0", "1"}:
        return {
            "format": "v2",
            "valid": False,
            "error": "parallel_task is not 0 or 1",
        }
    if data["state"] not in JOURNAL_V2_STATES:
        return {"format": "v2", "valid": False, "error": "state is malformed"}
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", data["updated_at"]):
        return {"format": "v2", "valid": False, "error": "updated_at is malformed"}

    return {
        "format": "v2",
        "valid": True,
        "host": data["host"],
        "lifecycle_owner": data["lifecycle_owner"],
        "path": data["path"],
        "branch": data["branch"],
        "base_sha": data["base_sha"],
        "default_ref": data["default_ref"],
        "owner_pid": int(owner_pid) if owner_pid else None,
        "task_key": data["task_key"],
        "parallel_task": data["parallel_task"] == "1",
        "state": data["state"],
    }


def _read_worktree_journal(w: dict) -> dict:
    """Read one registered worktree's journal; never treat unreadable as absent."""
    rc, gd = _git(Path(w["path"]), "rev-parse", "--git-dir")
    if rc != 0 or not gd:
        return {"format": "unreadable", "valid": False, "error": "gitdir unavailable"}
    gdp = Path(gd)
    if not gdp.is_absolute():
        gdp = Path(w["path"]) / gdp
    journal_path = gdp / "ai-worktree-state"
    try:
        raw = journal_path.read_bytes()
    except FileNotFoundError:
        return {"format": "absent", "valid": True}
    except OSError as exc:
        return {"format": "unreadable", "valid": False, "error": str(exc)}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        if any(
            marker in raw for marker in (b"version=2", b"task_key=", b"parallel_task=")
        ):
            return {"format": "v2", "valid": False, "error": "is not valid UTF-8"}
        return {"format": "unreadable", "valid": False, "error": "is not valid UTF-8"}
    return _parse_worktree_journal_text(text)


def _legacy_task_key(branch: str | None) -> str | None:
    """Derive only the generator's unambiguous `wt/<slug>-<8 hex>` shape."""
    if not branch:
        return None
    match = LEGACY_TASK_BRANCH_RE.fullmatch(branch)
    return f"slug:{match.group(1)}" if match else None


def _v2_lock_matches(w: dict, journal: dict, branch: str) -> bool:
    """V2 journals count only when Git corroborates their lifecycle identity."""
    if journal["path"] != w["path"]:
        return False
    if journal.get("lifecycle_owner") == "codex-desktop":
        if branch:
            return journal["branch"] == branch
        return journal["state"] == "attached" and w.get("head") == journal["base_sha"]
    reason = w.get("lock_reason", "")
    expected_pid = str(journal["owner_pid"] or "")
    expected_lock = (
        f"ai-worktree-v2 host={journal['host']} lifecycle=framework "
        f"branch={branch} default={journal['default_ref']} base={journal['base_sha']} "
        f"pid={expected_pid} task={journal['task_key']} "
        f"parallel={'1' if journal['parallel_task'] else '0'} start="
    )
    return (
        journal["branch"] == branch
        and re.fullmatch(
            re.escape(expected_lock) + r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
            reason,
        )
        is not None
    )


def _ownership_pids(w: dict) -> list[int] | None:
    """Every pid recorded as owning this worktree, strongest evidence first.

    Two sources, because neither alone is authoritative: the lifecycle journal's
    `owner_pid`, which `prepare.sh` writes, and the Git lock reason, which
    corroborates it. A lock can be released by hand or lost to a crash; the
    journal survives it. Reading only the lock is what let an UNLOCKED but live
    worktree be reported as an orphan with a `git worktree remove` attached.

    Returns None — not an empty list — when a source could not be READ, so the
    caller reports `unknown` rather than `dead`.
    """
    pids: list[int] = []
    journal = w.get("journal") or _read_worktree_journal(w)
    if journal["format"] == "unreadable" or not journal.get("valid", False):
        # An unreadable or malformed journal cannot be replaced by lock evidence:
        # doing so lets one source silently answer for both.
        return None
    journal_pid = journal.get("owner_pid")
    if journal_pid is not None:
        pids.append(int(journal_pid))
    if w.get("lock_pid") is not None:
        pids.append(int(w["lock_pid"]))
    return pids


def _ownership_state(pids: list[int] | None, locked: bool = False) -> str:
    """`live`, `dead`, or `unknown` — and the third is not a synonym for `dead`.

    Only a pid that answers ESRCH proves death. No pid at all proves nothing,
    and must never license a destructive command: that is the whole point of
    keeping this tri-state instead of a boolean.

    A worktree LOCKED with no parseable owner is treated as live, not unknown.
    The lock is a deliberate act by someone protecting that tree, and the
    long-standing rule here is to degrade toward the quiet false positive rather
    than tell a maintainer their in-use checkout is residue.
    """
    if pids is None:
        # The evidence sources could not be READ. Never `dead`, and not even
        # `live if locked` — we know nothing, and unknown attaches no command.
        return "unknown"
    if not pids:
        return "live" if locked else "unknown"
    if any(_pid_alive(p) for p in pids):
        return "live"
    if len(set(pids)) > 1:
        # Sources disagree about who owns this. cleanup.sh already refuses here;
        # without this the ADVISORY tool handed over `git worktree remove` for a
        # tree the DESTRUCTIVE tool would not touch.
        return "unknown"
    return "dead"


def _pid_alive(pid: int | None) -> bool:
    """True when `pid` names a live process. Unknown/unparseable pid => True.

    DEGRADE TOWARD QUIET. A false "dead" tells someone their IN-USE worktree is
    residue and hands them `git worktree remove` for a tree another session is
    writing to. A false "alive" only softens the WORDING of a finding. The first
    error is destructive, so an unknown pid is treated as live.

    TWO CONSUMERS, and the cost is not the same for both -- say so, because a
    maintainer reading only the orphan-check story would "tighten" this toward the
    destructive side as an improvement:
      * `facts["worktrees"]` (orphan check): false-alive = a stale worktree is not
        nagged about. Untidy.
      * the `sibling_session_active` presence channel: false-alive = a branch is
        described as a live teammate's. It is NOT silenced -- ownership there is
        decided by `is_acting`, not by liveness -- so the cost is a misleading
        label, not a lost finding. That separation is deliberate.

    KNOWN GAP, accepted not solved: pid REUSE. This is existence only, so once the
    OS recycles a pid a dead owner reads as live. The lock reason also records
    `start <date>`, which would close it by comparing against the process start
    time; not implemented, and both failure paths above land on the quiet side.
    """
    if pid is None:
        return True
    try:
        os.kill(pid, 0)  # signal 0 = existence check only, delivers nothing
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by another user
    except (OverflowError, ValueError, OSError):
        return True
    return True


def _age_days(iso_date: str) -> int | None:
    """Days since an ISO date (git %cs = YYYY-MM-DD). None if unparseable."""
    try:
        d = datetime.strptime(iso_date.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - d).days
    except (ValueError, AttributeError):
        return None


def branch_evidence(repo: Path, branch: str, base: str) -> dict:
    """Per-file same/differs for the branch's unique commits. EVIDENCE, NOT A VERDICT.

    Ancestry is deliberately reported but NOT trusted: `ancestry_merged` is included so
    the human can see it disagree with `files`. That disagreement is the whole lesson.
    """
    rc, out = _git(repo, "rev-list", "--count", branch, "--not", base)
    unique = int(out) if rc == 0 and out.isdigit() else -1

    rc, _ = _git(repo, "merge-base", "--is-ancestor", branch, base)
    ancestry_merged = rc == 0

    if unique <= 0:
        return {
            "unique_commits": unique,
            "ancestry_merged": ancestry_merged,
            "files": [],
        }

    rc, out = _git(repo, "rev-list", branch, "--not", base)
    shas = out.split()[:200] if rc == 0 else []

    paths: list[str] = []
    for sha in shas:
        rc, out = _git(repo, "diff-tree", "-r", "--no-commit-id", "--name-only", sha)
        if rc == 0:
            paths.extend(p for p in out.splitlines() if p)
    paths = sorted(set(paths))[:500]

    files = []
    for p in paths:
        # NOTE: plain `git rev-parse <rev>:<path>` echoes the UNRESOLVED SPEC on stdout
        # while exiting 128 -- so the natural `$(git rev-parse ... || echo MISSING)` idiom
        # yields garbage that compares unequal to everything. `--verify --quiet` fixes
        # that: it is silent and exits non-zero with empty stdout on a miss, so the
        # rc-keyed `blob if rc == 0 else None` below is unambiguous.
        rc_b, blob_b = _git(repo, "rev-parse", "--verify", "--quiet", f"{branch}:{p}")
        rc_m, blob_m = _git(repo, "rev-parse", "--verify", "--quiet", f"{base}:{p}")
        b = blob_b if rc_b == 0 else None
        m = blob_m if rc_m == 0 else None
        if b == m:
            state = "same"
        elif m is None:
            state = "absent-on-base"
        else:
            state = "differs"
        files.append({"path": p, "state": state})

    return {
        "unique_commits": unique,
        "ancestry_merged": ancestry_merged,
        "files": files,
        "recovery_sha": shas[0][:7] if shas else None,
    }


def _is_churn(path: str) -> bool:
    """Append-only memory files diverge on ANY branch, forever. Not substantive."""
    name = path.rsplit("/", 1)[-1]
    return name in {
        "SESSION-STATE.md",
        "BACKLOG.md",
        "LEARNING-LOG.md",
        "PROJECT-MEMORY.md",
        "OPERATIONS.md",
    }


def read_keep_markers(repo: Path) -> dict[str, str]:
    """Parse `keep: <ref>` lines from BACKLOG. The marker lives next to the REASON.

    A keep-with-a-reason IS a backlog item (worktree-session-218 was kept because "the
    #48 probe live run is still owed" -- which is literally BACKLOG #48). A bespoke
    ledger would duplicate the framework's own tracker.
    """
    out: dict[str, str] = {}
    for candidate in (repo / "_ai-context" / "BACKLOG.md", repo / "BACKLOG.md"):
        if not candidate.exists():
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in KEEP_LINE_RE.finditer(text):
            out[m.group(1)] = "BACKLOG"
        break
    return out


def collect_local_facts(repo: Path) -> dict:
    base = default_branch(repo)
    facts: dict = {"default_branch": base, "keep_markers": read_keep_markers(repo)}

    rc, out = _git(repo, "status", "--porcelain")
    facts["dirty_files"] = [ln for ln in out.splitlines() if ln] if rc == 0 else []

    rc, out = _git(repo, "log", "--format=%H %cs", "@{u}..HEAD")
    facts["unpushed_commits"] = []
    if rc == 0 and out:
        for ln in out.splitlines():
            parts = ln.split(None, 1)
            if len(parts) == 2:
                facts["unpushed_commits"].append(
                    {"sha": parts[0][:7], "date": parts[1]}
                )

    rc, out = _git(repo, "branch", "--show-current")
    facts["current_branch"] = out.strip() if rc == 0 else ""

    # Commits that exist on NO remote, attributed per local branch.
    #
    # WHY THIS IS SEPARATE FROM `unpushed_commits` ABOVE: that fact measures
    # `@{u}..HEAD` -- the CURRENT checkout, against an upstream it must already have.
    # It is blind twice over: to a SIBLING worktree branch, and to a fresh branch with
    # no upstream at all (where `git log @{u}..HEAD` simply errors and yields nothing).
    #
    # Both blind spots have now destroyed real work. Session-241's `ddbb1aa` (Shepherd
    # INFLUENCES row + a reference capture + a backlog item) went dangling when its
    # worktree was removed. Session-255 repeated it at n=2: three commits carrying a
    # user-approved reference capture, BACKLOG #206, and an index fix were discarded
    # when `EnterWorktree` re-created an existing branch name from origin/main.
    #
    # The 2026-07-10 lesson's rule was ADVISORY -- "record the unpushed SHA in
    # SESSION-STATE as an explicit UN-LANDED item". Session-255 followed it, and still
    # lost the work, because the record was written into the SESSION-STATE living on the
    # at-risk branch. A note stored inside the thing it warns about dies with it. That is
    # what promotes this from advisory to computed (V-004 advisory->structural arc):
    # the state is derivable from git, so per #200's thesis it must be COMPUTED, never
    # recalled from a claim someone wrote down.
    facts["local_only_commits"] = {}
    facts["local_only_scan_errors"] = []
    # GUARD -- test corpus caught its absence on the first run. With NO remote there is
    # no durable elsewhere for a commit to be, so `--not --remotes` excludes nothing and
    # every commit reads as "exists nowhere else": the tool would chirp at a repo this
    # corpus defines as clean and tell the human to push to a remote that does not exist.
    # Test CONFIGURED remotes, not remote-tracking refs: a repo with `origin` set but
    # never fetched has zero `refs/remotes`, and that is precisely when 100% of the work
    # is local-only and a durable destination DOES exist -- disabling there would be a
    # false negative in the exact class this check was built for.
    rc, remotes_out = _git(repo, "remote")
    has_remote = rc == 0 and bool(remotes_out.strip())

    # Iterate FULL refnames, not short names. A bare short name in an argv slot is two
    # distinct bugs at once, and both were found in review:
    #   1. `git log` OPTION-PARSES a leading-dash name. A branch named `--output=<path>`
    #      makes this read-only tool write and TRUNCATE that file -- falsifying Invariant
    #      1 in the module docstring. (Reachable via `git fetch` with an explicit
    #      refspec; `git branch`/`checkout -b` refuse such names.)
    #   2. A name colliding with a path in the tree ("scripts", "tests") makes git abort
    #      `ambiguous argument ... both revision and filename` -- verified empirically.
    # `refs/heads/<name>` cannot begin with `-` and is unambiguous; the trailing `--`
    # closes pathspec parsing. Short name is kept for display and comparison only.
    rc, out = _git(
        repo, "for-each-ref", "--format=%(refname)%09%(refname:short)", "refs/heads"
    )
    for ln in out.splitlines() if (rc == 0 and has_remote) else []:
        full, _, short = ln.partition("\t")
        full, short = full.strip(), short.strip()
        if not full or not short:
            continue
        # `--not --remotes` = reachable from this branch, from no remote-tracking ref.
        # Exactly "if this branch disappears, these commits exist nowhere else."
        rc_b, out_b = _git(
            repo, "log", "--format=%H %cs", full, "--not", "--remotes", "--"
        )
        if rc_b != 0:
            # A git failure must NEVER read as "this branch is clean" -- that is the
            # T-169 class the module docstring elevates to an invariant (a real red
            # dismissed for days as expected background). Record it so render() can
            # announce what it could not check, the way `gh unavailable` does.
            facts["local_only_scan_errors"].append(short)
            continue
        if not out_b:
            continue
        entries = []
        for line in out_b.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                entries.append({"sha": parts[0][:7], "date": parts[1]})
        if entries:
            facts["local_only_commits"][short] = entries

    rc, out = _git(repo, "stash", "list")
    facts["stashes"] = [ln for ln in out.splitlines() if ln] if rc == 0 else []

    worktrees = []
    rc, out = _git(repo, "worktree", "list", "--porcelain")
    if rc == 0:
        cur: dict = {}
        for ln in out.splitlines():
            if ln.startswith("worktree "):
                if cur:
                    worktrees.append(cur)
                cur = {"path": ln.split(" ", 1)[1], "locked": False}
            elif ln.startswith("branch "):
                # Keep BOTH forms. The short name is what every other consumer keys
                # on (`all_worktree_branches`, `worktree_owners`, the keep-marker
                # lookup), and changing it would ripple. But it is LOSSY: git emits
                # `refs/heads/wt/foo` and this drops the `wt/`, so any consumer that
                # feeds the short name back to git as a REF resolves the wrong thing --
                # or, for every branch in this project, nothing at all. The landedness
                # scan below needs a real ref, so the full one is kept beside it.
                _full_ref = ln.split(" ", 1)[1]
                cur["branch_ref"] = _full_ref
                cur["branch"] = _full_ref.rsplit("/", 1)[-1]
            elif ln.startswith("HEAD "):
                cur["head"] = ln.split(" ", 1)[1]
            elif ln == "detached":
                cur["branch"] = None
            elif ln.startswith("locked"):
                # A LOCKED worktree is IN ACTIVE USE -- Claude Code locks the worktree it
                # gave a running subagent. Reporting it as residue is a false positive on a
                # live resource, and a checker that nags about things you are currently
                # using gets tuned out by the third day (the T-169 failure, in miniature).
                # Found by dogfooding this tool on its own session, which had a live
                # subagent worktree open. Locked == busy, not abandoned.
                cur["locked"] = True
                # ...but "locked" alone is a LIVE-PROCESS claim with no expiry, and the
                # lock outlives the process that took it. Discarding the reason threw away
                # the one fact that distinguishes busy from abandoned, so a dead session's
                # worktree stayed exempt from `stale_worktree` FOREVER -- the exact inverse
                # of the false positive the exemption was added to fix, and invisible in
                # both directions (session-268; contrarian a76cbd88644813821).
                #
                # Claude Code writes: `claude session <name> (pid 12345 start <date>)`.
                # A reason we cannot parse leaves `lock_pid` None, which is treated as
                # "assume live" below -- degrade toward the quiet FP, never toward telling
                # someone their in-use worktree is orphaned.
                reason = ln[len("locked") :].strip()
                cur["lock_reason"] = reason
                cur["lock_pid"] = _parse_lock_pid(reason)
        if cur:
            worktrees.append(cur)

    for w in worktrees:
        w["journal"] = _read_worktree_journal(w)
        w["lock_alive"] = _pid_alive(w.get("lock_pid")) if w.get("locked") else False
        w["owner_pids"] = _ownership_pids(w)
        w["ownership"] = _ownership_state(w["owner_pids"], bool(w.get("locked")))

    # Fleet/task diagnostics are detection, not a mutex: state can change after
    # this read, and nothing here blocks creation. Facts cover ALL registered
    # worktrees, including
    # live and primary checkouts. Filtering live trees out of the orphan list is
    # correct for cleanup advice but would hide the exact task collision this
    # inventory exists to make visible.
    facts["worktree_journal_errors"] = []
    task_entries: list[dict] = []
    for w in worktrees:
        journal = w["journal"]
        branch_full = (w.get("branch_ref") or "").removeprefix("refs/heads/")
        if journal["format"] in {"v2", "legacy"} and not journal.get("valid", False):
            facts["worktree_journal_errors"].append(
                {
                    "kind": "malformed",
                    "format": journal["format"],
                    "path": w["path"],
                    "branch": branch_full,
                    "error": journal["error"],
                }
            )
            continue
        if journal["format"] == "v2":
            branch_ok, _ = _git(repo, "check-ref-format", "--branch", journal["branch"])
            default_ok, _ = _git(
                repo, "check-ref-format", "--branch", journal["default_ref"]
            )
            if branch_ok != 0 or default_ok != 0:
                facts["worktree_journal_errors"].append(
                    {
                        "kind": "malformed",
                        "path": w["path"],
                        "branch": branch_full,
                        "error": "branch or default_ref is malformed",
                    }
                )
                continue
            if not _v2_lock_matches(w, journal, branch_full):
                facts["worktree_journal_errors"].append(
                    {
                        "kind": "lock-mismatch",
                        "path": w["path"],
                        "branch": branch_full,
                        "error": "does not match its ai-worktree-v2 Git lock",
                    }
                )
                continue
            task_entries.append(
                {
                    "task_key": journal["task_key"],
                    "parallel_task": bool(journal["parallel_task"]),
                    "path": w["path"],
                    "branch": branch_full,
                    "source": "v2",
                    "state": journal["state"],
                }
            )
            continue
        legacy_key = _legacy_task_key(branch_full)
        if legacy_key:
            task_entries.append(
                {
                    "task_key": legacy_key,
                    "parallel_task": False,
                    "path": w["path"],
                    "branch": branch_full,
                    "source": "legacy-derived",
                    "state": "legacy",
                }
            )
    facts["active_task_entries"] = task_entries

    # A locked worktree whose owning process is GONE is residue, not live work. Keep the
    # exemption for live owners; drop it for dead ones. Also exclude the acting worktree —
    # flagging the session's own tree as "orphan" is a false positive (#249e).
    #
    # The exemption keys on OWNERSHIP, not on the lock. Keying it on the lock meant an
    # UNLOCKED worktree was treated as ownerless, so this tool told a maintainer to
    # `git worktree remove` a checkout a live Codex session was writing to. Absence of a
    # lock is not proof of death; only a pid that answers ESRCH is.
    acting = _real(repo)
    facts["worktrees"] = [
        w
        for w in worktrees[1:]
        if w.get("ownership") != "live" and _real(w["path"]) != acting
    ]  # [0] is primary

    # DIRTY STATE per sibling worktree (session-278b). `git status --porcelain` from
    # a worktree path returns THAT tree's uncommitted files. A worktree with dirty
    # files is NOT an orphan — it is unfinished work, and `git worktree remove` on
    # it destroys that work. The classify() split keys on this field.
    #
    # DEGRADE TOWARD QUIET, same as _pid_alive: a false "clean" hands someone
    # `git worktree remove` for a tree that might have uncommitted work (destructive);
    # a false "dirty" only suppresses the removal command (untidy). On failure,
    # assume dirty.
    for w in facts["worktrees"]:
        rc, out = _git(Path(w["path"]), "status", "--porcelain")
        w["dirty_files"] = (
            [ln for ln in out.splitlines() if ln]
            if rc == 0
            else ["<status check failed>"]
        )

    # LANDEDNESS per sibling worktree. Clean + a proved-dead owner was read as "nothing
    # to lose" and handed over `git worktree remove`. Clean means no UNCOMMITTED files;
    # it says nothing about whether the commits ever reached the default branch. On
    # 2026-08-23 this tool reported a clean, dead-owner worktree as `[HIGH] Orphan
    # worktree` with that command attached while its branch sat 23 commits ahead of
    # `main`. Same class as the dirty-tree split above, and as LEARNING-LOG 2026-08-08
    # ("clean working tree is necessary but not sufficient for worktree removal"):
    # /all-clear names three axes -- CLEAN, DURABLE, LANDED -- and conflating any two is
    # the defect it exists to catch. `dirty_files` covers clean; this covers landed.
    #
    # ANCESTRY LIES (invariant 2) -- and HERE THE LIE IS SAFE, which is why the cheap
    # count is the right instrument for this gate and the wrong one for `stale_branch`.
    # A squash- or rebase-landed branch reads as unlanded, and the only consequence is
    # that a destructive command is WITHHELD. In `stale_branch` the same lie pointed the
    # other way -- toward deleting real work -- so that check pays for per-file evidence.
    # cleanup.sh does the content-level comparison at execution time; all this decides is
    # whether to hand the human a command at all. DEGRADE TOWARD QUIET: -1 means "could
    # not determine", and classify() treats it exactly like unlanded.
    # Resolve ONCE to a ref that exists. See resolve_base_ref for why a bare name here
    # both writes files and silently mutes the gate. `worktrees[0]` is the primary by
    # git's porcelain ordering — the same assumption the `worktrees[1:]` slice relies on.
    _primary_ref = worktrees[0].get("branch_ref") if worktrees else None
    _base = resolve_base_ref(repo, facts["default_branch"], _primary_ref)
    facts["landed_base_ref"] = _base
    for w in facts["worktrees"]:
        # branch_ref, NOT branch: the short name drops the `wt/` component and would
        # resolve to nothing, making every worktree in this project read as
        # "undetermined". That fails safe, which is exactly why it would have gone
        # unnoticed -- the command is withheld either way and nothing looks broken.
        _branch = w.get("branch_ref")
        if not _branch or not _base:
            # Detached HEAD, or no default branch to compare against. Nothing proves the
            # work landed, so nothing licenses removal.
            w["unlanded_commits"] = -1
            continue
        # `refs/heads/<name>` for the same reason the local_only_commits scan uses it: a
        # branch named `--output=<path>` would otherwise be option-parsed by git.
        _rc, _out = _git(repo, "rev-list", "--count", _branch, "--not", _base, "--")
        w["unlanded_commits"] = (
            int(_out.strip()) if _rc == 0 and _out.strip().isdigit() else -1
        )

    # Prefer the canonical gate over a raw `git worktree remove` wherever we advise
    # removal at all. cleanup.sh re-verifies ownership, durability, completeness, clean
    # tree and irreplaceable ignored files AT EXECUTION TIME -- these facts can be stale
    # by the time a human reads the report, and this tool never re-checks before the
    # human acts. Absent (repo_hygiene must run in any repo), fall back to plain git.
    _cleanup = repo / "global-skills" / "start-worktree" / "cleanup.sh"
    facts["cleanup_script"] = str(_cleanup) if _cleanup.is_file() else None

    # EVERY worktree's branch, including the primary checkout AND locked ones. Distinct
    # from `worktrees` above on purpose: that list answers "is this worktree residue?"
    # (so it drops the primary and drops LIVE-locked, which means in-active-use), while
    # this answers the opposite question -- "is someone sitting on this branch right now?"
    # Reusing the filtered list here would mark every actively-used worktree's branch as
    # stranded and fire HIGH on the normal steady state, the FP that kills the tool.
    facts["all_worktree_branches"] = [w["branch"] for w in worktrees if w.get("branch")]

    # OWNERSHIP, not just presence (session-268). `all_worktree_branches` says a branch is
    # occupied but not BY WHOM, so every consumer had to treat "someone's branch" and "your
    # branch" identically -- which is how the tool came to hand one session a
    # `git push origin <another session's branch>` command, crossing an ownership boundary
    # and contradicting the standing ask-before-push rule. Keeping the owner lets a finding
    # about someone else's tree be reported as PRESENCE instead of as your action item.
    facts["worktree_owners"] = {
        w["branch"]: {
            "path": w["path"],
            "pid": w.get("lock_pid"),
            "alive": bool(w.get("lock_alive")),
            "is_acting": _real(w["path"]) == acting,
        }
        for w in worktrees
        if w.get("branch")
    }

    # Is the checkout we are STANDING IN the primary, or a worktree?
    #
    # `worktrees[0]` is the primary by git's own porcelain ordering (the same
    # assumption the `worktrees[1:]` slice above already relies on). This is a
    # different question from `is_acting`, which asks "is this worktree mine?" —
    # here we ask "is mine the shared one?"
    #
    # WHY IT IS RECORDED AS A FACT AND NOT RECOMPUTED IN classify(): classify()
    # is pure over `local`/`remote` and has no repo path to ask. Every prior
    # attempt to smuggle a path in there is what produced the wrong-tree class
    # of bug this file's own docstrings keep recording.
    facts["acting_is_primary"] = (
        bool(worktrees) and _real(worktrees[0]["path"]) == acting
    )

    tags = []
    rc, local_out = _git(repo, "tag")
    rc2, remote_out = _git(repo, "ls-remote", "--tags", "origin")
    if rc == 0 and rc2 == 0:
        remote_tags = {
            ln.rsplit("refs/tags/", 1)[-1]
            for ln in remote_out.splitlines()
            if "refs/tags/" in ln and not ln.endswith("^{}")
        }
        tags = [t for t in local_out.splitlines() if t and t not in remote_tags]
    facts["unpushed_tags"] = tags

    branches = []
    rc, out = _git(
        repo,
        "for-each-ref",
        "--format=%(refname:short)|%(committerdate:short)",
        "refs/remotes/origin",
    )
    if rc == 0:
        for ln in out.splitlines():
            if "|" not in ln:
                continue
            name, date = ln.split("|", 1)
            short = name.replace("origin/", "", 1)
            if short in (base, "HEAD") or not short:
                continue
            branches.append({"ref": name, "short": short, "date": date})
    facts["branches"] = branches
    return facts


def collect_remote_facts(repo: Path, timeout: int = 5) -> dict | None:
    """The ONLY network call. Returns None if gh is unavailable/unauthenticated.

    Degradation follows post-push-ci-check.sh: report partial, NEVER silently omit.
    """
    try:
        r = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
            [
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--json",
                "number,title,headRefName,createdAt",
            ],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if r.returncode != 0:
            return None
        return {"prs": json.loads(r.stdout or "[]")}
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError, ValueError):
        return None


# ======================================================================================
# OFFLINE LAYER -- no git, no network, no filesystem. Fully testable with zero mocking.
#
# Honesty note (code-review MEDIUM): classify() does read the WALL CLOCK, via _age_days(),
# to age-stamp findings against the severity thresholds. It is therefore not referentially
# pure. What IS clock-independent is every SAFETY-critical decision: the no-mutation
# guarantee and the remote-None branch interlock (a branch is never even considered without
# remote facts) do not depend on the date. The only clock effect is a finding crossing a
# severity threshold as it ages — which is the intended behavior. Tests stay hermetic by
# generating fixture dates relative to now(); do NOT hardcode an absolute date in a test.
# ======================================================================================


def classify(local: dict, remote: dict | None) -> list[Finding]:
    findings: list[Finding] = []
    keeps = local.get("keep_markers", {})
    pr_branches = {pr["headRefName"] for pr in remote["prs"]} if remote else set()

    def mark_keep(f: Finding) -> Finding:
        """A keep is suppressed from the ALARM, never from the COUNT -- and it EXPIRES.

        RC11 (Reconciliation Checkpoint) names the failure this avoids: "The Dropped
        Exception -- AI removes an unreconciled item from the exception list without
        resolving it... particularly dangerous because the reconciliation APPEARS clean."
        An ack that never expires is a mute button. So the age is the escalation: past
        KEEP_EXPIRY_DAYS the finding re-enters the alarm as `keep_expired`.
        """
        for ref in (f.ref, f.ref.replace("origin/", "", 1), f"PR #{f.ref}"):
            if ref in keeps:
                age = f.evidence.get("age_days")
                if age is not None and age > KEEP_EXPIRY_DAYS:
                    f.check = "keep_expired"
                    f.severity = "warn"
                    f.title = f"{f.title} — KEPT {age}d ago. Still?"
                    return f
                f.kept = True
                f.kept_reason = "BACKLOG keep: marker"
                f.severity = "info"
                f.disposition = "keep"
                return f
        return f

    for error in local.get("worktree_journal_errors", []):
        mismatch = error.get("kind") == "lock-mismatch"
        findings.append(
            Finding(
                check=(
                    "worktree_lifecycle_mismatch"
                    if mismatch
                    else "malformed_worktree_journal"
                ),
                ref=error.get("branch") or error["path"],
                severity="high",
                title=(
                    (
                        "Incoherent v2 worktree lifecycle evidence"
                        if mismatch
                        else "Malformed worktree journal"
                    )
                    + f": {error['path']} — {error['error']}"
                ),
                disposition="investigate",
                evidence=error,
            )
        )

    task_groups: dict[str, list[dict]] = {}
    for entry in local.get("active_task_entries", []):
        task_groups.setdefault(entry["task_key"], []).append(entry)
    for task_key, entries in sorted(task_groups.items()):
        if len(entries) < 2:
            continue
        legacy_only = all(entry.get("source") == "legacy-derived" for entry in entries)
        v2_entries = [entry for entry in entries if entry.get("source") == "v2"]
        intentional = (
            not legacy_only
            and len(v2_entries) == len(entries)
            and sum(entry.get("parallel_task") is False for entry in v2_entries) == 1
            and sum(entry.get("parallel_task") is True for entry in v2_entries)
            == len(entries) - 1
            and all(entry.get("state") != "task-conflict" for entry in v2_entries)
        )
        if intentional:
            check = "intentional_parallel_task"
            severity = "info"
            title = f"Intentional parallel task '{task_key}': {len(entries)} worktrees"
        elif legacy_only:
            check = "task_key_collision"
            severity = "high"
            title = f"Ambiguous legacy task '{task_key}': {len(entries)} generated worktrees"
        else:
            check = "task_key_collision"
            severity = "high"
            title = f"Task-key collision '{task_key}': {len(entries)} active worktrees"
        findings.append(
            Finding(
                check=check,
                ref=task_key,
                severity=severity,
                title=title,
                disposition="investigate",
                evidence={"task_key": task_key, "worktrees": entries},
            )
        )

    # Report the ref actually compared against, not the NAME we hoped to compare against.
    # Those differ exactly when resolution fell through to the primary checkout's branch,
    # and a title citing the wrong base is evidence the reader cannot check.
    base_branch = local.get("landed_base_ref") or local.get("default_branch", "")
    # Route removal through the canonical gate when it is available: cleanup.sh re-checks
    # ownership, durability, completeness, clean tree and ignored files at the moment the
    # human runs it, which a raw `git worktree remove` does not. Duplicating only part of
    # that check here is what produced the defect this arm now guards against.
    _cleanup_script = local.get("cleanup_script")

    def remove_cmd(path: str) -> str | None:
        """The canonical gate, or NO command at all. Never raw `git worktree remove`.

        This used to fall back to `git worktree remove` wherever cleanup.sh was absent,
        on the reasoning that repo_hygiene must be useful in any repository. That reason
        is real and it is not good enough. The raw command skips every proof that makes
        removal safe — execution-time ownership, durability on a remote, completeness,
        clean tree, and irreplaceable ignored files — which is precisely the set whose
        absence produced the defect this arm was written to fix. The facts here are
        computed once and read later; only the script re-checks them at the moment a
        human acts.

        Withholding is the established shape in this module, not a new severity:
        `stale_branch` never proposes `delete`, a dirty worktree gets no command, and
        unknown ownership gets no command. A diagnostic that cannot vouch for a
        destructive command reports the finding and stays quiet about the remedy.

        NOTE: no `--default-ref` is passed even though we hold a base. cleanup.sh
        resolves the integration branch itself, by content as well as ancestry, and
        overriding that with the cheaper answer computed here would replace its better
        check with our worse one.

        The path is shell-quoted: this string is printed for a human to paste, and a
        worktree path containing a space silently becomes two arguments there.
        """
        if not _cleanup_script:
            return None
        return f"{shlex.quote(_cleanup_script)} {shlex.quote(path)}"

    for wt in local.get("worktrees", []):
        dirty = wt.get("dirty_files", [])
        ref = wt.get("branch") or wt["path"]
        # A dirty worktree is UNFINISHED WORK, not an orphan. Session-278b removed a
        # worktree with ~80 lines of uncommitted code because this check called it
        # "Orphan" and handed over `git worktree remove`. The split: dirty worktrees
        # get no removal command and a title that says what is actually there; clean
        # worktrees keep the removal command because there is nothing to lose.
        if dirty:
            findings.append(
                mark_keep(
                    Finding(
                        check="stale_worktree",
                        ref=ref,
                        severity="high",
                        title=(
                            f"Worktree with uncommitted work: {wt['path']}"
                            f" ({len(dirty)} file(s))"
                        ),
                        disposition="investigate",
                        evidence={
                            "path": wt["path"],
                            "branch": wt.get("branch"),
                            "dirty_count": len(dirty),
                            "dirty_files": dirty[:10],
                        },
                    )
                )
            )
        elif wt.get("ownership") == "dead":
            # DEAD OWNER IS NOT ENOUGH. The owner answering ESRCH proves nobody is
            # WORKING here; it proves nothing about whether the work LANDED. Both must
            # hold before "nothing to lose" is true, and only then does this tool hand
            # over a removal command. See the `unlanded_commits` fact for the incident.
            unlanded = wt.get("unlanded_commits", -1)
            landed = unlanded == 0
            landed_cmd = remove_cmd(wt["path"]) if landed else None
            if landed and landed_cmd:
                title = f"Orphan worktree: {wt['path']}"
            elif landed:
                # Landed and unowned, but the canonical gate is not present in this
                # repo. Say so, so the silence about a remedy reads as a deliberate
                # withholding rather than as an incomplete finding.
                title = (
                    f"Orphan worktree: {wt['path']}"
                    " — work has landed, but no cleanup.sh is available here to verify"
                    " removal safely, so no removal command is offered"
                )
            elif unlanded > 0:
                title = (
                    f"Worktree whose work never landed: {wt['path']}"
                    f" — {unlanded} commit(s) not on {base_branch}"
                )
            else:
                title = (
                    f"Worktree with undetermined landedness: {wt['path']}"
                    " — could not compare its branch against the default branch"
                )
            findings.append(
                mark_keep(
                    Finding(
                        check="stale_worktree",
                        ref=ref,
                        severity="high",
                        title=title,
                        disposition="investigate",
                        evidence={
                            "path": wt["path"],
                            "branch": wt.get("branch"),
                            "ownership": "dead",
                            "owner_pids": wt.get("owner_pids", []),
                            "unlanded_commits": unlanded,
                            "default_branch": base_branch,
                        },
                        # Unlanded (or undeterminable) work licenses NO command. The
                        # branch survives `git worktree remove`, so this is not about
                        # destroying commits -- it is that an inventory telling you to
                        # delete the checkout reads as "this is finished", and it is not.
                        command=landed_cmd,
                    )
                )
            )
        else:
            # UNKNOWN ownership. Nothing names an owner, so nothing proves the
            # owner is gone — and a removal command here is exactly the advice
            # that pointed at a checkout a live session was writing to. Report
            # it, ask for verification, attach NO command.
            findings.append(
                mark_keep(
                    Finding(
                        check="stale_worktree",
                        ref=ref,
                        severity="medium",
                        title=(
                            f"Worktree with unverifiable ownership: {wt['path']}"
                            " — no live session recorded, and none proved gone"
                        ),
                        disposition="investigate",
                        evidence={
                            "path": wt["path"],
                            "branch": wt.get("branch"),
                            "ownership": "unknown",
                            "why": (
                                "no lifecycle journal owner_pid and no parseable pid"
                                " in the Git lock reason"
                            ),
                        },
                    )
                )
            )

    for b in local.get("branches", []):
        # HARD INTERLOCK: with no remote facts we cannot know whether a branch carries an
        # open PR. Deleting the Dependabot branch would CLOSE PR #14 and Dependabot would
        # recreate it -- session-250 caught this by hand. So: never suggest touching a
        # branch we cannot vet. This is a rule, not a heuristic.
        if remote is None:
            continue
        if b["short"] in pr_branches:
            continue
        age = _age_days(b["date"])
        if age is None or age < STALE_BRANCH_DAYS:
            continue
        ev = {"age_days": age, "date": b["date"]}
        findings.append(
            mark_keep(
                Finding(
                    check="stale_branch",
                    ref=b["ref"],
                    severity="high",
                    title=f"Stale branch: {b['ref']} ({age}d, no open PR)",
                    # NEVER 'delete'. Ancestry lies; the human adjudicates on evidence.
                    disposition="investigate",
                    evidence=ev,
                )
            )
        )

    for t in local.get("unpushed_tags", []):
        findings.append(
            mark_keep(
                Finding(
                    check="unpushed_tag",
                    ref=t,
                    severity="warn",
                    title=f"Tag exists only locally: {t}",
                    disposition="push",
                    evidence={"age_days": STALE_TAG_DAYS + 1},
                    command=f"git push origin {t}",
                )
            )
        )

    commits = local.get("unpushed_commits", [])
    if commits:
        ages = [a for a in (_age_days(c["date"]) for c in commits) if a is not None]
        oldest = max(ages) if ages else 0
        # Per-push authorization (restored session-250) makes "commits sit unpushed
        # pending approval" the NORMAL steady state. Alarming on that would mean the
        # tool's first act every morning is to complain about last night.
        sev = "info" if oldest <= FRESH_COMMIT_DAYS else "warn"
        findings.append(
            Finding(
                check="unpushed_commits",
                ref=f"{len(commits)}-commits",
                severity=sev,
                title=f"{len(commits)} unpushed commit(s), oldest {oldest}d",
                disposition="push",
                evidence={"age_days": oldest, "count": len(commits)},
            )
        )

    # Commits that exist on no remote, per branch. See the collect-side comment for the
    # two incidents (session-241 `ddbb1aa`, session-255 x3) this check exists to make
    # visible BEFORE a branch is re-created or a worktree removed.
    base = local.get("default_branch", "")
    current = local.get("current_branch", "")
    live_worktree_branches = set(local.get("all_worktree_branches", []))
    unpushed_sev = next(
        (f.severity for f in findings if f.check == "unpushed_commits"), None
    )

    # GROUP BY COMMIT SET FIRST. `git log <br> --not --remotes` returns everything
    # reachable from <br> and absent from every remote -- NOT commits unique to <br>. So
    # three worktrees branched from an unpushed `main` all hold the SAME commits, and
    # reporting per-branch would triple-count the normal steady state and hand out a
    # `git push origin <worktree-branch>` that pushes main's work onto a stray remote
    # branch (which later resurfaces as a `stale_branch` finding). Count inflation on the
    # steady state is the FP-fatal direction for this tool, so collapse identical sets.
    groups: dict[frozenset, dict] = {}
    for br, entries in sorted(local.get("local_only_commits", {}).items()):
        if not entries:
            continue
        g = groups.setdefault(
            frozenset(c["sha"] for c in entries), {"branches": [], "entries": entries}
        )
        g["branches"].append(br)

    for g in groups.values():
        branches, entries = g["branches"], g["entries"]
        ages = [a for a in (_age_days(c["date"]) for c in entries) if a is not None]
        oldest = max(ages) if ages else 0
        is_current = current in branches
        # STRANDED = no live worktree is sitting on any branch holding these commits, and
        # it is not the current checkout. That is work nobody is working on -- a genuine
        # anomaly, not the steady state -- so it earns HIGH and thereby reaches the
        # PRIMARY seam (pre-push runs at --min-severity high; session-start runs at warn).
        # Work on a branch someone IS sitting on stays WARN: with per-push authorization
        # and concurrent worktree sessions that is normal, and crying HIGH every session
        # is how a checker becomes wallpaper (the T-169 failure).
        # ...but NOT while the work is same-day fresh. In a repo that does not use
        # worktrees, every branch you are not currently on reads as "stranded", so
        # stranded-alone would fire HIGH on ordinary feature branches and become the
        # wallpaper this severity split exists to avoid. Work nobody is sitting on AND
        # that has survived a day is the anomaly worth escalating to the pre-push seam.
        stranded = not is_current and not (set(branches) & live_worktree_branches)
        sev = (
            "high"
            if (
                oldest >= STALE_BRANCH_DAYS or (stranded and oldest > FRESH_COMMIT_DAYS)
            )
            else "warn"
        )

        # SEVERITY-AWARE suppression, not presence-based. Presence-based was a false
        # NEGATIVE in precisely the destruction class: `unpushed_commits` is `info` for
        # same-day commits, both hooks run at `warn` or `high`, so a current branch WITH
        # an upstream and fresh commits produced a single `info` finding and the tool
        # reported the repo CLEAN -- the session-255 shape with an upstream present.
        # Only stay quiet when the other finding already surfaces at this floor or above.
        if (
            is_current
            and len(branches) == 1
            and unpushed_sev is not None
            and SEVERITY_ORDER[unpushed_sev] >= SEVERITY_ORDER[sev]
        ):
            continue

        # SOMEONE ELSE'S BRANCH IS PRESENCE, NOT YOUR ACTION ITEM (session-268).
        #
        # Verified live: run from session-267's checkout, this emitted
        #   [WARN] 1 commit(s) on worktree-session-268 exist on no remote
        #          -> git push origin worktree-session-268
        # handing one session a command to push ANOTHER live session's branch. That
        # crosses an ownership boundary and contradicts the standing ask-before-push
        # rule, and it is precisely the "warning me about the other session beyond
        # that work is being done" the concurrency model exists to prevent.
        #
        # The severity logic already knew which branches were occupied
        # (`live_worktree_branches`) but used it only to LOWER severity, never to
        # attribute. With ownership retained we can say whose it is. Report it once,
        # neutrally, with no command -- their unpushed work is not a defect in your
        # tree, and it is genuinely useful to know a sibling is active.
        # PARTITION THE GROUP, NEVER SHORT-CIRCUIT IT. The first version of this fix
        # did `if foreign: ... continue`, which suppressed the WHOLE group as soon as
        # ANY member was foreign -- and groups routinely mix owners, because
        # `git log <br> --not --remotes` returns everything absent from remotes, so a
        # sibling's worktree cut from an unpushed `main` shares main's commit set
        # exactly. Concretely: group {main, wt-sibling} viewed from wt-mine emitted the
        # sibling presence line and then dropped MAIN's unpushed commits on the floor --
        # a false negative in the same work-destruction class (n=2) this module exists
        # to prevent, introduced by the fix for a false positive. Caught by three
        # independent reviewers; none of the tests covered a mixed group.
        #
        # Ownership is a PER-BRANCH property, so suppression must be per-branch too:
        # announce the foreign branches, then carry on with the ones you own.
        #
        # Gated on `is_acting`, NOT on liveness. "Is this my checkout?" needs no lock:
        # you should never be handed a push command aimed at another checkout's branch
        # whether or not its owner is currently breathing. Liveness only decides the
        # WORDING (an active teammate vs an abandoned tree) -- and a dead owner's
        # stranded work stays a real finding, which is the session-255 class.
        owners = local.get("worktree_owners", {})
        foreign = [
            (b, owners[b])
            for b in branches
            if b in owners and not owners[b].get("is_acting") and b != current
        ]
        live_foreign = [(b, o) for b, o in foreign if o.get("alive")]
        if live_foreign:
            b0, o0 = live_foreign[0]
            findings.append(
                Finding(
                    check="sibling_session_active",
                    ref=b0,
                    severity="info",
                    title=(
                        f"Another session is working on {b0}"
                        f" ({len(entries)} unpushed commit(s)) — not your branch"
                    ),
                    disposition="keep",
                    evidence={
                        "path": o0.get("path"),
                        "pid": o0.get("pid"),
                        "branches": [b for b, _ in live_foreign],
                        "count": len(entries),
                    },
                )
            )

        # Drop only the LIVE-foreign branches from the actionable set. A dead owner's
        # branch stays actionable: that is stranded work, not a teammate.
        live_foreign_names = {b for b, _ in live_foreign}
        owned = [b for b in branches if b not in live_foreign_names]
        if not owned:
            continue
        branches = owned

        # Push whichever branch the human actually thinks in: the default branch if it
        # holds these commits, else the current checkout, else the first alphabetically.
        target = next((b for b in (base, current) if b in branches), branches[0])
        where = branches[0] if len(branches) == 1 else f"{len(branches)} branches"
        findings.append(
            mark_keep(
                Finding(
                    check="local_only_commits",
                    ref=branches[0],
                    severity=sev,
                    title=(
                        f"{len(entries)} commit(s) on {where} exist on no remote"
                        f", oldest {oldest}d — lost if the branch is deleted or re-created"
                    ),
                    disposition="push",
                    evidence={
                        "age_days": oldest,
                        "count": len(entries),
                        "branches": branches,
                        "is_current_checkout": is_current,
                        "stranded": stranded,
                        # Where the work actually lives, when that is NOT your tree.
                        # An unlocked worktree is indistinguishable from an abandoned
                        # one, so it stays actionable (silencing stranded work is the
                        # destructive error) -- but the human should not have to assume
                        # it is their own branch before acting on it.
                        **(
                            {"other_checkout": _oc}
                            if (
                                _oc := next(
                                    (
                                        o.get("path")
                                        for b in branches
                                        if (o := owners.get(b))
                                        and not o.get("is_acting")
                                        and b != current
                                    ),
                                    None,
                                )
                            )
                            else {}
                        ),
                        # The recovery handle. Recorded HERE, computed from git, and
                        # deliberately NOT on the branch it describes.
                        "tip_sha": entries[0]["sha"],
                    },
                    command=f"git push origin {target}",
                )
            )
        )

    # A branch we could not scan is NOT a clean branch. Surfacing it as a finding is the
    # T-169 discipline: "the tool broke" must never render as "the repo is clean".
    for short in local.get("local_only_scan_errors", []):
        findings.append(
            Finding(
                check="local_only_scan_failed",
                ref=short,
                severity="warn",
                title=f"Could NOT check {short} for local-only commits — this is not 'clean'",
                disposition="investigate",
                evidence={"age_days": 0, "branch": short},
            )
        )

    if local.get("dirty_files"):
        # SEVERITY DEPENDS ON *WHICH* TREE IS DIRTY.
        #
        # Uncommitted work in a worktree is ordinary mid-session state — that is
        # what a worktree is for, and firing HIGH on it would make this check
        # noise on the normal steady state, which is the false-positive class
        # that kills a tool (and, in this repo, trains use of a bypass flag that
        # also disables the secret scanner).
        #
        # Uncommitted work in the PRIMARY checkout is a different animal. The
        # primary is the shared integration point: work left there belongs to no
        # branch, blocks a sibling's fast-forward merge, and — because the global
        # skill and hook symlinks resolve into it — can go live machine-wide
        # while still uncommitted. All three of this repo's recorded work losses
        # have that shape, session-267's uncommitted security review being the
        # one that also blocked another session's merge.
        #
        # `warn` sits BELOW the pre-push seam's `--min-severity high` floor, so
        # before this the single most dangerous case was the one case the seam
        # could not see. Escalating is safe rather than bypass-training because
        # pre-push Check 9 reports and never denies ("WHY IT WARNS AND DOES NOT
        # BLOCK") — this makes the finding visible, not blocking.
        in_primary = local.get("acting_is_primary", False)
        findings.append(
            Finding(
                check="dirty_tree",
                ref="working-tree",
                severity="high" if in_primary else "warn",
                title=(
                    f"{len(local['dirty_files'])} uncommitted file(s) in the PRIMARY "
                    "checkout — belongs to no branch, blocks sibling merges"
                    if in_primary
                    else f"{len(local['dirty_files'])} uncommitted file(s)"
                ),
                disposition="fix",
                evidence={
                    "files": local["dirty_files"][:20],
                    "acting_is_primary": in_primary,
                },
            )
        )

    for i, s in enumerate(local.get("stashes", [])):
        findings.append(
            mark_keep(
                Finding(
                    check="stash",
                    ref=f"stash@{{{i}}}",
                    severity="warn",
                    title=f"Stash: {s}",
                    disposition="decide",
                    evidence={"age_days": 0},
                )
            )
        )

    if remote:
        for pr in remote["prs"]:
            age = _age_days(pr["createdAt"][:10]) or 0
            if age >= OPEN_PR_HIGH_DAYS:
                sev = "high"
            elif age >= OPEN_PR_WARN_DAYS:
                sev = "warn"
            else:
                sev = "info"
            findings.append(
                mark_keep(
                    Finding(
                        check="open_pr",
                        ref=str(pr["number"]),
                        severity=sev,
                        title=f"PR #{pr['number']} open {age}d: {pr['title'][:60]}",
                        disposition="merge",
                        evidence={"age_days": age, "branch": pr["headRefName"]},
                    )
                )
            )

    for ref in keeps:
        known = {f.ref for f in findings} | {
            f.ref.replace("origin/", "", 1) for f in findings
        }
        if ref not in known:
            findings.append(
                Finding(
                    check="stale_keep_marker",
                    ref=ref,
                    severity="info",
                    title=f"BACKLOG `keep: {ref}` points at a ref that no longer exists — prune it",
                    disposition="fix",
                    evidence={},
                )
            )

    return findings


def summarize(findings: list[Finding], min_sev: str) -> dict:
    floor = SEVERITY_ORDER[min_sev]
    # PRESENCE IS CONTEXT, NOT A FINDING (session-268). "Another session is working
    # here" is something the human asked to always see, and it is never something to
    # act on -- so it is carried in its own channel: excluded from `alarming` at EVERY
    # severity floor (otherwise `--min-severity info` would report a live teammate as
    # an open finding), excluded from `clean` (a busy sibling does not make your repo
    # dirty), and rendered unconditionally below.
    presence_checks = {"sibling_session_active", "intentional_parallel_task"}
    presence = [f for f in findings if f.check in presence_checks]
    rest = [f for f in findings if f.check not in presence_checks]
    # A kept finding is suppressed from the ALARM but stays in the COUNT (RC11).
    alarming = [f for f in rest if not f.kept and SEVERITY_ORDER[f.severity] >= floor]
    kept = [f for f in rest if f.kept]
    return {
        "clean": not alarming,
        "counts": {
            "alarming": len(alarming),
            "kept": len(kept),
            "presence": len(presence),
            "total": len(rest),
        },
        "findings": [f.to_dict() for f in alarming],
        "kept": [f.to_dict() for f in kept],
        "presence": [f.to_dict() for f in presence],
    }


def render(report: dict, network_ok: bool) -> str:
    lines: list[str] = []
    alarming = report["findings"]
    presence = report.get("presence", [])
    if not alarming and not report["kept"] and not presence:
        return ""
    if alarming:
        lines.append(f"Repo hygiene — {len(alarming)} open finding(s):")
        for f in alarming:
            lines.append(f"  [{f['severity'].upper():4}] {f['title']}")
            if f.get("command"):
                lines.append(
                    f"           → {f['command']}   (run it yourself; this tool never does)"
                )
    if report["kept"]:
        kept_refs = ", ".join(f["ref"] for f in report["kept"])
        lines.append(f"  {len(report['kept'])} kept (BACKLOG marker): {kept_refs}")
    # ONE NEUTRAL LINE, no command, no severity tag — the explicit requirement is to
    # be told that work is in progress and nothing more. Rendered even when the repo
    # is otherwise clean, because that is the case where a session most needs to know
    # a sibling is live before it touches a shared file.
    for p in presence:
        ev = p.get("evidence", {}) or {}
        if p["check"] == "intentional_parallel_task":
            lines.append(f"  {p['title']}.")
        else:
            lines.append(
                f"  Another session is working here: {p['ref']} ({ev.get('path', '?')})."
            )
    if not network_ok:
        lines.append(
            "  NOTE: gh unavailable — open PRs and branch-vs-PR checks were NOT run."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Compute the repo's close-out inventory (read-only)."
    )
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--offline", action="store_true", help="skip all network calls")
    ap.add_argument(
        "--min-severity",
        choices=["info", "warn", "medium", "high"],
        default="warn",
    )
    args = ap.parse_args(argv)

    repo = args.repo.resolve()
    if not is_git_repo(repo):
        print(f"not a git repository: {repo}", file=sys.stderr)
        return 3  # NOT 0 -- "can't tell" must never read as "clean"

    # NORMALIZE TO THE WORKTREE TOPLEVEL. `is_git_repo` is true for any SUBdirectory,
    # and `--repo .` is the argparse default -- so running this by hand from `scripts/`
    # gave an acting path that matches no entry in `git worktree list`, making every
    # `is_acting` False and your OWN worktree look like a stranger's. Both shipped
    # callers happen to pass a toplevel, so this was latent rather than live; it is one
    # line, and `.claude/hooks/lib/repo-root.sh` already documents the same
    # normalization as house practice.
    rc_top, top = _git(repo, "rev-parse", "--show-toplevel")
    if rc_top == 0 and top:
        repo = Path(top)

    try:
        local = collect_local_facts(repo)
        remote = None if args.offline else collect_remote_facts(repo)
        findings = classify(local, remote)
        report = summarize(findings, args.min_severity)
        report["network"] = {"attempted": not args.offline, "ok": remote is not None}
        # render/dumps stay INSIDE the try (code-review LOW): a crash while formatting is a
        # TOOL error (rc 2), not a "findings" result (rc 1). Outside the try it would leak
        # as an uncaught exception -> rc 1, mislabeling a tool failure as a real result.
        rendered = (
            json.dumps(report, indent=2)
            if args.json
            else render(report, network_ok=remote is not None)
        )
    except Exception as exc:  # noqa: BLE001 - a crash must be rc 2, never rc 0
        print(f"repo_hygiene: internal error: {exc}", file=sys.stderr)
        return 2

    if rendered:
        print(rendered)

    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
