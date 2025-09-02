from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./pepperbot.db"

    # Security
    secret_key: str = "your-secret-key-change-in-production"  # TODO: Set via environment variable
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Telegram
    telegram_bot_token: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()