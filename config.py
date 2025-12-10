# config.py
import json
import os
import stat
from pathlib import Path
import click
from getpass import getpass

CONFIG_DIR = Path.home() / ".pytenable-was"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def ensure_config_dir():
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> dict:
    ensure_config_dir()

    if not CONFIG_FILE.exists():
        return _default_config()

    try:
        with CONFIG_FILE.open("r") as f:
            return json.load(f)
    except Exception:
        click.echo("Warning: Config file corrupted. Rebuilding default config.")
        return _default_config()


def save_config(config: dict):
    """Atomic safe-write with chmod 600."""
    ensure_config_dir()
    tmp_file = CONFIG_FILE.with_suffix(".tmp")

    with tmp_file.open("w") as f:
        json.dump(config, f, indent=2)

    # Replace original atomically
    tmp_file.replace(CONFIG_FILE)

    # Permissions: user read/write only when possible
    try:
        CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def _default_config():
    return {
        "api_key": None,
        "proxy_url": None,
        "proxy_username": None,
        "proxy_password": None,
        "proxy_auth": False,
    }


# ------------------------------------------------------------
# Validators
# ------------------------------------------------------------
def _normalize_proxy_url(url: str) -> str:
    u = url.strip()

    # Normalize scheme case
    if u.lower().startswith("http://"):
        return "http://" + u[7:]
    if u.lower().startswith("https://"):
        return "https://" + u[8:]

    raise click.ClickException("Proxy URL must start with http:// or https://")


def _validate_proxy_components(config):
    """Ensure proxy auth only valid when username & password exist."""
    if config["proxy_auth"]:
        if not config["proxy_username"] or not config["proxy_password"]:
            raise click.ClickException(
                "Proxy authentication enabled but username/password not set."
            )


# ------------------------------------------------------------
# Click command group
# ------------------------------------------------------------
@click.group(help="Manage pytenable-was configuration.")
def config():
    pass


# ------------------------------------------------------------
# Show config (masked)
# ------------------------------------------------------------
@config.command("show", help="Show current configuration with masked secrets.")
def config_show():
    cfg = load_config()

    masked_key = "****" if cfg["api_key"] else "(not set)"
    masked_pw = "****" if cfg["proxy_password"] else "(none)"

    click.echo("Current pytenable-was configuration:")
    click.echo(f"  API Key:         {masked_key}")
    click.echo(f"  Proxy URL:       {cfg['proxy_url'] or '(none)'}")
    click.echo(f"  Proxy Auth:      {'Enabled' if cfg['proxy_auth'] else 'Disabled'}")
    click.echo(f"  Proxy Username:  {cfg['proxy_username'] or '(none)'}")
    click.echo(f"  Proxy Password:  {masked_pw}")
    click.echo(f"  Config Path:     {CONFIG_FILE}")


# ------------------------------------------------------------
# Set API key
# ------------------------------------------------------------
@config.command("set-key", help="Set the API key.")
def config_set_key():
    key = getpass("Enter API key (input hidden): ").strip()
    if not key:
        raise click.ClickException("API key cannot be empty.")

    cfg = load_config()
    cfg["api_key"] = key

    save_config(cfg)
    click.echo("API key saved.")


# ------------------------------------------------------------
# Clear API key (with confirmation)
# ------------------------------------------------------------
@config.command("clear-key", help="Remove the stored API key.")
def config_clear_key():
    confirm = input("Remove API key? (y/N): ").strip().lower()
    if confirm != "y":
        click.echo("Operation cancelled. API key not removed.")
        return

    cfg = load_config()
    cfg["api_key"] = None
    save_config(cfg)

    click.echo("API key cleared.")


# ------------------------------------------------------------
# Set proxy
# ------------------------------------------------------------
@config.command("set-proxy", help="Set proxy address.")
@click.argument("url")
def config_set_proxy(url):
    try:
        normalized = _normalize_proxy_url(url)
    except Exception as e:
        raise click.ClickException(str(e))

    cfg = load_config()
    cfg["proxy_url"] = normalized
    save_config(cfg)

    click.echo(f"Proxy URL set to: {normalized}")


# ------------------------------------------------------------
# Clear proxy
# ------------------------------------------------------------
@config.command("clear-proxy", help="Clear proxy configuration.")
def config_clear_proxy():
    cfg = load_config()

    cfg["proxy_url"] = None
    cfg["proxy_username"] = None
    cfg["proxy_password"] = None
    cfg["proxy_auth"] = False

    save_config(cfg)
    click.echo("Proxy configuration cleared.")


# ------------------------------------------------------------
# Set proxy authentication credentials
# ------------------------------------------------------------
@config.command("set-proxy-auth", help="Set proxy authentication credentials.")
def config_set_proxy_auth():
    username = input("Proxy username: ").strip()
    if not username:
        raise click.ClickException("Proxy username cannot be empty.")

    password = getpass("Proxy password (input hidden): ").strip()
    if not password:
        raise click.ClickException("Proxy password cannot be empty.")

    cfg = load_config()
    cfg["proxy_username"] = username
    cfg["proxy_password"] = password
    cfg["proxy_auth"] = True

    _validate_proxy_components(cfg)
    save_config(cfg)

    click.echo("Proxy authentication set.")


# ------------------------------------------------------------
# Clear proxy auth
# ------------------------------------------------------------
@config.command("clear-proxy-auth", help="Disable proxy authentication.")
def config_clear_proxy_auth():
    cfg = load_config()
    cfg["proxy_auth"] = False
    cfg["proxy_username"] = None
    cfg["proxy_password"] = None

    save_config(cfg)
    click.echo("Proxy authentication cleared.")


# ------------------------------------------------------------
# Reset everything (with safety checks)
# ------------------------------------------------------------
@config.command("reset", help="Reset the entire configuration file.")
def config_reset():
    # Reject non-interactive environments (safety)
    if not click.get_text_stream("stdin").isatty():
        raise click.ClickException("Cannot reset config in non-interactive mode.")

    confirm = input(
        "This will delete ALL pytenable-was config settings. Proceed? (y/N): "
    ).strip().lower()

    if confirm != "y":
        click.echo("Reset cancelled.")
        return

    # Overwrite file with defaults
    save_config(_default_config())
    click.echo("Configuration reset to defaults.")
