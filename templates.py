# pytenable_was/templates.py

"""
Tenable-provided WAS Templates (read-only)

Endpoints:
    GET /was/v2/templates
    GET /was/v2/templates/{template_id}

These are the built-in scanning templates Tenable ships. They are
immutable; you cannot create or modify them through the API.

This module intentionally provides:
    • list_all()
    • get(template_id)
"""

import logging
from typing import Dict, List, Any

from .errors import TenableAPIError

logger = logging.getLogger(__name__)


class TemplatesAPI:
    """
    Wrapper for WAS system templates (read-only).
    """

    def __init__(self, http):
        self.http = http

    # ---------------------------------------------------------
    # Raw API calls
    # ---------------------------------------------------------
    def _api_list_templates(self) -> Dict[str, Any]:
        logger.info("Fetching Tenable-provided templates")
        return self.http.get("/was/v2/templates")

    def _api_get_template(self, template_id: str) -> Dict[str, Any]:
        logger.info("Fetching template %s", template_id)
        return self.http.get(f"/was/v2/templates/{template_id}")

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------
    def list_all(self) -> List[Dict[str, Any]]:
        """
        Returns list of Tenable-provided templates.
        """
        raw = self._api_list_templates()
        templates = raw.get("items") or raw.get("templates") or []

        if not isinstance(templates, list):
            raise TenableAPIError("Malformed template list response")

        return templates

    def get(self, template_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a single built-in template.
        """
        raw = self._api_get_template(template_id)
        if not isinstance(raw, dict):
            raise TenableAPIError(f"Malformed template details for {template_id}")
        return raw
