"""Import anonymized log samples into the alerts table."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from teleops.db import SessionLocal
from teleops.models import Alert


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _import_records(records: list[dict], dry_run: bool) -> int:
    inserted = 0
    db = SessionLocal()
    try:
        for record in records:
            model = Alert(
                timestamp=_parse_timestamp(record.get("timestamp")),
                source_system=record.get("source_system", "unknown"),
                host=record.get("host", "unknown"),
                service=record.get("service", "unknown"),
                severity=record.get("severity", "info"),
                alert_type=record.get("alert_type", "unknown"),
                message=record.get("message", ""),
                tags=record.get("tags", {}),
                raw_payload=record.get("raw_payload", {}),
                tenant_id=record.get("tenant_id"),
            )
            if not dry_run:
                db.add(model)
            inserted += 1
        if not dry_run:
            db.commit()
    finally:
        db.close()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Import anonymized log samples into TeleOps.")
    parser.add_argument(
        "--file",
        default="docs/data_samples/anonymized_alerts.jsonl",
        help="Path to JSONL file containing anonymized alerts.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate and count records without DB writes.")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    records = _load_records(path)
    inserted = _import_records(records, args.dry_run)
    mode = "validated" if args.dry_run else "imported"
    print(f"{mode} {inserted} alert records from {path}")


if __name__ == "__main__":
    main()
