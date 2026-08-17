from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

from app.rag.loader import load_document
from app.rag.service import split_document

router = APIRouter(
    prefix="/api/rag",
    tags=["RAG"]
)

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    organization_id: str,
    file: UploadFile = File(...)
):

    allowed_extensions = [".pdf", ".txt"]

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    file_id = str(uuid.uuid4())

    file_path = os.path.join(
        UPLOAD_DIR,
        f"{file_id}{extension}"
    )

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    text = load_document(file_path)

    chunks = split_document(text)

    return {
        "message": "Document uploaded successfully",
        "filename": file.filename,
        "chunks": len(chunks)
    }