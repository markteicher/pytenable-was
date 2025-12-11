# pytenable-was

A modular Python client and command-line interface for the **Tenable Web Application Scanning (WAS) v2 API**.  
This SDK provides clean, predictable wrappers around WAS scans, applications, findings, plugins, templates, and related endpoints.

---

## ⚠️ Disclaimer

This tool is **not an official Tenable product**.

Use of this software is **not covered** by any license, warranty, or support agreement you may have with Tenable.  
All functionality is implemented independently based on publicly available WAS v2 API documentation.

---

# Overview

Tenable Web Application Scanning (WAS) v2 exposes a modern API for:

- Managing scans  
- Inspecting scan details  
- Reviewing findings and vulnerabilities  
- Working with plugins and metadata  
- Managing applications  
- Managing Tenable-provided templates and user-defined templates  
- Exporting findings  
- Retrieving folders and filters  
- Querying users for scan owner enrichment  

`pytenable-was` provides a **lightweight, dependency-minimal**, fully scriptable interface for all of the above:

- `scans` — list scans, retrieve details, export, multi-ownership updates  
- `applications` — retrieve application metadata and URLs  
- `findings` — retrieve findings and export flattened CSV/JSON  
- `plugins` — list plugins, fetch plugin details, multi-ID export  
- `templates` — list Tenable-provided templates  
- `user_templates` — list and access user-defined templates  
- `folders` — list WAS folders  
- `filters` — retrieve WAS filter metadata (scan configs, scans, vulns, templates)  
- `users` — retrieve user metadata and map scans to owners  
- `config` — local credential storage with masking and proxy support  
- `http` — authenticated HTTP client with retry/throttling handling  

All modules produce **raw WAS JSON** unless a helper method (e.g., `flatten`, `summary`) explicitly transforms output.

---

# Features

### Core SDK Features
- Full WAS v2 API coverage (scans → plugins → findings → folders → filters → templates)  
- Clean, modular Python modules (no Tenable SDK dependency)  
- Authentication via AccessKey / SecretKey  
- Uniform error handling with `TenableAPIError`  
- Automatic retry logic for Tenable throttling (`HTTP 429`)  
- Optional proxy support (`http://` or `https://`, with or without authentication)  
- Flattened export helpers for CSV or DataFrame loading  
- In-memory caching layer for high-volume operations  

### Command-Line Interface (CLI)
- Configure API keys, proxy settings, and config resets  
- List scans or retrieve scan details  
- Export findings for a scan  
- List or fetch plugin details  
- Export a plugin or multiple plugins (JSON or CSV)  
- List Tenable-provided templates  
- List user-defined templates  
- List users (for owner enrichment)  
- List folders  
- Retrieve WAS filter metadata  
- Output to terminal, JSON, or CSV  

---

# Installation

```
pip install pytenable-was
```

Or install from source:

```
git clone https://github.com/markteicher/pytenable-was
cd pytenable-was
pip install .
```

Python 3.8+ is required.

---

# Configuration

Before using the CLI, configure your API credentials:

```
pytenable-was config set --access-key <ACCESS_KEY> --secret-key <SECRET_KEY>
```

Optional proxy:

```
pytenable-was config set --access-key ... --secret-key ... --proxy http://proxy.example.com:8080
```

Show stored configuration (keys are masked):

```
pytenable-was config get
```

Clear configuration:

```
pytenable-was config clear
```

Reset with confirmation prompt:

```
pytenable-was config reset
```

Configuration is stored locally in the OS-standard user config directory.

---

# CLI Usage

Run:

```
pytenable-was --help
```

---

## Scans

### List scans
```
pytenable-was scans list
```

### Get scan details
```
pytenable-was scans details <scan_id>
```

### (Future) Launch, stop, or update ownership for multiple scans

---

## Findings Export

Export all findings for a given scan:

### JSON
```
pytenable-was findings export <scan_id> --json-out findings.json
```

### CSV (flattened)
```
pytenable-was findings export <scan_id> --csv-out findings.csv
```

Flattening converts nested WAS findings into one row per finding for DataFrame/Splunk ingestion.

---

## Plugins

### List plugins
```
pytenable-was plugins list
```

### Get a single plugin
```
pytenable-was plugins get <plugin_id>
```

### Export a single plugin
```
pytenable-was plugins export <plugin_id> --json-out 98074.json
```

### Export multiple plugins
```
pytenable-was plugins export 98074,12345,77777 --csv-out plugins.csv
```

### Export all plugins
```
pytenable-was plugins export-all --json-out plugins.json
```

---

## Templates (Tenable-provided)

```
pytenable-was templates list
```

---

## User-Defined Templates

```
pytenable-was user-templates list
```

---

## Users (for scan owner enrichment)

```
pytenable-was users list
```

---

## Folders

```
pytenable-was folders list
```

---

## Filters

Retrieve WAS v2 filter schema:

```
pytenable-was filters scan-configs
pytenable-was filters scans
pytenable-was filters user-templates
pytenable-was filters vulns
pytenable-was filters vulns-scan
```

---

# Python SDK Usage

```python
from pytenable_was import WASClient

client = WASClient(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    proxy=None
)

# List scans
scans = client.scans.list_scans()

# Get a scan
details = client.scans.get_scan("12345")

# Export findings
findings = client.findings.flatten("12345")

# Plugin metadata
plugin = client.plugins.get_plugin("98074")
```

---

# Error Handling

All API failures raise:

```
TenableAPIError(message, status_code, payload)
```

Attributes include:

- HTTP status  
- Raw JSON payload  
- Human-readable message  

Cache lookups may raise:

```
CacheKeyError
```

---

# License

MIT License  
© Mark Teicher
