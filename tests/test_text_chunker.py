
import unittest

from backend.app.services.text_chunker import (
    clean_text,
    split_text_into_chunks,
    split_csv_into_chunks,
)


class TestTextChunker(unittest.TestCase):

    def test_clean_text_removes_extra_whitespace(self):
        text = "Hello   world.\r\n\r\n\r\nNext line."
        result = clean_text(text)

        self.assertEqual(result, "Hello world.\n\nNext line.")

    def test_clean_text_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            clean_text("   ")

    def test_chunks_respect_maximum_size(self):
        text = "This is a test document. " * 100

        chunks = split_text_into_chunks(text)

        self.assertTrue(chunks)
        self.assertTrue(all(len(chunk) <= 500 for chunk in chunks))

    def test_chunks_preserve_overlap(self):
        text = "This is a test document. " * 100

        chunks = split_text_into_chunks(text)

        for index in range(1, len(chunks)):
            self.assertEqual(
                chunks[index - 1][-100:],
                chunks[index][:100]
            )

    def test_invalid_chunk_size(self):
        with self.assertRaises(ValueError):
            split_text_into_chunks("Sample text", chunk_size=0)

    def test_invalid_overlap(self):
        with self.assertRaises(ValueError):
            split_text_into_chunks(
                "Sample text",
                chunk_size=100,
                chunk_overlap=100
            )

    def test_csv_chunks_keep_headers(self):
        text = (
            "id,status\n"
            "1,open\n"
            "2,closed\n"
            "3,pending\n"
        )

        chunks = split_csv_into_chunks(text, chunk_size=20)

        self.assertTrue(chunks)

        for chunk in chunks:
            self.assertTrue(chunk.startswith("id,status"))

    def test_csv_rejects_invalid_chunk_size(self):
        with self.assertRaises(ValueError):
            split_csv_into_chunks("id,status\n1,open", chunk_size=0)


if __name__ == "__main__":
    unittest.main()
