FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY providers/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY providers/provider_app.py /app/provider_app.py
COPY backend/app/flight_generator.py /app/flight_generator.py
EXPOSE 8000
CMD ["uvicorn", "provider_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
