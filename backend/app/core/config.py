from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "BloodFlow"
    API_V1_STR: str = "/api/v1"

    # Database — set DATABASE_URL directly or use individual POSTGRES_* vars.
    # Falls back to SQLite for local development without Docker.
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "bloodflow"
    POSTGRES_PASSWORD: str = "bloodflow_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "bloodflow"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite:///./bloodflow_dev.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    JWT_SECRET: str = "supersecret_please_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Aliases used by deps.py
    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET

    @property
    def ALGORITHM(self) -> str:
        return self.JWT_ALGORITHM

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()

