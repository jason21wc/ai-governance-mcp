---
description: |
  Subagent model and effort routing table. Use when dispatching subagents via the Agent
  tool or Workflow scripts to select the right model and effort level. Triggers: "route
  this subagent", "which model for", "model routing", "effort level", "subagent model".
  Does NOT apply to: session model selection (that's /model), DOE calibration (#209),
  or non-Claude platforms (Codex routable via MCP but effort param not exposed).
disable-model-invocation: false
allowed-tools: Read
---

# /model-routing — Subagent Model & Effort Dispatch

Quick-reference for routing subagent `model` and `effort` via the Agent tool or Workflow scripts.

## Context

**Available models:** `sonnet`, `opus`, `haiku`, `fable` — aliases that auto-resolve to the latest generation on each release. Check the system prompt ("You are powered by…") for the current resolution.
**Effort:** settable in Workflow `agent(prompt, {effort: "high"})` only. The Agent tool has no `effort` parameter — subagents inherit session effort. Levels: `low`/`medium`/`high`/`xhigh`/`max` on opus, sonnet, and fable. **haiku has no effort parameter** — omit it there.
**Default:** omit `model` to inherit the session model. Only override when the task's cognitive function demands a different tier.

## Core Principle

**Effort is the primary lever; model is the ceiling.** Raising effort on a cheaper model often outperforms dropping effort on a more expensive one. Route by cognitive function, not by generic "difficulty."

## Routing Table

| Cognitive Function | Model | Effort | When to use |
|--------------------|-------|--------|-------------|
| Heavy implementation | `opus` | xhigh | Multi-file code changes, complex refactors, architectural rewrites |
| Deep analysis | `opus` | high | Security audits, multi-file code review, architecture assessment |
| Hardest reasoning | `fable` | high | Long-horizon autonomous runs, problems opus stalls on — 2× opus cost, so earn it |
| LLM-as-judge | `fable` | medium | Eval scoring, independent quality assessment, grading rubrics |
| Standard tasks | `sonnet` | medium | Single-file edits, test writing, documentation, data transforms |
| Mechanical work | `sonnet` | low | Log analysis, formatting, simple lookups, template expansion |
| Fast classification | `haiku` | *omit* | Categorization, boolean checks, format validation (no effort parameter; **row is out of DOE #209 scope — untested**) |
| Cross-vendor review | Codex (MCP) | *n/a* | Independent second opinion, peer review — dispatched via `mcp__codex__codex`, not Agent tool; effort param not exposed |
| **Inherit (no override)** | *omit* | *omit* | Task matches session model's tier — often the right call |

**Relative cost:** haiku ≪ sonnet < opus < **fable** (~2× opus). Reach for fable for capability, not habit. Reaching for opus on a sonnet-tier task wastes tokens; reaching for haiku on an opus-tier task wastes quality. Check the vendor pricing page for current per-MTok rates.

**Context window is no longer a routing axis between the top tiers.** opus, sonnet, and fable share the same large window. Only `haiku` is smaller — that is the one case where window size decides.

## Cross-Model Effort Calibrations

Manufacturer-reported, not empirically validated (DOE BACKLOG #209 pending). These shift with each release — treat as approximate:

- **opus low and medium punch well above their weight** — start at `xhigh` for coding/agentic and `high` elsewhere, then sweep *down* and keep the cheapest level your evals still pass. Effort defaults from a prior generation rarely transfer.
- sonnet medium ≈ prior-gen high
- sonnet high ≈ prior-gen max
- fable low often exceeds prior-gen xhigh/max

**Effort is the primary cost lever, but it does not reliably shorten user-facing output on opus** — prompt for concision instead. At `xhigh`/`max`, give the agent a large token budget so it isn't truncated mid-thought.

## Usage

```javascript
// Workflow — full control (model + effort)
agent("prompt", { model: "fable", effort: "medium", label: "judge" })

// Agent tool — model override only (effort inherits from session)
Agent({ model: "opus", prompt: "...", description: "..." })

// Agent tool — inherit everything (the default, often correct)
Agent({ prompt: "...", description: "..." })
```

## Decision Checklist

1. **Need a subagent at all?** A single-model task doesn't need dispatch overhead.
2. **What cognitive function?** Match the routing table — function, not difficulty.
3. **How much context?** Only `haiku` is context-limited; opus/sonnet/fable share the same large window. Route large sweeps by capability, not window.
4. **Side effects?** Code writes or consequential changes → `opus` at higher effort.
5. **Independence needed?** Judge/reviewer roles benefit from a different model than the one being evaluated.
6. **Cost proportional?** Don't reach for `opus` on mechanical tasks. Don't economize on security audits.

## Scope & Limitations

- **Volatile — and this file is the framework's designated live source, which makes that a load-bearing property, not a caveat.** `rules-of-procedure` §10.1.4 tells authors *not* to pin model versions in governance documents and to resolve them from a live source instead; this skill is one of the sources it names. So the values here are supposed to be current — but the file is hand-maintained markdown, not an API, and a "keep this updated" note is not an enforcement mechanism (the lesson `tests/test_document_versions_pin.py` was built on).
  **The honest statement of the gap:** every value below rots on a vendor's release cadence, nothing checks that this file was refreshed, and a governance document that de-pinned *to* here inherits whatever staleness sits here. Treat a stale entry as a defect in the doctrine's plumbing, not a cosmetic lag.
  **Refresh trigger:** OPERATIONS **T-166** (working-model upgrade) whenever it fires. If today is materially past a release you know about, verify against the vendor's models API before trusting a value here — and say so when you do, per `meta-safety-transparent-limitations`.
- **Agent tool effort gap:** The Agent tool does not expose an `effort` parameter. Use Workflow `agent()` when effort control matters.
- **Haiku has no effort control:** `effort` is not a parameter on haiku. Omit it rather than passing a level that has no meaning there.
- **Empirical calibration pending:** See BACKLOG #209 (DOE screening experiment).
- **Platform:** Claude Code. Codex is routable via MCP (`mcp__codex__codex`) but `effort` is not exposed — dispatch it for cross-vendor review, not effort-controlled work.
- **Session settings are separate — model AND effort.** This skill routes *subagents*. Your own session model and `effortLevel` are user preferences set via `/model` and `settings.json`, not routing decisions. Do not propagate a session preference into this table: "I rarely run my session at low effort" says nothing about whether a subagent should parse logs at low effort. They are different decision surfaces with different cost profiles.
