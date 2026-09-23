from pathlib import Path
import json
import uuid

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import(
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
    Filter,
    FieldCondition,
    MatchValue,
)
from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-base"

CHUNKS_PATH = Path("data/chunks.jsonl")
VECTORS_PATH = Path("data/chunk_vectors.npy")

COLLECTION_NAME = "official_docs"
VECTOR_SIZE = 768

model = SentenceTransformer(MODEL_NAME)

def load_chunks() -> list[dict]:
    chunks = []

    with CHUNKS_PATH.open("r", encoding='utf-8') as file:
        for line in file:
            chunks.append(json.loads(line))

    return chunks

def load_vectors() -> np.ndarray:
    return np.load(VECTORS_PATH)

def point_id_for(chunk_id: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            F"studienhelfer: {chunk_id}",
        )
    )

def build_points(
        chunks: list[dict],
        vectors: np.ndarray,
) -> list[PointStruct]:

    if len(chunks) != len(vectors):
        raise ValueError(
            f"Chunk/vector count mismatch: "
            f"{len(chunks)} chunks vs {len(vectors)} vectors"
        )

    points = []

    for chunk, vector in zip(chunks,vectors):
        points.append(
            PointStruct(
                id=point_id_for(chunk['chunk_id']),
                vector=vector.tolist(),
                payload=chunk,
            )
        )

    return points

def create_payload_indexes(client: QdrantClient) -> None:
    collection = client.get_collection(COLLECTION_NAME)

    existing_fields = collection.payload_schema

    fields = {
        "jurisdiction": PayloadSchemaType.KEYWORD,
        "authority_level": PayloadSchemaType.KEYWORD,
        "topics": PayloadSchemaType.KEYWORD,
    }

    for field_name, field_type in fields.items():
        if field_name in existing_fields:
            print(f"Payload index already exists: {field_name}")
            continue

        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=field_type,
        )

        print(f"Created payload index: {field_name}")

def search_qdrant(client: QdrantClient) -> None:
    query = "query: How many days can students work per year?"

    query_vector = model.encode(
        query,
        normalize_embeddings=True,
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector.tolist(),
        limit=5,
        with_payload=True,
    ).points

    print("\nUNFILTERED SEARCH")
    print("="*60)

    for rank,result in enumerate(results, start=1):
        print(f"\n#{rank}")
        print(f"Score: {result.score:.4f}")
        print(f"Chunk ID: {result.payload['chunk_id']}")
        print(f"Authority: {result.payload['authority_level']}")
        print(f"Title: {result.payload['title']}")

    statute_filter = Filter(
        must=[
            FieldCondition(
                key="authority_level",
                match=MatchValue(value='statute'),
            )
        ]
    )

    filtered_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query = query_vector.tolist(),
        query_filter=statute_filter,
        limit=5,
        with_payload=True,
    ).points

    for result in filtered_results:
        assert result.payload["authority_level"] == "statute"


    print("\nFILTERED SEARCH: authority_level = statute")
    print("=" * 60)

    for rank, result in enumerate(filtered_results, start=1):
        print(f"\n#{rank}")
        print(f"Score: {result.score:.4f}")
        print(f"Chunk ID: {result.payload['chunk_id']}")
        print(f"Authority: {result.payload['authority_level']}")
        print(f"Jurisdiction: {result.payload['jurisdiction']}")
        print(f"Title: {result.payload['title']}")


def main():
    chunks = load_chunks()
    vectors = load_vectors()

    print(f"Loaded chunks: {len(chunks)}")
    print(f"Loaded vectors: {vectors.shape}")

    client = QdrantClient(url="http://localhost:6333")

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            ),
        )

        print(f"Created collection: {COLLECTION_NAME}")
    else:
        print(f"Collection already exists: {COLLECTION_NAME}")


    create_payload_indexes(client)

    points = build_points(chunks, vectors)

    print(f"\nBuilt Qdrant points: {len(points)}")

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    print("\nAll Points upserted")

    if points:
        first_point = points[0] 

        print("\nFirst point:")
        print(f"  Qdrant ID: {first_point.id}")
        print(f"  Chunk ID: {first_point.payload['chunk_id']}")
        print(f"  Authority: {first_point.payload['authority_level']}")
        print(f"  Title: {first_point.payload['title']}")
        print(f"  Vector length: {len(first_point.vector)}")
        print(f"  Payload keys: {list(first_point.payload.keys())}")

    search_qdrant(client)

if __name__ == "__main__":
    main()