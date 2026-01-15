#!/bin/bash

# Emulator Setup Script for AI Pokemon Player
# This script helps set up mGBA and mGBA-http on macOS

set -e

echo "🎮 AI Pokemon Player - Emulator Setup"
echo "======================================="

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install it first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✅ Homebrew found"

# Install mGBA
echo ""
echo "📦 Installing mGBA..."
if brew list --cask mgba &> /dev/null; then
    echo "✅ mGBA already installed"
else
    brew install --cask mgba
    echo "✅ mGBA installed"
fi

# Create mGBA-http directory
MGBA_HTTP_DIR="$(dirname "$0")/mGBA-http"
mkdir -p "$MGBA_HTTP_DIR"

# Download mGBA-http if not present
if [ ! -f "$MGBA_HTTP_DIR/mGBA-http" ]; then
    echo ""
    echo "📦 Downloading mGBA-http..."
    
    # Get latest release
    MGBA_HTTP_URL="https://github.com/nikouu/mGBA-http/releases/latest"
    
    echo "⚠️  Please download mGBA-http manually from:"
    echo "   $MGBA_HTTP_URL"
    echo ""
    echo "   Download the macOS version and place it in:"
    echo "   $MGBA_HTTP_DIR/"
else
    echo "✅ mGBA-http found"
fi

# Download Lua script if not present
LUA_SCRIPT="$MGBA_HTTP_DIR/../scripts/mGBASocketServer.lua"
mkdir -p "$(dirname "$LUA_SCRIPT")"

if [ ! -f "$LUA_SCRIPT" ]; then
    echo ""
    echo "📦 Downloading mGBA socket server script..."
    curl -sL "https://raw.githubusercontent.com/nikouu/mGBA-http/main/mGBASocketServer.lua" -o "$LUA_SCRIPT"
    echo "✅ Lua script downloaded"
else
    echo "✅ Lua script found"
fi

echo ""
echo "======================================="
echo "✅ Setup complete!"
echo ""
echo "📖 To run the emulator:"
echo "   1. Open mGBA: /Applications/mGBA.app"
echo "   2. Load ROM: File > Open ROM > rom.gba"
echo "   3. Load script: Tools > Scripting > Load Script"
echo "      Select: $LUA_SCRIPT"
echo "   4. In a terminal, run: $MGBA_HTTP_DIR/mGBA-http"
echo ""
echo "🚀 Then start the AI player backend and frontend!"
