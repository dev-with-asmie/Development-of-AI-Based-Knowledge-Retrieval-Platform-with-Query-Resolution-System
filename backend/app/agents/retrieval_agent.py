
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

    # Validate query
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    # Validate classification
    if not isinstance(classification, dict):
        raise ValueError("Classification must be a dictionary.")

    # Validate top_k
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise ValueError("top_k must be an integer.")

    if top_k <= 0 or top_k > 10:
        raise ValueError("top_k must be between 1 and 10.")

    # Validate relevance threshold
    if not isinstance(min_relevance_score, (int, float)):
        raise ValueError("Minimum relevance score must be numeric.")

    if not 0 <= min_relevance_score <= 1:
        raise ValueError(
            "Minimum relevance score must be between 0 and 1."
        )

    query_type = classification.get("query_type")

    # Handle ambiguous queries
    if query_type == "ambiguous":
        return {
            "status": "clarification_required",
            "query": query,
            "query_type": query_type,
            "results": [],
            "result_count": 0,
            "confidence": 0.0
        }

    # Validate supported query type
    if query_type not in SUPPORTED_QUERY_TYPES:
        raise ValueError(
            f"Unsupported query type: {query_type}"
        )

    semantic_threshold = SEMANTIC_THRESHOLDS[query_type]

    # Retrieve more candidates before filtering
    retrieved_chunks = retrieve_relevant_chunks(
        query=query.strip(),
        top_k=top_k * 3,
        allowed_filenames=allowed_filenames
    )

    results = []

    for result in retrieved_chunks:

        relevance_score = float(
            result.get("relevance_score") or 0.0
        )

        similarity_score = result.get("similarity_score")

        # Apply minimum relevance threshold
        if relevance_score < min_relevance_score:
            continue

        # Apply semantic threshold when a semantic score exists.
        # Structured CSV records may not have a similarity score,
        # so they are evaluated using their relevance score.
        if similarity_score is not None:
            similarity_score = float(similarity_score)

            if similarity_score < semantic_threshold:
                continue

        filename = result.get("filename") or result.get("source")

        normalized_result = {
            "rank": len(results) + 1,

            # Both fields are retained for compatibility.
            "filename": filename,
            "source": filename,

            "chunk_index": result.get("chunk_index"),
            "text": result.get("text", ""),

            "similarity_score": similarity_score,
            "keyword_score": result.get("keyword_score", 0.0),
            "relevance_score": relevance_score,

            "matched_records": result.get("matched_records", 0)
        }

        results.append(normalized_result)

        if len(results) >= top_k:
            break

    # Calculate average retrieval confidence
    if results:
        confidence = sum(
            item["relevance_score"] for item in results
        ) / len(results)
    else:
        confidence = 0.0

    # Return retrieval result
    return {
        "status": (
            "retrieved"
            if results
            else "no_relevant_results"
        ),
        "query": query,
        "query_type": query_type,
        "results": results,
        "result_count": len(results),
        "confidence": round(confidence, 4),
        "thresholds": {
            "minimum_relevance_score": min_relevance_score,
            "minimum_semantic_score": semantic_threshold
        }
    }
