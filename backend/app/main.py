
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes.documents import router as document_router

app = FastAPI(
    title="AI-Based Knowledge Retrieval Platform",
    description="Backend API for document ingestion and knowledge retrieval",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Knowledge Retrieval Platform Backend is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


app.include_router(document_router)
