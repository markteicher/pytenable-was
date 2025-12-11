# pytenable_was/notes.py

"""
WAS v2 — Scan Notes API
=======================

Scan Notes are diagnostic messages automatically generated *by the Tenable Web
App Scanning engine* during a scan. They are **not vulnerabilities** and they are
**not user-authored**. Notes appear only when the scanner detects conditions that
affect scan success, configuration, or coverage.

Each scan note includes:

    - scan_note_id : Unique identifier for the note
    - scan_id      : ID of the scan that produced the note
    - created_at   : Timestamp (ISO8601)
    - severity     : Critical / High / Medium / Low / Info
    - title        : Short label describing the issue
    - message      : Detailed context + troubleshooting guidance

Notes provide actionable insight into why a scan may:
    - fail authentication
    - miss expected coverage
    - encounter redirects or blocked paths
    - detect misconfiguration conditions
    - experience performance or timeout issues

Tenable refers to these as **Scan Notes Severity Details**.

Endpoint:
    GET /was/v2/scans/{scan_id}/notes
"""

import logging
from typing import Dict, List, Optional

from .errors import TenableAPIError
from .utils import parse_timestamp, flatten_dict

logger = logging.getLogger(__name__)


class NotesAPI:
    """
    Client wrapper for the WAS v2 Scan Notes endpoint.

    Provides:
        - list_notes(scan_id)
        - flatten_notes(scan_id)
    """

    def __init__(self, http):
        self.http = http

    # ----------------------------------------------------------------------
    # Raw API call
    # ----------------------------------------------------------------------
    def _api_list_notes(self, scan_id: str) -> Dict:
        """
        Retrieve all scan notes associated with a scan.

        API:
            GET /was/v2/scans/{scan_id}/notes
        """
        if not scan_id:
            raise TenableAPIError("scan_id is required for listing notes")

        logger.info("Fetching scan notes for scan %s...", scan_id)
        return self.http.get(f"/was/v2/scans/{scan_id}/notes")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def list_notes(self, scan_id: str) -> List[Dict]:
        """
        Return the raw scan note dictionaries exactly as Tenable provides them.

        Response format:
            {
              "pagination": {...},
              "items": [
                 {
                    "scan_note_id": "...",
                    "scan_id": "...",
                    "created_at": "...",
                    "severity": "high",
                    "title": "Authentication Failed",
                    "message": "The scanner was unable to authenticate ..."
                 }
              ]
            }
        """
        raw = self._api_list_notes(scan_id)
        items = raw.get("items") or []

        logger.info("Loaded %s scan notes for scan %s", len(items), scan_id)
        return items

    # ----------------------------------------------------------------------
    def flatten_notes(self, scan_id: str) -> List[Dict]:
        """
        Flatten note objects for CSV export.

        Each row includes:
            scan_note_id
            scan_id
            created_at
            severity
            title
            message
            (additional fields if added by Tenable)
        """
        notes = self.list_notes(scan_id)
        flat = []

        for n in notes:
            row = flatten_dict(n)
            # Convert ISO timestamps to epoch for easier ingestion
            if "created_at" in n:
                row["created_at_epoch"] = parse_timestamp(n["created_at"])
            flat.append(row)

        return flat
