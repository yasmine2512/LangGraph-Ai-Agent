from fastapi import APIRouter
from pydantic import BaseModel
from app.rag.loader import load_document_from_url
from app.rag.service import split_document
from app.rag.vector import VectorStore


router = APIRouter(
    prefix="/api/rag",
    tags=["RAG"]
)

vector_store = None

def get_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()

    return vector_store

class ProcessDocumentRequest(BaseModel):
    file_id: str
    organization_id: str
    filename: str
    file_url: str


@router.post("/upload")
async def upload_document(
    request: ProcessDocumentRequest
):
    print(f"RAG: starting {request.filename} ,getting vector store", flush=True)
    vector_store = get_vector_store()
    print(f"vector_store: {vector_store}", flush=True)
    print("RAG: downloading document...", flush=True)
    text = await load_document_from_url(
        request.file_url,
        request.filename
    )
    print(f"RAG: document loaded, {len(text)} characters", flush=True)
    chunks = split_document(text)
    print(f"RAG: created {len(chunks)} chunks", flush=True)
    print("RAG: starting embeddings...", flush=True)
    vector_store.add_documents(
        chunks=chunks,
        organization_id=request.organization_id,
        file_id=request.file_id,
        filename=request.filename
    )
    print("RAG: embeddings + storage completed", flush=True)

    return {
        "message": "Document processed successfully",
        "file_id": request.file_id,
        "chunks": len(chunks)
    }