
from backend.app.agents.query_understanding_agent import classify_query
from backend.app.agents.retrieval_agent import retrieve_with_agent


TEST_QUERIES = [
    # Ticket Management
    ("Which tickets are still open?", "factual", "T-503"),
    ("Show me all critical priority tickets", "factual", "T-506"),
    ("Give me the status of each ticket_id", "factual", "ALL_TICKETS"),

    # General Documents and Procedures
    ("How can I resolve the network issue?", "procedural", "NETWORK"),
    ("What is a computer network?", "factual", "COMPUTER_NETWORK"),
    ("How do I follow the documented procedure?", "procedural", "PROCEDURE"),
    ("Compare the two approaches discussed in the document", "comparative", "COMPARISON"),

    # Unavailable information
    ("What is the population of Mars?", "factual", "NO_RESULTS"),
]


def verify_result(result, expected):
    combined_text = " ".join(
        item.get("text", "")
        for item in result.get("results", [])
    ).lower()

    if expected == "T-503":
        assert "t-503" in combined_text
        assert "corporate ssid" in combined_text

    elif expected == "T-506":
        assert "t-506" in combined_text
        assert "critical" in combined_text

    elif expected == "ALL_TICKETS":
        for ticket_id in [
            "T-501", "T-502", "T-503",
            "T-504", "T-505", "T-506"
        ]:
            assert ticket_id.lower() in combined_text, (
                f"Missing ticket: {ticket_id}"
            )

    elif expected == "NETWORK":
        assert "t-503" in combined_text
        assert "corporate ssid" in combined_text

    elif expected == "COMPUTER_NETWORK":
        assert "interconnected devices" in combined_text

    elif expected == "PROCEDURE":
        assert result["results_count"] > 0
        assert (
            "readme" in combined_text
            or "fastapi" in combined_text
            or "procedure" in combined_text
        )

    elif expected == "COMPARISON":
        assert "ai vs me" in combined_text or "compare" in combined_text

    elif expected == "NO_RESULTS":
        assert result["status"] == "no_relevant_results"
        assert result["results_count"] == 0

    # Check semantic thresholds for results with semantic scores.
    for item in result.get("results", []):
        similarity = item.get("similarity_score")

        if similarity is not None:
            assert similarity >= result["minimum_similarity_score"], (
                "A result below the semantic threshold was returned."
            )


def run_tests():
    print("\n========== M2.2 RETRIEVAL AGENT TESTS ==========\n")

    passed = 0
    failed = 0

    for index, (query, expected_type, expected_content) in enumerate(
        TEST_QUERIES, start=1
    ):
        print(f"\nTest {index}: {query}")

        try:
            classification = classify_query(query)

            assert classification["query_type"] == expected_type, (
                f"Expected query type {expected_type}, "
                f"got {classification['query_type']}"
            )

            result = retrieve_with_agent(
                query=query,
                classification=classification,
                top_k=5
            )

            verify_result(result, expected_content)

            print("Query type:", result["query_type"])
            print("Status:", result["status"])
            print("Results:", result["results_count"])
            print(
                "Retrieval confidence:",
                result["retrieval_confidence"]
            )

            print("PASS: Expected retrieval behaviour verified.")
            passed += 1

        except Exception as error:
            print("FAIL:", str(error))
            failed += 1

    total = len(TEST_QUERIES)

    print("\n========== TEST SUMMARY ==========")
    print("Total tests:", total)
    print("Passed:", passed)
    print("Failed:", failed)
    print(f"Test execution success: {(passed / total) * 100:.2f}%")


if __name__ == "__main__":
    run_tests()
