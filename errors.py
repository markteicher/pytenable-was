# pytenable_was/errors.py

class APIError(Exception):
    """
    Generic API error for Tenable WAS responses.

    Attributes:
        status (int): HTTP status code returned by Tenable.
        message (str): Raw response body or error description.
    """

    def __init__(self, status: int, message: str):
        super().__init__(f"API Error {status}: {message}")
        self.status = status
        self.message = message


class ThrottleError(Exception):
    """
    Raised when HTTP 429 throttling persists beyond retry limits.
    """
    pass


class PermissionError(Exception):
    """
    Raised when WAS returns an authorization/permission issue (HTTP 403).
    """
    pass


class ValidationError(Exception):
    """
    Raised when WAS returns HTTP 422 for invalid inputs or payloads.
    """
    pass
