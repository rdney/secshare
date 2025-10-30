from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "SecShare API"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://secshare:secshare@localhost:5432/secshare"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_TEAM: str = ""
    STRIPE_PRICE_ID_ENTERPRISE: str = ""

    # Subscription Limits
    FREE_SECRETS_PER_MONTH: int = 10
    PRO_SECRETS_PER_MONTH: int = 100
    TEAM_SECRETS_PER_MONTH: int = 500

    FREE_MAX_ATTACHMENT_SIZE: int = 0
    PRO_MAX_ATTACHMENT_SIZE: int = 10 * 1024 * 1024  # 10MB
    TEAM_MAX_ATTACHMENT_SIZE: int = 50 * 1024 * 1024  # 50MB

    FREE_TEAM_SIZE: int = 1
    PRO_TEAM_SIZE: int = 1
    TEAM_TEAM_SIZE: int = 5

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
