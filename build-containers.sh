#!/bin/bash
# Build script for all Extrophi Ecosystem containers
# Usage: ./build-containers.sh [podman|docker]

set -e

# Detect container runtime
RUNTIME="${1:-podman}"

if ! command -v "$RUNTIME" &> /dev/null; then
    echo "Error: $RUNTIME not found. Please install Podman or Docker."
    exit 1
fi

echo "🚀 Building Extrophi Ecosystem containers with $RUNTIME..."
echo ""

# Build Orchestrator (lightest, ~150-200MB)
echo "📦 Building Orchestrator..."
cd orchestrator
$RUNTIME build -f Containerfile -t extrophi-orchestrator:latest .
cd ..
echo "✅ Orchestrator built successfully"
echo ""

# Build Research Backend (~300-400MB)
echo "📦 Building Research Backend..."
cd research
$RUNTIME build -f Containerfile -t extrophi-research:latest .
cd ..
echo "✅ Research Backend built successfully"
echo ""

# Build Backend (~400-500MB with Playwright)
echo "📦 Building Backend..."
cd backend
$RUNTIME build -f Containerfile -t extrophi-backend:latest .
cd ..
echo "✅ Backend built successfully"
echo ""

# Build Writer (build environment, ~300-400MB)
echo "📦 Building Writer..."
cd writer
$RUNTIME build -f Containerfile -t extrophi-writer:latest .
cd ..
echo "✅ Writer built successfully"
echo ""

# Display image sizes
echo "📊 Container Image Sizes:"
echo "========================"
$RUNTIME images | grep extrophi

echo ""
echo "🎉 All containers built successfully!"
echo ""
echo "To verify sizes are under 500MB:"
echo "  $RUNTIME images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' | grep extrophi"
echo ""
echo "To run containers:"
echo "  $RUNTIME run -p 8000:8000 extrophi-orchestrator:latest"
echo "  $RUNTIME run -p 8001:8000 extrophi-research:latest"
echo "  $RUNTIME run -p 8002:8000 extrophi-backend:latest"
