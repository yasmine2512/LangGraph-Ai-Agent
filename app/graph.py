from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq
from groq import APIStatusError,RateLimitError
from langgraph.checkpoint.mongodb import MongoDBSaver
from app.state import AgentState
from bson import ObjectId
from app.database.DbConnection import client,MONGODB_DATABASE
from langchain_core.messages import SystemMessage, RemoveMessage, trim_messages
import tiktoken
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
# RECENT_MESSAGES_TO_KEEP = 3
MAX_LLM_TOKENS = 1500

enc = tiktoken.encoding_for_model("gpt-4o")

def get_total_tokens(messages) -> int:
    total = 0
    for m in messages:
        content_str = str(m.content) if hasattr(m, "content") else str(m)
        total += len(enc.encode(content_str)) + 20 # Buffer for metadata/role overhead
    return total

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=300,
    max_retries=0,
)

trimmer = trim_messages(
    max_tokens=MAX_LLM_TOKENS,
    strategy="last",
    token_counter=get_total_tokens,
    include_system=True,
    allow_partial=False,
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
        context = trim_messages(
        state["messages"],
        max_tokens=MAX_LLM_TOKENS,
        strategy="last",
        token_counter=get_total_tokens,
        include_system=True,
        allow_partial=False,
        )
        print(get_total_tokens(context))
        response = llm_with_tools.invoke(context)

        return {
            "messages": [response]
        }
    except RateLimitError as e:
        print("Groq rate limit reached:", e)

        return {
            "messages": [
                AIMessage(
                    content=(
                        " The AI service has reached its usage limit. "
                        "Please try again later."
                    )
                )
            ]
        }
    except APIStatusError as e:

        if e.status_code == 413 or "too large" in str(e).lower():
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

def should_summarize(state: AgentState):
    messages = state["messages"]

    if get_total_tokens(messages) > MAX_LLM_TOKENS:
        print("should_summarize")
        return "summarize"
    print("llm")
    return "llm"

def summarize_conversation(state: AgentState):
    messages = state["messages"]

    if get_total_tokens(messages) < MAX_LLM_TOKENS:
        return {}
    
    existing_summary = None
    regular_messages = []

    for m in messages:
        if isinstance(m, SystemMessage) and "Global Conversation Summary:" in m.content:
            existing_summary = m
        else:
            regular_messages.append(m)

    recent_messages = trim_messages(
        messages,
        max_tokens=MAX_LLM_TOKENS, 
        strategy="last",
        token_counter=get_total_tokens,    
        allow_partial=False   
    )

    recent_ids = {m.id for m in recent_messages if m.id}
    old_messages = [m for m in messages if m.id not in recent_ids]

    if not old_messages:
        return {}

    previous_summary = (
        existing_summary.content
        if existing_summary
        else "None"
    )

    conversation_text = "\n".join(
        f"{message.type}: {message.content}"
        for message in old_messages
        if message.content
    )

    summary_prompt = f"""
        Summarize the previous business-agent conversation.
        Maximum: 150-250 words.
        Keep ONLY information that could help answer future user questions.

        Preserve:
        - important user requests
        - relevant business context
        - important IDs
        - important dates
        - numerical results
        - conclusions
        - information needed to understand follow-up questions

        Remove:
        - greetings
        - unnecessary wording
        - irrelevant conversation.
        - Repeated answers
        - Tool arguments
        - Raw database documents
        - Product/order/customer lists
        - ObjectIds
        - Timestamps unless important
        - Unnecessary explanations

        Previous summary:
        {previous_summary}

        Older conversation:
        {conversation_text}
        """
    try:
        response = llm.invoke(summary_prompt)
        print(response)
        summary_text = response.content if response and response.content else ""
    except Exception:
        summary_text = ""
    if not summary_text.strip():
        summary_text = f"Previous conversation containing {len(old_messages)} earlier messages and tool interactions."   

    summary_message = SystemMessage(content=f"Global Conversation Summary:\n{summary_text}")
    messages_to_delete = old_messages.copy()
    if existing_summary:
        messages_to_delete.append(existing_summary)

    delete_actions = [RemoveMessage(id=m.id) for m in messages_to_delete if m.id]

    return {
        "messages": delete_actions + [summary_message]
    }


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
builder.add_node("llm", call_llm)
builder.add_node("tools", call_tools)
builder.add_node("fallback", fallback_node)

builder.add_conditional_edges(
    START,
    should_summarize,
    {
        "summarize": "summarize",
        "llm": "llm"
    }
)
builder.add_edge("summarize", "llm")
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

checkpointer = MongoDBSaver(
    client,
    db_name=MONGODB_DATABASE
)

graph = builder.compile(checkpointer= checkpointer)