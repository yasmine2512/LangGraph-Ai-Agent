from app.rag.vector import VectorStore


store = VectorStore()

store.add_documents([
    "Refunds are allowed within 30 days.",
    "Premium customers receive free shipping.",
    "Orders above $100 receive a discount.",
])

results = store.search(
    "How long do I have to request a refund?"
)

for result in results:
    print(result)