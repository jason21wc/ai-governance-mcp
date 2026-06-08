# Release & Repository Model

This repository is the **public extract** of a larger, privately-maintained AI
Governance framework. It contains the governance **engine** (MCP server + context
engine), the **meta-framework** (constitution + rules of procedure), specialized
subagents, enforcement hooks, and infrastructure. **Subject-matter domains** (AI
coding, multi-agent, accounting, etc.) and any third-party material are maintained
in a separate **private** repository and are not part of this public extract.

## How the public extract is produced

The private repository is the primary, where development happens. The public repo
is produced by a **fail-closed allowlist extraction**, not a fork — so private
content cannot leak by omission:

1. **Allowlist** (`documents/.public-allowlist`) — the single source of truth for
   what may exist in the public tree. Anything not explicitly listed is private by
   default. It drives both the copy and the check, so they cannot drift.
2. **De-domain** — the extraction strips the domain registry fallback, drops
   domain-coupled tests, and removes any domain references from runtime config, so
   the engine runs cleanly on the meta-framework alone.
3. **Meta-only index** — the search index is **rebuilt from `documents/`** at
   install/CI/Docker time (constitution only). It is a build artifact and is **not
   committed** (`index/` is gitignored here).
4. **Leak-guard** (`scripts/check-public-release.py`) — a three-layer, fail-closed
   check run before publish and in this repo's CI (`public-release-guard` job):
   - **path allowlist** — every file must match an allowlist glob, else fail;
   - **content scan** (private-side only) — proprietary markers must not appear in
     an allowlisted file;
   - **structural invariant** — the domain-enumerating fallback must be absent.
5. **Human gate** — publishing is treated as an external-irreversible action; a
   human reviews the staged tree and performs the push. The extraction tooling
   never pushes.

You can verify any checkout of this repo is clean:

```bash
python3 scripts/check-public-release.py --root .   # exit 0 = clean
```

## Leak-remediation runbook

If private content ever reaches this public repository:

1. **Scrub history** — `git filter-repo --path <leaked-path> --invert-paths` (or
   `--replace-text` for strings), then force-push the rewritten history.
2. **Purge caches** — request a GitHub cache/fork purge for the affected refs;
   assume anything pushed may already have been cloned (treat as disclosed).
3. **Rotate** — if any credential was exposed, rotate it immediately. (Proprietary
   *text* cannot be rotated; history-scrub + assume-disclosed is the response.)
4. **Tighten** — update the allowlist / content denylist so the leak class cannot
   recur, and add a regression case.
5. **Record** — log the incident and the fix in the private operations log.

## License

- **Code:** Apache-2.0 (`LICENSE`)
- **Framework content:** CC-BY-NC-ND-4.0 (`LICENSE-CONTENT`)
