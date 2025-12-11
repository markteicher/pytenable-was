# pytenable_was/scans.py

"""
Tenable WAS v2 Scans Module (Rewritten)

Supports:
    • List scans
    • Retrieve scan details
    • Change owner for a single scan
    • Bulk owner change for many scans
    • Export all scan details to JSON/CSV
    • Flattening for Splunk/DataFrame ingestion
    • Pagination-safe full scan listing
    • tqdm progress for long operations
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


class ScansAPI:
    """
    WAS v2 Scans API wrapper.

    Endpoints supported:
        GET   /was/v2/scans
        GET   /was/v2/scans/{scan_id}
        PATCH /was/v2/scans/{scan_id}   (owner changes)
    """

    def __init__(self, http):
        self.http = http

    # ----------------------------------------------------------------------
    # RAW ENDPOINT CALLS
    # ----------------------------------------------------------------------

    def _api_list_scans(self, limit: int = 200, offset: int = 0) -> Dict[str, Any]:
        """
        GET /was/v2/scans

        WAS v2 scans API uses pagination:
            ?limit=200&offset=0
        """
        path = f"/was/v2/scans?limit={limit}&offset={offset}"

        try:
            resp = self.http.get(path)
        except Exception as exc:
            raise TenableAPIError("Failed calling GET /was/v2/scans") from exc

        if not isinstance(resp, dict):
            raise TenableAPIError("Malformed response from scans list API")

        return resp

    def _api_get_scan(self, scan_id: str) -> Dict[str, Any]:
        """
        GET /was/v2/scans/{scan_id}
        """
        try:
            resp = self.http.get(f"/was/v2/scans/{scan_id}")
        except Exception as exc:
            raise TenableAPIError(f"Failed retrieving scan {scan_id}") from exc

        if not isinstance(resp, dict):
            raise TenableAPIError(f"Malformed scan details response for {scan_id}")

        return resp

    def _api_patch_scan(self, scan_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        PATCH /was/v2/scans/{scan_id}

        Used to modify metadata, including ownership.
        """
        try:
            resp = self.http.patch(f"/was/v2/scans/{scan_id}", json=body)
        except Exception as exc:
            raise TenableAPIError(f"Failed modifying scan {scan_id}") from exc

        if not isinstance(resp, dict):
            raise TenableAPIError(f"Malformed PATCH response for scan {scan_id}")

        return resp

    # ----------------------------------------------------------------------
    # PUBLIC: LIST SCANS
    # ----------------------------------------------------------------------

    def list_scans(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Retrieve ALL scans (pagination-aware).
        """
        first = self._api_list_scans(limit=limit, offset=0)

        pagination = first.get("pagination", {}) or {}
        total = pagination.get("total", 0)
        items = first.get("items", [])

        if not isinstance(items, list):
            raise TenableAPIError("Malformed scans payload: items not a list")

        results = list(items)

        if total <= len(items):
            return results

        pbar = tqdm(
            total=total,
            initial=len(items),
            unit="scan",
            desc="Collecting scans",
        )

        offset = len(items)

        while offset < total:
            page = self._api_list_scans(limit=limit, offset=offset)
            page_items = page.get("items", [])

            if not page_items:
                break

            results.extend(page_items)
            pbar.update(len(page_items))

            pagination = page.get("pagination") or {}
            server_offset = pagination.get("offset")
            server_limit = pagination.get("limit")

            if server_offset is not None and server_limit:
                offset = server_offset + server_limit
            else:
                offset += len(page_items)

        pbar.close()

        return results

    # ----------------------------------------------------------------------
    # PUBLIC: SCAN DETAILS
    # ----------------------------------------------------------------------

    def get_scan(self, scan_id: str) -> Dict[str, Any]:
        """
        Return WAS scan metadata/details.
        """
        return self._api_get_scan(scan_id)

    # ----------------------------------------------------------------------
    # OWNER MANAGEMENT
    # ----------------------------------------------------------------------

    def change_owner(self, scan_id: str, new_owner_id: str) -> Dict[str, Any]:
        """
        Change the owner of a single scan.

        PATCH /was/v2/scans/{scan_id}
        Body:
            {
                "owner_id": "<user_id>"
            }
        """
        body = {"owner_id": new_owner_id}
        return self._api_patch_scan(scan_id, body)

    def change_owner_bulk(
        self,
        scan_ids: List[str],
        new_owner_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Update owner for many scans with progress tracking.
        """
        results: List[Dict[str, Any]] = []

        for scan_id in tqdm(scan_ids, desc="Updating scan owners", unit="scan"):
            resp = self.change_owner(scan_id, new_owner_id)
            results.append(
                {
                    "scan_id": scan_id,
                    "new_owner": new_owner_id,
                    "status": "ok",
                }
            )

        return results

    # ----------------------------------------------------------------------
    # EXPORT SCAN DETAILS
    # ----------------------------------------------------------------------

    def export_all_scans_json(self, path: Optional[str] = None) -> str:
        """
        Export ALL scans into a JSON file.
        """
        if path is None:
            path = timestamp_filename("scans_all", "json")

        scans = self.list_scans()
        write_json_safe(path, scans)
        return path

    def export_all_scans_csv(self, path: Optional[str] = None) -> str:
        """
        Export ALL scans into a flattened CSV file.
        """
        if path is None:
            path = timestamp_filename("scans_all", "csv")

        scans = self.list_scans()
        flat = [flatten_dict(s) for s in scans]
        write_csv_safe(path, flat)
        return path

    # ----------------------------------------------------------------------
    # SIMPLE SUMMARIES
    # ----------------------------------------------------------------------

    def summary(self, scan_id: str) -> Dict[str, Any]:
        """
        Convenience helper for CLI dashboards.

        Returns fields like:
            scan_id
            name
            status
            created_at
            finished_at
            owner_id
        """
        s = self.get_scan(scan_id)

        return {
            "scan_id": s.get("scan_id"),
            "name": s.get("name"),
            "status": s.get("status"),
            "created_at": s.get("created_at"),
            "finished_at": s.get("finished_at"),
            "owner_id": s.get("owner_id"),
        }
