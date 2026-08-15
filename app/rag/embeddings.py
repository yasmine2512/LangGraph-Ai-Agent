from sentence_transformers import SentenceTransformer


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def embed_texts(texts):
    return embedding_model.encode(
        texts,
        normalize_embeddings=True
    )


def embed_query(query):
    return embedding_model.encode(
        [query],
        normalize_embeddings=True
    )[0]