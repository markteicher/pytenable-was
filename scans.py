# pytenable_was/scans.py

"""
Cadillac-grade Tenable WAS v2 Scans module.

Features:
    - WAS v2 API coverage
    - Pydantic v2 model parsing
    - In-memory caching for performance
    - Clean logging
    - Scan orchestration (launch + wait)
    - Status classification
    - Summary generation
"""

import logging
import time
from typing import Dict, Optional, List

from .models import ScanModel, ScanSummary, parse_model
from .errors import TimeoutError, ScanWaitError
from .utils import parse_timestamp
from .cache import InMemoryCache

logger = logging.getLogger(__name__)


class ScansAPI:
    """
    Handles all Scan-related operations for Tenable WAS v2.

    - Raw API calls
    - Typed model parsing
    - Cache integration
    - Orchestration utilities
    """

    # Tenable-status terminal states
    TERMINAL_STATES = ("completed", "failed", "cancelled")

    def __init__(self, http, cache: Optional[InMemoryCache] = None):
        self.http = http
        self.cache = cache or InMemoryCache()

    # ===============================================================
    # RAW API CALLS (no interpretation)
    # ===============================================================

    def _api_list_scans(self) -> Dict:
        logger.info("Fetching scan list from WAS API...")
        return self.http.get("/was/v2/scans")

    def _api_get_scan(self, scan_id: str) -> Dict:
        logger.info("Fetching scan %s...", scan_id)
        return self.http.get(f"/was/v2/scans/{scan_id}")

    def _api_launch_scan(self, scan_id: str):
        logger.info("Launching scan %s...", scan_id)
        return self.http.post(f"/was/v2/scans/{scan_id}/launch")

    # ===============================================================
    # MODEL PARSING + CACHE
    # ===============================================================

    def list_all(self, use_cache: bool = True) -> List[ScanModel]:
        """
        Retrieve all scans. Use cache when available.
        """
        try:
            if use_cache:
                # Collect cached scans
                scans = list(self.cache._store["scans"].values())
                if scans:
                    logger.debug("Loaded %s scans from cache.", len(scans))
                    return [entry.value for entry in scans]
        except Exception:
            pass

        raw = self._api_list_scans()
        items = raw.get("scans") or raw.get("items") or []

        models = []
        for s in items:
            model = parse_model(ScanModel, s)
            if model and model.id:
                self.cache.set("scans", model.id, model, ttl=300)
            models.append(model)

        logger.info("Loaded %s scans from API.", len(models))
        return models

    def get_scan(self, scan_id: str, use_cache: bool = True) -> ScanModel:
        """
        Retrieve a scan by ID with cache fallback.
        """
        if use_cache:
            try:
                model = self.cache.get("scans", scan_id)
                logger.debug("Scan %s loaded from cache.", scan_id)
                return model
            except Exception:
                pass

        raw = self._api_get_scan(scan_id)
        model = parse_model(ScanModel, raw)

        if model and model.id:
            self.cache.set("scans", model.id, model, ttl=300)

        return model

    def get_status(self, scan_id: str) -> Optional[str]:
        """
        Return the current scan status.
        """
        scan = self.get_scan(scan_id, use_cache=False)
        return scan.status

    # ===============================================================
    # STATUS CLASSIFICATION
    # ===============================================================

    @staticmethod
    def classify_status(status: Optional[str]) -> str:
        """
        Convert raw status into human-friendly description.
        """
        if not status:
            return "unknown"

        mapping = {
            "queued": "Queued (waiting to start)",
            "running": "Running",
            "processing": "Processing results",
            "completed": "Completed successfully",
            "failed": "Failed",
            "cancelled": "Cancelled",
        }
        return mapping.get(status.lower(), f"unknown ({status})")

    # ===============================================================
    # ORCHESTRATION
    # ===============================================================

    def launch_scan(self, scan_id: str) -> None:
        """Launch a scan."""
        self._api_launch_scan(scan_id)

        # Clear stale cache
        self.cache.delete("scans", scan_id)

    def wait_until_complete(
        self,
        scan_id: str,
        interval: int = 20,
        timeout: int = 7200,
    ) -> ScanModel:
        """
        Poll scan status until it reaches a terminal state.

        Raises:
            TimeoutError
            ScanWaitError
        """
        logger.info("Waiting for scan %s to complete...", scan_id)

        start = time.time()

        while True:
            scan = self.get_scan(scan_id, use_cache=False)
            status = scan.status

            logger.info("Scan %s status: %s", scan_id, status)

            if status in self.TERMINAL_STATES:
                return scan

            if time.time() - start > timeout:
                raise TimeoutError(f"Scan {scan_id} did not complete within timeout.")

            time.sleep(interval)

    def launch_and_wait(
        self,
        scan_id: str,
        interval: int = 20,
        timeout: int = 7200,
    ) -> ScanModel:
        """Launch a scan and block until it completes."""
        self.launch_scan(scan_id)
        return self.wait_until_complete(scan_id, interval, timeout)

    # ===============================================================
    # SUMMARY
    # ===============================================================

    def summary(self, scan_id: str) -> ScanSummary:
        """
        Return a ScanSummary model.
        """
        scan = self.get_scan(scan_id)
        return ScanSummary.from_scan(scan)
