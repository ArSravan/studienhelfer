from pathlib import Path
import json

import numpy as np
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("data/chunks.jsonl")
VECTORS_PATH = Path("data/chunk_vectors.npy")
IDS_PATH =  Path("data/chunk_ids.json")

MODEL_NAME = "intfloat/multilingual-e5-base"

def load_chunks() -> list[dict]:
    chunks = []

    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        for line in file:
            chunks.append(json.loads(line)) 

    return chunks

def main():
    print(f"Loading Model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print(f"Model max_seq_length: {model.max_seq_length}")

    chunks = load_chunks()

    print(f"Loaded chunks: {len(chunks)}")


    tokenizer = model.tokenizer
    max_length = model.max_seq_length

    oversized = []

    for chunk in chunks:
        tokens = tokenizer(
            chunk["text"],
            truncation=False,
            add_special_tokens=True,
        )

        token_count = len(tokens["input_ids"])

        if token_count > max_length:
            oversized.append({
                "chunk_id": chunk["chunk_id"],
                "token_count": token_count,
                "title": chunk["title"],
            })

    print("\nTOKEN LENGTH CHECK")
    print("=" * 60)
    print(f"Model limit: {max_length} tokens")
    print(f"Chunks checked: {len(chunks)}")
    print(f"Chunks exceeding limit: {len(oversized)}")

    if oversized:
        print("\nOversized chunks:")

        for chunk in oversized:
            print(
                f"  {chunk['chunk_id']}: "
                f"{chunk['token_count']} tokens | "
                f"{chunk['title']}"
            )

    passages = [
        f"passage: {chunk['text']}"
        for chunk in chunks
    ]

    print("\nEmbedding passages...")

    vectors = model.encode(
        passages,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    vectors = np.asarray(vectors)

    print(f"Vector shape: {vectors.shape}")

    np.save(VECTORS_PATH, vectors)

    chunk_ids = [chunk['chunk_id'] for chunk in chunks]

    with open(IDS_PATH, "w", encoding="utf-8") as file:
        json.dump(chunk_ids, file, ensure_ascii=False, indent=2)

    print(f"Saved vectors to: {VECTORS_PATH}")
    print(f"Saved chunk IDs to: {IDS_PATH}")


    query = "query: How many days can students work per year?"

    print("\nEmbedding test quesry:")
    print(query)

    query_vector = model.encode(
        query,
        normalize_embeddings=True
    )

    similarities = vectors @ query_vector

    top_indices = np.argsort(similarities)[::-1][:5]

    print("\nTop 5 Results")
    print("=" * 60)

    for rank, index in enumerate(top_indices, start=1):
        chunk = chunks[index]

        print(f"\n#{rank}")
        print(f"Similarity: {similarities[index]:.4f}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Title: {chunk['title']}")
        print(f"Text: {chunk['text'][:500]}")

if __name__ == "__main__":
    main()