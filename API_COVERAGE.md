# WAS v2 Coverage Matrix

| WAS Endpoint                                         | Implemented In         | SDK Method(s)                          | CLI Command(s)                                   | Status |
|---------------------------------------------------------|-------------------------|-----------------------------------------|--------------------------------------------------|--------|
| **Scans**                                               | `scans.py`              | `list_scans`, `get_scan`                | `scans list`, `scans details`                    | ✔ Full |
| GET /was/v2/scans                                       |                         |                                         |                                                  |        |
| GET /was/v2/scans/{scan_id}                            |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **Findings**                                            | `findings.py`           | `list_findings`, `get_finding`, `flatten` | `findings export`                               | ✔ Full |
| GET /was/v2/scans/{scan_id}/findings                   |                         |                                         |                                                  |        |
| GET /was/v2/scans/{scan_id}/findings/{finding_id}      |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **Vulnerabilities**                                     | `vulns.py`              | `search`, `details`, `flatten_single`, `flatten_multi` | `vulns search`, `vulns details`, `vulns export`, `vulns export-all` | ✔ Full |
| POST /was/v2/vulns/search                              |                         |                                         |                                                  |        |
| GET /was/v2/vulns/{vuln_id}                             |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **Plugins**                                             | `plugins.py`            | `list_plugins`, `get_plugin`, `flatten_all` | `plugins list`, `plugins get`, `plugins export`, `plugins export-all` | ✔ Full |
| GET /was/v2/plugins                                    |                         |                                         |                                                  |        |
| GET /was/v2/plugins/{plugin_id}                        |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **Templates (Tenable-provided)**                        | `templates.py`          | `list_all`, `get_template`              | `templates list`                                 | ✔ Full |
| GET /was/v2/templates                                   |                         |                                         |                                                  |        |
| GET /was/v2/templates/{template_id}                    |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **User Templates**                                      | `user_templates.py`     | `list_user_templates`, `get_user_template` | `user-templates list`                         | ✔ Full |
| GET /was/v2/user-templates                             |                         |                                         |                                                  |        |
| GET /was/v2/user-templates/{uuid}                      |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **Folders**                                             | `folders.py`            | `list_folders`                          | `folders list`                                   | ✔ Full |
| GET /was/v2/folders                                    |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **Filters**                                             | `filters.py`            | `scan_configs`, `scans`, `user_templates`, `vulns`, `vulns_scan` | `filters scan-configs`, etc. | ✔ Full |
| GET /was/v2/filters/scan-configs                       |                         |                                         |                                                  |        |
| GET /was/v2/filters/scans                               |                         |                                         |                                                  |        |
| GET /was/v2/filters/user-templates                     |                         |                                         |                                                  |        |
| GET /was/v2/filters/vulns                              |                         |                                         |                                                  |        |
| GET /was/v2/filters/vulns-scan                         |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **Users**                                               | `users.py`              | `fetch_all_users`, `fetch_user_details`, `enrich_scan_owner` | `users list`                        | ✔ Full |
| GET /users                                             |                         |                                         |                                                  |        |
| GET /users/{id}                                        |                         |                                         |                                                  |        |
|                                                         |                         |                                         |                                                  |        |
| **Config**                                              | `config.py`             | key/proxy storage, masking, reset       | `config get/set/clear/reset`                     | ✔ Full |
|                                                         |                         |                                         |                                                  |        |
| **HTTP Core**                                           | `http.py`               | authenticated requests + retry           | Used implicitly by all commands                  | ✔ Full |
