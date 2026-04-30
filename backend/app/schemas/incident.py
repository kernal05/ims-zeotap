from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.incident import Severity, Status

class AlertSignal(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    severity: Severity = Severity.P3
    service_affected: str = Field(..., min_length=2)
    alert_source: Optional[str] = "manual"

class IncidentUpdate(BaseModel):
    assigned_to: Optional[str] = None
    status: Optional[Status] = None

class RCACreate(BaseModel):
    root_cause: str = Field(..., min_length=10)
    timeline: str = Field(..., min_length=10)
    fix_applied: str = Field(..., min_length=10)
    prevention: str = Field(..., min_length=10)
    written_by: str = Field(..., min_length=2)

class RCAResponse(BaseModel):
    id: UUID
    incident_id: UUID
    root_cause: str
    timeline: str
    fix_applied: str
    prevention: str
    written_by: str
    created_at: datetime

    class Config:
        from_attributes = True

class IncidentResponse(BaseModel):
    id: UUID
    title: str
    description: str
    severity: Severity
    status: Status
    assigned_to: Optional[str]
    service_affected: str
    alert_source: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    rca: Optional[RCAResponse] = None
    allowed_transitions: Optional[list] = None

    class Config:
        from_attributes = True
