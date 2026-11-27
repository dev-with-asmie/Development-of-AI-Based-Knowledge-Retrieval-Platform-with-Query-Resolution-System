from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4


# Temporary storage for questions waiting for clarification.
# This is separate from the permanent document knowledge base.
_pending_clarifications = {}

_lock = Lock()

# A pending clarification expires after 30 minutes.
CLARIFICATION_TTL = timedelta(minutes=30)


def create_pending_clarification(
    original_query: str,
    clarification: dict
) -> dict:
    """
    Save a query that requires clarification.
    Returns a conversation ID that the frontend can use
    when submitting the user's clarification response.
    """
    if not isinstance(original_query, str) or not original_query.strip():
        raise ValueError("Original query cannot be empty.")

    if not isinstance(clarification, dict):
        raise ValueError("Clarification must be a dictionary.")

    conversation_id = str(uuid4())

    pending_data = {
        "conversation_id": conversation_id,
        "original_query": original_query.strip(),
        "clarification_question": clarification.get(
            "clarification_question"
        ),
        "clarification_type": clarification.get(
            "clarification_type"
        ),
        "created_at": datetime.now(timezone.utc),
    }

    with _lock:
        _pending_clarifications[conversation_id] = pending_data

    return {
        "conversation_id": conversation_id,
        "original_query": pending_data["original_query"],
        "clarification_question": pending_data["clarification_question"],
        "clarification_type": pending_data["clarification_type"],
    }


def get_pending_clarification(conversation_id: str) -> dict | None:
    """
    Retrieve a pending clarification using its conversation ID.
    Expired conversations are removed automatically.
    """
    if not isinstance(conversation_id, str) or not conversation_id.strip():
        return None

    with _lock:
        pending = _pending_clarifications.get(conversation_id)

        if pending is None:
            return None

        expires_at = pending["created_at"] + CLARIFICATION_TTL

        if datetime.now(timezone.utc) > expires_at:
            del _pending_clarifications[conversation_id]
            return None

        return dict(pending)


def update_pending_clarification(
    conversation_id: str,
    clarification: dict
) -> dict | None:
    """
    Update the pending question if another clarification is needed.
    The conversation ID remains unchanged.
    """
    with _lock:
        pending = _pending_clarifications.get(conversation_id)

        if pending is None:
            return None

        expires_at = pending["created_at"] + CLARIFICATION_TTL

        if datetime.now(timezone.utc) > expires_at:
            del _pending_clarifications[conversation_id]
            return None

        pending["clarification_question"] = clarification.get(
            "clarification_question"
        )
        pending["clarification_type"] = clarification.get(
            "clarification_type"
        )

        return {
            "conversation_id": conversation_id,
            "original_query": pending["original_query"],
            "clarification_question": pending["clarification_question"],
            "clarification_type": pending["clarification_type"],
        }


def complete_pending_clarification(conversation_id: str) -> bool:
    """
    Remove a clarification after it has been successfully processed.
    """
    with _lock:
        return _pending_clarifications.pop(conversation_id, None) is not None


def cancel_pending_clarification(conversation_id: str) -> bool:
    """
    Cancel a pending clarification.
    """
    return complete_pending_clarification(conversation_id)


def refine_query(
    original_query: str,
    clarification_response: str
) -> str:
    """
    Combine the original question with the user's clarification.
    """
    if not isinstance(original_query, str) or not original_query.strip():
        raise ValueError("Original query cannot be empty.")

    if not isinstance(clarification_response, str):
        raise ValueError("Clarification response must be text.")

    if not clarification_response.strip():
        raise ValueError("Clarification response cannot be empty.")

    return (
        f"{original_query.strip()}\n\n"
        f"Additional context provided by the user: "
        f"{clarification_response.strip()}"
    )