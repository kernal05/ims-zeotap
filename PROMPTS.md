# Prompts, Spec and Plans

## Assignment Interpretation

The goal was to build a Mission-Critical IMS that handles high-volume
signal ingestion, manages incident lifecycle, enforces RCA, and provides
a real-time dashboard.

## System Design Plan

### Phase 1 - Architecture Decision
- FastAPI for async backend (handles 10k signals/sec without blocking)
- PostgreSQL for structured incident + RCA data (ACID transactions)
- MongoDB for raw alert payloads (schemaless, different alert shapes)
- Redis for caching hot incidents + pub/sub real-time alerts
- React + Vite for frontend SPA dashboard
- nginx as reverse proxy (single port 80 entry point)
- Docker Compose for one-command startup

### Phase 2 - Backend Design
- Signal ingestion endpoint with debouncing via Redis TTL keys
- Rate limiter using Redis INCR + EXPIRE pattern
- State machine using VALID_TRANSITIONS dictionary
- Strategy pattern for alerting (abstract base + concrete strategies)
- Async SQLAlchemy engine to prevent event loop blocking
- MongoDB audit log for every state change

### Phase 3 - Resilience Design
- Retry decorator with configurable attempts and backoff
- Redis cache with 5-minute TTL, invalidated on updates
- Throughput metrics printed every 5 seconds via asyncio task
- Docker healthcheck on PostgreSQL before backend starts
- restart: unless-stopped on all services

### Phase 4 - Frontend Design
- React functional components with hooks
- Auto-refresh every 30 seconds
- Filter by status and severity
- Modal for incident detail + RCA submission
- Stats bar showing total, open, P1 active, avg MTTR

## Key Design Decisions

### Why debounce with Redis TTL?
Redis SETEX with 10-second expiry is atomic and microsecond-fast.
No database round-trip needed to check for existing incidents.
The key pattern debounce:{service_affected} naturally groups by component.

### Why separate PostgreSQL and MongoDB?
PostgreSQL enforces the RCA constraint at database level via UNIQUE
foreign key. MongoDB stores raw payloads without needing schema changes
when new alert sources are added.

### Why Strategy Pattern for alerting?
Adding a new component type (e.g. Kubernetes pod) requires only adding
a new strategy class and registering it. No changes to existing code.
Open/Closed principle applied correctly.

### Why nginx reverse proxy?
Single entry point hides internal container ports. Frontend and backend
accessible from same origin (port 80), eliminating CORS complexity in
production. Industry standard pattern.

### Why production React build?
Vite dev server requires WebSocket for HMR which causes issues through
nginx proxy. Production build creates static files served directly by
nginx with zero runtime overhead.
