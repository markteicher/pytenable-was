# pytenable_was/cli.py

"""
Cadillac CLI for the Tenable WAS v2 SDK
Supports:
    - CLI credential flags
    - Environment variable fallback
    - Interactive prompting (Option C)
    - Verbose/debug logging
    - Scans: list/get/launch/wait/summary
    - Apps: full CRUD + URL management
    - Findings: list/summary/filter/flatten
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
# Credential + Proxy Resolution (Cadillac Option C)
# ----------------------------------------------------------------------

def resolve_credentials(args):
    """
    Cadillac precedence:
      1. CLI flags
      2. Environment variables
      3. Interactive input
    """

    # 1️⃣ CLI flags
    access = args.access_key
    secret = args.secret_key
    proxy = args.proxy

    # 2️⃣ Environment
    if not access:
        access = os.getenv("TENABLE_ACCESS_KEY")

    if not secret:
        secret = os.getenv("TENABLE_SECRET_KEY")

    if not proxy:
        proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

    # 3️⃣ PROMPT USER
    if not access:
        access = getpass.getpass("Enter Tenable Access Key: ").strip()

    if not secret:
        secret = getpass.getpass("Enter Tenable Secret Key: ").strip()

    if not proxy:
        p = input("Proxy (optional): ").strip()
        proxy = p if p else None

    return access, secret, proxy


# ----------------------------------------------------------------------
# Initialize HTTP + SDK modules
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
        proxies = {"http": proxy, "https": proxy}

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
# Command Handlers (FULL — NOTHING OMITTED)
# ----------------------------------------------------------------------

# ----- Scans -----

def cmd_scans_list(api: ScansAPI, args):
    scans = api.list_all()
    print(pretty_json([s.model_dump() for s in scans]))

def cmd_scans_get(api: ScansAPI, args):
    scan = api.get_scan(args.scan_id, use_cache=not args.no_cache)
    print(pretty_json(scan.model_dump()))

def cmd_scans_launch(api: ScansAPI, args):
    api.launch_scan(args.scan_id)
    print(f"Scan {args.scan_id} launched.")

def cmd_scans_wait(api: ScansAPI, args):
    scan = api.wait_until_complete(
        args.scan_id,
        interval=args.interval,
        timeout=args.timeout,
    )
    print(pretty_json(scan.model_dump()))

def cmd_scans_summary(api: ScansAPI, args):
    summary = api.summary(args.scan_id)
    print(pretty_json(summary.model_dump()))


# ----- Applications -----

def cmd_apps_list(api: ApplicationsAPI, args):
    apps = api.list_all()
    print(pretty_json([a.model_dump() for a in apps]))

def cmd_apps_get(api: ApplicationsAPI, args):
    app = api.get_app(args.app_id)
    print(pretty_json(app.model_dump()))

def cmd_apps_create(api: ApplicationsAPI, args):
    app = api.create_app(args.name, args.description, args.urls)
    print(pretty_json(app.model_dump()))

def cmd_apps_update(api: ApplicationsAPI, args):
    app = api.update_app(args.app_id, args.name, args.description)
    print(pretty_json(app.model_dump()))

def cmd_apps_delete(api: ApplicationsAPI, args):
    api.delete_app(args.app_id)
    print(f"Deleted application {args.app_id}")

def cmd_apps_urls(api: ApplicationsAPI, args):
    if args.set:
        urls = args.set.split(",")
        models = api.set_urls(args.app_id, urls)
        print(pretty_json([u.model_dump() for u in models]))
    else:
        urls = api.list_urls(args.app_id)
        print(pretty_json([u.model_dump() for u in urls]))


# ----- Findings -----  ⭐ THIS SECTION WAS PREVIOUSLY COLLAPSED — NOW FULL

def cmd_findings_list(api: FindingsAPI, args):
    fset = api.list_findings(args.scan_id)
    print(pretty_json([f.model_dump() for f in fset.findings]))

def cmd_findings_summary(api: FindingsAPI, args):
    summary = api.summary(args.scan_id)
    print(pretty_json(summary))

def cmd_findings_filter(api: FindingsAPI, args):
    items = api.filter(
        args.scan_id,
        severity=args.severity,
        plugin_id=args.plugin,
    )
    print(pretty_json([f.model_dump() for f in items]))

def cmd_findings_flatten(api: FindingsAPI, args):
    flat = api.flatten(args.scan_id)
    print(pretty_json(flat))


# ----------------------------------------------------------------------
# Argument Parser (FULL)
# ----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pytenable-was",
        description="Cadillac CLI for Tenable WAS v2 SDK",
    )

    # Logging/verbosity flags
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--debug", action="store_true")

    # Credential flags
    parser.add_argument("--access-key", help="Tenable Access Key")
    parser.add_argument("--secret-key", help="Tenable Secret Key")
    parser.add_argument("--proxy", help="Proxy (http://proxy:8080)")

    sub = parser.add_subparsers(dest="command_group")

    # ---------------- Scans ----------------
    scans = sub.add_parser("scans", help="Scan operations")
    scans_sub = scans.add_subparsers(dest="command")

    s_list = scans_sub.add_parser("list")
    s_list.set_defaults(func=cmd_scans_list)

    s_get = scans_sub.add_parser("get")
    s_get.add_argument("scan_id")
    s_get.add_argument("--no-cache", action="store_true")
    s_get.set_defaults(func=cmd_scans_get)

    s_launch = scans_sub.add_parser("launch")
    s_launch.add_argument("scan_id")
    s_launch.set_defaults(func=cmd_scans_launch)

    s_wait = scans_sub.add_parser("wait")
    s_wait.add_argument("scan_id")
    s_wait.add_argument("--interval", type=int, default=20)
    s_wait.add_argument("--timeout", type=int, default=7200)
    s_wait.set_defaults(func=cmd_scans_wait)

    s_summary = scans_sub.add_parser("summary")
    s_summary.add_argument("scan_id")
    s_summary.set_defaults(func=cmd_scans_summary)

    # ---------------- Applications ----------------
    apps = sub.add_parser("apps")
    apps_sub = apps.add_subparsers(dest="command")

    a_list = apps_sub.add_parser("list")
    a_list.set_defaults(func=cmd_apps_list)

    a_get = apps_sub.add_parser("get")
    a_get.add_argument("app_id")
    a_get.set_defaults(func=cmd_apps_get)

    a_create = apps_sub.add_parser("create")
    a_create.add_argument("name")
    a_create.add_argument("--description", default="")
    a_create.add_argument("--urls", nargs="*")
    a_create.set_defaults(func=cmd_apps_create)

    a_update = apps_sub.add_parser("update")
    a_update.add_argument("app_id")
    a_update.add_argument("--name")
    a_update.add_argument("--description")
    a_update.set_defaults(func=cmd_apps_update)

    a_delete = apps_sub.add_parser("delete")
    a_delete.add_argument("app_id")
    a_delete.set_defaults(func=cmd_apps_delete)

    a_urls = apps_sub.add_parser("urls")
    a_urls.add_argument("app_id")
    a_urls.add_argument("--set")
    a_urls.set_defaults(func=cmd_apps_urls)

    # ---------------- Findings ----------------
    findings = sub.add_parser("findings", help="Findings operations")
    findings_sub = findings.add_subparsers(dest="command")

    f_list = findings_sub.add_parser("list")
    f_list.add_argument("scan_id")
    f_list.set_defaults(func=cmd_findings_list)

    f_summary = findings_sub.add_parser("summary")
    f_summary.add_argument("scan_id")
    f_summary.set_defaults(func=cmd_findings_summary)

    f_filter = findings_sub.add_parser("filter")
    f_filter.add_argument("scan_id")
    f_filter.add_argument("--severity")
    f_filter.add_argument("--plugin")
    f_filter.set_defaults(func=cmd_findings_filter)

    f_flatten = findings_sub.add_parser("flatten")
    f_flatten.add_argument("scan_id")
    f_flatten.set_defaults(func=cmd_findings_flatten)

    return parser


# ----------------------------------------------------------------------
# Entry Point
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
