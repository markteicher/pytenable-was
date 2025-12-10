"""
pytenable_was
=============

Tenable Web Application Scanning (WAS) v2 SDK.

Features:
    - Pydantic v2 modeling
    - In-memory caching
    - Retry + throttle-safe HTTP client
    - Full CRUD for Applications
    - Full Scan lifecycle orchestration
    - Findings retrieval, filtering, grouping, flattening
    - CLI with credential prompting + verbose/debug modes
"""

from .auth import build_headers
from .http import HTTPClient
from .cache import InMemoryCache

from .scans import ScansAPI
from .apps import ApplicationsAPI
from .findings import FindingsAPI

from .models import (
    ScanModel,
    ScanSummary,
    ApplicationModel,
    URLModel,
    FindingModel,
    FindingsSet,
)

__all__ = [
    "build_headers",
    "HTTPClient",
    "InMemoryCache",
    "ScansAPI",
    "ApplicationsAPI",
    "FindingsAPI",
    "ScanModel",
    "ScanSummary",
    "ApplicationModel",
    "URLModel",
    "FindingModel",
    "FindingsSet",
    "WASClient",
]


class WASClient:
    """
    High-level unified client for the Tenable WAS v2 SDK.

    Example:
        >>> client = WASClient(access_key="...", secret_key="...")
        >>> scans = client.scans.list_all()
        >>> apps  = client.apps.list_all()
        >>> fset  = client.findings.list_findings(scan_id)

    The WASClient consolidates common setup steps and exposes
    the three core APIs using a single configured HTTP client.
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        proxy: str = None,
        base_url: str = "https://cloud.tenable.com",
        user_agent: str = "pytenable-was/1.0",
        timeout: int = 30,
    ):
        headers = build_headers(
            access_key=access_key,
            secret_key=secret_key,
            user_agent=user_agent,
        )

        proxies = None
        if proxy:
            proxies = {
                "http": proxy,
                "https": proxy,
            }

        http = HTTPClient(
            base_url=base_url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
        )

        cache = InMemoryCache()

        # Public API submodules
        self.scans = ScansAPI(http=http, cache=cache)
        self.apps = ApplicationsAPI(http=http, cache=cache)
        self.findings = FindingsAPI(http=http, cache=cache)
