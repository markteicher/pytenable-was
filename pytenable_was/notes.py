# pytenable_was/notes.py
"""
Tenable WAS v2 Scan Notes module.

Scan Notes are diagnostic, scanner-generated messages produced during a WAS scan.
They describe issues that impacted scan execution such as authentication failures,
timeouts, unreachable URLs, unexpected HTTP responses, or misconfiguration.

This module provides:
    - list notes for a single scan
    - list notes for multiple scans (merged but labeled by scan_id)
    - flattening helpers for export (CSV/JSON-ready)
    - summary helpers
    - optional cache usage
"""

import logging
from typing import Dict, List, Optional

from .errors import TenableAPIError
from .cache import InMemoryCache

logger = logging.getLogger(__name__)


class NotesAPI:
    """
    WAS v2 Scan Notes API client.

    Endpoints:
        GET /was/v2/scans/{scan_id}/notes
    """

    def __init__(self, http, cache: Optional[InMemoryCache] = None):
        self.http = http
        self.cache = cache or InMemoryCache()

    # ----------------------------------------------------------------------
    # Raw API
    # ----------------------------------------------------------------------
    def _api_list_notes(self, scan_id: str) -> Dict:
        """
        Fetch notes for a single scan.

        Expected structure:
        {
          "pagination": { ... },
          "items": [
            {
              "scan_note_id": "...",
              "scan_id": "...",
              "created_at": "...",
              "severity": "high",
              "title": "...",
              "message": "..."
            }
          ]
        }
        """
        logger.info("Fetching notes for scan %s...", scan_id)
        return self.http.get(f"/was/v2/scans/{scan_id}/notes")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def list_notes(self, scan_id: str, use_cache: bool = True) -> List[Dict]:
        """
        List all notes for a single scan (items only, not pagination).

        Returns:
            List[Dict]
        """
        if use_cache:
            try:
                cached = self.cache.get("notes", scan_id)
                logger.debug("Loaded notes for scan %s from cache.", scan_id)
                return cached
            except Exception:
                pass

        raw = self._api_list_notes(scan_id)
        items = raw.get("items", [])

        # Cache for 10 minutes
        self.cache.set("notes", scan_id, items, ttl=600)

        logger.info("Loaded %s notes for scan %s", len(items), scan_id)
        return items

    def list_notes_multi(self, scan_ids: List[str], use_cache: bool = True) -> List[Dict]:
        """
        Retrieve notes for multiple scan IDs.

        Returns a flattened list where each record includes:
            scan_id, scan_note_id, severity, title, message, created_at, ...

        Perfect for export or bulk processing.
        """
        all_notes: List[Dict] = []

        for sid in scan_ids:
            try:
                notes = self.list_notes(sid, use_cache=use_cache)
                for n in notes:
                    rec = dict(n)
                    rec["scan_id"] = sid  # ensure labeling
                    all_notes.append(rec)
            except TenableAPIError as exc:
                logger.error("Failed retrieving notes for scan %s: %s", sid, exc)
                continue

        logger.info("Collected %s total notes across %s scan(s).",
                    len(all_notes), len(scan_ids))
        return all_notes

    # ----------------------------------------------------------------------
    # Export helpers
    # ----------------------------------------------------------------------
    def flatten(self, notes: List[Dict]) -> List[Dict]:
        """
        Notes are already essentially flat structures. This ensures:

            - all values are JSON-safe
            - unexpected nested structures are stringified
        """
        flat = []

        for n in notes:
            row = {}
            for k, v in n.items():
                if isinstance(v, (dict, list)):
                    # stringified for CSV safety
                    row[k] = str(v)
                else:
                    row[k] = v
            flat.append(row)

        return flat

    # ----------------------------------------------------------------------
    # Export-all helper (high volume)
    # ----------------------------------------------------------------------
    def list_all_notes(self, scan_ids: List[str], use_cache: bool = True) -> List[Dict]:
        """
        Fetch all notes from all provided scans.

        This is used by CLI for "notes export-all", where scan_ids
        are determined dynamically by listing all scans first.
        """
        return self.list_notes_multi(scan_ids, use_cache=use_cache)

    # ----------------------------------------------------------------------
    # Summary helper (optional)
    # ----------------------------------------------------------------------
    def summarize(self, notes: List[Dict]) -> Dict:
        """
        Generate a simple summary of note severities.

        Example:
            {
              "total": 5,
              "critical": 1,
              "high": 2,
              "medium": 1,
              "low": 1,
              "info": 0
            }
        """
        result = {
            "total": len(notes),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }

        for n in notes:
            sev = (n.get("severity") or "").lower()
            if sev in result:
                result[sev] += 1

        return result
