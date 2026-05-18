---
id: ref-multi-agent-rtk-hook-compliance-patterns
title: "RTK Hook-Based Compliance Patterns — Enforcement Architecture Evidence"
domain: multi-agent
tags: ["hooks", "enforcement", "deterministic-compliance", "http-hooks", "gap-analysis-sensor", "tiered-enforcement", "token-compression"]
status: current
entry_type: reference
summary: "RTK brief gap analysis: HTTP hooks as remote governance endpoints + rtk-discover missed-coverage sensor. Validates deterministic (~100%) vs probabilistic (~70-85%) compliance gap."
created: 2026-05-18
last_verified: 2026-05-18
maturity: seedling
decay_class: framework
source: "1rtk-reference-brief.md prepared for ai-governance-mcp review, May 2026"
related: [ref-multi-agent-harness-engineering-synthesis]
external_url: "https://github.com/rtk-ai/rtk"
external_author: "Szymkowiak, Bruniaux, Eppling (RTK core team)"
accessed_date: 2026-05-10
---

## Context

Use when designing enforcement layers, evaluating hook handler types, or assessing platform-tiered compliance strategies. HTTP hook pattern relevant to enforcement proxy implementation (EXECUTION-FRAMEWORK §8). Gap-analysis sensor pattern relevant to PostToolUse monitoring. Quantitative compliance data provides independent evidence for deterministic-over-probabilistic design in title-20 §4.6.

## Artifact

### Two Genuinely New Items

**1. HTTP Hooks as Remote Governance Evaluation Endpoints**

Claude Code supports four hook handler types: command (shell scripts), HTTP (POST to URL), prompt (Claude model yes/no), and agent (subagent with tool access). The HTTP handler POSTs the PreToolUse event JSON to a configured URL and parses the allow/deny/ask response. This means governance evaluation can run on a remote server — a single endpoint serving multiple developers/machines rather than local shell scripts per installation.

The JSON contract:
- Input: `{ "tool_name": "Bash", "tool_input": { "command": "..." }, "session_id": "...", "cwd": "..." }`
- Output: `{ "permissionDecision": "allow|deny|ask", "permissionDecisionReason": "...", "updatedInput": {...}, "additionalContext": "..." }`
- Exit codes: 0 = proceed (parse JSON), 2 = block (stderr fed to model)

This is a concrete implementation path for the enforcement proxy documented in EXECUTION-FRAMEWORK §8 — currently described architecturally but not specified at protocol level.

**2. `rtk discover` — Missed-Coverage Sensor Pattern**

RTK includes a gap-analysis command that identifies shell commands which ran without compression and could have been compressed. The pattern: a PostToolUse sensor that audits whether a beneficial intervention was available but not applied. Analogous governance application: a sensor that flags actions where governance could have provided guidance but wasn't consulted — "missed opportunity" detection rather than "violation" detection. The existing Guide/Sensor taxonomy (ref-multi-agent-harness-engineering-synthesis) classifies enforcement by type but doesn't include this "coverage gap" sensor category.

### Validation Evidence (No Framework Changes Needed)

**Deterministic vs probabilistic compliance gap — quantified:**
RTK adoption data: hook-based interception achieves ~100% command adoption across all conversations and subagents; prompt/instruction-based injection (CLAUDE.md) achieves ~70-85%. The 15-30% gap represents the model ignoring injected instructions. Independent confirmation of title-20 §4.6 and EXECUTION-FRAMEWORK §8 design choice.

**Tiered enforcement by platform capability:**
Hook support varies: Claude Code (21+ lifecycle events, 4 handler types), Cursor (lifecycle hooks), Copilot (preToolUse), Gemini CLI (BeforeTool) — all deterministic. Codex/Windsurf/Cline use prompt injection only (~70-85%). Claude app/ChatGPT/Gemini web have no hook support. Maps cleanly to EXECUTION-FRAMEWORK §8.4 enforcement layer matrix.

**`additionalContext` for just-in-time injection:**
Already implemented in UserPromptSubmit hook (title-20 §4.6.3 Pattern 1). RTK uses it for compression metadata — confirms field versatility.

**Token savings data (context, not governance):**
89% average noise removal across 2,900+ commands (first-party). Independent: 50-75% typical. High on test runners/git (80-98%), low on compact output (<30%). Relevant to context management, not enforcement.

### Platform Hook Support (May 2026)

| Platform | Hooks | Handler Types | MCP | Deterministic Enforcement |
|----------|-------|---------------|-----|--------------------------|
| Claude Code | 21+ events | command, HTTP, prompt, agent | Yes | Yes |
| Cursor | lifecycle events | command | Yes | Yes |
| GitHub Copilot | preToolUse | command | Limited | Yes |
| Gemini CLI | BeforeTool | command | Yes | Yes |
| Codex | None | N/A (AGENTS.md instructions) | N/A | No |
| Claude app | None | N/A | Yes | No (MCP context only) |

## Lessons Learned

1. HTTP hooks are the missing specification layer for our enforcement proxy. EXECUTION-FRAMEWORK §8 describes the proxy architecturally but doesn't specify the protocol. HTTP hooks provide the mechanism: JSON POST with allow/deny/ask. However, they're Claude Code-only — they solve centralized evaluation but not cross-platform enforcement.

2. `rtk discover` reveals a sensor category our Guide/Sensor taxonomy doesn't name: coverage-gap sensors (missed opportunities, not violations). Current sensors detect whether taken actions were compliant — not whether beneficial guidance was available but unconsulted.

3. The 70-85% instruction adoption rate has a structural explanation: autoregressive generation means instructions loaded early decay as context grows. Hooks bypass this because they execute outside the model's decision loop — independent confirmation of forward-continuation bias research.

4. RTK's four-handler taxonomy (command, HTTP, prompt, agent) maps to increasing capability and decreasing determinism. Our enforcement correctly uses command hooks for maximum determinism.

## Cross-References

- Principles: multi-method-hook-based-enforcement-client-side-deterministic, coding-method-third-party-hook-vetting-procedure
- Methods: EXECUTION-FRAMEWORK §8 (Enforcement Layer Matrix), title-20 §4.6 (Enforcement Levels), title-20 §4.6.3 (Hook Patterns), rules-of-procedure §3.6.4 (Platform Compatibility)
- See also: ref-multi-agent-harness-engineering-synthesis (Guide/Sensor taxonomy, ratchet pattern)
