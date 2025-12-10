# pytenable_was/__init__.py

"""
pytenable-was
A clean, modular Python client for the Tenable Web Application Scanning (WAS) v2 API.

This package exposes a single high-level interface: TenableWAS

Modules exposed:
    - auth       : Builds authentication headers
    - http       : HTTP engine (retry, throttling, proxy support)
    - scans      : Scan execution + helpers
    - apps       : Application CRUD + URL management
    - findings   : Findings retrieval + helpers
    - utils      : Shared utilities (sorting, flattening, timestamps)

The goal of this __init__.py is to provide a clean, stable public API surface.
"""

from .auth import build_headers
from .http import HTTPClient
from .scans import ScansAPI
from .apps import ApplicationsAPI
from .findings import FindingsAPI

# Public version identifier
__version__ = "0.1.0"


class TenableWAS:
    """
    High-level WAS v2 client wrapper. This class binds together all of the
    available WAS modules and provides a unified interface to the API.

    Parameters:
        access_key (str): Tenable Access Key
        secret_key (str): Tenable Secret Key
        proxies (dict, optional): Proxy mapping for HTTP(S)
        timeout (int): HTTP timeout in seconds
        base_url (str): Override only for self-hosted environments
    """

    DEFAULT_BASE_URL = "https://cloud.tenable.com"

    def __init__(self, access_key, secret_key, proxies=None, timeout=30, base_url=None):
        # Allow custom base URL but use official cloud by default
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

        # Build authentication headers
        headers = build_headers(access_key, secret_key)

        # Create shared HTTP client for all modules
        self.http = HTTPClient(
            base_url=self.base_url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
        )

        # Bind feature modules to this client
        self.scans = ScansAPI(self.http)
        self.apps = ApplicationsAPI(self.http)
        self.findings = FindingsAPI(self.http)

    # ------------------------------------------------------------
    # Convenience helpers (top-level user experience)
    # ------------------------------------------------------------
    def ping(self):
        """
        Lightweight health check.

        WAS v2 does not have a formal 'me' or 'health' endpoint,
        so this performs a minimal request that always exists.
        """
        return self.scans.list_scans()

    def version(self):
        """Return the library version."""
        return __version__

    def info(self):
        """
        Return a descriptive summary of the client configuration.
        """
        return {
            "version": __version__,
            "base_url": self.base_url,
            "modules": ["scans", "applications", "findings"],
            "http_timeout": self.http.timeout,
            "proxy_enabled": self.http.proxies is not None,
        }
