#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
[[ $EUID == 0 ]] || { echo 'Run this installer with sudo' >&2; exit 1; }
# Hold both generations of the lock while migrating. Never unlink a live lock.
if [[ -e /run/lock/nancy-deployment.lock ]]; then
    exec 7</run/lock/nancy-deployment.lock
    flock -n 7 || { echo 'Maintenance is active; retry installation later' >&2; exit 1; }
fi
install -d -o root -g root -m 0755 /run/nancy-maintenance
exec 8>>/run/nancy-maintenance/deployment.lock
flock -n 8 || { echo 'Maintenance is active; retry installation later' >&2; exit 1; }
chown root:root /run/nancy-maintenance/deployment.lock
chmod 0600 /run/nancy-maintenance/deployment.lock
install -m 0755 "$ROOT/ops/maintenance/update-applications.sh" /usr/local/sbin/nancy-update-applications
install -m 0755 "$ROOT/ops/maintenance/health-repair.sh" /usr/local/sbin/nancy-health-repair
install -m 0755 "$ROOT/ops/maintenance/update-cloudflared.sh" /usr/local/sbin/nancy-update-cloudflared
install -m 0755 "$ROOT/ops/maintenance/reset-codex-session.sh" /usr/local/sbin/nancy-reset-codex-session
install -m 0755 "$ROOT/ops/maintenance/docker-cleanup.sh" /usr/local/sbin/nancy-docker-cleanup
install -m 0755 "$ROOT/ops/maintenance/reboot-if-required.sh" /usr/local/sbin/nancy-reboot-if-required
install -m 0644 "$ROOT"/ops/systemd/*.service "$ROOT"/ops/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now \
    nancy-app-update.timer \
    nancy-health-repair.timer \
    nancy-cloudflared-update.timer \
    nancy-codex-reset.timer \
    nancy-docker-cleanup.timer \
    nancy-reboot-if-required.timer
systemctl list-timers 'nancy-*' --no-pager

