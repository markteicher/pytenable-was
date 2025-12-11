# pytenable_was/cli.py

"""
Command-line interface for pytenable-was.

Exposes high-level operations for:
    - configuration (API keys, proxy)
    - scans (list, details, owner change)
    - findings (single export, export-all)
    - vulnerabilities (search, get, export-all)
    - templates (Tenable-provided)
    - user templates
    - plugins
    - folders
    - filters
    - notes

The heavy lifting is done by the API modules; the CLI is a thin,
user-friendly wrapper around them.
"""

import sys
from pathlib import Path
from typing import List, Optional

import click

from .config import Config
from .http import HTTPClient
from .scans import ScansAPI
from .findings import FindingsAPI
from .vulns import VulnsAPI
from .templates import TemplatesAPI
from .user_templates import UserTemplatesAPI
from .plugins import PluginsAPI
from .notes import NotesAPI
from .folders import FoldersAPI
from .filters import FiltersAPI

from .utils import (
    pretty_json,
    write_csv_safe,
    write_json_safe,
    timestamp_filename,
)


CLI_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Helper: HTTP Client from Config
# ---------------------------------------------------------------------------

def _load_http_from_config() -> HTTPClient:
    cfg = Config().load()
    access_key = cfg.get("access_key")
    secret_key = cfg.get("secret_key")
    proxy = cfg.get("proxy")

    if not access_key or not secret_key:
        raise click.ClickException(
            "API keys not configured. Run: pytenable-was config set"
        )

    return HTTPClient(
        access_key=access_key,
        secret_key=secret_key,
        proxy=proxy,
        timeout=30,
    )


def _parse_ids_arg(ids: str) -> List[str]:
    """
    Parse comma-separated IDs like 'id1,id2,id3'.
    """
    return [s.strip() for s in ids.split(",") if s.strip()]


def _load_ids_from_file(path: str) -> List[str]:
    """
    Load scan IDs from a newline-delimited text file.
    """
    p = Path(path)
    if not p.exists():
        raise click.ClickException(f"File not found: {path}")

    ids: List[str] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                ids.append(line)
    return ids


# ---------------------------------------------------------------------------
# Root CLI
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version=CLI_VERSION, prog_name="pytenable-was")
def cli():
    """Tenable Web Application Scanning (WAS) v2 SDK + CLI."""
    pass


# ---------------------------------------------------------------------------
# CONFIG COMMANDS
# ---------------------------------------------------------------------------

@cli.group()
def config():
    """Configure API keys & proxy."""
    pass


@config.command("set")
@click.option("--access-key", required=True, help="Tenable Access Key")
@click.option("--secret-key", required=True, help="Tenable Secret Key")
@click.option("--proxy", default=None, help="Optional HTTP/HTTPS proxy")
def config_set(access_key, secret_key, proxy):
    """Set API keys and optional proxy."""
    cfg = Config()
    cfg.set_access_key(access_key)
    cfg.set_secret_key(secret_key)

    if proxy:
        cfg.set_proxy(proxy)

    click.echo("Configuration saved.")


@config.command("get")
def config_get():
    """Show current configuration (keys masked)."""
    cfg = Config().load()
    click.echo(pretty_json(cfg))


@config.command("clear")
def config_clear():
    """Clear stored configuration."""
    Config().clear()
    click.echo("Configuration cleared.")


@config.command("reset")
def config_reset():
    """Reset configuration with confirmation."""
    if click.confirm("Reset all configuration?"):
        Config().clear()
        click.echo("Configuration reset.")
    else:
        click.echo("Cancelled.")


# ---------------------------------------------------------------------------
# SCANS
# ---------------------------------------------------------------------------

@cli.group()
def scans():
    """Manage WAS scans."""
    pass


@scans.command("list")
def scans_list():
    """List all scans."""
    http = _load_http_from_config()
    api = ScansAPI(http)

    scans = api.list_scans()
    for s in scans:
        scan_id = s.get("scan_id") or s.get("id")
        name = s.get("name") or ""
        status = s.get("status") or ""
        click.echo(f"{scan_id}\t{status}\t{name}")


