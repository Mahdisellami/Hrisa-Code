# Regression Test Suite

This document contains manual regression tests to verify existing functionality still works after adding multi-model orchestration.

## Prerequisites

```bash
# Make sure you're in the project directory
cd /Users/peng/Documents/mse/private/Hrisa-Code

# Activate virtual environment
source venv/bin/activate

# Make sure Ollama is running
ollama list  # Should show available models

# Make sure you have at least one model
ollama pull qwen2.5-coder:32b  # If you don't have one already
```

---

## Test 1: Basic CLI - Version Check ✓

**Purpose**: Verify CLI entry point works

```bash
hrisa --version
```

**Expected Output**:
```
Hrisa Code version 0.1.0
```

**Status**: [ ] Pass [ ] Fail

---

## Test 2: Basic CLI - Help Text ✓

**Purpose**: Verify help system works

```bash
hrisa --help
```

**Expected Output**: Should show:
- `chat` command
- `models` command
- `init` command
- No errors

**Status**: [ ] Pass [ ] Fail

---

## Test 3: List Models ✓

**Purpose**: Verify Ollama client integration works

```bash
hrisa models
```

**Expected Output**:
- Table showing available Ollama models
- No errors
- Should include at least qwen2.5-coder:32b

**Status**: [ ] Pass [ ] Fail

---

## Test 4: Config Initialization (Simple) ✓

**Purpose**: Verify basic config creation works

```bash
# Create test directory
mkdir -p /tmp/hrisa-test-simple
cd /tmp/hrisa-test-simple

# Initialize config only (skip HRISA generation)
hrisa init --skip-hrisa --force
```

**Expected Output**:
- Creates `.hrisa/config.yaml`
- Shows "Configuration initialized at..."
- Shows "Next steps" message
- No errors

**Verification**:
```bash
cat .hrisa/config.yaml
```

Should show valid YAML config.

**Cleanup**:
```bash
rm -rf /tmp/hrisa-test-simple
```

**Status**: [ ] Pass [ ] Fail

---

## Test 5: Simple HRISA Generation (Non-Comprehensive) ✓

**Purpose**: Verify basic single-prompt HRISA generation still works

```bash
# Create test directory
mkdir -p /tmp/hrisa-test-basic
cd /tmp/hrisa-test-basic

# Create a minimal Python project
cat > main.py << 'EOF'
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
EOF

# Generate HRISA.md (basic mode, not comprehensive)
hrisa init --model qwen2.5-coder:32b --force
```

**Expected Output**:
- Shows "Generating HRISA.md..."
- Shows tip about --comprehensive flag
- Creates HRISA.md file
- No crashes or errors
- NO multi-step orchestration (single prompt only)

**Verification**:
```bash
# Check files created
ls -la .hrisa/config.yaml
ls -la HRISA.md

# Check HRISA.md has content
wc -l HRISA.md  # Should have multiple lines
```

**Cleanup**:
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
rm -rf /tmp/hrisa-test-basic
```

**Status**: [ ] Pass [ ] Fail

---

## Test 6: Comprehensive HRISA (Single Model) ✓

**Purpose**: Verify comprehensive orchestration works WITHOUT multi-model

```bash
# Create test directory
mkdir -p /tmp/hrisa-test-comprehensive
cd /tmp/hrisa-test-comprehensive

# Create a minimal Python project
cat > test.py << 'EOF'
import sys

def add(a, b):
    return a + b

def main():
    print(add(1, 2))

if __name__ == "__main__":
    main()
EOF

# Generate comprehensive HRISA.md (single model)
hrisa init --comprehensive --model qwen2.5-coder:32b --force
```

**Expected Output**:
- Shows "Generating comprehensive HRISA.md..."
- Shows "This will use multi-step orchestration for thorough analysis."
- Shows tip about --multi-model flag
- Shows 5 orchestration steps:
  - Step 1/5: Architecture Discovery
  - Step 2/5: Component Analysis
  - Step 3/5: Feature Identification
  - Step 4/5: Workflow Understanding
  - Step 5/5: Documentation Synthesis
- NO model selection panels (single model throughout)
- Creates HRISA.md
- Shows "✓ Comprehensive HRISA.md generated successfully!"
- No crashes or errors

**Verification**:
```bash
# Check HRISA.md was created and has content
ls -la HRISA.md
wc -l HRISA.md  # Should have many lines (comprehensive)

