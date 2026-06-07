---
description: Run a focused security scan — secrets detection, dependency audit, and basic auth pattern checks. Invoke when the user says "security scan", "security review", "security audit", "check for secrets", "vulnerability check", or "scan for credentials". Do NOT use for general code review (use /code-review) or comprehensive OWASP analysis (perform a dedicated manual security review with project-specific context).
disable-model-invocation: true
allowed-tools: Bash Read Grep
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Branch:** !`git branch --show-current`
**Project root:** !`pwd`

## Instructions

You are running a focused security scan. Read `procedure.md` in this skill folder for the full scanning protocol.

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

### Output Defaults

- **Severity gating:** CRITICAL and HIGH shown prominently; MEDIUM and LOW summarized
- **Evidence required:** Every finding must cite `file:line` + quoted code
- **Actionable fixes:** Each finding includes a specific remediation step
