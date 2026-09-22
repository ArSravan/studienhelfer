# ADR 0008: Multilingual E5 Base Embedding Model

* Status: Accepted
* Date: 2026-09-22
* Decision: Use `intfloat/multilingual-e5-base` as the local embedding model for the ingestion and retrieval pipeline.

## Context

The RAG system needs a single embedding model for both document chunks and user queries.

The corpus contains German official and legal sources, while the application has a cross-lingual requirement. The embedding model therefore needs to represent multilingual text in a shared semantic vector space rather than being limited to English.

The project also prefers local inference over a hosted embedding API. Local inference avoids sending source documents and user queries to an external embedding provider, removes a runtime dependency on an external embedding API, and makes the ingestion pipeline reproducible without per-request API costs. The trade-off is that the application must download and run the model locally and therefore requires sufficient local compute.

## Decision

Use `intfloat/multilingual-e5-base` through `sentence-transformers`.

The model is multilingual and its model configuration uses a hidden size of 768, giving each text a 768-dimensional embedding. Its tokenizer configuration specifies a maximum sequence length of 512 tokens.

Documents are embedded using the E5 passage format:

```text
passage: <chunk text>
```

Queries are embedded using the corresponding query format:

```text
query: <user query>
```

Embeddings are generated locally using `SentenceTransformer`.

The ingestion pipeline explicitly tokenizes every chunk with truncation disabled and reports chunks whose token count exceeds the model's maximum sequence length. This check is performed before embedding so that oversized chunks are visible rather than silently truncated.

## Alternatives Considered

### Hosted embedding API

A hosted embedding API would reduce local compute requirements and could provide a high-quality managed embedding service.

It was not selected because the project prefers local inference, particularly to avoid sending official-source content and user queries to an external embedding service and to keep the ingestion pipeline independent of API availability and per-request costs.

### English-only embedding model

An English-only model would not satisfy the multilingual requirement of the corpus and would be a poor fit for German legal and administrative documents.

### Smaller multilingual model

A smaller model could reduce local resource requirements, but `multilingual-e5-base` provides a suitable balance for this project while producing 768-dimensional vectors required by the current retrieval design.

## Token-Length Validation

The embedding pipeline does not rely on character count as a substitute for token count.

Before embedding, each chunk is passed through the model tokenizer with:

```python
truncation=False
```

The pipeline records chunks whose token count exceeds the model's maximum sequence length.

This is important because token count depends on the tokenizer and cannot be reliably inferred from character count alone.

## Consequences

### Positive

* Supports multilingual text, including German.
* Runs locally without an external embedding API.
* Produces 768-dimensional vectors suitable for the planned Qdrant collection.
* Uses explicit `query:` and `passage:` prefixes appropriate to the E5 model family.
* Provides an explicit token-length validation step before embedding.

### Negative

* Local inference requires model storage and local compute.
* The model is larger than some lightweight embedding alternatives.
* Chunks exceeding the model's token limit require additional chunking or other preprocessing rather than relying on silent truncation.
* Changing the embedding model later would require re-embedding the corpus because vectors from different embedding models are not interchangeable.

## Validation

The embedding script must report:

* the model's maximum sequence length,
* the number of chunks checked,
* the number of chunks exceeding the limit,
* and the resulting vector shape.

The expected embedding dimensionality for `intfloat/multilingual-e5-base` is 768.
