# agentic/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_cultpass_engine = create_engine("sqlite:///data/external/cultpass.db")
_udahub_engine = create_engine("sqlite:///data/core/udahub.db")

CultpassSession = sessionmaker(bind=_cultpass_engine)
UdahubSession = sessionmaker(bind=_udahub_engine)