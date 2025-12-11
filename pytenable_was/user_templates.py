# pytenable_was/user_templates.py

"""
User-defined WAS Templates

Endpoints:
    GET    /was/v2/user-templates
    GET    /was/v2/user-templates/{uuid}
    POST   /was/v2/user-templates
    PUT    /was/v2/user-templates/{uuid}
    DELETE /was/v2/user-templates/{uuid}

These are customizable, customer-owned templates. They support full CRUD.
"""

import logging
from typing import Dict, List, Any

from .errors import TenableAPIError

logger = logging.getLogger(__name__)


class UserTemplatesAPI:
    """
    Manage customer-created WAS scanning templates.
    """

    def __init__(self, http):
        self.http = http

    # ---------------------------------------------------------
    # Raw API calls
    # ---------------------------------------------------------
    def _api_list(self) -> Dict[str, Any]:
        logger.info("Fetching user-defined templates")
        return self.http.get("/was/v2/user-templates")

    def _api_get(self, template_id: str) -> Dict[str, Any]:
        logger.info("Fetching user template %s", template_id)
        return self.http.get(f"/was/v2/user-templates/{template_id}")

    def _api_create(self, body: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Creating user-defined template")
        return self.http.post("/was/v2/user-templates", json=body)

    def _api_update(self, template_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Updating user-defined template %s", template_id)
        return self.http.put(f"/was/v2/user-templates/{template_id}", json=body)

    def _api_delete(self, template_id: str) -> Dict[str, Any]:
        logger.info("Deleting user-defined template %s", template_id)
        return self.http.delete(f"/was/v2/user-templates/{template_id}")

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------
    def list_user_templates(self) -> List[Dict[str, Any]]:
        """
        Returns list of user-defined templates.
        """
        raw = self._api_list()
        items = raw.get("items") or raw.get("user_templates") or []

        if not isinstance(items, list):
            raise TenableAPIError("Malformed user template list response")

        return items

    def get_user_template(self, template_id: str) -> Dict[str, Any]:
        """
        Returns a full template definition.
        """
        raw = self._api_get(template_id)
        if not isinstance(raw, dict):
            raise TenableAPIError(f"Malformed template details for {template_id}")
        return raw

    def create_user_template(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user template.

        Typical payload:
            {
               "name": "...",
               "description": "...",
               "template_id": "<base-system-template>",
               "settings": {},
               "permissions": [...]
            }
        """
        return self._api_create(payload)

    def update_user_template(self, template_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a user-defined template.

        Only fields included in the payload will be updated.
        """
        return self._api_update(template_id, payload)

    def delete_user_template(self, template_id: str) -> None:
        """
        Delete a user template.
        """
        self._api_delete(template_id)
