"""
pytenable-was
A modular SDK for the Tenable Web Application Scanning (WAS) v2 API.
"""

__version__ = "1.0.0"

# Core HTTP client
from .http import HTTPClient

# SDK API modules
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
    "__version__",
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
