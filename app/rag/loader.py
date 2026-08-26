import pymupdf
import httpx
import os

async def load_pdf_from_url(url: str):

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

    document = pymupdf.open(
        stream=response.content,
        filetype="pdf"
    )
    content_type = response.headers.get("content-type", "")

    if "application/pdf" not in content_type:
        raise ValueError(
            f"URL did not return a PDF. Content-Type: {content_type}"
        )

    text_parts = []

    for page in document:
        text_parts.append(page.get_text())

    document.close()

    return "\n".join(text_parts)

async def load_txt_from_url(url: str):

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

    return response.content.decode("utf-8")

async def load_document_from_url(
    url: str,
    filename: str
):

    extension = os.path.splitext(
        filename
    )[1].lower()

    if extension == ".pdf":
        return await load_pdf_from_url(url)

    if extension == ".txt":
        return await load_txt_from_url(url)

    raise ValueError(
        "Unsupported file type"
    ) 