"""
SDK + CLI for Tenable Web Application Scanning (WAS) v2.

Provides:
    - HTTP client for WAS v2
    - Pydantic v2 data models
    - Scan lifecycle operations
    - Application CRUD operations
    - Findings retrieval, filtering, flattening
    - Optional command-line interface
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
    Unified client for interacting with the Tenable WAS v2 API.

    Example:
        >>> client = WASClient(access_key="...", secret_key="...")
        >>> scans = client.scans.list_all()
        >>> apps  = client.apps.list_all()
        >>> findings = client.findings.list_findings(scan_id)
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        proxy: str = None,
        base_url: str = "https://cloud.tenable.com",
        user_agent: str = "tenable-was-sdk/1.0",
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

        self.scans = ScansAPI(http=http, cache=cache)
        self.apps = ApplicationsAPI(http=http, cache=cache)
        self.findings = FindingsAPI(http=http, cache=cache)
