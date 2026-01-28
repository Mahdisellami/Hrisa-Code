#!/bin/bash
# Comprehensive test script for Hrisa-Code core functionality

set -e  # Exit on error

echo "=========================================="
echo "Hrisa-Code Comprehensive Functionality Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

test_passed() {
    echo -e "${GREEN}✓ PASSED${NC}: $1"
    ((pass_count++))
}

test_failed() {
    echo -e "${RED}✗ FAILED${NC}: $1"
    ((fail_count++))
}

test_section() {
    echo ""
    echo -e "${YELLOW}==== $1 ====${NC}"
}

# Test 1: Python syntax check
test_section "Python Syntax Validation"
echo "Checking all Python files compile without syntax errors..."
if python3 -m py_compile src/hrisa_code/**/*.py 2>/dev/null; then
    test_passed "All Python files have valid syntax"
else
    test_failed "Syntax errors found in Python files"
fi

# Test 2: Import test
test_section "Module Import Test"
echo "Testing if main modules can be imported..."
if python3 -c "import sys; sys.path.insert(0, 'src'); from hrisa_code.cli import app" 2>/dev/null; then
    test_passed "CLI module imports successfully"
else
    test_failed "CLI module import failed"
fi

if python3 -c "import sys; sys.path.insert(0, 'src'); from hrisa_code.core.ollama_client import OllamaClient" 2>/dev/null; then
    test_passed "OllamaClient imports successfully"
else
    test_failed "OllamaClient import failed"
fi

if python3 -c "import sys; sys.path.insert(0, 'src'); from hrisa_code.core.conversation import ConversationManager" 2>/dev/null; then
    test_passed "ConversationManager imports successfully"
else
    test_failed "ConversationManager import failed"
fi

if python3 -c "import sys; sys.path.insert(0, 'src'); from hrisa_code.core.agent import AgentLoop" 2>/dev/null; then
    test_passed "AgentLoop imports successfully"
else
    test_failed "AgentLoop import failed"
fi

if python3 -c "import sys; sys.path.insert(0, 'src'); from hrisa_code.tools.file_operations import AVAILABLE_TOOLS" 2>/dev/null; then
    test_passed "File operations tools import successfully"
else
    test_failed "File operations import failed"
fi

if python3 -c "import sys; sys.path.insert(0, 'src'); from hrisa_code.tools.git_operations import GIT_TOOLS" 2>/dev/null; then
    test_passed "Git operations tools import successfully"
else
    test_failed "Git operations import failed"
fi

# Test 3: CLI command availability
test_section "CLI Commands Availability"
echo "Checking if hrisa CLI is installed and commands are available..."

if command -v hrisa &> /dev/null; then
    test_passed "hrisa command is available"

    # Test help command
    if hrisa --help &> /dev/null; then
        test_passed "hrisa --help works"
    else
        test_failed "hrisa --help failed"
    fi
else
    echo -e "${YELLOW}⚠ WARNING${NC}: hrisa not installed (run 'pip install -e .')"
fi

# Test 4: Configuration
test_section "Configuration System"
echo "Testing configuration loading..."
if python3 -c "
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.config import load_config, DEFAULT_CONFIG
config = load_config()
assert config is not None
assert hasattr(config, 'model')
assert hasattr(config, 'server')
print('Config loaded successfully')
" 2>/dev/null; then
    test_passed "Configuration system works"
else
    test_failed "Configuration system failed"
fi

# Test 5: Tool definitions
test_section "Tool System"
echo "Verifying tool definitions are valid..."
if python3 -c "
import sys
import json
sys.path.insert(0, 'src')
from hrisa_code.tools.file_operations import AVAILABLE_TOOLS
from hrisa_code.tools.git_operations import GIT_TOOLS

# Merge all tools
all_tools = {**AVAILABLE_TOOLS, **GIT_TOOLS}

# Check each tool has required fields
for name, tool_class in all_tools.items():
    definition = tool_class.get_definition()
    assert 'type' in definition
    assert 'function' in definition
    assert 'name' in definition['function']
    assert 'description' in definition['function']
    assert 'parameters' in definition['function']

print(f'Verified {len(all_tools)} tools')
" 2>/dev/null; then
    test_passed "All tool definitions are valid"
else
    test_failed "Tool definitions validation failed"
fi

# Test 6: Orchestrators
test_section "Orchestrator System"
echo "Testing orchestrators can be instantiated..."
if python3 -c "
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.hrisa_orchestrator import HRISAOrchestrator
from hrisa_code.core.readme_orchestrator import ReadmeOrchestrator
from hrisa_code.core.contributing_orchestrator import ContributingOrchestrator
from hrisa_code.core.api_orchestrator import APIOrchestrator

# Try to instantiate
hrisa_orch = HRISAOrchestrator('/tmp/test', model='test')
readme_orch = ReadmeOrchestrator('/tmp/test', model='test')
contrib_orch = ContributingOrchestrator('/tmp/test', model='test')
api_orch = APIOrchestrator('/tmp/test', model='test')

# Check workflow definitions
assert hrisa_orch.workflow_definition is not None
assert readme_orch.workflow_definition is not None
assert contrib_orch.workflow_definition is not None
assert api_orch.workflow_definition is not None

print('All orchestrators instantiated successfully')
" 2>/dev/null; then
    test_passed "Orchestrators work correctly"
else
    test_failed "Orchestrator instantiation failed"
fi

# Test 7: Approval Manager
test_section "Approval Manager"
echo "Testing approval manager..."
if python3 -c "
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.approval_manager import ApprovalManager

manager = ApprovalManager(auto_approve=True)
assert manager.should_approve('write_file', {'file_path': '/tmp/test.txt', 'content': 'test'}) == True

print('Approval manager works')
" 2>/dev/null; then
    test_passed "Approval manager works correctly"
else
    test_failed "Approval manager test failed"
fi

# Test 8: Loop Detector
test_section "Loop Detector"
echo "Testing loop detector..."
if python3 -c "
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.loop_detector import LoopDetector

detector = LoopDetector(max_identical_calls=3)
call1 = {'tool': 'read_file', 'args': {'file_path': '/tmp/test.txt'}}

# Should allow first 3 calls
assert detector.is_loop([call1]) == False
assert detector.is_loop([call1]) == False
assert detector.is_loop([call1]) == False

# 4th identical call should be detected as loop
assert detector.is_loop([call1]) == True

print('Loop detector works')
" 2>/dev/null; then
    test_passed "Loop detector works correctly"
else
    test_failed "Loop detector test failed"
fi

# Test 9: Goal Tracker
test_section "Goal Tracker"
echo "Testing goal tracker..."
if python3 -c "
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.goal_tracker import GoalTracker

tracker = GoalTracker(task_description='Test task')
assert tracker.is_goal_achieved() == False

# Simulate progress
tracker.record_tool_round(['test'], 'Some output')
tracker.record_tool_round(['test'], 'More output')

print('Goal tracker works')
" 2>/dev/null; then
    test_passed "Goal tracker works correctly"
else
    test_failed "Goal tracker test failed"
fi

# Test 10: Task Manager
test_section "Task Manager"
echo "Testing task manager..."
if python3 -c "
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.task_manager import TaskManager

manager = TaskManager()
assert len(manager.list_tasks()) == 0

# Test task creation
task_id = manager.create_task('echo test')
assert task_id is not None

print('Task manager works')
" 2>/dev/null; then
    test_passed "Task manager works correctly"
else
    test_failed "Task manager test failed"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $pass_count${NC}"
echo -e "${RED}Failed: $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Hrisa-Code is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the errors above.${NC}"
    exit 1
fi
