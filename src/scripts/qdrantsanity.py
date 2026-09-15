#pls dont mind this, just checking if everything is intact in my vector db

from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)

points, _ = client.scroll(
    collection_name="sec_chunks",
    limit=5000,
    with_payload=True,
    with_vectors=False
)

sections = {}
for p in points:
    sec = p.payload.get("section")
    if sec:
        sections[sec] = sections.get(sec, 0) + 1

print(sections)

from qdrant_client import QdrantClient
from collections import Counter

client = QdrantClient(host="localhost", port=6333)

collection = "sec_chunks"

print("count:", client.count(collection_name=collection).count)
print("collection:", client.get_collection(collection))

points, _ = client.scroll(
    collection_name=collection,
    limit=10,
    with_payload=True,
    with_vectors=False,
)

for p in points:
    print(p.payload)

from collections import Counter

points, _ = client.scroll(
    collection_name=collection,
    limit=100000,
    with_payload=True,
    with_vectors=False,
)

sections = Counter()
for p in points:
    section = p.payload.get("section", "unknown")
    sections[section] += 1

print(sections.most_common(20))