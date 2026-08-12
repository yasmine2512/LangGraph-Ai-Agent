from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.database.DbConnection import connect_db,close_db

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class AgentRequest(BaseModel):
    message: str
    organization_id: str
    thread_id: str


@router.post("/chat")
def chat_with_agent(request: Request,
    body: AgentRequest):

    config = {
        "configurable": {
            "thread_id": body.thread_id,
            "organization_id": body.organization_id
        }
    }
    graph = request.app.state.graph
    try:
        result = graph.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": body.message
                    }
                ],
                "tool_calls": 0,
            },
            config
        )

        last_message = result["messages"][-1]

        return {
            "message": last_message.content
        }

    except Exception as e:
        print("Agent error:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to process the request"
        )