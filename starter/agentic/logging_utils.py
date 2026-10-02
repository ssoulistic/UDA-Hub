# agentic/logging_utils.py
from json import dumps
from datetime import datetime

def log_event(node: str, **fields):
    entry = {"timestamp": datetime.now().isoformat(), "node": node, **fields}
    print(dumps(entry, ensure_ascii=False))