"""Transport security middleware tests for TLS-only protected paths.

Scope:
- insecure requests to protected paths are redirected to HTTPS
- trusted proxy HTTPS forwarding headers are accepted
- untrusted forwarded headers are ignored
"""

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security.middleware import TLSRedirectMiddleware


def _create_tls_app(trusted_proxies: set[str]) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        TLSRedirectMiddleware,
        enabled=True,
        protected_path_prefixes=("/api/v1/chats", "/api/v1/auth/login"),
        trusted_proxies=trusted_proxies,
    )

    @app.post("/api/v1/auth/login")
    async def login() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/v1/chats/{session_id}/messages")
    async def create_message(session_id: str) -> dict[str, str]:
        return {"session_id": session_id}

    @app.get("/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_insecure_login_request_redirects_to_https() -> None:
    """HTTP login request to protected path is redirected to HTTPS."""
    client = TestClient(_create_tls_app(trusted_proxies={"127.0.0.1", "::1"}))

    response = client.post("/api/v1/auth/login", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://")


def test_trusted_forwarded_proto_https_allows_chat_message_post() -> None:
    """Trusted proxy with X-Forwarded-Proto=https can access protected chat path."""
    client = TestClient(_create_tls_app(trusted_proxies={"testclient"}))

    response = client.post(
        f"/api/v1/chats/{uuid4()}/messages",
        headers={"x-forwarded-proto": "https"},
    )

    assert response.status_code == 200


def test_untrusted_forwarded_proto_is_ignored() -> None:
    """X-Forwarded-Proto from an untrusted client does not bypass TLS enforcement."""
    client = TestClient(_create_tls_app(trusted_proxies=set()))

    response = client.post(
        "/api/v1/auth/login",
        headers={"x-forwarded-proto": "https"},
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://")
