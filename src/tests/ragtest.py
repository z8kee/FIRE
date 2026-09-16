import os, time, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from retrieval.bmsearch import BMRetrieving
from retrieval.embeddings import Embedder
from retrieval.indexvector import VectorStorage
from retrieval.query_parser import QueryParser
from retrieval.reranker import Reranker
from database.connections import SECRepository
from rag.generator import RAGPipeline, Generator
from retrieval.finalpipeline import RetrievalPipeline


def main():
    db = SECRepository(
        dbname="fire_rag",
        user="fire_user",
        password=os.getenv("POSTGRESPASS"),
    )

    companies = db.get_companies()
    parser = QueryParser(companies)
    embedder = Embedder()
    vector_store = VectorStorage()
    bm25 = BMRetrieving(db.get_chunks())
    reranker = Reranker()

    try:
        retrieval = RetrievalPipeline(db, parser, embedder, vector_store, bm25, reranker)
        bigraga = RAGPipeline(retrieval, Generator(model="qwen2.5:1.5b"))
        f = '0'
        while f != '1':
            f = input("enter question: ")
            if f == '1':
                break
            answer = bigraga.ask(f)

            print(answer["answer"])
            print(answer["citations"])

    finally:
        db.close()

if __name__ == "__main__":
    s = time.time()
    main()
    e = time.time()
    print(f"Latency: {e-s} seconds")
