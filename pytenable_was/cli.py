# pytenable_was/cli.py

"""
Command-line interface for pytenable-was.

Thin Click wrapper around SDK modules.
All state (API key, proxy) is loaded from config.py.
"""

from pathlib import Path
from typing import List, Optional

import click
from tqdm import tqdm

from . import __version__
from .config import load_config, config as config_group
from .http import HTTPClient
from .scans import ScansAPI
from .findings import FindingsAPI
from .vulns import VulnsAPI
from .plugins import PluginsAPI
from .templates import TemplatesAPI
from .user_templates import UserTemplatesAPI
from .folders import FoldersAPI
from .filters import FiltersAPI
from .notes import NotesAPI
from .utils import (
    pretty_json,
    write_csv_safe,
    write_json_safe,
    timestamp_filename,
)

# ============================================================================
# INTERNAL HELPERS
# ============================================================================

def _proxy_dict_from_config(cfg: dict) -> Optional[dict]:
    proxy_url = cfg.get("proxy_url")
    if not proxy_url:
        return None

    if cfg.get("proxy_auth"):
        user = cfg.get("proxy_username")
        pw = cfg.get("proxy_password")
        if not user or not pw:
            raise click.ClickException(
                "Proxy authentication enabled but credentials missing."
            )

        if "://" not in proxy_url:
            raise click.ClickException("Proxy URL must start with http:// or https://")

        scheme, rest = proxy_url.split("://", 1)
        proxy_url = f"{scheme}://{user}:{pw}@{rest}"

    return {"http": proxy_url, "https": proxy_url}


def _load_http_from_config() -> HTTPClient:
    cfg = load_config()
    api_key = cfg.get("api_key")

    if not api_key:
        raise click.ClickException(
            "API key not configured. Run: pytenable-was config set-key"
        )

    proxies = _proxy_dict_from_config(cfg)

    # NOTE: This assumes your HTTPClient supports api_key + proxies.
    # If your HTTPClient still uses access_key/secret_key, update http.py
    # or adjust this call accordingly.
    return HTTPClient(
        api_key=api_key,
        proxies=proxies,
        timeout=30,
    )


def _parse_ids(ids: str) -> List[str]:
    return [s.strip() for s in ids.split(",") if s.strip()]


def _load_ids_from_file(path: str) -> List[str]:
    p = Path(path)
    if not p.exists():
        raise click.ClickException(f"File not found: {path}")

    with p.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# ============================================================================
# ROOT CLI
# ============================================================================

@click.group()
@click.version_option(__version__, prog_name="pytenable-was")
def cli():
    """Tenable Web Application Scanning (WAS) v2 SDK + CLI."""
    pass


# Register config command group implemented in config.py
cli.add_command(config_group, name="config")


# ============================================================================
# SCANS
# ============================================================================

@cli.group()
def scans():
    """Manage WAS scans."""
    pass


@scans.command("list")
def scans_list():
    http = _load_http_from_config()
    api = ScansAPI(http)

    for s in api.list_scans():
        sid = s.get("scan_id") or s.get("id")
        status = s.get("status", "")
        name = s.get("name", "")
        click.echo(f"{sid}\t{status}\t{name}")


@scans.command("details")
@click.argument("scan_id")
def scans_details(scan_id):
    http = _load_http_from_config()
    api = ScansAPI(http)
    click.echo(pretty_json(api.get_scan(scan_id)))


@scans.command("set-owner")
@click.argument("scan_id")
@click.option("--user-id", required=True)
def scans_set_owner(scan_id, user_id):
    """Change owner of a single scan."""
    http = _load_http_from_config()
    api = ScansAPI(http)
    api.change_owner(scan_id, user_id)
    click.echo(f"Owner updated for scan {scan_id} -> {user_id}")


