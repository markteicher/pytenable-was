# pytenable_was/http.py

"""
HTTP engine for the Tenable WAS v2 SDK.

Features:
- Clean, readable request lifecycle
- Logging on every request (method, URL, status)
- Exponential backoff handling for HTTP 429
- Structured exception mapping
- JSON parsing with safe fallbacks
- Proxy and timeout support
- Optional request/response hooks for debugging or caching
"""

import logging
import time
from typing import Any, Callable, Dict, Optional

import requests

from .errors import APIError, ThrottleError, ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    Core HTTP client used by all WAS SDK modules.

    Parameters:
        base_url (str): Base URL of Tenable.io (https://cloud.tenable.com)
        headers (dict): Authentication + content headers
        proxies (dict, optional): Proxy mapping for HTTP(S)
        timeout (int): Request timeout in seconds
        before_request (callable, optional): Debug hook
        after_response (callable, optional): Debug/cache hook
    """

    def __init__(
        self,
        base_url: str,
        headers: Dict[str, str],
        proxies: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        before_request: Optional[Callable] = None,
        after_response: Optional[Callable] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.proxies = proxies
        self.timeout = timeout
        self.before_request = before_request
        self.after_response = after_response

    # ================================================================
    # Core request handler with logging + retry + backoff
    # ================================================================
    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        attempt = 0

        # Allow debugging / tracing hooks
        if self.before_request:
            try:
                self.before_request(method, url, kwargs)
            except Exception:
                logger.warning("before_request hook raised an exception.", exc_info=True)

        logger.info("%s %s", method.upper(), url)

        while attempt < 5:
            try:
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=self.timeout,
                    **kwargs
                )

                logger.debug("HTTP %s → %s", response.status_code, url)

                # >>> Handle throttling (429 Too Many Requests)
                if response.status_code == 429:
                    delay = 2 ** attempt
                    logger.warning("HTTP 429 received. Retry #%s in %s seconds...", attempt + 1, delay)
                    time.sleep(delay)
                    attempt += 1
                    continue

                # >>> Any other non-success status code
                if response.status_code >= 400:
                    logger.error(
                        "HTTP Error %s for %s: %s",
                        response.status_code,
                        url,
                        response.text,
                    )
                    raise APIError(response.status_code, response.text, url)

                # >>> No content case
                if not response.text.strip():
                    if self.after_response:
                        try:
                            self.after_response(method, url, None)
                        except Exception:
                            logger.warning("after_response hook error.", exc_info=True)
                    return None

                # >>> Return parsed JSON
                data = response.json()

                if self.after_response:
                    try:
                        self.after_response(method, url, data)
                    except Exception:
                        logger.warning("after_response hook error.", exc_info=True)

                return data

            except requests.exceptions.Timeout:
                logger.error("Request timed out for %s", url)
                raise TimeoutError(f"Timeout while calling {url}")

            except requests.exceptions.ConnectionError as exc:
                logger.error("Connection failed for %s", url)
                raise ConnectionError(f"Connection failed for {url}") from exc

        # Too many 429 retries
        raise ThrottleError(f"Exceeded retry attempts after repeated 429 responses for {url}")

    # ================================================================
    # Public convenience wrappers
    # ================================================================
    def get(self, path: str, **kwargs) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Any:
        return self._request("POST", path, **kwargs)

    def delete(self, path: str, **kwargs) -> Any:
        return self._request("DELETE", path, **kwargs)
