import faiss
import numpy as np

from .embeddings import embed_texts, embed_query


class VectorStore:

    def __init__(self, dimension=384):
        self.index = faiss.IndexFlatIP(dimension)
        self.documents = []

    def add_documents(self, chunks):
        embeddings = embed_texts(chunks)

        embeddings = np.array(
            embeddings,
            dtype="float32"
        )

        self.index.add(embeddings)

        self.documents.extend(chunks)

    def search(self, query, k=5):

        query_embedding = embed_query(query)

        query_embedding = np.array(
            [query_embedding],
            dtype="float32"
        )

        scores, indexes = self.index.search(
            query_embedding,
            k
        )

        results = []

        for score, index in zip(scores[0], indexes[0]):

            if index == -1:
                continue

            results.append({
                "content": self.documents[index],
                "score": float(score)
            })

        return results