from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from app.state import AgentState


llm = ChatOpenAI(
    model="",
    temperature=0
)


def call_llm(state: AgentState):
    response = llm.invoke(state["message"])

    return {
        "response": response.content
    }


graph_builder = StateGraph(AgentState)

graph_builder.add_node("llm", call_llm)

graph_builder.add_edge(START, "llm")
graph_builder.add_edge("llm", END)

graph = graph_builder.compile()