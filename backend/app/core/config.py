from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_URL: str = "postgresql+asyncpg://ims_user:ims_pass@postgres:5432/ims_db"
    MONGODB_URL: str = "mongodb://ims_user:ims_pass@mongodb:27017/ims_raw?authSource=admin"
    REDIS_URL: str = "redis://redis:6379"
    APP_NAME: str = "IMS - Incident Management System"
    VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"

settings = Settings()
