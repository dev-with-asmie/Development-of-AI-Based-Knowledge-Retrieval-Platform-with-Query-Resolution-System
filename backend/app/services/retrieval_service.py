
from qdrant_client.models import Filter, FieldCondition, MatchValue

from backend.app.services.embedding_service import generate_embeddings
from backend.app.services.qdrant_service import (
    get_qdrant_client,
    COLLECTION_NAME
)


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    allowed_filenames: list[str] | None = None
) -> list[dict]:

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    query_embedding = generate_embeddings([query])[0]

    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()

    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        raise ValueError("Knowledge collection does not exist.")

    search_filter = None

    if allowed_filenames:
        search_filter = Filter(
            should=[
                FieldCondition(
                    key="filename",
                    match=MatchValue(value=filename)
                )
                for filename in allowed_filenames
            ]
        )

    search_response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=search_filter,
        limit=top_k,
        with_payload=True
    )

    results = []

    for point in search_response.points:
        results.append({
            "filename": point.payload.get("filename"),
            "chunk_index": point.payload.get("chunk_index"),
            "text": point.payload.get("text"),
            "similarity_score": point.score
        })

    return results
