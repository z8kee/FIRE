import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime, timezone

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_ROOT):
	if str(path) not in sys.path:
		sys.path.insert(0, str(path))

from retrieval.indexvector import VectorStorage
from retrieval.query_parser import QueryParser
from scripts.build_index import *

class VectorIndexingTests(unittest.TestCase):
	@patch("retrieval.indexvector.QdrantClient")
	def test_search_queries_qdrant_and_returns_points(self, mock_qdrant_client):
		client = mock_qdrant_client.return_value
		client.collection_exists.return_value = True
		expected_points = [SimpleNamespace(id=1, score=0.95)]
		client.query_points.return_value.points = expected_points

		vector_store = VectorStorage(collection_name="test_sec_chunks")
		query_vector = np.zeros(384, dtype=np.float32)
		results = vector_store.search(query_vector, limit=3)

		self.assertEqual(results, expected_points)
		client.query_points.assert_called_once_with(
			collection_name="test_sec_chunks",
			query=query_vector.tolist(),
			query_filter=None,
			limit=3,
		)

def check_query():
	embedding = Embedder()
	vector_store = VectorStorage()
	db = SECRepository(dbname="fire_rag",
					user="fire_user",
					password=os.getenv("POSTGRESPASS"))
	parsing = QueryParser(db.get_companies())

	query = "What was microsoft's revenue in 2023?"
	parsed = parsing.parse(query)
	query_embedding = embedding.encode([query])[0]
	results = vector_store.search(query_embedding,
							   ticker=parsed['tickers'],
							   cutoff_datetime=parsed["cutoff_datetime"],
							   limit=10)

	for result in results:
		chunk = db.get_specific_chunk(result.payload["chunk_id"])

		print("=========================")
		print(result.score)
		print("Ticker", chunk["ticker"])
		print("Date", chunk["filing_date"])
		print("Section:", chunk["section"])
		print()
		print(chunk["text"])


	cutoff = datetime(
		2022, 12, 31,
		23, 59, 59,
		tzinfo=timezone.utc
	)

	results = vector_store.search(
		query_embedding,
		ticker="MSFT",
		cutoff_datetime=cutoff,
		limit=20
	)

	for result in results:
		result_date = datetime.fromisoformat(
			result.payload[
				"acceptance_datetime"
			]
		)

		assert result_date <= cutoff

		
if __name__ == "__main__":
	# unittest.main()
	check_query()