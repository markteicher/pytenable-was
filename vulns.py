# pytenable_was/vulns.py

"""
Tenable WAS v2 Vulnerabilities Module (Rewritten)

Supports:
    • Search vulnerabilities via /was/v2/vulns/search
    • Retrieve a single vulnerability via /was/v2/vulns/{vuln_id}
    • Export ALL vulnerabilities (search-all with pagination)
    • Flattened CSV/JSON exports
    • Progress bars via tqdm

Designed to work with the rewritten utils.py for:
    - flatten_dict
    - write_json_safe
    - write_csv_safe
    - timestamp_filename
"""

import logging
from typing import Any, Dict, List, Optional

from tqdm import tqdm

from .errors import TenableAPIError
from .utils import (
    flatten_dict,
    write_json_safe,
    write_csv_safe,
    timestamp_filename,
)

logger = logging.getLogger(__name__)


class VulnsAPI:
    """
    High-level interface for Tenable WAS v2 vulnerability data.

    Endpoints:
        POST /was/v2/vulns/search
        GET  /was/v2/vulns/{vuln_id}
    """

    def __init__(self, http):
        """
        Parameters
        ----------
        http : HTTPClient
            Configured HTTP client instance.
        """
        self.http = http

    # ----------------------------------------------------------------------
    # RAW API CALLS
    # ----------------------------------------------------------------------

    def _api_search(self, query: str = "*", limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """
        POST /was/v2/vulns/search

        Typical request body:
            {
                "query": "<lucene-like query or *>",
                "limit": 1000,
                "offset": 0
            }

        Response example:
            {
                "pagination": {
                    "total": 1234,
                    "offset": 0,
                    "limit": 1000
                },
                "items": [ ... vulnerability objects ... ]
            }
        """
        body: Dict[str, Any] = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }

        try:
            resp = self.http.post("/was/v2/vulns/search", json=body)
        except Exception as exc:
            raise TenableAPIError("Failed calling /was/v2/vulns/search") from exc

        if not isinstance(resp, dict):
            raise TenableAPIError("Malformed response from /vulns/search")

        return resp

    def _api_get_vuln(self, vuln_id: str) -> Dict[str, Any]:
        """
        GET /was/v2/vulns/{vuln_id}
        """
        try:
            resp = self.http.get(f"/was/v2/vulns/{vuln_id}")
        except Exception as exc:
            raise TenableAPIError(f"Failed retrieving vulnerability {vuln_id}") from exc

        if not isinstance(resp, dict):
            raise TenableAPIError(f"Malformed response for vulnerability {vuln_id}")

        return resp

    # ----------------------------------------------------------------------
    # PUBLIC SEARCH + GET
    # ----------------------------------------------------------------------

    def search(
        self,
        query: str = "*",
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Run a single-page vulnerability search.

        Parameters
        ----------
        query : str
            WAS v2 vulnerability search query (e.g. 'risk_factor:high').
        limit : int
            Number of records to fetch in this page.
        offset : int
            Offset of the first record.

        Returns
        -------
        List[dict]
            List of vulnerability objects.
        """
        payload = self._api_search(query=query, limit=limit, offset=offset)
        items = payload.get("items", [])
        if not isinstance(items, list):
            raise TenableAPIError("Malformed vulns.search payload: 'items' missing or invalid")
        return items

    def search_all(self, query: str = "*", page_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve ALL vulnerabilities matching the query by paging through
        /was/v2/vulns/search until all results are collected.

        Parameters
        ----------
        query : str
            Vulnerability search query. Default '*' returns all accessible vulns.
        page_size : int
            Number of vulns to fetch per API call.

        Returns
        -------
        List[dict]
            Complete list of vulnerability objects.
        """
        # First request: determine total & first page of data
        first = self._api_search(query=query, limit=page_size, offset=0)

        pagination = first.get("pagination", {}) or {}
        total = pagination.get("total", 0)
        items = first.get("items", [])
        if not isinstance(items, list):
            raise TenableAPIError("Malformed payload: 'items' not a list in first search page")

        results: List[Dict[str, Any]] = []
        results.extend(items)

        if total <= len(items):
            # all results returned in first page
            return results

        # Progress bar over total vulns; start from first page count
        pbar = tqdm(
            total=total,
            initial=len(items),
            desc="Collecting vulnerabilities",
            unit="vuln",
        )

        offset = len(items)
        while offset < total:
            page = self._api_search(query=query, limit=page_size, offset=offset)
            page_items = page.get("items", [])
            if not page_items:
                # no more or malformed; break to avoid infinite loop
                break

            results.extend(page_items)
            pbar.update(len(page_items))

            # update offset based on server pagination if present
            pagination = page.get("pagination") or {}
            server_offset = pagination.get("offset")
            server_limit = pagination.get("limit")

            if server_offset is not None and server_limit:
                offset = server_offset + server_limit
            else:
                offset += len(page_items)

        pbar.close()

        return results

    def get_vuln(self, vuln_id: str) -> Dict[str, Any]:
        """
        Retrieve a single vulnerability by ID.
        """
        return self._api_get_vuln(vuln_id)

    # ----------------------------------------------------------------------
    # FLATTENING HELPERS
    # ----------------------------------------------------------------------

    def flatten_vulns(self, vulns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Flatten a list of vulnerability objects for CSV or dataframe usage.
        """
        return [flatten_dict(v) for v in vulns]

    # ----------------------------------------------------------------------
    # EXPORT-ALL FILE WRITERS
    # ----------------------------------------------------------------------

    def export_all_vulns_json(
        self,
        path: Optional[str] = None,
        query: str = "*",
        page_size: int = 1000,
    ) -> str:
        """
        Export all vulnerabilities matching the query to a JSON file.

        If path is None, generates:
            vulns_all_<timestamp>.json
        """
        if path is None:
            path = timestamp_filename(prefix="vulns_all", ext="json")

        vulns = self.search_all(query=query, page_size=page_size)
        write_json_safe(path, vulns)
        return path

    def export_all_vulns_csv(
        self,
        path: Optional[str] = None,
        query: str = "*",
        page_size: int = 1000,
    ) -> str:
        """
        Export all vulnerabilities matching the query to a flattened CSV file.

        If path is None, generates:
            vulns_all_<timestamp>.csv
        """
        if path is None:
            path = timestamp_filename(prefix="vulns_all", ext="csv")

        vulns = self.search_all(query=query, page_size=page_size)
        flat = self.flatten_vulns(vulns)
        write_csv_safe(path, flat)
        return path
