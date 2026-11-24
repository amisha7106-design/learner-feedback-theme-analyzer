import csv
from pathlib import Path
from typing import Iterable

REQUIRED_COLUMNS = {"feedback_text"}

def validate_feedback_rows(rows: Iterable[dict]) -> list[dict]:
    cleaned = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} must be a dictionary.")
        text = str(row.get("feedback_text", "")).strip()
        if not text:
            continue
        cleaned.append({
            "feedback_text": text,
            "course_name": str(row.get("course_name", "General")).strip() or "General",
            "trainer_name": str(row.get("trainer_name", "Not specified")).strip() or "Not specified",
            "learner_id": str(row.get("learner_id", f"sample_{index}")).strip(),
            "submitted_at": str(row.get("submitted_at", "")).strip() or None,
        })
    if not cleaned:
        raise ValueError("No usable feedback found. Add a non-empty feedback_text column.")
    return cleaned

def read_csv_feedback(file_path: str | Path) -> list[dict]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "feedback_text" not in reader.fieldnames:
            raise ValueError("CSV must contain a 'feedback_text' column.")
        return validate_feedback_rows(reader)

def read_uploaded_csv(uploaded_file) -> list[dict]:
    import io
    content = uploaded_file.getvalue().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames or "feedback_text" not in reader.fieldnames:
        raise ValueError("CSV must contain a 'feedback_text' column.")
    return validate_feedback_rows(reader)
