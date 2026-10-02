# agentic/agents/supervisor.py
from typing import Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

from ..prompts import SUPERVISOR_SYSTEM_PROMPT
from ..state import TicketState, get_last_human_content
from ..memory import save_resolved_ticket
from ..config import BASE_URL, MAX_RESOLVER_ATTEMPTS
from ..logging_utils import log_event

class SupervisorReview(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str


llm = ChatOpenAI(model="gpt-4o-mini", base_url=BASE_URL)
structured_llm = llm.with_structured_output(SupervisorReview)


def supervisor_node(state: TicketState) -> TicketState:
    draft = state.get("draft_answer", "")
    review = structured_llm.invoke([
        {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
        {"role": "user", "content": draft},
    ])

    if review.decision == "approve":
        save_resolved_ticket(
            state.get("user_id", "unknown"), state.get("category", "general"),
            get_last_human_content(state), draft, "ai",
        )
        log_event("supervisor", decision=review.decision)
        return {
            "is_approved": True,
            "final_answer": draft,
            "resolved_by": "ai",
            "messages": [AIMessage(content=draft)],
        }

    attempts = state.get("resolver_attempts", 0)
    if attempts >= MAX_RESOLVER_ATTEMPTS:
        reason = f"Resolver failed to produce an approved answer after {attempts} attempts. Last rejection reason: {review.reason}"
    else:
        reason = review.reason
    log_event("supervisor", decision=review.decision, reason=review.reason)
    return {"is_approved": False, "escalation_reason": reason}