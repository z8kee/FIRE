import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.indexvector import VectorStorage
from src.build_index import *

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
			limit=3,
		)

def check_query():
    embedding = Embedder()
    vector_store = VectorStorage()
    db = SECRepository(dbname="fire_rag",
                    user="fire_user",
                    password=os.getenv("POSTGRESPASS"))
    
    query = "What risks does Microsoft face from its supply chain?"
    query_embedding = embedding.encode([query])[0]
    results = vector_store.search(query_embedding, ticker="MSFT", limit=10)

    for result in results:
        chunk = db.get_specific_chunk(result.payload["chunk_id"])

        print(result.score)
        print("Ticker", chunk["ticker"])
        print("Date", chunk["filing_date"])
        print("Section:", chunk["section"])
        print()
        print(chunk["text"])

if __name__ == "__main__":
	unittest.main()
	check_query()