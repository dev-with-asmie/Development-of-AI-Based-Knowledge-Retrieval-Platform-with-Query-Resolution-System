
from pathlib import Path
from uuid import uuid4

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def save_uploaded_document(filename: str, content: bytes):
    if not filename:
        raise ValueError("Filename cannot be empty.")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload PDF, DOCX, TXT or CSV.")

    if not content:
        raise ValueError("The uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File size exceeds the 20 MB limit.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a unique name to avoid filename conflicts.
    stored_filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    with open(file_path, "wb") as uploaded_file:
        uploaded_file.write(content)

    return {
        "original_filename": Path(filename).name,
        "stored_filename": stored_filename,
        "file_size": len(content),
        "file_type": extension.lstrip(".")
    }
