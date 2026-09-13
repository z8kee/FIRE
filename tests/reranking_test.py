import os
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import argparse
import dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

dotenv.load_dotenv()

from database.connections import SECRepository
from retrieval.embeddings import Embedder
from retrieval.bmsearch import BMRetrieving
from retrieval.indexvector import VectorStorage
from retrieval.reranker import Reranker

def run_hybrid_search(query, ticker, cutoff_datetime):
    db = SECRepository(
            dbname="fire_rag",
            user="fire_user",
            password=os.getenv("POSTGRESPASS"),
        )

    try:
        rows = db.get_chunks()
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
            limit=30,
        )
        bm25_results = bm25.search(
            query,
            ticker=ticker,
            cutoff_datetime=cutoff_datetime,
            limit=30,
        )
        hybrid_results = BMRetrieving.reciprocal_rank_fusion(
            vector_results,
            bm25_results,
            limit=30,
        )

        candidates = []

        for chunk_id, hybrid_score in hybrid_results:
            chunk = db.get_specific_chunk(chunk_id)

            candidates.append({
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "ticker": chunk["ticker"],
                "section": chunk["section"],
                "filing_type": chunk["filing_type"],
                "filing_date": chunk["filing_date"],
                "hybrid_score": hybrid_score
            })
    finally:
        db.close()

    reranking = Reranker()
    final_results = reranking.rerank(query, candidates, limit=10)
    print("\n--- DENSE ---")

    for result in vector_results[:5]:
        print(
            result.score,
            result.payload["chunk_id"]
        )

    print("\n--- BM25 ---")

    for result in bm25_results[:5]:
        print(
            result["score"],
            result["chunk_id"]
        )

    print("\n--- HYBRID ---")

    for result in hybrid_results[:10]:
        print(result)

    print("\n--- FINAL RERANKING ---")
    
    for result in final_results:
        print(
            "\n",
            result["rerank_score"],
            result["chunk_id"],
            result["filing_date"],
            result["section"]
        )

        print(result["text"][:500])

if __name__ == "__main__":
    run_hybrid_search(
        "How did Netflix describe competition for streaming subscribers?",
        "NFLX",
        datetime(2022, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        )