"""Fresh-process routing tests for #363, independent of pytest's sys.path.

The negative control imports the primary source through a .pth file in a
dedicated interpreter. Linked-worktree execution must instead import its edited
source, without changing that .pth file or the caller's configuration.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

import pytest

REPO = Path(__file__).resolve().parents[1]
LAUNCHER = REPO / "scripts" / "run_local.py"


def run(argv, cwd, env):
    return subprocess.run(
        [str(arg) for arg in argv],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )


@pytest.fixture
def checkouts(tmp_path):
    primary = tmp_path / "primary checkout"
    linked = tmp_path / "linked checkout"
    primary.mkdir()
    (primary / "scripts").mkdir()
    shutil.copyfile(LAUNCHER, primary / "scripts/run_local.py")
    package = primary / "src/ai_governance_mcp"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('MARKER = "primary"\n')
    (package / "probe.py").write_text(
        "import json, os, sys, ai_governance_mcp\n"
        "print(json.dumps(dict(marker=ai_governance_mcp.MARKER, "
        "source=ai_governance_mcp.__file__, executable=sys.executable, "
        "cwd=os.getcwd(), args=sys.argv[1:], "
        "env={k:v for k,v in os.environ.items() if k.startswith('AI_GOVERNANCE_')})))\n"
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    for args in (
        ["init"],
        ["add", "."],
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-m",
            "fixture",
        ],
        ["worktree", "add", "-b", "linked", str(linked)],
    ):
        proc = run(["git", *args], primary, env)
        assert proc.returncode == 0, proc.stderr
    (linked / "src/ai_governance_mcp/__init__.py").write_text('MARKER = "linked"\n')
    virtual = tmp_path / "interpreter"
    venv.EnvBuilder(with_pip=False).create(virtual)
    python = virtual / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    proc = run(
        [python, "-c", "import site; print(site.getsitepackages()[0])"], primary, env
    )
    assert proc.returncode == 0, proc.stderr
    pth = Path(proc.stdout.strip()) / "primary-editable.pth"
    pth.write_text(str(primary / "src") + "\n")
    return primary, linked, python, pth, env


@pytest.mark.parametrize("which", [0, 1])
def test_launcher_routes_primary_and_linked_without_repointing_install(
    checkouts, which
):
    primary, linked, python, pth, env = checkouts
    checkout = (primary, linked)[which]
    before = pth.read_bytes()
    bare = run([python, "-m", "ai_governance_mcp.probe"], checkout, env)
    assert bare.returncode == 0, bare.stderr
    assert json.loads(bare.stdout)["marker"] == "primary"
    proc = run(
        [python, checkout / "scripts/run_local.py", "ai_governance_mcp.probe"],
        checkout,
        env,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["marker"] == ("primary", "linked")[which]
    assert Path(result["source"]) == checkout / "src/ai_governance_mcp/__init__.py"
    assert Path(result["executable"]) == python
    assert pth.read_bytes() == before


def test_preserves_cwd_arguments_and_configuration_with_competing_pythonpath(checkouts):
    primary, linked, python, _, env = checkouts
    explicit = {
        "AI_GOVERNANCE_DOCUMENTS_PATH": "relative documents",
        "AI_GOVERNANCE_INDEX_PATH": "relative index",
        "AI_GOVERNANCE_REFERENCE_LIBRARY_PATH": "relative library",
        "AI_GOVERNANCE_PRIVATE_REFERENCE_LIBRARY_PATH": "private library",
        "AI_GOVERNANCE_LOGS_PATH": "relative logs",
        "AI_GOVERNANCE_USER_DATA_ROOT": "relative data",
    }
    env.update(explicit, PYTHONPATH=str(primary / "src"))
    env["AI_GOVERNANCE_EMBEDDING_MODEL"] = "explicit-model-setting"
    args = ["space argument", "--force", "--check", "$(literal)"]
    proc = run(
        [python, linked / "scripts/run_local.py", "ai_governance_mcp.probe", *args],
        primary,
        env,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["marker"] == "linked"
    assert result["cwd"] == str(primary)
    assert result["args"] == args
    assert result["env"] == {
        key: value for key, value in env.items() if key.startswith("AI_GOVERNANCE_")
    }


def test_missing_dependencies_fail_before_extractor_body(checkouts):
    _, linked, python, _, env = checkouts
    marker = linked / "index-write"
    (linked / "src/ai_governance_mcp/extractor.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
    )
    proc = run(
        [python, linked / "scripts/run_local.py", "ai_governance_mcp.extractor"],
        linked,
        env,
    )
    assert proc.returncode == 2
    assert str(python) in proc.stderr
    assert "numpy" in proc.stderr
    assert not marker.exists()


def test_module_exit_status_is_preserved(checkouts):
    _, linked, python, _, env = checkouts
    (linked / "src/ai_governance_mcp/exit_probe.py").write_text("raise SystemExit(7)\n")
    proc = run(
        [python, linked / "scripts/run_local.py", "ai_governance_mcp.exit_probe"],
        linked,
        env,
    )
    assert proc.returncode == 7


@pytest.mark.parametrize(
    "dependency",
    [
        "numpy",
        "yaml",
        "pydantic",
        "pydantic_settings",
        "rank_bm25",
        "sentence_transformers",
    ],
)
def test_unavailable_dependency_is_rejected_before_build(dependency, tmp_path):
    # Shadow just one dependency in a fresh process; pytest's imports cannot
    # satisfy the check. Broken transitive imports take this same failure path.
    (tmp_path / f"{dependency}.py").write_text(
        f"raise ImportError('unavailable dependency: {dependency}')\n"
    )
    env = os.environ.copy()
    env.update(
        PYTHONPATH=str(tmp_path), AI_GOVERNANCE_INDEX_PATH=str(tmp_path / "index")
    )
    proc = run([sys.executable, LAUNCHER, "ai_governance_mcp.extractor"], tmp_path, env)
    assert proc.returncode == 2, proc.stderr
    assert f"unavailable dependency: {dependency}" in proc.stderr
    assert sys.executable in proc.stderr
    assert not (tmp_path / "index").exists()


@pytest.mark.parametrize(
    "args",
    [
        ["os"],
        ["ai_governance_mcp/other"],
        ["--check", "ai_governance_mcp.server"],
        ["--check", "ai_governance_mcp.extractor", "other-docs"],
    ],
)
def test_rejects_invalid_check_or_module(args, tmp_path):
    proc = run([sys.executable, LAUNCHER, *args], tmp_path, os.environ.copy())
    assert proc.returncode == 2


def test_extractor_check_imports_real_dependencies_without_building(tmp_path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    paths = {
        name: str(tmp_path / name)
        for name in (
            "documents_path",
            "index_path",
            "reference_library_path",
            "private_reference_library_path",
            "logs_path",
        )
    }
    env.update({"AI_GOVERNANCE_" + k.upper(): v for k, v in paths.items()})
    env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    proc = run(
        [sys.executable, LAUNCHER, "--check", "ai_governance_mcp.extractor"],
        tmp_path,
        env,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["paths"] == paths
    assert Path(result["package_source"]) == REPO / "src/ai_governance_mcp/__init__.py"
    assert result["interpreter"] == sys.executable
    assert result["extractor_dependencies"] == "importable (model not loaded)"
    assert all(not Path(path).exists() for path in paths.values())
