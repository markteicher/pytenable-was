# pytenable_was/scans.py

"""
Tenable WAS v2 Scans API

Supports:
    - Listing all scans
    - Retrieving detailed scan info
    - Safe model parsing (no breakage if Tenable changes fields)
    - Optional caching for performance

This module is intentionally lightweight and dictionary-oriented.
"""

import logging
from typing import List, Dict, Any, Optional

from .cache import InMemoryCache
from .errors import TenableAPIError
from .models import ScanModel, parse_model

logger = logging.getLogger(__name__)


class ScansAPI:
    """
    WAS v2 Scan management API.

    Endpoints used:
        GET /was/v2/scans
        GET /was/v2/scans/{scan_id}
    """

    def __init__(self, http, cache: Optional[InMemoryCache] = None):
        self.http = http
        self.cache = cache or InMemoryCache()

    # -------------------------------------------------------------------
    # Raw API Calls
    # -------------------------------------------------------------------
    def _api_list_scans(self) -> Dict[str, Any]:
        logger.info("Fetching list of scans")
        return self.http.get("/was/v2/scans")

    def _api_get_scan(self, scan_id: str) -> Dict[str, Any]:
        logger.info(f"Fetching scan details for {scan_id}")
        return self.http.get(f"/was/v2/scans/{scan_id}")

    # -------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------
    def list_all(self) -> List[ScanModel]:
        """
        Return a list of ScanModel objects.

        The CLI expects:
            api.list_all() → iterable of models with .id and .name
        """
        raw = self._api_list_scans()
        items = raw.get("items") or raw.get("scans") or []

        models: List[ScanModel] = []
        for s in items:
            model = parse_model(ScanModel, s)
            if model.id:
                # cache each scan for 10 minutes
                self.cache.set("scans", model.id, model, ttl=600)
            models.append(model)

        return models

    def get_details(self, scan_id: str) -> ScanModel:
        """
        Fetch detailed scan information.

        CLI calls:
            pytenable-was scans details <scan_id>
        """

        # First attempt cached
        try:
            cached = self.cache.get("scans", scan_id)
            logger.debug(f"Loaded scan {scan_id} from cache")
            return cached
        except Exception:
            pass

        raw = self._api_get_scan(scan_id)
        model = parse_model(ScanModel, raw)

        # store to cache
        if model.id:
            self.cache.set("scans", model.id, model, ttl=600)

        return model

    # -------------------------------------------------------------------
    # Future expansion points
    # -------------------------------------------------------------------
    # Create scan
    # Delete scan
    # Launch scan
    # Pause scan
    # Resume scan
    #
    # (All follow the same convention and are easy to add later.)
