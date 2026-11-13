
from functools import lru_cache
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)


# Qdrant configuration
COLLECTION_NAME = "knowledge_documents"
VECTOR_SIZE = 384

QDRANT_STORAGE_PATH = (
    Path(__file__).resolve().parents[2] / "qdrant_storage"
)


@lru_cache(maxsize=1)
def get_qdrant_client():
    """
    Create and reuse a persistent local Qdrant client.
    """

    QDRANT_STORAGE_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    return QdrantClient(
        path=str(QDRANT_STORAGE_PATH)
    )


def create_collection():
    """
    Create the document collection if it doesn't exist.
    """

    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )

    return COLLECTION_NAME


def store_embeddings(
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]]
) -> int:
    """
    Store document chunks and their embeddings in Qdrant.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks and embeddings must match."
        )

    if not chunks:
        return 0

    if any(len(vector) != VECTOR_SIZE for vector in embeddings):
        raise ValueError(
            "Every embedding must have 384 dimensions."
        )

    client = get_qdrant_client()

    create_collection()

    points = []

    for index, (chunk, vector) in enumerate(
        zip(chunks, embeddings)
    ):
        point_id = str(
            uuid5(
                NAMESPACE_URL,
                f"{filename}:{index}"
            )
        )

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "filename": filename,
                    "chunk_index": index,
                    "text": chunk
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True
    )

    return len(points)
