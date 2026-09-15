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

    def format_evidence(self, results):
        blocks = []

        for i, result in enumerate(results, start=1):
            block = f"""
            [{i}]
            Company: {result["ticker"]}
            Filing: {result["filing_type"]}
            Filed: {result["filing_date"]}
            Section: {result["section"]}
            Text:
            {result["text"]}
            """

            blocks.append(block.strip())

        return "\n\n".join(blocks)