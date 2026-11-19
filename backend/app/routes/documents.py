
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.document_extractor import extract_text
from backend.app.services.document_service import save_uploaded_document
from backend.app.services.retrieval_service import retrieve_relevant_chunks
from backend.app.services.ingestion_service import ingest_document


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


# Request format for document questions
class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


# Endpoint 1: Upload a document
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    try:
        content = await file.read(20 * 1024 * 1024 + 1)

        result = save_uploaded_document(
            filename=file.filename or "",
            content=content
        )

        return {
            "success": True,
            "message": "Document uploaded successfully!",
            "document": result
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    finally:
        await file.close()


# Endpoint 2: Extract text
@router.get("/{stored_filename}/extract")
def extract_document_text(stored_filename: str):

    try:
        text = extract_text(stored_filename)

        return {
            "success": True,
            "filename": stored_filename,
            "extracted_text": text,
            "character_count": len(text)
        }

    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# Endpoint 3: Process and index document
@router.post("/{stored_filename}/process")
def process_uploaded_document(stored_filename: str):

    try:
        result = ingest_document(stored_filename)
        return result

    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# Endpoint 4: Ask a question and retrieve relevant chunks
@router.post("/query")
def query_documents(request: RetrievalRequest):

    try:
        results = retrieve_relevant_chunks(
            query=request.query.strip(),
            top_k=request.top_k
        )

        return {
            "success": True,
            "query": request.query,
            "results_count": len(results),
            "results": results
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
