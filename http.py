# http.py
import time
import requests

class HTTPClient:
    def __init__(self, base_url, headers, proxies=None, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.proxies = proxies
        self.timeout = timeout

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"

        for attempt in range(5):     # simple exponential backoff
            resp = requests.request(
                method=method.upper(),
                url=url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.timeout,
                **kwargs
            )

            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue

            if resp.status_code >= 400:
                raise Exception(f"WAS API Error {resp.status_code}: {resp.text}")

            if resp.text.strip() == "":
                return None

            return resp.json()

        raise Exception("Too many retries (429).")

    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)
