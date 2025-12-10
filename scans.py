# pytenable_was/scans.py

import time


class ScansAPI:
    """
    Fully-featured Tenable WAS v2 Scan API wrapper.

    OFFICIAL ENDPOINTS (from Tenable WAS v2 documentation):
        - GET  /was/v2/scans
        - GET  /was/v2/scans/{scan_id}
        - POST /was/v2/scans/{scan_id}/launch

    THIS MODULE ADDS CLIENT-SIDE FEATURES:
        - Safe listing & pagination helpers
        - Scan status extraction
        - Human-readable status classification
        - wait_until_complete() polling utility
        - launch_and_wait() orchestration
        - summary extraction
    """

    def __init__(self, http):
        self.http = http

    # ===================================================================
    # RAW OFFICIAL ENDPOINTS
    # ===================================================================
    def list_scans(self):
        """
        List all WAS scans (single API call).
        """
        return self.http.get("/was/v2/scans")

    def get_scan(self, scan_id: str):
        """
        Retrieve details for a specific scan.

        Parameters:
            scan_id (str): Unique scan UUID.
        """
        return self.http.get(f"/was/v2/scans/{scan_id}")

    def launch_scan(self, scan_id: str):
        """
        Launch an existing scan configuration.

        Returns:
            dict or None: Launch response body (some launch endpoints return empty).
        """
        return self.http.post(f"/was/v2/scans/{scan_id}/launch")

    # ===================================================================
    # PAGINATION & LIST MANAGEMENT
    # ===================================================================
    def list_all_scans(self):
        """
        WAS v2 does not implement pagination server-side.

        This helper normalizes results and returns a clean list.
        """
        response = self.list_scans()

        # Tenable sometimes uses "scans"; sometimes top-level list.
        if isinstance(response, dict):
            scans = (
                response.get("scans")
                or response.get("items")
                or response.get("data")
            )
            if scans is not None:
                return scans

        # If response is already a list
        if isinstance(response, list):
            return response

        # Fallback: return raw response
        return [response]

    # ===================================================================
    # STATUS HELPERS
    # ===================================================================
    def get_scan_status(self, scan_id: str):
        """
        Extract only the scan status string.
        """
        scan = self.get_scan(scan_id)
        return scan.get("status")

    def classify_status(self, status: str):
        """
        Convert WAS status into a human-friendly description.
        """
        table = {
            "queued": "Queued and waiting to start",
            "running": "Scan is in progress",
            "processing": "Results are being processed",
            "completed": "Scan finished successfully",
            "failed": "Scan execution failed",
            "cancelled": "Scan was cancelled",
        }

        if not status:
            return "Unknown or missing status"

        return table.get(status.lower(), f"Unrecognized status: {status}")

    # ===================================================================
    # ORCHESTRATION HELPERS
    # ===================================================================
    def wait_until_complete(self, scan_id: str, poll_interval: int = 20, timeout: int = 7200):
        """
        Poll the scan until it completes, fails, or is cancelled.

        Returns:
            dict: Final scan JSON.

        Raises:
            TimeoutError: If the scan does not finish within the timeout.
        """
        start = time.time()

        while True:
            status = self.get_scan_status(scan_id)

            # Terminal statuses
            if status in ("completed", "failed", "cancelled"):
                return self.get_scan(scan_id)

            # Timeout check
            if (time.time() - start) > timeout:
                raise TimeoutError(f"Scan {scan_id} did not complete within {timeout} seconds.")

            time.sleep(poll_interval)

    def launch_and_wait(self, scan_id: str, poll_interval: int = 20, timeout: int = 7200):
        """
        Launch a scan, then automatically wait for it to complete.

        Returns:
            dict: Final scan details.
        """
        self.launch_scan(scan_id)
        return self.wait_until_complete(scan_id, poll_interval=poll_interval, timeout=timeout)

    # ===================================================================
    # SUMMARY & REPORTING HELPERS
    # ===================================================================
    def extract_summary(self, scan_id: str):
        """
        Extract key metadata for reporting or UI display.

        This does NOT invent new API behavior—it simply organizes
        existing fields returned by WAS v2.
        """
        scan = self.get_scan(scan_id)

        return {
            "scan_id": scan.get("id") or scan.get("scan_id"),
            "name": scan.get("name"),
            "status": scan.get("status"),
            "started": scan.get("start_time") or scan.get("started_at"),
            "completed": scan.get("end_time") or scan.get("completed_at"),
            "application": scan.get("application") or scan.get("application_id"),
            "duration_seconds": self._calculate_duration(scan),
        }

    def _calculate_duration(self, scan: dict):
        """
        Compute scan duration if timestamps exist.
        """
        start = scan.get("start_time")
        end = scan.get("end_time")

        if not start or not end:
            return None

        try:
            start_ts = int(start)
            end_ts = int(end)
            return end_ts - start_ts
        except:
            return None
