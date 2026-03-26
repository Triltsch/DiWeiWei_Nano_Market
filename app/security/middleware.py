"""Middleware helpers for transport security enforcement."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp


def parse_csv_values(raw: str) -> tuple[str, ...]:
    """Parse a comma-separated value string into a normalized tuple."""
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def get_effective_request_scheme(request: Request, trusted_proxies: set[str]) -> str:
    """Return effective request scheme, honoring trusted proxy forwarding headers."""
    direct_client_ip = request.client.host if request.client else ""

    if direct_client_ip in trusted_proxies:
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        if forwarded_proto:
            return forwarded_proto.split(",")[0].strip().lower()

    return request.url.scheme.lower()


class TLSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect non-TLS requests for protected API paths.

    Protected paths are only enforced when middleware is enabled.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool,
        protected_path_prefixes: tuple[str, ...],
        trusted_proxies: set[str],
        allowed_hosts: frozenset[str] = frozenset(),
        redirect_status_code: int = 307,
    ) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._protected_path_prefixes = protected_path_prefixes
        self._trusted_proxies = trusted_proxies
        self._allowed_hosts = allowed_hosts
        self._redirect_status_code = redirect_status_code

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._enabled or not self._is_protected_path(request.url.path):
            return await call_next(request)

        effective_scheme = get_effective_request_scheme(request, self._trusted_proxies)
        if effective_scheme == "https":
            return await call_next(request)

        # Guard against open redirect: only redirect when Host is in the configured
        # allowlist.  If no allowlist is configured, allow all (backward-compatible
        # behaviour for local development).
        if self._allowed_hosts and request.url.hostname not in self._allowed_hosts:
            return await call_next(request)

        https_url = request.url.replace(scheme="https")
        return RedirectResponse(url=str(https_url), status_code=self._redirect_status_code)

    def _is_protected_path(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self._protected_path_prefixes)
