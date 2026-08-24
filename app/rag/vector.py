from .embeddings import embed_texts, embed_query
from app.database.DbConnection import get_db
from bson import ObjectId

def get_document_chunks():
    db = get_db()
    return db["document_chunks"]

class VectorStore:
    

    def add_documents(self,chunks,organization_id,file_id,filename):
        document_chunks = get_document_chunks()
        embeddings = embed_texts(chunks)

        documents = []

        for i, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            documents.append({
                "organization": ObjectId(organization_id),
                "fileId": ObjectId(file_id),
                "filename": filename,
                "content": chunk,
                "embedding": embedding.tolist(),
                "chunkIndex": i
            })

        if documents:
            document_chunks.insert_many(documents)


    def search(self,query,organization_id,k=3):
        document_chunks = get_document_chunks()
        query_embedding = embed_query(query)
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding.tolist(),
                    "numCandidates": 50,
                    "limit": k,

                    "filter": {
                        "organization": organization_id
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "content": 1,
                    "filename": 1,
                    "fileId": 1,
                    "chunkIndex": 1,
                    "score": {
                        "$meta": "vectorSearchScore"
                    }
                }
            }
        ]

        results = list(
            document_chunks.aggregate(pipeline)
        )

        return results