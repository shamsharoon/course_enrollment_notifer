#!/bin/bash

# Course Availability Notifier - Run Script
# Make this file executable with: chmod +x run.sh

set -e  # Exit on any error

echo "🎓 Course Availability Notifier Startup"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
echo "📋 Installing dependencies..."
pip install -U pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Please copy env.example to .env and configure your settings:"
    echo "   cp env.example .env"
    echo "   nano .env"
    exit 1
fi

# Check if Chrome/Chromium is installed
if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    echo "⚠️  Chrome/Chromium not found!"
    echo "📦 Please install Chrome or Chromium:"
    echo "   Ubuntu/Debian: sudo apt-get install google-chrome-stable"
    echo "   CentOS/RHEL: sudo yum install google-chrome-stable"
    echo "   macOS: brew install --cask google-chrome"
    exit 1
fi

# Create chrome profile directory
if [ ! -d "chrome_profile" ]; then
    echo "🌐 Creating Chrome profile directory..."
    mkdir -p chrome_profile
fi

# Run the application
echo "🚀 Starting Course Availability Notifier..."
echo "📱 Monitor will send SMS alerts to the configured number"
echo "⏹️  Press Ctrl+C to stop"
echo ""

python main.py 