# Check it has expected sections
grep -i "project overview" HRISA.md
grep -i "tech stack" HRISA.md
grep -i "project structure" HRISA.md
```

**Cleanup**:
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
rm -rf /tmp/hrisa-test-comprehensive
```

**Status**: [ ] Pass [ ] Fail

---

## Test 7: Interactive Chat Session ✓

**Purpose**: Verify interactive chat mode still works

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code

# Start interactive chat (will need to exit manually)
hrisa chat --model qwen2.5-coder:32b
```

**In the chat session, test:**

1. **Basic message**:
   ```
   > Hello, can you help me?
   ```
   Expected: Model responds

2. **Help command**:
   ```
   > /help
   ```
   Expected: Shows available commands

3. **Config command**:
   ```
   > /config
   ```
   Expected: Shows current configuration

4. **Tool usage** (if model supports it):
   ```
   > List the Python files in src/hrisa_code/core/
   ```
   Expected: Model uses tools to list files

5. **Exit**:
   ```
   > /exit
   ```
   Expected: Exits cleanly

**Status**: [ ] Pass [ ] Fail

---

## Test 8: Config with Custom Settings ✓

**Purpose**: Verify config file customization works

```bash
mkdir -p /tmp/hrisa-test-config
cd /tmp/hrisa-test-config

# Initialize with custom model
hrisa init --skip-hrisa --model deepseek-coder --force

# Check config has custom model
grep "deepseek-coder" .hrisa/config.yaml
```

**Expected**: Config file contains `name: deepseek-coder`

**Cleanup**:
```bash
rm -rf /tmp/hrisa-test-config
```

**Status**: [ ] Pass [ ] Fail

---

## Test 9: Global Config ✓

**Purpose**: Verify global config creation works

```bash
# Backup existing global config if it exists
if [ -f ~/.config/hrisa-code/config.yaml ]; then
    cp ~/.config/hrisa-code/config.yaml ~/.config/hrisa-code/config.yaml.backup
fi

# Create global config
hrisa init --global --skip-hrisa --force

# Verify it was created
ls -la ~/.config/hrisa-code/config.yaml
```

**Expected**:
- Creates `~/.config/hrisa-code/config.yaml`
- Shows success message

**Cleanup**:
```bash
# Restore backup if it existed
if [ -f ~/.config/hrisa-code/config.yaml.backup ]; then
    mv ~/.config/hrisa-code/config.yaml.backup ~/.config/hrisa-code/config.yaml
else
    rm -f ~/.config/hrisa-code/config.yaml
fi
```

**Status**: [ ] Pass [ ] Fail

---

## Test 10: Import Test (Python) ✓

**Purpose**: Verify all modules can be imported without errors

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code

python3 << 'EOF'
# Test all imports
print("Testing imports...")

# Core modules
from hrisa_code.core.config import Config
from hrisa_code.core.ollama_client import OllamaClient, OllamaConfig
from hrisa_code.core.conversation import ConversationManager
from hrisa_code.core.interactive import InteractiveSession
from hrisa_code.core.hrisa_orchestrator import HrisaOrchestrator

# New modules
from hrisa_code.core.model_catalog import ModelCatalog, ModelProfile, ModelCapability
from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy

# Tools
from hrisa_code.tools.file_operations import AVAILABLE_TOOLS, get_all_tool_definitions

print("✓ All imports successful!")
print("✓ No syntax errors!")
print("✓ All modules are valid Python!")
EOF
```

**Expected Output**:
```
Testing imports...
✓ All imports successful!
✓ No syntax errors!
✓ All modules are valid Python!
```

**Status**: [ ] Pass [ ] Fail

---

## Test 11: Model Catalog Instantiation ✓

**Purpose**: Verify model catalog works independently

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code

