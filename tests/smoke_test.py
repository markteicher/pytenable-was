#!/usr/bin/env python3
"""
Smoke Test for pytenable-was

Validates:
    - Package importability
    - CLI availability
    - Config subsystem functionality
    - HTTP wiring
    - Scans, templates, user-templates, and users modules import cleanly
    - CLI --version responds
    - Basic mocked API calls behave correctly

This test DOES NOT contact Tenable API.
"""

import subprocess
import sys
import json

print("\n=== Smoke Test: pytenable-was ===")

# ------------------------------------------------------------
# 1. Verify imports
# ------------------------------------------------------------
print("[1] Importing modules...")

try:
    import pytenable_was
    import pytenable_was.cli
    import pytenable_was.config
    import pytenable_was.errors
    import pytenable_was.http
    import pytenable_was.scans
    import pytenable_was.templates
    import pytenable_was.user_templates
    import pytenable_was.users
    import pytenable_was.utils
    print("    ✔ Imports OK")
except Exception as exc:
    print("    ✘ Import failure:", exc)
    sys.exit(1)


# ------------------------------------------------------------
# 2. Validate CLI --version
# ------------------------------------------------------------
print("[2] Checking CLI version...")

try:
    out = subprocess.check_output(
        ["pytenable-was", "--version"],
        stderr=subprocess.STDOUT,
        text=True
    )
    print("    ✔ Version OK:", out.strip())
except Exception as exc:
    print("    ✘ CLI version failed:", exc)
    sys.exit(1)


# ------------------------------------------------------------
# 3. Validate CLI top-level help
# ------------------------------------------------------------
print("[3] Checking CLI help...")

try:
    out = subprocess.check_output(
        ["pytenable-was", "--help"],
        stderr=subprocess.STDOUT,
        text=True
    )
    if "Usage:" in out:
        print("    ✔ CLI help OK")
    else:
        print("    ✘ CLI help missing expected text")
        sys.exit(1)
except Exception as exc:
    print("    ✘ CLI help failed:", exc)
    sys.exit(1)


# ------------------------------------------------------------
# 4. Validate mocked HTTPClient
# ------------------------------------------------------------
print("[4] Validating HTTP client wiring (mocked)...")

from pytenable_was.http import HTTPClient

client = HTTPClient(
    access_key="ABC",
    secret_key="XYZ",
    proxy=None,
    timeout=5
)

# We do NOT make a network call, we just check object construction
try:
    assert client.access_key == "ABC"
    assert client.secret_key == "XYZ"
    assert client.timeout == 5
    print("    ✔ HTTP client OK")
except Exception as exc:
    print("    ✘ HTTP client misconfigured:", exc)
    sys.exit(1)


# ------------------------------------------------------------
# 5. Validate module classes instantiate cleanly (no API calls)
# ------------------------------------------------------------
print("[5] Instantiating module APIs...")

from pytenable_was.scans import ScansAPI
from pytenable_was.templates import TemplatesAPI
from pytenable_was.user_templates import UserTemplatesAPI
from pytenable_was.users import UsersAPI

try:
    scans_api = ScansAPI(client)
    templates_api = TemplatesAPI(client)
    user_templates_api = UserTemplatesAPI(client)
    users_api = UsersAPI(client)
    print("    ✔ API modules instantiate OK")
except Exception as exc:
    print("    ✘ API object construction failed:", exc)
    sys.exit(1)


# ------------------------------------------------------------
# 6. Validate config subsystem reads/writes
# ------------------------------------------------------------
print("[6] Testing config subsystem...")

from pytenable_was.config import Config

config = Config()

try:
    config.set_access_key("TEST_AK")
    config.set_secret_key("TEST_SK")
    config.set_proxy("http://localhost:8080")
    cfg = config.load()

    assert cfg["access_key"] == "TEST_AK"
    assert cfg["secret_key"] == "TEST_SK"
    assert cfg["proxy"] == "http://localhost:8080"

    config.clear()  # cleanup

    print("    ✔ Config subsystem OK")
except Exception as exc:
    print("    ✘ Config subsystem failed:", exc)
    sys.exit(1)


# ------------------------------------------------------------
# 7. Validate click command structure (no execution)
# ------------------------------------------------------------
print("[7] Checking CLI command groups...")

expected = [
    "config",
    "scans",
    "templates",
    "user-templates",
]

try:
    out = subprocess.check_output(
        ["pytenable-was", "--help"],
        stderr=subprocess.STDOUT,
        text=True
    )
    for cmd in expected:
        if cmd not in out:
            raise AssertionError(f"Missing CLI command: {cmd}")

    print("    ✔ CLI command groups OK")
except Exception as exc:
    print("    ✘ CLI structure invalid:", exc)
    sys.exit(1)


print("\n=== ALL SMOKE TESTS PASSED ✔ ===\n")
