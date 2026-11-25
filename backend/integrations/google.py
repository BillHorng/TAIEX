from __future__ import annotations

import os
from pathlib import Path

from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from backend.models import RunSummary


class GooglePublisher:
    """Publishes artifacts using ADC/WIF; no credential JSON is read by the app."""

    def __init__(self, folder_id: str | None = None, spreadsheet_id: str | None = None) -> None:
        self.folder_id = folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.spreadsheet_id = spreadsheet_id or os.getenv("GOOGLE_SHEETS_ID")

    @property
    def enabled(self) -> bool:
        return bool(self.folder_id or self.spreadsheet_id)

    def publish(self, csv_path: Path, json_path: Path, summary: RunSummary) -> list[str]:
        credentials, _ = default(scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets",
        ])
        messages: list[str] = []
        if self.folder_id:
            drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
            for path, mime in ((csv_path, "text/csv"), (json_path, "application/json")):
                drive.files().create(
                    body={"name": path.name, "parents": [self.folder_id]},
                    media_body=MediaFileUpload(str(path), mimetype=mime, resumable=False), fields="id",
                ).execute()
            messages.append("Drive artifacts uploaded")
        if self.spreadsheet_id and summary.records:
            sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
            header = list(summary.records[0].model_dump(mode="json"))
            values = [[str(row.model_dump(mode="json")[field] or "") for field in header] for row in summary.records]
            sheets.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id, range="MarketData!A1", valueInputOption="RAW",
                insertDataOption="INSERT_ROWS", body={"values": values},
            ).execute()
            messages.append("Sheets rows appended")
        return messages

