# cli.py
import click

# Import command groups from their modules
from .config import config
from .scans import scans
from .templates import templates
from .users import users


# ------------------------------------------------------------
# Top-level CLI group
# ------------------------------------------------------------
@click.group(help="Tenable Web Application Scanning (WAS) command-line interface.")
def cli():
    """
    The main pytenable-was CLI entrypoint.
    Subcommands are provided by imported command groups.
    """
    pass


# ------------------------------------------------------------
# Register command groups
# ------------------------------------------------------------

cli.add_command(config)
cli.add_command(scans)
cli.add_command(templates)
cli.add_command(users)


# ------------------------------------------------------------
# Utility for JSON output
# Users expect consistent formatting across commands.
# ------------------------------------------------------------
@click.command(hidden=True)
def version():
    """Show version information (internal command)."""
    click.echo("pytenable-was CLI")


# Optional hidden commands can be added later.
# cli.add_command(version)
