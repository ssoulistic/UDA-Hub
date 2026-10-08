# agentic/logging_utils.py
from datetime import datetime
from json import dumps
from pathlib import Path

LOG_PATH = Path("logs/events.jsonl")
LOG_PATH.parent.mkdir(exist_ok=True)

def log_event(node: str, **fields):
    entry = {"timestamp": datetime.now().isoformat(), "node": node, **fields}
    line = dumps(entry, ensure_ascii=False)
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")