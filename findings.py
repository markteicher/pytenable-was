# pytenable_was/findings.py

"""
Tenable WAS v2 Findings Module (Rewritten)

Supports:
    • Retrieve findings for a single scan
    • Export findings using /export/findings (full bulk export)
    • Export flattened CSV/JSON
    • Export ALL findings across ALL scans
    • Progress bars (tqdm)
    • Unified flattening, writing, and error handling via utils

This module replaces the older findings_export.py by integrating its
/export/findings logic directly into the findings API.
"""

import logging
from typing import List, Dict, Any, Optional

from tqdm import tqdm

from .errors import TenableAPIError
from .utils import (
    flatten_dict,
    write_csv_safe,
    write_json_safe,
    timestamp_filename,
)

logger = logging.getLogger(__name__)


class FindingsAPI:
    """
    High-level interface for retrieving and exporting Tenable WAS findings.

    Endpoints used:
        GET  /was/v2/scans/{scan_id}/findings
        POST /was/v2/export/findings

    Raw API methods:
        • _api_get_findings()
        • _api_export_findings()

    Public operations:
        • list_findings()
        • export_findings_json()
        • export_findings_csv()
        • export_all_findings()
        • export_all_findings_flat()
    """

    def __init__(self, http, scans_api):
        """
        Parameters
        ----------
        http : HTTPClient
            Configured HTTP client w/ auth + retry logic.
        scans_api : ScansAPI
            Required so we can iterate all scans during export-all.
        """
        self.http = http
        self.scans = scans_api

    # --------------------------------------------------------------------------
    # RAW API CALLS
    # --------------------------------------------------------------------------

    def _api_get_findings(self, scan_id: str) -> Dict[str, Any]:
        """
        GET /was/v2/scans/{scan_id}/findings
        May be paginated on Tenable's side; returned JSON usually includes:
            { "findings": [...], "pagination": ... }
        """
        try:
            return self.http.get(f"/was/v2/scans/{scan_id}/findings")
        except Exception as exc:
            raise TenableAPIError(
                f"Failed retrieving findings for scan {scan_id}"
            ) from exc

    def _api_export_findings(self, scan_id: str) -> Dict[str, Any]:
        """
        POST /was/v2/export/findings
        Returns the FULL findings payload for a scan (not paginated).

        Example:
            {
                "scan_id": "...",
                "findings": [...]
            }
        """
        body = {"scan_id": scan_id}
        try:
            return self.http.post("/was/v2/export/findings", json=body)
        except Exception as exc:
            raise TenableAPIError(
                f"Failed exporting findings for scan {scan_id}"
            ) from exc

    # --------------------------------------------------------------------------
    # RETRIEVE + NORMALIZE
    # --------------------------------------------------------------------------

    def list_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve findings using GET /findings.
        May be partial for very large scans. Prefer export_findings_* for full data.
        """
        payload = self._api_get_findings(scan_id)
        findings = payload.get("findings", [])
        if not isinstance(findings, list):
            raise TenableAPIError("Malformed findings payload")
        return findings

    def export_findings_full(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve *full* findings for a scan using /export/findings.

        This is the preferred method when exporting a single scan’s entire dataset.
        """
        payload = self._api_export_findings(scan_id)
        findings = payload.get("findings", [])
        if not isinstance(findings, list):
            raise TenableAPIError("Malformed export-findings payload")
        return findings

    # --------------------------------------------------------------------------
    # EXPORT SINGLE SCAN (JSON/CSV)
    # --------------------------------------------------------------------------

    def export_findings_json(self, scan_id: str, path: Optional[str] = None) -> str:
        """
        Export full findings to JSON.

        If path is None, generates:
            findings_<scanid>_<timestamp>.json
        """
        if path is None:
            path = timestamp_filename(prefix=f"findings_{scan_id}", ext="json")

        findings = self.export_findings_full(scan_id)
        payload = {"scan_id": scan_id, "findings": findings}
        write_json_safe(path, payload)
        return path

    def export_findings_csv(self, scan_id: str, path: Optional[str] = None) -> str:
        """
        Export full findings to CSV (flattened rows).

        If path is None, generates:
            findings_<scanid>_<timestamp>.csv
        """
        if path is None:
            path = timestamp_filename(prefix=f"findings_{scan_id}", ext="csv")

        findings = self.export_findings_full(scan_id)
        rows = [flatten_dict(f) for f in findings]
        write_csv_safe(path, rows)
        return path

    # --------------------------------------------------------------------------
    # EXPORT-ALL FINDINGS ACROSS ALL SCANS
    # --------------------------------------------------------------------------

    def export_all_findings(self) -> List[Dict[str, Any]]:
        """
        Return **raw, unflattened** findings for EVERY scan in the tenant.

        Returns:
            [
                {"scan_id": "...", "findings": [...]},
                ...
            ]
        """
        scans = self.scans.list_scans()
        results = []

        for sc in tqdm(scans, desc="Exporting findings (raw)", unit="scan"):
            scan_id = sc.get("scan_id") or sc.get("id")
            if not scan_id:
                continue

            try:
                findings = self.export_findings_full(scan_id)
                results.append({
                    "scan_id": scan_id,
                    "findings": findings
                })
            except TenableAPIError as exc:
                logger.error("Failed exporting scan %s: %s", scan_id, exc)

        return results

    def export_all_findings_flat(self) -> List[Dict[str, Any]]:
        """
        Return a single flattened list of ALL findings across ALL scans.

        Output:
            [
                {
                    "scan_id": "...",
                    "<flattened fields>": ...
                },
                ...
            ]
        """
        scans = self.scans.list_scans()
        all_rows = []

        for sc in tqdm(scans, desc="Exporting findings (flattened)", unit="scan"):
            scan_id = sc.get("scan_id") or sc.get("id")
            if not scan_id:
                continue

            try:
                findings = self.export_findings_full(scan_id)
            except TenableAPIError:
                continue

            for f in findings:
                flat = flatten_dict(f)
                flat["scan_id"] = scan_id
                all_rows.append(flat)

        return all_rows

    # --------------------------------------------------------------------------
    # EXPORT-ALL FILE WRITERS (JSON/CSV)
    # --------------------------------------------------------------------------

    def export_all_findings_json(self, path: Optional[str] = None) -> str:
        """
        Write all raw findings for all scans to a JSON file.
        """
        if path is None:
            path = timestamp_filename(prefix="findings_all", ext="json")

        data = self.export_all_findings()
        write_json_safe(path, data)
        return path

    def export_all_findings_csv(self, path: Optional[str] = None) -> str:
        """
        Write all flattened findings for all scans to a CSV file.
        """
        if path is None:
            path = timestamp_filename(prefix="findings_all", ext="csv")

        rows = self.export_all_findings_flat()
        write_csv_safe(path, rows)
        return path
