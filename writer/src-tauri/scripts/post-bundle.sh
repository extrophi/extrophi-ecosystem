#!/bin/bash
# Post-bundle script to ensure dylib is in the correct location

set -e

APP_PATH="$1"

if [ -z "$APP_PATH" ]; then
    echo "Usage: $0 <path-to-app-bundle>"
    exit 1
fi

echo "Post-bundling for: $APP_PATH"

# Copy dylib to MacOS directory
DYLIB_SOURCE="$APP_PATH/Contents/Resources/_up_/build/src/api/libbraindump.3.dylib"
DYLIB_DEST="$APP_PATH/Contents/MacOS/libbraindump.3.dylib"

if [ -f "$DYLIB_SOURCE" ]; then
    echo "Copying dylib to MacOS directory..."
    cp "$DYLIB_SOURCE" "$DYLIB_DEST"
    chmod +x "$DYLIB_DEST"
    echo "Dylib copied successfully"
else
    echo "Warning: Source dylib not found at $DYLIB_SOURCE"
fi

echo "Post-bundle complete"
