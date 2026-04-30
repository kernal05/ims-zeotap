from app.models.incident import Status

VALID_TRANSITIONS = {
    Status.OPEN: [Status.INVESTIGATING],
    Status.INVESTIGATING: [Status.MITIGATING, Status.RESOLVED],
    Status.MITIGATING: [Status.RESOLVED],
    Status.RESOLVED: [Status.CLOSED],
    Status.CLOSED: []
}

def can_transition(current: Status, next: Status) -> bool:
    return next in VALID_TRANSITIONS.get(current, [])

def get_allowed_transitions(current: Status) -> list:
    return VALID_TRANSITIONS.get(current, [])

def validate_close(rca) -> tuple[bool, str]:
    if rca is None:
        return False, "RCA report is mandatory before closing an incident"
    if not rca.root_cause.strip():
        return False, "Root cause cannot be empty"
    if not rca.timeline.strip():
        return False, "Timeline cannot be empty"
    if not rca.fix_applied.strip():
        return False, "Fix applied cannot be empty"
    if not rca.prevention.strip():
        return False, "Prevention steps cannot be empty"
    return True, "OK"
