import fitz
import os

def load_pdf(file_path: str) -> str:
    document = fitz.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text

def load_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def load_document(file_path: str) -> str:

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return load_pdf(file_path)

    if extension == ".txt":
        return load_txt(file_path)

    raise ValueError("Unsupported file type")   