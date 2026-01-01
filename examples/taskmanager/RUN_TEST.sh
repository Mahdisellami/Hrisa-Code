#!/bin/bash
# Q3 2025 Test V2 - Automated Setup Script
# Run this to prepare for the test

set -e  # Exit on error

echo "================================================"
echo "  Q3 2025 Real Project Test V2 - Setup"
echo "================================================"
echo ""

# Step 1: Clean previous test artifacts
echo "Step 1: Cleaning previous test artifacts..."
rm -rf task_manager taskmanager tests .hrisa .pytest_cache *.db
echo "✓ Cleaned"
echo ""

# Step 2: Verify config
echo "Step 2: Verifying Hrisa config..."
if [ -f ~/.hrisa/config.yaml ]; then
    echo "✓ Config found at ~/.hrisa/config.yaml"
    echo ""
    echo "Current model:"
    grep "name:" ~/.hrisa/config.yaml | head -1
else
    echo "⚠ No config found, will use default"
fi
echo ""

# Step 3: Ready to start
echo "================================================"
echo "  READY TO START TEST!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. In a SECOND TERMINAL, start model download:"
echo "   ollama pull deepseek-r1:14b"
echo ""
echo "2. In THIS TERMINAL, press ENTER to start Hrisa..."
read -p ""

# Start Hrisa
echo ""
echo "Starting Hrisa Chat..."
echo ""
hrisa chat
