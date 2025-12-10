# pytenable_was/__init__.py

from .auth import build_headers
from .http import HTTPClient
from .scans import ScansAPI
from .apps import ApplicationsAPI
from .findings import FindingsAPI


class TenableWAS:
    """
    Unified WAS v2 API client.
    
    Provides access to:
      - ScansAPI: list scans, retrieve details, launch scans
      - ApplicationsAPI: list applications, fetch application details
      - FindingsAPI: retrieve findings for a scan

    Parameters:
        access_key (str): Tenable Access Key
        secret_key (str): Tenable Secret Key
        proxies (dict, optional): Proxy mapping passed to requests
        timeout (int): HTTP timeout in seconds
    """

    def __init__(self, access_key, secret_key, proxies=None, timeout=30):
        # Build Tenable-required auth header
        headers = build_headers(access_key, secret_key)

        # Core HTTP client shared by all API modules
        http = HTTPClient(
            base_url="https://cloud.tenable.com",
            headers=headers,
            proxies=proxies,
            timeout=timeout,
        )

        # Bind API components
        self.scans = ScansAPI(http)
        self.apps = ApplicationsAPI(http)
        self.findings = FindingsAPI(http)
