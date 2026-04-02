# SMTP Operations Runbook (Ubuntu)

Purpose: Operational runbook for DNS readiness, SMTP monitoring/alerting, incident response, and secrets rotation for the self-hosted authentication mail flow.

Scope:
- Ubuntu-targeted operations for SMTP delivery used by auth flows.
- Production-safe examples only (no real credentials, hostnames, or customer data).

## 1. DNS and Domain Readiness (Section 5.2)

Use this checklist before enabling production SMTP sends.

### 1.1 MX record

1. Create MX record for the sender domain.
2. Keep priority deterministic (single host: one MX record, multiple hosts: explicit preference values).

Example:
```dns
example.com.  300  IN  MX  10 mail.example.com.
```

Verify:
```bash
dig +short MX example.com
host -t MX example.com
```

Expected outcome: the configured MX target appears consistently from at least two DNS resolvers.

### 1.2 Reverse DNS (PTR)

1. Identify the public sending IP of the SMTP host.
2. Configure PTR at the provider level so IP resolves to the same hostname used in SMTP banner/EHLO.

Verify:
```bash
dig +short -x 203.0.113.10
host 203.0.113.10
```

Expected outcome: PTR resolves to `mail.example.com` and forward lookup for `mail.example.com` resolves back to the same IP.

### 1.3 SPF policy

1. Publish SPF TXT on the sender domain.
2. Keep policy explicit and minimal.

Example:
```dns
example.com.  300  IN  TXT  "v=spf1 mx ip4:203.0.113.10 -all"
```

Verify:
```bash
dig +short TXT example.com
host -t TXT example.com
```

Expected outcome: exactly one effective SPF record is published.

### 1.4 DKIM key and selector

Selector convention:
- Use `s<year><quarter>` (example: `s2026q2`) for predictable rotation cadence.

Generate keypair (OpenSSL):
```bash
mkdir -p dkim && cd dkim
openssl genrsa -out s2026q2.private 2048
openssl rsa -in s2026q2.private -pubout -out s2026q2.public
```

Create DNS TXT record:
```dns
s2026q2._domainkey.example.com.  300  IN  TXT  "v=DKIM1; k=rsa; p=<base64-public-key-without-whitespace>"
```

Verify:
```bash
dig +short TXT s2026q2._domainkey.example.com
host -t TXT s2026q2._domainkey.example.com
```

Expected outcome: published key matches the generated public key.

### 1.5 DMARC policy

1. Publish DMARC TXT record under `_dmarc`.
2. Start production with `p=quarantine` and move to stricter policy after monitoring stabilizes.

Example:
```dns
_dmarc.example.com.  300  IN  TXT  "v=DMARC1; p=quarantine; pct=100; adkim=s; aspf=s; rua=mailto:dmarc-reports@example.com"
```

Verify:
```bash
dig +short TXT _dmarc.example.com
host -t TXT _dmarc.example.com
```

Expected outcome: record is globally resolvable and parsed by deliverability tooling.

### 1.6 DNS readiness quick gate

Proceed to production only when all checks are true:
- MX record resolves and points to intended host.
- PTR is aligned with sending hostname.
- SPF publishes authorized sender paths.
- DKIM selector TXT exists and validates.
- DMARC policy exists with reporting address.

## 2. Monitoring and Alerting (Section 5.3)

### 2.1 Planned metrics (pending transport instrumentation; Issue #127)

Target state: expose and scrape the following metrics from SMTP transport once instrumentation is implemented:
- `smtp_send_total{status="success|failure",message_type="verification|resend|reset"}`
- `smtp_send_latency_seconds` histogram (use p50 and p95 views)
- `smtp_retry_queue_depth` gauge
- `smtp_auth_failures_total` counter

Note: As of this runbook version, these Prometheus metrics are not yet exported by `app/modules/mail/transport.py`. Until Issue #127 is implemented, use existing SMTP-related application logs and provider-side dashboards for delivery failures, latency, queue behavior, and authentication errors.

### 2.2 Prometheus alert rules (YAML)

