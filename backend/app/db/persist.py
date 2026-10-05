from app.db.retry import with_retry


@with_retry(max_attempts=3, delay=0.5)
async def persist_incident(db, incident):
    """Insert an incident; roll back the session before each retry."""
    try:
        db.add(incident)
        await db.flush()
        await db.commit()
    except Exception:
        await db.rollback()
        raise
