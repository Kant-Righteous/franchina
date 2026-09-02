from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from mcp.server import MCPServer
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import __version__
from .config import resolve_database_path
from .database import RatesRepository
from .models import (
    ExchangeRateBatch,
    SaveExchangeRatesInput,
    SaveExchangeRatesResult,
)

LOOPBACK_ALLOWED_HOSTS = (
    "127.0.0.1",
    "127.0.0.1:*",
    "localhost",
    "localhost:*",
    "[::1]",
    "[::1]:*",
)
PUBLIC_ALLOWED_HOSTS = (
    "mcp.franchina.qzz.io",
    "mcp.franchina.qzz.io:*",
)
PUBLIC_ALLOWED_ORIGINS = ("https://mcp.franchina.qzz.io",)


@dataclass(frozen=True, slots=True)
class AuthorizationConfiguration:
    """Official MCP OAuth resource-server settings and bearer-token verifier."""

    settings: AuthSettings
    token_verifier: TokenVerifier


def _validate_public_mode(
    *,
    public: bool,
    authorization: AuthorizationConfiguration | None,
) -> None:
    authorization_is_complete = (
        authorization is not None
        and isinstance(authorization.settings, AuthSettings)
        and authorization.settings.resource_server_url is not None
        and callable(getattr(authorization.token_verifier, "verify_token", None))
    )
    if public and not authorization_is_complete:
        raise ValueError(
            "public mode requires AuthSettings with resource_server_url and a TokenVerifier"
        )


def create_transport_security_settings(
    *,
    public: bool = False,
    authorization: AuthorizationConfiguration | None = None,
) -> TransportSecuritySettings:
    _validate_public_mode(public=public, authorization=authorization)
    allowed_hosts = list(LOOPBACK_ALLOWED_HOSTS)
    allowed_origins: list[str] = []
    if public:
        allowed_hosts.extend(PUBLIC_ALLOWED_HOSTS)
        allowed_origins.extend(PUBLIC_ALLOWED_ORIGINS)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def create_server(
    repository: RatesRepository | None = None,
    *,
    authorization: AuthorizationConfiguration | None = None,
    public: bool = False,
) -> MCPServer:
    _validate_public_mode(public=public, authorization=authorization)
    authorization_notice = (
        "MCP HTTP requests require OAuth 2.1 bearer-token authorization."
        if authorization is not None
        else (
            "This loopback-only instance has no OAuth authorization and is not ready "
            "for a public reverse proxy; configure AuthSettings and TokenVerifier first."
        )
    )
    server = MCPServer(
        "FranChina Exchange Rates",
        version=__version__,
        description=(
            "Stores normalized EUR and USD exchange rates whose only meaning is "
            "1 currency = rate CNY."
        ),
        instructions=(
            "Each record must mean 1 currency = rate CNY, where currency is EUR or "
            "USD. If a source quotes CNY per 100 foreign-currency units, divide it "
            f"by 100 before calling the tool. {authorization_notice}"
        ),
        auth=authorization.settings if authorization is not None else None,
        token_verifier=(
            authorization.token_verifier if authorization is not None else None
        ),
    )
    active_repository = repository
    repository_lock = Lock()

    def get_repository() -> RatesRepository:
        nonlocal active_repository
        if active_repository is None:
            with repository_lock:
                if active_repository is None:
                    active_repository = RatesRepository(resolve_database_path())
        return active_repository

    @server.tool()
    def save_exchange_rates(
        rates: ExchangeRateBatch,
    ) -> SaveExchangeRatesResult:
        """Save normalized EUR/USD rates where 1 currency = rate CNY."""
        request = SaveExchangeRatesInput(rates=rates)
        return get_repository().save_exchange_rates(request.rates)

    @server.custom_route("/health", methods=["GET"])
    async def health(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return server


mcp = create_server()


def main() -> None:
    repository = RatesRepository(resolve_database_path())
    server = create_server(repository, public=False)
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8765,
        streamable_http_path="/mcp",
        transport_security=create_transport_security_settings(public=False),
    )


if __name__ == "__main__":
    main()
