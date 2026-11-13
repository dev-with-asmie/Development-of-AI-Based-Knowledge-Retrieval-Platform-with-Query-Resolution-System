
from functools import lru_cache
from sentence_transformers import SentenceTransformer


# Selected embedding model from M1.1
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model once and reuse it.
    """
    return SentenceTransformer(MODEL_NAME)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Convert text chunks into numerical embedding vectors.
    """

    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Text list cannot contain empty strings.")

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return embeddings.tolist()
