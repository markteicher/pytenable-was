# configs.py
"""
System Scan Configurations (Predefined Templates)
=================================================

These are the built-in, non-editable scan configurations provided
by Tenable WAS v2. They are NOT user templates and do not support
create/update/delete.

Endpoints:
    GET /was/v2/configurations
    GET /was/v2/configurations/{template_id}
"""

from .errors import TenableAPIError


class ConfigAPI:
    """
    Wrapper for WAS v2 system scan configurations.

    These represent built-in scan templates (API Scan, SSL/TLS Scan,
    PCI, Config Audit, etc.). They are read-only.
    """

    def __init__(self, http):
        self.http = http

    # --------------------------------------------------------------
    # LIST SYSTEM CONFIGURATIONS
    # --------------------------------------------------------------
    def list(self):
        """
        Returns a list of predefined WAS system configurations.

        Example fields returned:
            template_id
            name
            description
            plugin_state
            scanner_types
        """
        path = "/was/v2/configurations"
        response = self.http.get(path)

        if "items" not in response:
            raise TenableAPIError("Malformed response: missing 'items'")

        return response["items"]

    # --------------------------------------------------------------
    # GET SYSTEM CONFIGURATION BY ID
    # --------------------------------------------------------------
    def get(self, template_id: str):
        """
        Retrieve full configuration details for a predefined WAS system template.

        Returns a very large structure including:
            settings.*
            defaults.*
            plugin mappings
            scanner definitions
            rate limiting
        """
        if not template_id:
            raise ValueError("template_id is required")

        path = f"/was/v2/configurations/{template_id}"
        response = self.http.get(path)

        return response
