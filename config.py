# config.py
import json
import os
import stat
from pathlib import Path
import click
from getpass import getpass


# =====================================================================
# CONFIG FILE LOCATION
# =====================================================================

CONFIG_DIR = Path.home() / ".pytenable-was"
CONFIG_FILE = CONFIG_DIR / "config.json"


# =====================================================================
# DEFAULT CONFIG STRUCTURE
# =====================================================================

def _default_config() -> dict:
    return {
        "api_key": None,

        "proxy_url": None,
        "proxy_auth": False,
        "proxy_username": None,
        "proxy_password": None,
    }


# =====================================================================
# INTERNAL HELPERS
# =====================================================================

def ensure_config_dir():
    """Ensure ~/.pytenable-was exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load config from disk, or create defaults."""
    ensure_config_dir()

    if not CONFIG_FILE.exists():
        return _default_config()

    try:
        with CONFIG_FILE.open("r") as f:
            return json.load(f)
    except Exception:
        click.echo("Warning: config file corrupted. Resetting.")
        return _default_config()


def save_config(cfg: dict):
    """Save config atomically with safe permissions."""
    ensure_config_dir()
    temp = CONFIG_FILE.with_suffix(".tmp")

    with temp.open("w") as f:
        json.dump(cfg, f, indent=2)

    temp.replace(CONFIG_FILE)

    # chmod 600 where possible
    try:
        CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def _normalize_proxy_url(url: str) -> str:
    """Ensure http:// or https:// prefix is correct."""
    u = url.strip()

    if u.lower().startswith("http://"):
        return "http://" + u[7:]
    if u.lower().startswith("https://"):
        return "https://" + u[8:]

    raise click.ClickException("Proxy URL must start with http:// or https://")


def _validate_proxy_block(cfg: dict):
    """Ensure proxy auth configuration is internally consistent."""
    if cfg["proxy_auth"]:
        if not cfg["proxy_username"] or not cfg["proxy_password"]:
            raise click.ClickException(
                "Proxy authentication enabled but username/password are missing."
            )


# =====================================================================
# CLICK COMMAND GROUP
# =====================================================================

@click.group(help="Manage pytenable-was configuration (API keys, proxy settings).")
def config():
    pass


# =====================================================================
# SHOW CONFIG
# =====================================================================

@config.command("show", help="Display current configuration (masked).")
def config_show():
    cfg = load_config()

    masked_key = "****" if cfg.get("api_key") else "(not set)"
    masked_pw = "****" if cfg.get("proxy_password") else "(none)"

    click.echo("pytenable-was configuration:")
    click.echo(f"  API Key:         {masked_key}")
    click.echo(f"  Proxy URL:       {cfg.get('proxy_url') or '(none)'}")
    click.echo(f"  Proxy Auth:      {'Enabled' if cfg.get('proxy_auth') else 'Disabled'}")
    click.echo(f"  Proxy Username:  {cfg.get('proxy_username') or '(none)'}")
    click.echo(f"  Proxy Password:  {masked_pw}")
    click.echo(f"  Config File:     {CONFIG_FILE}")


# =====================================================================
# SET API KEY
# =====================================================================

@config.command("set-key", help="Set the API key.")
def config_set_key():
    key = getpass("Enter API key (hidden): ").strip()

    if not key:
        raise click.ClickException("API key cannot be empty.")

    cfg = load_config()
    cfg["api_key"] = key

    save_config(cfg)
    click.echo("API key saved.")


# =====================================================================
# CLEAR API KEY
# =====================================================================

@config.command("clear-key", help="Remove the stored API key.")
def config_clear_key():
    confirm = input("Remove API key? (y/N): ").strip().lower()
    if confirm != "y":
        click.echo("Cancelled.")
        return

    cfg = load_config()
    cfg["api_key"] = None
    save_config(cfg)

    click.echo("API key removed.")


# =====================================================================
# SET PROXY
# =====================================================================

@config.command("set-proxy", help="Set proxy URL.")
@click.argument("url")
def config_set_proxy(url: str):
    url = _normalize_proxy_url(url)

    cfg = load_config()
    cfg["proxy_url"] = url
    save_config(cfg)

    click.echo(f"Proxy set to: {url}")


# =====================================================================
# CLEAR PROXY
# =====================================================================

@config.command("clear-proxy", help="Clear all proxy settings.")
def config_clear_proxy():
    cfg = load_config()

    cfg["proxy_url"] = None
    cfg["proxy_auth"] = False
    cfg["proxy_username"] = None
    cfg["proxy_password"] = None

    save_config(cfg)
    click.echo("Proxy settings cleared.")


# =====================================================================
# SET PROXY AUTH
# =====================================================================

@config.command("set-proxy-auth", help="Set proxy authentication credentials.")
def config_set_proxy_auth():
    username = input("Proxy username: ").strip()
    password = getpass("Proxy password (hidden): ").strip()

    if not username or not password:
        raise click.ClickException("Username and password required.")

    cfg = load_config()
    cfg["proxy_auth"] = True
    cfg["proxy_username"] = username
    cfg["proxy_password"] = password

    _validate_proxy_block(cfg)
    save_config(cfg)

    click.echo("Proxy authentication saved.")


# =====================================================================
# CLEAR PROXY AUTH
# =====================================================================

@config.command("clear-proxy-auth", help="Disable proxy authentication.")
def config_clear_proxy_auth():
    cfg = load_config()

    cfg["proxy_auth"] = False
    cfg["proxy_username"] = None
    cfg["proxy_password"] = None

    save_config(cfg)
    click.echo("Proxy authentication cleared.")


# =====================================================================
# RESET EVERYTHING
# =====================================================================

@config.command("reset", help="Reset ALL configuration values.")
def config_reset():
    if not click.get_text_stream("stdin").isatty():
        raise click.ClickException("Reset requires interactive use.")

    confirm = input(
        "This will DELETE ALL pytenable-was config. Proceed? (y/N): "
    ).strip().lower()

    if confirm != "y":
        click.echo("Cancelled.")
        return

    save_config(_default_config())
    click.echo("Configuration reset to defaults.")
