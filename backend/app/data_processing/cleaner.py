"""
Text and record cleaning utilities for GIKI Nexus data processing.
Provides safe whitespace normalization, Unicode normalization,
punctuation stripping, and field sanitization without inventing missing data.
"""

import re
import unicodedata
from typing import Optional, List, Any, Dict, Tuple


def normalize_text(text: Optional[str]) -> Optional[str]:
    """
    Normalize text:
    - Unicode NFKC normalization
    - Strips zero-width spaces and control artifacts
    - Replaces non-breaking spaces with standard spaces
    - Collapses consecutive whitespace
    - Strips leading/trailing whitespace
    Returns None if text is empty or None.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        text = str(text)

    # Normalize Unicode
    text = unicodedata.normalize("NFKC", text)

    # Remove zero-width characters and unusual whitespace
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\u00a0", " ")

    # Collapse multiple spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)
    
    # Trim leading/trailing whitespace and bullets
    text = text.strip(" \t\n\r|•-–—")

    return text if text else None


def normalize_label(label: Optional[str]) -> Optional[str]:
    """
    Normalize entity labels (such as research areas, degree names, departments):
    - Applies normalize_text
    - Strips dangling trailing parentheses, brackets, or commas
    - Balances or strips unclosed parentheses
    """
    clean = normalize_text(label)
    if not clean:
        return None

    # Fix unbalanced trailing parenthesis or punctuation
    # e.g., 'Computational Fluid Dynamics)' -> 'Computational Fluid Dynamics'
    if clean.endswith(")") and "(" not in clean:
        clean = clean[:-1].strip()
    if clean.startswith("(") and ")" not in clean:
        clean = clean[1:].strip()

    # Strip trailing punctuation
    clean = re.sub(r"[,;.:\-–—]+$", "", clean).strip()

    return clean if clean else None


def clean_string_list(items: Optional[List[Any]]) -> List[str]:
    """
    Normalize a list of strings, removing duplicates while preserving order,
    and filtering out empty or invalid items.
    """
    if not items:
        return []
    
    result = []
    seen = set()
    
    for item in items:
        norm = normalize_label(item)
        if norm and norm.lower() not in seen:
            seen.add(norm.lower())
            result.append(norm)
            
    return result


def sanitize_email(email: Optional[str]) -> Optional[str]:
    """
    Sanitize email: strip spaces, convert to lowercase.
    Returns None if empty or invalid.
    """
    if not email:
        return None
    clean = email.strip().replace(" ", "").lower()
    # Simple regex check for reasonable email format
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
        return clean
    return None


def clean_phone(phone: Optional[str]) -> Optional[str]:
    """
    Clean and normalize phone or extension number.
    """
    return normalize_text(phone)


def parse_credits(credits_val: Optional[Any]) -> Tuple[Optional[str], Optional[int]]:
    """
    Parse credit specifications:
    - Normalizes strings like '3 0 3' to '3-0-3'
    - Extracts total credit hours (last integer in pattern, e.g. '3-0-3' -> 3, '0-3-1' -> 1)
    - Returns (credits_str, credit_hours_int)
    """
    if credits_val is None:
        return None, None
    s = normalize_text(str(credits_val))
    if not s or s.lower() in {"none", "nil"}:
        return None, None

    # Replace spaces with hyphens in '3 0 3' patterns
    s_norm = re.sub(r"(\d)\s+(\d)", r"\1-\2", s)
    nums = [int(n) for n in re.findall(r"\d+", s)]
    credit_hours = nums[-1] if nums else None

    return s_norm, credit_hours


def clean_course_code(code: Optional[str]) -> Optional[str]:
    """
    Normalize course codes (e.g. 'CS 101' -> 'CS101').
    GIKI format: 'CS101', 'AI202', 'EE485', 'CE221L'.
    For placeholder/composite elective codes (e.g. 'CS3XX/CS4xx'),
    preserves slash and case distinctions so distinct elective offerings do not collide.
    """
    if not code:
        return None
    norm = normalize_text(code)
    if not norm:
        return None
    # Remove interior spaces between letters and numbers: 'CS 101' -> 'CS101'
    collapsed = re.sub(r"([A-Za-z]+)\s+(\d+)", r"\1\2", norm)
    # If standard course code without slashes or elective wildcards, uppercase it
    if "/" not in collapsed and "xx" not in collapsed.lower():
        return collapsed.upper()
    return collapsed