@scans.command("set-owner-bulk")
@click.argument("scan_ids", required=False)
@click.option("--from-file", "ids_file")
@click.option("--user-id", required=True)
def scans_set_owner_bulk(scan_ids, ids_file, user_id):
    """
    Change owner for many scans.

    Provide scan_ids as comma-separated, or use --from-file with one ID per line.
    """
    if bool(scan_ids) == bool(ids_file):
        raise click.ClickException("Provide scan_ids OR --from-file")

    ids = _parse_ids(scan_ids) if scan_ids else _load_ids_from_file(ids_file)
    if not ids:
        raise click.ClickException("No scan IDs provided.")

    http = _load_http_from_config()
    api = ScansAPI(http)

    for sid in tqdm(ids, desc="Updating scan owners"):
        api.change_owner(sid, user_id)

    click.echo(f"Updated owner for {len(ids)} scans -> {user_id}")


# ============================================================================
# FINDINGS
# ============================================================================

@cli.group()
def findings():
    """Export WAS findings."""
    pass


@findings.command("export")
@click.argument("scan_id")
@click.option("--json-out")
@click.option("--csv-out")
def findings_export(scan_id, json_out, csv_out):
    """Export full findings for a single scan via /export/findings."""
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    scans_api = ScansAPI(http)
    api = FindingsAPI(http=http, scans_api=scans_api)

    if json_out:
        out_path = api.export_findings_json(
            scan_id, None if json_out == "auto" else json_out
        )
        click.echo(f"Findings JSON written: {out_path}")

    if csv_out:
        out_path = api.export_findings_csv(
            scan_id, None if csv_out == "auto" else csv_out
        )
        click.echo(f"Findings CSV written: {out_path}")


@findings.command("export-all")
@click.option("--json-out")
@click.option("--csv-out")
def findings_export_all(json_out, csv_out):
    """Export ALL findings across ALL scans."""
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    scans_api = ScansAPI(http)
    api = FindingsAPI(http=http, scans_api=scans_api)

    if json_out:
        out_path = api.export_all_findings_json(None if json_out == "auto" else json_out)
        click.echo(f"All findings JSON written: {out_path}")

    if csv_out:
        out_path = api.export_all_findings_csv(None if csv_out == "auto" else csv_out)
        click.echo(f"All findings CSV written: {out_path}")


# ============================================================================
# VULNERABILITIES
# ============================================================================

@cli.group()
def vulns():
    """WAS vulnerabilities."""
    pass


@vulns.command("get")
@click.argument("vuln_id")
def vulns_get(vuln_id):
    """Get vulnerability details."""
    http = _load_http_from_config()
    api = VulnsAPI(http)
    click.echo(pretty_json(api.get_vuln(vuln_id)))


@vulns.command("export-all")
@click.option("--query", default="*")
@click.option("--json-out")
@click.option("--csv-out")
def vulns_export_all(query, json_out, csv_out):
    """Export ALL vulnerabilities matching the query (default: all)."""
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    api = VulnsAPI(http)

    if json_out:
        out_path = api.export_all_vulns_json(
            query=query, path=None if json_out == "auto" else json_out
        )
        click.echo(f"All vulns JSON written: {out_path}")

    if csv_out:
        out_path = api.export_all_vulns_csv(
            query=query, path=None if csv_out == "auto" else csv_out
        )
        click.echo(f"All vulns CSV written: {out_path}")


# ============================================================================
# TEMPLATES
# ============================================================================

@cli.group()
def templates():
    """Tenable-provided WAS templates."""
    pass


@templates.command("list")
def templates_list():
    http = _load_http_from_config()
    api = TemplatesAPI(http)
    for t in api.list_all():
        tid = t.get("template_id") or t.get("id")
        name = t.get("name", "")
        click.echo(f"{tid}\t{name}")


# ============================================================================
# USER TEMPLATES
# ============================================================================

@cli.group(name="user-templates")
def user_templates():
    """User-defined WAS templates."""
    pass


@user_templates.command("list")
def user_templates_list():
    http = _load_http_from_config()
    api = UserTemplatesAPI(http)
    for t in api.list_user_templates():
        tid = t.get("user_template_id") or t.get("id")
        name = t.get("name", "")
        click.echo(f"{tid}\t{name}")


# ============================================================================
# PLUGINS
# ============================================================================

