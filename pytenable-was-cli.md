flowchart TD
    A[Start] --> B[Parse arguments]
    B --> C{Valid args}
    C -- No --> C1[Print usage] --> X2[Exit 2]
    C -- Yes --> D[Set log level and output settings]

    D --> E[Pre-flight checks]
    E --> E1{ssh present and supports options}
    E1 -- No --> X2
    E1 -- Yes --> E2{Not running with set -x}
    E2 -- No --> X2
    E2 -- Yes --> E3{Output path writable}
    E3 -- No --> X2
    E3 -- Yes --> F[Load targets]

    F --> G[Validate targets]
    G --> G1[Malformed targets recorded as INDETERMINATE]
    G --> H{DNS precheck enabled}

    H -- Yes --> H1[Resolve hostnames]
    H1 --> H2[DNS failures recorded as INDETERMINATE]
    H -- No --> I[Deduplicate targets]
    H2 --> I

    I --> I1[Duplicates recorded as DUPLICATE_SKIPPED]
    I1 --> J{Any valid targets}

    J -- No --> N[Write output]
    J -- Yes --> L[Evaluate target via SSH]

    L --> M{SSH reachable}
    M -- No --> M1[INDETERMINATE SSH failure] --> L
    M -- Yes --> V[get system status]

    V --> V1{Version parsed}
    V1 -- No --> V2[INDETERMINATE version unknown] --> L
    V1 -- Yes --> W[Extract FortiOS version]

    W --> Y{Version vulnerable}
    Y -- No --> Y1[NOT_VULNERABLE] --> L
    Y -- Yes --> Z[show system global]

    Z --> AA{admin-https enabled}
    AA -- No --> AA1[NOT_VULNERABLE] --> L
    AA -- Yes --> AB[VULNERABLE] --> L

    L --> N[Write output]

    N --> O[Exit decision]
    O --> O1{Any vulnerable}
    O1 -- Yes --> X1[Exit 1]
    O1 -- No --> O2{Any not vulnerable}
    O2 -- Yes --> X0[Exit 0]
    O2 -- No --> X3[Exit 3]
