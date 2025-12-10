# cli.py
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .config import Config
from .http import HTTPClient
from .configs import ConfigAPI
from .templates import TemplateAPI
from .scans import ScanAPI
from .users import UserAPI
from .utils import write_csv, pretty_json
from .errors import TenableAPIError


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def timestamp():
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def ensure_keys(cfg: Config):
    """Ensure API keys exist; if not, prompt the user."""
    if not cfg.access_key or not cfg.secret_key:
        print("API keys not configured. Run: tenable-was config keys")
        sys.exit(1)


def create_client(cfg: Config):
    return HTTPClient(
        access_key=cfg.access_key,
        secret_key=cfg.secret_key,
        proxy=cfg.proxy,
    )


# ----------------------------------------------------------------------
# Command Handlers
# ----------------------------------------------------------------------

# ===========================
# CONFIGS — SYSTEM TEMPLATES
# ===========================

def handle_configs_list(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = ConfigAPI(http)

    items = api.list()

    # Show only template_id, name, description
    print(f"{'TEMPLATE ID':36}  {'NAME':20}  DESCRIPTION")
    print("-" * 90)
    for item in items:
        tid = item.get("template_id", "")
        name = item.get("name", "")
        desc = item.get("description", "")
        print(f"{tid:36}  {name:20}  {desc}")


def handle_configs_get(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = ConfigAPI(http)

    data = api.get(args.template_id)
    print(pretty_json(data))


def handle_configs_export(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = ConfigAPI(http)

    data = api.get(args.template_id)

    ts = timestamp()

    if args.json:
        filename = f"config_{args.template_id}_{ts}.json"
        Path(filename).write_text(json.dumps(data, indent=2))
        print(f"Exported JSON → {filename}")
        return

    if args.csv:
        # CSV only includes minimal fields
        row = [{
            "template_id": data.get("template_id"),
            "name": data.get("name"),
            "description": data.get("description"),
        }]
        filename = f"config_{args.template_id}_{ts}.csv"
        write_csv(filename, row)
        print(f"Exported CSV → {filename}")
        return

    print("Specify --json or --csv")


# ===========================
# USER TEMPLATES — CRUD
# ===========================

def handle_templates_list(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = TemplateAPI(http)

    items = api.list()

    # user_template_id, name, created_at, updated_at, is_shared
    print(f"{'USER TEMPLATE ID':36}  {'NAME':22}  {'SHARED':6}  CREATED AT                  UPDATED AT")
    print("-" * 120)
    for t in items:
        print(
            f"{t.get('user_template_id',''):36}  "
            f"{t.get('name','')[:22]:22}  "
            f"{str(t.get('is_shared',False)):6}  "
            f"{t.get('created_at',''):26}  "
            f"{t.get('updated_at','')}"
        )


def handle_templates_get(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = TemplateAPI(http)

    data = api.get(args.user_template_id)
    print(pretty_json(data))


def handle_templates_create(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = TemplateAPI(http)

    payload = json.loads(Path(args.config_file).read_text())
    data = api.create(payload)
    print(pretty_json(data))


def handle_templates_update(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = TemplateAPI(http)

    payload = json.loads(Path(args.config_file).read_text())
    data = api.update(args.user_template_id, payload)
    print(pretty_json(data))


def handle_templates_delete(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = TemplateAPI(http)

    api.delete(args.user_template_id)
    print(f"Deleted user template {args.user_template_id}")


def handle_templates_export(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)
    api = TemplateAPI(http)

    data = api.get(args.user_template_id)
    ts = timestamp()

    if args.json:
        filename = f"user_template_{args.user_template_id}_{ts}.json"
        Path(filename).write_text(json.dumps(data, indent=2))
        print(f"Exported JSON → {filename}")
        return

    if args.csv:
        filename = f"user_template_{args.user_template_id}_{ts}.csv"
        row = [{
            "user_template_id": data.get("user_template_id"),
            "name": data.get("name"),
            "description": data.get("description"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "is_shared": data.get("is_shared"),
        }]
        write_csv(filename, row)
        print(f"Exported CSV → {filename}")
        return

    print("Specify --json or --csv")


# ===========================
# SCANS — OWNER RESOLUTION
# ===========================

def handle_scans_list(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)

    user_api = UserAPI(http)
    scan_api = ScanAPI(http, user_api)

    scans = scan_api.list()

    # Header
    if args.show_owner:
        print(f"{'SCAN ID':34}  {'NAME':20}  {'OWNER NAME':20}  OWNER EMAIL")
        print("-" * 120)
    else:
        print(f"{'SCAN ID':34}  NAME")
        print("-" * 60)

    for s in scans:
        sid = s.get("scan_id", "")
        name = s.get("name", "")

        if args.show_owner:
            owner = s.get("owner", {})
            oname = owner.get("name", "")
            oemail = owner.get("email", "")
            print(f"{sid:34}  {name:20}  {oname:20}  {oemail}")
        else:
            print(f"{sid:34}  {name}")


def handle_scans_get(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)

    user_api = UserAPI(http)
    scan_api = ScanAPI(http, user_api)

    data = scan_api.get(args.scan_id)
    print(pretty_json(data))


def handle_scans_export(args, cfg):
    ensure_keys(cfg)
    http = create_client(cfg)

    user_api = UserAPI(http)
    scan_api = ScanAPI(http, user_api)

    data = scan_api.get(args.scan_id)
    ts = timestamp()

    if args.json:
        filename = f"scan_{args.scan_id}_{ts}.json"
        Path(filename).write_text(json.dumps(data, indent=2))
        print(f"Exported JSON → {filename}")
        return

    print("Only JSON export is supported for scans at this time.")


# ===========================
# CONFIG (KEYS + PROXY)
# ===========================

def handle_config_keys(args, cfg):
    access = input("Access Key: ").strip()
    secret = input("Secret Key: ").strip()

    cfg.access_key = access
    cfg.secret_key = secret
    cfg.save()

    print("API keys saved.")


def handle_config_proxy(args, cfg):
    proxy = input("Proxy URL (blank to clear): ").strip()
    cfg.proxy = proxy if proxy else None
    cfg.save()

    print("Proxy configuration updated.")


def handle_config_show(args, cfg):
    print("Current Configuration:")
    print(json.dumps(cfg.to_dict(), indent=2))


# ===========================
# VERSION
# ===========================

def handle_version(args, cfg):
    print("pytenable-was version 1.0.0")


# ----------------------------------------------------------------------
# ARGUMENT PARSER
# ----------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="tenable-was",
        description="CLI for Tenable Web Application Scanning (WAS) v2"
    )

    sub = parser.add_subparsers(dest="command")

    # CONFIGS
    configs = sub.add_parser("configs")
    configs_sub = configs.add_subparsers(dest="subcommand")

    c_list = configs_sub.add_parser("list")
    c_list.set_defaults(func=handle_configs_list)

    c_get = configs_sub.add_parser("get")
    c_get.add_argument("template_id")
    c_get.set_defaults(func=handle_configs_get)

    c_export = configs_sub.add_parser("export")
    c_export.add_argument("template_id")
    c_export.add_argument("--csv", action="store_true")
    c_export.add_argument("--json", action="store_true")
    c_export.set_defaults(func=handle_configs_export)

    # TEMPLATES
    templates = sub.add_parser("templates")
    tpl = templates.add_subparsers(dest="subcommand")

    t_list = tpl.add_parser("list")
    t_list.set_defaults(func=handle_templates_list)

    t_get = tpl.add_parser("get")
    t_get.add_argument("user_template_id")
    t_get.set_defaults(func=handle_templates_get)

    t_create = tpl.add_parser("create")
    t_create.add_argument("--config-file", required=True)
    t_create.set_defaults(func=handle_templates_create)

    t_update = tpl.add_parser("update")
    t_update.add_argument("user_template_id")
    t_update.add_argument("--config-file", required=True)
    t_update.set_defaults(func=handle_templates_update)

    t_delete = tpl.add_parser("delete")
    t_delete.add_argument("user_template_id")
    t_delete.set_defaults(func=handle_templates_delete)

    t_export = tpl.add_parser("export")
    t_export.add_argument("user_template_id")
    t_export.add_argument("--csv", action="store_true")
    t_export.add_argument("--json", action="store_true")
    t_export.set_defaults(func=handle_templates_export)

    # SCANS
    scans = sub.add_parser("scans")
    scans_sub = scans.add_subparsers(dest="subcommand")

    s_list = scans_sub.add_parser("list")
    s_list.add_argument("--show-owner", action="store_true")
    s_list.set_defaults(func=handle_scans_list)

    s_get = scans_sub.add_parser("get")
    s_get.add_argument("scan_id")
    s_get.set_defaults(func=handle_scans_get)

    s_export = scans_sub.add_parser("export")
    s_export.add_argument("scan_id")
    s_export.add_argument("--json", action="store_true")
    s_export.set_defaults(func=handle_scans_export)

    # CONFIG COMMANDS
    config = sub.add_parser("config")
    config_sub = config.add_subparsers(dest="subcommand")

    k = config_sub.add_parser("keys")
    k.set_defaults(func=handle_config_keys)

    p = config_sub.add_parser("proxy")
    p.set_defaults(func=handle_config_proxy)

    s = config_sub.add_parser("show")
    s.set_defaults(func=handle_config_show)

    # VERSION
    ver = sub.add_parser("version")
    ver.set_defaults(func=handle_version)

    return parser


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    cfg = Config.load()
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args, cfg)
    except TenableAPIError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
