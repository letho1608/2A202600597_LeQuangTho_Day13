from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "jwt": r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}\b",
    "bearer_token": r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}",
    "credit_card": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
    "cccd": r"(?<!\d)\d{12}(?!\d)",
    "passport": r"\b[A-Z]{1,2}\d{6,9}\b",
    "phone_vn": r"(?<!\d)0\d{2}[ \.-]?\d{3}[ \.-]?\d{3,4}(?!\d)",
    "phone_intl": r"(?<!\d)\+\d{1,3}[ \.-]?\d{2,4}[ \.-]?\d{2,4}[ \.-]?\d{2,4}(?!\d)",
    "ip_v4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
