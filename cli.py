# pytenable_was/cli.py

import argparse
import json
from . import TenableWAS


def pretty(data):
    """Pretty-print JSON output."""
    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Tenable WAS v2 Command Line Interface"
    )

    # ------------------------------------------------------------------
    # GLOBAL AUTH OPTIONS
    # ------------------------------------------------------------------
    parser.add_argument("--access-key", required=True, help="Tenable Access Key")
    parser.add_argument("--secret-key", required=True, help="Tenable Secret Key")
    parser.add_argument("--proxy", help="HTTP/HTTPS proxy (optional)")

    sub = parser.add_subparsers(dest="command")

    # ==================================================================
    # APPLICATION COMMANDS
    # ==================================================================
    apps = sub.add_parser("apps", help="Application operations")
    apps_sub = apps.add_subparsers(dest="apps_cmd")

    apps_sub.add_parser("list", help="List applications")

    get_app = apps_sub.add_parser("get", help="Retrieve an application")
    get_app.add_argument("app_id")

    create_app = apps_sub.add_parser("create", help="Create application")
    create_app.add_argument("json_payload", help="JSON string payload")

    update_app = apps_sub.add_parser("update", help="Update application")
    update_app.add_argument("app_id")
    update_app.add_argument("json_payload")

    delete_app = apps_sub.add_parser("delete", help="Delete application")
    delete_app.add_argument("app_id")

    # URL MANAGEMENT
    urls = apps_sub.add_parser("urls", help="Application URL operations")
    urls.add_argument("app_id")
    urls.add_argument("--add", help="Add URL (JSON payload: {\"url\": \"https://...\"})")
    urls.add_argument("--list", action="store_true", help="List URLs")
    urls.add_argument("--delete", help="Delete URL ID")

    # ==================================================================
    # SCAN COMMANDS
    # ==================================================================
    scans = sub.add_parser("scans", help="Scan operations")
    scans_sub = scans.add_subparsers(dest="scans_cmd")

    scans_sub.add_parser("list", help="List scans")

    get_scan = scans_sub.add_parser("get", help="Get scan details")
    get_scan.add_argument("scan_id")

    launch_scan = scans_sub.add_parser("launch", help="Launch scan")
    launch_scan.add_argument("scan_id")

    launch_wait = scans_sub.add_parser("launch-wait", help="Launch and wait to finish")
    launch_wait.add_argument("scan_id")
    launch_wait.add_argument("--interval", type=int, default=20)
    launch_wait.add_argument("--timeout", type=int, default=7200)

    # ==================================================================
    # FINDINGS COMMANDS
    # ==================================================================
    findings = sub.add_parser("findings", help="Findings operations")
    findings_sub = findings.add_subparsers(dest="find_cmd")

    list_find = findings_sub.add_parser("list", help="List findings for a scan")
    list_find.add_argument("scan_id")

    get_find = findings_sub.add_parser("get", help="Get finding details")
    get_find.add_argument("finding_id")

    # ==================================================================
    # EXECUTION
    # ==================================================================
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    # Prepare WAS client
    proxies = {"http": args.proxy, "https": args.proxy} if args.proxy else None

    was = TenableWAS(
        access_key=args.access_key,
        secret_key=args.secret_key,
        proxies=proxies,
    )

    # ==================================================================
    # APPLICATION HANDLING
    # ==================================================================
    if args.command == "apps":

        # LIST APPLICATIONS
        if args.apps_cmd == "list":
            pretty(was.apps.list_all())
            return

        # GET APPLICATION
        if args.apps_cmd == "get":
            pretty(was.apps.get_application(args.app_id))
            return

        # CREATE APPLICATION
        if args.apps_cmd == "create":
            payload = json.loads(args.json_payload)
            pretty(was.apps.create_application(payload))
            return

        # UPDATE APPLICATION
        if args.apps_cmd == "update":
            payload = json.loads(args.json_payload)
            pretty(was.apps.update_application(args.app_id, payload))
            return

        # DELETE APPLICATION
        if args.apps_cmd == "delete":
            pretty(was.apps.delete_application(args.app_id))
            return

        # URL MANAGEMENT
        if args.apps_cmd == "urls":
            if args.list:
                pretty(was.apps.list_urls(args.app_id))
                return
            if args.add:
                payload = json.loads(args.add)
                pretty(was.apps.add_url(args.app_id, payload))
                return
            if args.delete:
                pretty(was.apps.delete_url(args.app_id, args.delete))
                return

    # ==================================================================
    # SCAN HANDLING
    # ==================================================================
    if args.command == "scans":

        if args.scans_cmd == "list":
            pretty(was.scans.list_all_scans())
            return

        if args.scans_cmd == "get":
            pretty(was.scans.get_scan(args.scan_id))
            return

        if args.scans_cmd == "launch":
            pretty(was.scans.launch_scan(args.scan_id))
            return

        if args.scans_cmd == "launch-wait":
            result = was.scans.launch_and_wait(
                args.scan_id,
                poll_interval=args.interval,
                timeout=args.timeout
            )
            pretty(result)
            return

    # ==================================================================
    # FINDINGS HANDLING
    # ==================================================================
    if args.command == "findings":

        if args.find_cmd == "list":
            findings = was.findings.list_all(args.scan_id)
            pretty(findings)
            return

        if args.find_cmd == "get":
            pretty(was.findings.get_finding(args.finding_id))
            return
