# pytenable-was

A modular Python client and command-line interface for the **Tenable Web Application Scanning (WAS) v2 API**.  
This SDK provides clean, predictable wrappers around WAS scans, applications, findings, vulnerabilities, plugins, templates, folders, filters, notes, and related endpoints.

---

## ⚠️ Disclaimer

This tool is **not an official Tenable product**.

Use of this software is **not covered** by any license, warranty, or support agreement you may have with Tenable.  
All functionality is implemented independently based on publicly available WAS v2 API documentation.

---

# Overview

Tenable WAS v2 exposes a modern API for:

- Scans  
- Applications  
- Findings  
- Vulnerabilities  
- Plugins  
- Templates  
- User-defined templates  
- Folders  
- Filters  
- Scan notes  

`pytenable-was` provides a lightweight, dependency-minimal interface for all modules.  
All methods return **raw WAS JSON**, unless explicitly flattened for export.

---

# Features

### Core SDK
- Full WAS v2 endpoint coverage  
- AccessKey / SecretKey authentication  
- Automatic retry for Tenable throttling (`HTTP 429`)  
- Optional proxy support  
- Consistent error handling with `TenableAPIError`  
- Flattened CSV export helpers  
- In-memory caching for high-volume operations  

### CLI
- Configure credentials  
- List scans  
- Export findings (JSON or CSV)  
- List & export plugins (single, multi-ID, all)  
- Search vulnerabilities  
- Retrieve templates and user templates  
- Retrieve folders  
- Retrieve WAS filter schemas  
- Retrieve scan notes  
- JSON and CSV output options  

---

# Installation

### Standard install
```
pip install pytenable-was
```

### From source
```
git clone https://github.com/markteicher/pytenable-was
cd pytenable-was
pip install .
```

### macOS installation
macOS uses `python3` and `pip3`:

```
pip3 install pytenable-was
```

Or from source:

```
git clone https://github.com/markteicher/pytenable-was
cd pytenable-was
pip3 install .
```

Verify:

```
python3 -m pytenable_was --help
```

---

# Configuration

Set credentials:

```
pytenable-was config set --access-key <ACCESS_KEY> --secret-key <SECRET_KEY>
```

Optional proxy:

```
pytenable-was config set --access-key ... --secret-key ... --proxy http://proxy.example.com:8080
```

Show configuration:

```
pytenable-was config get
```

Clear:

```
pytenable-was config clear
```

Reset:

```
pytenable-was config reset
```

---

# CLI Usage

```
pytenable-was --help
```

---

# Scans

List scans:

```
pytenable-was scans list
```

Scan details:

```
pytenable-was scans details <scan_id>
```

---

# Findings Export

Export findings for a scan:

### JSON
```
pytenable-was findings export <scan_id> --json-out findings.json
```

### CSV
```
pytenable-was findings export <scan_id> --csv-out findings.csv
```

Flattened output is suitable for pandas and Splunk ingestion.

---

# Plugins

List plugins:

```
pytenable-was plugins list
```

Get a plugin:

```
pytenable-was plugins get <plugin_id>
```

Export a plugin (single):

```
pytenable-was plugins export <id> --json-out plugin.json
```

Export multiple plugins:

```
pytenable-was plugins export 98074,12345,77777 --csv-out plugins.csv
```

Export all plugins:

```
pytenable-was plugins export-all --json-out plugins.json
```

---

# Vulnerabilities

Search vulnerabilities:

```
pytenable-was vulns search --query "risk_factor:high"
```

Get vulnerability details:

```
pytenable-was vulns get <vuln_id>
```

Export vulnerabilities:

```
pytenable-was vulns export --csv-out vulns.csv
```

---

# Templates

```
pytenable-was templates list
```

# User-Defined Templates

```
pytenable-was user-templates list
```

---

# Folders

```
pytenable-was folders list
```

---

# Filters

```
pytenable-was filters scan-configs
pytenable-was filters scans
pytenable-was filters user-templates
pytenable-was filters vulns
pytenable-was filters vulns-scan
```

---

# Notes

Scan notes provide Tenable-generated informational or diagnostic messages related to a scan.  
Examples include authentication failures, configuration problems, or important runtime conditions.

List notes for one scan:

```
pytenable-was notes list <scan_id>
```

Export notes for multiple scans:

```
pytenable-was notes export 12345,67890 --csv-out notes.csv
```

Export all notes:

```
pytenable-was notes export-all --json-out all_notes.json
```

---

# Python SDK Example

```python
from pytenable_was import WASClient

client = WASClient(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
)

scans = client.scans.list_scans()
findings = client.findings.flatten("12345")
plugin = client.plugins.get_plugin("98074")
vuln = client.vulns.get_vuln("VULN_ID")
notes = client.notes.list_notes("12345")
```

---

# Error Handling

All API failures raise:

```
TenableAPIError(message, status_code, payload)
```

Includes:

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
