# pytenable_was/users.py

"""
Tenable WAS v2 Users API

Supports:
    • Fetching all WAS users
    • Fetching user details via /users/{user_id}
    • Building lookup tables for scan-owner enrichment

This module does NOT manage users (create/update/delete) — it is
strictly a lookup/enrichment helper for other SDK components.
"""

import logging
from typing import Dict, List, Any

from .errors import TenableAPIError

logger = logging.getLogger(__name__)


class UsersAPI:
    """
    WAS v2 Users Lookup API.

    Endpoints used:
        GET /was/v2/users
        GET /was/v2/users/{user_id}
    """

    def __init__(self, http):
        self.http = http

    # -------------------------------------------------------------------
    # RAW API CALLS
    # -------------------------------------------------------------------
    def _api_list_users(self) -> Dict[str, Any]:
        """
        GET /was/v2/users
        Returns:
            { "items": [ {...}, {...} ] }
        """
        logger.info("Fetching WAS user list...")
        return self.http.get("/was/v2/users")

    def _api_user_details(self, user_id: str) -> Dict[str, Any]:
        """
        GET /was/v2/users/{user_id}

        This endpoint returns detailed metadata for a user.
        You stated you only care about:
            • name
            • email
        """
        logger.info("Fetching details for user %s", user_id)
        return self.http.get(f"/was/v2/users/{user_id}")

    # -------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------
    def fetch_all_users(self) -> List[Dict[str, Any]]:
        """
        Return a list of user records as dictionaries.

        Expected fields from Tenable:
            user_id
            email
            name
            username (sometimes)
            type
        """
        raw = self._api_list_users()
        items = raw.get("items") or raw.get("users") or []

        if not isinstance(items, list):
            raise TenableAPIError("Malformed /users response")

        return items

    def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """
        Return details for an individual user.

        Only `email` and `name` matter for scan-owner enrichment.
        """
        raw = self._api_user_details(user_id)
        if not isinstance(raw, dict):
            raise TenableAPIError(f"Malformed user details for {user_id}")
        return raw

    # -------------------------------------------------------------------
    # OWNER ENRICHMENT HELPERS
    # -------------------------------------------------------------------
    def build_owner_map(self) -> Dict[str, Dict[str, str]]:
        """
        Returns:
            {
                "user_id_1": { "email": "...", "name": "..." },
                "user_id_2": { "email": "...", "name": "..." },
                ...
            }

        This provides one lookup call scans can use to enrich:
            scan.owner_id → owner.name / owner.email
        """
        users = self.fetch_all_users()
        owner_map: Dict[str, Dict[str, str]] = {}

        for u in users:
            uid = u.get("user_id")
            if not uid:
                continue

            owner_map[uid] = {
                "email": u.get("email"),
                "name": u.get("name"),
            }

        return owner_map

    def enrich_scans(self, scans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich a list of scan dicts with owner name/email.

        Input scan dicts must contain:
            scan["owner_id"]  (Tenable field)

        Output will include:
            scan["owner_email"]
            scan["owner_name"]

        If owner is unknown → blank values.
        """
        owners = self.build_owner_map()

        enriched = []
        for s in scans:
            owner_id = s.get("owner_id")
            owner_info = owners.get(owner_id, {})

            s["owner_email"] = owner_info.get("email")
            s["owner_name"]  = owner_info.get("name")

            enriched.append(s)

        return enriched
