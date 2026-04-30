from abc import ABC, abstractmethod
from app.models.incident import Severity


# Abstract Strategy — defines the interface
class AlertStrategy(ABC):
    @abstractmethod
    def get_severity(self, signal: dict) -> Severity:
        pass

    @abstractmethod
    def get_alert_message(self, signal: dict) -> str:
        pass


# Concrete Strategy 1 — RDBMS failures are most critical
class RDBMSAlertStrategy(AlertStrategy):
    def get_severity(self, signal: dict) -> Severity:
        return Severity.P1  # Database down = P1

    def get_alert_message(self, signal: dict) -> str:
        return f"CRITICAL: Database failure detected on {signal.get('service_affected')}. Immediate action required."


# Concrete Strategy 2 — Cache failures are high priority
class CacheAlertStrategy(AlertStrategy):
    def get_severity(self, signal: dict) -> Severity:
        return Severity.P2  # Cache down = P2, system still works but slow

    def get_alert_message(self, signal: dict) -> str:
        return f"WARNING: Cache failure on {signal.get('service_affected')}. Performance degraded."


# Concrete Strategy 3 — API failures
class APIAlertStrategy(AlertStrategy):
    def get_severity(self, signal: dict) -> Severity:
        return Severity.P1  # API down = P1

    def get_alert_message(self, signal: dict) -> str:
        return f"HIGH: API failure on {signal.get('service_affected')}. Users affected."


# Concrete Strategy 4 — Queue failures
class QueueAlertStrategy(AlertStrategy):
    def get_severity(self, signal: dict) -> Severity:
        return Severity.P2

    def get_alert_message(self, signal: dict) -> str:
        return f"WARNING: Message queue failure on {signal.get('service_affected')}. Jobs delayed."


# Concrete Strategy 5 — Default/unknown
class DefaultAlertStrategy(AlertStrategy):
    def get_severity(self, signal: dict) -> Severity:
        return Severity.P3

    def get_alert_message(self, signal: dict) -> str:
        return f"INFO: Signal received for {signal.get('service_affected')}."


# Strategy selector — picks the right strategy based on component type
COMPONENT_STRATEGIES = {
    "database": RDBMSAlertStrategy(),
    "postgres": RDBMSAlertStrategy(),
    "mysql": RDBMSAlertStrategy(),
    "rdbms": RDBMSAlertStrategy(),
    "cache": CacheAlertStrategy(),
    "redis": CacheAlertStrategy(),
    "memcache": CacheAlertStrategy(),
    "api": APIAlertStrategy(),
    "payments-api": APIAlertStrategy(),
    "auth-service": APIAlertStrategy(),
    "queue": QueueAlertStrategy(),
    "kafka": QueueAlertStrategy(),
    "rabbitmq": QueueAlertStrategy(),
}


def get_alert_strategy(service_affected: str) -> AlertStrategy:
    # Check if any keyword matches the service name
    service_lower = service_affected.lower()
    for keyword, strategy in COMPONENT_STRATEGIES.items():
        if keyword in service_lower:
            return strategy
    return DefaultAlertStrategy()
