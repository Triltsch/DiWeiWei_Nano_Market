# 10 — Operations & Observability (Open-Source Stack)

---

## 1. Monitoring Architecture (Prometheus + Grafana + Loki)

```
Application
├─ Application Metrics  → Prometheus
├─ System Metrics       → Node Exporter → Prometheus
├─ PostgreSQL Metrics   → postgres_exporter → Prometheus
├─ Redis Metrics        → redis_exporter → Prometheus
├─ Structured Logs      → Loki
├─ Container Logs       → Promtail → Loki
└─ Traces               → Jaeger or Zipkin

Visualization & Alerting
├─ Prometheus Dashboards (Real-time)
├─ Grafana Dashboards (Rich UI)
├─ Prometheus AlertManager (Email/Webhook)
├─ Slack/Email Integrations
└─ Incident Management (Optional: Alertmanager → PagerDuty bridge)
```

### Components Overview

**Prometheus:** Metrics collection & storage (TSDB)
- Scrapes endpoints every 15 seconds
- Retains data for 30 days (configurable)
- Query language: PromQL

**Grafana:** Visualization & dashboarding
- Rich UI for dashboards
- Multiple data sources (Prometheus, Loki, etc.)
- Alert evaluation engine (optional, can use Prometheus)

**Loki:** Log aggregation (lightweight alternative to ELK)
- Indexes labels, not full text (more efficient)
- Compatible with Prometheus label scheme
- Query language: LogQL

**Jaeger/Zipkin:** Distributed tracing (Phase 1)
- Request flow visualization
- Latency breakdown
- Issue identification

---

## 2. Key Metrics & SLOs

### ApplicationMetrics

| Metrik | Target (SLO) | Alert Threshold |
|--------|--------------|-----------------|
| **Availability** | 99.95% | <99% (1h) |
| **API Latency p95** | <1s | >2s (5 min) |
| **API Latency p99** | <2s | >3s (5 min) |
| **Error Rate (5xx)** | <0.5% | >1% (5 min) |
| **Error Rate (4xx)** | <2% | >5% (5min) |

### DatabaseMetrics

| Metrik | Target | Alert |
|--------|--------|-------|
| **CPU Utilization** | <70% | >80% |
| **Storage** | <80% used | >85% |
| **Connections** | <100 / 150 | >140 |
| **Query Latency p95** | <100ms | >200ms |
| **Replication Lag** | <1s | >5s |

### Infrastructure

| Metrik | Target | Alert |
|--------|--------|-------|
| **ECS CPU** | <70% | >75% |
| **ECS Memory** | <80% | >85% |
| **ALB Latency** | <50ms | >100ms |
| **S3 Upload Errors** | 0% | any |

### Business Metrics

| Metrik | Target | Alert |
|--------|--------|-------|
| **Daily Active Users (DAU)** | >100 | <50 (trending) |
| **New Nanos/Day** | >5 | <2 (alert) |
| **Chat Response Time** | <24h avg | >48h (alert) |
| **Moderation Queue** | <24h | >48h (alert) |

---

## 3. Logging Strategy

### 3.1 Log Levels

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: Detailed info for debugging
logger.debug(f"User {user_id} searched for '{query}'")

# INFO: General info events
logger.info(f"Nano {nano_id} published by {creator_id}")

# WARNING: Potentially harmful situations
logger.warning(f"Rate limit approaching: {ip_address}")

# ERROR: Error conditions (recoverable)
logger.error(f"Failed to upload to S3: {bucket}/{key}", exc_info=True)

# CRITICAL: Critical conditions (unrecoverable)
logger.critical(f"Database connection pool exhausted")
```

### 3.2 Structured Logging

```json
{
  "timestamp": "2025-02-24T10:15:00.123Z",
  "level": "INFO",
  "service": "nano-api",
  "action": "NANO_PUBLISHED",
  "nano_id": "abc-123",
  "creator_id": "xyz-789",
  "duration_ms": 245,
  "http_status": 201,
  "http_method": "POST",
  "http_path": "/api/v1/nanos",
  "user_id": "xyz-789",
  "request_id": "req-12345",
  "trace_id": "trace-abc",
  "correlation_id": "corr-xyz",
  "error": null
}
```

### 3.3 Loki Setup (Log Aggregation)

```yaml
# docker-compose.yml additions
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - ./loki-config.yml:/etc/loki/local-config.yml:ro
    - loki_data:/loki
  command: -config.file=/etc/loki/local-config.yml

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock
    - ./promtail-config.yml:/etc/promtail/config.yml:ro
  command: -config.file=/etc/promtail/config.yml
  depends_on:
    - loki
