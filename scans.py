# scans.py
from typing import List, Dict, Any

from .http import http_request
from .errors import WasApiError
from .users import resolve_user

from tqdm import tqdm


# =====================================================================
# WAS SCANS – BACKEND ONLY (NO CLI COMMANDS HERE)
# =====================================================================


# ------------------------------------------------------------
# 1️⃣ List scans → GET /was/v2/scans
# ------------------------------------------------------------
def list_scans() -> List[Dict[str, Any]]:
    """
    Retrieve all WAS scans.

    API:
        GET /was/v2/scans
    """
    return http_request("GET", "/was/v2/scans")


# ------------------------------------------------------------
# 2️⃣ Get scan details → GET /was/v2/scans/{scan_id}
# ------------------------------------------------------------
def get_scan(scan_id: str) -> Dict[str, Any]:
    """
    Retrieve a single WAS scan.

    API:
        GET /was/v2/scans/{scan_id}
    """
    return http_request("GET", f"/was/v2/scans/{scan_id}")


# ------------------------------------------------------------
# 3️⃣ Create a scan → POST /was/v2/scans
# ------------------------------------------------------------
def create_scan(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new WAS scan.

    API:
        POST /was/v2/scans
    """
    return http_request("POST", "/was/v2/scans", json=payload)


# ------------------------------------------------------------
# 4️⃣ Delete a scan → DELETE /was/v2/scans/{scan_id}
# ------------------------------------------------------------
def delete_scan(scan_id: str) -> Dict[str, Any]:
    """
    Delete a WAS scan.

    API:
        DELETE /was/v2/scans/{scan_id}
    """
    return http_request("DELETE", f"/was/v2/scans/{scan_id}")


# ------------------------------------------------------------
# 5️⃣ Launch a scan → POST /was/v2/scans/{scan_id}/launch
# ------------------------------------------------------------
def launch_scan(scan_id: str) -> Dict[str, Any]:
    """
    Launch a WAS scan.

    API:
        POST /was/v2/scans/{scan_id}/launch
    """
    return http_request("POST", f"/was/v2/scans/{scan_id}/launch")


# =====================================================================
# OWNER CHANGE OPERATIONS
# =====================================================================

# ------------------------------------------------------------
# 6️⃣ Change owner (single)
# ------------------------------------------------------------
def change_scan_owner(scan_id: str, new_owner_identifier: str) -> Dict[str, Any]:
    """
    Change the owner of a single WAS scan.

    new_owner_identifier:
        - email
        - username
        - uuid

    resolve_user() converts to UUID.
    """

    new_owner_uuid = resolve_user(new_owner_identifier)

    payload = {"owner": new_owner_uuid}

    return http_request(
        "PUT",
        f"/was/v2/scans/{scan_id}",
        json=payload
    )


# ------------------------------------------------------------
# 7️⃣ Bulk owner change with tqdm progress
# ------------------------------------------------------------
def change_scan_owner_bulk(scan_ids: List[str], new_owner_identifier: str) -> List[Dict[str, Any]]:
    """
    Change owner for many scans at once.

    - Resolves owner once (uuid)
    - Updates each scan individually
    - Shows tqdm progress bar
    - Returns list of results
    """

    new_owner_uuid = resolve_user(new_owner_identifier)
    results = []

    for scan_id in tqdm(scan_ids, desc="Changing scan owners", unit="scan"):
        payload = {"owner": new_owner_uuid}

        try:
            result = http_request("PUT", f"/was/v2/scans/{scan_id}", json=payload)
        except WasApiError as e:
            result = {"scan_id": scan_id, "error": str(e)}

        results.append(result)

    return results
