---
description: Run a focused security scan — secrets detection, dependency audit, and basic auth pattern checks. Invoke when the user says "security scan", "security review", "security audit", "check for secrets", "vulnerability check", or "scan for credentials". Do NOT use for general code review (use /code-review) or comprehensive OWASP analysis (perform a dedicated manual security review with project-specific context).
disable-model-invocation: false  # read-only (Bash Read Grep); model-invocable per §9.5.3 per-skill flip, Compliance Review #14 (2026-07-01)
allowed-tools: Bash Read Grep
---

## Runtime Context

After the skill loads, establish the project root, branch, dependency manifests,
and relevant authentication/configuration surfaces with ordinary read-only calls.

## Instructions

You are running a focused security scan. Collect the Runtime Context above, then read `procedure.md` in this skill folder for the full scanning protocol.

### Scope

This skill covers the most mechanical, portable security concerns:
1. **Secrets detection** — API keys, tokens, passwords, private keys in code and config
2. **Dependency audit** — known vulnerabilities in project dependencies
3. **Basic auth patterns** — hardcoded credentials, default passwords, missing auth

For deeper analysis (full OWASP systematic review, attack surface mapping, data flow tracing), perform a comprehensive manual security review with project-specific context.

### Execution Protocol

1. **Read `procedure.md`** for the full scanning procedure.
2. **Execute all three scan phases** in order.
3. **Present findings** with severity gating — CRITICAL and HIGH findings first.
4. **Every finding needs evidence** — file:line + quoted code, or it's dropped.

### Portability Note

Slash-command references (e.g. `/code-review`) name companion skills. On hosts where a named skill isn't installed, perform the equivalent manually instead of invoking it.

### Output Defaults

- **Severity gating:** CRITICAL and HIGH shown prominently; MEDIUM and LOW summarized
- **Evidence required:** Every finding must cite `file:line` + quoted code
- **Actionable fixes:** Each finding includes a specific remediation step
