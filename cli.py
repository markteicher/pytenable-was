# pytenable_was/cli.py

import json
import csv
import click
from pathlib import Path
from datetime import datetime

from .config import Config
from .http import HTTPClient
from .utils import pretty_json
from .scans import ScansAPI
from .templates import TemplatesAPI
from .user_templates import UserTemplatesAPI
from .users import UsersAPI
from .plugins import PluginsAPI
from .folders import FoldersAPI
from .findings_export import FindingsExportAPI


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def load_http_from_config():
    cfg = Config().load()

    access_key = cfg.get("access_key")
    secret_key = cfg.get("secret_key")
    proxy = cfg.get("proxy")

    if not access_key or not secret_key:
        raise click.ClickException("API keys not configured. Run: pytenable-was config set")

    return HTTPClient(
        access_key=access_key,
        secret_key=secret_key,
        proxy=proxy,
        timeout=30
    )


def write_json(path: str, data):
    path = Path(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    click.echo(f"JSON written: {path}")


def write_csv(path: str, rows: list):
    if not rows:
        click.echo("No data to write.")
        return

    path = Path(path)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    click.echo(f"CSV written: {path}")


def now_timestamp():
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def auto_filename(prefix: str, ext: str):
    ts = now_timestamp()
    return f"{prefix}_{ts}.{ext}"


# -------------------------------------------------------------------
# Root CLI
# -------------------------------------------------------------------
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Tenable WAS v2 SDK + CLI"""
    pass


# -------------------------------------------------------------------
# Config Commands
# -------------------------------------------------------------------

@cli.group()
def config():
    """Configure API keys & proxy settings"""
    pass


@config.command("set")
@click.option("--access-key", required=True)
@click.option("--secret-key", required=True)
@click.option("--proxy", default=None)
def config_set(access_key, secret_key, proxy):
    cfg = Config()
    cfg.set_access_key(access_key)
    cfg.set_secret_key(secret_key)

    if proxy:
        cfg.set_proxy(proxy)

    click.echo("Configuration saved.")


@config.command("get")
def config_get():
    cfg = Config().load()
    click.echo(pretty_json(cfg))


@config.command("clear")
def config_clear():
    Config().clear()
    click.echo("Configuration cleared.")


@config.command("reset")
def config_reset():
    if click.confirm("Reset all configuration?"):
        Config().clear()
        click.echo("Configuration reset.")
    else:
        click.echo("Cancelled.")


# -------------------------------------------------------------------
# Scans
# -------------------------------------------------------------------

@cli.group()
def scans():
    """Manage WAS scans"""
    pass


@scans.command("list")
def scans_list():
    """List all scans"""
    http = load_http_from_config()
    api = ScansAPI(http)
    scans = api.list_all()

    for s in scans:
        click.echo(f"{s.id}  {s.name}")


@scans.command("details")
@click.argument("scan_id")
def scans_details(scan_id):
    """Get detailed scan information"""
    http = load_http_from_config()
    api = ScansAPI(http)

    details = api.get_details(scan_id)
    click.echo(pretty_json(details.model_dump()))


@scans.command("export-findings")
@click.argument("scan_id")
@click.option("--json-out", help="Export findings to JSON (or 'auto')")
@click.option("--csv-out", help="Export findings to CSV (or 'auto')")
def scans_export_findings(scan_id, json_out, csv_out):
    """Export scan findings using the WAS export endpoint"""
    if not json_out and not csv_out:
        raise click.ClickException("Specify --json-out or --csv-out")

    http = load_http_from_config()
    api = FindingsExportAPI(http)

    # JSON export
    if json_out:
        if json_out.lower() == "auto":
            json_out = auto_filename(f"scan-{scan_id}-findings", "json")
        api.export_json(scan_id, json_out)
        click.echo(f"Exported JSON: {json_out}")

    # CSV export
    if csv_out:
        if csv_out.lower() == "auto":
            csv_out = auto_filename(f"scan-{scan_id}-findings", "csv")
        api.export_csv(scan_id, csv_out)
        click.echo(f"Exported CSV: {csv_out}")


# -------------------------------------------------------------------
# Templates (Tenable-provided)
# -------------------------------------------------------------------

@cli.group()
def templates():
    """List Tenable-provided WAS templates"""
    pass


@templates.command("list")
def templates_list():
    http = load_http_from_config()
    api = TemplatesAPI(http)
    items = api.list_all()

    for t in items:
        click.echo(f"{t.get('template_id')}  {t.get('name')}")


# -------------------------------------------------------------------
# User-Defined Templates
# -------------------------------------------------------------------

@cli.group(name="user-templates")
def user_templates():
    """List user-created WAS templates"""
    pass


@user_templates.command("list")
def user_templates_list():
    http = load_http_from_config()
    api = UserTemplatesAPI(http)
    items = api.list_user_templates()

    for t in items:
        click.echo(f"{t.get('user_template_id')}  {t.get('name')}")


# -------------------------------------------------------------------
# Users (lookup, enrichment)
# -------------------------------------------------------------------

@cli.group()
def users():
    """Lookup users and resolve scan ownership"""
    pass


@users.command("list")
def users_list():
    http = load_http_from_config()
    api = UsersAPI(http)
    users = api.fetch_all_users()

    for u in users:
        click.echo(f"{u.get('user_id')}  {u.get('email')}")


# -------------------------------------------------------------------
# Folders
# -------------------------------------------------------------------

@cli.group()
def folders():
    """List WAS folders"""
    pass


@folders.command("list")
def folders_list():
    http = load_http_from_config()
    api = FoldersAPI(http)
    items = api.list()

    for f in items:
        click.echo(f"{f.get('folder_id')}  {f.get('name')}")


# -------------------------------------------------------------------
# Plugins
# -------------------------------------------------------------------

@cli.group()
def plugins():
    """WAS Plugin metadata"""
    pass


@plugins.command("list")
def plugins_list():
    http = load_http_from_config()
    api = PluginsAPI(http)

    items = api.list_plugins()
    for p in items:
        click.echo(f"{p.get('plugin_id')}  {p.get('name')}")


@plugins.command("get")
@click.argument("plugin_ids")
def plugins_get(plugin_ids):
    """
    Get one or more plugin IDs (comma-separated)
    Example:
        pytenable-was plugins get 98074
        pytenable-was plugins get 98074,51530,12345
    """
    http = load_http_from_config()
    api = PluginsAPI(http)

    ids = [p.strip() for p in plugin_ids.split(",") if p.strip()]
    results = [api.get_plugin(pid) for pid in ids]

    if len(results) == 1:
        click.echo(pretty_json(results[0]))
    else:
        click.echo(pretty_json(results))


@plugins.command("export")
@click.argument("plugin_ids")
@click.option("--json-out", help="Write JSON (or 'auto')")
@click.option("--csv-out", help="Write CSV (or 'auto')")
def plugins_export(plugin_ids, json_out, csv_out):
    """
    Export one or more plugins to JSON or CSV
    """
    if not json_out and not csv_out:
        raise click.ClickException("Specify --json-out or --csv-out")

    http = load_http_from_config()
    api = PluginsAPI(http)

    ids = [p.strip() for p in plugin_ids.split(",") if p.strip()]
    rows = [api.flatten_single(pid) for pid in ids]

    # JSON
    if json_out:
        if json_out.lower() == "auto":
            json_out = auto_filename(
                "plugin" if len(rows) == 1 else "plugins",
                "json"
            )
        write_json(json_out, rows if len(rows) > 1 else rows[0])

    # CSV
    if csv_out:
        if csv_out.lower() == "auto":
            csv_out = auto_filename(
                "plugin" if len(rows) == 1 else "plugins",
                "csv"
            )
        write_csv(csv_out, rows)


@plugins.command("export-all")
@click.option("--json-out", help="Write JSON (or 'auto')")
@click.option("--csv-out", help="Write CSV (or 'auto')")
def plugins_export_all(json_out, csv_out):
    """
    Export all plugins
    """
    if not json_out and not csv_out:
        raise click.ClickException("Specify --json-out or --csv-out")

    http = load_http_from_config()
    api = PluginsAPI(http)
    rows = api.flatten_all()

    # JSON
    if json_out:
        if json_out.lower() == "auto":
            json_out = auto_filename("plugins-all", "json")
        write_json(json_out, rows)

    # CSV
    if csv_out:
        if csv_out.lower() == "auto":
            csv_out = auto_filename("plugins-all", "csv")
        write_csv(csv_out, rows)
