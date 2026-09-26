"""Tests for the unregistered-skip gate in ``tests/conftest.py``.

The gate (session-302) makes one observation structural: a skip must be
registered in ``tests/skip_allowlist.py`` with a reason, or the run fails. It
shipped verified only by a hand-run negative control and no test, and it
carried a defect for exactly that reason — it swept up **xfail**, because
pytest reports an xfailed test as ``outcome == "skipped"`` with a ``wasxfail``
attribute. Consequence measured before the fix: ``pytest
tests/test_doc_pointer_resolution.py`` exited 1 with 5 passed / 1 xfailed /
zero real skips, and the xfail it flagged is BACKLOG #325's acceptance test.

These call the real hook function rather than re-implementing its logic, and the
xfail case is the regression test: before the fix it collected the report.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests import conftest as gate


class _Report:
    """Minimal stand-in for a pytest TestReport.

    ``longrepr`` for a skip is the ``(path, lineno, reason)`` triple the gate
    parses; ``wasxfail`` is set by pytest only on xfail reports, which is the
    single attribute that distinguishes the two outcomes here.
    """

    def __init__(self, nodeid: str, reason: str, *, wasxfail: bool = False):
        self.nodeid = nodeid
        self.skipped = True
        self.longrepr = ("some/file.py", 12, reason)
        if wasxfail:
            self.wasxfail = reason


@pytest.fixture
def collected(monkeypatch):
    """Isolate the gate's module-level accumulator so a test cannot leak into the run."""
    bucket: list[tuple[str, str]] = []
    monkeypatch.setattr(gate, "_UNREGISTERED_SKIPS", bucket)
    return bucket


def test_xfail_is_not_treated_as_an_unregistered_skip(collected):
    """An xfail is a declared expected failure — the opposite of a silent skip.

    Regression test for the shipped defect: pytest sets ``skipped`` True on xfail
    reports, so the gate's bare ``if report.skipped`` failed runs containing any
    xfail. ``strict=True`` already fails the run if such a test starts passing,
    which is a stronger form of this gate's own discipline.
    """
    gate.pytest_runtest_logreport(
        _Report(
            "tests/test_x.py::test_a",
            "BACKLOG #325 — floor not indexed yet",
            wasxfail=True,
        )
    )
    assert collected == []


def test_an_unregistered_plain_skip_is_still_collected(collected):
    """The gate must keep doing its job — this is what makes the test above discriminating."""
    gate.pytest_runtest_logreport(
        _Report("tests/test_y.py::test_b", "some brand new reason nobody registered")
    )
    assert [nodeid for nodeid, _ in collected] == ["tests/test_y.py::test_b"]


def test_a_registered_skip_reason_is_allowed(collected):
    """A reason present in the allowlist passes, so the gate is not merely a skip ban."""
    from tests.skip_allowlist import REGISTERED_SKIP_REASONS

    assert REGISTERED_SKIP_REASONS, "allowlist is empty — this test would be vacuous"
    gate.pytest_runtest_logreport(
        _Report("tests/test_z.py::test_c", next(iter(REGISTERED_SKIP_REASONS)))
    )
    assert collected == []


@pytest.mark.parametrize(
    "reason",
    [
        "knowledge-graph extras not installed (litellm required)",
        "could not import 'litellm': No module named 'litellm'",
        "cognee not installed — 'not indexed' guard is unreachable",
    ],
)
def test_optional_knowledge_graph_skips_are_registered(reason):
    """Default installs explicitly register unavailable optional-KG paths."""
    from tests.skip_allowlist import is_registered

    assert is_registered(reason)


def test_literal_skip_reasons_are_registered_without_triggering_the_condition():
    """A CI-only skip must be discoverable during an ordinary local run."""
    from tests.skip_allowlist import is_registered

    tests_dir = Path(__file__).resolve().parent
    found: list[tuple[str, int, str]] = []
    for path in tests_dir.glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_skip = isinstance(func, ast.Attribute) and func.attr == "skip"
            is_skipif = isinstance(func, ast.Attribute) and func.attr == "skipif"
            values = []
            if is_skip and node.args:
                values.append(node.args[0])
            if is_skipif:
                values.extend(kw.value for kw in node.keywords if kw.arg == "reason")
            for value in values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    found.append((path.name, node.lineno, value.value))

    unregistered = [item for item in found if not is_registered(item[2])]
    assert not unregistered, "literal skip reasons missing from allowlist: " + repr(
        unregistered
    )


@pytest.fixture
def run_execution_gate(tmp_path):
    """Run actual production hook bodies with pytest in a tiny isolated suite."""
    import os
    import subprocess
    import sys

    source = Path(gate.__file__).read_text(encoding="utf-8")
    names = {
        "_PassedTestsGate",
        "pytest_addoption",
        "pytest_configure",
        "_UNREGISTERED_SKIPS",
        "pytest_runtest_logreport",
        "pytest_sessionfinish",
    }
    nodes = []
    for node in ast.parse(source).body:
        name = getattr(node, "name", None)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
        if name in names:
            nodes.append(ast.get_source_segment(source, node))
    (tmp_path / "execution_plugin.py").write_text(
        "import pytest\n" + "\n\n".join(nodes), encoding="utf-8"
    )
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    env = dict(os.environ)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(tmp_path), str(Path(__file__).resolve().parent.parent)]
    )

    def run(body, *args):
        (tmp_path / "test_sample.py").write_text(
            "import pytest\n" + body, encoding="utf-8"
        )
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--noconftest",
                "-c",
                str(tmp_path / "pytest.ini"),
                "-p",
                "execution_plugin",
                str(tmp_path / "test_sample.py"),
                *args,
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    return run


