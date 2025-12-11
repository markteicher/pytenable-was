## PyTenable-WAS SDK+CLI Application Flowhart

```mermaid
flowchart TD

    subgraph CLI["pytenable-was CLI"]
        C1[scans] -->|calls| SAPI
        C2[findings] -->|calls| FAPI
        C3[vulns] -->|calls| VAPI
        C4[plugins] -->|calls| PAPI
        C5[templates] -->|calls| TAPI
        C6[user-templates] -->|calls| UTAPI
        C7[folders] -->|calls| FOAPI
        C8[filters] -->|calls| FIAPI
        C9[users] -->|calls| UAPI
    end

    subgraph SDK["pytenable_was SDK Modules"]
        SAPI[scans.py]
        FAPI[findings.py]
        VAPI[vulns.py]
        PAPI[plugins.py]
        TAPI[templates.py]
        UTAPI[user_templates.py]
        FOAPI[folders.py]
        FIAPI[filters.py]
        UAPI[users.py]
        CONFIG[config.py]
        CACHE[cache.py]
    end

    subgraph CORE["Core Utilities"]
        HTTP[http.py<br/>Authenticated HTTP Client<br/>Retries + Throttling]
        UTILS[utils.py]
        ERR[errors.py]
    end

    subgraph WASAPI["Tenable WAS v2 API"]
        WAS1[/Scans<br/>GET/POST/DETAILS/…/]
        WAS2[/Findings/]
        WAS3[/Vulns/]
        WAS4[/Plugins/]
        WAS5[/Templates/]
        WAS6[/User Templates/]
        WAS7[/Filters/]
        WAS8[/Folders/]
        WAS9[/Users/]
    end

    %% Wiring
    C1 --> SAPI --> HTTP --> WAS1
    C2 --> FAPI --> HTTP --> WAS2
    C3 --> VAPI --> HTTP --> WAS3
    C4 --> PAPI --> HTTP --> WAS4
    C5 --> TAPI --> HTTP --> WAS5
    C6 --> UTAPI --> HTTP --> WAS6
    C7 --> FOAPI --> HTTP --> WAS8
    C8 --> FIAPI --> HTTP --> WAS7
    C9 --> UAPI --> HTTP --> WAS9

    %% Shared utilities
    SAPI --> CACHE
    FAPI --> CACHE
    VAPI --> CACHE
    PAPI --> CACHE
    TAPI --> CACHE
    UTAPI --> CACHE

    SAPI --> UTILS
    FAPI --> UTILS
    VAPI --> UTILS
    PAPI --> UTILS
    UTAPI --> UTILS
    UAPI --> UTILS
