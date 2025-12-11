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
from .notes import NotesAPI


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def timestamp():
    """Return compact timestamp for filenames."""
    return datetime.utcnow().strftime("%Y%m%d_%H%M")


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
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    click.echo(f"CSV written: {path}")


def auto_filename(prefix: str, ext: str, scan_ids=None):
    """
    Generate an auto timestamped filename if user did not supply one.
    - prefix: base name (notes, plugins, findings, etc)
    - ext: json or csv
    - scan_ids: optional list of scan_ids
    """
    ts = timestamp()

    if scan_ids is None:
        return f"{prefix}_all_{ts}.{ext}"

    if len(scan_ids) == 1:
        return f"{prefix}_{scan_ids[0]}_{ts}.{ext}"

    return f"{prefix}_multi_{ts}.{ext}"


def parse_scan_ids(arg: str):
    """Convert comma-separated scan IDs into a list."""
    return [x.strip() for x in arg.split(",") if x.strip()]


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
    """Configure API keys & proxy"""
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
    http = load_http_from_config()
    api = ScansAPI(http)
    items = api.list_scans()
    for s in items:
        click.echo(f"{s.get('scan_id')}  {s.get('name')}")


# -------------------------------------------------------------------
# Templates (Tenable-provided)
# -------------------------------------------------------------------
@cli.group()
def templates():
    """Manage Tenable-provided templates"""
    pass


@templates.command("list")
def templates_list():
    http = load_http_from_config()
    api = TemplatesAPI(http)
    items = api.list_all()
    for t in items:
        click.echo(f"{t.get('template_id')}  {t.get('name')}")


# -------------------------------------------------------------------
# User Templates
# -------------------------------------------------------------------
@cli.group(name="user-templates")
def user_templates():
    """Manage user-defined templates"""
    pass


@user_templates.command("list")
def user_templates_list():
    http = load_http_from_config()
    api = UserTemplatesAPI(http)
    items = api.list_user_templates()
    for t in items:
        click.echo(f"{t.get('user_template_id')}  {t.get('name')}")


# -------------------------------------------------------------------
# Users (lookup/enrichment)
# -------------------------------------------------------------------
@cli.group()
def users():
    """User lookup & scan-owner enrichment"""
    pass


@users.command("list")
def users_list():
    http = load_http_from_config()
    api = UsersAPI(http)
    items = api.fetch_all_users()

    for u in items:
        click.echo(f"{u.get('user_id')}  {u.get('email')}")


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
    for p in api.list_plugins():
        click.echo(f"{p.get('plugin_id')}  {p.get('name')}")


@plugins.command("get")
@click.argument("plugin_ids")
def plugins_get(plugin_ids):
    http = load_http_from_config()
    api = PluginsAPI(http)

    ids = [x.strip() for x in plugin_ids.split(",")]

    for pid in ids:
        details = api.get_plugin(pid)
        click.echo(pretty_json(details))
        click.echo("-" * 50)


@plugins.command("export")
@click.argument("plugin_ids")
@click.option("--json-out", "json_out", required=False)
@click.option("--csv-out", "csv_out", required=False)
def plugins_export(plugin_ids, json_out, csv_out):
    ids = [x.strip() for x in plugin_ids.split(",")]

    if not json_out and not csv_out:
        raise click.ClickException("Must specify either --json-out or --csv-out")

    http = load_http_from_config()
    api = PluginsAPI(http)

    flat = api.flatten_plugins(ids)

    if json_out is not None:
        if json_out is True or json_out.strip() == "":
            json_out = auto_filename("plugins", "json", ids)
        write_json(json_out, flat)

    if csv_out is not None:
        if csv_out is True or csv_out.strip() == "":
            csv_out = auto_filename("plugins", "csv", ids)
        write_csv(csv_out, flat)


@plugins.command("export-all")
@click.option("--json-out", required=False)
@click.option("--csv-out", required=False)
def plugins_export_all(json_out, csv_out):
    if not json_out and not csv_out:
        raise click.ClickException("Must specify either --json-out or --csv-out")

    http = load_http_from_config()
    api = PluginsAPI(http)

    flat = api.flatten_all()

    if json_out is not None:
        if json_out is True or json_out.strip() == "":
            json_out = auto_filename("plugins", "json", None)
        write_json(json_out, flat)

    if csv_out is not None:
        if csv_out is True or csv_out.strip() == "":
            csv_out = auto_filename("plugins", "csv", None)
        write_csv(csv_out, flat)


# -------------------------------------------------------------------
# Notes (NEW)
# -------------------------------------------------------------------
@cli.group()
def notes():
    """Scan Notes (diagnostic messages from WAS scanner)"""
    pass


@notes.command("list")
@click.argument("scan_ids")
def notes_list(scan_ids):
    """List notes for one or multiple scans (comma-separated)."""
    http = load_http_from_config()
    api = NotesAPI(http)

    ids = parse_scan_ids(scan_ids)
    notes = api.list_notes_multi(ids)

    click.echo(pretty_json(notes))


@notes.command("export")
@click.argument("scan_ids")
@click.option("--json-out", required=False)
@click.option("--csv-out", required=False)
def notes_export(scan_ids, json_out, csv_out):
    """Export notes for one or multiple scans."""
    ids = parse_scan_ids(scan_ids)

    if not json_out and not csv_out:
        raise click.ClickException("Must specify either --json-out or --csv-out")

    http = load_http_from_config()
    api = NotesAPI(http)

    notes = api.list_notes_multi(ids)
    flat = api.flatten(notes)

    # Auto filename support
    if json_out is not None:
        if json_out is True or json_out.strip() == "":
            json_out = auto_filename("notes", "json", ids)
        write_json(json_out, flat)

    if csv_out is not None:
        if csv_out is True or csv_out.strip() == "":
            csv_out = auto_filename("notes", "csv", ids)
        write_csv(csv_out, flat)


@notes.command("export-all")
@click.option("--json-out", required=False)
@click.option("--csv-out", required=False)
def notes_export_all(json_out, csv_out):
    """Export notes for ALL scans."""
    if not json_out and not csv_out:
        raise click.ClickException("Must specify either --json-out or --csv-out")

    http = load_http_from_config()
    scans_api = ScansAPI(http)
    notes_api = NotesAPI(http)

    scans = scans_api.list_scans()
    scan_ids = [s.get("scan_id") for s in scans if s.get("scan_id")]

    notes = notes_api.list_all_notes(scan_ids)
    flat = notes_api.flatten(notes)

    if json_out is not None:
        if json_out is True or json_out.strip() == "":
            json_out = auto_filename("notes", "json", None)
        write_json(json_out, flat)

    if csv_out is not None:
        if csv_out is True or csv_out.strip() == "":
            csv_out = auto_filename("notes", "csv", None)
        write_csv(csv_out, flat)
