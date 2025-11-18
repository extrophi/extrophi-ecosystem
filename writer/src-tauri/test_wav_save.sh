#!/bin/bash

# Test WAV save functionality using existing test file

SOURCE_WAV="/Users/kjd/01-projects/IAC-30-brain-dump-voice-processor/tests/test1.wav"
TARGET_DIR="/Users/kjd/09-personal/BrainDumpSessions/audio"
TEST_FILENAME="$(date +%Y-%m-%d_%H-%M-%S)_recording.wav"
TARGET_PATH="$TARGET_DIR/$TEST_FILENAME"

echo "Testing WAV file save functionality..."
echo "Source: $SOURCE_WAV"
echo "Target: $TARGET_PATH"
echo ""

# Verify source exists
if [ ! -f "$SOURCE_WAV" ]; then
    echo "ERROR: Source WAV file not found!"
    exit 1
fi

# Copy to simulate save
cp "$SOURCE_WAV" "$TARGET_PATH"

# Verify save
if [ -f "$TARGET_PATH" ]; then
    echo "SUCCESS: WAV file saved successfully!"
    echo ""
    ls -lh "$TARGET_PATH"
    echo ""
    file "$TARGET_PATH"
    echo ""
    echo "File path: $TARGET_PATH"
else
    echo "ERROR: Failed to save WAV file!"
    exit 1
fi
