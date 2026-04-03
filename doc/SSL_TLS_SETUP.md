# SSL/TLS Setup for Reverse Proxy

This document describes local MVP setup for TLS termination with Nginx and self-signed certificates.

## 1. Generate self-signed certificate

Use Git Bash, WSL, or any shell with OpenSSL available.

```bash
sh docker/generate-ssl.sh
```

Expected output files:

- `docker/ssl/server.crt`
- `docker/ssl/server.key`

## 2. Start stack with reverse proxy

```bash
docker compose up -d
```

If `docker/ssl/server.crt` and `docker/ssl/server.key` are missing, the `reverse_proxy`
service generates a local self-signed certificate automatically on first start.

The reverse proxy is available on:

- HTTPS: `https://localhost`
- HTTP redirect endpoint: `http://localhost` (redirects to HTTPS)

## 3. Verify transport security

```bash
curl -k -I https://localhost/health
```

Expected headers include:

- `Strict-Transport-Security`
- `Content-Security-Policy`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- `Permissions-Policy`

Verify HTTP redirect:

```bash
curl -I http://localhost/api/v1/auth/login
```

Expected: `301` redirect to `https://...`

## 4. Verify rate limiting

Example login endpoint burst test:

```bash
for i in $(seq 1 8); do curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"bad"}'; done
```

Expected: `429` after threshold is reached.

## 5. Production path (Sprint 10+)

- Replace self-signed cert with ACME managed certs (Caddy or certbot based flow).
- Enable renewal monitoring and alerting before expiry.
- Run SSL Labs scan for public host and target A+.

## Troubleshooting

- Missing certificate files:
  - Re-run `sh docker/generate-ssl.sh`.
- Proxy fails to start:
  - Check `docker compose logs reverse_proxy`.
- Certificate warning in browser:
  - Expected for self-signed local certs.
