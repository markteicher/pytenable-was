# pytenable_was/cli.py

"""
Command-line interface for the Cadillac Tenable WAS v2 SDK.

Features:
    - argparse with subcommands
    - --verbose and --debug logging modes
    - Scans: list, get, launch, wait, summary
    - Apps: list, get, create, update, delete, urls
    - Findings: list, summary, filter, flatten
    - Pretty JSON output
"""

import argparse
import logging
import sys
from typing import Optional

from .auth import build_headers, load_credentials_from_env
from .http import HTTPClient
from .cache import InMemoryCache
from .utils import pretty_json

from .scans import ScansAPI
from .apps import ApplicationsAPI
from .findings import FindingsAPI


# -------------------------------------------------------------------
# Logging configuration
# -------------------------------------------------------------------

def configure_logging(verbose: bool, debug: bool):
    """
    Configure global logging with verbosity control.
    """
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


# -------------------------------------------------------------------
# HTTP/SDK Initialization
# -------------------------------------------------------------------

def init_sdk(args):
    """
    Load credentials, build HTTP client, initialize API modules.
    """

    # Load creds from environment or other source
    access, secret = load_credentials_from_env()

    headers = build_headers(
        access_key=access,
        secret_key=secret,
        user_agent="pytenable-was-cli/1.0",
    )

    http = HTTPClient(
        base_url="https://cloud.tenable.com",
        headers=headers,
        proxies=None,          # expandable later
        timeout=30,
    )

    cache = InMemoryCache()

    return (
        ScansAPI(http=http, cache=cache),
        ApplicationsAPI(http=http, cache=cache),
        FindingsAPI(http=http, cache=cache),
    )


# -------------------------------------------------------------------
# Command Handlers
# -------------------------------------------------------------------

# ---------- Scans ----------

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


# ---------- Applications ----------

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


# ---------- Findings ----------

def cmd_findings_list(api: FindingsAPI, args):
    fset = api.list_findings(args.scan_id)
    print(pretty_json([f.model_dump() for f in fset.findings]))


def cmd_findings_summary(api: FindingsAPI, args):
    summary = api.summary(args.scan_id)
    print(pretty_json(summary))


def cmd_findings_filter(api: FindingsAPI, args):
    items = api.filter(args.scan_id, severity=args.severity, plugin_id=args.plugin)
    print(pretty_json([f.model_dump() for f in items]))


def cmd_findings_flatten(api: FindingsAPI, args):
    flat = api.flatten(args.scan_id)
    print(pretty_json(flat))


# -------------------------------------------------------------------
# Argument Parser
# -------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pytenable-was",
        description="CLI for the Cadillac Tenable WAS v2 SDK",
    )

    # Global logging options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (very noisy)")

    sub = parser.add_subparsers(dest="command_group")

    # ---------------- Scans ----------------
    scans = sub.add_parser("scans", help="Scan operations")
    scans_sub = scans.add_subparsers(dest="command")

    s_list = scans_sub.add_parser("list", help="List all scans")
    s_list.set_defaults(func=cmd_scans_list)

    s_get = scans_sub.add_parser("get", help="Get a scan")
    s_get.add_argument("scan_id")
    s_get.add_argument("--no-cache", action="store_true")
    s_get.set_defaults(func=cmd_scans_get)

    s_launch = scans_sub.add_parser("launch", help="Launch a scan")
    s_launch.add_argument("scan_id")
    s_launch.set_defaults(func=cmd_scans_launch)

    s_wait = scans_sub.add_parser("wait", help="Wait for scan completion")
    s_wait.add_argument("scan_id")
    s_wait.add_argument("--interval", type=int, default=20, help="Polling interval")
    s_wait.add_argument("--timeout", type=int, default=7200, help="Timeout in seconds")
    s_wait.set_defaults(func=cmd_scans_wait)

    s_summary = scans_sub.add_parser("summary", help="Scan summary")
    s_summary.add_argument("scan_id")
    s_summary.set_defaults(func=cmd_scans_summary)

    # ---------------- Applications ----------------
    apps = sub.add_parser("apps", help="Application operations")
    apps_sub = apps.add_subparsers(dest="command")

    a_list = apps_sub.add_parser("list", help="List applications")
    a_list.set_defaults(func=cmd_apps_list)

    a_get = apps_sub.add_parser("get", help="Get an application")
    a_get.add_argument("app_id")
    a_get.set_defaults(func=cmd_apps_get)

    a_create = apps_sub.add_parser("create", help="Create an application")
    a_create.add_argument("name")
    a_create.add_argument("--description", default="")
    a_create.add_argument("--urls", nargs="*", help="Space-separated URLs")
    a_create.set_defaults(func=cmd_apps_create)

    a_update = apps_sub.add_parser("update", help="Update an application")
    a_update.add_argument("app_id")
    a_update.add_argument("--name")
    a_update.add_argument("--description")
    a_update.set_defaults(func=cmd_apps_update)

    a_delete = apps_sub.add_parser("delete", help="Delete an application")
    a_delete.add_argument("app_id")
    a_delete.set_defaults(func=cmd_apps_delete)

    a_urls = apps_sub.add_parser("urls", help="Manage URLs for an application")
    a_urls.add_argument("app_id")
    a_urls.add_argument("--set", help="Comma-separated URL list")
    a_urls.set_defaults(func=cmd_apps_urls)

    # ---------------- Findings ----------------
    findings = sub.add_parser("findings", help="Findings operations")
    findings_sub = findings.add_subparsers(dest="command")

    f_list = findings_sub.add_parser("list", help="List findings for a scan")
    f_list.add_argument("scan_id")
    f_list.set_defaults(func=cmd_findings_list)

    f_summary = findings_sub.add_parser("summary", help="Findings summary for a scan")
    f_summary.add_argument("scan_id")
    f_summary.set_defaults(func=cmd_findings_summary)

    f_filter = findings_sub.add_parser("filter", help="Filter findings")
    f_filter.add_argument("scan_id")
    f_filter.add_argument("--severity")
    f_filter.add_argument("--plugin")
    f_filter.set_defaults(func=cmd_findings_filter)

    f_flat = findings_sub.add_parser("flatten", help="Flatten findings for export")
    f_flat.add_argument("scan_id")
    f_flat.set_defaults(func=cmd_findings_flatten)

    return parser


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

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

    api_instance = api_map.get(args.command_group)

    if hasattr(args, "func"):
        args.func(api_instance, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
