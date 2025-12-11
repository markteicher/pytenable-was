"""
HTTP Client for Tenable WAS v2

Handles:
    - X-API-Key authentication
    - GET, POST, PUT, DELETE
    - Proxy support
    - 429 retry with exponential backoff
    - JSON decoding
    - TenableAPIError wrapping
"""

import time
import requests
from typing import Any, Dict, Optional
from .errors import TenableAPIError


class HTTPClient:
    BASE_URL = "https://cloud.tenable.com"

    def __init__(self, api_key: str, proxy: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout

        self.proxies = None
        if proxy:
            self.proxies = {
                "http": proxy,
                "https": proxy
            }

    # ------------------------------------------------------------
    # Build headers
    # ------------------------------------------------------------
    def _headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    # ------------------------------------------------------------
    # Internal request wrapper
    # ------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ):
        url = f"{self.BASE_URL}{path}"

        retries = 5
        backoff = 2

        while True:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    params=params,
                    json=json_body,
                    proxies=self.proxies,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise TenableAPIError(f"HTTP request failed: {exc}")

            # Handle rate-limiting
            if response.status_code == 429:
                if retries <= 0:
                    raise TenableAPIError("Too many retries (429 Too Many Requests)")
                time.sleep(backoff)
                retries -= 1
                backoff *= 2
                continue

            break

        # Error handling
        if response.status_code >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = response.text or ""
            raise TenableAPIError(
                message="Tenable API error",
                status_code=response.status_code,
                payload=payload,
            )

        # No content
        if response.status_code == 204:
            return None

        # JSON response
        try:
            return response.json()
        except ValueError:
            raise TenableAPIError("Invalid JSON response from Tenable API.")

    # ------------------------------------------------------------
    # Public verbs
    # ------------------------------------------------------------
    def get(self, path: str, params: Optional[Dict[str, Any]] = None):
        return self._request("GET", path, params=params)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None):
        return self._request("POST", path, json_body=json)

    def put(self, path: str, json: Optional[Dict[str, Any]] = None):
        return self._request("PUT", path, json_body=json)

    def delete(self, path: str):
        return self._request("DELETE", path)
