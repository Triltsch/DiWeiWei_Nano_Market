# Self-Hosted Mailserver for Auth Emails (Sprint 8 Add-on, Issue #123)

## Objective

This document specifies a production-oriented, self-hosted mail architecture for authentication emails in Docker environments, with Ubuntu as the target runtime platform.

Covered flows:
- Registration -> verification email
- Resend verification email
- Optional password reset email (if enabled in current sprint scope)

Not covered in this issue:
- Full production DNS automation
- Live cutover and go-live operations

## 1. Docker Compose Architecture (Design)

### 1.1 Services

Recommended service set for self-hosted SMTP delivery:
- `mailpit` (development/staging validation): SMTP sink + web UI for local and CI verification
- `postfix` (production relay candidate): outbound SMTP relay for auth mail delivery
- `dkim` (optional sidecar or integrated signer): DKIM signing for outbound domain mail

### 1.2 Network and Volume Design

Use an isolated internal network for mail components and app SMTP traffic:

```yaml
networks:
  app_internal:
    driver: bridge

volumes:
  mail_queue_data:
  mail_config:
  mail_logs:
```

Service-level expectations:
- `postfix` uses persistent queue volume (`mail_queue_data`) to avoid mail loss on container restart.
- Config and credentials are injected via mounted files or environment references, not hardcoded in Compose.
- Logs are persisted in a dedicated volume and optionally shipped to central logging.

### 1.3 Healthchecks

Mail services must expose health checks in Compose:
- SMTP health probe (TCP connect to SMTP port)
- Queue process liveness check
- Optional synthetic send probe in non-production

Example (conceptual):

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "nc -z localhost 587"]
  interval: 30s
  timeout: 5s
  retries: 5
  start_period: 20s
```

## 2. Auth Flow Integration Concept

### 2.1 Registration -> Verification Mail

1. User registers via backend auth endpoint.
2. Backend creates verification token with expiry.
3. Backend sends verification mail via SMTP client abstraction.
4. API response:
   - success without exposing SMTP internals
   - stable error mapping when SMTP send fails

### 2.2 Resend Verification

1. User requests resend endpoint.
2. System verifies user status (`unverified` only).
3. New token is generated or previous token rotated.
4. Verification mail is sent through same SMTP abstraction.
5. Rate limit and abuse protection are applied.

Current behavior vs target behavior:
- Current MVP behavior: `/auth/resend-verification-email` returns a verification token in the API response to support manual/local verification workflows.
- Target behavior after SMTP delivery integration: token value is not returned in API responses; success/failure is communicated via stable, product-safe response contracts.
- Recommended migration toggle: add an environment switch (for example `AUTH_RESEND_RETURN_TOKEN`) so development/test can keep explicit-token responses while production uses email-only delivery semantics.

### 2.3 Password Reset (Optional Scope)

If password reset is currently active:
- Reuse same mail transport abstraction and retry policy.
- Enforce short-lived token and one-time token consumption.
- Avoid leaking account existence in API responses.

## 3. Configuration Requirements (Environment + Secrets)

### 3.1 Mandatory SMTP Variables

The app should resolve all SMTP settings from environment variables (or equivalent secret injection):
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_ADDRESS`
- `SMTP_FROM_NAME`
- `SMTP_USE_TLS` (implicit TLS, usually 465)
- `SMTP_USE_STARTTLS` (usually 587)
- `SMTP_CONNECT_TIMEOUT_SECONDS`
- `SMTP_READ_TIMEOUT_SECONDS`
- `SMTP_RETRY_MAX_ATTEMPTS`
- `SMTP_RETRY_BACKOFF_SECONDS`

#### 3.1.1 TLS / STARTTLS Mode Semantics

`SMTP_USE_TLS` and `SMTP_USE_STARTTLS` are mutually exclusive transport mode flags:

- `SMTP_USE_TLS=true`, `SMTP_USE_STARTTLS=false`
  - Mode: implicit TLS (SMTPS)
  - Recommended port: `465`
- `SMTP_USE_TLS=false`, `SMTP_USE_STARTTLS=true`
  - Mode: STARTTLS upgrade
  - Recommended port: `587`
