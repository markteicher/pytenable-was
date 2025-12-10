# cli.py
import click

# Import command groups EXACTLY as they exist in the library
from .config import config   # contains: set-key, clear-key, set-proxy, clear-proxy, set-proxy-auth, clear-proxy-auth, show, reset
from .scans import scans     # contains: list, get, create, delete, launch, change-owner, change-owner-bulk
from .templates import templates  # contains template-related commands


# =====================================================================
# TOP-LEVEL CLI (with exposed --version)
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
    """
    pytenable-was main CLI entrypoint.

    Subcommands are attached below:
        config      - API keys, proxy settings, reset
        scans       - WAS scan operations
        templates   - WAS scan templates
    """
    pass


# =====================================================================
# REGISTER COMMAND GROUPS
# =====================================================================

# ---- CONFIG COMMAND GROUP ----
# This exposes ALL config commands:
#
#   pytenable-was config set-key
#   pytenable-was config clear-key
#   pytenable-was config show
#   pytenable-was config set-proxy
#   pytenable-was config clear-proxy
#   pytenable-was config set-proxy-auth
#   pytenable-was config clear-proxy-auth
#   pytenable-was config reset
#
cli.add_command(config)


# ---- SCANS COMMAND GROUP ----
# This exposes:
#
#   pytenable-was scans list
#   pytenable-was scans get <scan_id>
#   pytenable-was scans create
#   pytenable-was scans delete <scan_id>
#   pytenable-was scans launch <scan_id>
#   pytenable-was scans change-owner <scan_id> <owner>
#   pytenable-was scans change-owner-bulk <file> <owner>
#
cli.add_command(scans)


# ---- TEMPLATES COMMAND GROUP ----
# This exposes:
#
#   pytenable-was templates list
#   pytenable-was templates get <template_id>
#   pytenable-was templates export <template_id> <output>
#
cli.add_command(templates)
