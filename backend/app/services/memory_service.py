
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


# Conversation memory is stored separately from the permanent
# document knowledge base.
DATABASE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "conversation_memory.db"
)

FOLLOW_UP_MARKERS = {
    "it", "its", "they", "them", "their", "this", "that",
    "these", "those", "there", "also", "same", "again",
    "what", "why", "how", "and", "but"
}

STOP_WORDS = {
    "the", "is", "a", "an", "of", "to", "in", "on", "for",
    "and", "or", "what", "why", "how", "about", "please",
    "me", "my", "i", "you", "it", "its", "this", "that",
    "with", "from", "do", "does", "can", "could", "would"
}


def _get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(DATABASE_PATH),
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_memory():
    """Create the conversation memory table if it does not exist."""

    with _get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversation_messages
            ON conversation_messages (
                conversation_id,
                id
            )
        """)


def add_message(
    conversation_id: str,
    role: str,
    content: str
):
    """Save a message in a conversation."""

    if not conversation_id or not content:
        return

    allowed_roles = {
        "user",
        "assistant",
        "clarification"
    }

    if role not in allowed_roles:
        raise ValueError("Unsupported conversation message role.")

    initialize_memory()

    with _get_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversation_messages (
                conversation_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content.strip(),
                datetime.now(timezone.utc).isoformat()
            )
        )


def get_recent_messages(
    conversation_id: str,
    limit: int = 12
) -> list[dict]:
    """Retrieve the most recent messages from one conversation."""

    if not conversation_id:
        return []

    initialize_memory()

    with _get_connection() as connection:
        rows = connection.execute(
            """
            SELECT role, content, created_at
            FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversation_id, limit)
        ).fetchall()

    return [
        dict(row)
        for row in reversed(rows)
    ]


def _tokens(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())

    return {
        word for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


def is_follow_up(query: str) -> bool:
    """Identify questions that may depend on earlier context."""

    words = set(re.findall(r"\b[a-zA-Z]+\b", query.lower()))

    if not words:
        return False

    if words.intersection(FOLLOW_UP_MARKERS):
        return True

    # Very short questions often depend on previous context.
    if len(words) <= 4:
        return True

    return False


def get_relevant_history(
    conversation_id: str,
    query: str,
    limit: int = 8
) -> list[dict]:
    """
    Select relevant earlier messages using recent conversation
    context and simple lexical similarity.
    """

    messages = get_recent_messages(
        conversation_id,
        limit=20
    )

    if not messages:
        return []

    query_tokens = _tokens(query)

    if not query_tokens:
        return messages[-limit:]

    scored_messages = []

    for index, message in enumerate(messages):
        message_tokens = _tokens(message["content"])

        overlap = len(query_tokens.intersection(message_tokens))

        # Give more recent messages a small advantage.
        recency_bonus = index / max(len(messages), 1)

        score = overlap + recency_bonus

        if score > 0:
            scored_messages.append((score, index, message))

    scored_messages.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True
    )

    selected_indices = {
        item[1]
        for item in scored_messages[:limit]
    }

    # Keep the recent conversation sequence understandable.
    if is_follow_up(query):
        selected_indices.update(
            range(max(0, len(messages) - 4), len(messages))
        )

    return [
        message
        for index, message in enumerate(messages)
        if index in selected_indices
    ][-limit:]


def build_contextualized_query(
    query: str,
    history: list[dict]
) -> str:
    """
    Add relevant previous context to a follow-up question.
    Leave independent questions unchanged.
    """

    if not history or not is_follow_up(query):
        return query

    context_lines = []

    for message in history[-6:]:
        role = message["role"].capitalize()
        content = message["content"].strip()

        if content:
            context_lines.append(f"{role}: {content}")

    if not context_lines:
        return query

    context = "\n".join(context_lines)

    return (
        "Use the following previous conversation only to resolve "
        "references in the current question. Answer the current "
        "question, not the earlier questions.\n\n"
        f"Previous conversation:\n{context}\n\n"
        f"Current question: {query}"
    )


def copy_conversation(
    old_conversation_id: str,
    new_conversation_id: str
):
    """Copy conversation history when a clarification session
    receives a new conversation ID."""

    if not old_conversation_id or not new_conversation_id:
        return

    messages = get_recent_messages(
        old_conversation_id,
        limit=100
    )

    for message in messages:
        add_message(
            new_conversation_id,
            message["role"],
            message["content"]
        )
