import os #для чтения переменных окружения
from dataclasses import dataclass # для компактного объявления класса настроек


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://loyalty:loyalty@postgres:5432/loyalty",
    ) # читает две переменные если 1 нет 2 дефолт
    rabbitmq_url: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://loyalty:loyalty@rabbitmq:5672/",
    )


settings = Settings() #экземпляр Все остальные файлы делают from .config import settings и читают поля.
