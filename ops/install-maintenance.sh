#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
install -m 0755 "$ROOT/ops/maintenance/health-repair.sh" /usr/local/sbin/nancy-health-repair
install -m 0755 "$ROOT/ops/maintenance/update-cloudflared.sh" /usr/local/sbin/nancy-update-cloudflared
install -m 0755 "$ROOT/ops/maintenance/reset-codex-session.sh" /usr/local/sbin/nancy-reset-codex-session
install -m 0755 "$ROOT/ops/maintenance/docker-cleanup.sh" /usr/local/sbin/nancy-docker-cleanup
install -m 0755 "$ROOT/ops/maintenance/reboot-if-required.sh" /usr/local/sbin/nancy-reboot-if-required
install -m 0644 "$ROOT"/ops/systemd/*.service "$ROOT"/ops/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now \
    nancy-health-repair.timer \
    nancy-cloudflared-update.timer \
    nancy-codex-reset.timer \
    nancy-docker-cleanup.timer \
    nancy-reboot-if-required.timer
systemctl list-timers 'nancy-*' --no-pager

