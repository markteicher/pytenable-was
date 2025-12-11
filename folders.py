# pytenable_was/folders.py

"""
Tenable WAS v2 Folders API

Endpoint:
    GET /was/v2/folders

Folders are used to organize scans and applications in the UI,
but the API provides only a read-only listing endpoint.

This module provides:
    • list() → returns list of folder dictionaries
"""

import logging
from typing import List, Dict, Any

from .errors import TenableAPIError

logger = logging.getLogger(__name__)


class FoldersAPI:
    """
    Lightweight client for WAS folders.

    Only operation supported:
        GET /was/v2/folders
    """

    def __init__(self, http):
        self.http = http

    def list(self) -> List[Dict[str, Any]]:
        """
        Return all folders as a list of dicts.

        Expected fields include:
            folder_id
            name
            created_at
            updated_at
            permissions (varies)
        """
        logger.info("Fetching WAS folder list...")

        try:
            resp = self.http.get("/was/v2/folders")
        except Exception as exc:
            raise TenableAPIError(f"Failed to retrieve folders: {exc}")

        # Tenable may return:
        #  { "items": [...] }
        #  or  { "folders": [...] }
        folders = resp.get("items") or resp.get("folders") or []

        if not isinstance(folders, list):
            raise TenableAPIError(
                "Malformed response from /folders endpoint (expected list)."
            )

        return folders
