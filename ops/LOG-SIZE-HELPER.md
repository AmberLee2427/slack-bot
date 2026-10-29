# Fixed log-size collector

Install with `sudo bash /home/nancy/slack-bot/ops/install-log-size-helper.sh`.

Invoke as Nancy: `sudo -n /usr/local/sbin/nancy-watchdog-log-sizes`.
No arguments are accepted, including through sudo. The installed helper and sudoers
rule are root-owned. Python runs in isolated mode. It reads only fixed container
metadata and returns JSON mapping the five Nancy container names to active and rotated
JSON log-file sizes in bytes. No file contents, credentials, or Docker environment
variables are returned. Null means missing container, unsupported logging driver,
or unavailable file; treat it as a coverage gap, not zero bytes.

Numbered rotations, including gzip files, are included. A command/timeout failure can exit nonzero; the
caller should capture stderr locally rather than include raw errors in alerts.
Merge the returned values into the VM snapshot's `containers[*].log_bytes` by name.
This does not grant repair permissions or change SSH, Docker, or directory access.
