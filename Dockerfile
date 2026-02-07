FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY teleops/ teleops/
COPY docs/ docs/
COPY storage/ storage/

# Create non-root user
RUN useradd -m teleops && chown -R teleops:teleops /app
USER teleops

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run API server
CMD ["uvicorn", "teleops.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
