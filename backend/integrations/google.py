from __future__ import annotations

import os
from pathlib import Path

from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from backend.models import RunSummary


class GooglePublisher:
    """Idempotent Drive/Sheets publisher using ADC/WIF without key files."""

    def __init__(self, csv_folder_id: str | None = None, json_folder_id: str | None = None,
                 spreadsheet_id: str | None = None) -> None:
        legacy_folder = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.csv_folder_id = csv_folder_id or os.getenv("GOOGLE_DRIVE_CSV_FOLDER_ID") or legacy_folder
        self.json_folder_id = json_folder_id or os.getenv("GOOGLE_DRIVE_JSON_FOLDER_ID") or legacy_folder
        self.spreadsheet_id = spreadsheet_id or os.getenv("GOOGLE_SHEETS_ID")

    @property
    def enabled(self) -> bool:
        return bool(self.csv_folder_id or self.json_folder_id or self.spreadsheet_id)

    @staticmethod
    def _upsert_drive(drive, path: Path, folder_id: str, mime: str) -> str:
        escaped = path.name.replace("'", "\\'")
        matches = drive.files().list(
            q=f"name = '{escaped}' and '{folder_id}' in parents and trashed = false",
            spaces="drive", fields="files(id,name)", pageSize=2,
        ).execute().get("files", [])
        media = MediaFileUpload(str(path), mimetype=mime, resumable=False)
        if matches:
            drive.files().update(fileId=matches[0]["id"], media_body=media, fields="id").execute()
            return "updated"
        drive.files().create(
            body={"name": path.name, "parents": [folder_id]}, media_body=media, fields="id",
        ).execute()
        return "created"

    @staticmethod
    def _row_values(record) -> list:
        payload = record.model_dump(mode="json")
        return [payload[field] if payload[field] is not None else "" for field in payload]

    def _upsert_sheet(self, sheets, summary: RunSummary) -> None:
        existing = sheets.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range="MarketData!A2:A10000"
        ).execute().get("values", [])
        row_by_id = {row[0]: index + 2 for index, row in enumerate(existing) if row}
        new_rows: list[list] = []
        for record in summary.records:
            values = [self._row_values(record)]
            if record.record_id in row_by_id:
                row_number = row_by_id[record.record_id]
                sheets.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id, range=f"MarketData!A{row_number}:T{row_number}",
                    valueInputOption="RAW", body={"values": values},
                ).execute()
            else:
                new_rows.extend(values)
        if new_rows:
            sheets.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id, range="MarketData!A:T", valueInputOption="RAW",
                insertDataOption="INSERT_ROWS", body={"values": new_rows},
            ).execute()

        run_ids = sheets.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range="執行紀錄!A2:A10000"
        ).execute().get("values", [])
        if summary.run_id not in {row[0] for row in run_ids if row}:
            sheets.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id, range="執行紀錄!A:H", valueInputOption="RAW",
                insertDataOption="INSERT_ROWS", body={"values": [[
                    summary.run_id, summary.generated_at.isoformat(), summary.trading_date.isoformat(),
                    summary.scheduled_time, summary.calendar_status.value, summary.pipeline_status,
                    len(summary.records), " | ".join(summary.warnings),
                ]]},
            ).execute()

        quality_rows = []
        for record in summary.records:
            age = ""
            if record.market_data_time:
                age = round(max(0, (summary.generated_at - record.market_data_time).total_seconds() / 60), 1)
            quality_rows.append([
                summary.generated_at.isoformat(), record.symbol, record.data_status.value,
                record.market_data_time.isoformat() if record.market_data_time else "", age,
                next((warning for warning in summary.warnings if warning.startswith(record.symbol)), ""),
            ])
        if quality_rows:
            sheets.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id, range="資料品質!A:F", valueInputOption="RAW",
                insertDataOption="INSERT_ROWS", body={"values": quality_rows},
            ).execute()

    def publish(self, csv_path: Path, json_path: Path, summary: RunSummary) -> list[str]:
        credentials, _ = default(scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets",
        ])
        messages: list[str] = []
        if self.csv_folder_id or self.json_folder_id:
            drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
            if self.csv_folder_id:
                result = self._upsert_drive(drive, csv_path, self.csv_folder_id, "text/csv")
                messages.append(f"Drive CSV {result}")
            if self.json_folder_id:
                result = self._upsert_drive(drive, json_path, self.json_folder_id, "application/json")
                messages.append(f"Drive JSON {result}")
        if self.spreadsheet_id and summary.records:
            sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
            self._upsert_sheet(sheets, summary)
            messages.append("Sheets records upserted")
        return messages
