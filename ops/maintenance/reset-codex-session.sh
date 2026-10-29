#!/usr/bin/env bash
set -Eeuo pipefail

# This intentionally ends active Codex extension sessions during the maintenance window.
mapfile -t pids < <(pgrep -u nancy -f 'codex.*app-server|@openai/codex|/mcp/launch\.mjs' || true)
((${#pids[@]})) || exit 0
logger -t nancy-codex-reset "terminating stale Codex processes: ${pids[*]}"
kill -TERM "${pids[@]}" 2>/dev/null || true
sleep 20
for pid in "${pids[@]}"; do
    kill -KILL "$pid" 2>/dev/null || true
done

