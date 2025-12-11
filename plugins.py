# pytenable_was/plugins.py
"""
Tenable WAS v2 Plugins module.

Supports:
    - Listing all WAS plugins
    - Getting plugin details
    - Flattened export format
    - Zero external dependencies
"""

import logging
from typing import List, Dict

from .errors import TenableAPIError
from .utils import flatten_model

logger = logging.getLogger(__name__)


class PluginsAPI:
    """
    WAS v2 Plugins API client.

    Endpoints:
        GET /was/v2/plugins
        GET /was/v2/plugins/{plugin_id}
    """

    def __init__(self, http):
        self.http = http

    # ----------------------------------------------------------
    # Raw API calls
    # ----------------------------------------------------------
    def _api_list(self) -> Dict:
        logger.info("Fetching WAS plugin list…")
        return self.http.get("/was/v2/plugins")

    def _api_details(self, plugin_id: str) -> Dict:
        logger.info("Fetching plugin details for ID %s…", plugin_id)
        return self.http.get(f"/was/v2/plugins/{plugin_id}")

    # ----------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------
    def list_plugins(self) -> List[Dict]:
        """
        Returns a list of all WAS plugins.
        """
        raw = self._api_list()
        items = raw.get("items") or raw.get("plugins") or []
        return items

    def get_plugin(self, plugin_id: str) -> Dict:
        """
        Retrieve full plugin metadata.
        """
        if not plugin_id:
            raise ValueError("plugin_id is required")

        return self._api_details(plugin_id)

    # ----------------------------------------------------------
    # Flatten helpers (for CSV export)
    # ----------------------------------------------------------
    def flatten_all(self) -> List[Dict]:
        """
        Flatten all plugin metadata for export.
        """
        plugins = self.list_plugins()
        return [flatten_model(p) for p in plugins]

    def flatten_single(self, plugin_id: str) -> Dict:
        """
        Flatten a single plugin metadata record.
        """
        details = self.get_plugin(plugin_id)
        return flatten_model(details)
