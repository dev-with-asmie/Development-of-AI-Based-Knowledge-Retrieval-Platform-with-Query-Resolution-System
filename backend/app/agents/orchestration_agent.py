import uuid

from backend.app.agents.query_understanding_agent import classify_query
from backend.app.agents.clarification_agent import generate_clarification
from backend.app.agents.retrieval_agent import retrieve_with_agent
from backend.app.agents.response_generation_agent import generate_response

from backend.app.services.clarification_service import (
    create_pending_clarification,
    get_pending_clarification,
    update_pending_clarification,
    complete_pending_clarification,
    refine_query,
)

from backend.app.services.memory_service import (
    initialize_memory,
    add_message,
    get_relevant_history,
    build_contextualized_query,
    copy_conversation,
)


def process_query(
    query: str,
    top_k: int = 5,
    allowed_filenames: list[str] | None = None,
    response_generator=None,
    conversation_id: str | None = None,
    clarification_response: str | None = None,
) -> dict:
    """
    Coordinate query understanding, clarification, memory, retrieval,
    and response generation.

    Supports new questions, contextual follow-ups, and multi-turn
    clarification exchanges.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise ValueError("top_k must be an integer.")

    if not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10.")

    if conversation_id is not None:
        if not isinstance(conversation_id, str) or not conversation_id.strip():
            raise ValueError("Invalid conversation ID.")

    normalized_query = query.strip()
    initialize_memory()

    pending = None

    # STEP 1: Resolve a clarification reply or a normal user question.
    if clarification_response is not None:
        if not conversation_id:
            raise ValueError(
                "A conversation ID is required for a clarification response."
            )

        if not isinstance(clarification_response, str):
            raise ValueError("Invalid clarification response.")

        clarification_response = clarification_response.strip()
        if not clarification_response:
            raise ValueError("Clarification response cannot be empty.")

        pending = get_pending_clarification(conversation_id)

        if pending is None:
            message = (
                "This clarification session has expired. "
                "Please submit your original question again."
            )
            return {
                "success": False,
                "status": "clarification_expired",
                "conversation_id": conversation_id,
                "query": normalized_query,
                "message": message,
                "classification": None,
                "clarification": None,
                "retrieval": None,
                "response": {
                    "status": "clarification_expired",
                    "answer": message,
                    "sources": [],
                },
            }

        original_query = pending["original_query"]

        # Combine the stored question/context with the user's clarification.
        refined_query = refine_query(
            original_query=original_query,
            clarification_response=clarification_response,
        )

        # Important: classify the complete refined question, not just
        # the short clarification reply (e.g. "why?").
        classification = classify_query(refined_query)

        add_message(
            conversation_id,
            "clarification",
            clarification_response,
        )

    else:
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        original_query = normalized_query

        history = get_relevant_history(
            conversation_id,
            normalized_query,
        )

        refined_query = build_contextualized_query(
            normalized_query,
            history,
        )

        classification = classify_query(refined_query)

        add_message(
            conversation_id,
            "user",
            normalized_query,
        )

    # STEP 2: Ask for clarification only when the complete query is unclear.
    if classification.get("requires_clarification", False):
        clarification = generate_clarification(
            query=refined_query,
            classification=classification,
        )

        if pending is not None:
            pending_data = update_pending_clarification(
                conversation_id=conversation_id,
                clarification=clarification,
            )

            if pending_data is None:
                message = (
                    "This clarification session has expired. "
                    "Please ask your question again."
                )
                return {
                    "success": False,
                    "status": "clarification_expired",
                    "conversation_id": conversation_id,
                    "query": original_query,
                    "classification": classification,
                    "clarification": None,
                    "retrieval": None,
                    "response": {
                        "status": "clarification_expired",
                        "answer": message,
                        "sources": [],
                    },
                }

            active_conversation_id = conversation_id

        else:
            pending_data = create_pending_clarification(
                original_query=refined_query,
                clarification=clarification,
            )

            active_conversation_id = pending_data["conversation_id"]

            if active_conversation_id != conversation_id:
                copy_conversation(
                    conversation_id,
                    active_conversation_id,
                )

            conversation_id = active_conversation_id

        add_message(
            conversation_id,
            "assistant",
            clarification["clarification_question"],
        )

        return {
            "success": True,
            "status": "clarification_required",
            "conversation_id": active_conversation_id,
            "query": original_query,
            "refined_query": refined_query,
            "classification": classification,
            "clarification": clarification,
            "retrieval": None,
            "response": {
                "status": "clarification_required",
                "answer": clarification["clarification_question"],
                "sources": [],
            },
        }

    # STEP 3: Retrieve evidence using the complete refined question.
    retrieval = retrieve_with_agent(
        query=refined_query,
        classification=classification,
        top_k=top_k,
        allowed_filenames=allowed_filenames,
    )

    # STEP 4: Generate an answer from the newly retrieved evidence.
    response = generate_response(
        query=refined_query,
        retrieval_result=retrieval,
        generator=response_generator,
    )

    answer = response.get("answer")
    if answer:
        add_message(
            conversation_id,
            "assistant",
            answer,
        )

    # STEP 5: Clear pending clarification only after the reply has
    # completed the retrieval/response path.
    if pending is not None:
        complete_pending_clarification(conversation_id)

    return {
        "success": response.get("success", False),
        "status": response.get("status"),
        "conversation_id": conversation_id,
        "query": original_query,
        "refined_query": refined_query,
        "classification": classification,
        "clarification": None,
        "retrieval": retrieval,
        "response": response,
    }