@scans.command("details")
@click.argument("scan_id")
def scans_details(scan_id):
    """Show details for a scan."""
    http = _load_http_from_config()
    api = ScansAPI(http)

    details = api.get_scan(scan_id)
    click.echo(pretty_json(details))


@scans.command("set-owner")
@click.argument("scan_id")
@click.option("--user-id", required=True, help="New owner user_id")
def scans_set_owner(scan_id, user_id):
    """
    Change owner of a single scan.
    """
    http = _load_http_from_config()
    api = ScansAPI(http)

    resp = api.change_owner(scan_id, user_id)
    click.echo(f"Scan {scan_id} owner updated to {user_id}.")
    click.echo(pretty_json(resp))


@scans.command("set-owner-bulk")
@click.argument("scan_ids", required=False)
@click.option("--from-file", "ids_file", help="File containing scan IDs, one per line")
@click.option("--user-id", required=True, help="New owner user_id")
def scans_set_owner_bulk(scan_ids, ids_file, user_id):
    """
    Change owner for many scans.

    Either:
        scans set-owner-bulk 101,102,103 --user-id X
    Or:
        scans set-owner-bulk --from-file ids.txt --user-id X
    """
    if scan_ids and ids_file:
        raise click.ClickException("Use either scan_ids OR --from-file, not both.")
    if not scan_ids and not ids_file:
        raise click.ClickException("Provide scan_ids or --from-file.")

    if scan_ids:
        ids = _parse_ids_arg(scan_ids)
    else:
        ids = _load_ids_from_file(ids_file)

    if not ids:
        raise click.ClickException("No scan IDs provided.")

    http = _load_http_from_config()
    api = ScansAPI(http)

    results = api.change_owner_bulk(ids, user_id)
    click.echo(f"Updated owner to {user_id} for {len(results)} scans.")


# ---------------------------------------------------------------------------
# FINDINGS
# ---------------------------------------------------------------------------

@cli.group()
def findings():
    """Export WAS findings."""
    pass


@findings.command("export")
@click.argument("scan_id")
@click.option("--json-out", help='JSON output path or "auto" for auto filename')
@click.option("--csv-out", help='CSV output path or "auto" for auto filename')
def findings_export(scan_id, json_out, csv_out):
    """
    Export full findings for a single scan via /export/findings.
    """
    if not json_out and not csv_out:
        # default: CSV auto filename
        json_out = None
        csv_out = "auto"

    http = _load_http_from_config()
    scans_api = ScansAPI(http)
    api = FindingsAPI(http=http, scans_api=scans_api)

    if json_out:
        path = None if json_out == "auto" else json_out
        out = api.export_findings_json(scan_id, path)
        click.echo(f"Findings JSON written: {out}")

    if csv_out:
        path = None if csv_out == "auto" else csv_out
        out = api.export_findings_csv(scan_id, path)
        click.echo(f"Findings CSV written: {out}")


@findings.command("export-all")
@click.option("--json-out", help='JSON output path or "auto" for auto filename')
@click.option("--csv-out", help='CSV output path or "auto" for auto filename')
def findings_export_all(json_out, csv_out):
    """
    Export ALL findings across ALL scans.
    """
    if not json_out and not csv_out:
        # default: CSV auto filename
        csv_out = "auto"

    http = _load_http_from_config()
    scans_api = ScansAPI(http)
    api = FindingsAPI(http=http, scans_api=scans_api)

    if json_out:
        path = None if json_out == "auto" else json_out
        out = api.export_all_findings_json(path)
        click.echo(f"All findings JSON written: {out}")

    if csv_out:
        path = None if csv_out == "auto" else csv_out
        out = api.export_all_findings_csv(path)
        click.echo(f"All findings CSV written: {out}")


# ---------------------------------------------------------------------------
# VULNERABILITIES
# ---------------------------------------------------------------------------

@cli.group()
def vulns():
    """WAS vulnerability search & export."""
    pass


