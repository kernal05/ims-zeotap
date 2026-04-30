#!/bin/bash
echo "Simulating RDBMS outage followed by MCP failure..."

curl -s -X POST http://localhost/api/incidents/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"PostgreSQL primary node down","description":"RDBMS primary node unresponsive, all write operations failing","severity":"P1","service_affected":"postgres","alert_source":"prometheus"}'

sleep 2

curl -s -X POST http://localhost/api/incidents/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"MCP Host failure cascade","description":"MCP host failing due to DB unavailability, distributed cache invalidated","severity":"P1","service_affected":"mcp-host","alert_source":"datadog"}'

sleep 2

curl -s -X POST http://localhost/api/incidents/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"Redis cache cluster degraded","description":"Cache cluster experiencing high miss rate due to upstream DB failure","severity":"P2","service_affected":"redis-cache","alert_source":"cloudwatch"}'

echo "Done! Check http://localhost for incidents."
