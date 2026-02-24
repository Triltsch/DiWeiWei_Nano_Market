# 10 — Operations & Observability

---

## 1. Monitoring Architecture

```
Application
├─ Logs     → CloudWatch Logs
├─ Metrics  → CloudWatch Metrics
├─ Traces   → AWS X-Ray
└─ Events   → Event Bridge

Dashboards & Alerting
├─ CloudWatch Dashboards (Real-time)
├─ SNS Alerts (Email/SMS)
├─ PagerDuty Integration (Critical)
└─ Incident Management (Opsgenie)
```

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

### 3.3 CloudWatch Setup

```yaml
# Log Groups
/aws/ecs/nano-api
├─ Stream: nano-api-task-1
├─ Stream: nano-api-task-2
└─ Stream: nano-api-task-3

/aws/rds/nano-db
├─ error
├─ slowquery
└─ general

/aws/elasticache/nano-cache
└─ redis
```

**Retention:** 7 days (prod), 3 days (staging), 1 day (dev)

---

## 4. Distributed Tracing (X-Ray)

```
Request Flow:
1. Client → ALB (X-Ray interceptor)
2. ALB → ECS Task (FastAPI middleware)
3. FastAPI → RDS (X-Ray driver for SQL)
4. FastAPI → S3 (boto3 instrumented)
5. FastAPI → ElastiCache (Redis instrumented)

Result: Full request trace visible in X-Ray console
  - Bottleneck identification
  - Service dependencies
  - Error paths
```

**FastAPI Integration:**
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()
xray_recorder.configure(service='nano-api')

app = FastAPI()

# All HTTP, database, and AWS SDK calls now traced
```

---

## 5. Alerting Rules

### 5.1 Critical Alerts (Immediate Page)

```
1. Availability < 99% (1 hour cumulative)
   Action: On-call engineer paged

2. API Error Rate > 5% (5 minutes)
   Action: Page on-call

3. Database Replication Lag > 30 seconds
   Action: Page on-call

4. S3 Upload Failures > 10% (5 minutes)
   Action: Check S3 service status, page

5. ECS Task Crash Loop (>3 restarts in 5 min)
   Action: Page, auto-rollback if available
```

### 5.2 Warning Alerts (Email/Slack)

```
1. CPU Usage > 75% (sustained 10 min)
   Action: Check pending deploys, consider scale-up

2. Database Slow Queries (>500ms) increasing
   Action: Review query logs, analyze

3. Cache Hit Rate < 50%
   Action: Review cache strategy

4. Moderation Queue >100 items
   Action: Assign more reviewers

5. Daily Active Users declining >10%
   Action: Investigate churn
```

---

## 6. On-Call Runbooks

### 6.1 Critical: API Latency Spike

```
Alert: API Latency p99 > 3s (sustained 5 min)

DIAGNOSIS:
1. Check CloudWatch Metrics:
   - CPU utilization?
   - Memory pressure?
   - Network latency?
   - RDS slow queries?

2. Check X-Ray traces:
   - Which service is slow?
   - Database query time?
   - S3 calls?

3. Check Logs for errors:
   - grep "ERROR\|CRITICAL" /aws/ecs/nano-api

REMEDIATION:
- If CPU high: Scale-up ECS tasks (+1)
- If RDS slow: Check slow query log, add index
- If network: Check VPC flow logs
- If temporary: Often settles in <10 min (transient)

ESCALATION (>15 min):
- Page on-call architect
- Consider database failover
```

### 6.2 Critical: Database Unavailable

```
Alert: RDS connection failures in logs

DIAGNOSIS:
1. RDS Console → Check cluster status
2. Did Multi-AZ failover occur?
3. Check security group rules
4. Check parameter group changes

IMMEDIATE ACTION:
1. Try manual RDS reboot (triggers failover to replica)
2. If persistent: Restore from latest snapshot (30 min)

COMMUNICATION:
- Message on-call team
- Notify users (status page)
- Document incident
```

---

## 7. Backup & Disaster Recovery

### 7.1 Backup Strategy

```
RDS Aurora MySQL:
- Automated backups: Enabled (35-day retention)
- Backup window: 02:00-03:00 UTC (low traffic)
- Multi-region: Copy to dr-region (us-east-1) nightly

S3 Nanos:
- Versioning: Enabled (can restore old versions)
- Cross-region replication: Enabled (dr-region)
- Lifecycle: Transition to Glacier after 90 days

DynamoDB (if used for sessions):
- Point-in-time recovery: Enabled (35 days)
```

### 7.2 RTO & RPO

```
RTO (Recovery Time Objective): <1 hour
RPO (Recovery Point Objective): <15 minutes

If Primary Region (us-west-2) Fails:
1. Detect: CloudWatch alarm fails (2 min)
2. Decide: Page architect, assess (3 min)
3. Failover: Promote DR region's RDS read-replica (5 min)
4. DNS: Update CNAME to dr-region (1 min, cached ~5 min)
5. App: Restart in dr-region (3 min)
Total RTO: ~20 min

Data Lost: Max 15 min of chat messages (if not yet synced)
```

### 7.3 Disaster Recovery Drill

**Monthly (2nd Tuesday, 3 PM):**
```
1. Simulate primary region outage
2. Failover to DR region
3. Verify: API responsive, data consistent
4. Failback to primary
5. Document results & lessons
6. Public post-mortem if issues found
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
