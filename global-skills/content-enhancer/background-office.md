# Background Office conversion

Use `office_background.py` when a task needs unattended DOCX, XLSX, or PPTX
conversion to PDF, or XLSX recalculation. Reading existing files does not require
an Office process. This helper requires a POSIX host, Python 3.10+, and openpyxl
for XLSX validation; it installs nothing.

Resolve the host's supported runtime first. In Codex Desktop, call
`load_workspace_dependencies`, use its Python executable, and inspect its
returned Override binaries directory for an executable `soffice`; set
`OFFICE_ENGINE` to that executable, not to the directory. If absent, check the
returned runtime documentation or stop with an unavailable result.
Other hosts must supply an explicitly selected executable. Do not copy another
machine's absolute paths, replace system `soffice`, or change global PATH. A
system LibreOffice installation and a bundled headless build are different
engines; record which one ran. Engine availability is not proof of conversion
capability or calculation correctness.

With `OFFICE_PYTHON` and `OFFICE_ENGINE` set to those resolved paths and `CE` set
to the installed content-enhancer directory:

```bash
"$OFFICE_PYTHON" "$CE/office_background.py" \
  --engine "$OFFICE_ENGINE" --input /absolute/path/source.xlsx \
  --format xlsx --output-dir /absolute/path/new-recalculation \
  --expect 'Summary!B2=200' --timeout 90

"$OFFICE_PYTHON" "$CE/office_background.py" \
  --engine "$OFFICE_ENGINE" --input /absolute/path/source.docx \
  --format pdf --output-dir /absolute/path/new-render --timeout 90
```

Use the actual source and independent expected cells for the task. The output
directory must be new. Repeat `--expect` for multiple cells; the value is JSON
(quote JSON strings). Expectations use exact equality, so financial models
needing rounding/tolerances must run their own semantic verifier. This helper
does not replace a project's verification manifest or strict regression gate.

The helper copies the source, uses a disposable profile with
`OOXMLRecalcMode=0`, and checks that original bytes remain unchanged. It records
engine version, executable hash, exact commands, durations, return codes,
stdout/stderr and output hashes in `evidence.json`. A wrapper's hash identifies
the wrapper, not every binary it invokes. Timeouts terminate the process group.
Input/profile scratch is removed; converted outputs and evidence remain.

Exit zero / `PASS` establishes nonempty output, PDF signature or XLSX ZIP
integrity, and (for XLSX) saved error-cell absence plus the named expectations.
It does **not** certify complete model correctness, PDF parseability/layout,
OOXML schema validity, or native Word/Excel/PowerPoint compatibility. Open the
saved PDF with a parser, inspect relevant rendered pages, and run the project's
independent content/calculation checks. Test stale caches and deliberately
incorrect formulas/expected values when establishing a calculation path.

On failure, preserve evidence and report the failed stage. Do not retry the same
failing system launcher as a fallback or silently change renderer. Another
supported background renderer is acceptable when its output passes the same
task-specific checks; disclose the choice. Manual export can unblock extraction
if no supported renderer works, but does not satisfy an unattended workflow.
Native application checks are supplementary and only run when authorized.

Legacy `.doc`/`.ppt` conversion remains the separate procedure in source-handling.md; this
helper accepts modern OOXML inputs only. Title 10 §9.4.5 owns saved-artifact
validation; Title 35 owns reader-task and visual communication checks.
