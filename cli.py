# cli.py
import json
import click
from pathlib import Path

from .config import config
from .scans import scans
from .http import HttpClient
from .templates import ProvidedTemplatesAPI
from .user_templates import UserTemplatesAPI


# =====================================================================
# TOP-LEVEL CLI ENTRYPOINT
# =====================================================================
@click.group(
    help="Tenable Web Application Scanning (WAS) command-line interface."
)
@click.version_option(
    version="0.1.0",
    prog_name="pytenable-was",
    message="%(prog)s version %(version)s"
)
def cli():
    pass


# Attach config + scans groups
cli.add_command(config)
cli.add_command(scans)


# =====================================================================
# TEMPLATES (ONE TOP-LEVEL GROUP)
# =====================================================================
@cli.group(help="Manage WAS templates (Tenable-provided & User-defined).")
def templates():
    pass


# API factories
def prov():
    return ProvidedTemplatesAPI(HttpClient())

def user_defined():
    return UserTemplatesAPI(HttpClient())


# =====================================================================
# TENABLE-PROVIDED TEMPLATES
# =====================================================================
@templates.group(help="Tenable-provided templates (read-only).")
def provided():
    pass


@provided.command("list", help="List Tenable-provided templates.")
def provided_list():
    result = prov().list()
    click.echo_json(result)


@provided.command("get", help="Get a Tenable-provided template by ID.")
@click.argument("template_id")
def provided_get(template_id):
    result = prov().get(template_id)
    click.echo_json(result)


# =====================================================================
# USER-DEFINED TEMPLATES (FULL CRUD)
# =====================================================================
@templates.group(name="user-defined-templates", help="User-defined templates (create, update, delete).")
def user_defined_templates():
    pass


@user_defined_templates.command("list", help="List all user-defined templates.")
def user_list():
    result = user_defined().list()
    click.echo_json(result)


@user_defined_templates.command("get", help="Get a user-defined template by ID.")
@click.argument("template_id")
def user_get(template_id):
    result = user_defined().get(template_id)
    click.echo_json(result)


@user_defined_templates.command("create", help="Create a new user-defined template from a JSON payload file.")
@click.argument("payload_file")
def user_create(payload_file):
    payload = json.loads(Path(payload_file).read_text())
    result = user_defined().create(payload)
    click.echo_json(result)


@user_defined_templates.command("update", help="Update an existing user-defined template.")
@click.argument("template_id")
@click.argument("payload_file")
def user_update(template_id, payload_file):
    payload = json.loads(Path(payload_file).read_text())
    result = user_defined().update(template_id, payload)
    click.echo_json(result)


@user_defined_templates.command("delete", help="Delete a user-defined template.")
@click.argument("template_id")
def user_delete(template_id):
    result = user_defined().delete(template_id)
    click.echo_json(result)
