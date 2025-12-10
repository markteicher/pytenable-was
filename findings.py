# pytenable_was/findings.py

class FindingsAPI:
    """
    Fully-featured Tenable WAS v2 Findings API wrapper.

    OFFICIAL ENDPOINTS:
        - GET /was/v2/scans/{scan_id}/findings
        - GET /was/v2/findings/{finding_id}

    THIS MODULE ADDS CLIENT-SIDE FEATURES:
        - filtering (severity, status, CWE, URL, etc.)
        - sorting helpers
        - group-by utilities
        - finding summaries
        - statistics extraction
        - export normalization
    """

    def __init__(self, http):
        self.http = http

    # =====================================================================
    # RAW OFFICIAL API CALLS
    # =====================================================================
    def list_findings(self, scan_id: str):
        """
        Retrieve findings for a WAS scan.

        Returns:
            dict: Raw findings JSON.
        """
        return self.http.get(f"/was/v2/scans/{scan_id}/findings")

    def get_finding(self, finding_id: str):
        """
        Retrieve a single finding by UUID.
        """
        return self.http.get(f"/was/v2/findings/{finding_id}")

    # =====================================================================
    # NORMALIZED LISTING HELPERS
    # =====================================================================
    def list_all(self, scan_id: str):
        """
        Normalize WAS findings into a flat list.

        WAS v2 typically returns:
            { "findings": [ ... ] }

        This helper ensures consistent output.
        """
        raw = self.list_findings(scan_id)
        if isinstance(raw, dict):
            return raw.get("findings") or raw.get("items") or []
        return raw

    # =====================================================================
    # FINDING FILTERING (client-side)
    # =====================================================================
    def filter_by_severity(self, findings, severity: str):
        """Filter findings by severity level (e.g., 'high', 'medium')."""
        severity = severity.lower()
        return [f for f in findings if f.get("severity", "").lower() == severity]

    def filter_by_status(self, findings, status: str):
        """Filter findings by status (e.g., 'open', 'closed')."""
        status = status.lower()
        return [f for f in findings if f.get("status", "").lower() == status]

    def filter_by_cwe(self, findings, cwe_id: str):
        """Filter by CWE ID (e.g., 'CWE-79')."""
        return [f for f in findings if f.get("cwe") == cwe_id]

    def filter_by_url(self, findings, substring: str):
        """Return findings whose URL contains a substring."""
        sub = substring.lower()
        return [f for f in findings if sub in (f.get("url") or "").lower()]

    # =====================================================================
    # SORTING HELPERS
    # =====================================================================
    def sort_by_severity(self, findings, descending=True):
        """Sort findings by severity ranking."""
        rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        return sorted(findings, key=lambda f: rank.get(f.get("severity", "").lower(), -1), reverse=descending)

    def sort_by_url(self, findings):
        return sorted(findings, key=lambda f: f.get("url") or "")

    # =====================================================================
    # GROUPING HELPERS
    # =====================================================================
    def group_by_severity(self, findings):
        """Return dict: severity -> list of findings."""
        groups = {}
        for f in findings:
            sev = (f.get("severity") or "unknown").lower()
            groups.setdefault(sev, []).append(f)
        return groups

    def group_by_cwe(self, findings):
        groups = {}
        for f in findings:
            cwe = f.get("cwe") or "no-cwe"
            groups.setdefault(cwe, []).append(f)
        return groups

    def group_by_url(self, findings):
        groups = {}
        for f in findings:
            url = f.get("url") or "unknown"
            groups.setdefault(url, []).append(f)
        return groups

    # =====================================================================
    # SUMMARY HELPERS
    # =====================================================================
    def extract_summary(self, finding):
        """
        Produce a clean, simplified summary suitable for tables or exports.
        """
        return {
            "id": finding.get("id"),
            "severity": finding.get("severity"),
            "status": finding.get("status"),
            "title": finding.get("title"),
            "url": finding.get("url"),
            "cwe": finding.get("cwe"),
            "evidence_count": len(finding.get("evidence", [])),
        }

    def extract_summaries(self, findings):
        """Return simplified summaries for many findings."""
        return [self.extract_summary(f) for f in findings]

    # =====================================================================
    # STATISTICS
    # =====================================================================
    def compute_statistics(self, findings):
        """
        Compute severity counts and other simple metrics.
        """
        stats = {
            "total": len(findings),
            "severity": {},
            "cwe": {},
        }

        # Count severity
        for f in findings:
            sev = (f.get("severity") or "unknown").lower()
            stats["severity"][sev] = stats["severity"].get(sev, 0) + 1

            cwe = f.get("cwe") or "no-cwe"
            stats["cwe"][cwe] = stats["cwe"].get(cwe, 0) + 1

        return stats

    # =====================================================================
    # EXPORT HELPERS
    # =====================================================================
    def as_export_rows(self, findings):
        """
        Convert findings into a CSV/JSON-friendly flat structure.
        """
        rows = []
        for f in findings:
            rows.append({
                "id": f.get("id"),
                "severity": f.get("severity"),
                "status": f.get("status"),
                "title": f.get("title"),
                "url": f.get("url"),
                "cwe": f.get("cwe"),
                "description": f.get("description"),
                "solution": f.get("solution"),
            })
        return rows
