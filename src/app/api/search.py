from pydantic import BaseModel

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_retriever
from app.rag.retriever  import Retriever, RetrievedChunk

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    jurisdiction: str | None = None

@router.post(
    "/search",
    response_model=list[RetrievedChunk],
)

def search(
    request: SearchRequest,
    retriever: Retriever = Depends(get_retriever),
    current_user=Depends(get_current_user),
) -> list[RetrievedChunk]:
    return retriever.search(
        query=request.query,
        jurisdiction=request.jurisdiction,
    )