python3 << 'EOF'
from hrisa_code.core.model_catalog import ModelCatalog, ModelCapability

catalog = ModelCatalog()

# Test catalog methods
print("Testing ModelCatalog...")

# List all models
models = catalog.list_all_models()
print(f"✓ Catalog contains {len(models)} models")

# Get models by capability
code_models = catalog.get_models_by_capability(ModelCapability.CODE_ANALYSIS)
print(f"✓ Found {len(code_models)} models with CODE_ANALYSIS capability")

# Get best model for capability
best = catalog.get_best_model_for_capability(ModelCapability.DOCUMENTATION_WRITING)
if best:
    print(f"✓ Best model for documentation: {best.name}")
else:
    print("✗ No model found for documentation")

# Get specific profile
profile = catalog.get_profile("qwen2.5-coder:32b")
if profile:
    print(f"✓ Profile found for qwen2.5-coder:32b")
    print(f"  Quality: {profile.quality_tier.value}")
    print(f"  Speed: {profile.speed_tier.value}")
else:
    print("✗ Profile not found")

print("\n✓ ModelCatalog works correctly!")
EOF
```

**Expected Output**: Should show successful operations, no errors

**Status**: [ ] Pass [ ] Fail

---

## Test 12: Model Router Logic ✓

**Purpose**: Verify model router selection logic works

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code

python3 << 'EOF'
from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy, TaskType

print("Testing ModelRouter...")

# Create router with some available models
strategy = ModelSelectionStrategy(
    available_models={"qwen2.5-coder:32b", "codestral:22b"},
    default_model="qwen2.5-coder:32b"
)
router = ModelRouter(strategy=strategy)

# Test task routing
test_tasks = [
    TaskType.ARCHITECTURE_DISCOVERY,
    TaskType.COMPONENT_ANALYSIS,
    TaskType.DOCUMENTATION_SYNTHESIS,
]

for task in test_tasks:
    model = router.select_model_for_task(task)
    print(f"✓ Task {task.value} → {model}")

# Test orchestration step routing
steps = ["architecture", "components", "features", "workflows", "synthesis"]
for step in steps:
    model = router.select_model_for_orchestration_step(step)
    print(f"✓ Step '{step}' → {model}")

print("\n✓ ModelRouter works correctly!")
EOF
```

**Expected Output**: Should show model selections for each task, no errors

**Status**: [ ] Pass [ ] Fail

---

## Test 13: Conversation Manager Model Switching ✓

**Purpose**: Verify model switching preserves conversation history

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code

python3 << 'EOF'
from hrisa_code.core.ollama_client import OllamaConfig
from hrisa_code.core.conversation import ConversationManager
from pathlib import Path

print("Testing ConversationManager model switching...")

# Create conversation manager
config = OllamaConfig(model="qwen2.5-coder:32b")
conversation = ConversationManager(
    ollama_config=config,
    working_directory=Path.cwd(),
    enable_tools=False  # Disable tools for this test
)

# Check initial model
initial_model = conversation.get_current_model()
print(f"✓ Initial model: {initial_model}")
assert initial_model == "qwen2.5-coder:32b"

# Switch model
conversation.switch_model("deepseek-coder", verbose=False)
new_model = conversation.get_current_model()
print(f"✓ Switched to: {new_model}")
assert new_model == "deepseek-coder"

# Switch back
conversation.switch_model("qwen2.5-coder:32b", verbose=False)
back_model = conversation.get_current_model()
print(f"✓ Switched back to: {back_model}")
assert back_model == "qwen2.5-coder:32b"

print("\n✓ Model switching works correctly!")
EOF
```

**Expected Output**: Should show model switches, no errors

**Status**: [ ] Pass [ ] Fail

---

## Test 14: Backward Compatibility - Old CLI Commands ✓

**Purpose**: Verify old commands still work exactly as before

```bash
# These commands should work EXACTLY as they did before multi-model feature

# 1. Basic init (same as before)
mkdir -p /tmp/hrisa-compat-test
cd /tmp/hrisa-compat-test
hrisa init --force --skip-hrisa
[ -f .hrisa/config.yaml ] && echo "✓ Config created" || echo "✗ Config missing"

