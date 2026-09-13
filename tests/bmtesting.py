import argparse
import os
import sys

import dotenv

dotenv.load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.connections import SECRepository
from retrieval.bmsearch import BMRetrieving

#CHECKINg if bm25 retrieval and ranking works.
def main():
	parser = argparse.ArgumentParser(description="Test BM25 retrieval against stored SEC chunks")
	parser.add_argument("query", nargs="?", help="Text to search for", default="What is their leading risks in their supply chains?")
	parser.add_argument("--ticker", help="Only search chunks for this ticker")
	parser.add_argument("--limit", type=int, default=15, help="Maximum results to display")
	parser.add_argument("--sample", action="store_true", help="Run against built-in sample chunks")
	args = parser.parse_args()
	repository = None
	if args.sample:
		ticker = args.ticker or "ABC"
		rows = [
			{"chunk_id": 1, "text": "Revenue increased while operating costs remained stable.", "ticker": "ABC", "filing_type": "10-K", "section": "Results"},
			{"chunk_id": 2, "text": "Revenue increased significantly and net income grew during the year.", "ticker": "ABC", "filing_type": "10-K", "section": "Financial Results"},
			{"chunk_id": 3, "text": "The company expanded its manufacturing capacity in Europe.", "ticker": "XYZ", "filing_type": "10-Q", "section": "Operations"},
		]
	else:
		repository = SECRepository(
			dbname="fire_rag",
			user="fire_user",
			password=os.getenv("POSTGRESPASS"),
		)
		rows = repository.get_chunks()
		if not rows:
			print("No chunks found in the database.")
			return
		ticker = args.ticker
    
	results = BMRetrieving(rows).search(args.query, ticker=ticker, limit=args.limit)
	chunks_by_id = {row["chunk_id"]: row for row in rows}

	print(f"Query: {args.query}")
	print(f"Indexed chunks: {len(rows)}")
	print(f"Results: {len(results)}")
	for rank, result in enumerate(results, start=1):
		row = chunks_by_id[result["chunk_id"]]
		preview = " ".join(row["text"].split())[:240]
		print(f"{rank}. chunk_id={result['chunk_id']} score={result['score']:.4f}")
		print(f"   {row['ticker']} | {row['filing_type']} | {row['section']}")
		print(f"   {preview}")

	if repository is not None:
		repository.close()


if __name__ == "__main__":
	main()
