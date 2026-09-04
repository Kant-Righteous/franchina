"""Local-only API key management CLI for the FranChina MCP.

Run on the server shell, for example:

    python -m franchina_mcp.keys create --name "Zhengyi" --scope rates:write
    python -m franchina_mcp.keys list
    python -m franchina_mcp.keys revoke <key_id>
    python -m franchina_mcp.keys disable <key_id>
    python -m franchina_mcp.keys enable <key_id>

This tool is deliberately not exposed through MCP and performs no network
I/O; it only touches the local auth database (FRANCHINA_MCP_AUTH_DB_PATH).
Keys must never be created or revoked through GitHub Actions.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from .api_keys import ApiKeyRepository
from .config import resolve_auth_database_path


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive number of days")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m franchina_mcp.keys",
        description="Manage local API keys for api-key mode.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="create a new API key")
    create.add_argument("--name", required=True, help="owner name shown by `list`")
    create.add_argument(
        "--scope",
        action="append",
        default=[],
        metavar="SCOPE",
        help="scope to grant; repeatable, e.g. --scope rates:write",
    )
    create.add_argument(
        "--expires-in-days",
        type=_positive_int,
        default=None,
        metavar="DAYS",
        help="optional expiry counted from creation",
    )

    subparsers.add_parser("list", help="list keys (without secrets)")

    revoke = subparsers.add_parser("revoke", help="permanently disable a key")
    revoke.add_argument("key_id")
    enable = subparsers.add_parser("enable", help="re-enable a disabled key")
    enable.add_argument("key_id")
    disable = subparsers.add_parser("disable", help="disable a key temporarily")
    disable.add_argument("key_id")
    return parser


def _run_create(repository: ApiKeyRepository, args: argparse.Namespace) -> None:
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=args.expires_in_days)
        if args.expires_in_days is not None
        else None
    )
    record, plaintext_key = repository.create(
        name=args.name, scopes=args.scope, expires_at=expires_at
    )
    print("Created API key")
    print(f"  Name:     {record.name}")
    print(f"  Key ID:   {record.key_id}")
    print(f"  Scopes:   {record.scope_display}")
    print(f"  Expires:  {record.expires_at or 'never'}")
    print()
    print(plaintext_key)
    print()
    print("Store this key now: it is shown only once and cannot be recovered.")


def _run_list(repository: ApiKeyRepository) -> None:
    keys = repository.list_keys()
    if not keys:
        print("No API keys.")
        return
    for record in keys:
        state = "enabled" if record.enabled else "revoked"
        print(f"{record.key_id}  {state}")
        print(f"    name: {record.name}")
        print(f"    scopes: {record.scope_display}")
        print(f"    created: {record.created_at}")
        print(f"    expires: {record.expires_at or 'never'}")
        print(f"    last used: {record.last_used_at or 'never'}")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = ApiKeyRepository(resolve_auth_database_path())

    if args.command == "create":
        _run_create(repository, args)
        return 0
    if args.command == "list":
        _run_list(repository)
        return 0

    enabled = {"revoke": False, "disable": False, "enable": True}[args.command]
    if repository.set_enabled(args.key_id, enabled):
        action = {"revoke": "Revoked", "disable": "Disabled", "enable": "Enabled"}
        print(f"{action[args.command]} API key {args.key_id}")
        return 0
    print(f"No API key with id {args.key_id}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
