import redis.asyncio as aioredis
import json
from app.core.config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def cache_incident(incident_id: str, data: dict):
    await redis_client.setex(f"incident:{incident_id}", 300, json.dumps(data))

async def get_cached_incident(incident_id: str):
    data = await redis_client.get(f"incident:{incident_id}")
    return json.loads(data) if data else None

async def invalidate_cache(incident_id: str):
    await redis_client.delete(f"incident:{incident_id}")

async def publish_alert(channel: str, message: dict):
    await redis_client.publish(channel, json.dumps(message))
