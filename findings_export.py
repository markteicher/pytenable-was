# pytenable_was/findings_export.py

"""
Tenable WAS v2 Export Findings API

Endpoint:
    POST /was/v2/export/findings

This endpoint returns a complete findings payload for the given scan_id.
It is the preferred way to export large scans because it bypasses
pagination and returns a fully enumerated dataset.

This module supports:
    • JSON export
    • CSV export
    • Flattening of nested structures for tabular output
"""

import csv
import json
from typing import Dict, List, Any

from .errors import TenableAPIError


class FindingsExportAPI:
    """
    Wrapper around the WAS findings export endpoint.

    Usage (via CLI):
        pytenable-was scans export-findings <scan_id> --csv-out auto
        pytenable-was scans export-findings <scan_id> --json-out auto
    """

    def __init__(self, http):
        self.http = http

    # -------------------------------------------------------------------
    # RAW API CALL
    # -------------------------------------------------------------------
    def _api_export(self, scan_id: str) -> Dict[str, Any]:
        """
        POST /was/v2/export/findings

        Payload format:
            { "scan_id": "<id>" }

        Returns JSON:
            {
                "scan_id": "...",
                "findings": [...]
            }
        """
        body = {"scan_id": scan_id}
        resp = self.http.post("/was/v2/export/findings", json=body)

        if not isinstance(resp, dict):
            raise TenableAPIError("Malformed export response")

        return resp

    # -------------------------------------------------------------------
    # FLATTENING UTILITIES
    # -------------------------------------------------------------------
    def _flatten_dict(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert nested dicts/lists into CSV-safe flattened rows.

        Rules:
            • Lists   → comma-separated strings
            • Dicts   → JSON string
            • Scalars → preserved
        """
        flat = {}

        for key, val in obj.items():
            if val is None:
                flat[key] = None
                continue

            # simple scalar
            if isinstance(val, (str, int, float, bool)):
                flat[key] = val
                continue

            # list → join
            if isinstance(val, list):
                flat[key] = ", ".join(str(v) for v in val)
                continue

            # dict → JSON
            if isinstance(val, dict):
                try:
                    flat[key] = json.dumps(val, ensure_ascii=False)
                except Exception:
                    flat[key] = str(val)
                continue

            # fallback
            flat[key] = str(val)

        return flat

    # -------------------------------------------------------------------
    # PUBLIC EXPORT METHODS
    # -------------------------------------------------------------------
    def export_json(self, scan_id: str, path: str) -> str:
        """
        Export full findings result to a JSON file.
        """
        payload = self._api_export(scan_id)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return path

    def export_csv(self, scan_id: str, path: str) -> str:
        """
        Export findings to a CSV file.
        Automatically flattens nested structures.
        """
        payload = self._api_export(scan_id)
        findings = payload.get("findings")

        if not findings:
            raise TenableAPIError(f"No findings returned for scan {scan_id}")

        # flatten all rows
        rows = [self._flatten_dict(f) for f in findings]

        # ensure stable CSV headers
        headers = sorted(rows[0].keys())

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        return path