@vulns.command("search")
@click.option("--query", default="*", help="Vuln search query (default: *)")
def vulns_search(query):
    """
    Run a single-page vulnerability search and print basic info.
    """
    http = _load_http_from_config()
    api = VulnsAPI(http)

    items = api.search(query=query, limit=100, offset=0)
    for v in items:
        vuln_id = v.get("vuln_id") or v.get("id")
        name = v.get("name") or v.get("title") or ""
        risk = v.get("risk_factor") or ""
        click.echo(f"{vuln_id}\t{risk}\t{name}")


@vulns.command("get")
@click.argument("vuln_id")
def vulns_get(vuln_id):
    """Get details for a single vulnerability."""
    http = _load_http_from_config()
    api = VulnsAPI(http)

    v = api.get_vuln(vuln_id)
    click.echo(pretty_json(v))


@vulns.command("export-all")
@click.option("--query", default="*", help="Vuln search query (default: *)")
@click.option("--json-out", help='JSON output path or "auto" for auto filename')
@click.option("--csv-out", help='CSV output path or "auto" for auto filename')
def vulns_export_all(query, json_out, csv_out):
    """
    Export ALL vulnerabilities matching the query (default: all).
    """
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    api = VulnsAPI(http)

    if json_out:
        path = None if json_out == "auto" else json_out
        out = api.export_all_vulns_json(path=path, query=query)
        click.echo(f"All vulns JSON written: {out}")

    if csv_out:
        path = None if csv_out == "auto" else csv_out
        out = api.export_all_vulns_csv(path=path, query=query)
        click.echo(f"All vulns CSV written: {out}")


# ---------------------------------------------------------------------------
# TEMPLATES (Tenable-provided)
# ---------------------------------------------------------------------------

@cli.group()
def templates():
    """Tenable-provided WAS templates."""
    pass


@templates.command("list")
def templates_list():
    """List Tenable-provided templates."""
    http = _load_http_from_config()
    api = TemplatesAPI(http)

    items = api.list_all()
    for t in items:
        tid = t.get("template_id") or t.get("id")
        name = t.get("name") or ""
        click.echo(f"{tid}\t{name}")


# ---------------------------------------------------------------------------
# USER-DEFINED TEMPLATES
# ---------------------------------------------------------------------------

@cli.group(name="user-templates")
def user_templates():
    """User-defined WAS templates."""
    pass


@user_templates.command("list")
def user_templates_list():
    """List user-defined templates."""
    http = _load_http_from_config()
    api = UserTemplatesAPI(http)

    items = api.list_user_templates()
    for t in items:
        tid = t.get("user_template_id") or t.get("id")
        name = t.get("name") or ""
        click.echo(f"{tid}\t{name}")


# ---------------------------------------------------------------------------
# PLUGINS
# ---------------------------------------------------------------------------

@cli.group()
def plugins():
    """WAS plugin metadata."""
    pass


@plugins.command("list")
def plugins_list():
    """List all WAS plugins (basic info)."""
    http = _load_http_from_config()
    api = PluginsAPI(http)

    items = api.list_plugins()
    for p in items:
        pid = p.get("plugin_id") or p.get("id")
        name = p.get("name") or ""
        risk = p.get("risk_factor") or ""
        click.echo(f"{pid}\t{risk}\t{name}")


@plugins.command("get")
@click.argument("plugin_id")
def plugins_get(plugin_id):
    """Get details for a single plugin."""
    http = _load_http_from_config()
    api = PluginsAPI(http)

    details = api.get_plugin(plugin_id)
    click.echo(pretty_json(details))


