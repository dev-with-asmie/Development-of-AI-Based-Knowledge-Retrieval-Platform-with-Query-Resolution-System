
from backend.app.agents.query_understanding_agent import classify_query


# Test cases covering two knowledge domains:
# 1. Ticket Management
# 2. General Documents and Procedures

TEST_CASES = [
    # Domain 1: Ticket Management

    ("What is the status of ticket T-503?", "factual"),
    ("List all critical priority tickets", "factual"),

    ("How do I update a ticket status?", "procedural"),
    ("What are the steps to resolve an open ticket?", "procedural"),

    ("Compare critical and high priority tickets", "comparative"),
    (
        "What is the difference between open and resolved tickets?",
        "comparative"
    ),

    ("What about it?", "ambiguous"),
    ("Which one?", "ambiguous"),

    # Domain 2: General Documents and Procedures

    ("Who is responsible for updating the policy?", "factual"),
    ("When was the policy updated?", "factual"),

    ("How can I configure email notifications?", "procedural"),
    (
        "Explain the process for submitting an expense claim",
        "procedural"
    ),

    (
        "Compare the password reset procedure with account recovery",
        "comparative"
    ),
    (
        "What is the difference between the leave policy and attendance policy?",
        "comparative"
    ),

    ("Tell me more", "ambiguous"),
    ("Can you help?", "ambiguous"),
]


def run_tests():
    total = len(TEST_CASES)
    correct = 0

    print("\n========== QUERY UNDERSTANDING TESTS ==========\n")

    for index, (query, expected) in enumerate(TEST_CASES, start=1):

        try:
            result = classify_query(query)

            actual = result["query_type"]
            confidence = result["classification_confidence"]
            routing = result["routing"]

            passed = actual == expected

            if passed:
                correct += 1

            status = "PASS" if passed else "FAIL"

            print(f"Test {index}: {status}")
            print(f"Query: {query}")
            print(f"Expected: {expected}")
            print(f"Actual: {actual}")
            print(f"Confidence: {confidence}")
            print(f"Routing: {routing}")

        except Exception as error:
            print(f"Test {index}: ERROR")
            print(f"Query: {query}")
            print(f"Error: {error}")

        print("-" * 60)

    accuracy = (correct / total) * 100 if total else 0

    print("\n========== TEST SUMMARY ==========")
    print(f"Total test cases: {total}")
    print(f"Correct classifications: {correct}")
    print(f"Incorrect classifications: {total - correct}")
    print(f"Classification accuracy: {accuracy:.2f}%")
    print("==================================")


if __name__ == "__main__":
    run_tests()
