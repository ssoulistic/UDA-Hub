# agentic/state.py
from typing import TypedDict, List, Literal, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TicketState(TypedDict, total=False):
    user_id: str
    messages: Annotated[List[BaseMessage], add_messages]
    category: Literal["billing", "booking", "technical", "general"]
    sentiment: Literal["positive", "neutral", "negative"]
    urgency: Literal["low", "medium", "high"]
    needs_escalation: bool
    escalation_reason: str
    draft_answer: str
    is_approved: bool
    final_answer: str
    resolved_by: str
    resolver_attempts: int

# 가장 최근 사용자 메시지를 티켓 내용으로 사용하기 위한 헬퍼
def get_last_human_content(state: TicketState) -> str:
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            return msg.content
    return ""