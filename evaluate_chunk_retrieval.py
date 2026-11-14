
from backend.app.services.retrieval_service import retrieve_relevant_chunks
from backend.app.services.qdrant_service import get_qdrant_client


ACADEMIC_FILE = "26ef2860127046bab62f4a2926ed0a5c.txt"
NETWORKING_FILE = "74646933dc2e4f0f8d806aab5c3eb47b.txt"

ALLOWED_FILES = [ACADEMIC_FILE, NETWORKING_FILE]


# Each question has a known answer-containing chunk.
test_cases = [
    {
        "domain": "Academic",
        "question": "What percentage of attendance is required for semester examinations?",
        "expected_file": ACADEMIC_FILE,
        "expected_chunk": 0
    },
    {
        "domain": "Academic",
        "question": "How many books can a student borrow from the library?",
        "expected_file": ACADEMIC_FILE,
        "expected_chunk": 2
    },
    {
        "domain": "Academic",
        "question": "How long is the standard library borrowing period?",
        "expected_file": ACADEMIC_FILE,
        "expected_chunk": 2
    },
    {
        "domain": "Academic",
        "question": "What activities are included in internal assessment?",
        "expected_file": ACADEMIC_FILE,
        "expected_chunk": 1
    },
    {
        "domain": "Academic",
        "question": "Where can students request their academic transcripts?",
        "expected_file": ACADEMIC_FILE,
        "expected_chunk": 2
    },
    {
        "domain": "Networking",
        "question": "What is the main purpose of a computer network?",
        "expected_file": NETWORKING_FILE,
        "expected_chunk": 0
    },
    {
        "domain": "Networking",
        "question": "What is the difference between LAN and WAN?",
        "expected_file": NETWORKING_FILE,
        "expected_chunk": 0
    },
    {
        "domain": "Networking",
        "question": "Which network device forwards packets between different networks?",
        "expected_file": NETWORKING_FILE,
        "expected_chunk": 1
    },
    {
        "domain": "Networking",
        "question": "Which protocol provides reliable connection-oriented communication?",
        "expected_file": NETWORKING_FILE,
        "expected_chunk": 2
    },
    {
        "domain": "Networking",
        "question": "How many bits are used in an IPv4 address?",
        "expected_file": NETWORKING_FILE,
        "expected_chunk": 2
    }
]


hit_at_1 = 0
hit_at_3 = 0
hit_at_5 = 0

domain_results = {
    "Academic": {"correct": 0, "total": 0},
    "Networking": {"correct": 0, "total": 0}
}


try:
    print("\nCHUNK-LEVEL RETRIEVAL EVALUATION")
    print("=" * 65)

    for index, test in enumerate(test_cases, start=1):

        results = retrieve_relevant_chunks(
            query=test["question"],
            top_k=5,
            allowed_filenames=ALLOWED_FILES
        )

        retrieved_chunks = [
            (result["filename"], result["chunk_index"])
            for result in results
        ]

        expected = (
            test["expected_file"],
            test["expected_chunk"]
        )

        correct_at_1 = expected in retrieved_chunks[:1]
        correct_at_3 = expected in retrieved_chunks[:3]
        correct_at_5 = expected in retrieved_chunks[:5]

        hit_at_1 += int(correct_at_1)
        hit_at_3 += int(correct_at_3)
        hit_at_5 += int(correct_at_5)

        domain_results[test["domain"]]["total"] += 1
        domain_results[test["domain"]]["correct"] += int(correct_at_1)

        print(f"\nTest {index}: {test['domain']}")
        print(f"Question: {test['question']}")
        print(
            f"Expected chunk: "
            f"{test['expected_file']} | "
            f"Chunk {test['expected_chunk']}"
        )

        print("Retrieved chunks:")

        for rank, result in enumerate(results, start=1):
            print(
                f"  Rank {rank}: "
                f"Chunk {result['chunk_index']} | "
                f"Score: {result['similarity_score']:.4f}"
            )

        print(f"Hit@1: {'PASS' if correct_at_1 else 'FAIL'}")
        print(f"Hit@3: {'PASS' if correct_at_3 else 'FAIL'}")
        print(f"Hit@5: {'PASS' if correct_at_5 else 'FAIL'}")

    total = len(test_cases)

    print("\n" + "=" * 65)
    print("FINAL CHUNK-LEVEL EVALUATION")
    print("=" * 65)

    print(f"Total questions: {total}")
    print(f"Hit@1: {hit_at_1}/{total} = {hit_at_1 / total * 100:.2f}%")
    print(f"Hit@3: {hit_at_3}/{total} = {hit_at_3 / total * 100:.2f}%")
    print(f"Hit@5: {hit_at_5}/{total} = {hit_at_5 / total * 100:.2f}%")

    print("\nDOMAIN-WISE HIT@1")

    for domain, data in domain_results.items():
        percentage = data["correct"] / data["total"] * 100

        print(
            f"{domain}: "
            f"{data['correct']}/{data['total']} = "
            f"{percentage:.2f}%"
        )

finally:
    get_qdrant_client().close()
