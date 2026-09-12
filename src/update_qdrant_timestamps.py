import os
import sys

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from database.connections import SECRepository
from retrieval.indexvector import VectorStorage

load_dotenv()


def update():
    db = SECRepository(
        dbname="fire_rag",
        user="fire_user",
        password=os.getenv("POSTGRESPASS")
    )

    vector_store = VectorStorage()

    documents = db.get_document_timestamps()

    print(f"Updating timestamps for " f"{len(documents)} documents")

    for i, document in enumerate(documents, start=1):

        vector_store.update_document_timestamp(
            document["document_id"],
            document["acceptance_datetime"]
        )

        if i % 50 == 0:
            print(
                f"Updated {i}/{len(documents)}"
            )

    db.close()

    print("Qdrant timestamp update complete.")


if __name__ == "__main__":
    update()