# 2. Init with model override (same as before)
rm -rf .hrisa
hrisa init --model codellama --skip-hrisa --force
grep "codellama" .hrisa/config.yaml && echo "✓ Model override works" || echo "✗ Model override failed"

# 3. Models command (same as before)
cd /Users/peng/Documents/mse/private/Hrisa-Code
hrisa models > /tmp/models-output.txt
[ -s /tmp/models-output.txt ] && echo "✓ Models command works" || echo "✗ Models command failed"

# Cleanup
rm -rf /tmp/hrisa-compat-test /tmp/models-output.txt
```

**Expected**: All commands work identically to pre-multi-model behavior

**Status**: [ ] Pass [ ] Fail

---

## Quick Smoke Test (Run All At Once)

For a quick verification, run this script:

```bash
#!/bin/bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
source venv/bin/activate

echo "=== QUICK SMOKE TEST ==="
echo ""

echo "1. Testing imports..."
python3 -c "from hrisa_code.core.model_catalog import ModelCatalog; from hrisa_code.core.model_router import ModelRouter; print('✓ Imports work')"

echo ""
echo "2. Testing CLI..."
hrisa --version

echo ""
echo "3. Testing model catalog..."
python3 -c "from hrisa_code.core.model_catalog import ModelCatalog; c = ModelCatalog(); print(f'✓ Catalog has {len(c.list_all_models())} models')"

echo ""
echo "4. Testing model router..."
python3 -c "from hrisa_code.core.model_router import ModelRouter; r = ModelRouter(); print('✓ Router instantiated')"

echo ""
echo "5. Testing models command..."
hrisa models | head -n 5

echo ""
echo "6. Testing config init..."
mkdir -p /tmp/smoke-test
cd /tmp/smoke-test
hrisa init --skip-hrisa --force > /dev/null 2>&1
if [ -f .hrisa/config.yaml ]; then
    echo "✓ Config creation works"
else
    echo "✗ Config creation failed"
fi
cd /Users/peng/Documents/mse/private/Hrisa-Code
rm -rf /tmp/smoke-test

echo ""
echo "=== SMOKE TEST COMPLETE ==="
echo "If all tests show ✓, basic functionality is intact!"
```

**Save and run**:
```bash
chmod +x tests/smoke_test.sh
./tests/smoke_test.sh
```

---

## Test 15: Git Integration Tools ✓

**Purpose**: Verify git tools work correctly

**Prerequisites**:
```bash
# Create a git repository for testing
mkdir -p /tmp/hrisa-git-test
cd /tmp/hrisa-git-test
git init
echo "# Test" > README.md
git add README.md
git commit -m "Initial commit"
echo "Modified" >> README.md
```

**Test Commands**:
```bash
# In the test directory, start hrisa chat
hrisa chat --model qwen2.5-coder:7b

