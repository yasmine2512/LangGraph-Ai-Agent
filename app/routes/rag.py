from fastapi import APIRouter
import os
import uuid
from pydantic import BaseModel
from app.rag.loader import load_document_from_url
from app.rag.service import split_document
from app.rag.vector import VectorStore


router = APIRouter(
    prefix="/api/rag",
    tags=["RAG"]
)

vector_store = VectorStore()

class ProcessDocumentRequest(BaseModel):
    file_id: str
    organization_id: str
    filename: str
    file_url: str


@router.post("/upload")
async def upload_document(
    request: ProcessDocumentRequest
):

    text = await load_document_from_url(
        request.file_url,
        request.filename
    )

    chunks = split_document(text)

    vector_store.add_documents(
        chunks=chunks,
        organization_id=request.organization_id,
        file_id=request.file_id,
        filename=request.filename
    )

    return {
        "message": "Document processed successfully",
        "file_id": request.file_id,
        "chunks": len(chunks)
    }