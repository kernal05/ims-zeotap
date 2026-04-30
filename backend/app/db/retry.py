import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def with_retry(max_attempts=3, delay=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(f"All {max_attempts} attempts failed: {e}")
                        raise
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
