from sentence_transformers import CrossEncoder

#reranker sees the query and chunks together, gives better final ordering
class Reranker:
    def __init__(self):
        self.model = CrossEncoder("BAAI/bge-reranker-base")

    def rerank(self, query, chunks, limit=10):
        pairs = [[query, chunk["text"]] for chunk in chunks]
        scores = self.model.predict(pairs)
        
        results = []

        for chunk, score in zip(chunks, scores):
            results.append({**chunk, "rerank_score": float(score)})

        return sorted(results, key=lambda x:x["rerank_score"], reverse=True)[:limit]