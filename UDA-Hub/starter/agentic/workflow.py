from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from .state import TicketState
from .agents.classifier import classifier_node
from .agents.resolver import resolver_node
from .agents.supervisor import supervisor_node
from .agents.escalation import escalation_node
MAX_RESOLVER_ATTEMPTS = 3

def route_after_supervisor(state: TicketState) -> str:
    if state.get("needs_escalation"):
        return "escalation"
    if state.get("is_approved"):
        return END
    if state.get("urgency") == "high":
        return "escalation"
    if state.get("resolver_attempts", 0) >= MAX_RESOLVER_ATTEMPTS:
        return "escalation" 
    return "resolver"

graph = StateGraph(TicketState)
graph.add_node("classifier", classifier_node)
graph.add_node("resolver", resolver_node)
graph.add_node("supervisor", supervisor_node)
graph.add_node("escalation", escalation_node)

graph.set_entry_point("classifier")

graph.add_edge("classifier", "resolver")  # 무조건 이어야 함 (조건부 아님)
graph.add_edge("resolver", "supervisor")  # 항상 Supervisor를 거침

graph.add_conditional_edges("supervisor", route_after_supervisor)

graph.add_edge("escalation", END)

conn = sqlite3.connect("data/external/checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
orchestrator = graph.compile(checkpointer=checkpointer)