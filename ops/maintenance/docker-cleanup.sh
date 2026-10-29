#!/usr/bin/env bash
set -Eeuo pipefail

usage=$(df --output=pcent / | tail -1 | tr -dc '0-9')
if (( usage >= 80 )); then
    logger -p user.warning -t nancy-disk "root filesystem is ${usage}% full"
fi

# Untagged objects and old build cache are safe to remove; named rollback images remain.
docker image prune -f
docker builder prune -f --filter until=168h

