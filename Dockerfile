# ==================== Dockerfile ====================
# Multi-stage build for optimal size and security

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  g++ \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ==================== Final Stage ====================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 unhabit && \
  mkdir -p /app/chroma_db && \
  chown -R unhabit:unhabit /app

# Copy Python dependencies from builder
COPY --from=builder --chown=unhabit:unhabit /root/.local /home/unhabit/.local

# Copy application code
COPY --chown=unhabit:unhabit . .

# Set environment variables
ENV PATH=/home/unhabit/.local/bin:$PATH \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  CHROMA_PERSIST_DIR=/app/chroma_db

# Switch to non-root user
USER unhabit

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Run the application
CMD ["python", "main.py"]