def test_registered_all_skips_require_a_genuine_pass_only_when_enabled(
    run_execution_gate,
):
    from tests.skip_allowlist import REGISTERED_SKIP_REASONS

    reason = next(iter(REGISTERED_SKIP_REASONS))
    body = f"def test_skip():\n    pytest.skip({reason!r})\n"
    assert run_execution_gate(body).returncode == 0
    result = run_execution_gate(body, "--require-passed-tests")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "NO PASSED TESTS" in result.stdout


@pytest.mark.parametrize(
    "body",
    [
        "@pytest.mark.xfail(strict=True)\ndef test_expected():\n    assert False\n",
        "@pytest.mark.xfail(strict=False)\ndef test_unexpected():\n    assert True\n",
    ],
)
def test_expected_failure_or_nonstrict_xpass_is_not_a_genuine_pass(
    run_execution_gate, body
):
    result = run_execution_gate(body, "--require-passed-tests")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "NO PASSED TESTS" in result.stdout


def test_passing_call_with_skip_and_expected_failure_passes(run_execution_gate):
    from tests.skip_allowlist import REGISTERED_SKIP_REASONS

    reason = next(iter(REGISTERED_SKIP_REASONS))
    body = (
        f"def test_skip():\n    pytest.skip({reason!r})\n"
        "@pytest.mark.xfail(strict=True)\ndef test_expected():\n    assert False\n"
        "def test_pass():\n    assert 2 + 2 == 4\n"
    )
    result = run_execution_gate(body, "--require-passed-tests")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("body", "args", "expected"),
    [
        ("def test_fail():\n    assert False\n", [], 1),
        (
            "def test_pass():\n    assert True\n@pytest.mark.xfail(strict=True)\ndef test_xpass():\n    assert True\n",
            [],
            1,
        ),
        ("def test_pass():\n    assert True\n", ["-k", "absent"], 5),
        ("raise ValueError('collection failure')\n", [], 2),
        ("def test_interrupt():\n    raise KeyboardInterrupt\n", [], 2),
    ],
)
def test_execution_gate_preserves_pytest_nonzero_status(
    run_execution_gate, body, args, expected
):
    result = run_execution_gate(body, "--require-passed-tests", *args)
    assert result.returncode == expected, result.stdout + result.stderr


def test_execution_gate_counts_only_passed_calls_and_does_not_share_state():
    from types import SimpleNamespace

    first = gate._PassedTestsGate()
    second = gate._PassedTestsGate()
    first.pytest_runtest_logreport(SimpleNamespace(when="call", passed=True))
    for phase in ("setup", "teardown"):
        second.pytest_runtest_logreport(SimpleNamespace(when=phase, passed=True))
    first_session = SimpleNamespace(exitstatus=0)
    second_session = SimpleNamespace(exitstatus=0)
    first.pytest_sessionfinish(first_session)
    second.pytest_sessionfinish(second_session)
    assert first_session.exitstatus == 0
    assert second_session.exitstatus == 1


@pytest.mark.parametrize("status", [1, 2, 3, 4, 5])
def test_both_skip_gates_preserve_existing_nonzero_status(collected, status):
    from types import SimpleNamespace

    session = SimpleNamespace(exitstatus=status)
    gate._PassedTestsGate().pytest_sessionfinish(session)
    collected.append(("test_bad", "unregistered"))
    gate.pytest_sessionfinish(session, status)
    assert session.exitstatus == status


def test_registered_fixture_skip_does_not_count_setup_as_a_pass(run_execution_gate):
    from tests.skip_allowlist import REGISTERED_SKIP_REASONS

    reason = next(iter(REGISTERED_SKIP_REASONS))
    body = (
        f"@pytest.fixture\ndef missing_index():\n    pytest.skip({reason!r})\n"
        "def test_requires_index(missing_index):\n    assert False\n"
    )
    result = run_execution_gate(body, "--require-passed-tests")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "NO PASSED TESTS" in result.stdout


def test_each_pytest_configuration_registers_a_fresh_gate():
    from types import SimpleNamespace

    plugins = []
    manager = SimpleNamespace(register=lambda plugin, name: plugins.append(plugin))
    config = SimpleNamespace(getoption=lambda name: True, pluginmanager=manager)
    gate.pytest_configure(config)
    plugins[0].pytest_runtest_logreport(SimpleNamespace(when="call", passed=True))
    gate.pytest_configure(config)
    assert len(plugins) == 2 and plugins[0] is not plugins[1]
    session = SimpleNamespace(exitstatus=0)
    plugins[1].pytest_sessionfinish(session)
    assert session.exitstatus == 1
