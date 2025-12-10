# users.py
from typing import List, Dict, Any

from .http import http_request
from .errors import WasApiError


# =====================================================================
# USERS API HELPERS (NO CLI COMMANDS)
# Used ONLY to map WAS scans → owners
# =====================================================================

# ------------------------------------------------------------
# 1️⃣ List users → GET /users
# ------------------------------------------------------------
def list_users() -> List[Dict[str, Any]]:
    """
    Retrieve all Tenable.io users (summary list).
    Needed for:
      - resolving email → uuid
      - resolving username → uuid
      - mapping scan owner uuid → email/name

    API:
        GET /users
    """
    return http_request("GET", "/users")


# ------------------------------------------------------------
# 2️⃣ User details → GET /users/{user_id}
# ------------------------------------------------------------
def get_user_details(user_id: str) -> Dict[str, Any]:
    """
    Retrieve full user details by UUID.
    WAS scans store only the owner's UUID.
    """
    return http_request("GET", f"/users/{user_id}")


# ------------------------------------------------------------
# 3️⃣ Resolve: email OR username OR uuid → uuid
# ------------------------------------------------------------
def resolve_user(identifier: str) -> str:
    """
    Resolve a user identifier into a UUID.

    Accepts:
      - UUID
      - email
      - username

    Returns:
      UUID string

    This is used by:
      - scans.change-owner()
      - bulk ownership operations
    """
    ident = identifier.strip().lower()

    # Case 1 — already looks like a UUID
    if _looks_like_uuid(ident):
        return ident

    # Case 2 — match email/username from user list
    users = list_users()

    for u in users:
        if u.get("email", "").lower() == ident:
            return u["uuid"]
        if u.get("username", "").lower() == ident:
            return u["uuid"]

    raise WasApiError(404, f"No matching user found for '{identifier}'")


# ------------------------------------------------------------
# UUID check (simple format validation)
# ------------------------------------------------------------
def _looks_like_uuid(value: str) -> bool:
    parts = value.split("-")
    if len(parts) != 5:
        return False
    lengths = [8, 4, 4, 4, 12]
    return all(len(p) == l for p, l in zip(parts, lengths))


# =====================================================================
# 4️⃣ Enrich WAS scan with owner info (UUID → email/username/name)
# =====================================================================
def enrich_scan_owner(scan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a WAS scan object with minimal owner metadata.

    WAS scans store:
        scan["owner"] = "<uuid>"

    This function adds:
        scan["owner_enriched"] = {
            "uuid": ...,
            "email": ...,
            "username": ...,
            "name": ...
        }

    Only includes fields you actually care about.
    """

    owner_uuid = scan.get("owner")

    if not owner_uuid:
        scan["owner_enriched"] = None
        return scan

    # Load summary users
    users = list_users()
    lookup = {u["uuid"]: u for u in users}

    summary = lookup.get(owner_uuid, {})

    # Minimal enrichment (no created, roles, MFA, etc.)
    scan["owner_enriched"] = {
        "uuid": owner_uuid,
        "email": summary.get("email"),
        "username": summary.get("username"),
        "name": summary.get("name"),
    }

    return scan
