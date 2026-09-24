from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

from sentence_transformers import SentenceTransformer

from app.core.config import settings


class RetrievedChunk(BaseModel):
    chunk_id: str
    source_id: int
    title: str
    url: str
    text: str
    score: float
    authority_level: str
    jurisdiction: list[str]

class Retriever:
    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)
        self.client = QdrantClient(url=settings.qdrant_url)

    def search(
        self,
        query: str,
        limit: int=5,
        jurisdiction: str | None = None,
    ) -> list[RetrievedChunk]:

        query_text = f"query: {query}"
      
        query_vector = self.model.encode(
            query_text,
            normalize_embeddings=True,
        )

        query_filter = None

        if jurisdiction is not None:
            jurisdiction = jurisdiction.lower()

            query_filter = Filter(
                should=[
                    FieldCondition(
                        key='jurisdiction',
                        match=MatchValue(value=jurisdiction),
                    ),
                    FieldCondition(
                        key='jurisdiction',
                        match=MatchValue(value="federal"),
                    ),
                ]
            )

        results = self.client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector.tolist(),
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points

        chunks = []

        for result in results:
            payload = result.payload

            chunks.append(
                RetrievedChunk(
                    chunk_id=payload['chunk_id'],
                    source_id=payload['source_id'],
                    title=payload['title'],
                    url=payload['url'],
                    text=payload['text'],
                    score=result.score,
                    authority_level=payload['authority_level'],
                    jurisdiction=payload['jurisdiction']
                )
            )
        return chunks