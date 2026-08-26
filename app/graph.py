from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage,SystemMessage
from langchain_google_genai._common import GoogleGenerativeAIError
from langgraph.checkpoint.mongodb import MongoDBSaver
from app.state import AgentState,get_recent_messages
from bson import ObjectId
from app.database.DbConnection import get_client,MONGODB_DATABASE
from app.router import create_router, build_route_tools
from app.summarizer import summarize_conversation,should_summarize
from app.llm import llm
from fastapi import HTTPException
from langchain_core.runnables import RunnableConfig

MAX_TOOL_CALLS = 5

SYSTEM_PROMPT = """
You are InsightFlow AI, a business assistant.

Response style:
- Be concise, direct, and easy to scan.
- Keep answers short unless the user asks for details.
- Use simple numbered lists or bullet points when useful.
- Do not use bold markdown (**), italics, or decorative formatting.
- Do not repeat the user's question.
- Never invent data.

For business analytics:
- Give the relevant numbers directly.
- Include names and important details when useful.
- Base answers on the results returned by the tools.

"""
router = create_router(llm)

def get_tools_for_routes(routes,route_tools):
    tools = []
    seen = set()

    for route in routes:
        for tool in route_tools.get(route, []):
            if tool.name not in seen:
                tools.append(tool)
                seen.add(tool.name)

    return tools

def router_node(state: AgentState):

    context = get_recent_messages(
    state["messages"],
    max_human_turns=3
)
    routes = router(context)
    return {
        "routes": routes
    }

def call_llm(state: AgentState, config: RunnableConfig):
    organization_id = ObjectId(config["configurable"]["organization_id"])

    route_tools = build_route_tools(organization_id)

    routes = state.get("routes", [])

    tools = get_tools_for_routes(routes,route_tools)

    if tools:
        model = llm.bind_tools(tools)
    else:
        model = llm

    context = [
        SystemMessage(content=SYSTEM_PROMPT),
        *get_recent_messages(
        state["messages"],
        max_human_turns=3
    )]

    try:
        response = model.invoke(context)
        return {
            "messages": [response]
        }
    
    except GoogleGenerativeAIError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=429,
                detail="AI rate limit exceeded"
            )

        raise HTTPException(
            status_code=500,
            detail="AI service error"
        )


    except Exception as e:

        print("LLM ERROR:", repr(e))

        return {
            "messages": [
                AIMessage(
                    content=(
                        "Sorry, something went wrong while processing "
                        "your request. Please try again."
                    )
                )
            ]
        }



def call_tools(state: AgentState, config: RunnableConfig):

    organization_id = ObjectId(config["configurable"]["organization_id"])
    route_tools = build_route_tools(organization_id)
    routes = state.get("routes", [])

    tools = get_tools_for_routes(routes,route_tools)

    if not tools:
        return {
            "messages": [
                AIMessage(
                    content="I couldn't find an appropriate tool for this request."
                )
            ]
        }

    tool_node = ToolNode(tools)

    result = tool_node.invoke(state)

    return {
        "messages": result["messages"],
        "tool_calls": state.get("tool_calls", 0) + 1
    }


def should_continue(state: AgentState):

    if state.get("tool_calls", 0) >= MAX_TOOL_CALLS:
        return "fallback"
    
    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    if not last_message.content:
        return "fallback"

    return END

def fallback_node(state):
    return {
        "messages": [
            AIMessage(
                content=(
                    "I'm sorry, I couldn't process that request. "
                    "Please try asking in a more specific way."
                )
            )
        ]
    }

builder = StateGraph(AgentState)
builder.add_node("summarize", summarize_conversation)
builder.add_node("router", router_node)
builder.add_node("llm", call_llm)
builder.add_node("tools", call_tools)
builder.add_node("fallback", fallback_node)

builder.add_conditional_edges(
    START,
    should_summarize,
    {
        "summarize": "summarize",
        "router": "router"
    }
)
builder.add_edge("summarize", "router")
builder.add_edge("router", "llm")
builder.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tools": "tools",
        "fallback": "fallback",
        END: END
    }
)
builder.add_edge("tools", "llm")
builder.add_edge("fallback", END)

def create_graph():
    checkpointer = MongoDBSaver(
        get_client(),
        db_name=MONGODB_DATABASE
    )

    return builder.compile(checkpointer=checkpointer)