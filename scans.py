# scans.py
"""
Scan Operations for Tenable WAS v2
==================================

Endpoints:
    GET /was/v2/scans
    GET /was/v2/scans/{scan_id}

Scanning in WAS v2 includes:
    - scan metadata
    - configuration reference
    - schedule
    - statistics
    - owner_id   (must be resolved via Users API)

This module adds owner enrichment using the Users API.
"""

from .errors import TenableAPIError


class ScanAPI:
    """
    WAS v2 scans interface with owner resolution support.

    The owner of a scan is not included directly, only an owner_id.
    To resolve it, we use the Users API instance passed into ScanAPI.
    """

    def __init__(self, http, user_api):
        self.http = http
        self.user_api = user_api  # For resolving owner_id → {name,email}

    # ------------------------------------------------------------------
    # OWNER RESOLUTION
    # ------------------------------------------------------------------
    def _resolve_owner(self, scan: dict):
        """
        Resolve owner information (uuid, name, email).

        WAS v2 returns:
            "owner_id": "<uuid>"

        We resolve via Users API:
            GET /v2/users/<uuid>

        Returns:
            {
                "uuid": "...",
                "name": "...",
                "email": "..."
            }
        """
        owner_id = scan.get("owner_id")
        if not owner_id:
            return None

        # Use cached lookup
        user = self.user_api.get_user(owner_id)
        if not user:
            return None

        return {
            "uuid": user.get("uuid"),
            "name": user.get("name"),
            "email": user.get("email"),
        }

    # ------------------------------------------------------------------
    # LIST SCANS
    # ------------------------------------------------------------------
    def list(self):
        """
        Return list of WAS scans with owner metadata automatically populated.

        Output includes:
            scan_id
            name
            owner: { name, email }
        """
        path = "/was/v2/scans"
        response = self.http.get(path)

        if "items" not in response:
            raise TenableAPIError("Malformed response: missing 'items'")

        scans = response["items"]

        # Enrich each with owner info
        for scan in scans:
            scan["owner"] = self._resolve_owner(scan)

        return scans

    # ------------------------------------------------------------------
    # GET SCAN DETAILS
    # ------------------------------------------------------------------
    def get(self, scan_id: str):
        """
        Retrieve full WAS scan metadata and enrich with owner.

        Returns a large object with:
            scan_id
            name
            config_id
            state
            target metadata
            schedule
            owner (added)
        """
        if not scan_id:
            raise ValueError("scan_id is required")

        path = f"/was/v2/scans/{scan_id}"
        scan = self.http.get(path)

        # Add owner metadata
        scan["owner"] = self._resolve_owner(scan)

        return scan
