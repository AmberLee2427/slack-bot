#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE_DIR=${COMPOSE_DIR:-/home/nancy/slack-bot}
STATE_DIR=${STATE_DIR:-/run/nancy-maintenance}
COOLDOWN_SECONDS=${COOLDOWN_SECONDS:-900}
mkdir -p "$STATE_DIR"
exec 9>"$STATE_DIR/health-repair.lock"
flock -n 9 || exit 0

log() { logger -t nancy-health-repair -- "$*"; printf '%s\n' "$*"; }

can_restart() {
    local service=$1 stamp="$STATE_DIR/$1.last-restart" now last=0
    now=$(date +%s)
    [[ -f $stamp ]] && read -r last < "$stamp"
    (( now - last >= COOLDOWN_SECONDS ))
}

restart_service() {
    local service=$1 reason=$2
    if ! can_restart "$service"; then
        log "$service remains unhealthy; restart suppressed by ${COOLDOWN_SECONDS}s cooldown ($reason)"
        return 1
    fi
    date +%s > "$STATE_DIR/$service.last-restart"
    log "restarting $service ($reason)"
    (cd "$COMPOSE_DIR" && docker compose restart "$service")
}

check_url() { curl --fail --silent --show-error --max-time 15 "$1" >/dev/null; }

declare -A URLS=(
    [nancy-brain]="http://127.0.0.1:8000/health"
    [nancy-bot]="http://127.0.0.1:3000/health"
    [nancy-ui]="http://127.0.0.1:8501/_stcore/health"
)

for service in nancy-brain nancy-bot nancy-ui; do
    if ! check_url "${URLS[$service]}"; then
        restart_service "$service" "local health check failed" || true
    fi
done

for pair in "nancy-docs:nancy-hosted-docs" "tunnel:nancy-tunnel"; do
    service=${pair%%:*}
    container=${pair#*:}
    if [[ $(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null || true) != true ]]; then
        restart_service "$service" "container is not running" || true
    fi
done

# A healthy local service with a failed public route usually means the tunnel needs repair.
if ! check_url "https://nancy-brain.malpas.nz/health"; then
    restart_service tunnel "public Nancy Brain health check failed" || true
fi

