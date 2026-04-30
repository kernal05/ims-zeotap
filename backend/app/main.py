import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.postgres import init_db
from app.api.incidents import router as incidents_router
from app.services.metrics import print_throughput_metrics

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Mission-Critical Incident Management System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()
    asyncio.create_task(print_throughput_metrics())

app.include_router(incidents_router)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION
    }
