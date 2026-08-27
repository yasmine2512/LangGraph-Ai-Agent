from google import genai
from google.genai import types
import os

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def embed_query(query):
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=query,
        config={
            "output_dimensionality": 768,
            "task_type": "RETRIEVAL_QUERY"
        }
    )

    return response.embeddings[0].values

def embed_documents(chunks):
    contents = [
        types.Content(
            parts=[
                types.Part.from_text(text=chunk)
            ]
        )
        for chunk in chunks
    ]

    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=contents,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    return [
        embedding.values
        for embedding in response.embeddings
    ]