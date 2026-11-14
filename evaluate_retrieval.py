
from backend.app.services.retrieval_service import retrieve_relevant_chunks


ACADEMIC_FILE = "26ef2860127046bab62f4a2926ed0a5c.txt"
NETWORKING_FILE = "74646933dc2e4f0f8d806aab5c3eb47b.txt"


# Test questions with their expected source documents
test_cases = [
    {
        "domain": "Academic",
        "question": "What percentage of attendance is required for semester examinations?",
        "expected_file": ACADEMIC_FILE
    },
    {
        "domain": "Academic",
        "question": "How many books can a student borrow from the library?",
        "expected_file": ACADEMIC_FILE
    },
    {
        "domain": "Academic",
        "question": "How long is the standard library borrowing period?",
        "expected_file": ACADEMIC_FILE
    },
    {
        "domain": "Academic",
        "question": "What activities are included in internal assessment?",
        "expected_file": ACADEMIC_FILE
    },
    {
        "domain": "Academic",
        "question": "Where can students request their academic transcripts?",
        "expected_file": ACADEMIC_FILE
    },
    {
        "domain": "Networking",
        "question": "What is the main purpose of a computer network?",
        "expected_file": NETWORKING_FILE
    },
    {
        "domain": "Networking",
        "question": "What is the difference between LAN and WAN?",
        "expected_file": NETWORKING_FILE
    },
    {
        "domain": "Networking",
        "question": "Which network device forwards packets between different networks?",
        "expected_file": NETWORKING_FILE
    },
    {
        "domain": "Networking",
        "question": "Which protocol provides reliable connection-oriented communication?",
        "expected_file": NETWORKING_FILE
    },
    {
        "domain": "Networking",
        "question": "How many bits are used in an IPv4 address?",
        "expected_file": NETWORKING_FILE
    }
]


allowed_files = [ACADEMIC_FILE, NETWORKING_FILE]

hit_at_1 = 0
hit_at_3 = 0
hit_at_5 = 0

academic_correct = 0
networking_correct = 0

print("\nRETRIEVAL ACCURACY EVALUATION")
print("=" * 65)

for index, test in enumerate(test_cases, start=1):

    results = retrieve_relevant_chunks(
        query=test["question"],
        top_k=5,
        allowed_filenames=allowed_files
    )

    retrieved_files = [result["filename"] for result in results]

    expected = test["expected_file"]

    correct_at_1 = len(retrieved_files) >= 1 and retrieved_files[0] == expected
    correct_at_3 = expected in retrieved_files[:3]
    correct_at_5 = expected in retrieved_files[:5]

    hit_at_1 += int(correct_at_1)
    hit_at_3 += int(correct_at_3)
    hit_at_5 += int(correct_at_5)

    if correct_at_1:
        if test["domain"] == "Academic":
            academic_correct += 1
        else:
            networking_correct += 1

    print(f"\nTest {index}: {test['domain']}")
    print(f"Question: {test['question']}")
    print(f"Expected: {expected}")
    print(f"Top result: {retrieved_files[0] if retrieved_files else 'No result'}")
    print(f"Hit@1: {'PASS' if correct_at_1 else 'FAIL'}")
    print(f"Hit@3: {'PASS' if correct_at_3 else 'FAIL'}")
    print(f"Hit@5: {'PASS' if correct_at_5 else 'FAIL'}")


total = len(test_cases)

print("\n" + "=" * 65)
print("FINAL EVALUATION RESULTS")
print("=" * 65)

print(f"Total test questions: {total}")
print(f"Hit@1: {hit_at_1}/{total} = {hit_at_1 / total * 100:.2f}%")
print(f"Hit@3: {hit_at_3}/{total} = {hit_at_3 / total * 100:.2f}%")
print(f"Hit@5: {hit_at_5}/{total} = {hit_at_5 / total * 100:.2f}%")

print("\nDOMAIN-WISE TOP-1 RESULTS")
print(f"Academic: {academic_correct}/5 = {academic_correct / 5 * 100:.2f}%")
print(f"Networking: {networking_correct}/5 = {networking_correct / 5 * 100:.2f}%")
