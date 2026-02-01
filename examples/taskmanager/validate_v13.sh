#!/bin/bash
# V13 Post-Test Validation Script
# Run this AFTER the V13 test completes to automatically check results

echo "================================================"
echo "  V13 Test Validation"
echo "================================================"
echo ""

# Track failures
FAILURES=0
WARNINGS=0

# Test 1: Check file locations (CRITICAL)
echo "Test 1: File Locations"
echo "----------------------"
if [ -f "cli.py" ]; then
    echo "✅ cli.py found at root"
else
    echo "❌ FAIL: cli.py not at root"
    FAILURES=$((FAILURES + 1))
fi

if [ -f "models.py" ] || [ -f "db.py" ]; then
    echo "✅ Data layer file found at root"
else
    echo "❌ FAIL: No data layer files (models.py or db.py) at root"
    FAILURES=$((FAILURES + 1))
fi

if [ -d "src" ]; then
    echo "❌ FAIL: src/ directory created (should NOT exist)"
    FAILURES=$((FAILURES + 1))
    echo "   Files in src/:"
    ls -la src/
else
    echo "✅ No src/ directory (correct)"
fi
echo ""

# Test 2: Syntax validation
echo "Test 2: Syntax Validation"
echo "-------------------------"
if compgen -G "*.py" > /dev/null; then
    if python3 -m py_compile *.py 2>/dev/null; then
        echo "✅ All Python files have valid syntax"
    else
        echo "❌ FAIL: Syntax errors found"
        python3 -m py_compile *.py
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "⚠️  WARNING: No Python files found"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Test 3: Command count
echo "Test 3: Command Implementation"
echo "------------------------------"
if [ -f "cli.py" ]; then
    CMD_COUNT=$(grep -c "^def.*_task\|@app.command" cli.py 2>/dev/null || echo "0")
    if [ "$CMD_COUNT" -ge 4 ]; then
        echo "✅ $CMD_COUNT commands implemented (target: 4+)"
    elif [ "$CMD_COUNT" -ge 1 ]; then
        echo "⚠️  WARNING: Only $CMD_COUNT command(s) implemented (target: 4+)"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "❌ FAIL: No commands found in cli.py"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "⚠️  WARNING: cli.py not found, cannot count commands"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Test 4: Import structure
echo "Test 4: Import Validation"
echo "-------------------------"
if [ -f "cli.py" ]; then
    if grep -q "^from.*import\|^import" cli.py; then
        echo "✅ Imports found in cli.py"

        # Check for common import issues
        if grep -q "^from src\." cli.py; then
            echo "⚠️  WARNING: Imports from 'src.' found (may indicate wrong structure)"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo "⚠️  WARNING: No imports found in cli.py"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  WARNING: cli.py not found, cannot validate imports"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Test 5: File completeness
echo "Test 5: File Completeness"
echo "-------------------------"
EXPECTED_FILES=("cli.py" "models.py" "db.py")
FOUND=0
for FILE in "${EXPECTED_FILES[@]}"; do
    # Check root
    if [ -f "$FILE" ]; then
        echo "✅ $FILE found at root"
        FOUND=$((FOUND + 1))
    # Check src/ (wrong but count it)
    elif [ -f "src/$FILE" ]; then
        echo "⚠️  $FILE found in src/ (wrong location)"
        FOUND=$((FOUND + 1))
        WARNINGS=$((WARNINGS + 1))
    fi
done

if [ $FOUND -lt 2 ]; then
    echo "❌ FAIL: Only $FOUND/3 expected files found"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# Test 6: Check for test files
echo "Test 6: Test Coverage"
echo "--------------------"
if [ -d "tests" ] || compgen -G "test_*.py" > /dev/null; then
    echo "✅ Test files found"
else
    echo "⚠️  WARNING: No test files found (tests/ or test_*.py)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Summary
echo "================================================"
echo "  Validation Summary"
echo "================================================"
echo "Failures: $FAILURES"
echo "Warnings: $WARNINGS"
echo ""

if [ $FAILURES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "🎉 GRADE: A - All tests passed!"
    echo ""
    echo "V13 SUCCESS INDICATORS:"
    echo "✅ Files at root (not in src/)"
    echo "✅ Valid syntax"
    echo "✅ Commands implemented"
    echo "✅ Imports correct"
    exit 0
elif [ $FAILURES -eq 0 ]; then
    echo "⚠️  GRADE: B - Passed with warnings"
    echo ""
    echo "Review warnings above for minor issues"
    exit 0
elif [ $FAILURES -le 2 ]; then
    echo "⚠️  GRADE: C - Some failures"
    echo ""
    echo "Significant issues found, review failures above"
    exit 1
else
    echo "❌ GRADE: F - Critical failures"
    echo ""
    echo "Multiple critical issues, V13 may have regressed"
    exit 1
fi
