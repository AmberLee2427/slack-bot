#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE_DIR=${COMPOSE_DIR:-/home/nancy/slack-bot}
STATE_DIR=${STATE_DIR:-/var/lib/nancy-maintenance/applications}
cd "$COMPOSE_DIR"
exec 8>/run/lock/nancy-deployment.lock
flock -n 8 || exit 0
mkdir -p "$STATE_DIR"
git -c safe.directory="$COMPOSE_DIR" diff --quiet && git -c safe.directory="$COMPOSE_DIR" diff --cached --quiet || {
    echo 'Refusing automatic deployment of uncommitted tracked source' >&2; exit 1;
}
available=$(df --output=avail -k / | tail -1)
if [[ ${1:-} != --deploy-built ]]; then
    (( available >= 8 * 1024 * 1024 )) || { echo 'Need at least 8 GiB free before building' >&2; exit 1; }
fi

services=(nancy-brain nancy-ui nancy-bot nancy-docs)
containers=(nancy-brain-mcp nancy-brain-ui nancy-slack-bot nancy-hosted-docs)
stamp=$(date -u +%Y%m%dT%H%M%SZ)
rollback="$STATE_DIR/rollback.json"
printf '{"services":{' > "$rollback"
for i in "${!services[@]}"; do
    old=$(docker inspect -f '{{.Image}}' "${containers[$i]}")
    tag="nancy-rollback/${services[$i]}:$stamp"
    docker tag "$old" "$tag"
    (( i == 0 )) || printf ',' >> "$rollback"
    printf '"%s":{"image":"%s"}' "${services[$i]}" "$tag" >> "$rollback"
done
printf '}}\n' >> "$rollback"

# No running containers change until every build and import check has succeeded.
if [[ ${1:-} != --deploy-built ]]; then
    docker compose build --pull --no-cache nancy-brain nancy-bot nancy-docs
fi
docker run --rm --network none --entrypoint python slack-bot-nancy-brain:latest \
    -c 'import requests, streamlit, torch; import connectors.mcp_server.server'
docker run --rm --network none --entrypoint python slack-bot-nancy-bot:latest \
    -c 'import requests, slack_sdk, anthropic; import bot.plugins.rag.mcp_adapter'

rollback_on_error() {
    trap - ERR INT TERM
    echo "Application deployment failed; restoring $rollback" >&2
    docker compose -f docker-compose.yml -f "$rollback" up -d --no-build --pull never "${services[@]}"
    exit 1
}
trap rollback_on_error ERR INT TERM
docker compose up -d --no-build --pull never "${services[@]}"
healthy=false
for _ in {1..36}; do
    healthy=true
    for container in "${containers[@]}"; do
        state=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container")
        [[ $state == healthy ]] || healthy=false
    done
    [[ $healthy == true ]] && break
    sleep 10
done
[[ $healthy == true ]]
docker exec -i nancy-brain-mcp python - < "$COMPOSE_DIR/ops/maintenance/app-canary.py"
curl --fail --silent --show-error --max-time 30 https://nancy-brain.malpas.nz/health >/dev/null
trap - ERR INT TERM
git -c safe.directory="$COMPOSE_DIR" rev-parse HEAD > "$STATE_DIR/deployed-revision"
docker inspect -f '{{.Name}} {{.Image}}' "${containers[@]}" > "$STATE_DIR/deployed-images"
logger -t nancy-app-update 'Application refresh and functional verification succeeded'
