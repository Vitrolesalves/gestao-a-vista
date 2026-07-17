#!/bin/bash

# Gestão à Vista - Deployment Script
# Usage: ./scripts/deploy.sh [environment] [version]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
PROJECT_NAME="gestao-a-vista"

# Configuration
DOCKER_REGISTRY="ghcr.io"
IMAGE_NAME="$DOCKER_REGISTRY/$PROJECT_NAME"

echo -e "${BLUE}🚀 Starting deployment of $PROJECT_NAME${NC}"
echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"
echo -e "${BLUE}Version: $VERSION${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command_exists docker; then
    print_error "Docker is not installed"
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed"
    exit 1
fi

print_status "Prerequisites check passed"

# Environment-specific configurations
case $ENVIRONMENT in
    "development"|"dev")
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.dev"
        PORT="8000"
        ;;
    "staging")
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.staging"
        PORT="80"
        ;;
    "production"|"prod")
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.prod"
        PORT="80"
        ;;
    *)
        print_error "Unknown environment: $ENVIRONMENT"
        echo "Available environments: development, staging, production"
        exit 1
        ;;
esac

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    print_warning "Environment file $ENV_FILE not found"
    print_warning "Creating from template..."
    
    if [ -f ".env.example" ]; then
        cp .env.example "$ENV_FILE"
        print_warning "Please edit $ENV_FILE with your configuration"
    else
        print_error "No .env.example template found"
        exit 1
    fi
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
fi

# Pre-deployment checks
echo -e "${BLUE}🔍 Running pre-deployment checks...${NC}"

# Check if required environment variables are set
required_vars=("SECRET_KEY" "POSTGRES_PASSWORD")
if [ "$ENVIRONMENT" != "development" ]; then
    required_vars+=("ALLOWED_HOSTS")
fi

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

print_status "Environment variables check passed"

# Backup database (for production)
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${BLUE}💾 Creating database backup...${NC}"
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Create database backup
    docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump \
        -U "${POSTGRES_USER:-gestao_user}" \
        -d "${POSTGRES_DB:-gestao_vista}" \
        > "$BACKUP_DIR/database_backup.sql"
    
    # Create media backup
    docker-compose -f "$COMPOSE_FILE" exec -T web tar czf - /app/media \
        > "$BACKUP_DIR/media_backup.tar.gz"
    
    print_status "Backup created in $BACKUP_DIR"
fi

# Pull latest images
echo -e "${BLUE}📦 Pulling latest images...${NC}"

if [ "$VERSION" != "latest" ]; then
    # Pull specific version
    docker pull "$IMAGE_NAME:$VERSION"
else
    # Build locally or pull latest
    if [ -f "Dockerfile" ]; then
        echo -e "${BLUE}🏗️  Building application image...${NC}"
        docker-compose -f "$COMPOSE_FILE" build web
    else
        docker-compose -f "$COMPOSE_FILE" pull
    fi
fi

print_status "Images ready"

# Run database migrations
echo -e "${BLUE}🗄️  Running database migrations...${NC}"

docker-compose -f "$COMPOSE_FILE" run --rm web python manage.py migrate

print_status "Database migrations completed"

# Collect static files
echo -e "${BLUE}📁 Collecting static files...${NC}"

docker-compose -f "$COMPOSE_FILE" run --rm web python manage.py collectstatic --noinput

print_status "Static files collected"

# Deploy application
echo -e "${BLUE}🚀 Deploying application...${NC}"

# Stop existing containers
docker-compose -f "$COMPOSE_FILE" down

# Start new containers
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"

# Wait for web service
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f "http://localhost:$PORT/health/" >/dev/null 2>&1; then
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    print_error "Service failed to start within $timeout seconds"
    
    # Show logs for debugging
    echo -e "${BLUE}📋 Recent logs:${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50 web
    
    exit 1
fi

print_status "Application is running"

# Post-deployment checks
echo -e "${BLUE}🧪 Running post-deployment checks...${NC}"

# Health check
if curl -f "http://localhost:$PORT/health/" >/dev/null 2>&1; then
    print_status "Health check passed"
else
    print_error "Health check failed"
    exit 1
fi

# Database connectivity check
if docker-compose -f "$COMPOSE_FILE" exec -T web python manage.py check --database default >/dev/null 2>&1; then
    print_status "Database connectivity check passed"
else
    print_error "Database connectivity check failed"
    exit 1
fi

# Static files check
if curl -f "http://localhost:$PORT/static/css/bootstrap-custom.css" >/dev/null 2>&1; then
    print_status "Static files check passed"
else
    print_warning "Static files check failed (may be normal if files don't exist)"
fi

# Cleanup old images
echo -e "${BLUE}🧹 Cleaning up old images...${NC}"

docker image prune -f
docker system prune -f

print_status "Cleanup completed"

# Deployment summary
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo -e "Environment: $ENVIRONMENT"
echo -e "Version: $VERSION"
echo -e "URL: http://localhost:$PORT"
echo -e "Health Check: http://localhost:$PORT/health/"

if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "Backup Location: $BACKUP_DIR"
fi

# Show running containers
echo -e "${BLUE}📋 Running containers:${NC}"
docker-compose -f "$COMPOSE_FILE" ps

# Show recent logs
echo -e "${BLUE}📋 Recent application logs:${NC}"
docker-compose -f "$COMPOSE_FILE" logs --tail=20 web

echo -e "${GREEN}✅ Deployment script completed${NC}"
