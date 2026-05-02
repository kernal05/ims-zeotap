# Incident Management System (IMS)

Mission-Critical Incident Management System for Zeotap assignment.

## Quick Start
docker compose up --build

## Access
- Frontend: http://localhost
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost/docs
- Health Check: http://localhost/health

## Architecture
[ Alert Sources ] -> POST /api/incidents/alerts
        |
[ FastAPI Backend ]
   /        |        \
PostgreSQL  MongoDB   Redis
(incidents) (raw)   (cache+pubsub)
        |
[ React Dashboard ]
        ^
  [ nginx:80 ]

## Tech Stack
Backend     : Python + FastAPI (async, auto Swagger)
Primary DB  : PostgreSQL (ACID transactions, relational)
Raw Storage : MongoDB (schemaless raw alert payloads)
Cache/Queue : Redis (sub-ms cache + pub/sub)
Frontend    : React + Vite (production build)
Proxy       : nginx (single entry point)
Packaging   : Docker Compose (one command startup)

## Backpressure Handling
1. Rate Limiting - Max 100 signals/10s per component (HTTP 429 on breach)
2. Debouncing - Same component within 10s = 1 incident, rest linked in MongoDB
3. Redis Buffer - Signals hit Redis first before PostgreSQL
4. Async Processing - FastAPI never blocks, all DB ops are async

## Design Patterns
- Strategy Pattern - Alerting logic per component (RDBMS=P1, Cache=P2, API=P1)
- State Pattern - Workflow state machine with valid transition enforcement

## API Endpoints
POST   /api/incidents/alerts         - Ingest signal
GET    /api/incidents                - List all incidents
GET    /api/incidents/{id}           - Get incident (Redis cached)
GET    /api/incidents/{id}/signals   - Raw signals from MongoDB
PATCH  /api/incidents/{id}/status    - Update status (state machine enforced)
POST   /api/incidents/{id}/rca       - Submit RCA
GET    /api/incidents/stats/summary  - Dashboard stats
GET    /health                       - Health check

## Bonus Non-Functional Items
- Rate limiting per component (429 on breach)
- Debouncing within 10-second window
- Throughput metrics every 5 seconds to console
- Retry logic for DB writes (3 attempts with backoff)
- Redis cache with 5-minute TTL
- Production build frontend via nginx

## Simulate Failure
bash sample_data.sh

## Run Tests
cd backend && pip install pytest --break-system-packages && pytest tests/ -v

## How To Test Everything End-to-End

### Step 1 - Start the system
docker compose up --build -d

### Step 2 - Verify health
curl http://localhost/health

### Step 3 - Simulate failure scenario
bash sample_data.sh

### Step 4 - Open dashboard
http://localhost

### Step 5 - Run unit tests
docker exec ims_backend pytest tests/ -v

### Step 6 - Test debouncing
curl -X POST http://localhost/api/incidents/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","description":"Test debounce","severity":"P1","service_affected":"payments-api","alert_source":"test"}'

### Step 7 - Check Swagger docs
http://localhost/docs
