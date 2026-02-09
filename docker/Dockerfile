# =============================================================================
# QTS Trading System - Multi-stage Dockerfile
# =============================================================================

# Stage 1: Builder
# Uses python:3.11-slim for minimal base image.
# Installs dependencies to be copied to the final stage.
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies for cryptography, asyncpg, psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install packages to a local directory for easy copying
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Stage 2: Production
# Minimal runtime image
# =============================================================================
FROM python:3.11-slim

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul \
    # Platform paths
    PLATFORM_CODE_ROOT=/opt/platform/qts \
    PLATFORM_RUNTIME_ROOT=/opt/platform/runtime/qts \
    PYTHONPATH=/opt/platform/qts \
    # Deployment mode
    QTS_DEPLOYMENT_MODE=kubernetes \
    # Runtime paths (overridable by K8s)
    QTS_DATA_DIR=/opt/platform/runtime/qts/data \
    QTS_LOG_DIR=/opt/platform/runtime/qts/logs \
    QTS_CONFIG_DIR=/opt/platform/runtime/qts/config \
    # Observer data source (read-only mount from Observer PVC)
    OBSERVER_DATA_SOURCE_DIR=/opt/platform/runtime/observer/data

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    libpq5 \
    procps \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Security: Create a non-root user with a specific UID/GID
RUN groupadd -g 1000 qts && \
    useradd -u 1000 -g qts -m -s /bin/bash qts

# Set working directory
WORKDIR /opt/platform/qts

# Copy installed dependencies from builder
COPY --from=builder /root/.local /home/qts/.local
ENV PATH="/home/qts/.local/bin:${PATH}"

# Copy source code (refactored src/ structure)
COPY src /opt/platform/qts/src
COPY config /opt/platform/qts/config

# Setup permissions for both code and runtime directories
RUN mkdir -p /opt/platform/runtime/qts/data \
    /opt/platform/runtime/qts/logs \
    /opt/platform/runtime/qts/config && \
    chown -R qts:qts /opt/platform /home/qts/.local

# Switch to non-root user
USER qts

# Healthcheck: Verifies the QTS process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -f "python -m src.runtime.main" || exit 1

# Default command (uses src/ structure entry point)
CMD ["python", "-m", "src.runtime.main"]
