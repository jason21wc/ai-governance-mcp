#!/usr/bin/env python3
"""Run a governance module from this checkout using the caller's interpreter.

Unlike an installed console script or bare ``python -m``, this entry point pins
imports before loading the package. It neither installs dependencies nor changes
cwd or runtime configuration. See docs/local-python.md for the shell contract.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import runpy
import sys


def prepare(module: str) -> dict:
    """Select local source and check extractor imports before any index writes."""
    root = Path(__file__).resolve().parents[1]
    package = root / "src" / "ai_governance_mcp"
    if not (package / "__init__.py").is_file():
        raise RuntimeError(f"Checkout package is missing: {package}")
    sys.path.insert(0, str(package.parent))
    imported = importlib.import_module("ai_governance_mcp")
    source = Path(imported.__file__).resolve()
    if source != (package / "__init__.py").resolve():
        raise RuntimeError(f"Expected source in {package}, imported {source}")

    report = {
        "interpreter": sys.executable,
        "checkout": str(root),
        "package_source": str(source),
        "module": module,
    }
    if module == "ai_governance_mcp.extractor":
        # Real imports catch broken transitive dependencies too. Do not construct
        # a model or import extractor: its module body configures logging.
        for name in ("numpy", "yaml", "pydantic", "pydantic_settings"):
            importlib.import_module(name)
        from rank_bm25 import BM25Okapi  # noqa: F401
        from sentence_transformers import SentenceTransformer  # noqa: F401
        from ai_governance_mcp.config import load_settings

        settings = load_settings()
        report["extractor_dependencies"] = "importable (model not loaded)"
        report["paths"] = {
            name: str(getattr(settings, name))
            for name in (
                "documents_path",
                "index_path",
                "reference_library_path",
                "private_reference_library_path",
                "logs_path",
            )
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report extractor source, interpreter, imports and paths without building",
    )
    parser.add_argument("module", help="ai_governance_mcp module to execute")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="module arguments")
    options = parser.parse_args()
    if not options.module.startswith("ai_governance_mcp.") or not all(
        part.isidentifier() for part in options.module.split(".")
    ):
        parser.error("module must be a dotted name under ai_governance_mcp")
    if options.check and (
        options.module != "ai_governance_mcp.extractor" or options.args
    ):
        parser.error(
            "--check requires ai_governance_mcp.extractor without module arguments"
        )
    try:
        report = prepare(options.module)
    except Exception as exc:
        print(
            f"Local invocation preflight failed with {sys.executable}: "
            f"{type(exc).__name__}: {exc}\n"
            "Use an interpreter with this project's dependencies installed. "
            "See docs/local-python.md; no installation was changed.",
            file=sys.stderr,
        )
        return 2
    if options.check:
        print(json.dumps(report, indent=2))
        return 0
    print(
        f"Local invocation: {report['interpreter']} | {report['package_source']}",
        file=sys.stderr,
    )
    sys.argv = [options.module, *options.args]
    runpy.run_module(options.module, run_name="__main__", alter_sys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
