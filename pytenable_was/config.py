# pytenable_was/config.py

"""
Configuration management for pytenable-was.

Stores configuration locally at:
    ~/.pytenable-was/config.json

Supports:
    - API key storage (masked on display)
    - Optional proxy configuration
    - Optional proxy authentication
"""

import json
import stat
from pathlib import Path
from getpass import getpass
import click

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

CONFIG_DIR = Path.home() / ".pytenable-was"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------

def _default_config() -> dict:
    return {
        "api_key": None,
        "proxy_url": None,
        "proxy_auth": False,
        "proxy_username": None,
        "proxy_password": None,
    }

# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    _ensure_config_dir()

    if not CONFIG_FILE.exists():
        return _default_config()

    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return _default_config()


def save_config(cfg: dict):
    _ensure_config_dir()

    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2))
    tmp.replace(CONFIG_FILE)

    # best-effort chmod 600
    try:
        CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def _validate_proxy_url(url: str):
    if not url.startswith(("http://", "https://")):
        raise click.ClickException(
            "Proxy URL must start with http:// or https://"
        )

# ---------------------------------------------------------------------
# Click command group
# ---------------------------------------------------------------------

@click.group(help="Manage pytenable-was configuration.")
def config():
    pass

# ---------------------------------------------------------------------
# Show config
# ---------------------------------------------------------------------

@config.command("show")
def config_show():
    cfg = load_config()

    click.echo("pytenable-was configuration:")
    click.echo(f"  API Key:        {'****' if cfg['api_key'] else '(not set)'}")
    click.echo(f"  Proxy URL:      {cfg['proxy_url'] or '(none)'}")
    click.echo(f"  Proxy Auth:     {'enabled' if cfg['proxy_auth'] else 'disabled'}")
    click.echo(f"  Config File:    {CONFIG_FILE}")

# ---------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------

@config.command("set-key")
def config_set_key():
    key = getpass("Enter API key (hidden): ").strip()

    if not key:
        raise click.ClickException("API key cannot be empty.")

    cfg = load_config()
    cfg["api_key"] = key
    save_config(cfg)

    click.echo("API key saved.")


@config.command("clear-key")
def config_clear_key():
    if not click.confirm("Remove stored API key?"):
        return

    cfg = load_config()
    cfg["api_key"] = None
    save_config(cfg)

    click.echo("API key removed.")

# ---------------------------------------------------------------------
# Proxy
# ---------------------------------------------------------------------

@config.command("set-proxy")
@click.argument("url")
def config_set_proxy(url: str):
    _validate_proxy_url(url)

    cfg = load_config()
    cfg["proxy_url"] = url
    save_config(cfg)

    click.echo(f"Proxy set to {url}")


@config.command("clear-proxy")
def config_clear_proxy():
    cfg = load_config()
    cfg.update(
        proxy_url=None,
        proxy_auth=False,
        proxy_username=None,
        proxy_password=None,
    )
    save_config(cfg)

    click.echo("Proxy configuration cleared.")

# ---------------------------------------------------------------------
# Proxy authentication
# ---------------------------------------------------------------------

@config.command("set-proxy-auth")
def config_set_proxy_auth():
    username = input("Proxy username: ").strip()
    password = getpass("Proxy password (hidden): ").strip()

    if not username or not password:
        raise click.ClickException("Username and password are required.")

    cfg = load_config()
    cfg.update(
        proxy_auth=True,
        proxy_username=username,
        proxy_password=password,
    )
    save_config(cfg)

    click.echo("Proxy authentication saved.")


@config.command("clear-proxy-auth")
def config_clear_proxy_auth():
    cfg = load_config()
    cfg.update(
        proxy_auth=False,
        proxy_username=None,
        proxy_password=None,
    )
    save_config(cfg)

    click.echo("Proxy authentication disabled.")

# ---------------------------------------------------------------------
# Reset everything
# ---------------------------------------------------------------------

@config.command("reset")
def config_reset():
    if not click.confirm("Reset ALL pytenable-was configuration?"):
        return

    save_config(_default_config())
    click.echo("Configuration reset to defaults.")
