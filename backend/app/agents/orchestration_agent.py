
from backend.app.agents.query_understanding_agent import classify_query
from backend.app.agents.clarification_agent import generate_clarification
from backend.app.agents.retrieval_agent import retrieve_with_agent
from backend.app.agents.response_generation_agent import generate_response


def process_query(
    query: str,
    top_k: int = 5,
    allowed_filenames: list[str] | None = None,
    response_generator=None
) -> dict:
    """
    Coordinate the four agents to process a user query.

    Workflow:
    1. Understand and classify the query.
    2. Request clarification if the query is ambiguous.
    3. Retrieve relevant document passages.
    4. Generate a grounded response.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise ValueError("top_k must be an integer.")

    if not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10.")

    normalized_query = query.strip()

    # Agent 1: Understand the query.
    classification = classify_query(normalized_query)

    # Agent 2: Handle ambiguous queries.
    if classification["requires_clarification"]:
        clarification = generate_clarification(
            query=normalized_query,
            classification=classification
        )

        return {
            "success": True,
            "status": "clarification_required",
            "query": normalized_query,
            "classification": classification,
            "clarification": clarification,
            "retrieval": None,
            "response": {
                "answer": clarification["clarification_question"],
                "sources": []
            }
        }

    # Agent 3: Retrieve relevant document passages.
    retrieval = retrieve_with_agent(
        query=normalized_query,
        classification=classification,
        top_k=top_k,
        allowed_filenames=allowed_filenames
    )

    # Agent 4: Generate a grounded response.
    response = generate_response(
        query=normalized_query,
        retrieval_result=retrieval,
        generator=response_generator
    )

    return {
        "success": response.get("success", False),
        "status": response.get("status"),
        "query": normalized_query,
        "classification": classification,
        "clarification": None,
        "retrieval": retrieval,
        "response": response
    }
