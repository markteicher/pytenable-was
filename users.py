# users.py
"""
User Resolution and Lookup for Tenable WAS v2
=============================================

WAS scans reference owners by UUID:
    "owner_id": "<uuid>"

The WAS API *does not* include user details. To resolve:
    GET /v2/users/{uuid}

This module handles user lookup and caching.
"""

from .errors import TenableAPIError


class UserAPI:
    """
    Provides user resolution for UUIDs returned in WAS scans,
    templates, or other WAS-related objects.

    Includes in-memory caching to avoid repeated GET requests.
    """

    def __init__(self, http):
        self.http = http
        self._cache = {}  # uuid → user dict

    # --------------------------------------------------------------
    # INTERNAL CACHE HELPERS
    # --------------------------------------------------------------

    def _cache_user(self, user):
        """Store user in cache by UUID."""
        uuid = user.get("uuid")
        if uuid:
            self._cache[uuid] = user

    def _get_from_cache(self, uuid):
        """Return cached user if available."""
        return self._cache.get(uuid)

    # --------------------------------------------------------------
    # GET USER BY UUID
    # --------------------------------------------------------------

    def get_user(self, uuid: str):
        """
        Resolve a user by UUID.

        Returns minimal user identity structure:
            {
                "uuid": "...",
                "name": "...",
                "email": "..."
            }
        """
        if not uuid:
            return None

        # Cached?
        cached = self._get_from_cache(uuid)
        if cached:
            return cached

        # Query Tenable Users API
        path = f"/v2/users/{uuid}"

        try:
            data = self.http.get(path)
        except TenableAPIError:
            # User may have been deleted or permission denied
            return None

        # Normalize minimal user record
        user = {
            "uuid": data.get("uuid"),
            "name": data.get("name"),
            "email": data.get("email"),
        }

        self._cache_user(user)
        return user

    # --------------------------------------------------------------
    # FULL USER LIST (OPTIONAL)
    # --------------------------------------------------------------

    def list_users(self):
        """
        Fetch all users (optional for enrichment).

        Mostly useful for:
            - Pre-caching all owner lookups
            - Diagnostics
            - Export operations

        Not required for normal scan owner resolution.
        """
        path = "/v2/users"
        response = self.http.get(path)

        if "users" not in response:
            raise TenableAPIError("Malformed response: missing 'users'")

        for user in response["users"]:
            self._cache_user({
                "uuid": user.get("uuid"),
                "name": user.get("name"),
                "email": user.get("email")
            })

        return response["users"]
