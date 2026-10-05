# Python commands from a checkout

Use the checkout's launcher for shell commands in a primary clone or linked
worktree. A bare `python -m ai_governance_mcp.extractor` can import another
checkout through a shared editable installation. Pytest's source routing does
not apply to shell commands.

Choose the interpreter explicitly, then check it before rebuilding:

```bash
# Set this to an interpreter containing the dependencies in pyproject.toml.
GOV_PYTHON=/absolute/path/to/python
"$GOV_PYTHON" scripts/run_local.py --check ai_governance_mcp.extractor
"$GOV_PYTHON" scripts/run_local.py ai_governance_mcp.extractor
```

Run these commands from the intended checkout. The launcher uses its own
`src/` before installed packages, reports the interpreter and package source,
and checks NumPy, YAML, Pydantic, pydantic-settings, rank-bm25 and SentenceTransformer
imports before starting extraction. A failed preflight exits 2 without starting
the extractor. The check does not load a model, download weights, rebuild an
index, or prove model-cache availability or dependency-version compatibility.

The caller owns interpreter selection. If dependencies are missing, choose an
existing suitable interpreter or provision a dedicated environment using this
checkout's `pyproject.toml`. Do not run `pip install -e` against a shared
environment to change which checkout it imports: that also changes other
sessions. The launcher does not install anything or switch interpreters.

The declared Sentence Transformers dependency is 6.1.0. Version 6 enforces
`trust_remote_code=False` for custom modules in local model directories too
(CVE-2026-68770); the 5.6 release only warned about this behavior. Updating the
checkout does not upgrade an already installed interpreter or running MCP host.
Install this checkout's declared dependencies into the selected environment and
verify model loading before switching a shared host to it. Keep explicit distrust
and safetensors enabled; do not enable custom code to make a rejected model load.
The launcher preflight checks imports, not installed-version compliance.

## Preserve the intended data paths

Source selection and data selection are separate. The launcher leaves cwd,
environment variables and `.env` loading unchanged. Explicit
`AI_GOVERNANCE_DOCUMENTS_PATH`, `AI_GOVERNANCE_INDEX_PATH`,
`AI_GOVERNANCE_REFERENCE_LIBRARY_PATH`,
`AI_GOVERNANCE_PRIVATE_REFERENCE_LIBRARY_PATH`, `AI_GOVERNANCE_LOGS_PATH` and
`AI_GOVERNANCE_USER_DATA_ROOT` retain their normal meaning. Relative paths remain
relative to the caller's cwd. The check reports resolved settings; it accepts no
extractor arguments, so a positional documents-path override must be reviewed
separately when running the build.

A shell does not inherit the MCP host's environment. Supply the intended index
and reference-library paths before checking or rebuilding. Inspect your MCP
host configuration for those settings. Maintainer checkouts that include
`scripts/resolve_reference_library.py` can also list configured library candidates
with `"$GOV_PYTHON" scripts/resolve_reference_library.py`; its multiple results are
scan candidates, not permission to select the first one silently. Preserve
private-library configuration too. For verification,
choose an isolated index destination instead of overwriting a running server's
index. Existing extractor shrink and content-security guards still apply.

Other modules use the same launcher, with arguments forwarded unchanged:

```bash
"$GOV_PYTHON" scripts/run_local.py ai_governance_mcp.server --test "a query"
```

Only the extractor has the additional dependency preflight and `--check` mode.
Use an absolute path to the intended checkout's launcher when invoking it from
elsewhere; it does not change cwd. A symlink to another checkout's launcher
selects that other checkout. This is a local development entry point, not a
replacement for installed MCP host configuration. It affects this process's
imports; independently launched child interpreters still need their own source
selection. Arbitrary bare `python -c` and `python -m` retain Python's normal
import behavior.
