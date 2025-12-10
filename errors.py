# pytenable_was/errors.py

"""
Custom exception hierarchy for the Tenable WAS v2 SDK.

These exceptions provide meaningful structure for:
- HTTP errors returned by the WAS API
- Transport/connectivity failures
- Retry/throttling conditions
- Timeout conditions
- Model validation failures (Pydantic v2)
- Orchestration and workflow errors

All exceptions are designed to be readable, debuggable,
and consistent across the entire SDK.
"""

from typing import Any, Optional


# ================================================================
# Base SDK Error
# ================================================================
class TenableWASError(Exception):
    """Base class for all Tenable WAS SDK exceptions."""
    pass


# ================================================================
# HTTP & API Errors
# ================================================================
class APIError(TenableWASError):
    """
    Represents a non-200 HTTP response from the Tenable WAS API.

    Attributes:
        status   (int):    HTTP status code returned by the API
        message  (str):    Response text (raw)
        url      (str):    The URL requested
        payload  (Any):    Parsed JSON (if available)
    """

    def __init__(
        self,
        status: int,
        message: str,
        url: Optional[str] = None,
        payload: Optional[Any] = None,
    ):
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message
        self.url = url
        self.payload = payload

    def __str__(self):
        if self.url:
            return f"APIError {self.status} @ {self.url}: {self.message}"
        return f"APIError {self.status}: {self.message}"


class ThrottleError(TenableWASError):
    """
    Raised after repeated HTTP 429 responses despite retry attempts.
    """
    def __init__(self, message="Exceeded retry attempts due to throttling"):
        super().__init__(message)


# ================================================================
# Transport & Connectivity
# ================================================================
class ConnectionError(TenableWASError):
    """Raised when a network connectivity failure occurs."""
    pass


class TimeoutError(TenableWASError):
    """
    Raised for both:
    - request-level timeouts (HTTP layer)
    - orchestration timeouts (scan wait loops)
    """
    pass


# ================================================================
# Validation Errors (Model Layer)
# ================================================================
class ModelValidationError(TenableWASError):
    """
    Wraps Pydantic validation errors.

    Attributes:
        errors (list): Pydantic error objects
        raw    (Any):  The original payload that failed validation
    """
    def __init__(self, errors: Any, raw: Any = None):
        super().__init__("Model validation failed")
        self.errors = errors
        self.raw = raw

    def __str__(self):
        return f"Validation failed: {self.errors}"


# ================================================================
# Orchestration / Workflow Errors
# ================================================================
class ScanWaitError(TenableWASError):
    """Raised when a scan enters an unexpected status during wait cycle."""
    def __init__(self, scan_id: str, status: str):
        super().__init__(f"Unexpected scan status '{status}' for scan {scan_id}")
        self.scan_id = scan_id
        self.status = status


class NotFoundError(TenableWASError):
    """Raised when a requested entity does not exist (SDK-level resolution)."""
    def __init__(self, entity: str, identifier: str):
        super().__init__(f"{entity} not found: {identifier}")
        self.entity = entity
        self.identifier = identifier


class CacheKeyError(TenableWASError):
    """Raised when the in-memory cache misses or has type mismatches."""
    def __init__(self, key: str):
        super().__init__(f"Cache key not found: {key}")
        self.key = key
