from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone

from app.db.postgres import get_db
from app.db.mongodb import log_raw_alert, log_incident_event
from app.db.redis_client import cache_incident, get_cached_incident, invalidate_cache, publish_alert, redis_client
from app.models.incident import Incident, RCAReport, Status
from app.schemas.incident import AlertSignal, IncidentUpdate, RCACreate, IncidentResponse, RCAResponse
from app.services.workflow import can_transition, get_allowed_transitions, validate_close

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

# Throughput counter
signal_counter = {"count": 0, "last_reset": datetime.now(timezone.utc)}

@router.post("/alerts", status_code=201)
async def ingest_alert(alert: AlertSignal, db: AsyncSession = Depends(get_db)):
    # Track throughput
    from app.services.metrics import record_signal, record_debounced, record_rate_limited
    record_signal()

    # Rate limiting — max 100 requests per 10 seconds per component
    rate_key = f"rate:{alert.service_affected}"
    rate_count = await redis_client.incr(rate_key)
    if rate_count == 1:
        await redis_client.expire(rate_key, 10)
    if rate_count > 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Too many signals for this component.")

    # Debouncing — check if incident already exists for this component in last 10 seconds
    debounce_key = f"debounce:{alert.service_affected}"
    existing_incident_id = await redis_client.get(debounce_key)

    # Store raw alert in MongoDB
    raw_id = log_raw_alert({
        "title": alert.title,
        "description": alert.description,
        "severity": alert.severity,
        "service_affected": alert.service_affected,
        "alert_source": alert.alert_source,
        "received_at": datetime.now(timezone.utc).isoformat()
    })

    if existing_incident_id:
        # Debounce hit — link signal to existing incident, don't create new one
        log_incident_event(existing_incident_id, "duplicate_signal", {
            "raw_alert_id": raw_id,
            "service_affected": alert.service_affected
        })
        return {
            "incident_id": existing_incident_id,
            "raw_alert_id": raw_id,
            "status": "debounced",
            "message": "Signal linked to existing incident"
        }

    # No existing incident — create new one
    incident = Incident(
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        service_affected=alert.service_affected,
        alert_source=alert.alert_source,
        status=Status.OPEN
    )
    db.add(incident)
    await db.flush()

    # Set debounce key — expires in 10 seconds
    await redis_client.setex(debounce_key, 10, str(incident.id))

    log_incident_event(str(incident.id), "created", {
        "severity": alert.severity,
        "raw_alert_id": raw_id
    })

    await publish_alert("new_incident", {
        "incident_id": str(incident.id),
        "severity": alert.severity,
        "title": alert.title
    })

    return {"incident_id": str(incident.id), "raw_alert_id": raw_id, "status": "open"}


@router.get("", response_model=list[IncidentResponse])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident).options(selectinload(Incident.rca)).order_by(Incident.created_at.desc())
    )
    incidents = result.scalars().all()
    response = []
    for inc in incidents:
        data = IncidentResponse.model_validate(inc)
        data.allowed_transitions = [t.value for t in get_allowed_transitions(inc.status)]
        response.append(data)
    return response


@router.get("/stats/summary")
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident))
    all_incidents = result.scalars().all()
    total = len(all_incidents)
    open_count = sum(1 for i in all_incidents if i.status == Status.OPEN)
    p1_count = sum(1 for i in all_incidents if i.severity.value == "P1")
    resolved = [i for i in all_incidents if i.resolved_at]
    avg_mttr = 0
    if resolved:
        durations = [(i.resolved_at - i.created_at).total_seconds() / 60 for i in resolved]
        avg_mttr = round(sum(durations) / len(durations), 1)
    return {
        "total": total,
        "open": open_count,
        "p1_active": p1_count,
        "avg_mttr_minutes": avg_mttr,
        "signals_per_sec": round(signal_counter["count"] / max((datetime.now(timezone.utc) - signal_counter["last_reset"]).total_seconds(), 1), 2)
    }


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: UUID, db: AsyncSession = Depends(get_db)):
    cached = await get_cached_incident(str(incident_id))
    if cached:
        return cached

    result = await db.execute(
        select(Incident).options(selectinload(Incident.rca)).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    data = IncidentResponse.model_validate(incident)
    data.allowed_transitions = [t.value for t in get_allowed_transitions(incident.status)]
    await cache_incident(str(incident_id), data.model_dump(mode="json"))
    return data


@router.patch("/{incident_id}/status")
async def update_status(incident_id: UUID, update: IncidentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident).options(selectinload(Incident.rca)).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if update.status:
        if not can_transition(incident.status, update.status):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot move from {incident.status} to {update.status}"
            )
        if update.status == Status.CLOSED:
            valid, msg = validate_close(incident.rca)
            if not valid:
                raise HTTPException(status_code=400, detail=msg)

        if update.status == Status.RESOLVED:
            incident.resolved_at = datetime.now(timezone.utc)

        log_incident_event(str(incident.id), "status_changed", {
            "from": incident.status.value,
            "to": update.status.value
        })
        incident.status = update.status

    if update.assigned_to:
        incident.assigned_to = update.assigned_to

    await invalidate_cache(str(incident_id))
    return {"message": "Updated", "status": incident.status.value}


@router.post("/{incident_id}/rca", response_model=RCAResponse, status_code=201)
async def submit_rca(incident_id: UUID, rca_data: RCACreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    existing = await db.execute(select(RCAReport).where(RCAReport.incident_id == incident_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="RCA already submitted for this incident")

    rca = RCAReport(incident_id=incident_id, **rca_data.model_dump())
    db.add(rca)
    await db.flush()

    log_incident_event(str(incident_id), "rca_submitted", {"written_by": rca_data.written_by})
    await invalidate_cache(str(incident_id))
    return rca


@router.get("/{incident_id}/signals")
async def get_signals(incident_id: str):
    from app.db.mongodb import incident_logs_collection
    logs = list(incident_logs_collection.find(
        {"incident_id": incident_id},
        {"_id": 0}
    ))
    return logs
