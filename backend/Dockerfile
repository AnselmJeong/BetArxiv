# Backend Dockerfile
FROM python:3.12-slim

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy backend application
COPY backend/app/ ./app/

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 