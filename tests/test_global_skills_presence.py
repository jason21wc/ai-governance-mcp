"""Presence guard for framework-owned global skills (BACKLOG #55).

``scripts/sync-global-skills.sh`` auto-discovers whatever is under
``global-skills/`` (``for src in "$SRC_ROOT"/*/``), so it cannot detect a
framework-owned skill that silently drops back out of version control — a
deleted skill just syncs as "one fewer," with no error. The install target
``~/.claude/skills/<skill>/`` lives outside the repo, so the agents' byte-match
test (``tests/test_server_agents.py``) cannot apply either.

This test is the explicit registry: ``EXPECTED_FRAMEWORK_SKILLS`` must match the
directories actually present under ``global-skills/``, each carrying a
``SKILL.md``. Deleting a known skill — or adding one without registering it
here — fails the build. Update the set deliberately when a framework-owned
skill is genuinely added or removed.

Failure mode guarded: a framework-owned skill silently dropping out of version
control (the #55 guard class; sibling of the BACKLOG #163 sync mechanism, which
captured syncing but not presence).

Third-party skills with their own upstream + license (e.g. ``prompt-master``,
MIT, installed by clone+pin per title-10 CFR Appendix M.3.1) have no repo
canonical and are intentionally NOT under ``global-skills/`` — so they are
excluded from this guard.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_SKILLS_DIR = REPO_ROOT / "global-skills"

# Framework-owned skills that MUST remain captured under global-skills/.
# This set is the single source of truth for "what framework-owned skills exist."
# Update it deliberately when a framework-owned skill is added or removed.
EXPECTED_FRAMEWORK_SKILLS = frozenset(
    {
        "architecture-review",
        "code-review",
        "completion-sequence",
        "content-enhancer",
        "doc-gen",
        "dream",
        "journal",
        "refactor-audit",
        "security-scan",
        "test-suite",
    }
)


def _present_skill_dirs() -> set[str]:
    """Names of skill directories actually present under global-skills/."""
    return {
        p.name
        for p in GLOBAL_SKILLS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    }


def test_global_skills_dir_exists():
    """global-skills/ must exist (the canonical home for framework-owned skills)."""
    assert GLOBAL_SKILLS_DIR.is_dir(), f"global-skills/ missing at {GLOBAL_SKILLS_DIR}"


def test_expected_framework_skills_present():
    """Every expected framework-owned skill exists — catches silent deletion."""
    missing = EXPECTED_FRAMEWORK_SKILLS - _present_skill_dirs()
    assert not missing, (
        f"Framework-owned skill(s) missing from global-skills/: {sorted(missing)}. "
        "If intentionally removed, update EXPECTED_FRAMEWORK_SKILLS in this test."
    )


def test_no_unregistered_skills():
    """No skill dir under global-skills/ is unregistered — forces conscious add."""
    extra = _present_skill_dirs() - EXPECTED_FRAMEWORK_SKILLS
    assert not extra, (
        f"Unregistered skill dir(s) under global-skills/: {sorted(extra)}. "
        "If framework-owned, add to EXPECTED_FRAMEWORK_SKILLS; if third-party, it "
        "should be install-by-reference (not vendored under global-skills/)."
    )


def test_each_framework_skill_has_skill_md():
    """Each expected skill carries a SKILL.md — catches partial/broken capture."""
    missing_md = [
        skill
        for skill in sorted(EXPECTED_FRAMEWORK_SKILLS)
        if not (GLOBAL_SKILLS_DIR / skill / "SKILL.md").is_file()
    ]
    assert not missing_md, f"Framework-owned skill(s) without a SKILL.md: {missing_md}"
