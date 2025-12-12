# pytenable_was/config.py

import json
import stat
from pathlib import Path
from getpass import getpass
import click

# =====================================================================
# CONFIG LOCATION
# =====================================================================

CONFIG_DIR = Path.home() / ".pytenable-was"
CONFIG_FILE = CONFIG_DIR / "config.json"


# =====================================================================
# DEFAULT CONFIG
# =====================================================================

def default_config() -> dict:
    return {
        "api_key": None,
        "proxy_url": None,
        "proxy_auth": False,
        "proxy_username": None,
        "proxy_password": None,
    }


# =====================================================================
# FILE HELPERS
# =====================================================================

def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_config_dir()

    if not CONFIG_FILE.exists():
        return default_config()

    try:
        with CONFIG_FILE.open("r") as f:
            return json.load(f)
    except Exception:
        click.echo("⚠️  Config file is corrupted. Resetting.")
        return default_config()


def save_config(cfg: dict):
    ensure_config_dir()
    tmp = CONFIG_FILE.with_suffix(".tmp")

    with tmp.open("w") as f:
        json.dump(cfg, f, indent=2)

    tmp.replace(CONFIG_FILE)

    try:
        CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


# =====================================================================
# VALIDATION
# =====================================================================

def normalize_proxy_url(url: str) -> str:
    url = url.strip()

    if url.startswith("http://") or url.startswith("https://"):
        return url

    raise click.ClickException("Proxy URL must start with http:// or https://")


def validate_proxy(cfg: dict):
    if cfg["proxy_auth"]:
        if not cfg["proxy_username"] or not cfg["proxy_password"]:
            raise click.ClickException(
                "Proxy authentication enabled but credentials are missing."
            )


# =====================================================================
# CLICK GROUP
# =====================================================================

@click.group(help="Manage pytenable-was configuration (API key, proxy).")
def config():
    pass


# =====================================================================
# SHOW
# =====================================================================

@config.command("show")
def show():
    cfg = load_config()

    click.echo("pytenable-was configuration:")
    click.echo(f"  API Key:        {'****' if cfg['api_key'] else '(not set)'}")
    click.echo(f"  Proxy URL:      {cfg['proxy_url'] or '(none)'}")
    click.echo(f"  Proxy Auth:     {'Enabled' if cfg['proxy_auth'] else 'Disabled'}")
    click.echo(f"  Proxy Username: {cfg['proxy_username'] or '(none)'}")
    click.echo(f"  Proxy Password: {'****' if cfg['proxy_password'] else '(none)'}")
    click.echo(f"  Config File:    {CONFIG_FILE}")


# =====================================================================
# API KEY
# =====================================================================

@config.command("set-key")
def set_key():
    key = getpass("Enter API key (hidden): ").strip()

    if not key:
        raise click.ClickException("API key cannot be empty.")

    cfg = load_config()
    cfg["api_key"] = key
    save_config(cfg)

    click.echo("API key saved.")


@config.command("clear-key")
def clear_key():
    if input("Remove API key? (y/N): ").lower() != "y":
        click.echo("Cancelled.")
        return

    cfg = load_config()
    cfg["api_key"] = None
    save_config(cfg)

    click.echo("API key removed.")


# =====================================================================
# PROXY
# =====================================================================

@config.command("set-proxy")
@click.argument("url")
def set_proxy(url):
    cfg = load_config()
    cfg["proxy_url"] = normalize_proxy_url(url)
    save_config(cfg)

    click.echo(f"Proxy set to {cfg['proxy_url']}")


@config.command("clear-proxy")
def clear_proxy():
    cfg = load_config()
    cfg.update({
        "proxy_url": None,
        "proxy_auth": False,
        "proxy_username": None,
        "proxy_password": None,
    })
    save_config(cfg)

    click.echo("Proxy cleared.")


# =====================================================================
# PROXY AUTH
# =====================================================================

@config.command("set-proxy-auth")
def set_proxy_auth():
    username = input("Proxy username: ").strip()
    password = getpass("Proxy password (hidden): ").strip()

    if not username or not password:
        raise click.ClickException("Username and password required.")

    cfg = load_config()
    cfg["proxy_auth"] = True
    cfg["proxy_username"] = username
    cfg["proxy_password"] = password

    validate_proxy(cfg)
    save_config(cfg)

    click.echo("Proxy authentication saved.")


@config.command("clear-proxy-auth")
def clear_proxy_auth():
    cfg = load_config()
    cfg["proxy_auth"] = False
    cfg["proxy_username"] = None
    cfg["proxy_password"] = None

    save_config(cfg)
    click.echo("Proxy authentication disabled.")


# =====================================================================
# RESET
# =====================================================================

@config.command("reset")
def reset():
    if input("This will delete ALL config. Proceed? (y/N): ").lower() != "y":
        click.echo("Cancelled.")
        return

    save_config(default_config())
    click.echo("Configuration reset.")
