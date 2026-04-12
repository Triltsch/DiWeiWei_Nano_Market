"""Regression checks for reverse proxy hardening assets.

Scope:
- Ensure Nginx proxy config keeps required TLS, header and rate-limit directives.
- Ensure SSL generation script and compose integration stay present.
"""

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_nginx_default_conf_contains_required_security_controls() -> None:
    """Nginx config includes TLS, security headers and endpoint-specific rate limits."""
    content = (_repo_root() / "docker" / "nginx" / "default.conf").read_text(encoding="utf-8")

    required_fragments = (
        "listen 443 ssl;",
        "http2 on;",
        "ssl_protocols TLSv1.2 TLSv1.3;",
        "ssl_session_tickets off;",
        "limit_req_status 429;",
        "error_page 429 @rate_limited;",
        "add_header Retry-After 60 always;",
        "Strict-Transport-Security",
        "Content-Security-Policy",
        "X-Frame-Options",
        "Permissions-Policy",
        "limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;",
        "limit_req_zone $binary_remote_addr zone=register:10m rate=3r/m;",
        "limit_req_zone $binary_remote_addr zone=search:10m rate=30r/m;",
        "limit_req_zone $binary_remote_addr zone=chat_messages:10m rate=60r/m;",
        "limit_req_zone $binary_remote_addr zone=nano_ratings:10m rate=10r/m;",
        "limit_req_zone $binary_remote_addr zone=api_default:10m rate=100r/m;",
        "limit_req_status 429;",
        "location /api/v1/auth/login",
        "location /api/v1/auth/register",
        "location /api/v1/search",
        "location ~ ^/api/v1/chats/[^/]+/messages$",
        "location ~ ^/api/v1/nanos/[^/]+/ratings$",
        "location /api/",
        "location /api/v1/admin",
        "error_page 429 @rate_limited;",
        "location @rate_limited {",
        "add_header Retry-After 60 always;",
        "ssl_session_tickets off;",
        "location /ws/",
        "location /grafana/",
        "proxy_set_header X-Forwarded-Prefix /grafana;",
        "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
        "proxy_set_header X-Forwarded-Proto $scheme;",
    )

    for fragment in required_fragments:
        assert fragment in content


def test_ssl_script_and_compose_proxy_service_are_present() -> None:
    """Compose includes reverse proxy service and script path is stable."""
    root = _repo_root()
    compose_content = (root / "docker-compose.yml").read_text(encoding="utf-8")

    assert "reverse_proxy:" in compose_content
    assert "docker/Dockerfile.nginx" in compose_content
    assert '- "80:80"' in compose_content
    assert '- "443:443"' in compose_content
    assert "--no-check-certificate" in compose_content
    assert "https://127.0.0.1/health" in compose_content
    assert "subjectAltName=DNS:localhost,IP:127.0.0.1" in compose_content

    script_path = root / "docker" / "generate-ssl.sh"
    assert script_path.exists()
    script_content = script_path.read_text(encoding="utf-8")
    assert "subjectAltName=DNS:localhost,IP:127.0.0.1" in script_content
