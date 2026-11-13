
from pathlib import Path
from pypdf import PdfReader
from docx import Document
import csv

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


def extract_text(stored_filename: str) -> str:
    file_path = UPLOAD_DIR / stored_filename

    if Path(stored_filename).name != stored_filename:
        raise ValueError("Invalid stored filename.")

    if not file_path.exists():
        raise FileNotFoundError("Uploaded document not found.")

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        reader = PdfReader(str(file_path))
        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    elif extension == ".docx":
        doc = Document(str(file_path))

        paragraphs = [p.text for p in doc.paragraphs]

        tables = [
            " | ".join(cell.text for cell in row.cells)
            for table in doc.tables
            for row in table.rows
        ]

        text = "\n".join(paragraphs + tables)

    elif extension == ".txt":
        text = file_path.read_text(
            encoding="utf-8-sig",
            errors="replace"
        )

    elif extension == ".csv":
        with open(
            file_path,
            "r",
            encoding="utf-8-sig",
            errors="replace",
            newline=""
        ) as csv_file:
            reader = csv.reader(csv_file)
            rows = [
                " | ".join(row)
                for row in reader
            ]

        text = "\n".join(rows)

    else:
        raise ValueError("Unsupported document format.")

    if not text.strip():
        raise ValueError(
            "No readable text found in this document. "
            "The PDF may be scanned or image-based."
        )

    return text
