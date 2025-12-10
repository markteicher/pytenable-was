# pytenable_was/utils.py

import json
import time
from datetime import datetime


# =====================================================================
# JSON & SERIALIZATION HELPERS
# =====================================================================

def pretty_json(data):
    """
    Return pretty JSON string for logging or display.
    """
    return json.dumps(data, indent=2, sort_keys=True)


def safe_get(d: dict, *keys, default=None):
    """
    Helper to safely extract nested dictionary fields.
    Example:
        safe_get(scan, "metadata", "status")
    """
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
    return d if d is not None else default


def flatten_dict(d: dict, parent_key="", sep="."):
    """
    Shallow JSON flattener suitable for CSV export.
    """
    items = {}
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items


# =====================================================================
# SEVERITY + CLASSIFICATION HELPERS
# =====================================================================

SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}


def severity_rank(severity: str):
    """
    Convert severity label into numeric rank.
    """
    if not severity:
        return -1
    return SEVERITY_ORDER.get(severity.lower(), -1)


def sort_by_severity(items, key="severity", descending=True):
    """
    Sort list of findings or objects by severity ranking.
    """
    return sorted(
        items,
        key=lambda x: severity_rank(x.get(key)),
        reverse=descending,
    )


# =====================================================================
# TIMESTAMP HELPERS
# =====================================================================

def parse_timestamp(ts):
    """
    Parse Tenable WAS timestamps (numeric or ISO8601).
    Returns UNIX epoch seconds or None.
    """
    if ts is None:
        return None

    # Numeric timestamps
    try:
        return int(ts)
    except:
        pass

    # ISO8601 timestamps
    try:
        return int(datetime.fromisoformat(ts).timestamp())
    except:
        return None


def duration(start, end):
    """
    Compute duration in seconds between two timestamps.
    """
    s = parse_timestamp(start)
    e = parse_timestamp(end)
    if s is None or e is None:
        return None
    return max(e - s, 0)


# =====================================================================
# POLLING + WAIT HELPERS (shared for scans + future features)
# =====================================================================

def wait_for_condition(
    check_fn,
    interval=20,
    timeout=7200,
    terminal_values=None,
):
    """
    Generic polling helper.
    Executed by scans.wait_until_complete() under the hood.

    check_fn: function returning a value to test
    terminal_values: list of values that stop polling
    """
    start = time.time()

    while True:
        value = check_fn()

        if terminal_values and value in terminal_values:
            return value

        if (time.time() - start) > timeout:
            raise TimeoutError("Polling timed out before condition met.")

        time.sleep(interval)


# =====================================================================
# NORMALIZATION HELPERS
# =====================================================================

def normalize_url(u: str):
    """
    Lowercase + strip + safe cleanup for URLs used in scans/findings.
    """
    if not u:
        return None
    return u.strip().lower()


def normalize_id(val):
    """
    Normalize IDs (scan_id, app_id, finding_id, etc.)
    """
    if val is None:
        return None
    return str(val).strip()


# =====================================================================
# EXPORT HELPERS
# =====================================================================

def to_export_rows(records, flatten=False):
    """
    Convert list of dicts into export-ready rows.
    If flatten=True, flatten nested structures.
    """
    out = []
    for rec in records:
        if flatten:
            out.append(flatten_dict(rec))
        else:
            out.append(rec)
    return out
