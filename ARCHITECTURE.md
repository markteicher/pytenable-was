```mermaid
flowchart TD
    CLI["pytenable-was CLI<br>(click-based commands)"]
    SDK["SDK Modules<br>scans.py · findings.py · vulns.py · plugins.py · templates.py<br>user_templates.py · notes.py · folders.py · filters.py · users.py"]
    HTTP["HTTP Client<br>auth headers · retries · proxy · throttling"]
    API["Tenable WAS v2 API<br>cloud.tenable.com"]

    CLI --> SDK --> HTTP --> API
