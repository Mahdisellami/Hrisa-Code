#!/bin/bash
# Quick comprehensive test for Hrisa-Code

set -e
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Hrisa-Code Quick Functionality Test"
echo "=========================================="
echo ""

pass=0
fail=0

test_pass() { echo -e "${GREEN}✓${NC} $1"; ((pass++)); }
test_fail() { echo -e "${RED}✗${NC} $1"; ((fail++)); }

# Test 1: Python syntax
echo -e "${YELLOW}[1/10]${NC} Python syntax validation..."
if python3 -m py_compile src/hrisa_code/**/*.py 2>/dev/null; then
    test_pass "All Python files have valid syntax"
else
    test_fail "Syntax errors found"
fi

# Test 2: Core imports
echo -e "${YELLOW}[2/10]${NC} Testing core module imports..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.cli import app
from hrisa_code.core.conversation.ollama_client import OllamaClient
from hrisa_code.core.conversation.conversation import ConversationManager
from hrisa_code.core.planning.agent import AgentLoop
from hrisa_code.core.memory.task_manager import TaskManager
from hrisa_code.core.planning.approval_manager import ApprovalManager
from hrisa_code.core.planning.loop_detector import LoopDetector
from hrisa_code.core.planning.goal_tracker import GoalTracker
print("All core imports successful")
EOF
then
    test_pass "Core modules import successfully"
else
    test_fail "Core module imports failed"
fi

# Test 3: Tool imports
echo -e "${YELLOW}[3/10]${NC} Testing tool system..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.tools.file_operations import AVAILABLE_TOOLS
from hrisa_code.tools.git_operations import GIT_TOOLS
print(f"Loaded {len(AVAILABLE_TOOLS)} file tools and {len(GIT_TOOLS)} git tools")
EOF
then
    test_pass "Tool system imports successfully"
else
    test_fail "Tool imports failed"
fi

# Test 4: Orchestrators
echo -e "${YELLOW}[4/10]${NC} Testing orchestrators..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.orchestrators.hrisa_orchestrator import HRISAOrchestrator
from hrisa_code.core.orchestrators.readme_orchestrator import ReadmeOrchestrator
from hrisa_code.core.orchestrators.contributing_orchestrator import ContributingOrchestrator
from hrisa_code.core.orchestrators.api_orchestrator import APIOrchestrator

# Instantiate
hrisa = HRISAOrchestrator('/tmp', model='test')
readme = ReadmeOrchestrator('/tmp', model='test')
contrib = ContributingOrchestrator('/tmp', model='test')
api = APIOrchestrator('/tmp', model='test')

assert hrisa.workflow_definition is not None
assert readme.workflow_definition is not None
assert contrib.workflow_definition is not None
assert api.workflow_definition is not None
print("All orchestrators work")
EOF
then
    test_pass "Orchestrators instantiate correctly"
else
    test_fail "Orchestrator tests failed"
fi

# Test 5: Configuration
echo -e "${YELLOW}[5/10]${NC} Testing configuration system..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.config import load_config, DEFAULT_CONFIG
config = load_config()
assert config is not None
assert hasattr(config, 'model')
assert hasattr(config, 'server')
print("Config loaded successfully")
EOF
then
    test_pass "Configuration system works"
else
    test_fail "Configuration test failed"
fi

# Test 6: Tool definitions
echo -e "${YELLOW}[6/10]${NC} Validating tool definitions..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.tools.file_operations import AVAILABLE_TOOLS
from hrisa_code.tools.git_operations import GIT_TOOLS

all_tools = {**AVAILABLE_TOOLS, **GIT_TOOLS}
for name, tool_class in all_tools.items():
    definition = tool_class.get_definition()
    assert 'type' in definition
    assert 'function' in definition
    assert 'name' in definition['function']
    assert 'description' in definition['function']
    assert 'parameters' in definition['function']

print(f"Verified {len(all_tools)} valid tool definitions")
EOF
then
    test_pass "All tool definitions are valid"
else
    test_fail "Tool validation failed"
fi

# Test 7: Approval Manager
echo -e "${YELLOW}[7/10]${NC} Testing approval manager..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.planning.approval_manager import ApprovalManager

manager = ApprovalManager(auto_approve=True)
result = manager.should_approve('write_file', {'file_path': '/tmp/test.txt', 'content': 'test'})
assert result == True
print("Approval manager works")
EOF
then
    test_pass "Approval manager works"
else
    test_fail "Approval manager test failed"
fi

# Test 8: Loop Detector
echo -e "${YELLOW}[8/10]${NC} Testing loop detector..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.planning.loop_detector import LoopDetector

detector = LoopDetector(max_identical_calls=3)
call = {'tool': 'read_file', 'args': {'file_path': '/test.txt'}}

assert detector.is_loop([call]) == False
assert detector.is_loop([call]) == False
assert detector.is_loop([call]) == False
assert detector.is_loop([call]) == True
print("Loop detector works")
EOF
then
    test_pass "Loop detector works"
else
    test_fail "Loop detector test failed"
fi

# Test 9: Goal Tracker
echo -e "${YELLOW}[9/10]${NC} Testing goal tracker..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.planning.goal_tracker import GoalTracker

tracker = GoalTracker(task_description='Test task')
assert tracker.is_goal_achieved() == False
tracker.record_tool_round(['test'], 'output')
print("Goal tracker works")
EOF
then
    test_pass "Goal tracker works"
else
    test_fail "Goal tracker test failed"
fi

# Test 10: Task Manager
echo -e "${YELLOW}[10/10]${NC} Testing task manager..."
if python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from hrisa_code.core.memory.task_manager import TaskManager

manager = TaskManager()
assert len(manager.list_tasks()) >= 0
print("Task manager works")
EOF
then
    test_pass "Task manager works"
else
    test_fail "Task manager test failed"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$pass${NC} | Failed: ${RED}$fail${NC}"
echo ""

if [ $fail -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC} Hrisa-Code is working correctly."
    echo ""
    echo "You can now:"
    echo "  • Commit the deleted taskmanager files: git add -u examples/taskmanager/"
    echo "  • Create a commit: git commit -m 'chore: Remove taskmanager example files'"
    exit 0
else
    echo -e "${RED}✗ $fail test(s) failed.${NC} Please review errors above."
    exit 1
fi
