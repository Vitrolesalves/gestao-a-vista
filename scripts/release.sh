#!/bin/bash

# Gestão à Vista - Release Script
# Automatiza o processo de release com versionamento semântico

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BUMP_TYPE="auto"
DRY_RUN=false
SKIP_TESTS=false
SKIP_BUILD=false
PRERELEASE=""
BUILD_META=""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE        Bump type: major, minor, patch, auto (default: auto)"
    echo "  -p, --prerelease PRE   Set prerelease identifier (alpha, beta, rc.1, etc.)"
    echo "  -b, --build BUILD      Set build metadata"
    echo "  -d, --dry-run          Show what would be done without making changes"
    echo "  -s, --skip-tests       Skip running tests"
    echo "  -n, --skip-build       Skip building Docker image"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Auto-detect version bump from commits"
    echo "  $0 -t minor            # Force minor version bump"
    echo "  $0 -t patch -p beta.1  # Patch version with beta prerelease"
    echo "  $0 -d                  # Dry run to see what would happen"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUMP_TYPE="$2"
            shift 2
            ;;
        -p|--prerelease)
            PRERELEASE="$2"
            shift 2
            ;;
        -b|--build)
            BUILD_META="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -n|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch|auto)$ ]]; then
    print_error "Invalid bump type: $BUMP_TYPE"
    print_error "Valid types: major, minor, patch, auto"
    exit 1
fi

echo -e "${BLUE}🚀 Gestão à Vista Release Script${NC}"
echo -e "${BLUE}================================${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    print_warning "You have uncommitted changes:"
    git status --short
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Release cancelled"
        exit 0
    fi
fi

# Get current version
CURRENT_VERSION=$(python3 version.py --current | grep "Current version:" | cut -d' ' -f3)
print_info "Current version: $CURRENT_VERSION"

# Show what version would be created
if [[ "$DRY_RUN" == "true" ]]; then
    print_info "🔍 Dry run mode - showing what would happen:"
    
    ARGS="--bump $BUMP_TYPE --dry-run"
    if [[ -n "$PRERELEASE" ]]; then
        ARGS="$ARGS --prerelease $PRERELEASE"
    fi
    if [[ -n "$BUILD_META" ]]; then
        ARGS="$ARGS --build $BUILD_META"
    fi
    
    python3 version.py $ARGS
    exit 0
fi

# Pre-release checks
echo -e "${BLUE}🔍 Running pre-release checks...${NC}"

# Check if Python version script exists
if [[ ! -f "version.py" ]]; then
    print_error "version.py not found"
    exit 1
fi

# Check if we can run Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found"
    exit 1
fi

# Run tests if not skipped
if [[ "$SKIP_TESTS" != "true" ]]; then
    print_info "Running tests..."
    
    # Check if pytest is available
    if command -v pytest &> /dev/null; then
        if ! pytest tests/ -x --tb=short; then
            print_error "Tests failed"
            exit 1
        fi
        print_status "All tests passed"
    else
        print_warning "pytest not found, skipping tests"
    fi
else
    print_warning "Skipping tests as requested"
fi

# Check if Docker is available for building
if [[ "$SKIP_BUILD" != "true" ]] && command -v docker &> /dev/null; then
    print_info "Docker available for building"
    DOCKER_AVAILABLE=true
else
    DOCKER_AVAILABLE=false
    if [[ "$SKIP_BUILD" != "true" ]]; then
        print_warning "Docker not available, skipping build"
    fi
fi

# Create the release
echo -e "${BLUE}📦 Creating release...${NC}"

ARGS="--bump $BUMP_TYPE"
if [[ -n "$PRERELEASE" ]]; then
    ARGS="$ARGS --prerelease $PRERELEASE"
fi
if [[ -n "$BUILD_META" ]]; then
    ARGS="$ARGS --build $BUILD_META"
fi

# Run the version bump
NEW_VERSION=$(python3 version.py $ARGS | grep "New version:" | cut -d' ' -f3)

if [[ -z "$NEW_VERSION" ]]; then
    print_error "Failed to create new version"
    exit 1
fi

print_status "Version bumped from $CURRENT_VERSION to $NEW_VERSION"

# Commit version changes
print_info "Committing version changes..."
git add VERSION CHANGELOG.md
if [[ -f "package.json" ]]; then
    git add package.json
fi
if [[ -f "setup.py" ]]; then
    git add setup.py
fi

git commit -m "chore: bump version to $NEW_VERSION

- Updated VERSION file
- Updated CHANGELOG.md
- Automated release via release script"

print_status "Version changes committed"

# Build Docker image if available and not skipped
if [[ "$DOCKER_AVAILABLE" == "true" && "$SKIP_BUILD" != "true" ]]; then
    print_info "Building Docker image..."
    
    if docker build -t "gestao-a-vista:$NEW_VERSION" -t "gestao-a-vista:latest" .; then
        print_status "Docker image built successfully"
        
        # Tag for registry if needed
        if [[ -n "$DOCKER_REGISTRY" ]]; then
            docker tag "gestao-a-vista:$NEW_VERSION" "$DOCKER_REGISTRY/gestao-a-vista:$NEW_VERSION"
            docker tag "gestao-a-vista:$NEW_VERSION" "$DOCKER_REGISTRY/gestao-a-vista:latest"
            print_status "Docker images tagged for registry"
        fi
    else
        print_warning "Docker build failed, continuing anyway"
    fi
fi

# Push changes and tags
print_info "Pushing changes to remote..."

# Push commits
if git push origin $(git branch --show-current); then
    print_status "Changes pushed to remote"
else
    print_error "Failed to push changes"
    exit 1
fi

# Push tags
if git push origin --tags; then
    print_status "Tags pushed to remote"
else
    print_error "Failed to push tags"
    exit 1
fi

# Push Docker images if registry is configured
if [[ "$DOCKER_AVAILABLE" == "true" && "$SKIP_BUILD" != "true" && -n "$DOCKER_REGISTRY" ]]; then
    print_info "Pushing Docker images to registry..."
    
    if docker push "$DOCKER_REGISTRY/gestao-a-vista:$NEW_VERSION" && \
       docker push "$DOCKER_REGISTRY/gestao-a-vista:latest"; then
        print_status "Docker images pushed to registry"
    else
        print_warning "Failed to push Docker images"
    fi
fi

# Success message
echo ""
echo -e "${GREEN}🎉 Release $NEW_VERSION completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Release Summary:${NC}"
echo -e "Previous version: $CURRENT_VERSION"
echo -e "New version: $NEW_VERSION"
echo -e "Bump type: $BUMP_TYPE"
if [[ -n "$PRERELEASE" ]]; then
    echo -e "Prerelease: $PRERELEASE"
fi
if [[ -n "$BUILD_META" ]]; then
    echo -e "Build metadata: $BUILD_META"
fi
echo -e "Git tag: v$NEW_VERSION"

# Next steps
echo ""
echo -e "${BLUE}🔗 Next Steps:${NC}"
echo -e "1. Check the GitHub release: https://github.com/your-org/gestao-a-vista/releases/tag/v$NEW_VERSION"
echo -e "2. Monitor the CI/CD pipeline for deployment"
echo -e "3. Verify the deployment in staging/production"
echo -e "4. Update any dependent systems or documentation"

# Optional: Open GitHub release page
if command -v gh &> /dev/null; then
    echo ""
    read -p "Open GitHub release page? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh release view "v$NEW_VERSION" --web
    fi
fi

print_status "Release script completed"
