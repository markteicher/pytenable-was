# scans.py
import time
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from .http import http_request
from .errors import WasApiError


# ------------------------------------------------------------
# Internal helper: retry for 429 + transient 5xx errors
# ------------------------------------------------------------
def _retry_request(method, url, json=None, headers=None, max_retries=3):
    retries = 0

    while True:
        try:
            return http_request(method, url, json=json, headers=headers)

        except WasApiError as e:
            status = e.status_code

            # Retry logic for rate limits & temporary outages
            if status in (429, 500, 502, 503, 504) and retries < max_retries:
                delay = 2 ** retries
                time.sleep(delay)
                retries += 1
                continue

            # Propagate permanent failures
            raise


# ------------------------------------------------------------
# List all scans
# ------------------------------------------------------------
def list_scans() -> List[Dict[str, Any]]:
    """
    Retrieve all WAS scans.
    """
    url = "/was/v2/scans"
    return _retry_request("GET", url)


# ------------------------------------------------------------
# Get scan details
# ------------------------------------------------------------
def get_scan(scan_id: str) -> Dict[str, Any]:
    """
    Retrieve details for a single scan.
    """
    url = f"/was/v2/scans/{scan_id}"
    return _retry_request("GET", url)


# ------------------------------------------------------------
# Create a new scan
# ------------------------------------------------------------
def create_scan(name: str, target: str, template_id: str,
                description: Optional[str] = None,
                owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a WAS scan using a template and required fields.
    """
    url = "/was/v2/scans"

    payload = {
        "name": name,
        "target": target,
        "template": template_id
    }

    if description:
        payload["description"] = description

    if owner:
        payload["owner"] = owner

    return _retry_request("POST", url, json=payload)


# ------------------------------------------------------------
# Launch a scan
# ------------------------------------------------------------
def launch_scan(scan_id: str) -> Dict[str, Any]:
    """
    Launch a WAS scan now.
    """
    url = f"/was/v2/scans/{scan_id}/launch"
    payload = {}
    return _retry_request("POST", url, json=payload)


# ------------------------------------------------------------
# Delete a scan
# ------------------------------------------------------------
def delete_scan(scan_id: str) -> Dict[str, Any]:
    """
    Delete an existing scan.
    """
    url = f"/was/v2/scans/{scan_id}"
    return _retry_request("DELETE", url)


# ------------------------------------------------------------
# Change owner (single scan)
# ------------------------------------------------------------
def change_scan_owner(scan_id: str, new_owner_uuid: str) -> Dict[str, Any]:
    """
    Change the owner for a single scan.

    Returns:
        {
            "scan_id": "...",
            "success": True/False,
            "error": None or message
        }
    """
    url = f"/was/v2/scans/{scan_id}"
    payload = {"owner": new_owner_uuid}

    try:
        _retry_request("PUT", url, json=payload)
        return {
            "scan_id": scan_id,
            "success": True,
            "error": None
        }

    except WasApiError as e:
        return {
            "scan_id": scan_id,
            "success": False,
            "error": f"{e.status_code}: {e.message}"
        }


# ------------------------------------------------------------
# Bulk owner change with enhanced tqdm
# ------------------------------------------------------------
def change_scan_owner_bulk(scan_ids: List[str], new_owner_uuid: str) -> Dict[str, Any]:
    """
    Bulk owner change across any number of scans.

    Live tqdm display shows:
    - current scan being processed
    - success count
    - failure count

    Returns:
        {
            "total": N,
            "success": [...],
            "failed": [...],
            "success_count": int,
            "fail_count": int
        }
    """
    results_success = []
    results_failed = []
    success_count = 0
    fail_count = 0

    pbar = tqdm(
        scan_ids,
        desc="Changing scan ownership",
        unit="scan",
        dynamic_ncols=True,
        colour="cyan"
    )

    for scan_id in pbar:
        scan_id_clean = scan_id.strip()

        if not scan_id_clean:
            fail_count += 1
            results_failed.append({
                "scan_id": scan_id,
                "error": "Empty scan ID"
            })

            pbar.set_postfix({
                "success": success_count,
                "failed": fail_count,
                "current": "N/A"
            })
            continue

        # Update tqdm with context
        pbar.set_postfix({
            "success": success_count,
            "failed": fail_count,
            "current": scan_id_clean
        })

        result = change_scan_owner(scan_id_clean, new_owner_uuid)

        if result["success"]:
            success_count += 1
            results_success.append(result["scan_id"])
        else:
            fail_count += 1
            results_failed.append(result)

        # Update postfix after processing
        pbar.set_postfix({
            "success": success_count,
            "failed": fail_count,
            "current": scan_id_clean
        })

    pbar.close()

    return {
        "total": len(scan_ids),
        "success": results_success,
        "failed": results_failed,
        "success_count": success_count,
        "fail_count": fail_count
    }
