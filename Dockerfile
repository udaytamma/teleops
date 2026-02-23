FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (gcc needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY teleops/ teleops/
COPY docs/ docs/
COPY ui/ ui/

# Copy tracked storage files (test results, evaluation results, benchmarks)
# then ensure storage dir exists for runtime-generated files
COPY storage/evaluation_results.json storage/test_results.json storage/
COPY storage/benchmarks/ storage/benchmarks/

# Create non-root user
RUN useradd -m teleops && chown -R teleops:teleops /app
USER teleops

# Default port (Railway overrides via $PORT env var)
EXPOSE ${PORT:-8000}

# Health check -- uses $PORT so it works on Railway and locally
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run API server -- shell form required for $PORT expansion on Railway
CMD sh -c "uvicorn teleops.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"
