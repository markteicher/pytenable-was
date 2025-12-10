# templates.py
"""
Tenable-Provided Templates (Read-Only)
======================================

These are templates built and maintained by Tenable.
They can be listed and inspected but NOT modified or deleted.

Endpoints:
    GET /was/v2/templates
    GET /was/v2/templates/{template_id}
"""

from typing import List, Dict, Any
from .errors import TenableAPIError


class ProvidedTemplatesAPI:
    """
    Interface for querying Tenable-provided WAS v2 templates.
    """

    def __init__(self, http):
        self.http = http

    # --------------------------------------------------------------
    # LIST PROVIDED TEMPLATES
    # --------------------------------------------------------------
    def list(self) -> List[Dict[str, Any]]:
        """
        Returns a list of Tenable-provided templates.
        """
        path = "/was/v2/templates"
        response = self.http.get(path)

        if "items" not in response:
            raise TenableAPIError("Malformed response: missing 'items'")

        return response["items"]

    # --------------------------------------------------------------
    # GET TEMPLATE DETAILS
    # --------------------------------------------------------------
    def get(self, template_id: str) -> Dict[str, Any]:
        """
        Retrieve full metadata for a Tenable-provided template.
        """
        if not template_id:
            raise ValueError("template_id is required")

        path = f"/was/v2/templates/{template_id}"
        return self.http.get(path)
