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
        print("RAG TOOL CALLED")
        results = vector_store.search(
            question,
            organization_id,
            k=5
        )
        if not results:
            return "No relevant information was found in the organization's documents."
        formatted_results = []

        for result in results:
            formatted_results.append(
                f"""
                File: {result.get("filename", "Unknown")}
                Chunk: {result.get("chunkIndex", "Unknown")}
                Relevance: {result.get("score", 0):.3f}
                Content:
                {result.get("content", "")}
                """
            )
        print("\n\n---\n\n".join(formatted_results))
        return "\n\n---\n\n".join(formatted_results)

    return [search_knowledge_base]