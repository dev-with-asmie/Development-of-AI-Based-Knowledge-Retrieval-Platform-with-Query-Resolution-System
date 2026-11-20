
from backend.app.agents.clarification_agent import generate_clarification


def test_vague_follow_up():
    """Test clarification for a vague follow-up query."""

    result = generate_clarification("What about it?")

    assert result["success"] is True
    assert result["status"] == "clarification_required"
    assert result["requires_clarification"] is True
    assert result["clarification_type"] == "missing_context"
    assert result["clarification_question"] is not None

    print("PASS: Vague follow-up clarification.")


def test_missing_comparison_targets():
    """Test clarification when comparison targets are missing."""

    result = generate_clarification("Compare them.")

    assert result["success"] is True
    assert result["status"] == "clarification_required"
    assert result["clarification_type"] == "missing_comparison_targets"
    assert "which two items" in result["clarification_question"].lower()

    print("PASS: Missing comparison targets handled.")


def test_missing_subject():
    """Test clarification when the subject is unspecified."""

    result = generate_clarification("How does it work?")

    assert result["success"] is True
    assert result["status"] == "clarification_required"
    assert result["clarification_type"] == "missing_subject"
    assert "which system" in result["clarification_question"].lower()

    print("PASS: Missing subject handled.")


def test_unclear_intent():
    """Test clarification for an unrecognised ambiguous query."""

    result = generate_clarification(
        "Something about the previous topic, maybe."
    )

    assert result["success"] is True
    assert result["status"] == "clarification_required"
    assert result["clarification_type"] == "unclear_intent"

    print("PASS: Unclear intent handled.")


def test_clear_factual_query():
    """Test that a clear factual query proceeds to retrieval."""

    result = generate_clarification(
        "What is a computer network?"
    )

    assert result["success"] is True
    assert result["status"] == "ready_for_retrieval"
    assert result["requires_clarification"] is False
    assert result["clarification_question"] is None

    print("PASS: Clear factual query routed to retrieval.")


def test_clear_procedural_query():
    """Test that a clear procedural query proceeds to retrieval."""

    result = generate_clarification(
        "How do I configure a network?"
    )

    assert result["success"] is True
    assert result["status"] == "ready_for_retrieval"
    assert result["requires_clarification"] is False

    print("PASS: Clear procedural query routed to retrieval.")


def test_classification_input():
    """Test that a supplied classification is accepted."""

    classification = {
        "query_type": "ambiguous",
        "requires_clarification": True
    }

    result = generate_clarification(
        "Tell me more.",
        classification
    )

    assert result["success"] is True
    assert result["status"] == "clarification_required"

    print("PASS: Existing classification accepted.")


def test_invalid_classification():
    """Test handling of an unsupported classification."""

    try:
        generate_clarification(
            "What is a network?",
            {"query_type": "unsupported"}
        )
    except ValueError as error:
        assert "Unsupported query classification" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for unsupported classification."
        )

    print("PASS: Invalid classification rejected.")


def test_empty_query():
    """Test validation of an empty query."""

    try:
        generate_clarification("")
    except ValueError as error:
        assert "Query cannot be empty" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for empty query."
        )

    print("PASS: Empty query rejected.")


def test_invalid_classification_type():
    """Test validation when classification is not a dictionary."""

    try:
        generate_clarification(
            "What is a network?",
            classification="ambiguous"
        )
    except ValueError as error:
        assert "Classification must be a dictionary" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for invalid classification type."
        )

    print("PASS: Invalid classification type rejected.")


def run_tests():
    tests = [
        test_vague_follow_up,
        test_missing_comparison_targets,
        test_missing_subject,
        test_unclear_intent,
        test_clear_factual_query,
        test_clear_procedural_query,
        test_classification_input,
        test_invalid_classification,
        test_empty_query,
        test_invalid_classification_type
    ]

    passed = 0
    failed = 0

    print("\n========== M2.4 CLARIFICATION AGENT TESTS ==========\n")

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as error:
            failed += 1
            print(f"FAIL: {test.__name__}")
            print(f"Reason: {error}\n")

    total = len(tests)

    print("\n========== TEST SUMMARY ==========")
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("Test execution success: 100.00%")
    else:
        print(
            f"Test execution success: "
            f"{(passed / total) * 100:.2f}%"
        )


if __name__ == "__main__":
    run_tests()
