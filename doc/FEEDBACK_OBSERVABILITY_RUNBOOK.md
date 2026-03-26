# Feedback Observability Runbook

This runbook covers the feedback monitoring signals added for ratings, comments, and feedback moderation.

## Signals

- Dashboard: `Feedback Flows` in Grafana (`http://localhost:3001`)
- Prometheus alerts:
  - `FeedbackHighServerErrorRate`
  - `FeedbackSlowAPI`
- Metrics:
  - `feedback_requests_total`
  - `feedback_request_duration_seconds`
  - `feedback_moderation_decisions_total`

## Triage Steps

1. Open the `Feedback Flows` dashboard and identify the failing series by `feedback_type` and `operation`.
2. Check whether the issue is isolated to one path:
   - `rating create|read|update|moderate`
   - `comment create|list|update|moderate`
   - `moderation_queue list`
3. Correlate with generic API health in the `API Overview` dashboard.
4. Confirm infrastructure health in `DB Health` and `Infrastructure Health`.

## Prometheus Queries

Use these directly in Prometheus or Grafana Explore.

```promql
sum by (feedback_type, operation) (rate(feedback_requests_total[5m]))
```

```promql
100 * (
  sum by (feedback_type, operation) (rate(feedback_requests_total{outcome="server_error"}[5m]))
  /
  clamp_min(sum by (feedback_type, operation) (rate(feedback_requests_total[5m])), 0.001)
)
```

```promql
histogram_quantile(
  0.95,
  sum by (le, feedback_type, operation) (rate(feedback_request_duration_seconds_bucket[5m]))
)
```

```promql
sum by (feedback_type, decision) (increase(feedback_moderation_decisions_total[1h]))
```

## Common Failure Patterns

- `comment create` or `rating create` latency spike:
  - Inspect PostgreSQL health and response times first.
  - Review application logs for transaction retries or storage/network stalls.
- `comment moderate` or `rating moderate` server errors:
  - Check audit-log writes and database connectivity.
  - Verify moderator/admin authentication and JWT role claims.
- `moderation_queue list` slowdown:
  - Check the volume of pending ratings/comments.
  - Review slow query behavior against `nano_ratings` and `nano_comments`.

## Immediate Actions

1. Reproduce against the affected endpoint via Swagger or a local API client.
2. Review container status with `docker compose ps`.
3. Check app logs for the time window of the alert.
4. If database or Redis is unhealthy, stabilize infrastructure before retrying feedback flows.
5. If only one feedback operation is failing, scope the rollback or hotfix to that route instead of disabling the full monitoring stack.