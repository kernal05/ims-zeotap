import pytest
from app.services.workflow import validate_close, can_transition
from app.models.incident import Status

class MockRCA:
    def __init__(self, root_cause="", timeline="", fix_applied="", prevention=""):
        self.root_cause = root_cause
        self.timeline = timeline
        self.fix_applied = fix_applied
        self.prevention = prevention

def test_close_without_rca():
    valid, msg = validate_close(None)
    assert valid == False
    assert "mandatory" in msg.lower()

def test_close_with_empty_root_cause():
    rca = MockRCA(root_cause="", timeline="some timeline", fix_applied="fix", prevention="prevent")
    valid, msg = validate_close(rca)
    assert valid == False

def test_close_with_complete_rca():
    rca = MockRCA(root_cause="DB crashed", timeline="10am-11am", fix_applied="restart", prevention="monitoring")
    valid, msg = validate_close(rca)
    assert valid == True

def test_valid_transitions():
    assert can_transition(Status.OPEN, Status.INVESTIGATING) == True
    assert can_transition(Status.INVESTIGATING, Status.MITIGATING) == True
    assert can_transition(Status.MITIGATING, Status.RESOLVED) == True
    assert can_transition(Status.RESOLVED, Status.CLOSED) == True

def test_invalid_transitions():
    assert can_transition(Status.OPEN, Status.CLOSED) == False
    assert can_transition(Status.CLOSED, Status.OPEN) == False
    assert can_transition(Status.OPEN, Status.RESOLVED) == False
