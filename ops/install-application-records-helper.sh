#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
[[ $EUID == 0 ]] || { echo 'Run this installer with sudo' >&2; exit 1; }
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
printf '%s\n' 'nancy ALL=(root) NOPASSWD: /usr/local/sbin/nancy-watchdog-application-records ""' > "$tmp"
/usr/sbin/visudo -cf "$tmp"
install -o root -g root -m 0755 "$ROOT/ops/maintenance/application-records.py" /usr/local/sbin/nancy-watchdog-application-records
install -o root -g root -m 0440 "$tmp" /etc/sudoers.d/nancy-watchdog-application-records
