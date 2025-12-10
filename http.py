# http.py
"""
HTTP Client for Tenable WAS v2
==============================

Handles:
    - Authentication headers (accessKey / secretKey)
    - GET, POST, PUT, DELETE
    - Proxy support
    - Retry logic for 429 Too Many Requests
    - JSON decoding and error wrapping
"""

import json
import time
import requests
from .errors import TenableAPIError


class HTTPClient:
    """
    Thin wrapper around requests with:
        - WAS v2 authentication headers
        - automatic error handling
        - retry for status 429
        - proxy support
    """

    BASE_URL = "https://cloud.tenable.com"

    def __init__(self, access_key: str, secret_key: str, proxy: str = None, timeout: int = 30):
        self.access_key = access_key
        self.secret_key = secret_key
        self.timeout = timeout

        # Proxy format for requests:
        #   {"http": "<proxy>", "https": "<proxy>"}
        self.proxies = None
        if proxy:
            self.proxies = {
                "http": proxy,
                "https": proxy
            }

    # ------------------------------------------------------------------
    # BASE HEADERS
    # ------------------------------------------------------------------
    def _headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-ApiKeys": f"accessKey={self.access_key}; secretKey={self.secret_key}"
        }

    # ------------------------------------------------------------------
    # HTTP WRAPPER WITH RETRIES
    # ------------------------------------------------------------------
    def _request(self, method: str, path: str, json_body=None):
        url = f"{self.BASE_URL}{path}"

        # Retry loop for 429 Too Many Requests
        retries = 5
        backoff = 2

        while True:
            try:
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=self._headers(),
                    json=json_body,
                    proxies=self.proxies,
                    timeout=self.timeout
                )
            except requests.RequestException as exc:
                raise TenableAPIError(f"HTTP Request Failed: {exc}")

            # Handle 429
            if response.status_code == 429:
                if retries <= 0:
                    raise TenableAPIError("Too many retries (429 Too Many Requests)")
                time.sleep(backoff)
                retries -= 1
                backoff *= 2
                continue

            # Success or error — break loop
            break

        # ------------------------------------------------------------------
        # Error Handling
        # ------------------------------------------------------------------
        if response.status_code >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = response.text or ""

            raise TenableAPIError(
                f"HTTP {response.status_code}: {payload}"
            )

        # ------------------------------------------------------------------
        # Decode JSON
        # ------------------------------------------------------------------
        try:
            return response.json()
        except ValueError:
            raise TenableAPIError("Invalid JSON response from Tenable API.")

    # ------------------------------------------------------------------
    # PUBLIC HTTP VERBS
    # ------------------------------------------------------------------
    def get(self, path: str):
        return self._request("GET", path)

    def post(self, path: str, json=None):
        return self._request("POST", path, json_body=json)

    def put(self, path: str, json=None):
        return self._request("PUT", path, json_body=json)

    def delete(self, path: str):
        return self._request("DELETE", path)
