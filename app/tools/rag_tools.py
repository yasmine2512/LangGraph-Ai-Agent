from langchain_core.tools import tool
from app.rag.vector import VectorStore

store = VectorStore()
@tool
def search_knowledge_base(query: str):
    """
    Search uploaded organization documents for relevant information.

    Use this when the user asks about information contained
    in uploaded documents.
    """

    results = store.search(
        query,
        k=5
    )

    return results