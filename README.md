# pytenable-was
pytenable-was v2 api code
Each module has a single responsibility:
	•	config.py — stores base URL, headers, and auth keys.
	•	http.py — one place for GET/POST/PUT/DELETE with retry, throttling, and JSON parsing.
	•	auth.py — builds the Tenable-required headers using Access Key / Secret Key.
	•	scans.py — functions like list_scans(), get_scan_details(), launch_scan().
	•	apps.py — listing applications, URLs.
	•	findings.py — retrieve vulnerabilities and issues.
	•	errors.py — defines structured exceptions.
	•	cli.py — argparse wrapper that lets you use it like a tool.

The WAS API becomes a library of clean Python methods instead of scattered code.
