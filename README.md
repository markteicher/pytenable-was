# pytenable-was
pytenable-was

A modular Python client for Tenable Web Application Scanning (WAS) v2, built for real-world automation, API exploration, and integration pipelines.
This package wraps the official WAS v2 API with clean, testable modules, predictable error handling, and a simple command-line interface.

The goal is reliability and clarity: a small set of Python modules that behave exactly like the WAS v2 specification—nothing hidden, nothing invented.

⸻

Features
	•	Direct support for the Tenable WAS v2 API
	•	Clear Python modules for scans, applications, findings, and HTTP transport
	•	Built-in retry + throttling handling (e.g., Tenable’s common 429 responses)
	•	Simple authentication using Access Key + Secret Key
	•	Optional proxy support
	•	CLI utility (pytenable-was) for quick testing or scripting
	•	Clean exceptions and stable method signatures
	•	No external Tenable SDK dependencies

The package keeps close to the API surface so your automation isn’t trapped behind abstractions.
