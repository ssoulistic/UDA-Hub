# agentic/agents/classifier.py
from typing import Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

from ..prompts import CLASSIFIER_SYSTEM_PROMPT, build_classifier_user_prompt
from ..state import TicketState, get_last_human_content
from ..memory import get_customer_history_summary
from ..config import BASE_URL
from ..logging_utils import log_event

class ClassificationResult(BaseModel):
    category: Literal["billing", "booking", "technical", "general"]
    sentiment: Literal["positive", "neutral", "negative"]
    urgency: Literal["low", "medium", "high"]
    needs_escalation: bool


llm = ChatOpenAI(model="gpt-4o-mini", base_url=BASE_URL)
structured_llm = llm.with_structured_output(ClassificationResult)


def classifier_node(state: TicketState) -> TicketState:
    ticket_content = get_last_human_content(state)
    history_summary = get_customer_history_summary(state.get("user_id", "unknown"))
    user_msg = build_classifier_user_prompt(ticket_content, history_summary)

    result = structured_llm.invoke([
        {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])
    log_event("classifier", category=result.category, urgency=result.urgency,
           needs_escalation=result.needs_escalation)
    return {
        "category": result.category,
        "sentiment": result.sentiment,
        "urgency": result.urgency,
        "needs_escalation": result.needs_escalation,
        "escalation_reason": None,
        "draft_answer": None,
        "resolver_attempts": 0,
        "is_approved": None,
        "final_answer": None,
        "resolved_by": None,
    }