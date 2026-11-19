
import re


# Query categories supported by the Query Understanding Agent.
QUERY_TYPES = {
    "factual",
    "procedural",
    "comparative",
    "ambiguous"
}


# Expressions that indicate a comparison.
COMPARATIVE_PATTERNS = [
    r"\bcompare\b",
    r"\bcomparison\b",
    r"\bdifference between\b",
    r"\bdiffer(?:ence|ent)\b",
    r"\bversus\b",
    r"\bvs\.?\b",
    r"\bbetter than\b",
    r"\bworse than\b",
    r"\bhigher than\b",
    r"\blower than\b",
    r"\bmore than\b",
    r"\bless than\b",
    r"\bmost\b",
    r"\bleast\b",
    r"\bsimilarit(?:y|ies)\b",
]


# Expressions that indicate a request for instructions or a process.
PROCEDURAL_PATTERNS = [
    r"\bhow do i\b",
    r"\bhow can i\b",
    r"\bhow to\b",
    r"\bsteps to\b",
    r"\bstep[- ]by[- ]step\b",
    r"\bprocedure\b",
    r"\bprocess for\b",
    r"\bworkflow\b",
    r"\binstructions\b",
    r"\bguide\b",
    r"\bconfigure\b",
    r"\binstall\b",
    r"\bsubmit\b",
    r"\bcreate\b",
    r"\btroubleshoot\b",
    r"\bresolve\b",
    r"\bwhat should i do\b",
]


# Expressions that indicate a request for information.
FACTUAL_PATTERNS = [
    r"\bwhat\b",
    r"\bwho\b",
    r"\bwhen\b",
    r"\bwhere\b",
    r"\bwhich\b",
    r"\bhow many\b",
    r"\bhow much\b",
    r"\bstatus\b",
    r"\blist\b",
    r"\bshow\b",
    r"\bfind\b",
    r"\bidentify\b",
    r"\bcount\b",
    r"\bdefine\b",
    r"\bmeaning\b",
    r"\bgive me\b",
    r"\btell me\b",
]


# Follow-up questions that do not provide enough context.
AMBIGUOUS_PHRASES = {
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
    "can you explain",
}


def _matches_patterns(query: str, patterns: list[str]) -> list[str]:
    """Return the patterns that match the query."""

    return [
        pattern
        for pattern in patterns
        if re.search(pattern, query, flags=re.IGNORECASE)
    ]


def classify_query(query: str) -> dict:
    """
    Classify a user query into factual, procedural,
    comparative, or ambiguous.

    Confidence values are heuristic estimates based on
    explicit rule matches. They are not calibrated probabilities.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    normalized_query = " ".join(query.lower().split())
    normalized_query = re.sub(r"[?!.]+$", "", normalized_query).strip()

    # 1. Detect vague follow-up questions.
    if normalized_query in AMBIGUOUS_PHRASES:
        query_type = "ambiguous"
        confidence = 0.95
        matched_rules = ["vague_follow_up"]

    # 2. Detect questions that do not contain enough context.
    elif (
        len(normalized_query.split()) <= 2
        and not re.search(r"\bT-\d+\b", normalized_query)
    ):
        query_type = "ambiguous"
        confidence = 0.85
        matched_rules = ["insufficient_query_context"]

    else:
        comparative_matches = _matches_patterns(
            normalized_query,
            COMPARATIVE_PATTERNS
        )

        procedural_matches = _matches_patterns(
            normalized_query,
            PROCEDURAL_PATTERNS
        )

        factual_matches = _matches_patterns(
            normalized_query,
            FACTUAL_PATTERNS
        )

        # 3. Comparative intent takes priority.
        if comparative_matches:
            query_type = "comparative"
            confidence = 0.95
            matched_rules = comparative_matches

        # 4. Procedural intent.
        elif procedural_matches:
            query_type = "procedural"
            confidence = 0.90
            matched_rules = procedural_matches

        # 5. Factual intent.
        elif factual_matches:
            query_type = "factual"
            confidence = 0.90
            matched_rules = factual_matches

        # 6. Unrecognised intent needs clarification.
        else:
            query_type = "ambiguous"
            confidence = 0.55
            matched_rules = ["no_clear_intent_pattern"]

    requires_clarification = query_type == "ambiguous"

    return {
        "original_query": query,
        "normalized_query": normalized_query,
        "query_type": query_type,
        "classification_confidence": confidence,
        "routing": (
            "clarification"
            if requires_clarification
            else "retrieval"
        ),
        "requires_clarification": requires_clarification,
        "matched_rules": matched_rules
    }
