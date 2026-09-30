from fastapi import FastAPI

from app.api.library import router as library_router
from app.api.parking import router as parking_router


app = FastAPI(
    title="Лабораторная работа №2 — DDD"
)

app.include_router(library_router)
app.include_router(parking_router)


@app.get("/")
def root():
    return {
        "message": "DDD Laboratory №2"
    }