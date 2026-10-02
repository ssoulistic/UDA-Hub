# agentic/tools/experiences.py
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.tools import tool
from data.models import cultpass
from ..db import CultpassSession


@tool
def search_experiences(location: str = "", keyword: str = "") -> dict:
    """Search CultPass's experience catalog by location and/or keyword.

    location: city/region name. Leave empty to search all locations.
    keyword: word to match in title or description. Leave empty for no filtering.
    """
    if not isinstance(location, str) or not isinstance(keyword, str):
        return {"success": False, "error": "location and keyword must be strings.", "results": []}

    try:
        with CultpassSession() as session:
            query = select(cultpass.Experience)
            if location:
                query = query.where(cultpass.Experience.location.ilike(f"%{location}%"))
            if keyword:
                query = query.where(or_(
                    cultpass.Experience.title.ilike(f"%{keyword}%"),
                    cultpass.Experience.description.ilike(f"%{keyword}%"),
                ))
            rows = session.execute(query).scalars().all()
    except SQLAlchemyError as e:
        return {"success": False, "error": f"Database error: {e}", "results": []}

    return {
        "success": True,
        "results": [
            {"title": e.title, "location": e.location, "when": e.when.isoformat(),
             "slots_available": e.slots_available, "is_premium": e.is_premium}
            for e in rows
        ],
    }