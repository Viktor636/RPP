from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from database import SessionLocal, engine
from models import Base, Visit


# Создание таблицы при старте приложения
Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/hello", response_class=PlainTextResponse)
async def hello(request: Request):
    # Получаем IP-адрес клиента
    client_ip = request.client.host

    # Получаем текущее время
    current_time = datetime.utcnow()

    # Создаём запись
    db = SessionLocal()

    try:
        visit = Visit(
            timestamp=current_time,
            ip_address=client_ip
        )

        db.add(visit)
        db.commit()
    finally:
        db.close()

    return "Hello"