from __future__ import annotations

import os
from pathlib import Path

DATABASE_PATH_ENV = "FRANCHINA_MCP_DB_PATH"
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "dev_rates.sqlite"


def resolve_database_path() -> Path:
    configured_path = os.environ.get(DATABASE_PATH_ENV)
    if configured_path is None:
        return DEFAULT_DATABASE_PATH

    configured_path = configured_path.strip()
    if not configured_path:
        raise ValueError(f"{DATABASE_PATH_ENV} cannot be empty")

    path = Path(configured_path).expanduser()
    if path.is_absolute():
        return path
    return Path.cwd() / path
