#!/usr/bin/env bash
# Stop SSH tunnel started by tunnel-contabo.sh (local port forward).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_PORT="${CONTABO_LOCAL_PG_PORT:-5433}"

pids=$(lsof -tiTCP:"$LOCAL_PORT" -sTCP:LISTEN 2>/dev/null || true)
if [ -z "$pids" ]; then
  echo "No tunnel on port ${LOCAL_PORT}"
  exit 0
fi

for pid in $pids; do
  if ps -p "$pid" -o command= 2>/dev/null | grep -q "ssh.*${LOCAL_PORT}:127.0.0.1"; then
    kill "$pid" 2>/dev/null || true
    echo "Stopped tunnel (pid ${pid})"
  fi
done
