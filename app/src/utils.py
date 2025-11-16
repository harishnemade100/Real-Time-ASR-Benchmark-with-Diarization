"""
Shared utilities
"""
from datetime import datetime, timezone
import re

def iso_now():
    return datetime.now(timezone.utc).isoformat()

def normalize_text(s: str) -> str:
    s2 = s.lower()
    s2 = re.sub(r"[^a-z0-9\s]+", "", s2)
    s2 = re.sub(r"\s+", " ", s2).strip()
    return s2