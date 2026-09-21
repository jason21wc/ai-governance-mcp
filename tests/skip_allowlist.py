"""Registered skip reasons. An UNREGISTERED skip fails the run.

WHY THIS EXISTS — the root cause, not the instances.

This repo enforces ACTIONS structurally (hard-mode hooks block Bash/Edit/Write
until governance runs; pre-push blocks on tests, reviewers, checklists) and
enforces OBSERVATIONS advisorily. Every defect found in session-302 lived in the
observation layer and presented the same way: not as a failure, but as a value
that READS as success.

  - a 600-char truncated body shaped exactly like a complete one
  - a dead pointer returning five plausible, wrong results
  - 25 tests skipping instead of failing (the whole MRR/Recall benchmark)
  - a security scan reporting PASS while scanning zero files
  - a staleness guard skipping on a false signal (authored in that same session)

None of those failed. None was visible in a green run. The repo's own LEARNING-LOG
records that advisory compliance runs ~87% while structural blocking approaches
100% — a lesson applied to what the AI DOES and never to what the system REPORTS.

This module makes one observation structural: a skip must be REGISTERED, with a
reason someone wrote down on purpose.

WHAT THIS CATCHES: a new skip reason appearing anywhere in the suite. That is
exactly the failure mode of the mtime staleness guard — it introduced a new reason
("index is STALE") that silently disabled 13 real-index tests, and the only signal
was a skip count moving 4 -> 17 in a log nobody diffs.

WHAT THIS DOES NOT CATCH, stated plainly because overselling a guard is how the
last one got through: a REGISTERED reason firing far more often than it should.
The original 25-skip hole would have passed this check, because "Production index
not found" is a legitimate reason that would have been registered from day one.
Catching that needs a per-reason count expectation that is environment-aware (a
fresh clone and CI's default matrix legitimately have no index), which is a
larger design than this file. Filed rather than half-built here.
"""