```yaml
groups:
  - name: smtp-transport-alerts
    rules:
      - alert: SmtpSendSuccessRateLow
        expr: |
          (
            sum(rate(smtp_send_total{status="success"}[5m]))
            /
            clamp_min(sum(rate(smtp_send_total[5m])), 1)
          ) < 0.95
          and
          sum(rate(smtp_send_total[5m])) >= 0.1
        for: 5m
        labels:
          severity: warning
          service: app
          component: smtp
        annotations:
          summary: "SMTP send success rate below 95%"
          description: "Send success ratio over 5 minutes is below 0.95. Check provider health, queue depth, and auth status."

      - alert: SmtpRetryQueueDepthGrowing
        expr: |
          deriv(smtp_retry_queue_depth[10m]) > 0
        for: 10m
        labels:
          severity: warning
          service: app
          component: smtp
        annotations:
          summary: "SMTP retry queue depth is growing"
          description: "Retry queue depth shows a sustained increasing trend over 10 minutes. Investigate downstream SMTP availability and error categories."

      - alert: SmtpAuthFailuresHigh
        expr: |
          increase(smtp_auth_failures_total[1m]) > 5
        for: 2m
        labels:
          severity: critical
          service: app
          component: smtp
        annotations:
          summary: "SMTP authentication failures above 5/min"
          description: "SMTP auth failures exceed threshold. Validate credentials, account lock state, and auth mechanism negotiation."
```

### 2.3 Grafana dashboard panels

Create these baseline panels:
1. SMTP Success Ratio (5m)
   - Query: success/total ratio from `smtp_send_total`
   - Visualization: time series with alert threshold line at 0.95
2. SMTP Send Latency p50/p95
   - Query: `histogram_quantile` over `smtp_send_latency_seconds_bucket`
   - Visualization: time series (two lines) with p95 warning threshold
3. Retry Queue Depth
   - Query: `smtp_retry_queue_depth`
   - Visualization: time series + current stat
4. SMTP Auth Failures
  - Query: `increase(smtp_auth_failures_total[1m])`
   - Visualization: time series and incident marker annotations

## 3. Incident Response Procedures

### 3.1 SMTP down / timeout

Symptoms:
- Elevated send failures and latency.
- `SmtpSendSuccessRateLow` and queue growth alerts firing.

Response steps:
1. Confirm failure scope in metrics and app logs (error class, attempt count, timeout category).
2. Validate SMTP endpoint reachability from app container/host.
3. Switch to fallback/manual delivery mode according to team policy:
   - Pause automatic retries if queue is saturating infra.
   - Queue critical notifications for controlled replay.
4. Drain retry queue after recovery in controlled batches while monitoring success ratio and latency.
5. Document incident timeline and root cause.

### 3.2 SMTP auth failure

Symptoms:
- `smtp_auth_failures_total` spike.
- Auth errors in transport logs.

Immediate response:
1. Rotate `SMTP_PASSWORD` immediately (see Section 4).
2. Collect evidence:
   - Timestamp of first failure.
   - Current auth error messages/categories.
   - Related deployment/config changes.
3. Verify provider/account lock status and allowed auth methods.
4. If rotation fails, rollback to last known-good secret revision.
5. Confirm alert clears after credential validation.

### 3.3 DNS or deliverability degradation (bounce/spam)

Symptoms:
- Increased bounces or spam-folder placement while transport remains technically available.

Response steps:
1. Re-check SPF, DKIM, DMARC records with `dig` and external DNS resolvers.
2. Validate DKIM signing domain/selector alignment.
3. Review DMARC aggregate reports and provider postmaster dashboards.
4. Confirm PTR and HELO/EHLO hostname alignment remains valid.
5. Roll out corrective DNS policy updates and monitor for at least one full TTL period.

### 3.4 Docker container restart and queue preservation

Goal: prove queued mail is not lost across restarts.

Verification steps:
1. Confirm queue persistence volume exists:
   - Expected volume: `mail_queue_data`
2. Inspect volume attachment to SMTP service.
3. Restart SMTP container.
4. Verify queue depth and pending items are still present after restart.
5. Send a controlled test message and confirm queue processing resumes.

## 4. Secret Rotation Procedure (Section 3.2)

Rotate `SMTP_USERNAME` and/or `SMTP_PASSWORD` with minimal service impact.

1. Generate new SMTP credentials at provider/server side.
2. Update secret storage:
   - Production: Docker secrets or dedicated secret manager.
   - Never store real production credentials in `.env` committed to source control.
3. Restart only the `app` service so settings reload without full stack interruption.
4. Verify recovery within 2 minutes:
   - `smtp_send_total{status="success"}` resumes expected rate.
   - `smtp_auth_failures_total` returns to baseline.
5. Keep rollback path ready:
   - Restore prior known-good secret version if failures persist.

## 5. Operational Hygiene

- Never include real credentials, production hostnames, or customer email addresses in docs, logs, tickets, or screenshots.
- Use placeholder domains/IPs from documentation ranges (for example `example.com`, `203.0.113.0/24`).
- Keep this runbook updated whenever transport metrics, retry behavior, or auth flows change.