# users.py
from typing import List, Dict, Any

from .http import http_request
from .errors import WasApiError


# =====================================================================
# USERS API HELPERS (NO CLI)
# Used ONLY to map WAS scans → owners
# =====================================================================


# ------------------------------------------------------------
# 1️⃣ List users → GET /users
# ------------------------------------------------------------
def list_users() -> List[Dict[str, Any]]:
    """
    Retrieve all Tenable.io users (summary list).

    Used for:
      - email → uuid resolution
      - username → uuid resolution
      - mapping scan owner uuid → readable info
    """
    return http_request("GET", "/users")


# ------------------------------------------------------------
# 2️⃣ User details → GET /users/{user_id}
# ------------------------------------------------------------
def get_user_details(user_id: str) -> Dict[str, Any]:
    """
    Retrieve full user details (by UUID).

    WAS scans ONLY store owner UUID, so if needed,
    this can pull additional user attributes.

    You currently do NOT care about most detail fields,
    so this is optional for minimal enrichment.
    """
    return http_request("GET", f"/users/{user_id}")


# ------------------------------------------------------------
# 3️⃣ Resolve email/username/uuid → uuid
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

    This is used by scans.py for owner assignment.
    """
    ident = identifier.strip().lower()

    # Case 1 — already looks like a UUID
    if _looks_like_uuid(ident):
        return ident

    # Case 2 — match email/username from /users list
    users = list_users()

    for u in users:
        if u.get("email", "").lower() == ident:
            return u["uuid"]
        if u.get("username", "").lower() == ident:
            return u["uuid"]

    raise WasApiError(404, f"No matching user found for '{identifier}'")


# ------------------------------------------------------------
# 4️⃣ Minimal WAS scan owner enrichment
# ------------------------------------------------------------
def enrich_scan_owner(scan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a WAS scan with ONLY the minimal ownership info you care about:

    Adds:
        scan["owner_enriched"] = {
            "uuid": ...,
            "email": ...,
            "username": ...,
            "name": ...
        }

    Does NOT include:
        created date, permissions, MFA, roles, groups, status, etc.
    """

    owner_uuid = scan.get("owner")

    # If scan has no owner value
    if not owner_uuid:
        scan["owner_enriched"] = None
        return scan

    # Build lookup map from /users
    users = list_users()
    user_lookup = {u["uuid"]: u for u in users}

    summary = user_lookup.get(owner_uuid, {})

    # Minimal enrichment ONLY
    scan["owner_enriched"] = {
        "uuid": owner_uuid,
        "email": summary.get("email"),
        "username": summary.get("username"),
        "name": summary.get("name"),
    }

    return scan


# ------------------------------------------------------------
# Utility: basic UUID format check
# ------------------------------------------------------------
def _looks_like_uuid(value: str) -> bool:
    parts = value.split("-")
    if len(parts) != 5:
        return False
    lengths = [8, 4, 4, 4, 12]
    return all(len(p) == l for p, l in zip(parts, lengths))
