"""
Vulnerabilities module for Tenable WAS v2

Provides:
    - Vulnerability search (POST /was/v2/vulns/search)
    - Vulnerability details (GET /was/v2/vulns/{vuln_id})
    - Multi-ID retrieval
    - Flattening (one row per vulnerability × affected URL)
    - Export helpers for JSON/CSV-ready dicts
    - Filter construction from CLI flags
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .errors import TenableAPIError
from .utils import flatten_dict

logger = logging.getLogger(__name__)


# ======================================================================
# Utility
# ======================================================================

def _timestamp_now():
    """Return ISO8601 timestamp safe for filenames."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")


def _parse_multi_ids(value: str) -> List[str]:
    """
    Accepts comma-separated vuln IDs (e.g., "10,20,30").
    Strips whitespace and empties.
    """
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


# ======================================================================
# Main API
# ======================================================================

class VulnsAPI:
    """
    WAS v2 Vulnerability API Client.

    Supports:
        - search()
        - get_vuln()
        - get_many()
        - flatten_single()
        - flatten_multi()
    """

    def __init__(self, http):
        self.http = http

    # --------------------------------------------------------------
    # Raw Tenable calls
    # --------------------------------------------------------------

    def _api_search(self, body: Dict) -> Dict:
        """
        POST /was/v2/vulns/search
        """
        logger.info("Searching vulnerabilities with body=%s", body)
        return self.http.post("/was/v2/vulns/search", json=body)

    def _api_get_vuln(self, vuln_id: str) -> Dict:
        """
        GET /was/v2/vulns/{vuln_id}
        """
        logger.info("Fetching vulnerability %s", vuln_id)
        return self.http.get(f"/was/v2/vulns/{vuln_id}")

    # --------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------

    def search(self, filters: Dict, size: int = 1000, offset: int = 0) -> List[Dict]:
        """
        Perform vuln search with a filter dict or raw filter JSON.

        Returns a list of vulnerabilities.
        """
        body = {
            "filters": filters.get("filters", []),
            "size": size,
            "offset": offset,
        }

        out = self._api_search(body)

        # Typical payload shape:
        # {
        #   "returned": 50,
        #   "total": 200,
        #   "vulns": [ ... ]
        # }
        vulns = out.get("vulns") or out.get("items") or []

        logger.info("Search returned %s vulns", len(vulns))
        return vulns

    def get_vuln(self, vuln_id: str) -> Dict:
        """
        Retrieve details for a single vulnerability.
        """
        if not vuln_id:
            raise TenableAPIError("vuln_id is required")

        return self._api_get_vuln(vuln_id)

    def get_many(self, vuln_ids: Union[str, List[str]]) -> List[Dict]:
        """
        Retrieve multiple vulnerabilities by ID.
        Accepts:
            "10,12,15"
            ["10", "12", "15"]
        """
        if isinstance(vuln_ids, str):
            vuln_ids = _parse_multi_ids(vuln_ids)

        results = []
        for vid in vuln_ids:
            try:
                results.append(self.get_vuln(vid))
            except TenableAPIError as exc:
                logger.error("Error retrieving vuln %s: %s", vid, exc)
        return results

    # --------------------------------------------------------------
    # Filter Construction
    # --------------------------------------------------------------

    @staticmethod
    def build_filters(
        severity: Optional[str] = None,
        plugin_id: Optional[Union[str, int]] = None,
        scan_id: Optional[Union[str, int]] = None,
        application_id: Optional[Union[str, int]] = None,
        state: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convert CLI-style arguments into WAS filter objects.

        WAS Search filter structure:
        {
            "filters": [
                {"field": "severity", "operator": "eq", "value": "high"},
                {"field": "plugin_id", "operator": "in", "value": [98074]},
                ...
            ]
        }
        """
        filters = []

        if severity:
            filters.append({
                "field": "severity",
                "operator": "eq",
                "value": severity.lower()
            })

        if plugin_id:
            filters.append({
                "field": "plugin_id",
                "operator": "in",
                "value": [plugin_id] if not isinstance(plugin_id, list) else plugin_id
            })

        if scan_id:
            filters.append({
                "field": "scan_id",
                "operator": "in",
                "value": [scan_id]
            })

        if application_id:
            filters.append({
                "field": "application_id",
                "operator": "in",
                "value": [application_id]
            })

        if state:
            filters.append({
                "field": "state",
                "operator": "eq",
                "value": state
            })

        if since:
            filters.append({
                "field": "last_seen",
                "operator": "gte",
                "value": since
            })

        if until:
            filters.append({
                "field": "last_seen",
                "operator": "lte",
                "value": until
            })

        return {"filters": filters}

    # --------------------------------------------------------------
    # Flattening (One Row Per Vulnerability × Affected URL)
    # --------------------------------------------------------------

    def flatten_single(self, vuln: Dict) -> List[Dict]:
        """
        Flatten a single vulnerability into 1 row per affected URL.

        Example:
            vuln["affected_urls"] = ["https://a.com", "https://b.com"]
        Produces:
            2 rows with all shared vuln metadata.
        """
        if not vuln:
            return []

        urls = vuln.get("affected_urls") or []
        if not urls:
            # Still return one row with no URL
            base = flatten_dict(vuln)
            base["affected_url"] = None
            return [base]

        rows = []
        base = flatten_dict(vuln)

        for u in urls:
            row = dict(base)
            row["affected_url"] = u
            rows.append(row)

        return rows

    def flatten_multi(self, vulns: List[Dict]) -> List[Dict]:
        """
        Flatten many vulnerabilities into rows.
        """
        rows = []
        for v in vulns:
            rows.extend(self.flatten_single(v))
        return rows

    # --------------------------------------------------------------
    # Export-Oriented Helpers
    # --------------------------------------------------------------

    def export_one(self, vuln_id: str) -> List[Dict]:
        """
        Retrieve + flatten a single vulnerability.
        """
        vuln = self.get_vuln(vuln_id)
        return self.flatten_single(vuln)

    def export_many(self, vuln_ids: Union[str, List[str]]) -> List[Dict]:
        """
        Retrieve + flatten many vulnerabilities.
        """
        if isinstance(vuln_ids, str):
            vuln_ids = _parse_multi_ids(vuln_ids)

        vulns = self.get_many(vuln_ids)
        return self.flatten_multi(vulns)
