"""
pytenable-was
A modular SDK for the Tenable Web Application Scanning (WAS) v2 API.
"""

# Core HTTP client
from .http import HTTPClient

# SDK modules
from .scans import ScansAPI
from .findings import FindingsAPI
from .vulns import VulnsAPI
from .plugins import PluginsAPI
from .templates import TemplatesAPI
from .user_templates import UserTemplatesAPI
from .folders import FoldersAPI
from .filters import FiltersAPI
from .notes import NotesAPI

# Utilities
from .utils import flatten_dict, pretty_json

__all__ = [
    "HTTPClient",
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
