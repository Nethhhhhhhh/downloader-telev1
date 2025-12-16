#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create a bin directory
mkdir -p bin

# Download FFmpeg (Static build for Linux)
if [ ! -f bin/ffmpeg ]; then
    echo "Downloading FFmpeg..."
    curl -L https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/ffmpeg-linux-x64 -o bin/ffmpeg
    chmod +x bin/ffmpeg
fi

echo "Build complete."
