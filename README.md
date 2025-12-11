# pytenable-was

A modular Python client and command-line interface for the **Tenable Web Application Scanning (WAS) v2 API**.  
This SDK provides clean, predictable wrappers around WAS scans, applications, findings, plugins, templates, folders, filters, vulns, and scan notes.

---

## ⚠️ Disclaimer

This tool is **not an official Tenable product**.

Use of this software is **not covered** by any license, warranty, or support agreement you may have with Tenable.  
All functionality is implemented independently based on publicly available WAS v2 API documentation.

---

# Overview

Tenable Web Application Scanning (WAS) v2 exposes APIs for:

- Managing scans  
- Retrieving scan details  
- Reviewing findings  
- Inspecting vulnerabilities  
- Working with Tenable-provided & user-defined templates  
- Listing folders & filters  
- Fetching plugin metadata  
- **Accessing scanner-generated Scan Notes**  
- Enriching scan metadata (internally mapped via user-details APIs)  

`pytenable-was` provides a **lightweight, dependency-minimal**, fully scriptable interface for these WAS v2 modules:

- `scans` — list scans, retrieve details  
- `applications` — list & retrieve application metadata  
- `findings` — retrieve & export findings  
- `plugins` — list plugins, get details, export metadata  
- `templates` — Tenable-provided templates  
- `user_templates` — customer-created templates  
- `folders` — list WAS folders  
- `filters` — retrieve WAS filter metadata  
- `notes` — read scanner-generated notes for each scan  
- `vulns` — list and retrieve WAS vulnerability records  
- `config` — local credential storage & proxy configuration  
- `http` — retry logic, throttling, safe JSON parsing  

All modules return **raw WAS JSON** unless helper methods transform the output for export.

---

# Features

### Core SDK Features
- Full coverage of major WAS v2 endpoints  
- Predictable, modularized Python layout  
- Safe authentication via AccessKey/SecretKey  
- Uniform error handling (`TenableAPIError`)  
- Automatic retry logic for Tenable throttling (`HTTP 429`)  
- Proxy support (http/https, with or without authentication)  
- Flattened export helpers for analytics ingestion (CSV/JSON)  
- Local in-memory caching for performance  

### Command-Line Interface (CLI)
- Configure API keys + proxy support  
- List scans or retrieve scan details  
- Export findings  
- Export plugin metadata  
- List templates and user-defined templates  
- List WAS folders & filters  
- **List and export scan notes (single scan, multi-scan, or all scans)**  
- Output to JSON, CSV, or terminal  

---

# Installation

```sh
pip install pytenable-was
