---
description: Generate or update documentation for a target file, module, API, or project. Works in three phases — classify and generate a draft, verify every claim against actual code using tool-assisted verification (grep/read as oracle), and revise any failures. Auto-detects doc frameworks. Invoke when the user says "generate docs", "write docs", "document this", "add documentation", "doc-gen", "update docs", "README for", or "add docstrings". Do NOT use for code review (use /code-review), content enhancement/transformation (use /content-enhancer), test generation (use /test-suite), or building doc sites (use framework tooling directly).
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Grep
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`
**Branch:** !`git branch --show-current`
**Doc framework:** !`test -f mkdocs.yml && echo "mkdocs" || (test -f docusaurus.config.js -o -f docusaurus.config.ts && echo "docusaurus" || (test -f conf.py && echo "sphinx" || (test -f typedoc.json && echo "typedoc" || (test -f .readthedocs.yml && echo "readthedocs" || (test -f jsdoc.json -o -f jsdoc.conf.json && echo "jsdoc" || echo "none detected")))))`
**Existing docs:** !`find . -maxdepth 3 \( -name "*.md" -o -name "*.rst" -o -name "*.adoc" \) -not -path "./.git/*" -not -path "./node_modules/*" 2>/dev/null | wc -l | tr -d ' '` files

## Instructions

You are generating documentation. Read `procedure.md` in this skill folder for the full 3-phase protocol.

### Quick Start

1. **Determine the target.** If the user specified a file, module, or project, use that. If they said "document this" after editing code, document the most recently modified files. If ambiguous, ask.

2. **Read `procedure.md`** for the full protocol.

3. **Execute all three phases in order:**
   - **Phase 1: Classify & Generate** — classify Divio quadrant, identify audience, read target code, generate draft with corrective constraints
   - **Phase 2: Verify** — tool-assisted claim verification (grep/read as oracle), example validation, padding check, completeness check (non-skippable)
   - **Phase 3: Revise** — fix any claims/examples that failed verification, re-run checks until clean

4. **Deliver the documentation** with the verification results summary.

### Key Principles

- **Tool-assisted verification is non-negotiable.** The #1 AI documentation failure mode: fabricated claims (66% of AI doc hallucinations). Every factual claim must be confirmed via grep/read command, not self-attestation. Distinguish mechanically-verified claims from self-reviewed claims in output.
- **Value test, applied per-sentence.** "What does this tell the reader that they can't learn faster by reading the code?" If nothing, delete it.
- **Divio quadrant purity.** Classify before writing. Never blend tutorial with reference, or explanation with how-to, in the same section.
- **Documentation proportional to stability.** Stable public APIs get detailed docs. Internal code in flux gets minimal docs — let types and tests serve as living documentation until the API stabilizes.

### What This Skill Does NOT Do

- **Run or build doc sites** — it generates content. Use MkDocs/Docusaurus/Sphinx tooling for site building.
- **Review existing code** — use `/code-review` for that.
- **Transform/enhance existing content** — use `/content-enhancer` for that.
- **Generate tests** — use `/test-suite` for that.
- **Audit existing doc coverage** — planned for v2; for now, specify what to document.
