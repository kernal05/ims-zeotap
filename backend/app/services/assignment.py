SERVICE_OWNERS = {
    "payments": "payments_team",
    "payments-api": "payments_team",
    "auth": "auth_team",
    "auth-service": "auth_team",
    "cache": "infra_team",
    "redis-cache": "infra_team",
    "database": "db_team",
    "postgres": "db_team",
    "mcp-host": "platform_team",
    "cdn": "infra_team",
}

SEVERITY_FALLBACK = {
    "P1": "oncall_sre",
    "P2": "backend_team",
    "P3": "monitoring_team",
}

def auto_assign_incident(service: str, severity: str) -> str:
    service = service.lower()
    if service in SERVICE_OWNERS:
        return SERVICE_OWNERS[service]
    return SEVERITY_FALLBACK.get(severity, "oncall_sre")
