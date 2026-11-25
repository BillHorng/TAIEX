from backend.integrations.google import GooglePublisher


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class Files:
    def __init__(self, matches):
        self.matches = matches
        self.created = 0
        self.updated = 0

    def list(self, **kwargs):
        return Request({"files": self.matches})

    def create(self, **kwargs):
        self.created += 1
        return Request({"id": "new"})

    def update(self, **kwargs):
        self.updated += 1
        return Request({"id": kwargs["fileId"]})


class Drive:
    def __init__(self, matches):
        self.service = Files(matches)

    def files(self):
        return self.service


def test_drive_publish_creates_missing_file(tmp_path) -> None:
    path = tmp_path / "market.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    drive = Drive([])
    assert GooglePublisher._upsert_drive(drive, path, "folder", "text/csv") == "created"
    assert drive.service.created == 1
    assert drive.service.updated == 0


def test_drive_publish_updates_existing_file(tmp_path) -> None:
    path = tmp_path / "market.json"
    path.write_text("{}", encoding="utf-8")
    drive = Drive([{"id": "existing", "name": path.name}])
    assert GooglePublisher._upsert_drive(drive, path, "folder", "application/json") == "updated"
    assert drive.service.updated == 1
    assert drive.service.created == 0


def test_separate_drive_destinations(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_DRIVE_CSV_FOLDER_ID", "csv")
    monkeypatch.setenv("GOOGLE_DRIVE_JSON_FOLDER_ID", "json")
    monkeypatch.setenv("GOOGLE_SHEETS_ID", "sheet")
    publisher = GooglePublisher()
    assert publisher.enabled
    assert publisher.csv_folder_id == "csv"
    assert publisher.json_folder_id == "json"
