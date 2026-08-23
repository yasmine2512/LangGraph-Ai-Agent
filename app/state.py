from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    routes: list[str]
    tool_calls: int


def get_recent_messages(messages, max_human_turns=3):

    system_messages = [
        m for m in messages
        if m.type == "system"
    ]
    non_system_messages = [
        m for m in messages
        if m.type != "system"
    ]
    turns = []
    current_turn = []
    human_count = 0
    for msg in reversed(non_system_messages):
        if msg.type == "tool":
            continue
        current_turn.insert(0, msg)
        if msg.type == "human":
            human_count += 1
            turns.insert(0, current_turn)
            current_turn = []
            if human_count >= max_human_turns:
                break
    flattened_recent = [
        msg
        for turn in turns
        for msg in turn
    ]

    return system_messages + flattened_recent