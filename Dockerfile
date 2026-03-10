# Multi-stage build for FastAPI application
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /tmp

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (pyproject and application source)
COPY pyproject.toml .
COPY app/ ./app/

# Install project and dependencies to site-packages (non-editable)
RUN pip install --user --no-cache-dir .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code and scripts
COPY app/ /app/app/
COPY scripts/ /app/scripts/
COPY pyproject.toml /app/

# Make entrypoint script executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Set PATH to use local Python packages
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Use entrypoint script to initialize DB and start app
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
