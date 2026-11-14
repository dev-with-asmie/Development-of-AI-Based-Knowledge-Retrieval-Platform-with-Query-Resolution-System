
from qdrant_client.models import Filter, FieldCondition, MatchValue

from backend.app.services.qdrant_service import (
    get_qdrant_client,
    COLLECTION_NAME
)

ACADEMIC_FILE = "26ef2860127046bab62f4a2926ed0a5c.txt"
NETWORKING_FILE = "74646933dc2e4f0f8d806aab5c3eb47b.txt"

client = get_qdrant_client()

search_filter = Filter(
    should=[
        FieldCondition(
            key="filename",
            match=MatchValue(value=ACADEMIC_FILE)
        ),
        FieldCondition(
            key="filename",
            match=MatchValue(value=NETWORKING_FILE)
        )
    ]
)

try:
    points, next_offset = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=search_filter,
        limit=20,
        with_payload=True,
        with_vectors=False
    )

    points.sort(
        key=lambda p: (
            p.payload.get("filename", ""),
            p.payload.get("chunk_index", 0)
        )
    )

    print("\nEVALUATION DOCUMENT CHUNKS")
    print("=" * 60)

    for point in points:
        print(f"\nFile: {point.payload.get('filename')}")
        print(f"Chunk Index: {point.payload.get('chunk_index')}")
        print(f"Text:\n{point.payload.get('text')}")
        print("-" * 60)

finally:
    client.close()
