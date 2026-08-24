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

        IMPORTANT:
        - The returned results contain the relevant document passages.
        - After receiving the results, answer the user's question using them.
        - Do not call this tool again for the same question unless the first
        search returned no useful results.

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