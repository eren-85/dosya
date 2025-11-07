# syntax=docker/dockerfile:1.7
ARG PYVER=3.12
FROM python:${PYVER}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Sistem bağımlılıkları (derleme araçları vs.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Gereksinimler
COPY requirements.txt .
# Not: TA-Lib==0.6.8 wheel C kütüphanesini içerir — ekstra kurulum yok
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
        torch==2.5.1 torchvision==0.20.1

# Uygulama kodu
COPY backend ./backend
COPY scripts ./scripts

# Veri klasörleri
RUN mkdir -p /app/data/historical /app/data/models /app/data/knowledge \
    /app/data/annotations /app/data/patterns /app/data/training

# ---------- Backend ----------
FROM base AS backend
EXPOSE 8000
CMD ["python","-m","uvicorn","backend.api.main:app","--host","0.0.0.0","--port","8000"]

# ---------- Celery Worker ----------
FROM base AS celery_worker
CMD ["celery","-A","backend.tasks.celery_app","worker","-l","INFO","-Q","default"]

# ---------- Celery Beat ----------
FROM base AS celery_beat
CMD ["celery","-A","backend.tasks.celery_app","beat","-l","INFO"]

# ---------- Flower ----------
FROM base AS flower
EXPOSE 5555
CMD ["celery","-A","backend.tasks.celery_app","flower","--port=5555"]
