from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes.agent import router as agent_router
from app.routes.rag import router as rag_router
from app.database.DbConnection import connect_db, close_db
from app.graph import create_graph

@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.include_router(agent_router)
app.include_router(rag_router)