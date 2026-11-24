import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Streamlit Community Cloud secrets are exposed through st.secrets.
try:
    import streamlit as st
    _secrets = st.secrets
except Exception:
    _secrets = {}

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "data" / "feedback_analyzer.db"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip() or str(_secrets.get("OPENAI_API_KEY", "")).strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "").strip() or str(_secrets.get("OPENAI_MODEL", "gpt-4.1-mini")).strip()
