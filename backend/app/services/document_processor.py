
from pathlib import Path

from backend.app.services.document_extractor import extract_text
from backend.app.services.text_chunker import (
    clean_text,
    split_text_into_chunks,
    split_csv_into_chunks
)
from backend.app.services.embedding_service import generate_embeddings


def process_document(stored_filename: str) -> dict:
    """
    Extract, clean, chunk and generate embeddings
    for an uploaded document.
    """

    extracted_text = extract_text(stored_filename)
    cleaned_text = clean_text(extracted_text)

    extension = Path(stored_filename).suffix.lower()

    if extension == ".csv":
        chunks = split_csv_into_chunks(cleaned_text)
    else:
        chunks = split_text_into_chunks(cleaned_text)

    embeddings = generate_embeddings(chunks)

    return {
        "filename": stored_filename,
        "total_characters": len(cleaned_text),
        "total_chunks": len(chunks),
        "chunks": chunks,
        "embeddings": embeddings,
        "embedding_dimensions": (
            len(embeddings[0]) if embeddings else 0
        )
    }
