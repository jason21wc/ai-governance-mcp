# Happy MCP 5-min Disconnect — Investigation Artifact (2026-04-17 → 2026-04-18)

**Status (2026-04-18 session 113, closed):** Patch reverted to vanilla. Session-112's root-cause hypothesis (Node server-side `requestTimeout`) was **wrong**. Live logs from a fresh wrapper (PID 4801, started ~23h after session-112 patched both bundles) show drops continuing at N × 300s. Real root cause is **client-side**: undici's default `bodyTimeout = 300000 ms` fires on an SSE stream that `@modelcontextprotocol/sdk@1.25.3`'s `WebStandardStreamableHTTPServerTransport` never keeps alive (no heartbeat). See "Revised diagnosis (session 113)" section immediately below. Both bundle patches reverted 2026-04-18. Future work tracked in BACKLOG #103.

## Revised diagnosis (session 113, 2026-04-18)

**Root cause (revised):** Client-side undici `bodyTimeout` (300000 ms default in Node's built-in HTTP client) fires when no body data arrives on an open SSE stream for 5 min. The MCP SDK's `WebStandardStreamableHTTPServerTransport` sends messages when it has them and is otherwise silent — no `:keepalive\n\n` heartbeat, no `setInterval` write. Grep of `@modelcontextprotocol/sdk@1.25.3/dist/esm/server/webStandardStreamableHttp.js` and the Node wrapper `streamableHttp.js` finds zero heartbeat/setInterval/ping logic. When claude-code CLI (which uses undici fetch internally) opens an SSE stream to Happy and the stream goes idle for 300s, undici aborts.

**Why session-112 mis-localized to the server:**

1. **Dual-default coincidence.** Node's default `server.requestTimeout` is 300000 ms and undici's default `bodyTimeout` is 300000 ms. Two different 300s timers on opposite sides of the connection, same observed cadence. Disabling the server-side one was verifiable (patch the file) but produced no behavioral change.
2. **Cross-server drop comparison was confounded.** Session-112's diagnostic counted drops across 7 MCP servers on the same CLI (happy=888, every other server=0) and concluded "cause is happy-local." True but misleading — the other MCP servers (context-engine, ai-governance, etc.) use **stdio** transport, not HTTP/SSE. There's no undici `bodyTimeout` exposure on stdio at all. The comparison proved "HTTP-SSE transport without heartbeat is problematic in this CLI." Happy was the only instance of that transport, so the cause appeared Happy-specific. It is, in a narrow sense (Happy chose this SDK with this default), but the fix doesn't live in Happy's code.
3. **`TypeError: terminated`** in the claude-code MCP logs is undici's specific abort error — a direct tell for client-side origin. Different client versions on the same wrapper produced different error strings (`TimeoutError` vs `TypeError: terminated`) at the same 300s cadence, which is consistent with different undici wrapper behaviors timing out against the same silent stream, not with a single server timer killing everyone.

**Evidence (session-113 logs, post-patch, patched wrapper PID 4801 on port 52082):**

| Wrapper session | Uptime of drop | Client error |
|---|---|---|
| `5052470d-f647…` (claude-code/2.1.114 cli) | 299s / 600s / 901s | `TimeoutError: The operation timed out.` |
| `b729d8bc-12a0…` (claude-code/2.1.112 sdk-ts) | 300s / 602s / 1054s | `SSE stream disconnected: TypeError: terminated` |

Both sessions hit three consecutive terminal errors → transport torn down → reconnect → restored in <1s. The patch did not change the drop cadence because it was not the cause.

**Architecturally-correct fix (upstream):** `WebStandardStreamableHTTPServerTransport` needs a heartbeat option (e.g., `keepaliveMs: 25000`) that periodically writes `:keepalive\n\n` (an SSE comment line) to each open stream. Happy can then opt in. This matches the session-112 security-auditor's recommendation ("SDK-level SSE heartbeat as architecturally-correct upstream direction") — that recommendation was right; we just filed it as a stretch target instead of the primary fix.

**Path forward:** BACKLOG #103 reframed from "file Happy one-line patch upstream" to "file MCP SDK heartbeat request at github.com/modelcontextprotocol/typescript-sdk, cross-reference slopus/happy." No local hack. Claude-code auto-reconnect survives the drops; cost/benefit does not justify bundle-level workarounds.

## Outcome (2026-04-18)

- **Bundles restored to vanilla.** `server.requestTimeout = 0;` line removed from both MJS (line 5622) and CJS (line 5643). `grep server.requestTimeout /Users/jasoncollier/.nvm/versions/node/v22.18.0/lib/node_modules/happy/dist/*` returns no matches.
- **Investigation closed.** Session-112's hypothesis is superseded; LEARNING-LOG and SESSION-STATE corrected in same commit as this edit.
- **No upstream filing yet.** Wait for next engagement with BACKLOG #103.

---

**Everything below this line is session-112's investigation record, preserved as history. Its root-cause section is SUPERSEDED by the revised diagnosis above.**

## ⚠ Critical correction — wrapper vs daemon (session 112, 2026-04-17)

Initial plan assumed restarting the Happy *daemon* would activate the patch. It does not.

- **The MCP HTTP endpoint on port 60772 is hosted by the per-session `happy` wrapper process** (PID 93357 in this session; parent chain: `happy` CLI entrypoint → `dist/index.mjs` → our patched `dist/index-DR7ZghBK.mjs`). Verified via `lsof -nP -iTCP:60772 -sTCP:LISTEN`.
- **The Happy daemon is a separate process tree** (PID 92038 → 99688 after my restart). It hosts the daemon-control HTTP server (port 60141 → 62142) and the WSS relay connection to `api.cluster-fluster.com`. It does NOT host the per-session MCP endpoint.
- **Restarting the daemon does not reload the wrapper's in-memory bundle.** The wrapper process is a long-lived parent of the Claude Code CLI child; it picks up the patched bundle ONLY at its own startup.

Post-restart empirical check confirmed the failure mode: a drop still occurred at `05:39:13Z` (after 908s uptime) under the same un-patched wrapper. The patch is correct on disk; the activation step was wrong.

**Implication for future attempts:** the patch activation sequence is *end this session → start new `happy` invocation*, not *kill daemon*.

## What this is

Investigation and local diagnostic patch for the recurring 5-minute disconnect on Happy's local MCP HTTP server. Mirrors the `onnx-backend-attempt-2026-04-15.md` precedent for preserving un-shipped or partially-shipped diagnostic work outside `git` history, so a future session can pick up without re-deriving context.

## Problem summary

The Claude Code CLI's MCP transport to Happy's local loopback HTTP server (`http://127.0.0.1:<ephemeral>`) drops its SSE stream every ~300 seconds, regardless of activity. After 3 consecutive drops Claude Code tears down and re-registers the MCP connection, which churns the available tool set (e.g., swapping `TodoWrite` for `TaskCreate/Update/List/Get`) and, in at least one observed case, failed an in-flight tool call mid-drop (`ExitPlanMode`, 2026-04-17 session).

Other MCP servers on the same Claude Code CLI are unaffected.

## Root cause (session-112 hypothesis — SUPERSEDED, see revised diagnosis at top)

Happy wraps `@modelcontextprotocol/sdk@1.25.3` `StreamableHTTPServerTransport` in a bare Node `http.createServer()` at:

- `/Users/jasoncollier/.nvm/versions/node/v22.18.0/lib/node_modules/happy/dist/index-DR7ZghBK.mjs:5602–5621` (MJS, runtime path via `bin/happy-mcp.mjs`)
- `/Users/jasoncollier/.nvm/versions/node/v22.18.0/lib/node_modules/happy/dist/index-DDeR3Cx8.cjs:5623–5642` (CJS, loaded only by `require()` consumers)

The server is created without overriding `server.requestTimeout`. Node 22.18.0's default is exactly **300000 ms** (added in Node 18 as a Slowloris mitigation). This timer kills long-lived request/response pairs at 5 min regardless of SSE activity, closing the stream.

Verified on the actual runtime via `node -e`:
```
requestTimeout default: 300000 ms
headersTimeout default: 60000 ms
keepAliveTimeout default: 5000 ms
timeout default: 0 ms
```

Other timeouts confirmed non-contributory:
- `headersTimeout` — applies only until headers sent; SSE sends headers immediately.
- `keepAliveTimeout` — governs idle between requests on a kept-alive socket; an active SSE stream is not idle.
- `server.timeout` — already 0 (disabled).

## Evidence

**Drop-count localization** (rules out client side):

| MCP server | Historical drops in `mcp-logs-<server>/*.jsonl` |
|---|---|
| happy | **888** |
| context-engine | 0 |
| ai-governance | 0 |
| github | 0 |
| context7 | 0 |
| vercel | 0 |

Same Claude Code CLI, same time window. If the cause were CLI-side, all servers would drop proportionally.

**Drop-uptime distribution** (887 of 888 drops; 1 outlier):

| Uptime bucket (s) | Count |
|---|---|
| ~300 (300–302) | 294 |
| ~600 (602–605) | 289 |
| ~900 (904–907) | 286 |
| 618 / 626 / 671 / 920 / 354 / 350 | 1 each (6 total) |
| 4605 / 4907 / 5210 | 1 each (3 outliers — possibly unrelated or test-induced) |

The tight clustering at N × 300s confirms a deterministic periodic timer. The handful of off-cadence drops (<1% of total) are flagged for noting to upstream but do not change the dominant-cause diagnosis.

**24h baseline** (the comparator for Window 2): 100 drops across 6 log files ≈ 4 drops/hr.

## Patch diff (both bundles applied on disk)

```diff
--- a/dist/index-DR7ZghBK.mjs
+++ b/dist/index-DR7ZghBK.mjs
@@ -5619,6 +5619,7 @@ async function startHappyMcpServer(...) {
       mcp.close();
     }
   });
+  server.requestTimeout = 0;
   const baseUrl = await new Promise((resolve) => {
     server.listen(0, "127.0.0.1", () => {
       const addr = server.address();
```

The identical one-line insertion was applied to the `.cjs` bundle at `dist/index-DDeR3Cx8.cjs:5626` (same anchor). Per security-auditor: MJS is the primary runtime path (via the `happy` CLI entrypoint `dist/index.mjs`); CJS is used by any `require('happy')` consumers. Both patched for discipline. Patch will be wiped on next `npm install -g happy@<version>` upgrade.

**Do NOT patch** the `startHookServer` `createServer(...)` block that appears immediately below in both bundles (mjs:5642 / cjs:5663). It's a POST-only short-lived handler with its own intentional 5s timeout. Patching it would break health checks.

## Verification log

**Pre-patch baseline (captured 2026-04-17 session 112):**
- 100 drops in last 24h across 6 log files.
- Dominant cadence N × 300s confirmed.

**Session 112 attempt (did NOT activate patch):**
- Daemon restart at 05:36:43Z moved daemon control port 60141 → 62142 (PID 92038 → 99688).
- MCP endpoint on port 60772 was never restarted (hosted by wrapper PID 93357, not the daemon).
- Post-restart drop observed at 05:39:13Z (908s uptime — the old SSE stream unwinding).
- User-visible symptom: `ExitPlanMode` and `Bash(date)` tool calls failed with "Tool permission stream closed before response received" mid-drop.
- **Conclusion:** Did not verify the patch because the wrapper was still running pre-patch code. Verification is pending — see Resumption steps below.

**Pending — Window 1 (20 min fully idle, new `happy` session, patched wrapper):** TBD
**Pending — Window 2 (≥60 min mixed usage):** TBD
**Pass / fail:** TBD.

## Resumption steps (for the next session picking this up)

1. **Confirm patch is still on disk:**
   ```sh
   grep -n "server.requestTimeout = 0" \
     /Users/jasoncollier/.nvm/versions/node/v22.18.0/lib/node_modules/happy/dist/index-DR7ZghBK.mjs \
     /Users/jasoncollier/.nvm/versions/node/v22.18.0/lib/node_modules/happy/dist/index-DDeR3Cx8.cjs
   ```
   Expect one match in each. If missing (e.g., `happy` was upgraded), re-apply per "How to re-apply" section below.

2. **If the next session is already started via `happy`**, the patched bundle was loaded at its startup — you're already testing. Skip to step 4.

3. **If you want to explicitly start a fresh verification session:** exit the current Claude Code session, then run `happy` fresh from a terminal in this project. This spawns a new wrapper process (new PID) that reads the patched bundle.

4. **Capture baseline drop rate** for the last 24h of `mcp-logs-happy/*.jsonl` as the comparator (script: see "Monitor script" below).

5. **Run verification windows:**
   - Window 1: 20 min idle, expect 0 drops in the current session's `mcp-logs-happy/*.jsonl`.
   - Window 2: ≥60 min mixed usage, expect drops ≤ 10% of baseline and no drops at N × 300s multiples.

6. **Outcome:**
   - **Pass:** proceed to Track B (file upstream issue at github.com/slopus/happy using the pre-filing research already in conversation: Claude Code issues #3033, #20335, #18557 as adjacent reports).
   - **Fail:** revert both bundle edits (replace the `server.requestTimeout = 0;` line with its removal), document the negative result in this file, close investigation.

### Monitor script (for step 5)

```python
# background: poll every 20s for new drops after a chosen cutoff timestamp
import json, os, glob, time, sys
cutoff = '<RESTART_TIMESTAMP_UTC>'   # fill in from `date -u +%Y-%m-%dT%H:%M:%SZ`
deadline = time.time() + 1500        # 25 min
while time.time() < deadline:
    for f in sorted(glob.glob('/Users/jasoncollier/Library/Caches/claude-cli-nodejs/-Users-jasoncollier-Developer-ai-governance-mcp/mcp-logs-happy/*.jsonl')):
        if os.path.basename(f).replace('.jsonl','') < cutoff[:16].replace(':','-'): continue
        with open(f) as fh:
            for line in fh:
                try: d = json.loads(line)
                except: continue
                if 'connection dropped' in d.get('debug','') and d.get('timestamp','') > cutoff:
                    print(f'DROP: {d["timestamp"]} | {d["debug"]}'); sys.exit(1)
    time.sleep(20)
print('NO DROPS in 25 min')
```

## How to re-apply on Happy upgrade (manual procedure)

When `npm install -g happy@<new-version>` wipes the patch:

1. `grep -n "server.requestTimeout = 0" /Users/jasoncollier/.nvm/versions/node/v22.18.0/lib/node_modules/happy/dist/index-*.mjs` — confirm absence.
2. `happy doctor` → confirm version, get daemon PID if running.
3. Locate the `happyMCP` `createServer` block: `grep -n "const server = createServer" dist/index-*.mjs` — the relevant one is the block followed by `server.listen(0, "127.0.0.1", ...)` (NOT the `startHookServer` one).
4. Insert `  server.requestTimeout = 0;` immediately after the closing `});` of that `createServer` call.
5. Restart daemon: `kill <pid>` and re-run `happy` to auto-spawn.
6. Re-check upstream issue at `github.com/slopus/happy/issues?q=requestTimeout` to see if a fix shipped; if so, close this workaround.

No shell script is provided deliberately — per proportional rigor (contrarian review, plan file), the manual procedure is cheap enough and less prone to silent misapplication across bundle-layout changes.

## Related files

- Plan file: `~/.claude/plans/swift-booping-hamming.md` (approved 2026-04-17)
- LEARNING-LOG entry: "Cross-MCP-server drop comparison localizes disconnects" (2026-04-17)
- SESSION-STATE entry: session 112 summary (pending verification results)

## Why this is in `staging/` not `documents/`

This is operational diagnostic work on a third-party tool (Happy), not framework content. Precedent: `onnx-backend-attempt-2026-04-15.md`. The `staging/` directory is the correct home for time-stamped investigation artifacts that are not part of the canonical framework but must survive across sessions.

If the upstream fix ships and the local patch becomes obsolete, this file stays in `staging/` as a historical reference — same pattern as the ONNX investigation.
