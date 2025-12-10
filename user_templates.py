# user_templates.py
"""
User-Defined Templates for Tenable WAS v2
=========================================

Customers can create, modify, delete, and list their own templates.

Endpoints:
    GET    /was/v2/user-templates
    GET    /was/v2/user-templates/{uuid}
    POST   /was/v2/user-templates
    PUT    /was/v2/user-templates/{uuid}
    DELETE /was/v2/user-templates/{uuid}
"""

from typing import List, Dict, Any
from .errors import TenableAPIError


class UserTemplatesAPI:
    """
    Interface for managing user-defined WAS v2 templates.
    """

    def __init__(self, http):
        self.http = http

    # --------------------------------------------------------------
    # LIST USER TEMPLATES
    # --------------------------------------------------------------
    def list(self) -> List[Dict[str, Any]]:
        """
        Returns list of all user-defined templates.
        """
        path = "/was/v2/user-templates"
        response = self.http.get(path)

        if "items" not in response:
            raise TenableAPIError("Malformed response: missing 'items'")

        return response["items"]

    # --------------------------------------------------------------
    # GET USER TEMPLATE DETAILS
    # --------------------------------------------------------------
    def get(self, user_template_id: str) -> Dict[str, Any]:
        """
        Retrieve full template definition.
        """
        if not user_template_id:
            raise ValueError("user_template_id is required")

        path = f"/was/v2/user-templates/{user_template_id}"
        return self.http.get(path)

    # --------------------------------------------------------------
    # CREATE USER TEMPLATE
    # --------------------------------------------------------------
    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user-defined WAS template.
        """
        path = "/was/v2/user-templates"
        return self.http.post(path, json=payload)

    # --------------------------------------------------------------
    # UPDATE USER TEMPLATE
    # --------------------------------------------------------------
    def update(self, user_template_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing template.
        """
        if not user_template_id:
            raise ValueError("user_template_id is required")

        path = f"/was/v2/user-templates/{user_template_id}"
        return self.http.put(path, json=payload)

    # --------------------------------------------------------------
    # DELETE USER TEMPLATE
    # --------------------------------------------------------------
    def delete(self, user_template_id: str) -> Dict[str, Any]:
        """
        Delete a user-defined template.
        """
        if not user_template_id:
            raise ValueError("user_template_id is required")

        path = f"/was/v2/user-templates/{user_template_id}"
        return self.http.delete(path)
