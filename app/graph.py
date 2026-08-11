from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from groq import APIStatusError
from app.state import AgentState
from bson import ObjectId
from app.tools.customers import customer_tools
from app.tools.orders import order_tools
from app.tools.products import product_tools
from app.tools.analytics.customers_analysis import customer_analysis
from app.tools.analytics.inventory_analysis import inventory_tools
from app.tools.analytics.orders_analysis import order_analysis
from app.tools.analytics.products_analysis import product_analysis
from app.tools.analytics.sales_analysis import sales_tools
from app.tools.analytics.overview_analytics import overview_tools
MAX_TOOL_CALLS = 5

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=300
)

organization_id = ObjectId("69d7d122f1b2c8ffe9d9c781")

tools = [*product_tools(organization_id),
         *order_tools(organization_id),
         *customer_tools(organization_id),
         *customer_analysis(organization_id),
         *inventory_tools(organization_id),
         *order_analysis(organization_id),
         *product_analysis(organization_id),
         *sales_tools(organization_id),
         *overview_tools(organization_id)]
llm_with_tools = llm.bind_tools(tools)


def call_llm(state: AgentState):
    try:
        response = llm_with_tools.invoke(state["messages"])

        return {
            "messages": [response]
        }

    except APIStatusError as e:

        if e.status_code == 413:
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I couldn't perform that analysis because "
                            "the request was too large. Please try "
                            "a more specific question."
                        )
                    )
                ]
            }

        raise

tool_node = ToolNode(tools)

def call_tools(state: AgentState):
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

builder.add_node("llm", call_llm)
builder.add_node("tools", call_tools)
builder.add_node("fallback", fallback_node)

builder.add_edge(START, "llm")

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

graph = builder.compile()