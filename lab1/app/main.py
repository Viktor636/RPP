from fastapi import FastAPI, Request
from datebase import SessionLocal, engine
from models import Base, Visit
import datetime

# Создаем таблицы БД при старте
Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/hello")
async def hello(request: Request):
    #Получаем IP клиента
    client_ip = request.client.host

    # Сохраняем запись в БД
    db = SessionLocal()
    visit = Visit(ip_address=client_ip, timestamp=datetime.datetime.utcnow())
    db.add(visit)
    db.commit()
    db.close()


    return {"message": "Hello"}