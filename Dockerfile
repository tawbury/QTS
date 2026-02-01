# QTS Trading System Docker Image
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

LABEL maintainer="QTS Team"
LABEL description="QTS Trading System - Low-latency scalping execution engine"
LABEL version="1.0.0"

# Create app user (non-root)
RUN useradd -m -u 1000 -s /bin/bash qtsapp

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/qtsapp/.local

# Copy application code
COPY app/ ./app/
COPY ops/ ./ops/
COPY shared/ ./shared/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backup && \
    chown -R qtsapp:qtsapp /app

# Switch to app user
USER qtsapp

# Set Python path
ENV PYTHONPATH=/app
ENV PATH=/home/qtsapp/.local/bin:$PATH

# Environment variables (can be overridden at runtime)
ENV QTS_ENV=production
ENV OBSERVER_ENDPOINT=unix:///var/run/observer.sock
ENV BROKER_TYPE=kiwoom
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose ports (if needed for metrics/monitoring)
# EXPOSE 8080

# Default command
CMD ["python", "-m", "app.main"]
