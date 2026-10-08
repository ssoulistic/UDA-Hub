# agentic/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
MAX_RESOLVER_ATTEMPTS = 3
CULTPASS_ACCOUNT_ID = "cultpass"