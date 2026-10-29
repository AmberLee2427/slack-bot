#!/usr/bin/python3 -I
"""Bounded, redacted application deployment records; no user-supplied paths."""

import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path("/var/lib/nancy-maintenance/applications")
NAMES = (
    "deployed-revision", "deployed-images", "rollback.json",
    "nancy-brain-mcp.failed.log", "nancy-slack-bot.failed.log",
    "nancy-hosted-docs.failed.log", "nancy-brain-ui.failed.log",
)


def redact(text):
    text = re.sub(
        r'''(?ix)(["']?(?:authorization|[\w-]*(?:token|secret|password|api[_-]?key)[\w-]*)["']?\s*[:=]\s*)'''
        r'''(?:"[^"\n]*"|'[^'\n]*'|[^\s,;}]+(?:\s+[^\s,;}]+)?)''',
        r"\1[REDACTED]", text,
    )
    text = re.sub(r"(?i)\b(?:Bearer|Basic)\s+[^\s\"',;]+", "[REDACTED]", text)
    text = re.sub(r"(?:xox[baprs]-[\w-]+|sk-[\w-]+|gh[pousr]_[\w]+|github_pat_[\w]+|eyJ[\w.-]{20,})",
                  "[REDACTED]", text)
    return re.sub(r"(?s)-----BEGIN [^-]*PRIVATE KEY-----.*?(?:-----END [^-]*PRIVATE KEY-----|$)",
                  "[REDACTED PRIVATE KEY]", text)


def collect(root=ROOT):
    if not root.exists():
        return {"status": "No scheduled deployment record yet; use service result"}
    result = {}
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in NAMES:
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            except FileNotFoundError:
                continue
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    continue
                os.lseek(fd, max(0, info.st_size - 6000), os.SEEK_SET)
                text = os.read(fd, 6000).decode(errors="replace")
                # A bounded tail may begin midway through a secret-bearing line.
                if info.st_size > 6000:
                    text = text.partition("\n")[2]
                result[name] = {"modified": info.st_mtime, "text": redact(text)}
            finally:
                os.close(fd)
    finally:
        os.close(directory)
    return result


if __name__ == "__main__":
    if len(sys.argv) != 1:
        sys.exit("No arguments accepted")
    print(json.dumps(collect()))
