import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    rabbitmq_url: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://loyalty:loyalty@rabbitmq:5672/",
    )
    min_delay_ms: int = int(os.getenv("MIN_DELAY_MS", "200"))
    max_delay_ms: int = int(os.getenv("MAX_DELAY_MS", "1500"))
    unsubscribed_raw: str = os.getenv("UNSUBSCRIBED", "")

    @property
    def unsubscribed(self) -> set[str]:
        return {
            item.strip()
            for item in self.unsubscribed_raw.split(",")
            if item.strip()
        }


settings = Settings()
