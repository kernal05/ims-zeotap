import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings

engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    for attempt in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Auto-migrate schema drift
                await conn.execute(text("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS is_auto_assigned BOOLEAN DEFAULT FALSE"))
                await conn.execute(text("ALTER TABLE incidents ALTER COLUMN severity TYPE VARCHAR(10)"))
                await conn.execute(text("ALTER TABLE incidents ALTER COLUMN status TYPE VARCHAR(50)"))
            print("Database initialized successfully")
            return
        except Exception as e:
            print(f"DB init attempt {attempt+1}/10 failed: {e}")
            await asyncio.sleep(3)
    raise Exception("Could not connect to database after 10 attempts")
