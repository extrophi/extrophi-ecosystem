#!/bin/bash
# BrainDump V3.0 - Setup Verification Script
# Checks all prerequisites are in place

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}BrainDump V3.0 - Setup Verification${NC}"
echo "===================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
TAURI_DIR="$PROJECT_ROOT/src-tauri"

ISSUES=0

# Check 1: C++ Library
echo -n "Checking C++ library... "
if [ -f "$PROJECT_ROOT/build/src/api/libbraindump.dylib" ]; then
    echo -e "${GREEN}✓ Found${NC}"
    ls -lh "$PROJECT_ROOT/build/src/api/libbraindump.dylib" | awk '{print "  Size: "$5}'
else
    echo -e "${RED}✗ Missing${NC}"
    echo "  Build Stage A first: ./build-stage-a.sh"
    ((ISSUES++))
fi

# Check 2: Whisper Model
echo -n "Checking Whisper model... "
if [ -f "$PROJECT_ROOT/models/ggml-base.bin" ]; then
    echo -e "${GREEN}✓ Found${NC}"
    ls -lh "$PROJECT_ROOT/models/ggml-base.bin" | awk '{print "  Size: "$5}'
else
    echo -e "${YELLOW}⚠ Missing${NC}"
    echo "  Download with:"
    echo "    mkdir -p $PROJECT_ROOT/models"
    echo "    curl -L -o $PROJECT_ROOT/models/ggml-base.bin \\"
    echo "      https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
    ((ISSUES++))
fi

# Check 3: Rust Binary
echo -n "Checking Rust binary... "
if [ -f "$TAURI_DIR/target/debug/braindump" ]; then
    echo -e "${GREEN}✓ Found${NC}"
    ls -lh "$TAURI_DIR/target/debug/braindump" | awk '{print "  Size: "$5}'
else
    echo -e "${YELLOW}⚠ Not built${NC}"
    echo "  Build with: cd src-tauri && cargo build --bin braindump"
    ((ISSUES++))
fi

# Check 4: Icons
echo -n "Checking icons... "
ICON_COUNT=$(ls -1 "$TAURI_DIR/icons/"*.{png,icns,ico} 2>/dev/null | wc -l | tr -d ' ')
if [ "$ICON_COUNT" -ge 5 ]; then
    echo -e "${GREEN}✓ Found (${ICON_COUNT} files)${NC}"
else
    echo -e "${RED}✗ Missing or incomplete${NC}"
    echo "  Expected: 32x32.png, 128x128.png, 128x128@2x.png, icon.icns, icon.ico"
    ((ISSUES++))
fi

# Check 5: Frontend
echo -n "Checking frontend... "
if [ -f "$PROJECT_ROOT/index.html" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${YELLOW}⚠ Missing${NC}"
    echo "  Frontend being built by another agent"
    echo "  Expected location: $PROJECT_ROOT/index.html"
fi

# Check 6: Scripts
echo -n "Checking launch scripts... "
if [ -x "$TAURI_DIR/scripts/dev.sh" ] && [ -x "$TAURI_DIR/scripts/build.sh" ]; then
    echo -e "${GREEN}✓ Found and executable${NC}"
else
    echo -e "${RED}✗ Missing or not executable${NC}"
    echo "  Run: chmod +x $TAURI_DIR/scripts/*.sh"
    ((ISSUES++))
fi

# Summary
echo ""
echo "===================================="
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Ready to run development mode:"
    echo "  cd src-tauri && ./scripts/dev.sh"
else
    echo -e "${YELLOW}⚠ Found $ISSUES issue(s)${NC}"
    echo ""
    echo "Fix the issues above before running."
fi

echo ""
echo "Quick commands:"
echo "  Development: cd src-tauri && ./scripts/dev.sh"
echo "  Build:       cd src-tauri && ./scripts/build.sh"
echo "  Verify:      cd src-tauri && ./scripts/verify-setup.sh"
