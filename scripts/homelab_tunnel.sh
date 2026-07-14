#!/usr/bin/env bash
# SSH local forward: homelab Postgres (127.0.0.1 on VPS → LOCAL_PG_PORT).
# Same module as real-time-minaki-poc/api/scripts/homelab_tunnel.sh — sourced by start_dev.sh.
#
# Set POSTGRES_URI_CONTABO in .env to 127.0.0.1:LOCAL_PG_PORT (see scripts/sync_homelab_db_env.sh).
#
# .env:
#   HOMELAB_SSH_TARGET=user@host  (or HOMELAB_SSH_ENV_FILE with SERVER_IP + SSH_USER)
#   SSH_KEY=~/.ssh/id_ed25519     # optional
#   LOCAL_PG_PORT=15432
#   TUNNEL_SKIP_REDIS=1           # CMA uses postgres-only by default

homelab_tunnel_load_ssh() {
  if [[ -n "${HOMELAB_SSH_TARGET:-}" ]]; then
    SSH_USER="${HOMELAB_SSH_TARGET%%@*}"
    SERVER_IP="${HOMELAB_SSH_TARGET#*@}"
    if [[ -z "$SERVER_IP" || "$SSH_USER" == "$HOMELAB_SSH_TARGET" ]]; then
      echo "homelab_tunnel: HOMELAB_SSH_TARGET must be user@host (got ${HOMELAB_SSH_TARGET})" >&2
      return 1
    fi
    return 0
  fi
  local ef="${HOMELAB_SSH_ENV_FILE:-}"
  if [[ -n "$ef" && -f "$ef" ]]; then
    # shellcheck disable=1090
    set -a && source "$ef" && set +a
  fi
  if [[ -z "${SERVER_IP:-}" || -z "${SSH_USER:-}" ]]; then
    echo "homelab_tunnel: set HOMELAB_SSH_TARGET=user@host in .env, or SERVER_IP + SSH_USER via HOMELAB_SSH_ENV_FILE" >&2
    return 1
  fi
}

homelab_tunnel_wait_port() {
  local host="$1" port="$2" tries="${3:-45}"
  local attempt
  for ((attempt = 1; attempt <= tries; attempt++)); do
    if nc -z "$host" "$port" 2>/dev/null; then
      return 0
    fi
    sleep 1
  done
  echo "homelab_tunnel: timeout waiting for $host:$port" >&2
  return 1
}

homelab_tunnel_smoke_local_forward() {
  local port="$1" name="$2"
  if ! nc -w 5 -z 127.0.0.1 "$port" 2>/dev/null; then
    echo "homelab_tunnel: smoke test failed for ${name} on 127.0.0.1:${port}" >&2
    return 1
  fi
  return 0
}

homelab_tunnel_ssh_exec() {
  local user="${SSH_USER:-root}"
  if [[ -n "${SSH_KEY:-}" ]]; then
    ssh -i "${SSH_KEY/#\~/$HOME}" -o ConnectTimeout=15 -o BatchMode=yes "$user@$SERVER_IP" "$@"
  else
    ssh -o ConnectTimeout=15 -o BatchMode=yes "$user@$SERVER_IP" "$@"
  fi
}

homelab_tunnel_probe_remote() {
  homelab_tunnel_load_ssh || return 1
  local rh="${HOMELAB_TUNNEL_REMOTE_HOST:-127.0.0.1}"
  local rpg="${HOMELAB_TUNNEL_REMOTE_PG_PORT:-5432}"
  echo "homelab_tunnel: probing VPS Postgres ${rh}:${rpg} ..." >&2
  homelab_tunnel_ssh_exec "nc -z -w 5 ${rh} ${rpg}" || {
    echo "homelab_tunnel: Postgres not accepting ${rh}:${rpg} on VPS — is supabase_db up?" >&2
    return 1
  }
}

homelab_tunnel_start() {
  homelab_tunnel_load_ssh || return 1

  local lp="${LOCAL_PG_PORT:-15432}"
  local rh="${HOMELAB_TUNNEL_REMOTE_HOST:-127.0.0.1}"
  local rpg="${HOMELAB_TUNNEL_REMOTE_PG_PORT:-5432}"
  local user="${SSH_USER:-root}"

  if nc -z 127.0.0.1 "$lp" 2>/dev/null; then
    echo "homelab_tunnel: reusing existing forward on 127.0.0.1:${lp}" >&2
    HOMELAB_SSH_TUNNEL_PID=""
    return 0
  fi

  homelab_tunnel_probe_remote || return 1

  echo "homelab_tunnel: ssh -L ${lp}:${rh}:${rpg} ${user}@${SERVER_IP}" >&2
  if [[ -n "${SSH_KEY:-}" ]]; then
    ssh -i "${SSH_KEY/#\~/$HOME}" -N \
      -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=60 \
      -o ConnectTimeout=15 \
      -L "${lp}:${rh}:${rpg}" \
      "${user}@${SERVER_IP}" &
  else
    ssh -N \
      -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=60 \
      -o ConnectTimeout=15 \
      -L "${lp}:${rh}:${rpg}" \
      "${user}@${SERVER_IP}" &
  fi
  HOMELAB_SSH_TUNNEL_PID=$!

  homelab_tunnel_wait_port 127.0.0.1 "$lp" || {
    homelab_tunnel_stop
    return 1
  }
  homelab_tunnel_smoke_local_forward "$lp" "Postgres" || {
    homelab_tunnel_stop
    return 1
  }

  echo "homelab_tunnel: forward OK — Postgres 127.0.0.1:${lp}" >&2
}

homelab_tunnel_stop() {
  if [[ -n "${HOMELAB_SSH_TUNNEL_PID:-}" ]] && kill -0 "$HOMELAB_SSH_TUNNEL_PID" 2>/dev/null; then
    kill "$HOMELAB_SSH_TUNNEL_PID" 2>/dev/null || true
    wait "$HOMELAB_SSH_TUNNEL_PID" 2>/dev/null || true
    echo "homelab_tunnel: stopped pid $HOMELAB_SSH_TUNNEL_PID" >&2
  fi
  HOMELAB_SSH_TUNNEL_PID=""
}
