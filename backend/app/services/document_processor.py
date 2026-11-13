
from backend.app.services.document_extractor import extract_text
from backend.app.services.text_chunker import (
    clean_text,
    split_text_into_chunks
)
from backend.app.services.embedding_service import generate_embeddings


def process_document(stored_filename: str) -> dict:
    """
    Extract, clean, chunk and generate embeddings
    for an uploaded document.
    """

    # Step 1: Extract text
    extracted_text = extract_text(stored_filename)

    # Step 2: Clean extracted text
    cleaned_text = clean_text(extracted_text)

    # Step 3: Generate chunks
    chunks = split_text_into_chunks(cleaned_text)

    # Step 4: Generate embeddings
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
