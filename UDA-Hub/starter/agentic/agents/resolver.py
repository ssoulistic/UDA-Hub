# agentic/agents/resolver.py
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

from ..prompts import RESOLVER_SYSTEM_PROMPT, build_resolver_user_prompt
from ..tools.knowledge import search_knowledge
from ..tools.experiences import search_experiences
from ..tools.booking import check_booking_status
from ..tools.memory_tools import list_tickets_by_category, get_ticket_detail
from ..state import TicketState, get_last_human_content
from ..config import BASE_URL
from ..logging_utils import log_event

import time
from json import JSONDecodeError,dumps

TOOLS = [search_knowledge, search_experiences, check_booking_status,
         list_tickets_by_category, get_ticket_detail]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


class ResolverOutput(BaseModel):
    draft_answer: str
    needs_escalation: bool
    escalation_reason: str = ""


llm = ChatOpenAI(model="gpt-4o", base_url=BASE_URL)
llm_with_tools = llm.bind_tools(TOOLS)
structured_llm = llm.with_structured_output(ResolverOutput)


def _invoke_with_retry(llm_obj, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return llm_obj.invoke(messages)
        except JSONDecodeError:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
            
            
def resolver_node(state: TicketState) -> TicketState:
    ticket_content = get_last_human_content(state)
    user_msg = build_resolver_user_prompt(ticket_content, state.get("escalation_reason") or "")

    messages = [
        {"role": "system", "content": RESOLVER_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
    response = _invoke_with_retry(llm_with_tools, messages)

    tool_calls_made = []   
    while response.tool_calls:
        messages.append(response)
        for call in response.tool_calls:
            tool_calls_made.append({"tool": call["name"], "args": call["args"]}) 
            tool_result = TOOLS_BY_NAME[call["name"]].invoke(call["args"])
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": dumps(tool_result, ensure_ascii=False)})
        response = _invoke_with_retry(llm_with_tools, messages)

    final = _invoke_with_retry(structured_llm, messages + [
    {"role": "user", "content": "Based on the above, provide your final structured output."}
])

    final_needs_escalation = state.get("needs_escalation") or final.needs_escalation

    log_event("resolver", attempt=state.get("resolver_attempts", 0)+1,
            tools_called=tool_calls_made,
            classifier_flagged=state.get("needs_escalation"),   # Classifier가 뭐라 했는지
            resolver_flagged=final.needs_escalation,              # Resolver 혼자 뭐라 했는지
            final_needs_escalation=final_needs_escalation)  


    return {
    "draft_answer": final.draft_answer or "No relevant information was found for this request.",
    "needs_escalation": state.get("needs_escalation") or final.needs_escalation,
    "escalation_reason": state.get("escalation_reason") or (final.escalation_reason or None),
    "resolver_attempts": state.get("resolver_attempts", 0) + 1,
}