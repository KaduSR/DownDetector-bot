# ... (Build stage - mantido)
FROM python:3.11-slim as builder
# ... (Install build dependencies - mantido)

# Production stage
FROM python:3.11-slim

WORKDIR /app
# Create non-root user for security
# ... (useradd e chown mantidos)
RUN useradd --create-home --shell /bin/bash appuser

# Install runtime dependencies incluindo requisitos do Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    # Dependências mínimas do Playwright/Chromium para Debian Slim:
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

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# ... (Copy application code - mantido)
# ...

# Instalação dos binários do navegador (Chromium) para o Crawl4AI/Playwright
USER appuser
RUN python -m playwright install chromium

# Create logs directory
USER root 
RUN mkdir -p logs && chown appuser:appuser logs
USER appuser

# Expose port
EXPOSE 8000
# ... (restante mantido)
