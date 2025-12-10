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


# Attach config and scan commands
cli.add_command(config)
cli.add_command(scans)


# =====================================================================
# TEMPLATES (ONE TOP-LEVEL GROUP)
# =====================================================================
@cli.group(help="Manage WAS templates (Tenable-provided & User-defined).")
def templates():
    pass


# API helper factories
def prov():
    return ProvidedTemplatesAPI(HttpClient())

def user():
    return UserTemplatesAPI(HttpClient())


# =====================================================================
# TENABLE-PROVIDED TEMPLATES (READ-ONLY)
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
@templates.group(help="User-defined templates (create, update, delete).")
def user_templates():
    pass


@user_templates.command("list", help="List user-defined templates.")
def user_list():
    result = user().list()
    click.echo_json(result)


@user_templates.command("get", help="Get user-defined template by ID.")
@click.argument("template_id")
def user_get(template_id):
    result = user().get(template_id)
    click.echo_json(result)


@user_templates.command("create", help="Create a new user-defined template.")
@click.argument("payload_file")
def user_create(payload_file):
    payload = json.loads(Path(payload_file).read_text())
    result = user().create(payload)
    click.echo_json(result)


@user_templates.command("update", help="Update an existing user-defined template.")
@click.argument("template_id")
@click.argument("payload_file")
def user_update(template_id, payload_file):
    payload = json.loads(Path(payload_file).read_text())
    result = user().update(template_id, payload)
    click.echo_json(result)


@user_templates.command("delete", help="Delete a user-defined template.")
@click.argument("template_id")
def user_delete(template_id):
    result = user().delete(template_id)
    click.echo_json(result)
