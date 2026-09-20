"""Tests for portable module-invocation helpers (``_exec``).

These guard the invariant behind the Claude-Desktop launch fix: our modules
must be invoked through an ABSOLUTE interpreter path, never a bare name that a
GUI host's minimal PATH cannot resolve.
"""

import os
import sys

from ai_governance_mcp._exec import python_module_argv, resolve_python


class TestResolvePython:
    def test_default_is_current_interpreter(self):
        assert resolve_python() == sys.executable
        assert resolve_python(None) == sys.executable

    def test_default_is_nonempty_and_absolute(self):
        # A degenerate/embedded interpreter (empty or relative) must fail here —
        # the whole fix depends on the result being launchable without PATH.
        result = resolve_python()
        assert result
        assert os.path.isabs(result)

    def test_explicit_path_passthrough(self):
        assert resolve_python("/usr/local/bin/python3") == "/usr/local/bin/python3"


class TestPythonModuleArgv:
    def test_builds_argv_with_explicit_python(self):
        assert python_module_argv("pkg.mod", "/x/py") == ["/x/py", "-m", "pkg.mod"]

    def test_uses_resolved_default(self):
        assert python_module_argv("pkg.mod") == [sys.executable, "-m", "pkg.mod"]
