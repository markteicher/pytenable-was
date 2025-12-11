# pytenable_was/plugins.py

"""
Tenable WAS v2 Plugins API

Supports:
    - Listing all plugins
    - Retrieving a single plugin
    - Retrieving multiple plugins (comma-separated IDs)
    - Flattening plugins for CSV/JSON export
    - Uniform dictionary-based output (safe for Tenable field changes)

This module is intentionally simple:
    • No Pydantic models (plugin schemas vary frequently)
    • All methods return plain dicts or list[dict]
"""

import logging
from typing import List, Dict, Any

from .errors import TenableAPIError

logger = logging.getLogger(__name__)


class PluginsAPI:
    """
    Lightweight Tenable WAS plugin metadata client.

    Endpoints:
        GET /was/v2/plugins
        GET /was/v2/plugins/{plugin_id}
    """

    def __init__(self, http):
        self.http = http

    # ---------------------------------------------------------------
    # Raw API calls
    # ---------------------------------------------------------------
    def _api_list_plugins(self) -> Dict[str, Any]:
        logger.info("Fetching plugin list...")
        return self.http.get("/was/v2/plugins")

    def _api_get_plugin(self, plugin_id: str) -> Dict[str, Any]:
        logger.info("Fetching plugin %s", plugin_id)
        return self.http.get(f"/was/v2/plugins/{plugin_id}")

    # ---------------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------------
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        Return a list of plugin metadata dictionaries.
        """
        raw = self._api_list_plugins()
        return raw.get("items") or raw.get("plugins") or []

    def get_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """
        Get one plugin by ID (dict)
        """
        return self._api_get_plugin(plugin_id)

    # ---------------------------------------------------------------
    # Multi-ID Support (for CLI)
    # ---------------------------------------------------------------
    def get_multiple(self, plugin_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple plugin IDs.

        Ensures the return type is always a list[dict].
        """
        results = []
        for pid in plugin_ids:
            try:
                results.append(self.get_plugin(pid))
            except TenableAPIError as exc:
                # We do NOT raise — we return partial results and record error.
                logger.error("Failed to retrieve plugin %s: %s", pid, exc)
                results.append({"plugin_id": pid, "error": str(exc)})
        return results

    # ---------------------------------------------------------------
    # Flattening for export (CSV/JSON)
    # ---------------------------------------------------------------
    def _flatten_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return a flattened plugin metadata structure.

        Nested lists (e.g., CWE, WASC, OWASP) are comma-joined.
        Nested dicts are JSON-encoded.

        This keeps export files safe for Splunk, pandas, CSV, etc.
        """
        flat = {}

        for key, val in obj.items():
            # nulls → None
            if val is None:
                flat[key] = None
                continue

            # simple types
            if isinstance(val, (int, float, str, bool)):
                flat[key] = val
                continue

            # lists → comma-separated
            if isinstance(val, list):
                flat[key] = ", ".join(str(v) for v in val)
                continue

            # nested dicts → JSON string
            if isinstance(val, dict):
                try:
                    import json
                    flat[key] = json.dumps(val, ensure_ascii=False)
                except Exception:
                    flat[key] = str(val)
                continue

            # fallback — stringify
            flat[key] = str(val)

        return flat

    # ---------------------------------------------------------------
    # Flatten single plugin
    # ---------------------------------------------------------------
    def flatten_single(self, plugin_id: str) -> Dict[str, Any]:
        """
        Retrieve + flatten a single plugin.
        """
        obj = self.get_plugin(plugin_id)
        return self._flatten_object(obj)

    # ---------------------------------------------------------------
    # Flatten all plugins
    # ---------------------------------------------------------------
    def flatten_all(self) -> List[Dict[str, Any]]:
        """
        Retrieve all plugins and return flattened list.
        """
        items = self.list_plugins()
        return [self._flatten_object(p) for p in items]

    # ---------------------------------------------------------------
    # Flatten multiple specific plugin IDs
    # ---------------------------------------------------------------
    def flatten_multiple(self, plugin_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve + flatten specific plugins (multi-ID support).
        """
        objs = self.get_multiple(plugin_ids)
        return [self._flatten_object(o) for o in objs]
