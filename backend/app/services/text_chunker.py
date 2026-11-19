
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_text(text: str) -> str:
    """
    Remove unnecessary whitespace and clean extracted document text.
    """

    if not text or not text.strip():
        raise ValueError("Cannot clean empty document text.")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> list[str]:
    """
    Split ordinary documents into overlapping text chunks.
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

    return splitter.split_text(cleaned_text)


def split_csv_into_chunks(
    text: str,
    chunk_size: int = 500
) -> list[str]:
    """
    Keep CSV headers attached to their corresponding data rows.
    Each chunk contains the header and complete records.
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    cleaned_text = clean_text(text)

    lines = [
        line.strip()
        for line in cleaned_text.splitlines()
        if line.strip()
    ]

    if not lines:
        return []

    if len(lines) == 1:
        return [lines[0]]

    header = lines[0]
    chunks = []
    current_rows = []

    for row in lines[1:]:
        proposed_rows = current_rows + [row]
        proposed_chunk = "\n".join([header] + proposed_rows)

        if current_rows and len(proposed_chunk) > chunk_size:
            chunks.append(
                "\n".join([header] + current_rows)
            )
            current_rows = [row]
        else:
            current_rows.append(row)

    if current_rows:
        chunks.append(
            "\n".join([header] + current_rows)
        )

    return chunks
