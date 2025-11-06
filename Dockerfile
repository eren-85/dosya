# Multi-stage build for Python backend
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
COPY requirements_training.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements_training.txt

# Install PyTorch with CUDA support (for GPU training)
# Note: Remove this line if training only on CPU
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Copy application code
COPY backend /app/backend
COPY scripts /app/scripts

# Create data directories (volumes will mount here)
RUN mkdir -p /app/data/historical /app/data/models /app/data/knowledge \
    /app/data/annotations /app/data/patterns /app/data/training

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
