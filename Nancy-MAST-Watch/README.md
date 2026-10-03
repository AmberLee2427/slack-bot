# Nancy MAST watcher bundle

This directory is deliberately independent of the ICE dashboard and Nancy's
Slack implementation. Copy the whole directory into the desired container,
install its two dependencies, fill in `.env`, and invoke `watch.py` from your
own scheduler.

It does not send Slack messages or modify Nancy. When new Roman ICE calibrated
L2 images appear, it writes one atomic JSON file under `events/` for Nancy's
agent to consume later.

## Install inside the container

```bash
cd /path/to/Nancy-MAST-Watch
python -m pip install -r requirements.txt
chmod 600 .env
```

Add the authorized commissioning token to `.env`:

```dotenv
MAST_API_TOKEN=replace-with-real-token
```

Do not copy the token into an image layer or commit it.

## Test

`check` queries authenticated Roman OPS metadata without changing state:

```bash
python watch.py check
```

The first expected result is likely `awaiting_program`. Once the ICE program is
visible, the watcher discovers its PID from the authorized metadata using:

- `program_category="COM"`;
- field center RA 294.34, Dec 46.378;
- a one-degree search radius; and
- a program title matching `ice`.

If more than one program matches, it stops instead of guessing. The confirmed
PID can then be pinned as `ICE_MAST_PROGRAM` in `.env`.

## Operational poll

```bash
python watch.py poll
```

This resolves the program's datasets to MAST products and records only exact
`*_cal.asdf` filenames in `state/mast-watch.json`. Higher-level catalogs,
mosaics, and non-calibrated products do not trigger events. Previously unseen
calibrated images produce `events/mast-*.json`. Calls are protected by a file
lock so overlapping scheduler runs cannot race.

`crontab.example` contains a sample 15-minute cron entry. It is documentation
only: this bundle does not install cron, alter Docker/Compose, restart Nancy, or
make assumptions about how the container is launched.
