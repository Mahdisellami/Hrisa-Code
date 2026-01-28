#!/bin/bash
# Clean ALL V9 artifacts before V10 test

echo "=========================================="
echo "  V10 Environment Cleanup"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

echo "Removing generated code directories..."
rm -rf taskmanager/ src/ tests/ task_manager/

echo "Removing Python files at root..."
rm -f *.py

echo "Removing caches and databases..."
rm -rf __pycache__/ .pytest_cache/ .mypy_cache/
rm -f *.db *.db-journal

echo "Clearing Hrisa history (fresh start)..."
rm -f .hrisa/history.txt

echo ""
echo "✓ Cleanup complete"
echo ""
echo "=========================================="
echo "  Remaining Files"
echo "=========================================="
ls -la | grep -v "^total" | grep -v "^d" | head -20
echo ""
echo "Ready for V10 test!"
echo ""
