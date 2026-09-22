from pathlib import Path
import json

import numpy as np
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("data/chunks.jsonl")
VECTORS_PATH = Path("data/chunk_vectors.npy")

MODEL_NAME = "intfloat/multilingual-e5-base"

def load_chunks() -> list[dict]:
    chunks = []

    with open(CHUNKS_PATH, "r", encoding='utf-8') as file:
        for line in file:
            chunks.append(json.loads(line))

    return chunks

def search(
        query: str,
        model: SentenceTransformer,
        chunks: list[dict],
        vectors: np.ndarray,
        top_k: int = 10,
):
    query_vector =  model.encode(
        f"query: {query}",
        normalize_embeddings=True,
    )

    similarities = vectors @ query_vector

    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []

    for index in top_indices:
        results.append({
            "chunk_id": chunks[index]["chunk_id"],
            "title": chunks[index]["title"],
            "text": chunks[index]["text"],
            "similarity": float(similarities[index]),
        })

    return results

def main():
    print(f"Loading model: {MODEL_NAME}")  

    model = SentenceTransformer(MODEL_NAME)

    chunks = load_chunks()
    vectors = np.load(VECTORS_PATH)

    query = "How many days can students work per year?"

    results = search(
        query=query,
        model=model,
        chunks=chunks,
        vectors=vectors,
        top_k=5,
    )

    print(f"\nQuery: {query}")
    print("=" * 70)

    for rank, result in enumerate(results, start=1):
        print(f"\n#{rank}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Title: {result['title']}")
        print(f"Text: {result['text'][:500]}")

if __name__ == "__main__":
    main()