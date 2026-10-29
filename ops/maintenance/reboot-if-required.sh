#!/usr/bin/env bash
set -Eeuo pipefail

if [[ -f /var/run/reboot-required ]]; then
    logger -t nancy-maintenance "reboot-required marker present; rebooting in maintenance window"
    systemctl reboot
fi

