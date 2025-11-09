#!/bin/bash
# BrainDump V3.0 - Run Compiled Binary
# Runs the debug or release binary with proper library paths

set -e

# Get project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
TAURI_DIR="$PROJECT_ROOT/src-tauri"

# Set library path for C++ dylib (Stage A)
export DYLD_LIBRARY_PATH="$PROJECT_ROOT/build/src/api:$DYLD_LIBRARY_PATH"

# Determine which binary to run
if [ "$1" == "release" ] || [ "$1" == "--release" ]; then
    BINARY="$TAURI_DIR/target/release/braindump"
else
    BINARY="$TAURI_DIR/target/debug/braindump"
fi

# Check if binary exists
if [ ! -f "$BINARY" ]; then
    echo "Error: Binary not found at $BINARY"
    echo "Build it first with:"
    if [ "$1" == "release" ]; then
        echo "  ./scripts/build.sh"
    else
        echo "  cargo build --bin braindump"
    fi
    exit 1
fi

echo "Running: $BINARY"
echo "DYLD_LIBRARY_PATH: $DYLD_LIBRARY_PATH"
echo ""

# Run the binary
exec "$BINARY"
