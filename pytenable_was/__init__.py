"""
pytenable-was

A modular SDK and CLI for the Tenable Web Application Scanning (WAS) v2 API.
"""

from importlib.metadata import version

# ---------------------------------------------------------------------------
# Package version (single source of truth: pyproject.toml)
# ---------------------------------------------------------------------------

__version__ = version("pytenable-was")


# ---------------------------------------------------------------------------
# Core infrastructure
# ---------------------------------------------------------------------------

from .http import HTTPClient
from .config import Config


# ---------------------------------------------------------------------------
# API modules
# ---------------------------------------------------------------------------

from .scans import ScansAPI
from .findings import FindingsAPI
from .vulns import VulnsAPI
from .plugins import PluginsAPI
from .templates import TemplatesAPI
from .user_templates import UserTemplatesAPI
from .folders import FoldersAPI
from .filters import FiltersAPI
from .notes import NotesAPI


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

from .utils import (
    flatten_dict,
    pretty_json,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "__version__",
    "HTTPClient",
    "Config",
    "ScansAPI",
    "FindingsAPI",
    "VulnsAPI",
    "PluginsAPI",
    "TemplatesAPI",
    "UserTemplatesAPI",
    "FoldersAPI",
    "FiltersAPI",
    "NotesAPI",
    "flatten_dict",
    "pretty_json",
]
