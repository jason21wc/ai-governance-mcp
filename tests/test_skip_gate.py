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
