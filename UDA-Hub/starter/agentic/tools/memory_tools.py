# agentic/tools/memory_tools.py
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.tools import tool
from data.models import udahub
from ..db import UdahubSession
from ..config import CULTPASS_ACCOUNT_ID as ACCOUNT_ID


@tool
def list_tickets_by_category(external_user_id: str, category: str) -> dict:
    """List this customer's past ticket IDs and dates for a given category,
    when the category-level summary isn't enough and a specific past ticket needs review.
    """
    if not external_user_id or not category:
        return {"success": False, "error": "external_user_id and category are required.", "results": []}

    try:
        with UdahubSession() as session:
            user = session.execute(
                select(udahub.User).where(
                    udahub.User.account_id == ACCOUNT_ID,
                    udahub.User.external_user_id == external_user_id,
                )
            ).scalar_one_or_none()
            if user is None:
                return {"success": True, "results": []}

            rows = session.execute(
                select(udahub.Ticket.ticket_id, udahub.Ticket.created_at)
                .join(udahub.TicketMetadata, udahub.TicketMetadata.ticket_id == udahub.Ticket.ticket_id)
                .where(
                    udahub.Ticket.user_id == user.user_id,
                    udahub.TicketMetadata.main_issue_type == category,
                )
                .order_by(udahub.Ticket.created_at.desc())
            ).all()
    except SQLAlchemyError as e:
        return {"success": False, "error": f"Database error: {e}", "results": []}

    return {"success": True, "results": [{"ticket_id": tid, "date": created.isoformat()} for tid, created in rows]}


@tool
def get_ticket_detail(ticket_id: str) -> dict:
    """Fetch the full original conversation of a specific past ticket by its ID."""
    if not ticket_id:
        return {"success": False, "error": "ticket_id is required."}

    try:
        with UdahubSession() as session:
            messages = session.execute(
                select(udahub.TicketMessage)
                .where(udahub.TicketMessage.ticket_id == ticket_id)
                .order_by(udahub.TicketMessage.created_at)
            ).scalars().all()
    except SQLAlchemyError as e:
        return {"success": False, "error": f"Database error: {e}"}

    if not messages:
        return {"success": True, "found": False, "message": f"Ticket {ticket_id} not found."}

    return {"success": True, "found": True,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages]}