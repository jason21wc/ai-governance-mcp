"""Behavior tests for the explicitly selected background Office runner.

These use disposable fake engines, never LibreOffice or GUI applications.
"""

import json
import io
from contextlib import redirect_stdout, suppress
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import openpyxl

import importlib.util

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "global-skills/content-enhancer/office_background.py"
)
spec = importlib.util.spec_from_file_location("office_background", SCRIPT)
office = importlib.util.module_from_spec(spec)
spec.loader.exec_module(office)


class BackgroundOfficeTests(unittest.TestCase):
    def test_cli_saved_value_and_invalid_expectations(self):
        engine = self.engine(
            "import pathlib, shutil, sys\n"
            'if "--version" in sys.argv:\n'
            '    print("fake 1.0")\n'
            "    raise SystemExit(0)\n"
            'destination = pathlib.Path(sys.argv[sys.argv.index("--outdir") + 1])\n'
            "source = pathlib.Path(sys.argv[-1])\n"
            "shutil.copyfile(source, destination / source.name)\n"
        )
        for expectation, code in (
            ("Summary!B2=999", 0),
            ("Summary!B2=not-json", 1),
            ("B2=999", 1),
        ):
            with self.subTest(expectation=expectation):
                args = [
                    str(SCRIPT),
                    "--input",
                    str(self.source),
                    "--engine",
                    str(engine),
                    "--output-dir",
                    str(self.destination),
                    "--format",
                    "xlsx",
                    "--expect",
                    expectation,
                ]
                stream = io.StringIO()
                with patch.object(sys, "argv", args), redirect_stdout(stream):
                    self.assertEqual(office.main(), code)
                self.assertEqual(
                    json.loads(stream.getvalue())["status"],
                    "PASS" if code == 0 else "FAIL",
                )

    def test_saved_boolean_is_not_a_numeric_expectation(self):
        for actual, expected, passes in (
            (True, 1, False),
            (0, False, False),
            (True, True, True),
            (1, 1.0, True),
        ):
            with self.subTest(actual=actual, expected=expected):
                workbook = openpyxl.Workbook()
                workbook.active.title = "Summary"
                workbook.active["B2"] = actual
                workbook.save(self.source)
                workbook.close()
                self.assertEqual(
                    office.check_xlsx(self.source, [("Summary!B2", expected)])["pass"],
                    passes,
                )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="office-runner-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "example.xlsx"
        workbook = openpyxl.Workbook()
        workbook.active.title = "Summary"
        workbook.active["B2"] = 999
        workbook.save(self.source)
        workbook.close()
        self.original = self.source.read_bytes()
        self.destination = self.root / "result"

    def engine(self, body):
        path = self.root / "fake-soffice"
        path.write_text("#!" + sys.executable + "\n" + body)
        path.chmod(0o700)
        return path

    def run_conversion(self, engine, timeout=5, expectations=()):
        return office.convert(
            self.source, engine, self.destination, "xlsx", timeout, expectations
        )

    def assert_failed_evidence(self, result):
        self.assertEqual(result["status"], "FAIL")
        saved = json.loads((self.destination / "evidence.json").read_text())
        self.assertEqual(saved["status"], "FAIL")
        self.assertTrue(saved["source_unchanged"])
        self.assertEqual(self.source.read_bytes(), self.original)
        return saved

    def test_conversion_existing_destination_preserves_contents(self):
        engine = self.engine("raise SystemExit(99)\n")
        self.destination.mkdir()
        sentinel = self.destination / "preserve.txt"
        sentinel.write_text("existing user content")
        with self.assertRaises(FileExistsError):
            self.run_conversion(engine)
        self.assertEqual(sentinel.read_text(), "existing user content")
        self.assertEqual(list(self.destination.iterdir()), [sentinel])
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_conversion_missing_or_nonexecutable_engine_rejects_before_output(self):
        missing = self.root / "missing-engine"
        nonexecutable = self.root / "nonexecutable-engine"
        nonexecutable.write_text("not executable")
        nonexecutable.chmod(0o600)
        for engine in (missing, nonexecutable):
            with self.subTest(engine=engine.name):
                with self.assertRaisesRegex(ValueError, "executable file"):
                    self.run_conversion(engine)
                self.assertFalse(self.destination.exists())

    def test_conversion_nonfinite_or_out_of_range_timeout_rejects(self):
        engine = self.engine("raise SystemExit(99)\n")
        for timeout in (float("nan"), float("inf"), float("-inf"), 0, -1, 900.01):
            with self.subTest(timeout=timeout):
                with self.assertRaisesRegex(ValueError, "timeout must be finite"):
                    self.run_conversion(engine, timeout=timeout)
                self.assertFalse(self.destination.exists())

    def test_conversion_version_failure_never_starts_conversion(self):
        marker = self.root / "conversion-started"
        engine = self.engine(
            "import pathlib, sys\n"
            'if "--version" in sys.argv:\n'
            '    print("version unavailable", file=sys.stderr)\n'
            "    raise SystemExit(17)\n"
            f'pathlib.Path({str(marker)!r}).write_text("started")\n'
        )
        saved = self.assert_failed_evidence(self.run_conversion(engine))
        self.assertEqual(saved["version_probe"]["exit_code"], 17)
        self.assertIn("version probe failed", saved["error"])
        self.assertFalse(marker.exists())
        self.assertNotIn("conversion", saved)

    def test_conversion_zero_exit_without_artifact_rejects(self):
        engine = self.engine('print("fake engine success")\n')
        saved = self.assert_failed_evidence(self.run_conversion(engine))
        self.assertEqual(saved["conversion"]["exit_code"], 0)
        self.assertIn("no nonempty expected output", saved["error"])
        self.assertFalse((self.destination / self.source.name).exists())

    def test_conversion_incorrect_saved_value_rejects_successful_engine_output(self):
        engine = self.engine(
            "import pathlib, shutil, sys\n"
            'if "--version" in sys.argv:\n'
            '    print("fake 1.0")\n'
            "    raise SystemExit(0)\n"
            'destination = pathlib.Path(sys.argv[sys.argv.index("--outdir") + 1])\n'
            "source = pathlib.Path(sys.argv[-1])\n"
            "shutil.copyfile(source, destination / source.name)\n"
        )
        saved = self.assert_failed_evidence(
            self.run_conversion(engine, expectations=[("Summary!B2", 200)])
        )
        self.assertEqual(saved["conversion"]["exit_code"], 0)
        self.assertEqual(
            saved["calculation"]["saved_cell_checks"],
            [{"cell": "Summary!B2", "expected": 200, "actual": 999, "pass": False}],
        )
        self.assertIn("failed value/error checks", saved["error"])

    def test_conversion_success_retains_saved_value_and_identity(self):
        engine = self.engine(
            "import pathlib, shutil, sys\n"
            'if "--version" in sys.argv:\n'
            '    print("fake 1.0")\n'
            "    raise SystemExit(0)\n"
            'destination = pathlib.Path(sys.argv[sys.argv.index("--outdir") + 1])\n'
            "source = pathlib.Path(sys.argv[-1])\n"
            "shutil.copyfile(source, destination / source.name)\n"
        )
        result = self.run_conversion(engine, expectations=[("Summary!B2", 999)])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(self.destination.stat().st_mode & 0o077, 0)
        self.assertTrue(result["source_unchanged"])
        self.assertEqual(result["output"]["sha256"], office.sha(self.source))
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(list(self.destination.glob(".work-*")))

    def test_pdf_signature_acceptance_and_rejection(self):
        for content, status in ((b"%PDF-fake", "PASS"), (b"not a pdf", "FAIL")):
            with self.subTest(status=status):
                self.destination = self.root / status
                engine = self.engine(
                    "import pathlib, sys\n"
                    'if "--version" in sys.argv:\n'
                    "    raise SystemExit(0)\n"
                    'destination = pathlib.Path(sys.argv[sys.argv.index("--outdir") + 1])\n'
                    "source = pathlib.Path(sys.argv[-1])\n"
                    f"(destination / (source.stem + '.pdf')).write_bytes({content!r})\n"
                )
                result = office.convert(
                    self.source, engine, self.destination, "pdf", 5, []
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(self.source.read_bytes(), self.original)
                if status == "PASS":
                    self.assertIn("require separate checks", result["scope"])
                else:
                    self.assertIn("PDF signature", result["error"])

    def test_conversion_initial_source_or_engine_read_error_preserves_failure_evidence(
        self,
    ):
        engine = self.engine("raise SystemExit(99)\n")
        actual_sha = office.sha
        for unreadable in (self.source, engine):
            with self.subTest(unreadable=unreadable.name):
                self.destination = self.root / ("failed-read-" + unreadable.name)

                def fail_selected_read(path):
                    if Path(path) == unreadable:
                        raise OSError("injected initial read failure")
                    return actual_sha(path)

                with patch.object(office, "sha", side_effect=fail_selected_read):
                    result = self.run_conversion(engine)
                saved = json.loads((self.destination / "evidence.json").read_text())
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(saved["status"], "FAIL")
                self.assertIn("injected initial read failure", saved["error"])
                self.assertNotIn("version_probe", saved)
                self.assertEqual(self.source.read_bytes(), self.original)

    def test_conversion_final_source_read_error_preserves_failure_evidence(self):
        engine = self.engine(
            "import pathlib, shutil, sys\n"
            'if "--version" in sys.argv:\n'
            "    raise SystemExit(0)\n"
            'destination = pathlib.Path(sys.argv[sys.argv.index("--outdir") + 1])\n'
            "source = pathlib.Path(sys.argv[-1])\n"
            "shutil.copyfile(source, destination / source.name)\n"
        )
        actual_sha = office.sha
        source_unreadable = False

        def fail_source_after_output_read(path):
            nonlocal source_unreadable
            if Path(path) == self.source and source_unreadable:
                raise OSError("injected final read failure")
            value = actual_sha(path)
            if Path(path) == self.destination / self.source.name:
                source_unreadable = True
            return value

        with patch.object(office, "sha", side_effect=fail_source_after_output_read):
            result = self.run_conversion(engine, expectations=[("Summary!B2", 999)])
        saved = json.loads((self.destination / "evidence.json").read_text())
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(saved["status"], "FAIL")
        self.assertTrue(saved["calculation"]["pass"])
        self.assertIsNone(saved["source_unchanged"])
        self.assertIn("injected final read failure", saved["source_recheck_error"])
        self.assertEqual(self.source.read_bytes(), self.original)

    def bounded_with_ready_child(self, engine, heartbeat):
        """Separate fixture bootstrap from the real timeout/termination exercise."""
        popen = office.subprocess.Popen
        ready_at = None

        def start_ready_process(*args, **kwargs):
            nonlocal ready_at
            process = popen(*args, **kwargs)

            def cleanup_process_group():
                # Register from the actual PID, even if bootstrap never writes a file.
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                with suppress(ProcessLookupError):
                    process.kill()
                process.communicate(timeout=2)

            self.addCleanup(cleanup_process_group)
            deadline = time.monotonic() + 10
            while not (heartbeat.exists() and heartbeat.stat().st_size):
                self.assertIsNone(
                    process.poll(), "fake engine exited before child readiness"
                )
                self.assertLess(
                    time.monotonic(), deadline, "child bootstrap did not become ready"
                )
                time.sleep(0.01)
            ready_at = time.monotonic()
            return process

        # Launch with bounded()'s actual arguments; keep communicate and signals real.
        with patch.object(office.subprocess, "Popen", side_effect=start_ready_process):
            result = office.bounded([engine], timeout=0.5)
        self.assertLess(time.monotonic() - ready_at, 5)
        return result

    @unittest.skipUnless(os.name == "posix", "process-group termination requires POSIX")
    def test_bounded_timeout_terminates_parent_and_sigterm_resistant_child(self):
        heartbeat = self.root / "heartbeat"
        engine = self.engine(
            "import os, pathlib, signal, time\n"
            "time.sleep(0.75)\n"  # Bootstrap deliberately exceeds execution timeout.
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            "child = os.fork()\n"
            "if child == 0:\n"
            "    while True:\n"
            f'        with open({str(heartbeat)!r}, "a") as stream:\n'
            '            stream.write("alive\\n")\n'
            "        time.sleep(0.02)\n"
            "while True:\n"
            "    time.sleep(1)\n"
        )

        result = self.bounded_with_ready_child(engine, heartbeat)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["exit_code"], -signal.SIGKILL)
        self.assertTrue(
            heartbeat.exists(), "child must have run before testing its termination"
        )
        final_heartbeat = heartbeat.read_bytes()
        self.assertTrue(final_heartbeat)
        time.sleep(0.15)
        self.assertEqual(
            heartbeat.read_bytes(),
            final_heartbeat,
            "the child must stop writing after timeout returns",
        )

    @unittest.skipUnless(os.name == "posix", "process-group termination requires POSIX")
    def test_bounded_timeout_kills_child_even_after_parent_exits_and_pipes_close(self):
        heartbeat = self.root / "detached-pipes-heartbeat"
        engine = self.engine(
            "import os, pathlib, signal, time\n"
            "time.sleep(0.75)\n"  # Bootstrap deliberately exceeds execution timeout.
            "child = os.fork()\n"
            "if child == 0:\n"
            "    signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            '    with open(os.devnull, "wb") as null:\n'
            "        os.dup2(null.fileno(), 1)\n"
            "        os.dup2(null.fileno(), 2)\n"
            "    while True:\n"
            f'        with open({str(heartbeat)!r}, "a") as stream:\n'
            '            stream.write("alive\\n")\n'
            "        time.sleep(0.02)\n"
            "while True:\n"
            "    time.sleep(1)\n"
        )

        result = self.bounded_with_ready_child(engine, heartbeat)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["exit_code"], -signal.SIGTERM)
        self.assertTrue(
            heartbeat.exists(), "child must have run before testing its termination"
        )
        final_heartbeat = heartbeat.read_bytes()
        time.sleep(0.15)
        self.assertEqual(
            heartbeat.read_bytes(),
            final_heartbeat,
            "closed capture pipes do not prove that the child process stopped",
        )


if __name__ == "__main__":
    unittest.main()