@plugins.command("export")
@click.argument("plugin_ids")
@click.option("--json-out", help='JSON output path or "auto" for auto filename')
@click.option("--csv-out", help='CSV output path or "auto" for auto filename')
def plugins_export(plugin_ids, json_out, csv_out):
    """
    Export one or more plugins.

    plugin_ids can be:
        - single: "98074"
        - multiple: "98074,12345,77777"
    """
    if not json_out and not csv_out:
        csv_out = "auto"

    ids = _parse_ids_arg(plugin_ids)
    if not ids:
        raise click.ClickException("No plugin IDs provided.")

    http = _load_http_from_config()
    api = PluginsAPI(http)

    if len(ids) == 1:
        flat = [api.flatten_single(ids[0])]
    else:
        flat = api.flatten_multi(ids)

    if json_out:
        path = None if json_out == "auto" else json_out
        if path is None:
            path = timestamp_filename(prefix="plugins", ext="json")
        write_json_safe(path, flat)
        click.echo(f"Plugins JSON written: {path}")

    if csv_out:
        path = None if csv_out == "auto" else csv_out
        if path is None:
            path = timestamp_filename(prefix="plugins", ext="csv")
        write_csv_safe(path, flat)
        click.echo(f"Plugins CSV written: {path}")


@plugins.command("export-all")
@click.option("--json-out", help='JSON output path or "auto" for auto filename')
@click.option("--csv-out", help='CSV output path or "auto" for auto filename')
def plugins_export_all(json_out, csv_out):
    """Export ALL plugins."""
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    api = PluginsAPI(http)

    flat = api.flatten_all()

    if json_out:
        path = None if json_out == "auto" else json_out
        if path is None:
            path = timestamp_filename(prefix="plugins_all", ext="json")
        write_json_safe(path, flat)
        click.echo(f"All plugins JSON written: {path}")

    if csv_out:
        path = None if csv_out == "auto" else csv_out
        if path is None:
            path = timestamp_filename(prefix="plugins_all", ext="csv")
        write_csv_safe(path, flat)
        click.echo(f"All plugins CSV written: {path}")


# ---------------------------------------------------------------------------
# FOLDERS
# ---------------------------------------------------------------------------

@cli.group()
def folders():
    """WAS folders."""
    pass


@folders.command("list")
def folders_list():
    """List WAS folders."""
    http = _load_http_from_config()
    api = FoldersAPI(http)

    items = api.list_folders()
    for f in items:
        fid = f.get("id") or f.get("folder_id")
        name = f.get("name") or ""
        click.echo(f"{fid}\t{name}")


# ---------------------------------------------------------------------------
# FILTERS
# ---------------------------------------------------------------------------

@cli.group()
def filters():
    """WAS filter metadata."""
    pass


@filters.command("scan-configs")
def filters_scan_configs():
    """Show scan config filters."""
    http = _load_http_from_config()
    api = FiltersAPI(http)

    data = api.scan_configs_filters()
    click.echo(pretty_json(data))


@filters.command("scans")
def filters_scans():
    """Show scan filters."""
    http = _load_http_from_config()
    api = FiltersAPI(http)

    data = api.scans_filters()
    click.echo(pretty_json(data))


@filters.command("user-templates")
def filters_user_templates():
    """Show user-template filters."""
    http = _load_http_from_config()
    api = FiltersAPI(http)

    data = api.user_templates_filters()
    click.echo(pretty_json(data))


@filters.command("vulns")
def filters_vulns():
    """Show vulnerability filters."""
    http = _load_http_from_config()
    api = FiltersAPI(http)

    data = api.vulns_filters()
    click.echo(pretty_json(data))


@filters.command("vulns-scan")
def filters_vulns_scan():
    """Show scan-vuln filters."""
    http = _load_http_from_config()
    api = FiltersAPI(http)

    data = api.vulns_scan_filters()
    click.echo(pretty_json(data))


# ---------------------------------------------------------------------------
# NOTES
# ---------------------------------------------------------------------------

@cli.group()
def notes():
    """WAS scan notes."""
    pass


@notes.command("list")
@click.argument("scan_id")
def notes_list(scan_id):
    """List notes for a given scan."""
    http = _load_http_from_config()
    api = NotesAPI(http)

    items = api.list_notes(scan_id)
    for n in items:
        nid = n.get("scan_note_id") or n.get("id")
        sev = n.get("severity") or ""
        title = n.get("title") or ""
        click.echo(f"{nid}\t{sev}\t{title}")


# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------

def main():
    cli(prog_name="pytenable-was")


if __name__ == "__main__":
    main()
