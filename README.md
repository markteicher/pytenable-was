# pytenable-was

> ⚠️ **WARNING — NOT AN OFFICIAL TENABLE PRODUCT**
>
> This software is independently developed and **not supported by Tenable**.
> It is **not covered** under any commercial Tenable agreement.
> All functionality is based solely on publicly available WAS v2 API documentation.

A modular Python client and command-line interface for the **Tenable Web Application Scanning (WAS) v2 API**.  
This SDK provides clean, predictable wrappers around WAS scans, applications, findings, plugins, vulnerabilities, templates, folders, filters, and related endpoints.

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
- `vulns` — WAS vulnerabilities search, details, export, flattening  
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
- Full WAS v2 API coverage (scans → plugins → findings → vulns → filters → templates)  
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
- Search, retrieve, and export vulnerabilities  
- List or fetch plugin details  
- Export plugins individually or in batch  
- List Tenable-provided templates  
- List user-defined templates  
- List users (for owner enrichment)  
- List folders  
- Retrieve WAS filter metadata  
- Output to terminal, JSON, or CSV  

---

# Installation
