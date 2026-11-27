
from functools import lru_cache
import hashlib
import re
import math

# Selected embedding model from M1.1
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

VECTOR_SIZE = 384


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the SentenceTransformer model when available.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def _fallback_embedding(text: str) -> list[float]:
    """
    Generate a deterministic 384-dimensional feature-hashing
    vector using Python's standard library.

    This fallback avoids PyTorch when Windows blocks its DLLs.
    It is not a replacement for a semantic transformer model.
    """
    vector = [0.0] * VECTOR_SIZE

    normalized = text.lower()
    tokens = re.findall(r"\b\w+\b", normalized)

    features = list(tokens)

    # Add adjacent word pairs to retain some phrase information.
    features.extend(
        f"{tokens[i]}_{tokens[i + 1]}"
        for i in range(len(tokens) - 1)
    )

    for feature in features:
        digest = hashlib.blake2b(
            feature.encode("utf-8"),
            digest_size=8
        ).digest()

        number = int.from_bytes(digest, "little")

        index = number % VECTOR_SIZE
        sign = 1.0 if (number >> 8) & 1 else -1.0

        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))

    if magnitude:
        vector = [value / magnitude for value in vector]

    return vector


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using SentenceTransformers.

    If PyTorch cannot load because of a local environment
    restriction, use deterministic feature hashing instead.
    """
    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Text list cannot contain empty strings.")

    try:
        model = get_embedding_model()

        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return embeddings.tolist()

    except Exception as error:
        print(
            "WARNING: SentenceTransformer unavailable. "
            "Using deterministic fallback embeddings."
        )
        print(f"Reason: {error}")

        return [
            _fallback_embedding(text)
            for text in texts
        ]
