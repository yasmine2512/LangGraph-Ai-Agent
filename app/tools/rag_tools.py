from langchain_core.tools import tool
from app.rag.vector import VectorStore

vector_store = VectorStore()

@tool
def search_knowledge_base(question: str,organization_id: str):
    """
    Search uploaded organization documents for relevant information.
    
    Use this when the user asks about information contained
    in uploaded documents.
    """

    results = vector_store.search(
        question,
        organization_id,
        k=5
    )

    return results