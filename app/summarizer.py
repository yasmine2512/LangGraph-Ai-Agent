from pydantic import BaseModel
from langchain_core.messages import SystemMessage, RemoveMessage
import tiktoken
from app.llm import llm
from app.state import AgentState,get_recent_messages,extract_text

MAX_LLM_TOKENS = 5000

enc = tiktoken.encoding_for_model("gpt-4o")

def get_total_tokens(messages) -> int:
    total = 0
    for m in messages:
        content_str = str(m.content) if hasattr(m, "content") else str(m)
        total += len(enc.encode(content_str)) + 20 
    return total


def should_summarize(state: AgentState):
    messages = state["messages"]

    if get_total_tokens(messages) > MAX_LLM_TOKENS:
        return "summarize"
    return "router"

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

    recent_messages = get_recent_messages(messages,max_human_turns=3)

    recent_ids = {m.id for m in recent_messages if m.id is not None}
    old_messages = [m for m in messages if m.id not in recent_ids]

    if not old_messages:
        return {}

    previous_summary = (
        existing_summary.content
        if existing_summary
        else "None"
    )

    conversation_text = "\n".join(
    f"{m.type}: {m.content}"
    for m in old_messages
    if m.content and m.type != "tool"
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
        print("Summary:",response,"\n")
        summary_text = extract_text(response.content) if response and response.content else ""

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