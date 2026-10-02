# agentic/memory.py
import uuid
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from langchain_openai import ChatOpenAI
from data.models import udahub
from .db import UdahubSession
from .config import BASE_URL, CULTPASS_ACCOUNT_ID as ACCOUNT_ID

_summarizer = ChatOpenAI(model="gpt-4o-mini", base_url=BASE_URL)


def _summarize_issue(issue_text: str) -> str:
    try:
        response = _summarizer.invoke([
            {"role": "system", "content": "Summarize the customer's issue in under 15 words. Keep the key fact. No preamble."},
            {"role": "user", "content": issue_text},
        ])
        return response.content.strip()
    except Exception:
        return issue_text[:100]


def save_resolved_ticket(external_user_id: str, category: str, issue: str,
                          resolution: str, resolved_by: str) -> bool:
    try:
        with UdahubSession() as session:
            user = session.execute(
                select(udahub.User).where(
                    udahub.User.account_id == ACCOUNT_ID,
                    udahub.User.external_user_id == external_user_id,
                )
            ).scalar_one_or_none()

            if user is None:
                user = udahub.User(
                    user_id=str(uuid.uuid4()),
                    account_id=ACCOUNT_ID,
                    external_user_id=external_user_id,
                    user_name=external_user_id,
                )
                session.add(user)
                session.flush()

            ticket_id = str(uuid.uuid4())
            session.add(udahub.Ticket(
                ticket_id=ticket_id, account_id=ACCOUNT_ID,
                user_id=user.user_id, channel="chat",
            ))
            session.add(udahub.TicketMetadata(
                ticket_id=ticket_id, status="resolved",
                main_issue_type=category, tags=resolved_by,
            ))
            session.add(udahub.TicketMessage(
                message_id=str(uuid.uuid4()), ticket_id=ticket_id,
                role=udahub.RoleEnum.user, content=issue,
            ))
            session.add(udahub.TicketMessage(
                message_id=str(uuid.uuid4()), ticket_id=ticket_id,
                role=udahub.RoleEnum.agent if resolved_by == "human" else udahub.RoleEnum.ai,
                content=resolution,
            ))
            session.commit()
        return True
    except SQLAlchemyError:
        return False


def get_customer_history_summary(external_user_id: str) -> str:
    try:
        with UdahubSession() as session:
            user = session.execute(
                select(udahub.User).where(
                    udahub.User.account_id == ACCOUNT_ID,
                    udahub.User.external_user_id == external_user_id,
                )
            ).scalar_one_or_none()
            if user is None:
                return "No prior history."

            rows = session.execute(
                select(
                    udahub.TicketMetadata.main_issue_type,
                    func.count(udahub.Ticket.ticket_id),
                    func.max(udahub.Ticket.created_at),
                )
                .join(udahub.Ticket, udahub.Ticket.ticket_id == udahub.TicketMetadata.ticket_id)
                .where(udahub.Ticket.user_id == user.user_id)
                .group_by(udahub.TicketMetadata.main_issue_type)
            ).all()
    except SQLAlchemyError:
        return "No prior history."

    if not rows:
        return "No prior history."

    return "\n".join(
        f"- {category}: {count} past ticket(s), most recent {last_date.date()}"
        for category, count, last_date in rows
    )