# pytenable_was/models.py

"""
Pydantic v2 models for the Tenable WAS v2 SDK.

These models:
- Use flexible parsing (extra="allow") to survive Tenable's silent field changes.
- Provide clean, typed access to WAS objects (scans, applications, findings, URLs).
- Serve as a normalized interface between raw API JSON and higher-level SDK logic.
- Support safe model construction via model_validate() wrappers.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError


# ======================================================================
# Base model (flexible, extra fields allowed)
# ======================================================================

class WASBaseModel(BaseModel):
    """
    Base model for all WAS entities.
    Allows unknown fields to prevent breakage when Tenable updates the API.
    """
    model_config = ConfigDict(extra="allow")


# ======================================================================
# Utility functions for safe model creation
# ======================================================================

def parse_model(model_cls, raw: Any):
    """
    Safely parse a dict into a model instance.
    If parsing fails, return a WASBaseModel to preserve raw data.
    """
    if raw is None:
        return None

    try:
        return model_cls.model_validate(raw)
    except ValidationError:
        # Keep raw structure but as WASBaseModel to avoid raising
        return WASBaseModel.model_validate(raw)


# ======================================================================
# URL Model
# ======================================================================

class URLModel(WASBaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    enabled: Optional[bool] = None


# ======================================================================
# Application Model
# ======================================================================

class ApplicationModel(WASBaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    urls: Optional[List[URLModel]] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]):
        urls = data.get("urls") or []
        parsed_urls = [parse_model(URLModel, u) for u in urls]
        data = dict(data)
        data["urls"] = parsed_urls
        return parse_model(cls, data)


# ======================================================================
# Scan Model
# ======================================================================

class ScanStatus(WASBaseModel):
    """
    Allows unknown fields so Tenable can add more states safely.
    """
    status: Optional[str] = None


class ScanModel(WASBaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    application: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[Any] = Field(None, alias="start_time")
    end_time: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def duration_seconds(self) -> Optional[int]:
        """
        Returns scan duration in seconds, if timestamps are parseable.
        """
        try:
            if self.start_time and self.end_time:
                start = int(self.start_time)
                end = int(self.end_time)
                return max(0, end - start)
        except Exception:
            return None
        return None


# ======================================================================
# Finding Model
# ======================================================================

class FindingModel(WASBaseModel):
    id: Optional[str] = None
    scan_id: Optional[str] = None
    severity: Optional[str] = None
    plugin_id: Optional[str] = None
    description: Optional[str] = None
    evidence: Optional[Any] = None
    url: Optional[str] = None


# ======================================================================
# Scan Summary Model
# ======================================================================

class ScanSummary(WASBaseModel):
    scan_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    application: Optional[str] = None
    start: Optional[Any] = None
    end: Optional[Any] = None
    duration_seconds: Optional[int] = None

    @classmethod
    def from_scan(cls, scan: ScanModel):
        return cls(
            scan_id=scan.id,
            name=scan.name,
            status=scan.status,
            application=scan.application,
            start=scan.start_time,
            end=scan.end_time,
            duration_seconds=scan.duration_seconds,
        )


# ======================================================================
# Findings Collection Model
# ======================================================================

class FindingsSet(WASBaseModel):
    scan_id: Optional[str] = None
    findings: List[FindingModel] = None

    @classmethod
    def from_api(cls, scan_id: str, data: List[Dict[str, Any]]):
        parsed = [parse_model(FindingModel, f) for f in data]
        return cls(scan_id=scan_id, findings=parsed)
