# agentic/tools/knowledge.py
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.tools import tool
from data.models import udahub
from ..db import UdahubSession
from ..config import CULTPASS_ACCOUNT_ID


@tool
def search_knowledge(query: str) -> dict:
    """Search the CultPass support knowledge base for policy and how-to articles.

    query: keywords describing the customer's issue.
    Returns matching articles with a relevance score, or empty results if nothing relevant is found —
    signaling that the question may need human escalation instead of an AI-generated answer.
    """
    if not query or not isinstance(query, str):
        return {"success": False, "error": "query must be a non-empty string.", "results": []}

    keywords = [w.strip() for w in query.lower().split() if len(w.strip()) > 2]
    if not keywords:
        return {"success": True, "results": []}

    try:
        with UdahubSession() as session:
            stmt = select(udahub.Knowledge).where(udahub.Knowledge.account_id == CULTPASS_ACCOUNT_ID)
            results = session.execute(stmt).scalars().all()
    except SQLAlchemyError as e:
        return {"success": False, "error": f"Database error: {e}", "results": []}

    scored = []
    for article in results:
        haystack = f"{article.title} {article.content} {article.tags or ''}".lower()
        score = sum(1 for kw in keywords if kw in haystack)
        if score > 0:
            scored.append((score, article))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    return {
        "success": True,
        "results": [
            {"title": a.title, "content": a.content, "tags": a.tags, "relevance_score": s}
            for s, a in scored[:3]
        ],
    }