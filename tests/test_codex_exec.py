"""Hermetic tests for the shared keyless codex-exec helper (ai_governance_mcp.codex_exec).

No real Codex: subprocess.run / shutil.which are monkeypatched. Covers the invocation
contract (read-only sandbox, stdin, -o capture, -m flag) and the minimal-env secret
hardening — the fix the Codex peer found on codex_review, propagated here by the
session-238 shared-module extraction (so the plain-language judge gets it too).
"""

from pathlib import Path

from ai_governance_mcp import codex_exec as ce


def _fake_run_writing(output):
    """A subprocess.run stand-in that writes `output` to the -o path and records the call."""
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        Path(cmd[cmd.index("-o") + 1]).write_text(output, encoding="utf-8")

        class _R:
            returncode = 0

        return _R()

    return fake_run, captured


def test_run_codex_exec_reads_output_and_uses_read_only_stdin(monkeypatch):
    fake_run, captured = _fake_run_writing('{"verdict":"dense"}')
    monkeypatch.setattr(ce.subprocess, "run", fake_run)
    got = ce.run_codex_exec("my prompt", model=None)
    assert got == '{"verdict":"dense"}'
    assert captured["kwargs"]["input"] == "my prompt"  # prompt on stdin (closes on EOF)
    assert "--sandbox" in captured["cmd"] and "read-only" in captured["cmd"]
    assert "-m" not in captured["cmd"]  # no model -> no -m flag


def test_run_codex_exec_passes_model_flag(monkeypatch):
    fake_run, captured = _fake_run_writing("{}")
    monkeypatch.setattr(ce.subprocess, "run", fake_run)
    ce.run_codex_exec("p", model="gpt-x")
    cmd = captured["cmd"]
    assert cmd[cmd.index("-m") + 1] == "gpt-x"


def test_minimal_env_drops_secrets_keeps_infra_and_codex(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("CODEX_HOME", "/home/u/.codex")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-leak")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "should-not-leak")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_should_not_leak")
    # A secret-bearing CODEX_* var must NOT ride the namespace passthrough.
    monkeypatch.setenv("CODEX_AUTH_TOKEN", "codex-secret-should-not-leak")
    env = ce.minimal_env()
    assert env["PATH"] == "/usr/bin"
    assert env["CODEX_HOME"] == "/home/u/.codex"  # non-secret CODEX_* passes through
    assert "OPENAI_API_KEY" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "GITHUB_TOKEN" not in env
    assert "CODEX_AUTH_TOKEN" not in env  # secret-looking CODEX_* is filtered


def test_minimal_env_merges_extra(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    env = ce.minimal_env({"CODEX_REVIEW_ACTIVE": "1"})
    assert env["CODEX_REVIEW_ACTIVE"] == "1"
    assert env["PATH"] == "/usr/bin"


def test_run_codex_exec_extra_env_reaches_child_without_secrets(monkeypatch):
    fake_run, captured = _fake_run_writing("[]")
    monkeypatch.setattr(ce.subprocess, "run", fake_run)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-leak")
    ce.run_codex_exec("p", extra_env={"CODEX_REVIEW_ACTIVE": "1"})
    child_env = captured["kwargs"]["env"]
    assert child_env["CODEX_REVIEW_ACTIVE"] == "1"
    assert "OPENAI_API_KEY" not in child_env  # minimal-env hardening applied


def test_codex_available(monkeypatch):
    monkeypatch.setattr(ce.shutil, "which", lambda name: "/opt/homebrew/bin/codex")
    assert ce.codex_available() is True
    monkeypatch.setattr(ce.shutil, "which", lambda name: None)
    assert ce.codex_available() is False
