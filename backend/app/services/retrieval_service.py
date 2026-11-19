
import re
import math

from qdrant_client.models import Filter, FieldCondition, MatchValue

from backend.app.services.embedding_service import generate_embeddings
from backend.app.services.qdrant_service import (
    get_qdrant_client,
    COLLECTION_NAME
)


STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "of", "in", "on", "at", "to", "for", "and",
    "or", "me", "my", "i", "we", "our", "you",
    "each", "all", "give", "show", "tell", "what",
    "which", "please", "can", "could", "would",
    "get", "find", "list", "display", "still",
    "about", "do", "does", "did", "any",
    "has", "have", "had", "be", "been",
    "from", "with", "by", "as", "it",
    "their", "them", "this", "that",
    "every", "of", "me", "status"
}


def tokenize(text: str) -> set[str]:
    text = text.lower().replace("_", " ")

    return {
        word for word in re.findall(r"[a-z0-9]+", text)
        if word not in STOP_WORDS
    }


def parse_structured_chunk(text: str) -> dict | None:
    """Parse pipe-separated table chunks into headers and records."""

    lines = [
        line.strip()
        for line in text.splitlines()
        if "|" in line
    ]

    if len(lines) < 2:
        return None

    headers = [
        value.strip().lower()
        for value in lines[0].split("|")
    ]

    if len(headers) < 2:
        return None

    rows = []

    for line in lines[1:]:
        values = [value.strip() for value in line.split("|")]

        if len(values) != len(headers):
            continue

        rows.append(dict(zip(headers, values)))

    if not rows:
        return None

    return {
        "headers": headers,
        "rows": rows
    }


def is_ticket_query(query: str) -> bool:
    """Identify questions intended for the ticket dataset."""

    query_lower = query.lower()

    ticket_terms = [
        "ticket",
        "ticket_id",
        "ticket id",
        "priority",
        "status",
        "open tickets",
        "resolved tickets",
        "pending approval",
        "critical tickets",
        "high priority",
        "medium priority",
        "low priority"
    ]

    return any(term in query_lower for term in ticket_terms)


