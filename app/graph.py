from langgraph.graph import StateGraph, START, END
# from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from app.state import AgentState
from app.tools import get_products,get_orders,get_customers,get_customer,get_order,get_product

llm = ChatOllama(
    model="gpt-oss:20b-cloud",
    temperature=0
)

tools = [get_products,get_orders,get_customers,get_customer,get_order,get_product]
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