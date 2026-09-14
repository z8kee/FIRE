import sys
import unittest
from unittest.mock import patch
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.documents import build_chunks, chunk_text


class DocumentTests(unittest.TestCase):
    def test_chunk_text_creates_overlapping_chunks(self):
        chunks = chunk_text("one two three four five six seven eight", size=4, overlap=1)

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "one two three four")
        self.assertEqual(chunks[1], "four five six seven")
        self.assertEqual(chunks[2], "seven eight")

    def test_chunk_text_rejects_invalid_overlap(self):
        with self.assertRaisesRegex(ValueError, "Overlap must be smaller"):
            chunk_text("some text", size=4, overlap=4)

    @patch("pipeline.documents.chunk_text")
    def test_build_chunks_creates_one_record_per_chunk(self, mock_chunk_text):
        mock_chunk_text.return_value = ["first chunk", "second chunk"]
        filing = {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "cik": "0000320193",
            "filing_type": "10-K",
            "filing_date": "2025-10-31",
            "accession_number": "0000320193-25-000079",
            "source_url": "https://www.sec.gov/Archives/example",
            "sections": {"mda": "filing text"},
        }

        records = build_chunks([filing])

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["section_name"], "mda")
        self.assertEqual(records[0]["chunk_index"], 0)
        self.assertEqual(records[0]["chunk_text"], "first chunk")
        self.assertEqual(records[1]["chunk_index"], 1)
        self.assertEqual(records[1]["chunk_text"], "second chunk")
        self.assertEqual(records[0]["ticker"], "AAPL")

    @patch("pipeline.documents.chunk_text", return_value=[])
    def test_build_chunks_skips_empty_sections(self, mock_chunk_text):
        filing = {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "cik": "0000320193",
            "filing_type": "10-Q",
            "filing_date": "2025-07-31",
            "accession_number": "0000320193-25-000050",
            "source_url": "https://www.sec.gov/Archives/example",
            "sections": {"mda": "", "risk_factors": ""},
        }

        self.assertEqual(build_chunks([filing]), [])


if __name__ == "__main__":
    unittest.main()
