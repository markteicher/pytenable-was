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
from .filters import FiltersAPI
from .vulns import VulnsAPI


# ======================================================================
# Helpers
# ======================================================================

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


def auto_filename(prefix: str, ext: str) -> str:
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{prefix}_{ts}.{ext}"


# ======================================================================
# Root CLI
# ======================================================================
@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Tenable WAS v2 SDK + CLI"""
    pass


# ======================================================================
# Config Commands
# ======================================================================
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


# ======================================================================
# Scans
# ======================================================================
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


# ======================================================================
# Templates (Tenable Provided)
# ======================================================================
@cli.group()
def templates():
    """Tenable-provided templates"""
    pass


@templates.command("list")
def templates_list():
    http = load_http_from_config()
    api = TemplatesAPI(http)
    items = api.list_all()
    for t in items:
        click.echo(f"{t.get('template_id')}  {t.get('name')}")


# ======================================================================
# User Templates
# ======================================================================
@cli.group(name="user-templates")
def user_templates():
    """User-defined templates"""
    pass


@user_templates.command("list")
def user_templates_list():
    http = load_http_from_config()
    api = UserTemplatesAPI(http)
    items = api.list_user_templates()

    for t in items:
        click.echo(f"{t.get('user_template_id')}  {t.get('name')}")


# ======================================================================
# Users
# ======================================================================
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


# ======================================================================
# Plugins
# ======================================================================
@cli.group()
def plugins():
    """WAS plugin metadata"""
    pass


@plugins.command("list")
def plugins_list():
    http = load_http_from_config()
    api = PluginsAPI(http)
    for p in api.list_plugins():
        click.echo(f"{p.get('plugin_id')}  {p.get('name')}")


@plugins.command("get")
@click.argument("plugin_id")
def plugins_get(plugin_id):
    http = load_http_from_config()
    api = PluginsAPI(http)
    click.echo(pretty_json(api.get_plugin(plugin_id)))


@plugins.command("export")
@click.argument("plugin_ids")
@click.option("--json-out")
@click.option("--csv-out")
@click.option("--auto-name", is_flag=True, help="Generate timestamped filename")
def plugins_export(plugin_ids, json_out, csv_out, auto_name):
    http = load_http_from_config()
    api = PluginsAPI(http)

    flat = api.export_many(plugin_ids)

    if json_out:
        out = json_out if not auto_name else auto_filename("plugins", "json")
        write_json(out, flat)

    if csv_out:
        out = csv_out if not auto_name else auto_filename("plugins", "csv")
        write_csv(out, flat)


@plugins.command("export-all")
@click.option("--json-out")
@click.option("--csv-out")
@click.option("--auto-name", is_flag=True)
def plugins_export_all(json_out, csv_out, auto_name):
    http = load_http_from_config()
    api = PluginsAPI(http)

    flat = api.flatten_all()

    if json_out:
        out = json_out if not auto_name else auto_filename("plugins_all", "json")
        write_json(out, flat)

    if csv_out:
        out = csv_out if not auto_name else auto_filename("plugins_all", "csv")
        write_csv(out, flat)


# ======================================================================
# Folders
# ======================================================================
@cli.group()
def folders():
    """WAS folders"""
    pass


@folders.command("list")
def folders_list():
    http = load_http_from_config()
    api = FoldersAPI(http)
    items = api.list_folders()

    for f in items:
        click.echo(f"{f.get('id')}  {f.get('name')}")


# ======================================================================
# Filters
# ======================================================================
@cli.group()
def filters():
    """WAS filter metadata"""
    pass


@filters.command("scan-configs")
def filters_scan_configs():
    http = load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.scan_configs()))


@filters.command("scans")
def filters_scans():
    http = load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.scans()))


@filters.command("user-templates")
def filters_user_templates():
    http = load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.user_templates()))


@filters.command("vulns")
def filters_vulns():
    http = load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.vulns()))


@filters.command("vulns-scan")
def filters_vulns_scan():
    http = load_http_from_config()
    api = FiltersAPI(http)
    click.echo(pretty_json(api.vulns_scan()))


# ======================================================================
# Vulnerabilities
# ======================================================================
@cli.group()
def vulns():
    """WAS v2 vulnerabilities"""
    pass


# --------- SEARCH ------------------------------------------------------

@vulns.command("search")
@click.option("--severity")
@click.option("--plugin-id")
@click.option("--scan-id")
@click.option("--application-id")
@click.option("--state")
@click.option("--since", help="ISO8601 or epoch")
@click.option("--until", help="ISO8601 or epoch")
@click.option("--filters-file", type=click.Path(exists=True))
@click.option("--json-out")
@click.option("--csv-out")
@click.option("--auto-name", is_flag=True)
def vulns_search(severity, plugin_id, scan_id, application_id, state,
                 since, until, filters_file, json_out, csv_out, auto_name):

    http = load_http_from_config()
    api = VulnsAPI(http)

    # Use raw filters if provided
    if filters_file:
        with open(filters_file, "r", encoding="utf-8") as f:
            filters = json.load(f)
    else:
        filters = VulnsAPI.build_filters(
            severity=severity,
            plugin_id=plugin_id,
            scan_id=scan_id,
            application_id=application_id,
            state=state,
            since=since,
            until=until
        )

    vulns = api.search(filters)
    flat = api.flatten_multi(vulns)

    if json_out:
        out = json_out if not auto_name else auto_filename("vulns_search", "json")
        write_json(out, flat)

    if csv_out:
        out = csv_out if not auto_name else auto_filename("vulns_search", "csv")
        write_csv(out, flat)

    if not json_out and not csv_out:
        click.echo(pretty_json(flat))


# --------- DETAILS -----------------------------------------------------

@vulns.command("details")
@click.argument("vuln_id")
def vulns_details(vuln_id):
    http = load_http_from_config()
    api = VulnsAPI(http)

    details = api.get_vuln(vuln_id)
    click.echo(pretty_json(details))


# --------- EXPORT ------------------------------------------------------

@vulns.command("export")
@click.argument("vuln_ids")
@click.option("--json-out")
@click.option("--csv-out")
@click.option("--auto-name", is-flag=True)
def vulns_export(vuln_ids, json_out, csv_out, auto_name):
    http = load_http_from_config()
    api = VulnsAPI(http)

    flat = api.export_many(vuln_ids)

    if json_out:
        out = json_out if not auto_name else auto_filename("vulns", "json")
        write_json(out, flat)

    if csv_out:
        out = csv_out if not auto_name else auto_filename("vulns", "csv")
        write_csv(out, flat)


# --------- EXPORT ALL (search + export) --------------------------------

@vulns.command("export-all")
@click.option("--filters-file", type=click.Path(exists=True))
@click.option("--json-out")
@click.option("--csv-out")
@click.option("--auto-name", is_flag=True)
def vulns_export_all(filters_file, json_out, csv_out, auto_name):
    http = load_http_from_config()
    api = VulnsAPI(http)

    if filters_file:
        with open(filters_file, "r", encoding="utf-8") as f:
            filters = json.load(f)
    else:
        filters = {"filters": []}

    vulns = api.search(filters)
    flat = api.flatten_multi(vulns)

    if json_out:
        out = json_out if not auto_name else auto_filename("vulns_all", "json")
        write_json(out, flat)

    if csv_out:
        out = csv_out if not auto_name else auto_filename("vulns_all", "csv")
        write_csv(out, flat)

    if not json_out and not csv_out:
        click.echo(pretty_json(flat))