```

**Promtail Configuration:**
```yaml
# promtail-config.yml
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    static_configs:
      - targets:
          - localhost
        labels:
          job: docker
          __path__: /var/lib/docker/containers/*/*-json.log
    pipeline_stages:
      - json:
          expressions:
            timestamp: '.time'
            message: '.log'
            level: '.attrs.level'
      - labels:
          level:
          job:

  - job_name: nginx
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx
          __path__: /var/log/nginx/access.log
    pipeline_stages:
      - regex:
          expression: '^(?P<ip>\S+) (?P<method>\S+) (?P<path>\S+) (?P<status>\S+)'
      - labels:
          status:
          path:
```

**Log Retention:** Configure in Loki to keep 30 days

### 3.4 Structured Logging in FastAPI

```python
# app/logging_config.py
import json
import logging
import sys
from pythonjsonlogger import jsonlogger

# JSON-formatted structured logging
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage in FastAPI
from fastapi import FastAPI, Request
import logging
from uuid import uuid4

app = FastAPI()
logger = logging.getLogger(__name__)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    
    response = await call_next(request)
    
    logger.info("http_request_completed", extra={
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "client_host": request.client.host,
    })
    
    return response

# In other modules:
logger.info("action_completed", extra={
    "action": "NANO_PUBLISHED",
    "nano_id": nano.id,
    "creator_id": creator_id,
    "duration_ms": elapsed,
})
```

**Loki Query Examples:**
```
# View all ERROR logs from FastAPI
{job="docker", level="ERROR"}

# Count 5xx errors by path
sum by (path) (count_over_time({job="nginx"} |= "5" [5m]))

# Average latency by status code
avg by (status) (nginx_request_duration_seconds)
```

---

## 4. Distributed Tracing (Jaeger - Phase 1)

```
Request Flow:
1. Client → Nginx (Jaeger middleware optional)
2. Nginx → FastAPI (Jaeger instrumentation)
3. FastAPI → PostgreSQL (py_db instrumentation)
4. FastAPI → Redis (redis instrumentation)
5. FastAPI → Elasticsearch (instrumented client)

Result: Full request trace visible in Jaeger UI
  - Service map visualization
  - Bottleneck identification
  - Error paths & latencies
  - Trace comparison
```

**FastAPI Integration (using OpenTelemetry):**
```python
# app/tracing.py
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Setup Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument frameworks
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
RedisInstrumentor().instrument(client=redis_client)

tracer = trace.get_tracer(__name__)

# Usage
with tracer.start_as_current_span("process_nano") as span:
    span.set_attribute("nano_id", nano_id)
    nano = await nano_service.process(nano_id)
    span.set_attribute("status", "completed")
```

**Docker Compose Addition:**
```yaml
jaeger:
  image: jaegertracing/all-in-one:latest
  environment:
    - COLLECTOR_ZIPKIN_HOST_PORT=:9411
  ports:
    - "5775:5775/udp"  # Zipkin compact thrift
    - "6831:6831/udp"  # Jaeger compact thrift
    - "16686:16686"    # UI
    - "14268:14268"    # Jaeger collector HTTP
```

**Jaeger Queries:**
- Service map: View all service dependencies
- Trace search: Filter by service, operation, tags
- Latency analysis: p99, p95, p50 by operation
- Error rate: Filter by error tag

---

## 5. Alerting Rules (Prometheus AlertManager)

### 5.1 Alert Configuration

```yaml
# prometheus-rules.yml
groups:
  - name: application_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          (sum(rate(http_requests_total{status=~"5.."}[5m])) /
           sum(rate(http_requests_total[5m]))) > 0.05
        for: 5m
        annotations:
          summary: "High error rate: {{ $value | humanizePercentage }}"
          description: "API error rate > 5% for 5 minutes"
        labels:
          severity: critical

      - alert: HighLatency
        expr: |
          histogram_quantile(0.99, 
            rate(http_request_duration_seconds_bucket[5m])
          ) > 3
        for: 5m
        annotations:
          summary: "High API latency (p99)"
          description: "p99 latency > 3s"
        labels:
          severity: warning

  - name: database_alerts
    interval: 30s
    rules:
      - alert: HighDiskUsage
        expr: |
          (pg_database_size_bytes / (1024^3)) > 80
        annotations:
          summary: "Database size > 80GB"
          labels:
            severity: warning

      - alert: HighConnectionCount
        expr: |
          pg_connections_used > 90
        annotations:
          summary: "DB connections > 90% of max"
          labels:
            severity: warning

      - alert: ReplicationLag
        expr: |
          pg_replication_lag_seconds > 30
        for: 2m
        annotations:
          summary: "Replication lag > 30 seconds"
          labels:
            severity: critical

  - name: infrastructure_alerts
    interval: 30s
    rules:
      - alert: HighCPUUsage
        expr: |
          100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          labels:
            severity: warning

      - alert: LowMemory
        expr: |
          (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.1
        for: 5m
        annotations:
          summary: "Low memory available"
          labels:
            severity: warning

      - alert: DiskFull
        expr: |
          (node_filesystem_avail_bytes{fstype!~"tmpfs"} / node_filesystem_size_bytes) < 0.1
        for: 10m
        annotations:
          summary: "Disk {{ $labels.device }} < 10% free"
          labels:
            severity: critical

  - name: business_alerts
    interval: 5m
    rules:
      - alert: LowDAU
        expr: |
          deriv(nano_uploads_total[24h]) < 2
        for: 24h
        annotations:
          summary: "Low daily uploads (< 2 per day)"
          labels:
            severity: warning

      - alert: ModerationQueueBacklog
        expr: |
          moderation_queue_size > 100
        for: 30m
        annotations:
          summary: "Moderation queue > 100 items"
          labels:
            severity: warning
```

### 5.2 AlertManager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: '${SLACK_WEBHOOK_URL}'

route:
  receiver: 'team'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

  routes:
    - match:
        severity: critical
      receiver: 'critical-page'
      continue: true

    - match:
        severity: warning
      receiver: 'team-email'

receivers:
  - name: 'team'
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'

  - name: 'critical-page'
    email_configs:
      - to: 'oncall@nano-marketplace.de'
        from: 'alerts@nano-marketplace.de'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alerts@example.com'
        auth_password: '${SMTP_PASSWORD}'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_KEY}'

  - name: 'team-email'
    email_configs:
      - to: 'team@nano-marketplace.de'
        from: 'alerts@nano-marketplace.de'
        smarthost: 'smtp.example.com:587'
```

---

## 6. On-Call Runbooks

### 6.1 Critical: API Latency Spike

```
Alert: API Latency p99 > 3s (sustained 5 min)

DIAGNOSIS:
1. Check Prometheus Metrics (http://prometheus:9090):
   - node_cpu_usage_percent? (high = scale app)
   - container_memory_usage_bytes? (high = memory leak)
   - process_resident_memory_bytes? (memory growth?)

2. Check Grafana Dashboards (http://grafana:3000):
   - API Performance dashboard
   - Infrastructure dashboard

3. Check Jaeger Traces (http://jaeger:16686):
   - Service: nano-api
   - Operation: POST /api/v1/nanos or GET /api/v1/nanos
   - Identify which span is slow (app, db, network)

4. Check Loki Logs (http://grafana:3000 → Loki datasource):
   - {job="docker", level="ERROR"}
   - {job="nginx"} | = "5"

REMEDIATION:
- If app CPU high: Scale containers
  docker-compose up -d --scale app=5

- If PostgreSQL slow:
  docker exec nano_postgres_1 psql -U nano_user -d nano_db -c \
    "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
  Check EXPLAIN ANALYZE and add indexes if needed

- If memory leak: Check application logs, restart container:
  docker-compose restart app

- If network latency:
  docker exec app1 ping postgres  (check connectivity)
  docker exec app1 curl elasticsearch:9200/_cluster/health

ESCALATION (>15 min):
- Review recent deployments: git log --oneline -10
- Consider rollback if recent changes
- Check external dependencies status
```

### 6.2 Critical: Database Unavailable

```
Alert: PostgreSQL connection failures

DIAGNOSIS:
1. Check container status:
   docker ps | grep postgres
   docker logs <container-id>

2. Check connectivity:
   docker exec nano_postgres_1 pg_isready

3. Check disk space:
   docker exec nano_postgres_1 df -h /var/lib/postgresql/data

4. Check configuration:
   docker exec nano_postgres_1 psql -U nano_user -d nano_db -c "SHOW max_connections;"

REMEDIATION:
- If container down:
  docker-compose up -d postgres

- If disk full:
  rm old backups: rm /backups/db_*.sql.gz (keep recent ones)
  Run vacuum: docker exec nano_postgres_1 vacuumdb -z

- If connection limit reached:
  Edit docker-compose.yml env: POSTGRES_MAX_CONNECTIONS=200
  Restart: docker-compose restart postgres

- If corrupted (last resort):
  docker-compose stop app
  ./scripts/restore_db.sh /backups/db_latest.sql.gz
  docker-compose up -d

COMMUNICATION:
- Message on-call team (Slack channel)
- Update status page if public services down
- Document incident in runbook
```

---

## 7. Backup & Disaster Recovery (Open-Source)

### 7.1 Backup Strategy

```
PostgreSQL:
- Automated backups: Daily via cron script
- Backup location: /backups (local) + synced to MinIO
- Retention: 30 days (delete older backups)
- Backup window: 02:00 UTC (low traffic)

MinIO Object Storage:
- Versioning: Enabled (can restore old versions)
- Bucket replication: Replicate to external MinIO (if Phase 2)
- Lifecycle: Transition old audit logs after 2 years

Script (Bash):
  #!/bin/bash
  pg_dump -h postgres -U nano_user nano_db | gzip > /backups/db_$(date +%Y%m%d).sql.gz
  docker cp /backups/db_*.sql.gz <minio>:/data/nano-marketplace-backups/
```

### 7.2 RTO & RPO

```
RTO (Recovery Time Objective): <1 hour
RPO (Recovery Point Objective): <15 minutes

If Primary Region Fails:
1. Detect: Health checks fail (2 min)
2. Decide: Page architect, assess (3 min)
3. Failover: Restore PostgreSQL from backup (10 min)
4. DNS: Update DNS entry to new IP (1 min, cached ~5 min)
5. App: Restart containers on new server (3 min)
Total RTO: ~30 min

Data Lost: Max 15 min of chat messages (if not persisted to DB)
```

### 7.3 Disaster Recovery Drill

**Monthly (2nd Tuesday, 3 PM):**.
```
1. Simulate primary server outage
2. Restore database from backup to new server
3. Verify: API responsive, data consistent
4. Failback to primary
5. Document results & improvement areas
```

### 7.4 Restore Procedure

```bash
# 1. Get latest backup
ls -ltr /backups/db_*.sql.gz | tail -1

# 2. Create new PostgreSQL instance
docker run -d --name postgres_restore -v /backups:/backups \
  -e POSTGRES_DB=nano_db -e POSTGRES_USER=nano_user \
  postgres:15

# 3. Restore from backup
gunzip < /backups/db_20250224.sql.gz | \
  docker exec -i postgres_restore psql -U nano_user -d nano_db

# 4. Verify data
docker exec postgres_restore psql -U nano_user -d nano_db \
  -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM nanos;"

# 5. Point app to new DB
docker-compose env DATABASE_URL=postgresql://nano_user:pass@postgres_restore/nano_db
docker-compose restart app
```

---

## 8. Performance Tuning

### 8.1 Database Optimization

```sql
-- Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM nanos WHERE title LIKE '%excel%';

-- Add indexes on frequent filters
CREATE INDEX idx_nanos_status ON nanos(status)
  WHERE status = 'published';

CREATE INDEX idx_nano_rating ON nanos(average_rating DESC);

-- Monitor index usage
SELECT * FROM information_schema.statistics
  WHERE table_schema = 'nano_prod';

-- Connection pool tuning
-- SQLAlchemy pool_size: 20, pool_recycle: 3600
```

### 8.2 Caching Strategy

```
Layer 1: Browser Cache
  - Static assets: 1 year (versioned)
  - API responses: Cache-Control: max-age=300

Layer 2: CloudFront CDN
  - TTL: 600 sec (10 min)
  - Invalidate on content change

Layer 3: Application Cache (Redis)
  - Session: 1 hour TTL
  - Search results: 30 min TTL
  - User profile: 1 hour TTL
  - Eviction: LRU policy

Layer 4: Database Query Cache
  - Not recommended long-term (consistency risk)
  - Use for analytics queries only (aggregates)
```

### 8.3 Content Delivery Optimization

```
Nano ZIPs:
- Compression: zip already compressed, ok
- CDN: CloudFront distribution for S3
- Parallel downloads: Support Range requests

Static Assets (React, CSS, JS):
- Minification + Gzip in build pipeline
- Source maps for prod debugging (separate storage)
- CSS critical path inlined (above-the-fold)
```

---

## 9. Incident Management

### 9.1 Severity Levels

```
SEV-1 (Critical): Service Down / Major Impact
- Page on-call + manager
- Status page: "Major Outage"
- All-hands response

SEV-2 (High): Degraded Performance / Partial Impact
- Page on-call
- Status page: "Degraded Performance"
- Normal prioritization

SEV-3 (Medium): Feature Broken / Limited Impact
- Create ticket
- Status page: "Investigating"
- Normal priority

SEV-4 (Low): Minor Issue
- No alert
- Create ticket for backlog
```

### 9.2 Incident Response Process

```
DETECT (T+0 min)
└─ Alert fired → On-call paged

RESPOND (T+2 min)
├─ On-call: Acknowledge alert
├─ On-call: Assess severity
└─ On-call: Notify stakeholders

DIAGNOSE (T+5 min)
├─ Check logs / metrics
├─ Identify root cause
└─ Determine impact

MITIGATE (T+15 min)
├─ Apply temporary fix (if known)
├─ Scale infrastructure
└─ Roll back recent changes

COMMUNICATE (T+5,15,30 min)
├─ Status updates every 15 min
├─ Post-mortem 24h later
└─ Action items assigned

RESOLVE (T+60 min target)
├─ Service restored
├─ Status page: "Resolved"
└─ Schedule post-mortem
```

### 9.3 Post-Mortem Template

```markdown
# Incident Post-Mortem

**Date:** 2025-02-24  
**Time:** 10:15 - 11:30 UTC  
**Duration:** 75 Minuten  
**Severity:** SEV-1

## Summary
[2-3 sentence brief description]

## Timeline
- T+0: Alert fired (Error rate > 5%)
- T+3: On-call confirmed issue
- T+15: Root cause identified (DB connection pool exhausted)
- T+45: Workaround applied (scale ECS to 5 tasks)
- T+75: Permanent fix deployed (increase pool_size from 15 to 25)

## Root Cause
[Detailed analysis: what broke, why, how we missed it]

## Impact
- Users affected: ~500 (8% of active)
- Data lost: 0 (due to AsyncIO buffering)
- Revenue impact: $0 (no transactions)

## Resolution
[How it was fixed]

## Action Items (Assigned, Due Date)
- [  ] Review connection pool configuration (Sarah, Feb 28)
- [  ] Add load test for 1000 concurrent users (John, Mar 3)
- [  ] Implement circuit breaker pattern (Maria, Mar 7)

## Lessons Learned
- We don't test connection pool exhaustion scenarios
- Alert threshold was too lenient
- Playbook was outdated
```

---

## 10. Capacity Planning

```
2025 Q1: 1,000 DAU
└─ Infrastructure: 2 ECS tasks, db.t4g.medium RDS

2025 Q2: 5,000 DAU
└─ Infrastructure: 3-4 ECS tasks (auto-scaling), db.t4g.large

2025 Q3: 10,000 DAU
└─ Infrastructure: 5-8 ECS tasks, db.r6g.large (memory-optimized)

2026 Q1: 50,000 DAU
└─ Infrastructure: 10-20 ECS tasks, Microservices with separate DBs
```

**Scaling Trigger:** When 70% resource utilization reached sustainably

---

## 11. Operations Checklist (Weekly)

- [ ] Review error logs for anomalies
- [ ] Check database replication lag <1s
- [ ] Verify backup completion (last 3 days)
- [ ] Monitor uptime (99.95%+ ?)
- [ ] Capacity: Are we trending towards limits?
- [ ] Security: Any suspicious access patterns?
- [ ] Cost review: Any unexpected AWS bills?

---

## Referenzen

- [05 — Systemarchitektur](./05_system_architecture.md) (Infrastructure)
- [06 — Security & Compliance](./06_security_compliance.md) (Audit Logs)
- [09 — Teststrategie](./09_testing_quality.md) (Performance Tests)