# Then try these commands in chat:
User: "What's the git status?"
User: "Show me git log"
User: "What branches exist?"
User: "Show me the diff for README.md"
```

**Expected Behavior**:
- `git_status` tool should be called and show modified README.md
- `git_log` tool should show the initial commit
- `git_branch` tool should show current branch
- `git_diff` tool should show the "Modified" addition
- No errors in tool execution

**Status**: [ ] Pass [ ] Fail

---

## Test 16: Loop Detection System ✓

**Purpose**: Verify loop detector prevents repeated tool calls

**Test Setup**:
```bash
cd /tmp/hrisa-git-test
hrisa chat --model qwen2.5-coder:7b
```

**Test Scenario**:
Deliberately ask a question that might cause repeated calls:

```
User: "Check the git status repeatedly until you're sure"
```

**Expected Behavior**:
- Model may call `git_status` 2-3 times
- After 2 identical calls, should see `[LOOP DETECTOR WARNING]` message
- After 3 identical calls, loop detector should intervene
- Intervention message should guide model to provide answer or try different approach
- Model should not call the same tool infinitely

**What to Watch For**:
- Yellow warning after 2 identical calls
- Red intervention message after 3 identical calls
- Model changes behavior after intervention
- Conversation continues productively

**Status**: [ ] Pass [ ] Fail

---

## Test 17: Goal Tracking System ✓

**Purpose**: Verify goal tracker detects task completion

**Test Setup**:
```bash
mkdir -p /tmp/hrisa-goal-test
cd /tmp/hrisa-goal-test
echo "Task data" > data.txt
hrisa chat --model qwen2.5-coder:7b
```

**Test Scenario**:
Ask a simple question that requires minimal tool calls:

```
User: "What's in data.txt?"
```

**Expected Behavior**:
- Model calls `read_file` tool once
- After execution, goal tracker evaluates: "Do we have enough info?"
- May see `[GOAL TRACKER]` message suggesting completion
- Model provides answer based on file contents
- No unnecessary additional tool calls

**What to Watch For**:
- Task completes efficiently (1-2 tool calls max)
- Goal tracker message may appear if helpful
- Model doesn't perform redundant operations
- Clean, focused response

**Status**: [ ] Pass [ ] Fail

---

## Test 18: Background Task Execution ✓

**Purpose**: Verify background task execution works

**Test Setup**:
```bash
cd /tmp/hrisa-goal-test
hrisa chat --model qwen2.5-coder:7b
```

**Test Scenario**:
Request a long-running command:

```
User: "Run 'sleep 5 && echo done' in the background"
```

**Expected Behavior**:
- Model calls `execute_command` with `background=true`
- Response shows:
  - `[BACKGROUND TASK] Command started in background`
  - Task ID (e.g., `task-1`)
  - PID
  - Instructions to check status with `/task <id>`
- Command doesn't block the chat

**Follow-up Test**:
```
User: "Check the status of the background task"
```

Expected: Model should mention task ID or user can manually check.

**Manual Verification**:
```bash
# In a separate terminal
ls ~/.hrisa/tasks/logs/
# Should see task log files
```

**Status**: [ ] Pass [ ] Fail

---

## Test Summary Checklist

After running all tests, verify:

- [ ] Test 1: Version check passes
- [ ] Test 2: Help text displays
- [ ] Test 3: Models list displays
- [ ] Test 4: Config initialization works
- [ ] Test 5: Simple HRISA generation works
- [ ] Test 6: Comprehensive HRISA (single model) works
- [ ] Test 7: Interactive chat works
- [ ] Test 8: Custom config works
- [ ] Test 9: Global config works
- [ ] Test 10: All imports successful
- [ ] Test 11: Model catalog works
- [ ] Test 12: Model router works
- [ ] Test 13: Model switching works
- [ ] Test 14: Backward compatibility maintained
- [ ] Test 15: Git integration tools work
- [ ] Test 16: Loop detection prevents repeated calls
- [ ] Test 17: Goal tracking detects completion
- [ ] Test 18: Background task execution works

**Overall Status**: [ ] All Pass [ ] Some Failures

---

## Reporting Issues

If any test fails:

1. Note which test number failed
2. Copy the exact error message
3. Note what you expected vs. what happened
4. Check if it's related to:
   - Missing models (`ollama list` to verify)
   - Ollama not running (`ollama serve` to start)
   - Import errors (Python syntax issue)
   - Logic errors (feature broken)

---

## Notes

- Tests 1-9 focus on CLI and configuration (should work as before)
- Tests 10-14 verify modules and backward compatibility
- **Tests 15-18 verify new robustness features** (git tools, loop detection, goal tracking, background execution)
- Multi-model feature testing should be done separately after models download

### New Features (Tests 15-18)

**Test 15 - Git Integration**: Adds 4 git tools (status, diff, log, branch) for repository operations

**Test 16 - Loop Detection**: Prevents models from repeatedly calling the same tool with identical arguments. Provides intervention after 3 identical calls.

**Test 17 - Goal Tracking**: Uses lightweight LLM evaluation to detect when sufficient information has been gathered to answer the user's question. Prevents aimless exploration.

**Test 18 - Background Execution**: Allows long-running commands (tests, builds, servers) to run asynchronously without blocking the chat interface.
