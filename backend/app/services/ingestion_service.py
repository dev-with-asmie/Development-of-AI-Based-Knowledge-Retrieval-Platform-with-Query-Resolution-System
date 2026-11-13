
from backend.app.services.document_processor import process_document
from backend.app.services.qdrant_service import (
    store_embeddings,
    COLLECTION_NAME
)


def ingest_document(stored_filename: str) -> dict:
    """
    Complete document ingestion pipeline:
    Extract → Clean → Chunk → Embed → Store in Qdrant.
    """

    # Step 1: Process the document
    result = process_document(stored_filename)

    # Step 2: Store embeddings in Qdrant
    vectors_stored = store_embeddings(
        filename=result["filename"],
        chunks=result["chunks"],
        embeddings=result["embeddings"]
    )

    # Step 3: Return ingestion statistics
    return {
        "success": True,
        "filename": result["filename"],
        "total_characters": result["total_characters"],
        "total_chunks": result["total_chunks"],
        "embedding_dimensions": result["embedding_dimensions"],
        "vectors_stored": vectors_stored,
        "collection": COLLECTION_NAME
    }
