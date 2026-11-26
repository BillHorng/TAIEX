from __future__ import annotations

import csv
import json
from pathlib import Path

from backend.models import RunSummary


class LocalStorage:
    def __init__(self, output_dir: Path, public_json: Path, history_json: Path | None = None,
                 status_json: Path | None = None) -> None:
        self.output_dir = output_dir
        self.public_json = public_json
        self.history_json = history_json or public_json.with_name("history.json")
        self.status_json = status_json or public_json.with_name("run-status.json")

    def write(self, summary: RunSummary) -> tuple[Path, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"market-{summary.trading_date}-{summary.scheduled_time.replace(':', '')}"
        json_path = self.output_dir / f"{stem}.json"
        csv_path = self.output_dir / f"{stem}.csv"
        payload = summary.model_dump(mode="json")
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        json_path.write_text(rendered + "\n", encoding="utf-8")
        self.public_json.parent.mkdir(parents=True, exist_ok=True)
        self.status_json.write_text(rendered + "\n", encoding="utf-8")
        if summary.records and summary.pipeline_status in ("SUCCESS", "PARTIAL_SUCCESS"):
            self.public_json.write_text(rendered + "\n", encoding="utf-8")
            self._update_history(summary)
        fields = list(summary.records[0].model_dump(mode="json")) if summary.records else []
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            if fields:
                writer.writeheader()
                writer.writerows(r.model_dump(mode="json") for r in summary.records)
        return csv_path, json_path

    def _update_history(self, summary: RunSummary) -> None:
        if not summary.records:
            return
        existing: dict = {"updated_at": None, "records": []}
        if self.history_json.exists():
            try:
                existing = json.loads(self.history_json.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        by_id = {row["record_id"]: row for row in existing.get("records", []) if "record_id" in row}
        by_id.update({row.record_id: row.model_dump(mode="json") for row in summary.records})
        records = sorted(by_id.values(), key=lambda row: (row["trading_date"], row["scheduled_time"], row["symbol"]))[-360:]
        history = {"updated_at": summary.generated_at.isoformat(), "records": records}
        self.history_json.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