def filter_ticket_records(
    query: str,
    rows: list[dict]
) -> list[dict]:
    """Apply field-aware filtering to ticket records."""

    query_lower = query.lower()

    # 1. Exact ticket ID search.
    ticket_ids = re.findall(
        r"\bT-\d+\b",
        query,
        flags=re.IGNORECASE
    )

    if ticket_ids:
        wanted = {value.upper() for value in ticket_ids}

        return [
            row for row in rows
            if row.get("ticket_id", "").upper() in wanted
        ]

    # 2. Return every ticket when the user asks for all ticket statuses.
    asks_for_all = any(
        word in query_lower
        for word in ["each", "all", "every"]
    )

    asks_for_ticket_status = (
        "status" in query_lower
        and (
            "ticket" in query_lower
            or "ticket_id" in query_lower
            or "ticket id" in query_lower
        )
    )

    if asks_for_all and asks_for_ticket_status:
        return rows

    # 3. Exact status filtering.
    # Only inspect the status column, never issue/resolution text.
    status_values = {
        "pending approval": "pending approval",
        "in progress": "in progress",
        "resolved": "resolved",
        "open": "open",
        "closed": "closed"
    }

    for phrase, value in status_values.items():
        if re.search(r"\b" + re.escape(phrase) + r"\b", query_lower):
            return [
                row for row in rows
                if row.get("status", "").strip().lower() == value
            ]

    # 4. Exact priority filtering.
    priority_values = {
        "critical": "critical",
        "high priority": "high",
        "medium priority": "medium",
        "low priority": "low"
    }

    for phrase, value in priority_values.items():
        if re.search(r"\b" + re.escape(phrase) + r"\b", query_lower):
            return [
                row for row in rows
                if row.get("priority", "").strip().lower() == value
            ]

    # 5. General issue/category matching.
    query_terms = tokenize(query)

    if not query_terms:
        return []

    scored_rows = []

    for row in rows:
        # Search meaningful record values, not column names.
        row_text = " ".join(row.values()).lower()
        row_terms = tokenize(row_text)

        matched = query_terms.intersection(row_terms)

        if matched:
            score = len(matched) / len(query_terms)
            scored_rows.append((score, row))

    scored_rows.sort(key=lambda item: item[0], reverse=True)

    if scored_rows and scored_rows[0][0] >= 0.5:
        threshold = max(0.5, scored_rows[0][0] - 0.2)

        return [
            row for score, row in scored_rows
            if score >= threshold
        ]

    return []


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    allowed_filenames: list[str] | None = None
) -> list[dict]:

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

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

    # Retrieve indexed document chunks.
    documents = []
    offset = None

    while True:
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=search_filter,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        for point in points:
            payload = point.payload or {}

            if payload.get("text"):
                documents.append({
                    "filename": payload.get("filename"),
                    "chunk_index": payload.get("chunk_index"),
                    "text": payload["text"],
                    "point_id": str(point.id)
                })

        if next_offset is None:
            break

        offset = next_offset

    if not documents:
        return []

    # Ticket-specific retrieval.
    if is_ticket_query(query):

        structured_results = []

        for document in documents:
            filename = document.get("filename") or ""

            if not filename.lower().endswith(".csv"):
                continue

            parsed = parse_structured_chunk(document["text"])

            if not parsed:
                continue

            headers = parsed["headers"]

            required_fields = {
                "ticket_id",
                "status",
                "priority"
            }

            if not required_fields.issubset(set(headers)):
                continue

            matched_rows = filter_ticket_records(
                query,
                parsed["rows"]
            )

            if not matched_rows:
                continue

            header_line = " | ".join(headers)

            result_text = "\n".join(
                [header_line] + [
                    " | ".join(row.get(header, "") for header in headers)
                    for row in matched_rows
                ]
            )

            structured_results.append({
                "filename": filename,
                "chunk_index": document["chunk_index"],
                "text": result_text,
                "similarity_score": None,
                "keyword_score": 1.0,
                "relevance_score": 1.0,
                "matched_records": len(matched_rows)
            })

        # Important: never fall back to unrelated PDFs for a
        # recognised ticket query.
        return structured_results[:top_k]

    # General semantic and lexical retrieval.
    query_embedding = generate_embeddings([query])[0]

    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()

    vector_response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=search_filter,
        limit=max(top_k * 5, 20),
        with_payload=True
    )

    vector_scores = {
        str(point.id): float(point.score)
        for point in vector_response.points
    }

    query_terms = tokenize(query)

    document_frequency = {}

    for document in documents:
        terms = tokenize(document["text"])

        for term in query_terms.intersection(terms):
            document_frequency[term] = (
                document_frequency.get(term, 0) + 1
            )

    results = []

    for document in documents:
        terms = tokenize(document["text"])
        matched = query_terms.intersection(terms)

        if query_terms:
            weights = {
                term: math.log(
                    (len(documents) + 1)
                    / (document_frequency.get(term, 0) + 1)
                ) + 1
                for term in query_terms
            }

            total_weight = sum(weights.values())

            keyword_score = (
                sum(weights[term] for term in matched) / total_weight
                if total_weight else 0
            )
        else:
            keyword_score = 0

        vector_score = vector_scores.get(
            document["point_id"], 0
        )

        relevance = (
            0.70 * keyword_score
            + 0.30 * max(0, vector_score)
        )

        if keyword_score < 0.20 and vector_score < 0.45:
            continue

        results.append({
            "filename": document["filename"],
            "chunk_index": document["chunk_index"],
            "text": document["text"],
            "similarity_score": round(vector_score, 4),
            "keyword_score": round(keyword_score, 4),
            "relevance_score": round(relevance, 4)
        })

    results.sort(
        key=lambda item: item["relevance_score"],
        reverse=True
    )

    return results[:top_k]
