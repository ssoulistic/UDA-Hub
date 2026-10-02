# UDA-Hub

A LangGraph-based multi-agent customer support system for **CultPass**, a
cultural-experience membership service. Incoming tickets are classified,
resolved against a RAG-grounded knowledge base, reviewed by a supervisor
agent, and escalated to a human via human-in-the-loop when confidence is
low — with persistent short-term and long-term memory across the
conversation.

## Getting Started

Instructions for how to get a copy of the project running on your local
machine.

### Dependencies

```
python >= 3.11
langgraph>=0.5.4
langgraph-checkpoint-sqlite>=2.0.0
langchain>=0.3.27
langchain-core>=0.3.72
langchain-openai>=0.3.28
sqlalchemy>=2.0.41
pydantic>=2.0.0
python-dotenv>=1.1.1
ipykernel>=6.30.0
```

(See `requirements.txt` for the full pinned list.)

### Installation

Step by step explanation of how to get a dev environment running.

1. Clone the repository and create a virtual environment:

```
git clone <repo-url>
cd uda-hub
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

2. Copy the environment template and fill in your API key:

```
cp .env.example .env
```

3. Seed the databases by running the setup notebooks in order:

```
01_external_db_setup.ipynb   # seeds data/external/cultpass.db
02_core_db_setup.ipynb       # seeds data/core/udahub.db
```

4. Run the agentic app:

```
03_agentic_app.ipynb
```

## Testing

This project is verified through interactive scenario testing rather than
an automated test suite. Run `03_agentic_app.ipynb` and invoke
`chat_interface(orchestrator, "<ticket_id>", "<user_id>")` with the demo
tickets below to confirm correct classification, resolution, and
escalation behavior across categories.

### Break Down Tests

```python
chat_interface(orchestrator, "demo_1", "f556c0")
# Input: My QR code won't scan at the venue entrance.
# -> Resolved by RAG (search_knowledge match), no escalation needed.

chat_interface(orchestrator, "demo_2", "a4ab87")
# Input: Someone next to me was very loud during last week's concert
#        and I want to file a complaint.
# -> No confident knowledge match -> escalated to human review.

chat_interface(orchestrator, "demo_3", "f556c0")
# Input: My QR code failed again today, same as before.
# -> Same user, repeated issue; resolver finds no article addressing
#    repeated failures -> escalated even though the supervisor approved
#    the draft.

chat_interface(orchestrator, "demo_4", "f556c0")
# Input: My payment was charged twice right now and I need this fixed
#        urgently.
# -> Classifier flags urgency=high and needs_escalation immediately ->
#    escalated regardless of supervisor's decision.
```

Each scenario uses a distinct `thread_id` (`demo_1`-`demo_4`) so
checkpointed state doesn't bleed across tickets, and reuses
`external_user_id`s from the seeded CultPass users (`f556c0`, `a4ab87`) to
exercise the long-term memory lookup (`get_customer_history_summary`).

## End-to-End Demo

### Scenario 1: Successful AI resolution (RAG hit)

Classifier -> Resolver (search_knowledge hit) -> Supervisor (approved) -> END

### Scenario 2: Escalation due to no relevant knowledge found (RAG miss)

Classifier -> Resolver (search_knowledge miss, needs_escalation=True) -> Supervisor -> Escalation -> interrupt -> END

### Scenario 3: Returning customer — repeated issue raises urgency

Classifier -> Resolver (search_knowledge miss on repeated-issue query, needs_escalation=True) -> Supervisor (approved) -> Escalation (needs_escalation overrides approval) -> interrupt -> END

### Scenario 4: High urgency ticket routed directly to escalation

Classifier (urgency=high, needs_escalation=True) -> Resolver (confirms needs_escalation=True) -> Supervisor (rejected) -> Escalation -> interrupt -> END

## Project Instructions

This section should contain all the student deliverables for this project.

- Multi-agent architecture: Classifier -> Resolver -> Supervisor ->
  Escalation, orchestrated as a LangGraph `StateGraph`.
- Intelligent routing based on ticket metadata (category, sentiment,
  urgency) with a fixed priority order: escalation flag -> approval ->
  urgency -> retry limit.
- RAG-based knowledge retrieval (`search_knowledge`) with relevance
  scoring and escalation when no confident match is found.
- 5 DB-abstracted tools (`search_knowledge`, `search_experiences`,
  `check_booking_status`, `list_tickets_by_category`, `get_ticket_detail`)
  with input validation and `try/except SQLAlchemyError` handling.
- Persistent short-term memory via `SqliteSaver` (thread-scoped by
  ticket_id) and long-term memory via `udahub.db`
  (User / Ticket / TicketMetadata / TicketMessage).
- Full end-to-end integration with structured JSON logging of every
  agent decision and tool call.

See `design/architecture.md` for the full pipeline diagram and design
rationale.

## Built With

* [LangGraph](https://www.langchain.com/langgraph) - Multi-agent orchestration, conditional routing, and human-in-the-loop via `interrupt()`
* [LangChain](https://www.langchain.com/) - LLM integration and tool-calling abstractions
* [OpenAI API](https://platform.openai.com/) - gpt-4o / gpt-4o-mini via Vocareum proxy
* [SQLAlchemy](https://www.sqlalchemy.org/) - ORM for cultpass.db and udahub.db
* [Pydantic](https://docs.pydantic.dev/) - Structured output schemas for agent responses
* [SQLite](https://www.sqlite.org/) - Persistence layer (business data + CS system of record)

## License

[License](../LICENSE.md)