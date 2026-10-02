# reset_udahub.py
import os
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from langchain_core.messages import (
    SystemMessage,
    HumanMessage, 
)
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

Base = declarative_base()

def reset_db(db_path: str, echo: bool = True):
    """Drops the existing udahub.db file and recreates all tables."""

    # Remove the file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ Removed existing {db_path}")

    # Create a new engine and recreate tables
    engine = create_engine(f"sqlite:///{db_path}", echo=echo)
    Base.metadata.create_all(engine)
    print(f"✅ Recreated {db_path} with fresh schema")


@contextmanager
def get_session(engine: Engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def model_to_dict(instance):
    """Convert a SQLAlchemy model instance to a dictionary."""
    return {
        column.name: getattr(instance, column.name)
        for column in instance.__table__.columns
    }

def chat_interface(agent: CompiledStateGraph, ticket_id: str, user_id: str = "unknown"):
    config = {"configurable": {"thread_id": ticket_id}}

    while True:
        user_input = input("User: ")
        print("User:", user_input)
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Assistant: Goodbye!")
            break

        result = agent.invoke(
            {"user_id": user_id, "messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        # Handle human-in-the-loop escalation
        while "__interrupt__" in result:
            payload = result["__interrupt__"][0].value
            print("\n[Escalation] Human review required:")
            print(payload)

            action = input("Approve or reject? (approve/reject): ")
            final_answer = (
                input("Enter the final answer to send to the customer: ")
                if action == "reject"
                else payload.get("draft_answer", "")
            )
            result = agent.invoke(
                Command(resume={"action": action, "final_answer": final_answer}),
                config=config,
            )

        print("Assistant:", result["messages"][-1].content)