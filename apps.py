# pytenable_was/apps.py

class ApplicationsAPI:
    """
    Fully-featured Tenable WAS v2 Applications API wrapper.

    OFFICIAL ENDPOINTS SUPPORTED:
        - GET    /was/v2/applications
        - POST   /was/v2/applications
        - GET    /was/v2/applications/{app_id}
        - POST   /was/v2/applications/{app_id}
        - DELETE /was/v2/applications/{app_id}

        URL MANAGEMENT:
        - GET    /was/v2/applications/{app_id}/urls
        - POST   /was/v2/applications/{app_id}/urls
        - DELETE /was/v2/applications/{app_id}/urls/{url_id}

        AUTH FILES:
        - POST   /was/v2/applications/{app_id}/auth/files

    CLIENT-SIDE FEATURES:
        - Pagination helpers
        - Filtering utilities
        - Application summaries
        - URL helpers
        - Export helpers
    """

    def __init__(self, http):
        self.http = http

    # =====================================================================
    # RAW OFFICIAL ENDPOINTS — APPLICATION CRUD
    # =====================================================================
    def list_applications(self):
        """Return the list of all WAS applications."""
        return self.http.get("/was/v2/applications")

    def create_application(self, payload: dict):
        """
        Create a WAS application.

        Example payload may include:
            - name
            - description
            - tags
            - urls
            - auth settings
        """
        return self.http.post("/was/v2/applications", json=payload)

    def get_application(self, app_id: str):
        """Retrieve application details."""
        return self.http.get(f"/was/v2/applications/{app_id}")

    def update_application(self, app_id: str, payload: dict):
        """Update application configuration."""
        return self.http.post(f"/was/v2/applications/{app_id}", json=payload)

    def delete_application(self, app_id: str):
        """Delete a WAS application."""
        return self.http.delete(f"/was/v2/applications/{app_id}")

    # =====================================================================
    # URL MANAGEMENT (OFFICIAL)
    # =====================================================================
    def list_urls(self, app_id: str):
        """Return all URLs associated with an application."""
        return self.http.get(f"/was/v2/applications/{app_id}/urls")

    def add_url(self, app_id: str, payload: dict):
        """
        Add a URL to an application.

        Example payload:
            { "url": "https://example.com/login" }
        """
        return self.http.post(f"/was/v2/applications/{app_id}/urls", json=payload)

    def delete_url(self, app_id: str, url_id: str):
        """Remove a URL from an application."""
        return self.http.delete(f"/was/v2/applications/{app_id}/urls/{url_id}")

    # =====================================================================
    # AUTH FILE UPLOAD (OFFICIAL)
    # =====================================================================
    def upload_auth_file(self, app_id: str, file_path: str):
        """
        Upload an authentication file (e.g., cookie, cert).

        Parameters:
            file_path (str): Path to file to upload.
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            return self.http.post(f"/was/v2/applications/{app_id}/auth/files", files=files)

    # =====================================================================
    # CLIENT-SIDE ENHANCEMENTS
    # =====================================================================
    def list_all(self):
        """
        Normalize the list of applications into a clean Python list.
        """
        raw = self.list_applications()
        if isinstance(raw, dict):
            return raw.get("applications") or raw.get("items") or []
        return raw

    # ---------------------------------------------------------------------
    # APPLICATION FILTERING
    # ---------------------------------------------------------------------
    def filter_by_name(self, apps, substring: str):
        """Return applications whose name contains the substring."""
        sub = substring.lower()
        return [a for a in apps if sub in (a.get("name") or "").lower()]

    def filter_by_tag(self, apps, tag: str):
        """Return applications that contain the specific tag."""
        return [a for a in apps if tag in (a.get("tags") or [])]

    # ---------------------------------------------------------------------
    # SUMMARY HELPERS
    # ---------------------------------------------------------------------
    def extract_summary(self, app: dict):
        """Produce a clean summary of an application."""
        return {
            "id": app.get("id"),
            "name": app.get("name"),
            "url_count": len(app.get("urls") or []),
            "tags": app.get("tags"),
            "description": app.get("description"),
        }

    def extract_summaries(self, apps):
        """Produce summaries for many applications."""
        return [self.extract_summary(a) for a in apps]

    # ---------------------------------------------------------------------
    # STATISTICS
    # ---------------------------------------------------------------------
    def compute_statistics(self, apps):
        """
        Compute simple metrics for reporting, such as:
            - total apps
            - tag counts
        """
        stats = {
            "total": len(apps),
            "tags": {},
        }

        for a in apps:
            for tag in a.get("tags") or []:
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1

        return stats

    # ---------------------------------------------------------------------
    # EXPORT HELPERS
    # ---------------------------------------------------------------------
    def as_export_rows(self, apps):
        """
        Convert applications into a CSV/JSON-friendly flattened list.
        """
        rows = []
        for a in apps:
            rows.append({
                "id": a.get("id"),
                "name": a.get("name"),
                "description": a.get("description"),
                "tags": ",".join(a.get("tags") or []),
                "url_count": len(a.get("urls") or []),
            })
        return rows
