#!/usr/bin/python3 -I
"""Return JSON log sizes, including rotations, for fixed Nancy containers."""

import json
from pathlib import Path
import re
import subprocess
import sys

NAMES = (
    "nancy-brain-mcp",
    "nancy-slack-bot",
    "nancy-hosted-docs",
    "nancy-brain-ui",
    "nancy-tunnel",
)


def main():
    if len(sys.argv) != 1:
        sys.exit("This helper accepts no arguments")
    sizes = {}
    for name in NAMES:
        result = subprocess.run(
            ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock",
             "inspect", "--type", "container", "--format",
             '{{.Id}} {{.HostConfig.LogConfig.Type}} {{.LogPath}}', name],
            capture_output=True, text=True, timeout=10,
            env={"PATH": "/usr/bin:/bin", "HOME": "/root", "DOCKER_CONFIG": "/root/.docker"},
        )
        sizes[name] = None
        if result.returncode:
            continue
        parts = result.stdout.strip().split()
        if len(parts) != 3:
            continue
        cid, driver, path = parts
        if not re.fullmatch(r"[0-9a-f]{64}", cid) or driver != "json-file":
            continue
        expected = Path("/var/lib/docker/containers") / cid / (cid + "-json.log")
        if path != str(expected) or expected.resolve() != expected:
            continue
        try:
            sizes[name] = sum(
                entry.stat().st_size
                for entry in expected.parent.glob(expected.name + "*")
                if re.fullmatch(re.escape(expected.name) + r"(?:\.\d+(?:\.gz)?)?", entry.name)
                and not entry.is_symlink() and entry.is_file()
            ) if expected.exists() else None
        except (FileNotFoundError, PermissionError):
            pass
    print(json.dumps(sizes))


if __name__ == "__main__":
    main()
