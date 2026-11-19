
from backend.app.services.retrieval_service import (
    retrieve_relevant_chunks
)


SUPPORTED_QUERY_TYPES = {
    "factual",
    "procedural",
    "comparative"
}

DEFAULT_MIN_RELEVANCE_SCORE = 0.20

SEMANTIC_THRESHOLDS = {
    "factual": 0.20,
    "procedural": 0.20,
    "comparative": 0.15
}


def retrieve_with_agent(
    query: str,
    classification: dict,
    top_k: int = 5,
    min_relevance_score: float = DEFAULT_MIN_RELEVANCE_SCORE,
    allowed_filenames: list[str] | None = None
) -> dict:
    """
    Retrieve and filter relevant document chunks.

    Uses the existing M1 hybrid retrieval service and
    applies additional semantic relevance filtering.
    """

    # 1. Validate inputs.
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not isinstance(classification, dict):
        raise ValueError("Classification must be a dictionary.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    if not 0 <= min_relevance_score <= 1:
        raise ValueError(
            "Minimum relevance score must be between 0 and 1."
        )

    # 2. Read classification.
    query_type = classification.get("query_type")

    if query_type == "ambiguous":
        return {
            "success": True,
            "query": query,
            "query_type": "ambiguous",
            "status": "clarification_required",
            "message": (
                "The query is ambiguous. "
                "Please clarify it before retrieval."
            ),
            "results_count": 0,
            "retrieval_confidence": 0.0,
            "results": []
        }

    if query_type not in SUPPORTED_QUERY_TYPES:
        raise ValueError(
            f"Unsupported query type: {query_type}"
        )

    min_similarity_score = SEMANTIC_THRESHOLDS[query_type]

    # 3. Retrieve extra candidates to allow filtering.
    retrieved_chunks = retrieve_relevant_chunks(
        query=query.strip(),
        top_k=top_k * 3,
        allowed_filenames=allowed_filenames
    )

    # 4. Apply relevance and semantic filtering.
    filtered_results = []

    for result in retrieved_chunks:

        relevance_score = result.get("relevance_score")
        similarity_score = result.get("similarity_score")

        if relevance_score is None:
            continue

        if relevance_score < min_relevance_score:
            continue

        # Structured CSV results have no semantic score.
        # Preserve them because they use field-aware filtering.
        if similarity_score is not None:
            if similarity_score < min_similarity_score:
                continue

        filtered_results.append({
            "rank": len(filtered_results) + 1,
            "source": result.get("filename"),
            "chunk_index": result.get("chunk_index"),
            "text": result.get("text"),
            "similarity_score": similarity_score,
            "keyword_score": result.get("keyword_score"),
            "relevance_score": relevance_score,
            "matched_records": result.get("matched_records")
        })

        if len(filtered_results) >= top_k:
            break

    # 5. Calculate aggregate retrieval confidence.
    if filtered_results:
        retrieval_confidence = round(
            sum(
                item["relevance_score"]
                for item in filtered_results
            ) / len(filtered_results),
            4
        )
    else:
        retrieval_confidence = 0.0

    # 6. Handle unavailable information.
    if not filtered_results:
        return {
            "success": True,
            "query": query,
            "query_type": query_type,
            "status": "no_relevant_results",
            "message": (
                "No sufficiently relevant document chunks "
                "were found for this query."
            ),
            "results_count": 0,
            "retrieval_confidence": 0.0,
            "minimum_relevance_score": min_relevance_score,
            "minimum_similarity_score": min_similarity_score,
            "results": []
        }

    # 7. Return structured retrieval response.
    return {
        "success": True,
        "query": query,
        "query_type": query_type,
        "status": "retrieved",
        "message": (
            "Relevant document chunks retrieved successfully."
        ),
        "results_count": len(filtered_results),
        "retrieval_confidence": retrieval_confidence,
        "minimum_relevance_score": min_relevance_score,
        "minimum_similarity_score": min_similarity_score,
        "results": filtered_results
    }
