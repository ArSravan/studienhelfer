from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.search import router as search_router
from app.rag.retriever import Retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.retriever = Retriever()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(search_router)
