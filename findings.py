# pytenable_was/findings.py

"""
Tenable WAS v2 Findings module.

Capabilities:
    - Fetch all findings for a scan
    - Retrieve a single finding
    - Pydantic v2 model parsing
    - Pagination handling
    - In-memory caching
    - Severity sorting and grouping
    - Flattened export-ready structures
    - Summaries for dashboards/CLI
"""

import logging
from typing import Dict, List, Optional

from .models import FindingModel, FindingsSet, parse_model
from .cache import InMemoryCache
from .utils import (
    sort_by_severity,
    group_by_severity,
    flatten_model,
)

logger = logging.getLogger(__name__)


class FindingsAPI:
    """
    WAS v2 Findings API client.

    - Typed model parsing
    - Cache-aware operations
    - Useful analytics & export helpers
    """

    def __init__(self, http, cache: Optional[InMemoryCache] = None):
        self.http = http
        self.cache = cache or InMemoryCache()

    # ====================================================================
    # Raw API calls (Tenable documented endpoints)
    # ====================================================================

    def _api_list_findings(self, scan_id: str) -> Dict:
        """
        Tenable WAS v2 endpoint:
            GET /was/v2/scans/{scan_id}/findings
        """
        logger.info("Fetching findings for scan %s...", scan_id)
        return self.http.get(f"/was/v2/scans/{scan_id}/findings")

    def _api_get_finding(self, scan_id: str, finding_id: str) -> Dict:
        """
        Tenable WAS v2 endpoint:
            GET /was/v2/scans/{scan_id}/findings/{finding_id}
        """
        logger.info("Fetching finding %s for scan %s...", finding_id, scan_id)
        return self.http.get(f"/was/v2/scans/{scan_id}/findings/{finding_id}")

    # ====================================================================
    # Model parsing + caching
    # ====================================================================

    def list_findings(self, scan_id: str, use_cache: bool = True) -> FindingsSet:
        """
        Retrieve all findings for a scan.
        Automatically caches the entire findings set.

        Returns:
            FindingsSet (Pydantic model)
        """
        if use_cache:
            try:
                cached = self.cache.get("findings", scan_id)
                logger.debug("Loaded findings for scan %s from cache.", scan_id)
                return cached
            except Exception:
                pass

        raw = self._api_list_findings(scan_id)
        items = raw.get("findings") or raw.get("items") or []

        findings = FindingsSet.from_api(scan_id, items)

        # Cache results for 10 minutes
        self.cache.set("findings", scan_id, findings, ttl=600)

        logger.info("Loaded %s findings for scan %s", len(findings.findings), scan_id)
        return findings

    def get_finding(self, scan_id: str, finding_id: str, use_cache: bool = True) -> FindingModel:
        """
        Retrieve a specific finding.
        """
        if use_cache:
            try:
                # Try to load from cached FindingsSet
                fset = self.cache.get("findings", scan_id)
                for f in fset.findings:
                    if f.id == finding_id:
                        logger.debug("Finding %s loaded from cache.", finding_id)
                        return f
            except Exception:
                pass

        raw = self._api_get_finding(scan_id, finding_id)
        return parse_model(FindingModel, raw)

    # ====================================================================
    # Sorting + grouping + filtering
    # ====================================================================

    def sort_by_severity(self, scan_id: str, reverse: bool = True) -> List[FindingModel]:
        """
        Return findings sorted by severity ranking.
        """
        set_ = self.list_findings(scan_id)
        return sort_by_severity([f.model_dump() for f in set_.findings], reverse=reverse)

    def group_by_severity(self, scan_id: str) -> Dict[str, List[FindingModel]]:
        """
        Return findings grouped by severity.
        """
        set_ = self.list_findings(scan_id)
        return group_by_severity(set_.findings)

    def filter(self, scan_id: str, severity: Optional[str] = None, plugin_id: Optional[str] = None) -> List[FindingModel]:
        """
        Filter findings by severity and/or plugin ID.
        """
        findings = self.list_findings(scan_id).findings
        result = []

        for f in findings:
            if severity and (f.severity or "").lower() != severity.lower():
                continue
            if plugin_id and str(f.plugin_id) != str(plugin_id):
                continue
            result.append(f)

        logger.debug("Filter result: %s findings", len(result))
        return result

    # ====================================================================
    # Flattened export helpers
    # ====================================================================

    def flatten(self, scan_id: str) -> List[Dict]:
        """
        Return findings in flattened dict form for CSV or dataframe export.
        """
        set_ = self.list_findings(scan_id)
        return [flatten_model(f) for f in set_.findings]

    # ====================================================================
    # Summary
    # ====================================================================

    def summary(self, scan_id: str) -> Dict:
        """
        Return a statistical summary of findings.

        Output example:
            {
                "scan_id": "...",
                "total": 42,
                "critical": 3,
                "high": 5,
                "medium": 10,
                "low": 15,
                "info": 9,
            }
        """
        set_ = self.list_findings(scan_id)
        groups = self.group_by_severity(scan_id)

        return {
            "scan_id": scan_id,
            "total": len(set_.findings),
            "critical": len(groups.get("critical", [])),
            "high": len(groups.get("high", [])),
            "medium": len(groups.get("medium", [])),
            "low": len(groups.get("low", [])),
            "info": len(groups.get("info", [])),
        }