- `SMTP_USE_TLS=false`, `SMTP_USE_STARTTLS=false`
  - Mode: plain SMTP
  - Allowed only for local development/testing (for example Mailpit on `1025`)
- `SMTP_USE_TLS=true`, `SMTP_USE_STARTTLS=true`
  - Invalid configuration
  - Implementation must fail fast at startup with a clear configuration error

Port mismatch handling requirements:
- For implicit TLS mode, non-SMTPS ports should produce either a startup configuration error or an explicit warning with documented override behavior.
- For STARTTLS mode, the client must require successful TLS upgrade before sending credentials or message content.

Production security enforcement:
- Unencrypted SMTP mode (`SMTP_USE_TLS=false` and `SMTP_USE_STARTTLS=false`) must be rejected in production unless explicitly whitelisted for a non-production profile.

### 3.2 Secret Handling Rules

- No cleartext credentials committed to repository.
- Use local `.env` for development only, never with production secrets.
- For Ubuntu deployments, prefer Docker secrets or mounted secret files with least-privilege permissions.
- Rotate SMTP credentials periodically and after incident response.

## 4. Security Requirements

- Enforce TLS/STARTTLS for outbound SMTP transport.
- Reject insecure fallback unless explicitly allowed for local development.
- Log delivery metadata only (message type, destination domain hash, correlation id), not full PII payload.
- Protect against header injection by validating subject/from/to fields.
- Include SPF, DKIM, DMARC readiness in deployment checklist.

## 5. Operations and Delivery Checklist (Ubuntu Target)

### 5.1 Platform Readiness

- Ubuntu host patched and hardened.
- Docker Engine and Compose plugin at supported versions.
- Firewall allows required outbound SMTP and DNS ports only.

### 5.2 DNS and Domain Readiness

- MX records configured for sender domain when needed.
- Reverse DNS (PTR) aligned with sending host.
- SPF policy publishes allowed senders.
- DKIM keys generated, selectors published.
- DMARC policy defined and monitored.

### 5.3 Monitoring and Alerting

Track at minimum:
- Send success rate
- SMTP latency (`p50`, `p95`)
- Temporary vs permanent failures
- Retry queue depth and age
- Auth email throughput by template type

Alert examples:
- Send success rate below threshold for 5 minutes
- Queue depth growing continuously for 10 minutes
- SMTP auth failures above baseline

## 6. Failure Scenarios and Expected API Behavior

### 6.1 SMTP Down / Timeout

Expected behavior:
- API returns stable `503 Service Unavailable` for mail-dependent operation when immediate send is mandatory.
- Error payload uses product-safe message (no hostnames/secrets).
- Structured log emitted with correlation id.

### 6.2 SMTP Authentication Failure

Expected behavior:
- API maps to `503 Service Unavailable`.
- Error category tagged `smtp_auth_failed` in logs/metrics.
- Retry is not attempted for credential errors.

### 6.3 Temporary Provider Error (4xx SMTP)

Expected behavior:
- Retry according to bounded exponential backoff.
- If retries exhausted: stable 503 mapping and operational event emitted.

## 7. Test and QA Strategy

Minimum evidence required in container setup:

### 7.1 Unit Tests

- SMTP configuration parser and validation
- Mail payload builder (verification/reset templates)
- Error mapping from SMTP exceptions -> API responses

### 7.2 Integration Tests

- App + SMTP test container (for example `mailpit`) in Docker Compose
- Registration triggers verification email delivery observable in test mailbox
- Resend verification flow creates and delivers a fresh email
- Failure path tests for timeout/auth failure mapping

### 7.3 End-to-End Tests

- Full flow: register -> receive verification mail -> open link -> login success
- Optional: password reset request -> receive reset mail -> reset password -> login with new password
- Assertions include delivery timing and expected user-facing responses

## 8. Follow-Up Implementation Tasks

1. Add dedicated SMTP test service profile to `docker-compose.yml` for integration tests.
2. Introduce typed SMTP settings in backend config module with strict validation.
3. Implement backend mail transport abstraction with retry and metrics instrumentation.
  - Prefer an async SMTP client compatible with FastAPI async execution (recommended baseline: `aiosmtplib`).
4. Add auth-flow integration tests backed by mail test container.
5. Extend runbook with operational DNS and incident response procedures.
