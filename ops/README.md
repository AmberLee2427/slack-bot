# Nancy VM maintenance

## Application security refresh

`nancy-app-update.timer` rebuilds the current committed deployment each Saturday at
02:00 Eastern using `--pull --no-cache` (including dependency installation).
Brain and UI use the same image. No KB build is run. At least 8 GiB free is required.
Import checks precede deployment; container health, authenticated HTTP
search/retrieve/tree, and public health checks follow deployment. Failures restore
previous image tags using `/var/lib/nancy-maintenance/applications/rollback.json`.
The deployment lock also excludes local health repairs and tunnel updates.
No source is pulled automatically. Dependency versions constrained by project pins
still require reviewed dependency updates. These are smoke tests, not the full CI suite.
Rollback restores images only, not database/schema changes; review migrations separately.
Rollback tags are retained deliberately and consume disk; prune older named tags
only after a subsequent successful refresh, keeping the latest recovery set.
Framework should monitor `nancy-app-update.service` and its timer alongside the
existing maintenance units. Run manually with `sudo systemctl start nancy-app-update`.

These units keep LAN access unchanged: SSH remains on the VM, and Compose continues
publishing ports 3000, 8000, and 8501 to the LAN. Cloudflare is an additional public
route, not the route used by local SSH or direct container access.

## Install

Review the schedules in `ops/systemd`, then run:

```bash
sudo ./ops/install-maintenance.sh
```

The timers provide bounded health repair, a weekly Cloudflare Tunnel update with
rollback, safe Docker cleanup, a nightly Codex process reset, and a weekly reboot only
when Ubuntu has created `/var/run/reboot-required`. Installing the timers does not
immediately reboot the VM or reset the current Codex session.

Inspect activity with:

```bash
systemctl list-timers 'nancy-*'
journalctl -u nancy-health-repair.service --since today
```

## Increase the VM disk

The guest currently has no unallocated LVM space, so the virtual disk must be enlarged
in Proxmox first. In the Proxmox UI, select the Ubuntu VM, then **Hardware**, select its
hard disk, choose **Disk Action > Resize**, and add enough space to reach roughly
50-60 GB. This does not affect LAN networking.

After Proxmox reports the larger disk, verify it and grow the guest filesystem:

```bash
lsblk
sudo growpart /dev/sda 3
sudo pvresize /dev/sda3
sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
df -h /
```

Do not run the grow commands until `lsblk` shows that `/dev/sda` is larger than the
current 32 GB. A 2-4 GB swap file can be added after expansion if model builds need a
small safety margin, but swap is not a substitute for RAM.

