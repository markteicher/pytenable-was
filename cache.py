# pytenable_was/cache.py

"""
In-memory caching layer for the Tenable WAS v2 SDK.

Supports:
    - entity-level namespaces (scans, apps, findings, urls)
    - TTL-based expiration
    - thread safety
    - model-aware storage (Pydantic v2)
    - debug logging of cache activity
    - optional hooks for automatic population via HTTP layer

This cache is intentionally simple but powerful enough for
production workflows. Persistent caching (SQLite/MSSQL) will
be added later when required.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

from .errors import CacheKeyError

logger = logging.getLogger(__name__)


class CacheEntry:
    """
    Represents one cached item.
    Stores:
        - value (Pydantic model or raw data)
        - timestamp (epoch seconds)
        - ttl (seconds)
    """
    __slots__ = ("value", "timestamp", "ttl")

    def __init__(self, value: Any, ttl: Optional[int]):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl

    def expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.time() - self.timestamp) > self.ttl


class InMemoryCache:
    """
    Cadillac-grade in-memory cache for WAS SDK.

    Namespaces:
        scans[]
        apps[]
        findings[]
        urls[]
        raw[]

    TTL support:
        Per-entry TTL, not global.
        TTL=None means "never expire".

    Thread safe:
        All operations protected by a lock.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, CacheEntry]] = {
            "scans": {},
            "apps": {},
            "findings": {},
            "urls": {},
            "raw": {},
        }

    # ------------------------------------------------------------
    # Get item
    # ------------------------------------------------------------
    def get(self, namespace: str, key: str) -> Any:
        with self._lock:
            ns = self._store.get(namespace)
            if ns is None or key not in ns:
                logger.debug("Cache miss: %s[%s]", namespace, key)
                raise CacheKeyError(f"{namespace}:{key}")

            entry = ns[key]
            if entry.expired():
                logger.info("Cache expired: %s[%s]", namespace, key)
                del ns[key]
                raise CacheKeyError(f"{namespace}:{key} (expired)")

            logger.debug("Cache hit: %s[%s]", namespace, key)
            return entry.value

    # ------------------------------------------------------------
    # Set item
    # ------------------------------------------------------------
    def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None):
        with self._lock:
            if namespace not in self._store:
                self._store[namespace] = {}

            self._store[namespace][key] = CacheEntry(value, ttl)
            logger.debug("Cache set: %s[%s] ttl=%s", namespace, key, ttl)

    # ------------------------------------------------------------
    # Delete item
    # ------------------------------------------------------------
    def delete(self, namespace: str, key: str):
        with self._lock:
            if namespace in self._store and key in self._store[namespace]:
                del self._store[namespace][key]
                logger.debug("Cache delete: %s[%s]", namespace, key)

    # ------------------------------------------------------------
    # Clear namespace or whole cache
    # ------------------------------------------------------------
    def clear_namespace(self, namespace: str):
        with self._lock:
            if namespace in self._store:
                self._store[namespace].clear()
                logger.info("Cache cleared: %s", namespace)

    def clear_all(self):
        with self._lock:
            for ns in self._store.values():
                ns.clear()
            logger.info("All caches cleared.")

    # ------------------------------------------------------------
    # Preloading / warming helpers
    # ------------------------------------------------------------
    def warm(self, namespace: str, items: Dict[str, Any], ttl: Optional[int] = None):
        """
        Warm-cache a batch of items (useful for scans, apps, findings)
        """
        with self._lock:
            for key, value in items.items():
                self._store[namespace][key] = CacheEntry(value, ttl)
            logger.info("Warm-loaded %s items into %s", len(items), namespace)

    # ------------------------------------------------------------
    # Raw storage (for debugging or unstructured payloads)
    # ------------------------------------------------------------
    def raw_set(self, key: str, value: Any):
        self.set("raw", key, value)

    def raw_get(self, key: str) -> Any:
        return self.get("raw", key)
