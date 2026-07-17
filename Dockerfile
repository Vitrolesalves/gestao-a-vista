# Multi-stage build for Gestão à Vista
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including fonts for label generation
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    fonts-dejavu \
    fonts-liberation \
    fonts-ubuntu \
    fonts-noto \
    fontconfig \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Development command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production stage
FROM base as production

# Install production-only packages
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Install production dependencies only
RUN pip install gunicorn whitenoise

# Collect static files
RUN python manage.py collectstatic --noinput --settings=config.settings

# Create necessary directories
RUN mkdir -p /var/log/gunicorn /var/log/nginx /var/run

# Copy configuration files
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/gunicorn.conf.py /app/gunicorn.conf.py

# Change ownership to app user
RUN chown -R appuser:appuser /app /var/log/gunicorn
RUN chown -R www-data:www-data /var/log/nginx /var/lib/nginx /var/run

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Production command
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# Testing stage
FROM development as testing

# Copy test configuration
COPY pytest.ini .coveragerc ./

# Run tests
RUN python -m pytest tests/ --cov=Gestao_a_Vista --cov-report=html --cov-report=term

# Final production image
FROM production as final

# Add version label
ARG VERSION=latest
LABEL version=$VERSION \
      description="Gestão à Vista - Sistema de Gestão Administrativa" \
      maintainer="Gestão à Vista Team"

# Final health check and startup
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
