# pytenable_was/notes.py

"""
Tenable WAS v2 Scan Notes module.

Notes are *scanner-generated diagnostics* — failures, warnings,
auth issues, unreachable URLs, parser errors, etc.

Endpoint:
    GET /was/v2/scans/{scan_id}/notes
"""

import logging
from typing import Dict, List

from .http import HTTPClient
from .errors import TenableAPIError
from .utils import flatten_model

logger = logging.getLogger(__name__)


class NotesAPI:
    """
    WAS v2 Scan Notes API wrapper.

    Provides:
        - list notes for a scan
        - flatten notes for CSV/JSON export
    """

    def __init__(self, http: HTTPClient):
        self.http = http

    # --------------------------------------------------------------
    # Raw API call
    # --------------------------------------------------------------
    def _api_list_notes(self, scan_id: str) -> Dict:
        logger.info(f"Fetching notes for scan {scan_id}...")
        return self.http.get(f"/was/v2/scans/{scan_id}/notes")

    # --------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------
    def list_notes(self, scan_id: str) -> List[Dict]:
        """
        Returns:
            A list of note dictionaries, exactly reflecting WAS output.

        Example note:
        {
            "scan_note_id": "...",
            "scan_id": "...",
            "created_at": "2020-04-07T00:17:37Z",
            "severity": "high",
            "title": "Authentication Failed",
            "message": "The scanner was unable to authenticate..."
        }
        """
        raw = self._api_list_notes(scan_id)
        return raw.get("items") or []

    def flatten(self, scan_id: str) -> List[Dict]:
        """
        Flatten notes into export-friendly dicts.
        """
        notes = self.list_notes(scan_id)
        return [flatten_model(n) for n in notes]
