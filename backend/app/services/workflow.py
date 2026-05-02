VALID_TRANSITIONS = {
    "open": ["investigating"],
    "investigating": ["mitigating", "resolved"],
    "mitigating": ["resolved"],
    "resolved": ["closed"],
    "closed": []
}

def can_transition(current: str, next_status: str) -> bool:
    return next_status in VALID_TRANSITIONS.get(current, [])

def get_allowed_transitions(current: str) -> list:
    return VALID_TRANSITIONS.get(current, [])

def validate_close(rca) -> tuple:
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
