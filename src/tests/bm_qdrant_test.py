import os
import sys
from datetime import datetime
from types import SimpleNamespace

import argparse
import dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

dotenv.load_dotenv()

from database.connections import SECRepository
from retrieval.embeddings import Embedder
from retrieval.bmsearch import BMRetrieving
from retrieval.indexvector import VectorStorage


def test_reciprocal_rank_fusion_sorts_scores_descending():
	vector_results = [
		SimpleNamespace(payload={"chunk_id": 3}),
		SimpleNamespace(payload={"chunk_id": 1}),
	]
	bm25_results = [
		{"chunk_id": 1},
		{"chunk_id": 2},
	]

	ranked_results = BMRetrieving.reciprocal_rank_fusion(
		vector_results,
		bm25_results,
		k=0,
	)

	print("Ranked reciprocal-rank-fusion results:")
	for rank, (chunk_id, score) in enumerate(ranked_results, start=1):
		print(f"{rank}. chunk_id={chunk_id}, score={score:.4f}")

	assert ranked_results == [(1, 1.5), (3, 1.0), (2, 0.5)]


def run_hybrid_search(query, ticker, cutoff_datetime, limit):
	repository = SECRepository(
		dbname="fire_rag",
		user="fire_user",
		password=os.getenv("POSTGRESPASS"),
	)

	try:
		rows = repository.get_chunks()
		if not rows:
			print("No chunks found in the database.")
			return

		embedder = Embedder()
		vector_store = VectorStorage()
		bm25 = BMRetrieving(rows)

		query_vector = embedder.encode([query])[0]
		vector_results = vector_store.search(
			query_vector,
			ticker=ticker,
			cutoff_datetime=cutoff_datetime,
			limit=25,
		)
		bm25_results = bm25.search(
			query,
			ticker=ticker,
			cutoff_datetime=cutoff_datetime,
			limit=25,
		)
		hybrid_results = BMRetrieving.reciprocal_rank_fusion(
			vector_results,
			bm25_results,
			limit=limit,
		)

		print(f"Query: {query}")
		print(f"Ticker: {ticker}")
		print(f"Vector results: {len(vector_results)}")
		print(f"BM25 results: {len(bm25_results)}")
		print(f"Hybrid results: {len(hybrid_results)}")

		for rank, (chunk_id, score) in enumerate(hybrid_results, start=1):
			chunk = repository.get_specific_chunk(chunk_id)
			print(f"\n{rank}. Hybrid score: {score:.6f} | chunk_id: {chunk_id}")
			print(f"   {chunk['ticker']} | {chunk['filing_type']} | {chunk['section']}")
			print("   " + " ".join(chunk["text"].split())[:600])
	finally:
		repository.close()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Run a hybrid BM25 and Qdrant search")
	parser.add_argument("--query", default="What supply chain risks did Microsoft face?")
	parser.add_argument("--ticker", default="MSFT")
	parser.add_argument("--cutoff", help="Optional ISO datetime cutoff")
	parser.add_argument("--limit", type=int, default=10)
	parser.add_argument("--test", action="store_true", help="Run the local RRF sorting test")
	args = parser.parse_args()

	if args.test:
		test_reciprocal_rank_fusion_sorts_scores_descending()
		print("RRF sorting test passed")
	else:
		cutoff = datetime.fromisoformat(args.cutoff) if args.cutoff else None
		run_hybrid_search(args.query, args.ticker, cutoff, args.limit)

    
