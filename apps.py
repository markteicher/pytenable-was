# pytenable_was/apps.py

"""
Tenable WAS v2 Applications module.

Capabilities:
    - Full CRUD support for WAS applications
    - URL management (list, add, remove)
    - Pydantic v2 model parsing
    - In-memory caching
    - Logging for traceability
"""

import logging
from typing import Dict, List, Optional

from .models import ApplicationModel, URLModel, parse_model
from .cache import InMemoryCache

logger = logging.getLogger(__name__)


class ApplicationsAPI:
    """
    WAS v2 Applications API client with full CRUD + URL management.

    Uses:
        - HTTP client for API calls
        - Pydantic v2 models for parsing
        - InMemoryCache for low-latency access
    """

    def __init__(self, http, cache: Optional[InMemoryCache] = None):
        self.http = http
        self.cache = cache or InMemoryCache()

    # ====================================================================
    # Raw API calls
    # ====================================================================

    def _api_list_apps(self) -> Dict:
        logger.info("Fetching applications list...")
        return self.http.get("/was/v2/applications")

    def _api_get_app(self, app_id: str) -> Dict:
        logger.info("Fetching application %s...", app_id)
        return self.http.get(f"/was/v2/applications/{app_id}")

    def _api_create_app(self, body: Dict) -> Dict:
        logger.info("Creating new application...")
        return self.http.post("/was/v2/applications", json=body)

    def _api_update_app(self, app_id: str, body: Dict) -> Dict:
        logger.info("Updating application %s...", app_id)
        return self.http.post(f"/was/v2/applications/{app_id}", json=body)

    def _api_delete_app(self, app_id: str) -> Dict:
        logger.info("Deleting application %s...", app_id)
        return self.http.delete(f"/was/v2/applications/{app_id}")

    def _api_get_urls(self, app_id: str) -> Dict:
        logger.info("Fetching URLs for application %s...", app_id)
        return self.http.get(f"/was/v2/applications/{app_id}/urls")

    def _api_set_urls(self, app_id: str, urls: List[Dict]) -> Dict:
        logger.info("Updating URLs for application %s...", app_id)
        return self.http.post(f"/was/v2/applications/{app_id}/urls", json={"urls": urls})

    # ====================================================================
    # Models & cache
    # ====================================================================

    def list_all(self, use_cache: bool = True) -> List[ApplicationModel]:
        """
        List all WAS applications.
        """
        if use_cache:
            cached = self.cache._store.get("apps", {})
            if cached:
                logger.debug("Loaded %s apps from cache.", len(cached))
                return [entry.value for entry in cached.values()]

        raw = self._api_list_apps()
        items = raw.get("items") or raw.get("applications") or []

        models = []
        for app in items:
            model = ApplicationModel.from_api(app)
            if model.id:
                self.cache.set("apps", model.id, model, ttl=600)
            models.append(model)

        logger.info("Loaded %s applications from API.", len(models))
        return models

    def get_app(self, app_id: str, use_cache: bool = True) -> ApplicationModel:
        """
        Retrieve a single application by ID.
        """
        if use_cache:
            try:
                model = self.cache.get("apps", app_id)
                logger.debug("Application %s loaded from cache.", app_id)
                return model
            except Exception:
                pass

        raw = self._api_get_app(app_id)
        model = ApplicationModel.from_api(raw)
        if model.id:
            self.cache.set("apps", model.id, model, ttl=600)
        return model

    # ====================================================================
    # CRUD
    # ====================================================================

    def create_app(self, name: str, description: str = "", urls: Optional[List[str]] = None) -> ApplicationModel:
        """
        Create an application with optional URL list.
        """
        body = {"name": name, "description": description}
        if urls:
            body["urls"] = [{"url": u} for u in urls]

        raw = self._api_create_app(body)
        model = ApplicationModel.from_api(raw)

        if model.id:
            self.cache.set("apps", model.id, model, ttl=600)

        return model

    def update_app(self, app_id: str, name: Optional[str] = None, description: Optional[str] = None) -> ApplicationModel:
        """
        Update application metadata.
        """
        body = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description

        raw = self._api_update_app(app_id, body)
        model = ApplicationModel.from_api(raw)

        if model.id:
            self.cache.set("apps", model.id, model, ttl=600)

        return model

    def delete_app(self, app_id: str) -> None:
        """
        Delete an application.
        """
        self._api_delete_app(app_id)
        self.cache.delete("apps", app_id)

    # ====================================================================
    # URL Management
    # ====================================================================

    def list_urls(self, app_id: str) -> List[URLModel]:
        """
        Return all URLs associated with an application.
        """
        raw = self._api_get_urls(app_id)
        items = raw.get("urls") or []
        return [parse_model(URLModel, u) for u in items]

    def set_urls(self, app_id: str, urls: List[str]) -> List[URLModel]:
        """
        Replace URL list for an application.
        """
        payload = [{"url": u} for u in urls]
        raw = self._api_set_urls(app_id, payload)
        items = raw.get("urls") or []

        models = [parse_model(URLModel, u) for u in items]

        # refresh application cache
        try:
            app = self.get_app(app_id, use_cache=False)
            app.urls = models
            self.cache.set("apps", app_id, app, ttl=600)
        except Exception:
            pass

        return models

    # ====================================================================
    # Summary (Simple but useful)
    # ====================================================================

    def summary(self, app_id: str) -> Dict:
        """
        Return a simple summary useful for dashboards or CLI output.
        """
        app = self.get_app(app_id)
        return {
            "id": app.id,
            "name": app.name,
            "urls": len(app.urls or []),
            "tags": app.tags or [],
        }
