"""CVE-2026-68770: local model modules must not bypass explicit distrust.

Exercise the installed dependency, not a mocked constructor or a version string.
The positive control only writes a marker inside pytest's temporary directory.
No model weights, network access or shared model-cache writes are needed.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("route", ["direct", "extractor", "trusted_control"])
def test_local_custom_module_requires_explicit_trust(tmp_path, route):
    model = tmp_path / "model"
    model.mkdir()
    marker = tmp_path / "executed"
    (model / "modules.json").write_text(
        json.dumps([{"idx": 0, "name": "0", "path": "", "type": "custom_probe.Probe"}])
    )
    (model / "custom_probe.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "raise RuntimeError('TRUST_FIXTURE_EXECUTED')\n"
    )
    env = {
        **os.environ,
        "HF_HOME": str(tmp_path / "hf"),
        "HF_HUB_CACHE": str(tmp_path / "hf" / "hub"),
        "HF_MODULES_CACHE": str(tmp_path / "hf" / "modules"),
        "SENTENCE_TRANSFORMERS_HOME": str(tmp_path / "hf" / "hub"),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, sys\n"
            "from sentence_transformers import SentenceTransformer\n"
            "from ai_governance_mcp.extractor import _load_local_embedder\n"
            "try:\n"
            "    if sys.argv[2] == 'extractor':\n"
            "        _load_local_embedder(sys.argv[1])\n"
            "    else:\n"
            "        SentenceTransformer(sys.argv[1], local_files_only=True,\n"
            "            trust_remote_code=sys.argv[2] == 'trusted_control')\n"
            "except Exception as exc:\n"
            "    print(json.dumps({'type': type(exc).__name__, 'message': str(exc)}))\n"
            "else:\n"
            "    raise AssertionError('custom fixture unexpectedly loaded')\n",
            str(model),
            route,
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=True,
    )
    failure = json.loads(result.stdout.strip().splitlines()[-1])
    if route == "trusted_control":
        assert failure == {"type": "RuntimeError", "message": "TRUST_FIXTURE_EXECUTED"}
        assert marker.read_text() == "executed"
    else:
        assert failure["type"] == "ValueError", failure
        assert "trust_remote_code=True" in failure["message"]
        assert not marker.exists(), "untrusted model code executed before refusal"
