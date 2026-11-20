
from backend.app.agents.query_understanding_agent import classify_query


def _identify_clarification_type(query: str) -> str:
    """
    Identify the type of missing context in an ambiguous query.
    """

    normalized_query = " ".join(query.lower().split())
    normalized_query = normalized_query.rstrip("?!.")

    # Vague follow-up questions.
    if normalized_query in {
        "what about it",
        "tell me more",
        "explain more",
        "and then",
        "why",
        "how",
        "which one",
        "what is that",
        "is it done",
        "any update",
        "more details",
        "help me",
        "can you explain"
    }:
        return "missing_context"

    # Comparison without identifying the items.
    if normalized_query in {
        "compare them",
        "compare both",
        "compare these",
        "difference between them",
        "which is better"
    }:
        return "missing_comparison_targets"

    # Queries referring to an unspecified object or process.
    if normalized_query in {
        "how does it work",
        "how does that work",
        "what is its process",
        "what is the procedure"
    }:
        return "missing_subject"

    return "unclear_intent"


def _build_clarification_question(
    clarification_type: str
) -> str:
    """
    Generate an appropriate clarification question.
    """

    clarification_questions = {
        "missing_context": (
            "Could you provide a little more context "
            "about what you are referring to?"
        ),
        "missing_comparison_targets": (
            "Which two items, concepts, or approaches "
            "would you like me to compare?"
        ),
        "missing_subject": (
            "Which system, process, or concept "
            "would you like me to explain?"
        ),
        "unclear_intent": (
            "Could you rephrase your question or provide "
            "more details so I can understand what you need?"
        )
    }

    return clarification_questions.get(
        clarification_type,
        clarification_questions["unclear_intent"]
    )


def generate_clarification(
    query: str,
    classification: dict | None = None
) -> dict:
    """
    Generate a clarification request for ambiguous queries.

    If classification is not supplied, the Query Understanding
    Agent classifies the query automatically.
    """

    # 1. Validate input.
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    # 2. Obtain query classification.
    if classification is None:
        classification = classify_query(query)

    if not isinstance(classification, dict):
        raise ValueError(
            "Classification must be a dictionary."
        )

    query_type = classification.get("query_type")

    if query_type not in {
        "factual",
        "procedural",
        "comparative",
        "ambiguous"
    }:
        raise ValueError(
            "Unsupported query classification."
        )

    # 3. Route clear queries to retrieval.
    if not classification.get("requires_clarification", False):
        return {
            "success": True,
            "status": "ready_for_retrieval",
            "original_query": query,
            "clarification_question": None,
            "clarification_type": None,
            "requires_clarification": False
        }

    # 4. Identify missing context.
    clarification_type = _identify_clarification_type(query)

    # 5. Generate clarification question.
    clarification_question = _build_clarification_question(
        clarification_type
    )

    return {
        "success": True,
        "status": "clarification_required",
        "original_query": query,
        "clarification_question": clarification_question,
        "clarification_type": clarification_type,
        "requires_clarification": True
    }
