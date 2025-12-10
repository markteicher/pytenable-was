# pytenable_was/http.py

import time
import requests
from .errors import APIError, ThrottleError


class HTTPClient:
    """
    A lightweight HTTP engine for interacting with the Tenable WAS v2 API.

    Features:
        - Centralized GET/POST/DELETE handling
        - Automatic retry with exponential backoff for HTTP 429
        - JSON-safe response parsing
        - Raised exceptions with full context
        - Proxy support via requests

    Parameters:
        base_url (str): Root URL for Tenable cloud endpoints.
        headers (dict): Authentication + content headers.
        proxies (dict): Optional HTTP/S proxy configuration.
        timeout (int): Timeout for HTTP requests.
    """

    def __init__(self, base_url, headers, proxies=None, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.proxies = proxies
        self.timeout = timeout

    # ----------------------------------------------------------------------
    # Internal request execution
    # ----------------------------------------------------------------------
    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"

        # Up to 5 retries for Tenable throttling (HTTP 429)
        for attempt in range(5):
            resp = requests.request(
                method=method.upper(),
                url=url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.timeout,
                **kwargs,
            )

            # Handle Tenable rate limiting
            if resp.status_code == 429:
                sleep_time = 2 ** attempt
                time.sleep(sleep_time)
                continue

            # Handle all other HTTP errors centrally
            if resp.status_code >= 400:
                raise APIError(resp.status_code, resp.text)

            # Handle empty responses
            if not resp.text or not resp.text.strip():
                return None

            # Parse JSON and return it
            try:
                return resp.json()
            except ValueError:
                raise APIError(resp.status_code, "Invalid JSON response")

        raise ThrottleError("Exceeded retry limit after repeated HTTP 429 responses.")

    # ----------------------------------------------------------------------
    # Public request helpers
    # ----------------------------------------------------------------------
    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)
