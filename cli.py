# pytenable_was/cli.py

"""
CLI for Tenable WAS v2 SDK
Now supports:
    - CLI flags for access key, secret key, proxy
    - Environment variable fallback
    - Secure interactive prompts when missing
    - Verbose / debug logging
"""

import argparse
import getpass
import logging
import os
import sys
from typing import Optional

from .auth import build_headers
from .http import HTTPClient
from .cache import InMemoryCache
from .utils import pretty_json

from .scans import ScansAPI
from .apps import ApplicationsAPI
from .findings import FindingsAPI


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

def configure_logging(verbose: bool, debug: bool):
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


# ----------------------------------------------------------------------
# Credential + Proxy Resolution (Option C)
# ----------------------------------------------------------------------

def resolve_credentials(args):
    """
    Cadillac credential precedence:
        1. CLI flags
        2. Environment vars
        3. Interactive prompt
    """

    # 1️⃣ CLI flags
    access = args.access_key
    secret = args.secret_key
    proxy = args.proxy

    # 2️⃣ Environment variables
    if not access:
        access = os.getenv("TENABLE_ACCESS_KEY")

    if not secret:
        secret = os.getenv("TENABLE_SECRET_KEY")

    if not proxy:
        proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

    # 3️⃣ Interactive prompt
    if not access:
        access = getpass.getpass("Enter Tenable Access Key: ").strip()

    if not secret:
        secret = getpass.getpass("Enter Tenable Secret Key: ").strip()

    if not proxy:
        p = input("Proxy (optional): ").strip()
        proxy = p if p else None

    return access, secret, proxy


# ----------------------------------------------------------------------
# HTTP + SDK initialization
# ----------------------------------------------------------------------

def init_sdk(args):
    access, secret, proxy = resolve_credentials(args)

    headers = build_headers(
        access_key=access,
        secret_key=secret,
        user_agent="pytenable-was-cli/1.0",
    )

    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy,
        }

    http = HTTPClient(
        base_url="https://cloud.tenable.com",
        headers=headers,
        proxies=proxies,
        timeout=30,
    )

    cache = InMemoryCache()

    return (
        ScansAPI(http=http, cache=cache),
        ApplicationsAPI(http=http, cache=cache),
        FindingsAPI(http=http, cache=cache),
    )


# ----------------------------------------------------------------------
# Scan / App / Finding command handlers
# (Same as previous version — omitted here for space)
# ----------------------------------------------------------------------

# [handlers remain unchanged, using pretty_json() etc.]
# I can include them again verbatim if you want.


# ----------------------------------------------------------------------
# Argument parser
# ----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pytenable-was",
        description="Cadillac CLI for Tenable WAS v2 SDK",
    )

    # Global logging flags
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--debug", action="store_true")

    # NEW: Credential flags
    parser.add_argument("--access-key", help="Tenable Access Key")
    parser.add_argument("--secret-key", help="Tenable Secret Key")

    # NEW: Proxy flag
    parser.add_argument("--proxy", help="Proxy URL (e.g., http://proxy:8080)")

    sub = parser.add_subparsers(dest="command_group")

    # ---------------- Scans ----------------
    scans = sub.add_parser("scans", help="Scan operations")
    scans_sub = scans.add_subparsers(dest="command")

    s_list = scans_sub.add_parser("list", help="List scans")
    s_list.set_defaults(func=cmd_scans_list)

    s_get = scans_sub.add_parser("get", help="Get scan")
    s_get.add_argument("scan_id")
    s_get.add_argument("--no-cache", action="store_true")
    s_get.set_defaults(func=cmd_scans_get)

    s_launch = scans_sub.add_parser("launch", help="Launch scan")
    s_launch.add_argument("scan_id")
    s_launch.set_defaults(func=cmd_scans_launch)

    s_wait = scans_sub.add_parser("wait", help="Wait for scan to finish")
    s_wait.add_argument("scan_id")
    s_wait.add_argument("--interval", type=int, default=20)
    s_wait.add_argument("--timeout", type=int, default=7200)
    s_wait.set_defaults(func=cmd_scans_wait)

    s_summary = scans_sub.add_parser("summary", help="Scan summary")
    s_summary.add_argument("scan_id")
    s_summary.set_defaults(func=cmd_scans_summary)

    # ---------------- Apps ----------------
    apps = sub.add_parser("apps", help="Application ops")
    apps_sub = apps.add_subparsers(dest="command")

    a_list = apps_sub.add_parser("list")
    a_list.set_defaults(func=cmd_apps_list)

    a_get = apps_sub.add_parser("get")
    a_get.add_argument("app_id")
    a_get.set_defaults(func=cmd_apps_get)

    # (Rest unchanged, omitted for brevity)

    # ---------------- Findings ----------------
    # (Same as above, omitted for brevity)

    return parser


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def main(argv: Optional[list] = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.verbose, args.debug)

    if not args.command_group:
        parser.print_help()
        return

    scans_api, apps_api, findings_api = init_sdk(args)
    api_map = {
        "scans": scans_api,
        "apps": apps_api,
        "findings": findings_api,
    }

    instance = api_map.get(args.command_group)

    if hasattr(args, "func"):
        args.func(instance, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
