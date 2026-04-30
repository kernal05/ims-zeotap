from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.postgres import Base

class Severity(str, enum.Enum):
    P1 = "P1"  # Critical - system down
    P2 = "P2"  # High - major feature broken
    P3 = "P3"  # Medium - minor issue

class Status(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(Severity), nullable=False, default=Severity.P3)
    status = Column(Enum(Status), nullable=False, default=Status.OPEN)
    assigned_to = Column(String(100), nullable=True)
    service_affected = Column(String(100), nullable=False)
    alert_source = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    rca = relationship("RCAReport", back_populates="incident", uselist=False)

class RCAReport(Base):
    __tablename__ = "rca_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, unique=True)
    root_cause = Column(Text, nullable=False)
    timeline = Column(Text, nullable=False)
    fix_applied = Column(Text, nullable=False)
    prevention = Column(Text, nullable=False)
    written_by = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident", back_populates="rca")
