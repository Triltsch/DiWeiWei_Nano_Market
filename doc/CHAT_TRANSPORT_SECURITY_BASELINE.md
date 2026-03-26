# Chat Transport Security Baseline (Issue #102)

This document defines the MVP transport-security baseline for chat-related traffic.

## Protected paths

TLS enforcement applies to:

- `/api/v1/chats/**`
- `/api/v1/auth/login`

Behavior:

- If a protected request is not HTTPS, API redirects to HTTPS (`307 Temporary Redirect`).
- When the request comes through a trusted reverse proxy, `X-Forwarded-Proto` is used to detect HTTPS.

## Reverse proxy requirements

Your reverse proxy (Nginx/Caddy) must forward these headers:

- `X-Forwarded-For`
- `X-Forwarded-Proto`
- `Host`

Example Nginx snippet (minimum):

```nginx
location / {
    proxy_pass http://app:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

server {
    listen 80;
    server_name your-domain.example;
    return 301 https://$host$request_uri;
}
```

## Rate limiting

Two endpoint-level fixed-window limits are active:

- Login: `/api/v1/auth/login`
- Chat message send: `POST /api/v1/chats/{session_id}/messages`

Both return `429 Too Many Requests` plus `Retry-After` when exceeded.

## Configuration

All settings are environment-driven (`app.config.Settings`):

- `SECURITY_ENFORCE_TLS` (default: `false`)
- `SECURITY_TLS_REDIRECT_INSECURE` (default: `true`)
- `SECURITY_TLS_PROTECTED_PATHS` (default: `/api/v1/chats,/api/v1/auth/login`)
- `SECURITY_TRUSTED_PROXIES` (default: `127.0.0.1,::1`)
- `RATE_LIMIT_LOGIN_MAX_REQUESTS` (default: `10`)
- `RATE_LIMIT_LOGIN_WINDOW_SECONDS` (default: `60`)
- `RATE_LIMIT_CHAT_MESSAGE_MAX_REQUESTS` (default: `30`)
- `RATE_LIMIT_CHAT_MESSAGE_WINDOW_SECONDS` (default: `60`)

Recommended production baseline:

- set `SECURITY_ENFORCE_TLS=true`
- configure `SECURITY_TRUSTED_PROXIES` to your ingress/reverse-proxy source IPs
- keep `SECURITY_TLS_REDIRECT_INSECURE=true`

## Smoke checks

### Insecure request is redirected

```bash
curl -i http://<host>/api/v1/auth/login
```

Expected: `307` or `301` redirect to `https://...`

### HTTPS via trusted proxy header is accepted

```bash
curl -i http://<app-internal-host>/api/v1/auth/login \
  -H "X-Forwarded-Proto: https" \
  -H "X-Forwarded-For: <client-ip>"
```

Expected: endpoint result (not TLS redirect), when caller IP is in `SECURITY_TRUSTED_PROXIES`.

### Rate limit is enforced

Send repeated login or chat-message requests above threshold inside one window.

Expected: `429 Too Many Requests` with `Retry-After` response header.
