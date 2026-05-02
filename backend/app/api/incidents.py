from app.services.assignment import auto_assign_incident
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone
from app.db.postgres import get_db
from app.db.mongodb import log_raw_alert, log_incident_event
from app.db.redis_client import cache_incident, get_cached_incident, invalidate_cache, publish_alert, redis_client
from app.models.incident import Incident, RCAReport
from app.schemas.incident import AlertSignal, IncidentUpdate, RCACreate, IncidentResponse, RCAResponse
from app.services.workflow import can_transition, get_allowed_transitions, validate_close

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/alerts", status_code=201)
async def ingest_alert(alert: AlertSignal, db: AsyncSession = Depends(get_db)):
    from app.services.metrics import record_signal

    record_signal()

    rate_key = f"rate:{alert.service_affected}"
    rate_count = await redis_client.incr(rate_key)
    if rate_count == 1:
        await redis_client.expire(rate_key, 10)
    if rate_count > 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    debounce_key = f"debounce:{alert.service_affected}"
    existing_id = await redis_client.get(debounce_key)

    now = datetime.now(timezone.utc).isoformat()

    raw_id = log_raw_alert({
        "title": alert.title,
        "description": alert.description,
        "severity": alert.severity,
        "service_affected": alert.service_affected,
        "alert_source": alert.alert_source,
        "received_at": now
    })

    if existing_id:
        log_incident_event(existing_id, "duplicate_signal", {"raw_alert_id": raw_id})
        return {
            "incident_id": existing_id,
            "raw_alert_id": raw_id,
            "status": "debounced"
        }

    incident = Incident(
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        service_affected=alert.service_affected,
        alert_source=alert.alert_source,
        status="open"
    )

    incident.assigned_to = auto_assign_incident(alert.service_affected, alert.severity)
    incident.is_auto_assigned = True

    db.add(incident)
    await db.flush()

    # ✅ FIX: ensure DB write is committed
    await db.commit()
    await db.refresh(incident)

    await redis_client.setex(debounce_key, 10, str(incident.id))

    log_incident_event(
        str(incident.id),
        "created",
        {"severity": alert.severity, "raw_alert_id": raw_id}
    )

    await publish_alert(
        "new_incident",
        {
            "incident_id": str(incident.id),
            "severity": alert.severity,
            "title": alert.title
        }
    )

    return {
        "incident_id": str(incident.id),
        "raw_alert_id": raw_id,
        "status": "open"
    }


@router.get("", response_model=list[IncidentResponse])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident)
        .options(selectinload(Incident.rca))
        .order_by(Incident.created_at.desc())
    )

    response = []
    for inc in result.scalars().all():
        data = IncidentResponse.model_validate(inc)
        data.allowed_transitions = get_allowed_transitions(inc.status)
        response.append(data)

    return response


@router.get("/stats/summary")
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident))
    all_incidents = result.scalars().all()

    total = len(all_incidents)
    open_count = sum(1 for i in all_incidents if i.status == "open")
    p1_count = sum(1 for i in all_incidents if i.severity == "P1")

    resolved = [i for i in all_incidents if i.resolved_at]

    avg_mttr = 0.0
    if resolved:
        durations = [
            (i.resolved_at - i.created_at).total_seconds() / 60
            for i in resolved
        ]
        avg_mttr = round(sum(durations) / len(durations), 1)

    return {
        "total": total,
        "open": open_count,
        "p1_active": p1_count,
        "avg_mttr_minutes": avg_mttr
    }


@router.get("/stats/timeseries")
async def get_timeseries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident))

    buckets = {}

    for inc in result.scalars().all():
        ts = inc.created_at.replace(tzinfo=None)
        key = ts.replace(minute=0, second=0, microsecond=0).isoformat()

        if key not in buckets:
            buckets[key] = {
                "timestamp": key,
                "total": 0,
                "P1": 0,
                "P2": 0,
                "P3": 0
            }

        buckets[key]["total"] += 1

        if inc.severity in buckets[key]:
            buckets[key][inc.severity] += 1

    return {
        "window": "all",
        "resolution": "1h",
        "series": sorted(buckets.values(), key=lambda x: x["timestamp"])
    }


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: UUID, db: AsyncSession = Depends(get_db)):
    cached = await get_cached_incident(str(incident_id))
    if cached:
        return cached

    result = await db.execute(
        select(Incident)
        .options(selectinload(Incident.rca))
        .where(Incident.id == incident_id)
    )

    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    data = IncidentResponse.model_validate(incident)
    data.allowed_transitions = get_allowed_transitions(incident.status)

    await cache_incident(str(incident_id), data.model_dump(mode="json"))

    return data


@router.patch("/{incident_id}/status")
async def update_status(incident_id: UUID, update: IncidentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident)
        .options(selectinload(Incident.rca))
        .where(Incident.id == incident_id)
    )

    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if update.status:
        if not can_transition(incident.status, update.status):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {incident.status} to {update.status}"
            )

        if update.status == "closed":
            valid, msg = validate_close(incident.rca)
            if not valid:
                raise HTTPException(status_code=400, detail=msg)

        if update.status == "resolved":
            incident.resolved_at = datetime.now(timezone.utc)

        log_incident_event(
            str(incident.id),
            "status_changed",
            {"from": incident.status, "to": update.status}
        )

        incident.status = update.status

    if update.assigned_to:
        incident.assigned_to = update.assigned_to
        incident.is_auto_assigned = False

    await invalidate_cache(str(incident_id))

    return {"message": "Updated", "status": incident.status}


@router.post("/{incident_id}/rca", response_model=RCAResponse, status_code=201)
async def submit_rca(incident_id: UUID, rca_data: RCACreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))

    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Incident not found")

    existing = await db.execute(
        select(RCAReport).where(RCAReport.incident_id == incident_id)
    )

    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="RCA already submitted")

    rca = RCAReport(incident_id=incident_id, **rca_data.model_dump())

    db.add(rca)
    await db.flush()

    log_incident_event(
        str(incident_id),
        "rca_submitted",
        {"written_by": rca_data.written_by}
    )

    await invalidate_cache(str(incident_id))

    return rca


@router.get("/{incident_id}/signals")
async def get_signals(incident_id: str):
    from app.db.mongodb import incident_logs_collection

    return list(
        incident_logs_collection.find(
            {"incident_id": incident_id},
            {"_id": 0}
        )
    )
