# pytenable_was/utils.py

"""
Utility functions for the Tenable WAS v2 SDK.

This module provides:
    - ID and URL normalization
    - timestamp parsing utilities
    - severity ranking and sort helpers
    - flattening for CSV/JSON exports
    - pretty-printing for structured output
    - grouping and filtering helpers
    - safe dictionary access
    - model introspection utilities

All helpers are intentionally fast, predictable, and dependency-free.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# ======================================================================
# NORMALIZATION HELPERS
# ======================================================================

def normalize_id(value: Optional[Any]) -> Optional[str]:
    """Normalize a scan/app/finding ID to a clean string."""
    if value is None:
        return None
    return str(value).strip()


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize a WAS URL field."""
    if not url:
        return None
    return url.strip().lower()


def normalize_list(value: Any) -> List[Any]:
    """Ensure the value is always returned as a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


# ======================================================================
# SAFE DICT ACCESS
# ======================================================================

def safe_get(data: Any, *keys, default=None):
    """
    Safely navigate nested dictionaries.

    Example:
        safe_get(obj, "metadata", "scan", "status")
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
    Parse timestamps from Tenable WAS payloads.

    Accepts:
        - integers (epoch)
        - strings containing integers
        - ISO timestamps
    """
    if ts is None:
        return None

    # Already an int?
    try:
        return int(ts)
    except Exception:
        pass

    # ISO8601?
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        logger.debug("Unsupported timestamp format: %s", ts)
        return None


def format_iso(ts: Optional[int]) -> Optional[str]:
    """Convert epoch seconds to ISO8601."""
    if ts is None:
        return None
    try:
        return datetime.utcfromtimestamp(ts).isoformat() + "Z"
    except Exception:
        return None


def duration_seconds(start: Any, end: Any) -> Optional[int]:
    """Compute duration in seconds from two timestamps."""
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
    """Return numeric severity ranking."""
    if not sev:
        return -1
    return SEVERITY_ORDER.get(sev.lower(), -1)


def sort_by_severity(findings: List[Dict[str, Any]], key: str = "severity", reverse=True):
    """Sort findings by severity ranking."""
    return sorted(findings, key=lambda f: severity_rank(f.get(key)), reverse=reverse)


def group_by_severity(findings: List[Any]):
    """
    Group findings by severity label.

    Returns:
        {
            "critical": [...],
            "high": [...],
            ...
        }
    """
    groups: Dict[str, List[Any]] = {k: [] for k in SEVERITY_ORDER}
    for f in findings:
        sev = (f.severity if hasattr(f, "severity") else f.get("severity", "")).lower()
        if sev in groups:
            groups[sev].append(f)
        else:
            groups.setdefault("unknown", []).append(f)
    return groups


# ======================================================================
# FLATTENING UTILITIES (for CSV export)
# ======================================================================

def flatten_dict(data: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten a nested dictionary for CSV or dataframe loading.
    Example:
        {"a": {"b": 1}} → {"a.b": 1}
    """
    flattened = {}
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            flattened.update(flatten_dict(v, new_key, sep=sep))
        else:
            flattened[new_key] = v
    return flattened


def flatten_model(model: Any) -> Dict[str, Any]:
    """
    Convert a Pydantic model (or dict) into a flat dict.
    """
    if hasattr(model, "model_dump"):
        data = model.model_dump()
    elif isinstance(model, dict):
        data = model
    else:
        raise ValueError("flatten_model requires dict or Pydantic model")

    return flatten_dict(data)


# ======================================================================
# JSON PRETTY PRINT
# ======================================================================

def pretty_json(data: Any) -> str:
    """Return pretty JSON (for CLI output or logging)."""
    try:
        return json.dumps(data, indent=2, sort_keys=True)
    except Exception:
        return str(data)
