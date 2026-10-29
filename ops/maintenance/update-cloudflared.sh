#!/usr/bin/env bash
set -Eeuo pipefail
exec 8>/run/lock/nancy-deployment.lock
flock -n 8 || exit 0

COMPOSE_DIR=${COMPOSE_DIR:-/home/nancy/slack-bot}
IMAGE=cloudflare/cloudflared:latest
ROLLBACK_IMAGE=cloudflare/cloudflared:nancy-rollback
cd "$COMPOSE_DIR"
exec 9>/run/nancy-cloudflared-update.lock
flock -n 9 || exit 0

old_id=$(docker image inspect -f '{{.Id}}' "$IMAGE")
docker tag "$IMAGE" "$ROLLBACK_IMAGE"
docker compose pull tunnel
new_id=$(docker image inspect -f '{{.Id}}' "$IMAGE")
[[ $new_id == "$old_id" ]] && exit 0

docker compose up -d --no-deps --force-recreate tunnel
for _ in {1..12}; do
    if curl --fail --silent --max-time 15 https://nancy-brain.malpas.nz/health >/dev/null; then
        logger -t nancy-cloudflared-update "updated tunnel image to $new_id"
        exit 0
    fi
    sleep 10
done

logger -t nancy-cloudflared-update "new tunnel failed health check; rolling back to $old_id"
docker tag "$ROLLBACK_IMAGE" "$IMAGE"
docker compose up -d --no-deps --force-recreate tunnel
exit 1

