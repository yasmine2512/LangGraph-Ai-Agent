from langchain_core.tools import tool
from app.rag.vector import VectorStore

def rag_tools(organization_id: str):
    vector_store = VectorStore()

    @tool
    def search_knowledge_base(question: str):
        """
        Search uploaded organization documents for relevant information.
        
        Use this when the user asks about information contained
        in uploaded documents.

        The results contain document passages and their source filenames.

        After receiving the results:
        - Answer using only the retrieved passages.
        - Mention the source filename for information taken from a document.
        - Do not claim information exists if no relevant passages were returned.
        - Do not call this tool again for the same question if useful results
        were already returned.
        """
        results = vector_store.search(
            question,
            organization_id,
            k=3
        )

        if not results:
            return "No relevant information was found in the organization's documents."
        
        return "\n\n".join(
        f"Source: {r['filename']}\n"
        f"{r['content']}"
        for r in results
    )

    return [search_knowledge_base]