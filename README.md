# pytenable-was

A modular Python client and command-line interface for the **Tenable Web Application Scanning (WAS) v2 API**.  
This SDK provides clean, predictable wrappers around WAS scans, applications, findings, plugins, templates, vulnerabilities, notes, folders, and related metadata.

---

## ⚠️ Disclaimer

This tool is **not an official Tenable product**.

Use of this software is **not covered** by any license, warranty, or support agreement you may have with Tenable.  
All functionality is implemented independently using publicly available WAS v2 API documentation.


![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active%20development-yellow.svg)
---

# Overview

Tenable Web Application Scanning (WAS) v2 exposes REST endpoints for:

- Managing scans  
- Inspecting scan details  
- Reviewing findings & vulnerabilities  
- Accessing plugin metadata  
- Working with templates (Tenable-provided & user-defined)  
- Exporting findings  
- Retrieving folders & filters  
- Querying users for ownership mapping  
- Retrieving scan notes  
- Downloading attachments (future module)  

`pytenable-was` provides a **lightweight, dependency-minimal**, fully scriptable interface for all of these:

- `scans` — list scans, get scan details, **change scan owner**, **bulk owner updates**
- `findings` — list findings, export flattened CSV/JSON, export-all
- `vulns` — search vulnerabilities, get details, export-all
- `plugins` — list plugins, fetch details, export single or multiple
- `templates` — list Tenable-provided templates
- `user_templates` — list user-defined templates
- `notes` — list scan notes
- `folders` — list WAS folders
- `filters` — retrieve WAS metadata filters
- `users` — internal lookup module used for scan owner enrichment
- `config` — credential storage with masking & proxy support
- `http` — robust HTTP client with retry logic & throttling management

All modules return **raw WAS JSON** unless a helper (like `flatten`) is explicitly used.

---

# Features

### Core SDK Features
- Strict coverage of WAS v2 endpoints  
- Clean, predictable module layout  
- Automatic retry logic for `HTTP 429` throttling  
- Uniform error handling via `TenableAPIError`  
- Optional proxy support  
- Flatten helpers for Splunk/DataFrames  
- In-memory caching  
- Zero dependency on Tenable’s SDK  

### CLI Features
- Configure access keys & proxy  
- List scans or view scan details  
- **Change scan ownership (single + bulk)**  
- Export findings (single scan or all scans)  
- Export vulnerabilities  
- List plugins or fetch details  
- Export plugins (single or multiple)  
- List templates & user templates  
- List scan notes  
- Retrieve WAS filter metadata  
- Export flattened CSV or JSON  

---

# Installation

## Standard (Linux / Windows)
```
pip install pytenable-was
```

## macOS (Python 3 pre-installed)
macOS often aliases Python 3’s pip as `pip3`:

```
pip3 install pytenable-was
```

Or ensure you are using Python 3 explicitly:

```
python3 -m pip install pytenable-was
```

## Install from source
```
git clone https://github.com/markteicher/pytenable-was
cd pytenable-was
pip install .
```

Python 3.8+ is required.

---

# Configuration

Configure your API credentials:

```
pytenable-was config set --access-key <ACCESS_KEY> --secret-key <SECRET_KEY>
```

With proxy:

```
pytenable-was config set --access-key ... --secret-key ... --proxy http://proxy:8080
```

Show stored configuration:

```
pytenable-was config get
```

Clear configuration:

```
pytenable-was config clear
```

Prompted reset:

```
pytenable-was config reset
```

Credentials are stored locally in the OS-standard config directory  
(keys are masked—never logged or shown in full).

---

# CLI Usage

```
pytenable-was --help
pytenable-was --version
```

---

# Scans

## List scans
```
pytenable-was scans list
```

## Get scan details
```
pytenable-was scans details <scan_id>
```

---

# 🔐 Scan Ownership Management

## Change owner of a single scan
```
pytenable-was scans set-owner <scan_id> --user-id <USER_ID>
```

Example:
```
pytenable-was scans set-owner 123456 --user-id 88a1e9e2
```

---

## Bulk ownership change (comma-separated IDs)
```
pytenable-was scans set-owner-bulk 1001,1002,1003 --user-id <USER_ID>
```

Progress bar example:
```
Updating scan owners: 37% |███████▌          | 28/75 scans
```

---

## Bulk ownership change from a file
```
pytenable-was scans set-owner-bulk --from-file scan_ids.txt --user-id <USER_ID>
```

Where `scan_ids.txt` contains:
```
1001
1002
1003
```

---

# Findings

## Export findings from a single scan
### JSON
```
pytenable-was findings export <scan_id> --json-out findings.json
```

### CSV (flattened)
```
pytenable-was findings export <scan_id> --csv-out findings.csv
```

## Export all scan findings (all scans)
```
pytenable-was findings export-all --csv-out all_findings.csv
```

Flattened output is ideal for Splunk, SIEM ingestion, and DataFrame workloads.

---

# Vulnerabilities

## Search vulnerabilities
```
pytenable-was vulns search --severity high
```

## Get vulnerability details
```
pytenable-was vulns get <vuln_id>
```

## Export all vulnerabilities
```
pytenable-was vulns export-all --csv-out vulns.csv
```

---

# Plugins

## List plugins
```
pytenable-was plugins list
```

## Get details for a plugin
```
pytenable-was plugins get <plugin_id>
```

## Export a single plugin
```
pytenable-was plugins export <plugin_id> --json-out plugin.json
```

## Export multiple plugins
```
pytenable-was plugins export 98074,12345,77777 --csv-out plugins.csv
```

## Export ALL plugins
```
pytenable-was plugins export-all --json-out plugins_all.json
```

---

# Templates

## Tenable-provided templates
```
pytenable-was templates list
```

## User-defined templates
```
pytenable-was user-templates list
```

---

# Notes (Scan Notes)

```
pytenable-was notes list <scan_id>
```

Example output fields:

- `scan_note_id`  
- `scan_id`  
- `created_at`  
- `severity`  
- `title`  
- `message`  

Scan notes come directly from WAS results and reflect scan-level conditions, such as authentication failures or environmental issues during scanning.

---

# Folders

```
pytenable-was folders list
```

---

# Filters

Retrieve WAS metadata filters:

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
    access_key="YOUR_KEY",
    secret_key="YOUR_SECRET",
    proxy=None,
)

# List scans
scans = client.scans.list_scans()

# Scan details
details = client.scans.get_scan("12345")

# Change owner
client.scans.change_owner("12345", new_owner_id="88a1e9e2")

# Findings
findings = client.findings.flatten("12345")

# Vulnerability details
v = client.vulns.get_vuln("98074")
```

---

# Error Handling

All API failures raise:

```
TenableAPIError(message, status_code, payload)
```

Cache lookup failures:

```
CacheKeyError
```

All exceptions provide:

- HTTP status  
- Raw payload  
- Error context  
- Human-readable message  

---

# License

#MIT License

#Copyright (c) 2025 Mark Teicher

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
