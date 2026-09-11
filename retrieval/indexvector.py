from qdrant_client import QdrantClient, models

class VectorStorage:
    def __init__(self, host='localhost', port=6333, collection_name='sec_chunks'):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        #model bge-small v1.5 uses 384-dimensional vectors, had to search that one up lol
        self.vector_size = 384
        self._create_collection()

    def _create_collection(self):
        #creating a new one if it doesn't already exist
        if not self.client.collection_exists(collection_name = self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
    def insert_chunks(self, rows, embeddings):
        points = []

        for row, embedding in zip(rows, embeddings):
            points.append(models.PointStruct(
                id=row["chunk_id"],
                vector=embedding.tolist(),

                payload={"chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "ticker": row["ticker"],
                        "filing_type": row["filing_type"],
                        "filing_date": str(row["filing_date"]),
                        "section": row["section"]
                }
            )
        )
        self.client.upsert(collection_name=self.collection_name,
                           points=points,
                           wait=True)

    def search(self, query_vector, ticker, limit=15):
        query_filter = None

        if ticker is not None:
            query_filter = models.Filter(
                must=[models.FieldCondition(
                    key="ticker",
                    match=models.MatchValue(value=ticker.upper())
                    )
                ]
            )
        return self.client.query_points(collection_name=self.collection_name,
                                        query=query_vector.tolist(),
                                        query_filter=query_filter,
                                        limit=limit).points