"""Shared ASGI primitives for origin-side public-mode authentication gates.

Both the Cloudflare Access middleware and the API key middleware gate requests
with the same policy: machine-local loopback traffic is only protected on the
MCP endpoint itself (so deployment health checks keep working), while any
other Host must authenticate on every path. The helpers here are the single
implementation of that policy's low-level pieces.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit

# Host values this origin accepts for machine-local traffic (the systemd
# deployment health check and cloudflared on the same host). Everything else
# counts as public traffic and always requires authentication.
LOOPBACK_HOSTNAMES = frozenset({"127.0.0.1", "localhost", "::1"})


def is_loopback_host(host: str) -> bool:
    if not host:
        return False
    try:
        hostname = urlsplit(f"//{host}").hostname
    except ValueError:
        return False
    return hostname is not None and hostname.lower() in LOOPBACK_HOSTNAMES


def header_value(scope: dict[str, Any], name_bytes: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key.lower() == name_bytes:
            return value.decode("latin-1")
    return None


async def send_json_error(send: Any, status: int, payload: dict[str, str]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"cache-control", b"no-store"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
