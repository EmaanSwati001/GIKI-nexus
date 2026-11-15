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

    # Replace whitespace between digits with hyphens (e.g. '3 0 3' -> '3-0-3')
    s_norm = re.sub(r"(?<=\d)\s+(?=\d)", "-", s)
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


# -------------------------------------------------------------------------
# Academic Unit Prefix Rules & Curation Cleaners
# -------------------------------------------------------------------------

# Approved department mapping rules per GIKI catalog conventions
COURSE_PREFIX_TO_UNIT_MAP: Dict[str, str] = {
    "HMXYZ": "fbs",
    "CYS": "fcse",
    "AI": "fcse",
    "CS": "fcse",
    "CE": "fcse",
    "DS": "fcse",
    "CY": "fcse",
    "SE": "fcse",
    "ME": "fme",
    "MT": "fbs",
    "ES": "fbs",
    "HM": "fbs",
    "EE": "fee",
    "MM": "dmse",
    "CH": "dche",
    "CV": "dcve",
    "MS": "mgs",
}


def map_course_prefix_to_unit(
    code: Optional[str], valid_unit_ids: Optional[Any] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Match course code prefixes safely at the beginning of the string.
    Does NOT use unsafe substring matching.
    Checks that mapped unit exists in valid_unit_ids.
    Returns (unit_id, matched_prefix) or (None, None).
    """
    if not code:
        return None, None

    clean_code = clean_course_code(code)
    if not clean_code:
        return None, None

    # Sort prefixes by length descending so longer prefixes match first (e.g. HMXYZ, CYS)
    sorted_prefixes = sorted(COURSE_PREFIX_TO_UNIT_MAP.keys(), key=len, reverse=True)

    for prefix in sorted_prefixes:
        # Match prefix at start, bounded by digits, 'L', hyphen, slash, space, or end
        pattern = r"^" + re.escape(prefix) + r"(?=[0-9L\-\s/]|$)"
        if re.match(pattern, clean_code, re.I):
            target_unit = COURSE_PREFIX_TO_UNIT_MAP[prefix]
            if valid_unit_ids is None or target_unit in valid_unit_ids:
                return target_unit, prefix
            return None, None

    return None, None


def normalize_instructor_name(name: Optional[str]) -> Optional[str]:
    """
    Normalize instructor names:
    - Unicode NFKC normalization
    - Strip trailing periods from common honorifics (e.g. 'Dr.' -> 'Dr')
    - Collapse whitespace
    """
    if not name:
        return None
    cleaned = normalize_text(name)
    if not cleaned:
        return None
    # Normalize common honorifics: 'Dr.' -> 'Dr', 'Mr.' -> 'Mr', etc.
    cleaned = re.sub(r"\b(Dr|Mr|Ms|Mrs|Prof|Engr)\.", r"\1", cleaned)
    # Collapse any leftover spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else None


def parse_faculty_designation_components(
    listing_desig: Optional[str],
    profile_desig: Optional[str],
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze and parse faculty designation discrepancies without inventing information.
    Distinguishes:
    - academic_rank (Professor, Associate Professor, Assistant Professor, Lecturer, Lab Engineer)
    - administrative_role (HoD, Dean, Director)
    - professional_credentials (HEC Approved PhD Supervisor, MIEEE, EUR ING)
    - preferred_designation: profile page designation is preferred display designation
      as established by project documentation, while preserving listing designation.
    """
    list_clean = normalize_text(listing_desig)
    prof_clean = normalize_text(profile_desig)
    combined = f"{list_clean or ''} {prof_clean or ''}"

    # 1. Academic Rank
    rank = None
    ranks = [
        "Associate Professor",
        "Assistant Professor",
        "Professor",
        "Lecturer",
        "Lab Engineer",
    ]
    # Check profile designation first as preferred source
    for r in ranks:
        if prof_clean and re.search(r"\b" + re.escape(r) + r"\b", prof_clean, re.I):
            rank = r
            break
    if not rank and list_clean:
        for r in ranks:
            if re.search(r"\b" + re.escape(r) + r"\b", list_clean, re.I):
                rank = r
                break

    # 2. Administrative Role
    admin_role = None
    if re.search(r"\b(HoD|Head of Department)\b", combined, re.I):
        m = re.search(r"\b(HoD|Head of Department)\s*(?:\([^)]+\)|[A-Za-z &/]+)?", combined, re.I)
        admin_role = m.group(0).strip(" -:,") if m else "Head of Department"
    elif re.search(r"\bDean\b", combined, re.I):
        m = re.search(r"\bDean(?:\s*,\s*[^,]+|\s*-\s*[A-Za-z &/]+)?", combined, re.I)
        admin_role = m.group(0).strip(" -:,") if m else "Dean"
    elif re.search(r"\bDirector\b", combined, re.I):
        admin_role = "Director / PI"

    # 3. Professional Credentials
    creds = []
    if "hec approved" in combined.lower():
        creds.append("HEC Approved PhD Supervisor")
    if "mieee" in combined.lower() or "eur ing" in combined.lower():
        creds.append("MIEEE, EUR ING")

    # 4. Discrepancy Detection
    has_discrepancy = bool(
        list_clean and prof_clean and list_clean.lower() != prof_clean.lower()
    )

    # 5. Preferred display designation
    preferred = prof_clean if prof_clean else list_clean

    # 6. Review Status
    review_status = "resolved"
    if has_discrepancy and not rank and not admin_role:
        review_status = "needs_review"

    return {
        "preferred_designation": preferred,
        "academic_rank": rank,
        "administrative_role": admin_role,
        "professional_credentials": creds,
        "designation_discrepancy": has_discrepancy,
        "designation_review_status": review_status if has_discrepancy else None,
    }
