from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

DATABASE_PATH_ENV = "FRANCHINA_MCP_DB_PATH"
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "dev_rates.sqlite"

AUTH_DATABASE_PATH_ENV = "FRANCHINA_MCP_AUTH_DB_PATH"
DEFAULT_AUTH_DATABASE_PATH = Path(__file__).resolve().parents[1] / "dev_auth.sqlite"

MODE_ENV = "FRANCHINA_MCP_MODE"
LOOPBACK_MODE = "loopback"
CLOUDFLARE_ACCESS_MODE = "cloudflare-access"
API_KEY_MODE = "api-key"
KNOWN_MODES = (LOOPBACK_MODE, CLOUDFLARE_ACCESS_MODE, API_KEY_MODE)


def resolve_database_path() -> Path:
    return _resolve_configured_path(DATABASE_PATH_ENV, DEFAULT_DATABASE_PATH)


def resolve_auth_database_path() -> Path:
    return _resolve_configured_path(AUTH_DATABASE_PATH_ENV, DEFAULT_AUTH_DATABASE_PATH)


def _resolve_configured_path(environment_variable: str, default_path: Path) -> Path:
    configured_path = os.environ.get(environment_variable)
    if configured_path is None:
        return default_path

    configured_path = configured_path.strip()
    if not configured_path:
        raise ValueError(f"{environment_variable} cannot be empty")

    path = Path(configured_path).expanduser()
    if path.is_absolute():
        return path
    return Path.cwd() / path


def resolve_run_mode(environ: Mapping[str, str] | None = None) -> str:
    environment = os.environ if environ is None else environ
    raw = str(environment.get(MODE_ENV, "")).strip()
    if not raw or raw == LOOPBACK_MODE:
        return LOOPBACK_MODE
    if raw in (CLOUDFLARE_ACCESS_MODE, API_KEY_MODE):
        return raw
    raise SystemExit(
        f"{MODE_ENV} must be one of {', '.join(KNOWN_MODES)}; got: {raw!r}"
    )
