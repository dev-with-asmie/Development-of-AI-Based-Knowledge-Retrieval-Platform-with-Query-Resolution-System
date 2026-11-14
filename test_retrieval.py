
from backend.app.services.retrieval_service import retrieve_relevant_chunks

query = "What is the information in the uploaded document?"

results = retrieve_relevant_chunks(query, top_k=3)

print("\nRETRIEVAL RESULTS")
print("=" * 50)

if not results:
    print("No relevant results found.")

for i, result in enumerate(results, start=1):
    print(f"\nRank: {i}")
    print(f"File: {result['filename']}")
    print(f"Chunk: {result['chunk_index']}")
    print(f"Score: {result['similarity_score']:.4f}")
    print(f"Text: {result['text'][:300]}")
    print("-" * 50)
