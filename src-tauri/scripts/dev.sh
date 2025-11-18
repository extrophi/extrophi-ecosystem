#!/bin/bash
# BrainDump V3.0 - Development Mode Script
# Runs Tauri in development mode with proper library paths

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}BrainDump V3.0 - Development Mode${NC}"
echo "=================================="

# Get project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
TAURI_DIR="$PROJECT_ROOT/src-tauri"

echo "Project root: $PROJECT_ROOT"

# Set library path for C++ dylib (Stage A)
export DYLD_LIBRARY_PATH="$PROJECT_ROOT/build/src/api:$DYLD_LIBRARY_PATH"
echo -e "${GREEN}✓${NC} DYLD_LIBRARY_PATH set to: $DYLD_LIBRARY_PATH"

# Check if C++ library exists
if [ ! -f "$PROJECT_ROOT/build/src/api/libbraindump.dylib" ]; then
    echo "❌ ERROR: C++ library not found at $PROJECT_ROOT/build/src/api/libbraindump.dylib"
    echo "Please build Stage A first with: cd $PROJECT_ROOT && ./build-stage-a.sh"
    exit 1
fi
echo -e "${GREEN}✓${NC} C++ library found"

# Check if Whisper model exists
if [ ! -f "$PROJECT_ROOT/models/ggml-base.bin" ]; then
    echo "⚠️  WARNING: Whisper model not found at $PROJECT_ROOT/models/ggml-base.bin"
    echo "Download it with:"
    echo "  mkdir -p $PROJECT_ROOT/models"
    echo "  curl -L -o $PROJECT_ROOT/models/ggml-base.bin \\"
    echo "    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
fi

# Change to tauri directory
cd "$TAURI_DIR"

# Run Tauri dev mode
echo -e "${BLUE}Starting Tauri dev mode...${NC}"
cargo tauri dev
