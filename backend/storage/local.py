from __future__ import annotations

import csv
import json
from pathlib import Path

from backend.models import RunSummary


class LocalStorage:
    def __init__(self, output_dir: Path, public_json: Path) -> None:
        self.output_dir = output_dir
        self.public_json = public_json

    def write(self, summary: RunSummary) -> tuple[Path, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"market-{summary.trading_date}-{summary.scheduled_time.replace(':', '')}"
        json_path = self.output_dir / f"{stem}.json"
        csv_path = self.output_dir / f"{stem}.csv"
        payload = summary.model_dump(mode="json")
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        json_path.write_text(rendered + "\n", encoding="utf-8")
        self.public_json.parent.mkdir(parents=True, exist_ok=True)
        self.public_json.write_text(rendered + "\n", encoding="utf-8")
        fields = list(summary.records[0].model_dump(mode="json")) if summary.records else []
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            if fields:
                writer.writeheader()
                writer.writerows(r.model_dump(mode="json") for r in summary.records)
        return csv_path, json_path

