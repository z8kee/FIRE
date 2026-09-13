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
                        "acceptance_datetime": (
                            row["acceptance_datetime"].isoformat()
                            if row.get("acceptance_datetime") is not None
                            else None
                        ),
                        "section": row["section"]
                }
            )
        )
        self.client.upsert(collection_name=self.collection_name,
                           points=points,
                           wait=True)

    def search(self, query_vector, ticker=None, cutoff_datetime=None, limit=15):
        conditions = []

        if ticker:
            conditions.append(models.FieldCondition(
                key="ticker",
                match=models.MatchValue(value=ticker.upper())
            )
            )

        if cutoff_datetime:
            if hasattr(cutoff_datetime, "isoformat"):
                cutoff_datetime = (
                    cutoff_datetime.isoformat()
                )

            conditions.append(models.FieldCondition(
                key="acceptance_datetime",
                range=models.DatetimeRange(
                    lte=cutoff_datetime
                )
            )
        )

        query_filter = models.Filter(must=conditions) if conditions else None
        return self.client.query_points(collection_name=self.collection_name,
                                        query=query_vector.tolist(),
                                        query_filter=query_filter,
                                        limit=limit).points

    def update_document_timestamp(self, document_id, acceptance_datetime):
        self.client.set_payload(
            collection_name=self.collection_name,
            payload={
                "acceptance_datetime":
                acceptance_datetime.isoformat()
            },
            points=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(
                        value=document_id
                        )
                    )
                ]
            )
        )