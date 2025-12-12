# pytenable_was/cli.py

"""
Command-line interface for pytenable-was.

Thin Click wrapper around SDK modules.
All state (API key, proxy) is loaded from config.py.
"""

from pathlib import Path
from typing import List

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

def _proxy_dict_from_config(cfg: dict):
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


# register config commands implemented in config.py
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
    http = _load_http_from_config()
    api = ScansAPI(http)
    api.change_owner(scan_id, user_id)
    click.echo(f"Owner updated for scan {scan_id}")


@scans.command("set-owner-bulk")
@click.argument("scan_ids", required=False)
@click.option("--from-file", "ids_file")
@click.option("--user-id", required=True)
def scans_set_owner_bulk(scan_ids, ids_file, user_id):
    if bool(scan_ids) == bool(ids_file):
        raise click.ClickException("Provide scan_ids OR --from-file")

    ids = (
        _parse_ids(scan_ids)
        if scan_ids
        else _load_ids_from_file(ids_file)
    )

    http = _load_http_from_config()
    api = ScansAPI(http)

    for sid in tqdm(ids, desc="Updating scan owners"):
        api.change_owner(sid, user_id)

    click.echo(f"Updated owner for {len(ids)} scans")


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
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    scans_api = ScansAPI(http)
    api = FindingsAPI(http=http, scans_api=scans_api)

    if json_out:
        path = None if json_out == "auto" else json_out
        out = api.export_findings_json(scan_id, path)
        click.echo(f"JSON written: {out}")

    if csv_out:
        path = None if csv_out == "auto" else csv_out
        out = api.export_findings_csv(scan_id, path)
        click.echo(f"CSV written: {out}")


@findings.command("export-all")
@click.option("--json-out")
@click.option("--csv-out")
def findings_export_all(json_out, csv_out):
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    scans_api = ScansAPI(http)
    api = FindingsAPI(http=http, scans_api=scans_api)

    if json_out:
        out = api.export_all_findings_json(
            None if json_out == "auto" else json_out
        )
        click.echo(f"JSON written: {out}")

    if csv_out:
        out = api.export_all_findings_csv(
            None if csv_out == "auto" else csv_out
        )
        click.echo(f"CSV written: {out}")


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
    http = _load_http_from_config()
    api = VulnsAPI(http)
    click.echo(pretty_json(api.get_vuln(vuln_id)))


@vulns.command("export-all")
@click.option("--query", default="*")
@click.option("--json-out")
@click.option("--csv-out")
def vulns_export_all(query, json_out, csv_out):
    if not json_out and not csv_out:
        csv_out = "auto"

    http = _load_http_from_config()
    api = VulnsAPI(http)

    if json_out:
        out = api.export_all_vulns_json(
            query=query,
            path=None if json_out == "auto" else json_out,
        )
        click.echo(f"JSON written: {out}")

    if csv_out:
        out = api.export_all_vulns_csv(
            query=query,
            path=None if csv_out == "auto" else csv_out,
        )
        click.echo(f"CSV written: {out}")


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
        pid = p.get("plugin_id")
        name = p.get("name", "")
        risk = p.get("risk_factor", "")
        click.echo(f"{pid}\t{risk}\t{name}")


@plugins.command("export")
@click.argument("plugin_ids")
@click.option("--json-out")
@click.option("--csv-out")
def plugins_export(plugin_ids, json_out, csv_out):
    if not json_out and not csv_out:
        csv_out = "auto"

    ids = _parse_ids(plugin_ids)
    http = _load_http_from_config()
    api = PluginsAPI(http)

    rows = api.flatten_multi(ids) if len(ids) > 1 else [api.flatten_single(ids[0])]

    if json_out:
        path = timestamp_filename("plugins", "json") if json_out == "auto" else json_out
        write_json_safe(path, rows)
        click.echo(f"
