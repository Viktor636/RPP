from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine, # создаёт асинхронный движок SQLAlchemy
)

from .config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True) # expire_on_commit=False делает SELECT 1, и если оно умерло — прозрачно пересоздаёт.
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) # По умолчанию SQLAlchemy после commit() 
                                                                                        # инвалидирует все объекты в сессии и следующий доступ к 
                                                                                        # ним вызывает неявный SELECT
