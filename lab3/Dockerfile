# ---------- stage 1: build ----------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --upgrade pip && \
    pip install \
        "fastapi>=0.115" \
        "uvicorn[standard]>=0.30" \
        "pydantic>=2.7"

# ---------- stage 2: runtime ----------
FROM python:3.12-slim

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app ./app
COPY run.py ./

ENV PORT=8000 \
    LOG_LEVEL=info \
    PYTHONUNBUFFERED=1

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=2s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["sh", "-c", "uvicorn run:app --host 0.0.0.0 --port ${PORT} --log-level ${LOG_LEVEL} --workers 1"]