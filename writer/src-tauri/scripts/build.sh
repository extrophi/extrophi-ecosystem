#!/bin/bash
# BrainDump V3.0 - Production Build Script
# Creates production-ready Tauri bundle

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}BrainDump V3.0 - Production Build${NC}"
echo "=================================="

# Get project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
TAURI_DIR="$PROJECT_ROOT/src-tauri"

echo "Project root: $PROJECT_ROOT"

# Set library path for C++ dylib (Stage A)
export DYLD_LIBRARY_PATH="$PROJECT_ROOT/build/src/api:$DYLD_LIBRARY_PATH"
echo -e "${GREEN}✓${NC} DYLD_LIBRARY_PATH set"

# Check if C++ library exists
if [ ! -f "$PROJECT_ROOT/build/src/api/libbraindump.dylib" ]; then
    echo "❌ ERROR: C++ library not found"
    echo "Please build Stage A first with: cd $PROJECT_ROOT && ./build-stage-a.sh"
    exit 1
fi
echo -e "${GREEN}✓${NC} C++ library found"

# Check if Whisper model exists
if [ ! -f "$PROJECT_ROOT/models/ggml-base.bin" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Whisper model not found${NC}"
    echo "The app will fail at runtime without the model."
    echo "Download it with:"
    echo "  mkdir -p $PROJECT_ROOT/models"
    echo "  curl -L -o $PROJECT_ROOT/models/ggml-base.bin \\"
    echo "    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Change to tauri directory
cd "$TAURI_DIR"

# Clean previous builds
echo -e "${BLUE}Cleaning previous builds...${NC}"
cargo clean

# Build release binary
echo -e "${BLUE}Building release binary...${NC}"
cargo build --release --bin braindump

# Build Tauri bundle
echo -e "${BLUE}Creating Tauri bundle...${NC}"
cargo tauri build

echo ""
echo -e "${GREEN}✓ Build complete!${NC}"
echo ""
echo "Bundle location:"
ls -lh "$TAURI_DIR/target/release/bundle/macos/"*.app 2>/dev/null || echo "Bundle not found - check errors above"
echo ""
echo "Binary location:"
ls -lh "$TAURI_DIR/target/release/braindump"
