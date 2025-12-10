# pytenable-was

A modular Python client for the Tenable Web Application Scanning (WAS) v2 API.  
This package implements a clean, reliable set of endpoint wrappers for interacting with WAS scans, applications, and findings using AccessKey/SecretKey authentication.  
The goal is stability, clarity, and accurate reflection of the official WAS v2 API.

---

## Overview

Tenable Web Application Scanning (WAS) v2 provides programmatic access to scan management, application inventories, findings, vulnerabilities, and scan execution.  
`pytenable-was` exposes these capabilities through small, testable Python modules:

- `scans` — list scans, retrieve details, launch scans  
- `applications` — list applications, retrieve application details  
- `findings` — retrieve findings for a scan  
- `http` — request handling, retry logic, throttling, JSON parsing  
- `auth` — headers for AccessKey/SecretKey authentication  
- `cli` — optional command-line interface  

The design avoids hidden abstractions and returns raw WAS API JSON exactly as provided by Tenable.

---

## Features

- Native support for WAS v2 endpoints  
- Simple and predictable module layout  
- Automatic handling of Tenable throttling (`HTTP 429 Too Many Requests`)  
- Retry logic with exponential backoff  
- Detailed API errors with full JSON payloads included  
- Optional proxy support  
- No dependency on Tenable SDKs  

---

## Installation

Install from package source:
