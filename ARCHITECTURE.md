flowchart TD

%% ====================
%% Local Environment
%% ====================
    subgraph LocalEnvironment["Local Environment"]
        CLI["pytenable-was CLI
(click-based command interface)"]

        SDKModules["SDK Modules
• scans.py
• findings.py
• vulns.py
• plugins.py
• templates.py
• user_templates.py
• notes.py
• folders.py
• filters.py
• users.py
• utils.py
• auth.py
• errors.py"]
    end

%% ====================
%% HTTP Layer
%% ====================
    subgraph HTTP["HTTP Layer"]
        HTTPClient["HTTP Client
• Authentication Headers
• Retries / Backoff for 429
• Proxy Support
• Timeout Control
• JSON Handling
• Error Wrapping"]
    end

%% ====================
%% Tenable Cloud
%% ====================
    subgraph TenableCloud["Tenable Cloud"]
        WASAPI["Tenable WAS v2 API
• Scans
• Scan Details
• Findings
• Vulnerabilities
• Plugins
• Templates & User Templates
• Notes
• Folders
• Filters
• Owners / Users
• Bulk Export APIs"]
    end

%% FLOW
    CLI --> SDKModules --> HTTPClient --> WASAPI
