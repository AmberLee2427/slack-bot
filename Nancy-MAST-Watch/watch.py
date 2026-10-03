#!/usr/bin/env python3
"""Authenticated Roman MAST watcher for CAR201/ICE commissioning data."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
from typing import Any, Iterator, Mapping, Sequence

from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.mast import MastMissions
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
DEFAULT_ENV = ROOT / ".env"
SELECT_COLUMNS = [
    "program",
    "program_category",
    "program_title",
    "execution_plan",
    "pass",
    "segment",
    "observation",
    "visit",
    "optical_element",
    "detector",
    "productLevel",
    "product_type",
    "exposure_start_time",
    "fileSetName",
    "target_ra",
    "target_dec",
    "ra",
    "dec",
]
CAL_PRODUCT_COLUMNS = [
    "dataset",
    "filename",
    "dataURI",
    "filters",
    "size",
    "access",
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def scalar(value: Any) -> Any:
    if getattr(value, "mask", False) is True:
        return None
    if hasattr(value, "item"):
        try:
            value = value.item()
        except ValueError:
            pass
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def table_rows(table: Any) -> list[dict[str, Any]]:
    names = set(getattr(table, "colnames", []))
    return [
        {name: scalar(row[name]) if name in names else None for name in SELECT_COLUMNS}
        for row in table
    ]


def dataset_id(row: Mapping[str, Any]) -> str:
    value = row.get("filename") or row.get("dataURI")
    if value in (None, "", "--"):
        raise ValueError("MAST _cal product is missing filename and dataURI")
    return str(value)


def program_id(row: Mapping[str, Any]) -> int:
    value = row.get("program")
    if value in (None, "", "--"):
        raise ValueError("MAST result is missing program")
    return int(value)


def configured_path(value: str, default: str) -> Path:
    path = Path(value or default).expanduser()
    return path if path.is_absolute() else ROOT / path


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 2, "program": None, "seen": []}
    state = json.loads(path.read_text())
    if state.get("version") not in {1, 2} or not isinstance(state.get("seen"), list):
        raise ValueError(f"invalid watcher state: {path}")
    return state


def save_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


@contextmanager
def lock_state(state_path: Path) -> Iterator[None]:
    lock_path = state_path.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("another MAST watcher is already running") from None
        yield


def mast_client(token: str) -> MastMissions:
    client = MastMissions(mission="roman")
    client.login(token=token, store_token=False)
    return client


def discover(client: Any) -> tuple[int | None, list[dict[str, Any]]]:
    ra = float(os.getenv("ICE_MAST_RA_DEG", "294.34"))
    dec = float(os.getenv("ICE_MAST_DEC_DEG", "46.378"))
    radius = float(os.getenv("ICE_MAST_RADIUS_DEG", "1.0"))
    pattern = re.compile(os.getenv("ICE_MAST_TITLE_PATTERN", "ice"), re.IGNORECASE)
    page_size = 5000
    max_rows = int(os.getenv("ICE_MAST_DISCOVERY_MAX_ROWS", "50000"))
    rows: list[dict[str, Any]] = []
    for offset in range(0, max_rows, page_size):
        table = client.query_criteria(
            program_category="COM",
            select_cols=SELECT_COLUMNS,
            limit=page_size,
            offset=offset,
        )
        page = table_rows(table)
        rows.extend(page)
        if len(page) < page_size:
            break
    else:
        raise RuntimeError(
            f"ICE PID discovery exceeded {max_rows} commissioning rows; "
            "increase ICE_MAST_DISCOVERY_MAX_ROWS or pin ICE_MAST_PROGRAM."
        )
    center = SkyCoord(ra * u.deg, dec * u.deg)
    matching = []
    for row in rows:
        if not pattern.search(str(row.get("program_title") or "")):
            continue
        row_ra = row.get("target_ra") if row.get("target_ra") is not None else row.get("ra")
        row_dec = row.get("target_dec") if row.get("target_dec") is not None else row.get("dec")
        if row_ra is None or row_dec is None:
            continue
        position = SkyCoord(float(row_ra) * u.deg, float(row_dec) * u.deg)
        if center.separation(position).deg <= radius:
            matching.append(row)
    programs = sorted({program_id(row) for row in matching})
    if not programs:
        return None, rows
    if len(programs) > 1:
        raise RuntimeError(
            "ICE PID discovery is ambiguous: "
            + ", ".join(str(value) for value in programs)
            + ". Set ICE_MAST_PROGRAM after confirming the correct PID."
        )
    return programs[0], matching


def query_program(client: Any, program: int) -> list[dict[str, Any]]:
    """Return only detector-level Roman L2 ``_cal.asdf`` products."""
    observations = client.query_criteria(
            program=program,
            select_cols=SELECT_COLUMNS,
            limit=50000,
        )
    products = client.get_unique_product_list(observations)
    calibrated = client.filter_products(products, file_suffix="_cal")
    observation_rows = {
        str(row.get("fileSetName")): row for row in table_rows(observations)
    }
    names = set(getattr(calibrated, "colnames", []))
    rows = []
    for row in calibrated:
        product = {
            name: scalar(row[name]) if name in names else None
            for name in CAL_PRODUCT_COLUMNS
        }
        filename = str(product.get("filename") or "")
        if not filename.lower().endswith("_cal.asdf"):
            continue
        observation = observation_rows.get(str(product.get("dataset") or ""), {})
        product.update({
            name: observation.get(name)
            for name in SELECT_COLUMNS
            if name not in product or product.get(name) is None
        })
        # Keep the existing notification contract while making the displayed
        # identity the exact calibrated file rather than a parent dataset.
        product["fileSetName"] = product.get("dataset")
        rows.append(product)
    return rows


def execute(command: str, client: Any | None = None) -> dict[str, Any]:
    load_dotenv(DEFAULT_ENV, override=False)
    token = os.getenv("MAST_API_TOKEN", "").strip()
    if not token and client is None:
        raise RuntimeError(f"MAST_API_TOKEN is missing from {DEFAULT_ENV}")

    state_path = configured_path(os.getenv("ICE_MAST_STATE", ""), "state/mast-watch.json")
    event_dir = configured_path(os.getenv("ICE_MAST_EVENT_DIR", ""), "events")
    with lock_state(state_path):
        state = load_state(state_path)
        configured = os.getenv("ICE_MAST_PROGRAM", "").strip()
        program = int(configured) if configured else state.get("program")
        mast = client or mast_client(token)

        if program is None:
            program, discovery_rows = discover(mast)
            if program is None:
                return {
                    "checked_at": now().isoformat(),
                    "status": "awaiting_program",
                    "program": None,
                    "result_count": len(discovery_rows),
                    "new_count": 0,
                    "new_datasets": [],
                    "state_committed": False,
                }
        rows = query_program(mast, int(program))

        unique = {dataset_id(row): row for row in rows}
        # Version 1 tracked parent dataset rows. Product-level identities are
        # intentionally different, so migrate by taking a silent baseline;
        # otherwise deployment would announce every historical _cal file.
        if state.get("version") == 1:
            commit = command == "poll"
            if commit:
                save_json(state_path, {
                    "version": 2,
                    "program": int(program),
                    "seen": sorted(unique),
                    "updated_at": now().isoformat(),
                })
            return {
                "checked_at": now().isoformat(),
                "status": "migrated" if commit else "migration_required",
                "program": int(program),
                "result_count": len(unique),
                "new_count": 0,
                "new_datasets": [],
                "state_committed": commit,
            }
        seen = {str(value) for value in state.get("seen", [])}
        new_ids = sorted(set(unique) - seen)
        commit = command == "poll"
        report: dict[str, Any] = {
            "checked_at": now().isoformat(),
            "status": "new_data" if new_ids else "clear",
            "program": int(program),
            "result_count": len(unique),
            "new_count": len(new_ids),
            "new_datasets": [unique[value] for value in new_ids],
            "state_committed": commit,
        }

        if commit:
            save_json(
                state_path,
                {
                    "version": 2,
                    "program": int(program),
                    "seen": sorted(unique),
                    "updated_at": report["checked_at"],
                },
            )
            if new_ids:
                stamp = now().strftime("%Y%m%dT%H%M%S%fZ")
                event_path = event_dir / f"mast-{stamp}.json"
                report["event_file"] = str(event_path)
                save_json(event_path, report)
        return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "poll"))
    args = parser.parse_args(argv)
    try:
        report = execute(args.command)
    except Exception as error:
        print(json.dumps({"status": "error", "error": str(error)}, indent=2))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