# Each entry is a substring matched against the skip reason. Keep them specific
# enough that a genuinely new condition does not slip under an existing entry.
#
# Adding an entry is the point of the mechanism, not a workaround for it: it forces
# whoever adds a skip to say why the skip is correct, in a file someone reviews.
REGISTERED_SKIP_REASONS: dict[str, str] = {
    "POSIX watcher containment tests": (
        "The supervisor uses POSIX process groups and flock. Windows retains its "
        "existing uptime-only watcher and cannot execute these containment probes."
    ),
    # --- environment-conditional: the artifact under test genuinely may not exist
    "governance index not built": (
        "A fresh clone and CI's default matrix have no built index. Legitimate. "
        "The resolver names every location it looked in, so a miss is diagnosable "
        "rather than mysterious — see tests/index_paths.py."
    ),
    "is STALE": (
        "Index composition does not match documents/. Count assertions would be "
        "measured against a different corpus, so skipping is the honest outcome. "
        "check.sh's index-freshness step is the hard gate."
    ),
    "index built without embeddings": (
        "Row-identity tests need the .npy files; an index built without them cannot "
        "answer the question those tests ask."
    ),
    "knowledge-graph extras not installed (litellm required)": (
        "Knowledge-graph support is an optional extra. The default dev/context-engine "
        "install deliberately tests the non-KG product without pulling its provider stack."
    ),
    "could not import 'litellm'": (
        "Thinking-block integration requires the optional knowledge-graph provider stack; "
        "the tests run only when that extra is installed."
    ),
    "cognee not installed — 'not indexed' guard is unreachable": (
        "This test asks which precondition wins inside the optional Cognee path. Without "
        "Cognee the adapter rejects earlier, so the indexed-state assertion is unreachable."
    ),
    "compliance procedure is private; absent in the public tree": (
        "`.claude/skills/compliance-review/` is not in the public allowlist, so a test "
        "asserting against that procedure has nothing to read there. Registered "
        "2026-08-13 while clearing the public build."
    ),
    "not a git checkout": (
        "The public release STAGING TREE is a plain directory, not a repo — the build "
        "copies allowlisted files rather than cloning. Tests that read git ancestry "
        "have no history to read. Legitimate in staging; in the private repo this "
        "reason should never fire, and if it does it means the checkout is broken."
    ),
    "not in a git repo — adopter context outside VCS": (
        "Same condition as the entry above, from the adopter-facing angle: the "
        "framework is designed to be usable in a directory that is not under version "
        "control, so this probe legitimately has nothing to inspect."
    ),
    # --- behavioural: the probe does not apply to the thing under test
    "exposes no *_DEBUG channel to observe": (
        "session-start-hygiene.sh has no debug channel, so the observation this "
        "test makes is not available for that hook. Asserted elsewhere."
    ),
    "does not use `set -e`": (
        "session-start-hygiene.sh survives a failing source by design; the failure "
        "mode this test probes does not exist for it."
    ),
    "credential-path probe": (
        "This gate does not read credential paths, so the probe is inapplicable "
        "rather than passing."
    ),
    "risk signal that HOME-unset removes by construction": (
        "The OOM gate's deny needs a signal that unsetting HOME removes, so the "
        "condition cannot be constructed. Abort-freedom is asserted separately."
    ),
    # --- CI/local split
    "local-only check; no hook install on a runner": (
        "Hook-install verification is meaningless on a runner with no hook install."
    ),
    "inspects this developer's machine state": (
        "The live telemetry-location probe intentionally inspects local user data; CI "
        "has no representative developer machine state."
    ),
    "git did not produce a multi-base merge": (
        "Platform Git did not construct the optional criss-cross fixture."
    ),
    "python3 not found on PATH": (
        "The degraded-environment probe cannot execute without its subject interpreter."
    ),
    "no /dev/zero": ("The adversarial stream fixture is unavailable on this platform."),
    "hook not present in this checkout": (
        "Public or reduced-source checkouts may omit private hook assets."
    ),
    "uid has no passwd entry": (
        "Minimal containers can have a numeric uid without a passwd database row."
    ),
    "No PDF library available": (
        "PDF parsing is an optional context-engine capability."
    ),
    "tree-sitter-language-pack not installed": (
        "Tree-sitter language parsing is an optional extra."
    ),
    "tree-sitter not available": (
        "Tree-sitter parsing is optional in the default install."
    ),
    "root resolution needs git rev-parse": (
        "The journal root-resolution probe requires Git metadata."
    ),
    "domains.json not found": (
        "Reduced/public corpus fixtures may omit the private domain registry."
    ),
    "README.md not found": (
        "Reduced corpus fixtures can deliberately omit repository-level documentation."
    ),
    "No domains in index": (
        "An empty fixture index has no domain-specific assertion to make."
    ),
    "no retired registry entries yet": (
        "The validator probe is inapplicable until a retired entry exists."
    ),
    "registry file does not exist": (
        "Pre-registry historical checkpoints legitimately lack the registry file."
    ),
    "registry history truncated": (
        "A shallow clone cannot prove the historical registry assertion."
    ),
    "git not available": (
        "Git-backed validator and scaffold probes are inapplicable without Git."
    ),
    "git rev-parse unavailable": (
        "Repository-history probes require a working Git checkout."
    ),
    "documents/ not present in this checkout": (
        "Reduced/public source fixtures may omit the private corpus."
    ),
    "script parses registries with python3": (
        "The installed-hook checker requires its parser interpreter."
    ),
    "no canonical hooks in the repo": (
        "A reduced fixture with no hook corpus has no install target to assert."
    ),
    "hook parses its payload with jq": (
        "The post-push hook probe requires jq to parse its event payload."
    ),
    "jq still reachable on the lean PATH": (
        "The degraded-PATH fixture could not hide jq on this platform."
    ),
    "tiers.json not found": ("Reduced corpus fixtures may omit the tier registry."),
    "tiers.json files not found": (
        "The cross-file tier comparison is inapplicable when both registries are absent."
    ),
    "no governance corpus resolved here": (
        "A bare-wheel fixture deliberately contains code without the governance corpus."
    ),
    "ground-truth fixture fixture/semantic-rank-landed not present in this tree": (
        "The public release fresh snapshot has no private fixture refs. The private "
        "source tree retains and exercises this landed-content fixture."
    ),
    "ground-truth fixture fixture/probe-diverged not present in this tree": (
        "The public release fresh snapshot has no private fixture refs. The private "
        "source tree retains and exercises this divergence fixture."
    ),
}


def is_registered(reason: str) -> bool:
    """True when a skip reason matches a registered entry."""
    return any(known in reason for known in REGISTERED_SKIP_REASONS)
