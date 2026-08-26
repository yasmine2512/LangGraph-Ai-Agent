print("Starting application...")
from contextlib import asynccontextmanager
print("Importing FastAPI...")
from fastapi import FastAPI, Depends
print("Importing agent router...")
from app.routes.agent import router as agent_router
print("Importing RAG router...")
from app.routes.rag import router as rag_router
print("Importing database...")
from app.database.DbConnection import connect_db, close_db
print("Importing graph...")
from app.graph import create_graph
from app.middleware.service_auth import verify_ai_service
print("All imports completed.")
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("LIFESPAN STARTED", flush=True)
    global graph
    print("Connecting to MongoDB...")
    connect_db()
    app.state.graph = create_graph()
    yield
    print("Closing MongoDB...")
    close_db()


app = FastAPI(
    title="AI Agent API",
    version="0.1.0",
    lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "AI Agent API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(agent_router,dependencies=[Depends(verify_ai_service)])
app.include_router(rag_router,dependencies=[Depends(verify_ai_service)])