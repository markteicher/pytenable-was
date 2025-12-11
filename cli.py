# pytenable_was/cli.py

import json
import csv
import click
from pathlib import Path

from .config import Config
from .http import HTTPClient
from .utils import pretty_json
from .scans import ScansAPI
from .templates import TemplatesAPI
from .user_templates import UserTemplatesAPI
from .users import UsersAPI
from .plugins import PluginsAPI


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
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    click.echo(f"CSV written: {path}")


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
# Templates
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
    """List all WAS plugins"""
    http = load_http_from_config()
    api = PluginsAPI(http)

    plugins = api.list_plugins()
    for p in plugins:
        click.echo(f"{p.get('plugin_id')}  {p.get('name')}")


@plugins.command("get")
@click.argument("plugin_id")
def plugins_get(plugin_id):
    """Get details for a plugin ID"""
    http = load_http_from_config()
    api = PluginsAPI(http)

    details = api.get_plugin(plugin_id)
    click.echo(pretty_json(details))


@plugins.command("export")
@click.argument("plugin_id")
@click.option("--json-out", "json_out", help="Export plugin to JSON file")
@click.option("--csv-out", "csv_out", help="Export plugin to CSV file")
def plugins_export(plugin_id, json_out, csv_out):
    """Export a plugin’s metadata to JSON or CSV"""
    if not json_out and not csv_out:
        raise click.ClickException("Must specify either --json-out or --csv-out")

    http = load_http_from_config()
    api = PluginsAPI(http)

    flat = api.flatten_single(plugin_id)

    if json_out:
        write_json(json_out, flat)

    if csv_out:
        write_csv(csv_out, [flat])


@plugins.command("export-all")
@click.option("--json-out", "json_out", help="Export all plugins to JSON file")
@click.option("--csv-out", "csv_out", help="Export all plugins to CSV file")
def plugins_export_all(json_out, csv_out):
    """Export ALL plugins to JSON or CSV"""
    if not json_out and not csv_out:
        raise click.ClickException("Must specify either --json-out or --csv-out")

    http = load_http_from_config()
    api = PluginsAPI(http)

    flat = api.flatten_all()

    if json_out:
        write_json(json_out, flat)

    if csv_out:
        write_csv(csv_out, flat)
