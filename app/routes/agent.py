from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.state import extract_text
import traceback

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class AgentRequest(BaseModel):
    message: str
    organization_id: str
    thread_id: str

class DeleteThreadRequest(BaseModel):
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
        text = extract_text(last_message.content)

        return {
            "message": text
        }

    except Exception as e:
        print("Agent error:", repr(e))
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="The AI assistant encountered an error while processing your request."
        )

@router.delete("/thread")
def delete_thread(
    request: Request,
    body: DeleteThreadRequest
):
    graph = request.app.state.graph
    checkpointer = graph.checkpointer
    checkpointer.delete_thread(body.thread_id)

    return {
        "message": "Thread deleted successfully",
        "thread_id": body.thread_id
    }