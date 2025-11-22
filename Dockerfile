# DownDetector Notification Bot
# Multi-stage build for optimized image size

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
# Install Python dependencies globalmente no estágio builder (CORREÇÃO 1)
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Install runtime dependencies (incluindo dependências do Playwright)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libnss3 \
    libxss1 \
    libgconf-2-4 \
    libasound2 \
    libfontconfig1 \
    libdbus-1-3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia pacotes instalados do caminho global de site-packages (CORREÇÃO 2)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser templates/ ./templates/

# Cria diretório logs e define permissões (precisa ser feito como root)
RUN mkdir -p logs && chown appuser:appuser logs

# Switch to non-root user
USER appuser

# Instalação dos binários do navegador (Chromium) para o Crawl4AI/Playwright
RUN python -m playwright install chromium

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
