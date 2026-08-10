from langgraph.graph import StateGraph, START, END
# from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from app.state import AgentState
from bson import ObjectId
from app.tools.customers import customer_tools
from app.tools.orders import order_tools
from app.tools.products import product_tools

llm = ChatOllama(
    model="gpt-oss:20b-cloud",
    temperature=0
)

organization_id = ObjectId("69d7d122f1b2c8ffe9d9c781")

tools = [*product_tools(organization_id),*order_tools(organization_id),*customer_tools(organization_id)]
llm_with_tools = llm.bind_tools(tools)


def call_llm(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])

    return {
        # "response": response.content
        "messages": [response]
    }

def should_continue(state: AgentState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return END

builder = StateGraph(AgentState)

builder.add_node("llm", call_llm)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "llm")

builder.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

builder.add_edge("tools", "llm")

graph = builder.compile()