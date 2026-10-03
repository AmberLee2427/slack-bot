#!/usr/bin/env python3
"""Poll Roman MAST and deliver each unnotified event through Nancy on Slack."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from slack_sdk import WebClient

import watch


ROOT = Path(__file__).resolve().parent
EVENT_DIR = ROOT / "events"
LEDGER_PATH = ROOT / "state" / "notified.json"
ANALYSIS_URL = "https://roman.science.stsci.edu/hub/user-redirect/ice-dashboard/dashboard?page=run-analysis"


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return fallback


def save_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def alert_text(event: dict[str, Any]) -> str:
    datasets = event.get("new_datasets", [])
    identifiers = [
        str(item.get("filename") or item.get("fileSetName") or "unknown")
        for item in datasets
    ]
    shown = identifiers[:10]
    lines = [
        ":new: *New Data Alert — Roman ICE commissioning*",
        f"MAST program: `{event.get('program')}`",
        f"New `_cal.asdf` images: *{event.get('new_count', len(identifiers))}*",
        f"Detected: `{event.get('checked_at', 'unknown')}`",
    ]
    if shown:
        lines.append("\n" + "\n".join(f"• `{value}`" for value in shown))
    if len(identifiers) > len(shown):
        lines.append(f"• …and {len(identifiers) - len(shown)} more")
    lines.append("\nPlease start the Nexus server and trigger the analysis workflow.")
    return "\n".join(lines)


def alert_blocks(event: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": alert_text(event)},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Open ICE Analysis Dashboard"},
                    "url": ANALYSIS_URL,
                    "style": "primary",
                    "action_id": "open_ice_analysis_dashboard",
                    "accessibility_label": "Open the ICE dashboard to launch the analysis and alert pipeline",
                }
            ],
        },
    ]


def notify_pending() -> dict[str, Any]:
    load_dotenv(ROOT / ".env", override=False)
    recipients = [value.strip() for value in os.getenv("MAST_ALERT_USER_IDS", "").split(",") if value.strip()]
    if not recipients:
        raise RuntimeError("MAST_ALERT_USER_IDS is empty")
    token = os.getenv("SLACK_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN is unavailable")

    client = WebClient(token=token)
    ledger = load_json(LEDGER_PATH, {"version": 1, "events": {}})
    event_status = ledger.setdefault("events", {})
    sent_now = 0
    for event_path in sorted(EVENT_DIR.glob("mast-*.json")):
        event = load_json(event_path, {})
        delivered = set(event_status.get(event_path.name, []))
        for recipient in recipients:
            if recipient in delivered:
                continue
            response = client.chat_postMessage(
                channel=recipient,
                text=alert_text(event),
                blocks=alert_blocks(event),
                unfurl_links=False,
            )
            if response.get("ok") is not True:
                raise RuntimeError(f"Slack rejected alert for {recipient}: {response.get('error', 'unknown error')}")
            delivered.add(recipient)
            event_status[event_path.name] = sorted(delivered)
            save_json(LEDGER_PATH, ledger)
            sent_now += 1
    return {"status": "ok", "notifications_sent": sent_now, "tracked_events": len(event_status)}


def validate_slack() -> dict[str, Any]:
    load_dotenv(ROOT / ".env", override=False)
    recipients = [value.strip() for value in os.getenv("MAST_ALERT_USER_IDS", "").split(",") if value.strip()]
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    auth = client.auth_test()
    users = []
    for recipient in recipients:
        response = client.users_info(user=recipient)
        user = response["user"]
        users.append({"id": recipient, "name": user.get("real_name") or user.get("name")})
    return {"ok": True, "team": auth.get("team"), "bot": auth.get("user"), "recipients": users}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="query MAST without committing state or sending Slack")
    parser.add_argument("--validate-slack", action="store_true", help="verify Nancy and recipient IDs without sending")
    args = parser.parse_args()
    try:
        if args.validate_slack:
            print(json.dumps(validate_slack(), indent=2, sort_keys=True))
            return 0
        if args.check_only:
            print(json.dumps(watch.execute("check"), indent=2, sort_keys=True))
            return 0
        report = watch.execute("poll")
        result = notify_pending()
        print(json.dumps({"mast": report, "slack": result}, indent=2, sort_keys=True))
        return 0
    except Exception as error:
        print(json.dumps({"status": "error", "error": str(error)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
