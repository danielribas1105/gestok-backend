from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Conexão direta (Alembic)
    DATABASE_URL: str
    # Conexão pooled (runtime) — se não informada, usa a direta
    DATABASE_POOL_URL: Optional[str] = None

    JWT_TOKEN_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200

    @property
    def db_url(self) -> str:
        """Retorna a URL pooled para uso na aplicação."""
        return self.DATABASE_POOL_URL or self.DATABASE_URL

    class Config:
        env_file = ".env"


settings = Settings()
