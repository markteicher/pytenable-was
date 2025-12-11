"""
pytenable_was

Lightweight SDK + CLI helpers for Tenable Web Application Scanning (WAS) v2.

This package exposes:
    - HTTP client wrapper
    - Scan operations
    - Template operations (system + user-defined)
    - User lookup helpers for enriching scan ownership
    - CLI entrypoint (pytenable-was)
    
The SDK intentionally avoids heavy abstractions, Pydantic models, and caching
layers to remain stable against frequent Tenable API field changes.
"""

from .http import HTTPClient
from .errors import TenableAPIError
from .utils import (
    normalize_id,
    normalize_url,
    normalize_list,
    safe_get,
    parse_timestamp,
    format_iso,
    duration_seconds,
    severity_rank,
    sort_by_severity,
    group_by_severity,
    flatten_dict,
    flatten_model,
    pretty_json,
)

from .scans import ScansAPI
from .templates import TemplatesAPI
from .user_templates import UserTemplatesAPI
from .users import UsersAPI

__all__ = [
    "HTTPClient",
    "TenableAPIError",
    "normalize_id",
    "normalize_url",
    "normalize_list",
    "safe_get",
    "parse_timestamp",
    "format_iso",
    "duration_seconds",
    "severity_rank",
    "sort_by_severity",
    "group_by_severity",
    "flatten_dict",
    "flatten_model",
    "pretty_json",
    "ScansAPI",
    "TemplatesAPI",
    "UserTemplatesAPI",
    "UsersAPI",
]
