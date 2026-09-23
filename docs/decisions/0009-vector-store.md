# ADR 0009: Vector Store

## Status

Accepted

## Context

The application initially used NumPy for brute-force vector similarity search.

With the current dataset, containing only 132 chunks, brute-force NumPy search is simple and can be faster than a vector database because the dataset is very small.

However, the application requires capabilities that brute-force NumPy does not provide as cleanly:

* metadata filtering during retrieval;
* persistent vector storage;
* scalable approximate nearest-neighbor search;
* a network service that can be queried by the application.

In particular, metadata filtering must happen as part of the retrieval operation rather than retrieving an unfiltered top-k set and filtering it afterward. Post-filtering can remove relevant candidates from a small top-k result set.

## Decision

Use Qdrant as the vector store.

The application connects to a locally running Qdrant Server over HTTP:

```python
QdrantClient(url="http://localhost:6333")
```

The `official_docs` collection uses:

* 768-dimensional vectors;
* cosine distance;
* payload metadata containing the complete chunk metadata.

Payload indexes are created for:

* `jurisdiction`
* `authority_level`
* `topics`

These fields are indexed because they are used to constrain retrieval.

## Point IDs

Qdrant point IDs must be unsigned integers or UUIDs. The source `chunk_id`, such as `9_002`, cannot therefore be used directly.

The application derives a deterministic UUID5 from the chunk ID:

```python
uuid.uuid5(
    uuid.NAMESPACE_URL,
    f"studienhelfer: {chunk_id}",
)
```

Deterministic IDs are important for idempotent ingestion. Running the ingestion process again for the same chunk produces the same Qdrant point ID, so an upsert updates the existing point instead of creating a duplicate point.

## Consequences

### Positive

* Metadata filters can be applied during vector retrieval.
* Repeated ingestion is idempotent because point IDs are deterministic.
* Qdrant provides persistent vector storage.
* The application communicates with the vector store through a network interface.
* The architecture can scale beyond the current small dataset.

### Trade-offs

* Qdrant introduces an additional server/container compared with an in-process NumPy implementation.
* For only 132 vectors, NumPy brute-force search may be faster.
* The additional infrastructure is justified by filtering, persistence, and the intended scalable architecture.
