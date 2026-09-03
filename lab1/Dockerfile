# Первая стадия: установка зависимостей
FROM python:3.11-slim AS builder

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Вторая стадия: финальный образ
FROM python:3.11-slim

WORKDIR /app

# Копируем установленные зависимости из первой стадии
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY app/ .

# Запуск через gunicorn (FastAPI)
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]