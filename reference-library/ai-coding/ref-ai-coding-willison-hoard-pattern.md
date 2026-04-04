---
id: ref-ai-coding-willison-hoard-pattern
title: "Hoard Things You Know How to Do (Willison Pattern)"
domain: ai-coding
tags: [patterns, reuse, agent-productivity, knowledge-management]
status: current
entry_type: reference
summary: "Pattern for maintaining a curated library of working examples that AI agents can retrieve and recombine"
created: 2026-03-26
last_verified: 2026-03-26
maturity: evergreen
decay_class: evergreen
source: "Q&A session analyzing Willison's Agentic Engineering Patterns guide"
external_url: "https://simonwillison.net/guides/agentic-engineering-patterns/hoard-things-you-know-how-to-do/"
external_author: "Simon Willison"
accessed_date: 2026-03-26
related: [ref-ai-coding-autoresearch-pattern]
---

## Context

Simon Willison maintains 1,000+ repositories, TIL blog posts, and tool sites — each containing working code examples. When building something new, he tells agents to combine existing working examples. The recombination is the multiplier: "we only ever need to figure out a useful trick once."

This pattern directly inspired the Reference Library (TITLE 15 in ai-governance methods). The key insight: methods and principles capture *how to think about* a problem; the Reference Library captures *working solutions* to recombine.

## Artifact

**The pattern has three components:**

1. **Capture:** When something works, save it in a retrievable format — not just the code, but the context (when to use it, what problem it solves, what went wrong along the way).

2. **Index:** Make entries discoverable by semantic search, tags, and relationships. An agent that can't find the right precedent might as well not have one.

3. **Recombine:** Tell agents to combine existing working examples. "Take my MCP server pattern and my Docker multi-arch pattern and build a containerized MCP server." Each working example is a building block; the agent is the assembler.

**Willison's infrastructure for this:**
- Public TIL blog (til.simonwillison.net) — short "today I learned" entries with working code
- Tool websites (datasette, shot-scraper, etc.) — each is a working reference
- GitHub repos — each repo is a searchable working example
- The key: everything is public, searchable, and written for future-self consumption

## Lessons Learned

- The capture cost must be low or it won't happen. Auto-generation of metadata (title, tags, summary) helps.
- Working code > described approach. An agent can use working code directly; it must interpret a description.
- Context matters as much as code. "This works" is less useful than "this works for X problem when Y constraint applies."
- Volume compounds: 10 entries = modest utility; 100 entries = strong recombination; 1000 entries = transformative (Willison's scale).

## Cross-References

- Principles: meta-core-project-reference-persistence
- Methods: TITLE 15 (Reference Library), §7.0 (Memory Architecture)
- See also: This entry is the founding reference for the entire Reference Library concept
