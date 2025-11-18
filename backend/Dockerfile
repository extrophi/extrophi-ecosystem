# IAC-032 Unified Scraper - Core Engine
# Ubuntu-based Python container with UV package manager

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml ./

# Install dependencies with UV
RUN uv pip install --system -r pyproject.toml || pip install -e .

# Copy application code
COPY . .

# Create output directory for Markdown exports
RUN mkdir -p /app/output

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
