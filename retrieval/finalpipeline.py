import os

class RetrievalPipeline:
    def __init__(self, db, parser, embedder, vector_store, bm25, reranker):
        self.db = db
        self.parser = parser
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25 = bm25
        self.reranker = reranker

    def search(self, query, final_limit=6):
        params = self.parser.parse(query)
        tickers = params["tickers"]
        cutoff = params["cutoff_datetime"]

        query_vector = self.embedder.encode([query])[0]

        vector_results = self.vector_store.search(
            query_vector,
            tickers=tickers,
            cutoff_datetime=cutoff,
            limit=30
        )

        bm25_results = self.bm25.search(
            query,
            tickers=tickers,
            cutoff_datetime=cutoff,
            limit=30
        )

        hybrid_results = self.bm25.reciprocal_rank_fusion(
            vector_results,
            bm25_results,
            limit=30
        )

        candidates = []
        for chunk_id, hybrid_score in hybrid_results:
            chunk = self.db.get_specific_chunk(chunk_id)
            if chunk is None: continue

            candidates.append({
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "ticker": chunk["ticker"],
                "section": chunk["section"],
                "filing_type": chunk["filing_type"],
                "filing_date": chunk["filing_date"],
                "hybrid_score": hybrid_score
            })

            final_results = self.reranker.rerank(query,
                                                 candidates,
                                                 limit=final_limit
            )

            return {"query": query,
                    "tickers": tickers,
                    "cutoff_datetime": cutoff,
                    "results": final_results}

