# pytenable-was

A modular Python client for the Tenable Web Application Scanning (WAS) v2 API.  
This package implements a clean, reliable set of endpoint wrappers for interacting with WAS scans, applications, and findings using AccessKey/SecretKey authentication.  


# *** This tool is not an officially supported by Tenable ***

*** Use of this tool is subject to the terms and conditions identified below,
 and is not subject to any license agreement you may have with Tenable ***

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



## Features

- Native support for WAS v2 endpoints  
- Simple and predictable module layout  
- Automatic handling of Tenable throttling (`HTTP 429 Too Many Requests`)  
- Retry logic with exponential backoff  
- Detailed API errors with full JSON payloads included  
- Optional proxy support  
- No dependency on Tenable SDKs  

##Error Handling

Custom exceptions include:

- APIError
- Throttle Error
- Connection Error
- Timeout Error
- Model Validation Error
- Scan Wait Error
- Not Found Error
- Cache Key Error

All exceptions include:

- HTTP status codes
- Request URL
- Raw response messages
- Parsed JSON
  
## Requirements

- Python 3.8 
- requests
- pydantic v2
