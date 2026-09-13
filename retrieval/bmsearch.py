import re
from rank_bm25 import BM25Okapi

def tokenise(text):
    #need to tokenise, \b is word boundaries, \w+ is one or more word chars
    return re.findall(r"\b\w+\b", text.lower())

class BMRetrieving:
    def __init__(self, rows):
        #tokenise every row in a chunk then parse to bm25
        self.rows = rows
        self.tokenised_corpus = [tokenise(row["text"]) for row in rows]
        self.index = BM25Okapi(self.tokenised_corpus)

    #tokenises query to find similarites to tokenised chunks
    def search(self, query, ticker=None, cutoff_datetime=None, limit=15):
        query_tokens = tokenise(query)
        scores = self.index.get_scores(query_tokens)
        results = []

        for row, score in zip(self.rows, scores):
            if ticker is not None:
                if row["ticker"] != ticker.upper():
                    continue

            if cutoff_datetime is not None:
                acceptance_datetime = row.get("acceptance_datetime")
                if acceptance_datetime is not None and acceptance_datetime > cutoff_datetime:
                    continue

            results.append({
                "chunk_id": row["chunk_id"],
                "score": float(score),
                "source": "bm25"
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

    #fusing bm25 and qdrant vector search
    #since they're both on different scales we will use rrf, the higher the rank
    #the higher the points recieved

    def reciprocal_rank_fusion(vector_res, bm25_res, k=60, limit=15):
        scores = {}

        for rank, result in enumerate(vector_res, start=1):
            chunk_id = result.payload["chunk_id"]
            scores[chunk_id] = (scores.get(chunk_id, 0) + 1/(k+rank))

        for rank, result in enumerate(bm25_res, start=1):
            chunk_id = result["chunk_id"]
            scores[chunk_id] = (scores.get(chunk_id, 0) +1/(k+rank))

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]