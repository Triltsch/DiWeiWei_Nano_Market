# Monitoring Setup (Prometheus/Grafana Baseline)

This document describes the reproducible local/staging-like monitoring baseline and the
feedback-flow observability extension added in Sprint 6.

## Scope

- Prometheus metrics collection
- Grafana dashboard provisioning
- FastAPI application metrics via `/metrics`
- Feedback-flow business metrics via `/metrics`
- PostgreSQL metrics via `postgres_exporter`
- Redis metrics via `redis_exporter`
- Baseline alert rules (`HighErrorRate`, `SlowAPI`)
- Feedback alert rules (`FeedbackHighServerErrorRate`, `FeedbackSlowAPI`)

## Included Components

The stack is defined in `docker-compose.yml`:

- `prometheus` (`http://localhost:9090`)
- `grafana` (`http://localhost:3001`)
- `postgres_exporter` (`http://localhost:9187/metrics`)
- `redis_exporter` (`http://localhost:9121/metrics`)

Application and storage services provide scrape targets via compose networking:

- `app:8000/metrics`
- `postgres_exporter:9187/metrics`
- `redis_exporter:9121/metrics`

## Reproducible Compose Workflow

```powershell
docker compose pull
docker compose up -d --remove-orphans
docker compose ps
```

To stop and clean up:

```powershell
docker compose down
```

## Validation Checklist

1. Prometheus target status:
   - Open `http://localhost:9090/targets`
   - Ensure jobs `fastapi`, `postgres_exporter`, `redis_exporter` are `UP`

2. FastAPI metrics endpoint:
   - Open `http://localhost:8000/metrics`
   - Confirm Prometheus text format output (`# HELP`, `# TYPE` lines)

3. Grafana dashboards:
   - Open `http://localhost:3001`
   - Login with `admin/admin` (dev defaults)
   - Verify dashboards exist in folder `DiWeiWei`:
     - `API Overview`
     - `DB Health`
     - `Feedback Flows`
     - `Infrastructure Health`

4. Alert rules:
   - Open `http://localhost:9090/rules`
   - Confirm rules:
     - `HighErrorRate`
     - `SlowAPI`
     - `FeedbackHighServerErrorRate`
     - `FeedbackSlowAPI`

5. Feedback metrics visibility:
   - Open `http://localhost:8000/metrics`
   - Confirm feedback metrics are present:
     - `feedback_requests_total`
     - `feedback_request_duration_seconds`
     - `feedback_moderation_decisions_total`

## Files and Configuration

- Prometheus scrape + rules:
  - `monitoring/prometheus/prometheus.yml`
  - `monitoring/prometheus/alerts.yml`
- Grafana provisioning:
  - `monitoring/grafana/provisioning/datasources/datasource.yml`
  - `monitoring/grafana/provisioning/dashboards/dashboards.yml`
- Dashboards:
  - `monitoring/grafana/dashboards/api-overview.json`
  - `monitoring/grafana/dashboards/db-health.json`
  - `monitoring/grafana/dashboards/feedback-flows.json`
  - `monitoring/grafana/dashboards/infrastructure-health.json`

## Credentials and Secrets

- This baseline intentionally uses local development credentials (`admin/admin` for Grafana and compose defaults for internal services).
- No production credentials are committed in this setup.
- For non-local environments, override credentials via environment variables:
  - `GRAFANA_ADMIN_USER`
  - `GRAFANA_ADMIN_PASSWORD`
  - Existing DB/Redis credentials from `.env` / compose environment

## Alert Rule Notes

- `HighErrorRate` triggers when the 5xx ratio exceeds 5% over a 5-minute rate window for 2 minutes.
- `SlowAPI` triggers when p95 request latency exceeds 1 second over a 5-minute rate window for 2 minutes.
- `FeedbackHighServerErrorRate` triggers when feedback endpoints exceed 5% server errors over a 10-minute window for 10 minutes.
- `FeedbackSlowAPI` triggers when feedback endpoint p95 latency exceeds 750ms over a 10-minute window for 10 minutes.

Both rule sets are designed as baseline operational signals for MVP and can be tightened in later hardening phases.
