from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str  # postgresql://... (Alembic)
    DATABASE_POOL_URL: Optional[str] = None  # pooled do Neon, se existir

    JWT_TOKEN_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200

    @property
    def db_url(self) -> str:
        """Síncrono — usado pelo Alembic e database.py."""
        return self.DATABASE_POOL_URL or self.DATABASE_URL

    @property
    def async_db_url(self) -> str:
        """Async — usado pelo fastapi_async_sqlalchemy (asyncpg)."""
        url = self.DATABASE_POOL_URL or self.DATABASE_URL
        return url.replace("postgresql://", "postgresql+asyncpg://")

    class Config:
        env_file = ".env"


settings = Settings()
