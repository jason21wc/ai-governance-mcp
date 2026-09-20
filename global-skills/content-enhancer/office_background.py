#!/usr/bin/env python3
"""Run an explicitly selected headless Office engine; retain conversion evidence."""

from __future__ import annotations

import argparse
from contextlib import suppress
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import zipfile

PROFILE = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry">
<item oor:path="/org.openoffice.Office.Calc/Formula/Load">
<prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop>
</item></oor:items>"""


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bounded(command, timeout):
    start = time.monotonic()
    record = {"command": list(map(str, command)), "timeout_seconds": timeout}
    process = subprocess.Popen(
        record["command"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        record["timed_out"] = False
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate(timeout=2)
        finally:
            # A child may close its pipes and survive after the launcher exits.
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        record["timed_out"] = True
    record.update(
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        seconds=round(time.monotonic() - start, 3),
    )
    return record


def check_xlsx(path, expectations):
    import openpyxl  # Read saved values only; this does not calculate formulas.

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        errors = []
        for sheet in wb:
            for row in sheet:
                errors.extend(
                    f"{sheet.title}!{cell.coordinate}: {cell.value}"
                    for cell in row
                    if cell.data_type == "e"
                )
        checks = []
        for address, expected in expectations:
            sheet, coordinate = address.rsplit("!", 1)
            actual = wb[sheet][coordinate].value
            checks.append(
                {
                    "cell": address,
                    "expected": expected,
                    "actual": actual,
                    "pass": actual == expected
                    and isinstance(actual, bool) == isinstance(expected, bool),
                }
            )
        return {
            "saved_cell_checks": checks,
            "error_cells": errors,
            "pass": not errors and all(c["pass"] for c in checks),
            "coverage": "Named expected values and saved error cells only; not complete model validation.",
        }
    finally:
        wb.close()


def convert(source, engine, output, kind, timeout, expectations):
    source, engine, output = (
        Path(source).resolve(),
        Path(engine).resolve(),
        Path(output).absolute(),
    )
    if not source.is_file() or source.suffix.lower() not in {".docx", ".xlsx", ".pptx"}:
        raise ValueError("input must be an existing DOCX, XLSX, or PPTX")
    if kind == "xlsx" and source.suffix.lower() != ".xlsx":
        raise ValueError("recalculation accepts XLSX input only")
    if not engine.is_file() or not os.access(engine, os.X_OK):
        raise ValueError("explicit engine must be an executable file")
    if not math.isfinite(timeout) or not 0 < timeout <= 900:
        raise ValueError("timeout must be finite and in (0, 900] seconds")
    if expectations and kind != "xlsx":
        raise ValueError("saved-cell expectations require XLSX output")
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    evidence = {
        "schema": "office-background/v1",
        "status": "FAIL",
        "source": str(source),
        "source_sha256": None,
        "engine": str(engine),
        "engine_sha256": None,
        "profile": {"isolated": True, "OOXMLRecalcMode": 0},
        "gui_used": False,
        "format": kind,
    }
    try:
        evidence["source_sha256"] = sha(source)
        evidence["engine_sha256"] = sha(engine)
        version = bounded([engine, "--version"], min(timeout, 30))
        evidence["version_probe"] = version
        if version["exit_code"] != 0 or version["timed_out"]:
            raise RuntimeError("engine version probe failed; no fallback attempted")
        with tempfile.TemporaryDirectory(prefix=".work-", dir=output) as tmp:
            work = Path(tmp)
            profile = work / "profile"
            (profile / "user").mkdir(parents=True)
            (profile / "user/registrymodifications.xcu").write_text(PROFILE)
            stable = work / source.name
            shutil.copyfile(source, stable)
            if sha(stable) != evidence["source_sha256"]:
                raise RuntimeError("source changed before conversion")
            fmt = "xlsx:Calc MS Excel 2007 XML" if kind == "xlsx" else "pdf"
            run = bounded(
                [
                    engine,
                    "-env:UserInstallation=" + profile.as_uri(),
                    "--headless",
                    "--convert-to",
                    fmt,
                    "--outdir",
                    output,
                    stable,
                ],
                timeout,
            )
            evidence["conversion"] = run
            if run["exit_code"] != 0 or run["timed_out"]:
                raise RuntimeError("conversion failed; no fallback attempted")
            if (
                sha(stable) != evidence["source_sha256"]
                or sha(source) != evidence["source_sha256"]
            ):
                raise RuntimeError("source bytes changed during conversion")
        result = output / (source.stem + "." + kind)
        if not result.is_file() or not result.stat().st_size:
            raise RuntimeError("engine returned no nonempty expected output")
        evidence["output"] = {
            "path": str(result),
            "sha256": sha(result),
            "bytes": result.stat().st_size,
        }
        if kind == "xlsx":
            with zipfile.ZipFile(result) as z:
                if z.testzip() is not None:
                    raise RuntimeError("output ZIP integrity check failed")
            evidence["calculation"] = check_xlsx(result, expectations)
            if not evidence["calculation"]["pass"]:
                raise RuntimeError("saved workbook failed value/error checks")
        else:
            with result.open("rb") as f:
                if f.read(5) != b"%PDF-":
                    raise RuntimeError("output lacks PDF signature")
        evidence["status"] = "PASS"
        evidence["scope"] = (
            "Conversion and named saved-cell checks only. "
            "PDF layout, native compatibility, and full model correctness require separate checks."
        )
    except Exception as exc:
        evidence["error"] = str(exc)
    finally:
        try:
            evidence["source_unchanged"] = (
                evidence["source_sha256"] is not None
                and source.is_file()
                and sha(source) == evidence["source_sha256"]
            )
        except OSError as exc:
            evidence["source_unchanged"] = None
            evidence["source_recheck_error"] = str(exc)
        if not evidence["source_unchanged"]:
            evidence["status"] = "FAIL"
            evidence.setdefault(
                "error", "source identity could not be preserved or verified"
            )
        (output / "evidence.json").write_text(
            json.dumps(evidence, indent=2, default=str) + "\n"
        )
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--engine",
        required=True,
        help="Absolute path returned by the runtime loader; no PATH fallback",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="New directory; existing destinations are refused",
    )
    parser.add_argument("--format", choices=["pdf", "xlsx"], required=True)
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument(
        "--expect", action="append", default=[], metavar="SHEET!CELL=JSON_VALUE"
    )
    args = parser.parse_args()
    try:
        expectations = []
        for text in args.expect:
            address, value = text.split("=", 1)
            if "!" not in address:
                raise ValueError("expectation must identify SHEET!CELL")
            expectations.append((address, json.loads(value)))
        result = convert(
            args.input,
            args.engine,
            args.output_dir,
            args.format,
            args.timeout,
            expectations,
        )
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 1
    print(
        json.dumps(
            {
                "status": result["status"],
                "evidence": str(Path(args.output_dir).absolute() / "evidence.json"),
                "output": result.get("output"),
                "error": result.get("error"),
            }
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
