# Incident Management System (IMS)

Mission-Critical Incident Management System for Zeotap assignment.

## Quick Start
docker-compose up --build

## Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Tech Stack
- Backend: Python + FastAPI (async)
- Database: PostgreSQL (incidents + RCA)
- NoSQL: MongoDB (raw alerts + audit logs)
- Cache/Queue: Redis (caching + pub/sub)
- Frontend: React + Vite
- Packaging: Docker Compose

## Workflow States
OPEN -> INVESTIGATING -> MITIGATING -> RESOLVED -> CLOSED
Closing requires a complete RCA report (enforced at API level).

## API Endpoints
POST   /api/incidents/alerts        - Ingest alert
GET    /api/incidents               - List all incidents
GET    /api/incidents/{id}          - Get incident
PATCH  /api/incidents/{id}/status   - Update status
POST   /api/incidents/{id}/rca      - Submit RCA
GET    /api/incidents/stats/summary - Dashboard stats
GET    /health                      - Health check
