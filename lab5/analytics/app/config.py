import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    rabbitmq_url: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://loyalty:loyalty@rabbitmq:5672/",
    )


settings = Settings()
