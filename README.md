# Incident Management System (IMS) - Zeotap SRE Intern Assignment

**Vishal Jena** | vishaljena2001@gmail.com | +91 9265710767
GitHub: https://github.com/kernal05/ims-zeotap

## Quick Start

```bash
docker compose up --build
```

- Frontend Dashboard: http://localhost
- Swagger API Docs: http://localhost/docs
- Health Check: http://localhost/health
- Backend Direct: http://localhost:8000

## Architecture
[ Alert Sources: Prometheus / Datadog / CloudWatch ]
|
POST /api/incidents/alerts
|
[ FastAPI Async Backend - Python 3.12 ]
/              |              PostgreSQL        MongoDB          Redis
(Incidents+RCA)  (Raw payloads)  (Cache+PubSub)
|
[ React + Vite Dashboard ]
^
[ nginx :80 ]

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend | Python + FastAPI | Fully async, auto Swagger docs |
| Primary DB | PostgreSQL 15 | ACID transactions, one RCA per incident at DB level |
| Raw Storage | MongoDB 7 | Schemaless, Datadog/Prometheus shapes coexist |
| Cache/Queue | Redis 7 | Sub-ms reads, debounce TTL keys, pub/sub |
| Frontend | React + Vite | Production build, zero runtime overhead |
| Proxy | nginx | Single port 80, routes /api to backend |
| Packaging | Docker Compose | One command starts all 6 services |

## Test It Yourself

### 1. Create an incident
```bash
curl -X POST http://localhost/api/incidents/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "DB Down",
    "description": "Database not responding to queries",
    "severity": "P1",
    "service_affected": "database",
    "alert_source": "prometheus"
  }'
```
Expected: `{"incident_id":"...","raw_alert_id":"...","status":"open"}`

### 2. Test debouncing
Send same service_affected twice within 10 seconds:
```bash
curl -X POST http://localhost/api/incidents/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"DB Down again","description":"Still not responding","severity":"P1","service_affected":"database","alert_source":"prometheus"}'
```
Expected: `{"status":"debounced","message":"Signal linked to existing incident"}`

### 3. Test rate limiting
```bash
for i in $(seq 1 101); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost/api/incidents/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"Spam","description":"Rate limit test signal","severity":"P3","service_affected":"payments","alert_source":"test"}' &
done
wait
```
Expected: 429 after 100 requests

### 4. Full workflow test (copy-paste as one block)
```bash
ID=$(curl -s -X POST http://localhost/api/incidents/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"Test incident","description":"Testing full lifecycle","severity":"P1","service_affected":"auth","alert_source":"datadog"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['incident_id'])")

echo "Created incident: $ID"

curl -s -X PATCH http://localhost/api/incidents/$ID/status \
  -H "Content-Type: application/json" -d '{"status":"investigating"}'

curl -s -X PATCH http://localhost/api/incidents/$ID/status \
  -H "Content-Type: application/json" -d '{"status":"mitigating"}'

curl -s -X PATCH http://localhost/api/incidents/$ID/status \
  -H "Content-Type: application/json" -d '{"status":"resolved"}'

# This should FAIL - no RCA yet
curl -s -X PATCH http://localhost/api/incidents/$ID/status \
  -H "Content-Type: application/json" -d '{"status":"closed"}'

# Submit RCA
curl -s -X POST http://localhost/api/incidents/$ID/rca \
  -H "Content-Type: application/json" \
  -d '{"root_cause":"Connection pool exhausted","timeline":"14:00 alert, 14:15 fixed","fix_applied":"Increased pool size","prevention":"Added monitoring","written_by":"vishal"}'

# Now close works
curl -s -X PATCH http://localhost/api/incidents/$ID/status \
  -H "Content-Type: application/json" -d '{"status":"closed"}'
```

### 5. Run unit tests
```bash
docker exec ims_backend pytest tests/ -v
```
Expected: 5 passed

### 6. Run failure simulation
```bash
bash sample_data.sh
```

### 7. Watch live throughput metrics
```bash
docker logs ims_backend -f | grep "Signals"
```

### 8. Get stats
```bash
curl http://localhost/api/incidents/stats/summary | python3 -m json.tool
```

## Backpressure - How We Handle 10,000 Signals/sec

| Layer | Mechanism | Effect |
|-------|-----------|--------|
| 1 | Redis INCR rate limit | HTTP 429 instantly, zero DB writes |
| 2 | Redis SETEX debounce 10s | Duplicates go to MongoDB only |
| 3 | Redis as write buffer | DB slowness does not affect ingestion |
| 4 | Async FastAPI + SQLAlchemy | 1000+ concurrent, never blocks |

## Workflow State Machine
OPEN -> INVESTIGATING -> MITIGATING -> RESOLVED -> CLOSED

Invalid transitions return HTTP 400. CLOSED blocked without complete RCA.

## Hybrid Auto-Assignment

| Service | Assigned To |
|---------|------------|
| database | db_team |
| payments | payments_team |
| auth | auth_team |
| cache | infra_team |
| Unknown + P1 | oncall_sre |
| Unknown + P2 | backend_team |
| Unknown + P3 | monitoring_team |

Manual assignment via PATCH overrides auto-assignment.

## Unit Tests

| Test | What It Proves |
|------|---------------|
| test_close_without_rca | Cannot close without RCA |
| test_close_with_empty_root_cause | Incomplete RCA rejected |
| test_close_with_complete_rca | Complete RCA allows close |
| test_valid_transitions | All valid state transitions pass |
| test_invalid_transitions | Invalid transitions correctly blocked |

## Services

| Service | Port | Purpose |
|---------|------|---------|
| nginx | 80 | Reverse proxy, single entry point |
| backend | 8000 | FastAPI async API |
| postgres | 5432 | Incidents + RCA source of truth |
| mongodb | 27017 | Raw alerts + audit log |
| redis | 6379 | Cache + debounce + rate limit |
| frontend | - | React dashboard served via nginx |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/incidents/alerts | Ingest signal with debouncing and rate limiting |
| GET | /api/incidents | List all incidents with allowed transitions |
| GET | /api/incidents/{id} | Get incident (Redis cached 5 min TTL) |
| GET | /api/incidents/{id}/signals | Raw signals from MongoDB |
| PATCH | /api/incidents/{id}/status | Update status (state machine enforced) |
| POST | /api/incidents/{id}/rca | Submit RCA (all 5 fields required) |
| GET | /api/incidents/stats/summary | Total, open, P1 count, avg MTTR |
| GET | /api/incidents/stats/timeseries | Hourly incident counts by severity |
| GET | /health | Health check |
