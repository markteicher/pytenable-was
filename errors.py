# errors.py
"""
Error Types for pytenable-was
=============================

All Tenable WAS HTTP and API-related failures are wrapped in a single
TenableAPIError exception to keep error handling simple and consistent.
"""


class TenableAPIError(Exception):
    """
    Generic error for all Tenable WAS API failures.

    Supports:
        - status code (optional)
        - error message (string or dict)
        - response payload

    Used by:
        http.py      → error wrapping for HTTP 4xx/5xx
        cli.py       → user-friendly error messages
        configs.py   → malformed response detection
        templates.py → CRUD error surfacing
        scans.py     → owner resolution failures
        users.py     → lookup failures
    """

    def __init__(self, message, status_code=None, payload=None):
        """
        Parameters
        ----------
        message : str
            Human-readable error message.
        status_code : int, optional
            HTTP status code if applicable.
        payload : dict or str, optional
            Raw response body from Tenable API.
        """
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload

    def __str__(self):
        base = super().__str__()
        if self.status_code:
            base = f"[HTTP {self.status_code}] {base}"
        if self.payload:
            base += f" | Payload: {self.payload}"
        return base
