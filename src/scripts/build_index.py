import os, time, sys

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from database.connections import SECRepository
from retrieval.embeddings import Embedder
from retrieval.indexvector import VectorStorage

load_dotenv()
# connect to db, embedder, qdrant
db = SECRepository(dbname='fire_rag',
                            user='fire_user', 
                            password=os.getenv("POSTGRESPASS"))
embedding = Embedder()
vector_store = VectorStorage()
def build():

    #get chunks and put in batches
    rows = db.get_chunks()
    print(f"Found {len(rows)} chunks")

    batch_size = 128

    for s in range(0, len(rows), batch_size):
        batch = rows[s:s+batch_size]
        texts = [row["text"] for row in batch]

        embeddings = embedding.encode(texts)
        vector_store.insert_chunks(batch, embeddings)

        print(F"Indexed {min(s+batch_size, len(rows))}/{len(rows)}")

    db.close()

    print("Finito!")

if __name__ == "__main__":
    build()