@cli.group()
def plugins():
    """WAS plugin metadata."""
    pass


@plugins.command("list")
def plugins_list():
    http = _load_http_from_config()
    api = PluginsAPI(http)
    for p in api.list_plugins():
        pid = p.get("plugin_id") or p.get("id")
        name = p.get("name", "")
        risk = p.get("risk_factor", "")
        click.echo(f"{pid}\t{risk}\t{name}")


@plugins.command("get")
@click.argument("plugin_id")
def plugins_get(plugin_id):
    http = _load_http_from_config()
    api = PluginsAPI(http)
    click.echo(pretty_json(api.get_plugin(plugin_id)))


@plugins.command("export")
@click.argument("plugin_ids")
@click.option("--json-out")
@click.option("--csv-out")
def plugins_export(plugin_ids, json_out, csv_out):
    """Export one or more plugins (comma-separated IDs)."""
    if not json_out and not csv_out:
        csv_out = "auto"

    ids = _parse_ids(plugin_ids)
    if not ids:
        raise click.ClickException("No plugin IDs provided.")

    http = _load_http_from_config()
    api = PluginsAPI(http)

    rows = api.flatten_multi(ids) if len(ids) > 1 else [api.flatten_single(ids[0])]

    if json_out:
        path = timestamp_filename(prefix="plugins", ext="json") if json_out == "auto" else json_out
        write_json_safe(path, rows)
        click.echo(f"Plugins JSON written: {path}")

    if csv_out:
        path = timestamp_filename(prefix="plugins", ext="csv") if csv_out == "auto" else csv_out
        write_csv_safe(path, rows)
        click.echo(f"Plugins CSV written: {path}")


@plugins.command("export-all")
@click.option("--json-out")
@click.option("--csv-out")
def plugins_export_all(json_out, csv_out):
    """Export ALL plugins."""
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    api = PluginsAPI(http)
    rows = api.flatten_all()

    if json_out:
        path = timestamp_filename(prefix="plugins_all", ext="json") if json_out == "auto" else json_out
        write_json_safe(path, rows)
        click.echo(f"All plugins JSON written: {path}")

    if csv_out:
        path = timestamp_filename(prefix="plugins_all", ext="csv") if csv_out == "auto" else csv_out
        write_csv_safe(path, rows)
        click.echo(f"All plugins CSV written: {path}")


# ============================================================================
# FOLDERS
# ============================================================================

@cli.group()
def folders():
    """WAS folders."""
    pass


@folders.command("list")
def folders_list():
    http = _load_http_from_config()
    api = FoldersAPI(http)
    for f in api.list_folders():
        fid = f.get("folder_id") or f.get("id")
        name = f.get("name", "")
        click.echo(f"{fid}\t{name}")


# ============================================================================
# FILTERS
# ============================================================================

@cli.group()
def filters():
    """WAS filter metadata."""
    pass


@filters.command("scan-configs")
def filters_scan_configs():
    http = _load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.scan_configs_filters()))


@filters.command("scans")
def filters_scans():
    http = _load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.scans_filters()))


@filters.command("user-templates")
def filters_user_templates():
    http = _load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.user_templates_filters()))


@filters.command("vulns")
def filters_vulns():
    http = _load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.vulns_filters()))


@filters.command("vulns-scan")
def filters_vulns_scan():
    http = _load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.vulns_scan_filters()))


# ============================================================================
# NOTES
# ============================================================================

@cli.group()
def notes():
    """WAS scan notes."""
    pass


@notes.command("list")
@click.argument("scan_id")
def notes_list(scan_id):
    http = _load_http_from_config()
    api = NotesAPI(http)
    items = api.list_notes(scan_id)
    for n in items:
        nid = n.get("scan_note_id") or n.get("id")
        sev = n.get("severity", "")
        title = n.get("title", "")
        click.echo(f"{nid}\t{sev}\t{title}")


# ============================================================================
# ENTRYPOINTS
# ============================================================================

def main():
    cli(prog_name="pytenable-was")


if __name__ == "__main__":
    main()
