from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from mcp.server import MCPServer
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from . import __version__
from .api_keys import ApiKeyAuthenticator, ApiKeyMiddleware, ApiKeyRepository
from .cloudflare_access import (
    CloudflareAccessMiddleware,
    CloudflareAccessSettings,
    CloudflareAccessValidator,
)
from .config import (
    API_KEY_MODE,
    CLOUDFLARE_ACCESS_MODE,
    LOOPBACK_MODE,
    MODE_ENV,
    resolve_auth_database_path,
    resolve_database_path,
    resolve_run_mode,
)
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
    authorization: AuthorizationConfiguration | None = None,
    access_validator: CloudflareAccessValidator | None = None,
    api_key_authenticator: ApiKeyAuthenticator | None = None,
) -> None:
    if not public:
        if access_validator is not None or api_key_authenticator is not None:
            raise ValueError("authentication backends are only valid in public mode")
        return

    backends = sum(
        backend is not None
        for backend in (authorization, access_validator, api_key_authenticator)
    )
    if backends == 0:
        raise ValueError(
            "public mode requires one of: AuthSettings with resource_server_url "
            "and a TokenVerifier, a CloudflareAccessValidator, or an "
            "ApiKeyAuthenticator"
        )
    if backends > 1:
        raise ValueError(
            "public mode accepts exactly one authentication backend: an "
            "AuthorizationConfiguration, a CloudflareAccessValidator, or an "
            "ApiKeyAuthenticator"
        )
    if authorization is not None:
        authorization_is_complete = (
            isinstance(authorization.settings, AuthSettings)
            and authorization.settings.resource_server_url is not None
            and callable(getattr(authorization.token_verifier, "verify_token", None))
        )
        if not authorization_is_complete:
            raise ValueError(
                "public mode requires AuthSettings with resource_server_url and "
                "a TokenVerifier, a CloudflareAccessValidator, or an "
                "ApiKeyAuthenticator"
            )


def create_transport_security_settings(
    *,
    public: bool = False,
    authorization: AuthorizationConfiguration | None = None,
    access_validator: CloudflareAccessValidator | None = None,
    api_key_authenticator: ApiKeyAuthenticator | None = None,
) -> TransportSecuritySettings:
    _validate_public_mode(
        public=public,
        authorization=authorization,
        access_validator=access_validator,
        api_key_authenticator=api_key_authenticator,
    )
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
    access_validator: CloudflareAccessValidator | None = None,
    api_key_authenticator: ApiKeyAuthenticator | None = None,
    public: bool = False,
) -> MCPServer:
    _validate_public_mode(
        public=public,
        authorization=authorization,
        access_validator=access_validator,
        api_key_authenticator=api_key_authenticator,
    )
    if authorization is not None:
        authorization_notice = (
            "MCP HTTP requests require OAuth 2.1 bearer-token authorization."
        )
    elif access_validator is not None:
        authorization_notice = (
            "Public HTTP requests must pass Cloudflare Access; the origin "
            "cryptographically validates the Cf-Access-Jwt-Assertion header."
        )
    elif api_key_authenticator is not None:
        authorization_notice = (
            "Public HTTP requests require a per-user API key "
            "(Authorization: Bearer); write tools additionally require the "
            "rates:write scope."
        )
    else:
        authorization_notice = (
            "This loopback-only instance has no OAuth authorization and is not ready "
            "for a public reverse proxy; configure AuthSettings and TokenVerifier first."
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


def create_streamable_http_app(
    server: MCPServer,
    *,
    host: str = "127.0.0.1",
    streamable_http_path: str = "/mcp",
    stateless_http: bool = False,
    authorization: AuthorizationConfiguration | None = None,
    access_validator: CloudflareAccessValidator | None = None,
    api_key_authenticator: ApiKeyAuthenticator | None = None,
    max_request_body_bytes: int | None = None,
    public: bool = False,
) -> ASGIApp:
    """Build the streamable HTTP app, wrapped for authentication in public mode."""
    _validate_public_mode(
        public=public,
        authorization=authorization,
        access_validator=access_validator,
        api_key_authenticator=api_key_authenticator,
    )
    app = server.streamable_http_app(
        streamable_http_path=streamable_http_path,
        stateless_http=stateless_http,
        transport_security=create_transport_security_settings(
            public=public,
            authorization=authorization,
            access_validator=access_validator,
            api_key_authenticator=api_key_authenticator,
        ),
        host=host,
    )
    if access_validator is not None:
        app = CloudflareAccessMiddleware(app, access_validator)
    elif api_key_authenticator is not None:
        middleware_options = (
            {} if max_request_body_bytes is None
            else {"max_request_body_bytes": max_request_body_bytes}
        )
        app = ApiKeyMiddleware(app, api_key_authenticator, **middleware_options)
    return app


mcp = create_server()


def _run_loopback(repository: RatesRepository) -> None:
    server = create_server(repository, public=False)
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8765,
        streamable_http_path="/mcp",
        transport_security=create_transport_security_settings(public=False),
    )


def _run_cloudflare_access(repository: RatesRepository) -> None:
    import uvicorn

    settings = CloudflareAccessSettings.from_env()
    validator = CloudflareAccessValidator(settings)
    server = create_server(repository, public=True, access_validator=validator)
    app = create_streamable_http_app(
        server,
        host="127.0.0.1",
        access_validator=validator,
        public=True,
    )
    uvicorn.run(app, host="127.0.0.1", port=8765)


def _run_api_key(repository: RatesRepository) -> None:
    import uvicorn

    authenticator = ApiKeyAuthenticator(
        ApiKeyRepository(resolve_auth_database_path())
    )
    server = create_server(
        repository, public=True, api_key_authenticator=authenticator
    )
    app = create_streamable_http_app(
        server,
        host="127.0.0.1",
        api_key_authenticator=authenticator,
        public=True,
    )
    uvicorn.run(app, host="127.0.0.1", port=8765)


def main() -> None:
    repository = RatesRepository(resolve_database_path())
    mode = resolve_run_mode()
    if mode == CLOUDFLARE_ACCESS_MODE:
        _run_cloudflare_access(repository)
    elif mode == API_KEY_MODE:
        _run_api_key(repository)
    elif mode == LOOPBACK_MODE:
        _run_loopback(repository)
    else:  # pragma: no cover - resolve_run_mode only returns known modes
        raise SystemExit(f"Unsupported {MODE_ENV}: {mode!r}")


if __name__ == "__main__":
    main()
