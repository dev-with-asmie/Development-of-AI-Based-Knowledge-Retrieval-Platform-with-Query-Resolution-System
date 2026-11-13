
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_text(text: str) -> str:
    """
    Remove unnecessary whitespace and clean extracted document text.
    """

    if not text or not text.strip():
        raise ValueError("Cannot clean empty document text.")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> list[str]:
    """
    Split cleaned text into smaller overlapping chunks.
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be non-negative and smaller than chunk size."
        )

    cleaned_text = clean_text(text)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    chunks = splitter.split_text(cleaned_text)

    return chunks
