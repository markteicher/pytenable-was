# templates.py
"""
User-Defined Templates for Tenable WAS v2
=========================================

These are *customer-created* templates that can be listed, inspected,
created, updated, and deleted via WAS v2.

Endpoints:
    GET    /was/v2/user-templates
    GET    /was/v2/user-templates/{uuid}
    POST   /was/v2/user-templates
    PUT    /was/v2/user-templates/{uuid}
    DELETE /was/v2/user-templates/{uuid}
"""

from .errors import TenableAPIError


class TemplateAPI:
    """
    Interface for managing user-defined WAS v2 templates.
    """

    def __init__(self, http):
        self.http = http

    # --------------------------------------------------------------
    # LIST USER TEMPLATES
    # --------------------------------------------------------------
    def list(self):
        """
        Returns list of all user-defined templates.

        Response fields typically include:
            user_template_id
            template_id (base system config)
            name
            description
            created_at
            updated_at
            owner_id
            is_shared
        """
        path = "/was/v2/user-templates"
        response = self.http.get(path)

        if "items" not in response:
            raise TenableAPIError("Malformed response: missing 'items'")

        return response["items"]

    # --------------------------------------------------------------
    # GET USER TEMPLATE DETAILS
    # --------------------------------------------------------------
    def get(self, user_template_id: str):
        """
        Retrieve full template definition for a user-defined template.
        """
        if not user_template_id:
            raise ValueError("user_template_id is required")

        path = f"/was/v2/user-templates/{user_template_id}"
        return self.http.get(path)

    # --------------------------------------------------------------
    # CREATE USER TEMPLATE
    # --------------------------------------------------------------
    def create(self, payload: dict):
        """
        Create a new user-defined WAS template.

        Payload is passed exactly as provided by user: 
            {
                "name": "...",
                "description": "...",
                "template_id": "system-base-template",
                "settings": {...},
                "permissions": [...]
            }
        """
        path = "/was/v2/user-templates"
        return self.http.post(path, json=payload)

    # --------------------------------------------------------------
    # UPDATE USER TEMPLATE
    # --------------------------------------------------------------
    def update(self, user_template_id: str, payload: dict):
        """
        Update an existing user-defined template.

        Only fields included in the payload will be updated.
        """
        if not user_template_id:
            raise ValueError("user_template_id is required")

        path = f"/was/v2/user-templates/{user_template_id}"
        return self.http.put(path, json=payload)

    # --------------------------------------------------------------
    # DELETE USER TEMPLATE
    # --------------------------------------------------------------
    def delete(self, user_template_id: str):
        """
        Delete a user-defined template.
        """
        if not user_template_id:
            raise ValueError("user_template_id is required")

        path = f"/was/v2/user-templates/{user_template_id}"
        return self.http.delete(path)
