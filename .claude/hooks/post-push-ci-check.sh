#!/bin/bash
# Post-push CI check hook for Claude Code
# Triggers after any Bash tool call that contains "git push"
# Outputs CI run status so Claude can monitor for failures

set -euo pipefail

input=$(cat)

# Extract the command from tool_input
command=$(echo "$input" | jq -r '.tool_input.command // ""' 2>/dev/null)

# Only act on git push commands
if ! echo "$command" | grep -q 'git.*push'; then
  exit 0
fi

# Wait for GitHub to register the workflow run
sleep 5

# Try to get the latest CI run
if ! command -v gh &>/dev/null; then
  echo "[post-push hook] gh CLI not found — cannot check CI status"
  exit 0
fi

# Get the most recent workflow run triggered by push
run_info=$(gh run list --limit 1 --json status,conclusion,name,headBranch,url,createdAt 2>/dev/null) || {
  echo "[post-push hook] Could not fetch CI status"
  exit 0
}

status=$(echo "$run_info" | jq -r '.[0].status // "unknown"')
conclusion=$(echo "$run_info" | jq -r '.[0].conclusion // "pending"')
name=$(echo "$run_info" | jq -r '.[0].name // "unknown"')
branch=$(echo "$run_info" | jq -r '.[0].headBranch // "unknown"')
url=$(echo "$run_info" | jq -r '.[0].url // ""')

echo "[post-push hook] CI run detected: ${name} on ${branch}"
echo "  Status: ${status} | Conclusion: ${conclusion}"
echo "  URL: ${url}"

if [ "$status" = "in_progress" ] || [ "$status" = "queued" ]; then
  echo "  CI is still running. Use 'gh run watch' to monitor, or check back shortly."
fi
