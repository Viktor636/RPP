import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://loyalty:loyalty@postgres:5432/loyalty",
    )
    rabbitmq_url: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://loyalty:loyalty@rabbitmq:5672/",
    )


settings = Settings()
