# agentic/agents/escalation.py
from langgraph.types import interrupt
from langchain_core.messages import AIMessage

from ..state import TicketState, get_last_human_content
from ..memory import save_resolved_ticket
from ..logging_utils import log_event

def escalation_node(state: TicketState) -> TicketState:
    handoff_summary = {
        "category": state.get("category"),
        "sentiment": state.get("sentiment"),
        "reason_for_escalation": state.get("escalation_reason") or "Low confidence or policy requires human review",
        "draft_answer": state.get("draft_answer") or "",
    }

    human_decision = interrupt(handoff_summary) or {}
    final_answer = human_decision.get("final_answer") or state.get("draft_answer") or "No answer was generated."
    resolved_by = "human" if human_decision.get("action") == "reject" else "ai_approved_by_human"

    save_resolved_ticket(
        state.get("user_id", "unknown"), state.get("category", "general"),
        get_last_human_content(state), final_answer, resolved_by,
    )
    
    log_event("escalation", resolved_by=resolved_by)
    return {
        "final_answer": final_answer,
        "resolved_by": resolved_by,
        "messages": [AIMessage(content=final_answer)],
    }