# agentic/tools/booking.py
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.tools import tool
from data.models import cultpass
from ..db import CultpassSession


@tool
def check_booking_status(reservation_id: str) -> dict:
    """Look up a CultPass reservation's status by reservation ID."""
    if not reservation_id or not isinstance(reservation_id, str):
        return {"success": False, "error": "reservation_id must be a non-empty string."}

    try:
        with CultpassSession() as session:
            reservation = session.get(cultpass.Reservation, reservation_id)
    except SQLAlchemyError as e:
        return {"success": False, "error": f"Database error: {e}"}

    if not reservation:
        return {"success": True, "found": False, "message": f"Reservation ID {reservation_id} not found."}

    return {
        "success": True, "found": True,
        "status": reservation.status,
        "experience_title": reservation.experience.title,
    }