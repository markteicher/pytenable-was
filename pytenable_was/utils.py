# pytenable_was/utils.py

"""
Utility functions for the Tenable WAS v2 SDK.

This module provides:
    - ID and URL normalization
    - UUID validation
    - safe dictionary access for nested data
    - timestamp parsing and formatting helpers
    - severity ranking, sorting, and grouping
    - flattening helpers for CSV/JSON exports
    - JSON pretty-printing for CLI/log output

All helpers are intentionally fast, predictable, and dependency-free.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ======================================================================
# NORMALIZATION & IDENTIFIERS
# ======================================================================

_UUID_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)


def normalize_id(value: Optional[Any]) -> Optional[str]:
    """
    Normalize an ID (scan, app, finding, template, etc.) to a clean string.

    - Converts the value to `str`.
    - Strips leading/trailing whitespace.
    - Preserves `None` as `None`.
    """
    if value is None:
        return None
    return str(value).strip()


def normalize_url(url: Optional[str]) -> Optional[str]:
    """
    Normalize a WAS URL field.

    - Returns `None` if url is falsy.
    - Strips whitespace.
    - Lowercases the URL.

    This is intentionally simple; it does *not* validate URL format.
    """
    if not url:
        return None
    return url.strip().lower()


def normalize_list(value: Any) -> List[Any]:
    """
    Ensure the value is always returned as a list.

    - If value is `None` → returns [].
    - If value is already a list → returns it as-is.
    - Otherwise → wraps the value in a single-element list.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def is_uuid(value: Optional[str]) -> bool:
    """
    Check whether a string looks like a canonical UUID (8-4-4-4-12 hex).

    Returns:
        True if the value matches the UUID pattern, False otherwise.

    This does *not* check that the UUID is valid in any backend system,
    only that it is syntactically well-formed.
    """
    if not value:
        return False
    return bool(_UUID_REGEX.match(str(value)))


# ======================================================================
# SAFE DICT ACCESS
# ======================================================================

def safe_get(data: Any, *keys, default=None):
    """
    Safely navigate nested dictionaries.

    Example:
        safe_get(obj, "metadata", "scan", "status")

    Behavior:
        - If at any point the current value is not a dict, returns `default`.
        - If a key is missing, returns `default`.
        - If the final value is None, returns `default`.

    This is useful when traversing WAS responses where fields may be
    missing or structurally inconsistent between records.
    """
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


# ======================================================================
# TIME HELPERS
# ======================================================================

def parse_timestamp(ts: Any) -> Optional[int]:
    """
    Parse a timestamp from Tenable WAS payloads into epoch seconds (int).

    Accepted formats:
        - int / float epoch values
        - str containing an integer epoch
        - ISO8601 string (e.g., '2025-01-01T12:00:00Z')

    Returns:
        - epoch seconds as int, or
        - None if parsing fails
    """
    if ts is None:
        return None

    # Already an int-like?
    try:
        return int(ts)
    except Exception:
        pass

    # ISO8601-style string
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        logger.debug("Unsupported timestamp format: %s", ts)
        return None


def format_iso(ts: Optional[int]) -> Optional[str]:
    """
    Convert epoch seconds to an ISO8601 UTC string with trailing 'Z'.

    Example:
        1700000000 -> '2023-11-14T22:13:20Z'

    Returns:
        ISO8601 string, or None if ts is None or invalid.
    """
    if ts is None:
        return None
    try:
        return datetime.utcfromtimestamp(ts).isoformat() + "Z"
    except Exception:
        return None


def duration_seconds(start: Any, end: Any) -> Optional[int]:
    """
    Compute duration in seconds between two timestamps.

    Both `start` and `end` can be any format accepted by `parse_timestamp`.

    Returns:
        Non-negative integer number of seconds, or None if either timestamp
        cannot be parsed.
    """
    s = parse_timestamp(start)
    e = parse_timestamp(end)
    if s is None or e is None:
        return None
    return max(0, e - s)


# ======================================================================
# SEVERITY RANKING + SORTING
# ======================================================================

SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}


def severity_rank(sev: Optional[str]) -> int:
    """
    Map a severity label to a numeric rank.

    Known severities (case-insensitive):
        critical > high > medium > low > info

    Unknown or missing severities return -1.
    """
    if not sev:
        return -1
    return SEVERITY_ORDER.get(sev.lower(), -1)


def sort_by_severity(
    findings: List[Dict[str, Any]],
    key: str = "severity",
    reverse: bool = True,
) -> List[Dict[str, Any]]:
    """
    Sort a list of finding dicts by severity rank.

    Args:
        findings:
            List of dicts; each dict *should* have `key` (default 'severity').
        key:
            Field name holding severity string in each finding.
        reverse:
            Whether to sort from highest to lowest severity (default True).

    Returns:
        New list sorted according to severity_rank().
    """
    return sorted(findings, key=lambda f: severity_rank(f.get(key)), reverse=reverse)


def group_by_severity(findings: List[Any]) -> Dict[str, List[Any]]:
    """
    Group findings by severity label.

    Each element in `findings` may be:
        - a dict with a 'severity' key, or
        - an object with a `.severity` attribute.

    Returns:
        Dict of:
            {
                "critical": [...],
                "high": [...],
                "medium": [...],
                "low": [...],
                "info": [...],
                "unknown": [...]
            }
    """
    groups: Dict[str, List[Any]] = {k: [] for k in SEVERITY_ORDER}
    groups["unknown"] = []

    for f in findings:
        if hasattr(f, "severity"):
            sev_val = getattr(f, "severity", "")
        elif isinstance(f, dict):
            sev_val = f.get("severity", "")
        else:
            sev_val = ""

        sev = str(sev_val).lower()
        if sev in groups:
            groups[sev].append(f)
        else:
            groups["unknown"].append(f)

    return groups


# ======================================================================
# FLATTENING UTILITIES (for CSV / DataFrames)
# ======================================================================

def flatten_dict(
    data: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary for CSV or dataframe loading.

    Example:
        {"a": {"b": 1}} → {"a.b": 1}

    Lists are left as-is and not expanded; callers can decide how to
    handle list-valued fields.
    """
    flattened: Dict[str, Any] = {}
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            flattened.update(flatten_dict(v, new_key, sep=sep))
        else:
            flattened[new_key] = v
    return flattened


def flatten_model(model: Any) -> Dict[str, Any]:
    """
    Convert a Pydantic model or plain dict into a flat dict.

    For Pydantic v1/v2 models, `model_dump()` is used if available.
    For plain dicts, the dict is flattened directly.

    Raises:
        ValueError if the input is neither a dict nor a Pydantic-like object.
    """
    if hasattr(model, "model_dump"):
        data = model.model_dump()
    elif isinstance(model, dict):
        data = model
    else:
        raise ValueError("flatten_model requires a dict or a Pydantic model-like object")

    return flatten_dict(data)


# ======================================================================
# JSON PRETTY PRINT
# ======================================================================

def pretty_json(data: Any) -> str:
    """
    Return pretty-printed JSON for structured data.

    - Uses json.dumps(indent=2, sort_keys=True).
    - Falls back to str(data) if serialization fails.

    Intended for CLI output and logging where human-readable JSON
    is helpful for debugging or inspection.
    """
    try:
        return json.dumps(data, indent=2, sort_keys=True)
    except Exception:
        return str(data)
