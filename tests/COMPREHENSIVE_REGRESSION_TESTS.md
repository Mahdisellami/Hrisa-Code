# Comprehensive Regression Test Suite

**Living Document** - Update this as new features are added!

This test suite covers ALL features implemented in Hrisa Code. Run these tests after any significant change to ensure nothing breaks.

---

## Test Environment Setup

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
source venv/bin/activate

# Ensure Ollama is running
ollama list

# Ensure you have at least one working model
ollama pull qwen2.5-coder:32b  # Or any model you prefer
```

---

## Feature Matrix

| # | Feature | Status | Version Added |
|---|---------|--------|---------------|
| 1 | Basic CLI | ✅ | v0.1.0 |
| 2 | Configuration Management | ✅ | v0.1.0 |
| 3 | Ollama Integration | ✅ | v0.1.0 |
| 4 | File Operations Tools | ✅ | v0.1.0 |
| 5 | Interactive Chat | ✅ | v0.1.0 |
| 6 | Multi-Turn Tool Calling | ✅ | v0.1.0 |
| 7 | Text-Based Tool Parsing | ✅ | v0.1.0 |
| 8 | Simple HRISA Generation | ✅ | v0.1.0 |
| 9 | Comprehensive HRISA (Orchestration) | ✅ | v0.1.0 |
| 10 | Agent Mode | ✅ | v0.1.0 |
| 11 | Background Task Execution | ✅ | v0.1.0 |
| 12 | Multi-Model Orchestration | ✅ | v0.1.0 |

---

# Test Suite

## CATEGORY 1: Basic CLI Functionality

### Test 1.1: Version Display ✓
**Feature**: Basic CLI
**Command**:
```bash
hrisa --version
```
**Expected**:
- Displays: `Hrisa Code version 0.1.0`
- Exits cleanly
- No errors

**Status**: [ ] Pass [ ] Fail

---

### Test 1.2: Help Text ✓
**Feature**: Basic CLI
**Command**:
```bash
hrisa --help
```
**Expected**:
- Shows available commands: `chat`, `models`, `init`
- Shows description: "A CLI coding assistant powered by local LLMs via Ollama"
- No errors

**Status**: [ ] Pass [ ] Fail

---

### Test 1.3: Subcommand Help ✓
**Feature**: Basic CLI
**Commands**:
```bash
hrisa chat --help
hrisa models --help
hrisa init --help
```
**Expected**:
- Each shows relevant options and flags
- No errors

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 2: Configuration Management

### Test 2.1: Project Config Creation ✓
**Feature**: Configuration Management
**Commands**:
```bash
mkdir -p /tmp/test-config-1
cd /tmp/test-config-1
hrisa init --skip-hrisa --force
```
**Expected**:
- Creates `.hrisa/config.yaml`
- Config contains default values
- Shows success message

**Verification**:
```bash
cat .hrisa/config.yaml
# Should show model, ollama, tools sections
```
**Cleanup**: `rm -rf /tmp/test-config-1`

**Status**: [ ] Pass [ ] Fail

---

### Test 2.2: Global Config Creation ✓
**Feature**: Configuration Management
**Commands**:
```bash
# Backup existing config if present
[ -f ~/.config/hrisa-code/config.yaml ] && \
  cp ~/.config/hrisa-code/config.yaml ~/.config/hrisa-code/config.yaml.backup

hrisa init --global --skip-hrisa --force
```
**Expected**:
- Creates `~/.config/hrisa-code/config.yaml`
- Shows success message

**Verification**:
```bash
cat ~/.config/hrisa-code/config.yaml
```
**Cleanup**: Restore backup if it existed

**Status**: [ ] Pass [ ] Fail

---

### Test 2.3: Custom Model Override ✓
**Feature**: Configuration Management
**Commands**:
```bash
mkdir -p /tmp/test-config-2
cd /tmp/test-config-2
hrisa init --model deepseek-coder --skip-hrisa --force
grep "deepseek-coder" .hrisa/config.yaml
```
**Expected**:
- Config contains `name: deepseek-coder`

**Cleanup**: `rm -rf /tmp/test-config-2`

**Status**: [ ] Pass [ ] Fail

---

### Test 2.4: Config Priority (Project > Global) ✓
**Feature**: Configuration Management
**Setup**:
```bash
mkdir -p /tmp/test-config-priority
cd /tmp/test-config-priority

# Create global config with model A
hrisa init --global --model model-a --skip-hrisa --force

# Create project config with model B
hrisa init --model model-b --skip-hrisa --force
```
**Test**: Start chat and check which model is used
```bash
# In interactive test, /config should show model-b (project config takes priority)
```
**Expected**: Project config overrides global config

**Cleanup**:
```bash
rm -rf /tmp/test-config-priority
rm ~/.config/hrisa-code/config.yaml  # Or restore backup
```

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 3: Ollama Integration

### Test 3.1: List Available Models ✓
**Feature**: Ollama Integration
**Command**:
```bash
hrisa models
```
**Expected**:
- Shows table of available models
- No errors
- At least one model listed

**Status**: [ ] Pass [ ] Fail

---

### Test 3.2: Custom Ollama Host ✓
**Feature**: Ollama Integration
**Command**:
```bash
hrisa models --host http://localhost:11434
```
**Expected**:
- Connects to specified host
- Lists models
- No errors

**Status**: [ ] Pass [ ] Fail

---

### Test 3.3: Connection Error Handling ✓
**Feature**: Ollama Integration
**Command**:
```bash
# Stop Ollama first (if running)
hrisa models --host http://localhost:99999  # Invalid port
```
**Expected**:
- Shows clear error message
- Suggests running `ollama serve`
- Exits gracefully

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 4: File Operations Tools

### Test 4.1: Read File Tool ✓
**Feature**: File Operations
**Setup**:
```bash
mkdir -p /tmp/test-tools
cd /tmp/test-tools
echo "Test content" > test.txt
```
**Command**: Start chat and ask to read file
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "Read the file test.txt"
```
**Expected**:
- Model uses `read_file` tool
- Shows file content: "Test content"
- No errors

**Cleanup**: `rm -rf /tmp/test-tools`

**Status**: [ ] Pass [ ] Fail

---

### Test 4.2: Write File Tool ✓
**Feature**: File Operations
**Setup**:
```bash
mkdir -p /tmp/test-tools-write
cd /tmp/test-tools-write
```
**Command**: Start chat and ask to write file
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "Write 'Hello World' to hello.txt"
```
**Expected**:
- Model uses `write_file` tool
- Creates hello.txt with content
- Shows success message

**Verification**:
```bash
cat hello.txt  # Should show "Hello World"
```
**Cleanup**: `rm -rf /tmp/test-tools-write`

**Status**: [ ] Pass [ ] Fail

---

### Test 4.3: Search Files Tool ✓
**Feature**: File Operations
**Setup**:
```bash
mkdir -p /tmp/test-search
cd /tmp/test-search
cat > file1.py << 'EOF'
def hello():
    print("hello")
EOF
cat > file2.py << 'EOF'
def goodbye():
    print("goodbye")
EOF
```
**Command**: Start chat and ask to search
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "Search for Python files in the current directory"
```
**Expected**:
- Model uses `search_files` or `execute_command` tool
- Finds file1.py and file2.py
- No errors

**Cleanup**: `rm -rf /tmp/test-search`

**Status**: [ ] Pass [ ] Fail

---

### Test 4.4: Execute Command Tool ✓
**Feature**: File Operations
**Command**: Start chat
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
hrisa chat --model qwen2.5-coder:32b
# In chat: "List the files in src/hrisa_code/core/"
```
**Expected**:
- Model uses `execute_command` tool with `ls`
- Shows directory contents
- No errors

**Status**: [ ] Pass [ ] Fail

---

### Test 4.5: Path Validation ✓
**Feature**: File Operations (Security)
**Command**: Start chat
```bash
cd /tmp
hrisa chat --model qwen2.5-coder:32b
# In chat: "Read the file /etc/passwd"
```
**Expected**:
- Tool rejects access (path outside working directory)
- Shows error message about path restrictions
- Does NOT read the file

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 5: Interactive Chat

### Test 5.1: Basic Chat Session ✓
**Feature**: Interactive Chat
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
```
**In session, test**:
1. Send message: "Hello"
2. Check model responds
3. Type `/help` - should show commands
4. Type `/exit` - should exit cleanly

**Expected**:
- Session starts
- Model responds to messages
- Commands work
- Clean exit

**Status**: [ ] Pass [ ] Fail

---

### Test 5.2: Chat Commands ✓
**Feature**: Interactive Chat
**Command**: Start chat, test all commands
```bash
hrisa chat --model qwen2.5-coder:32b

# Test these commands:
/help      # Shows available commands
/config    # Shows current configuration
/clear     # Clears conversation history
/save      # Saves conversation (specify filename)
/exit      # Exits session
```
**Expected**: All commands work without errors

**Status**: [ ] Pass [ ] Fail

---

### Test 5.3: Conversation History ✓
**Feature**: Interactive Chat
**Command**: Start chat
```bash
hrisa chat --model qwen2.5-coder:32b

# In chat:
> My name is Alice
> What is my name?  # Should remember "Alice"
```
**Expected**:
- Model remembers previous messages
- Can reference earlier conversation

**Status**: [ ] Pass [ ] Fail

---

### Test 5.4: Save and Load Conversation ✓
**Feature**: Interactive Chat
**Commands**:
```bash
hrisa chat --model qwen2.5-coder:32b

# In chat:
> Tell me about Python
> /save /tmp/conv-test.json
> /exit

# Verify saved
cat /tmp/conv-test.json  # Should show JSON conversation data
```
**Expected**:
- Conversation saved to file
- JSON contains messages
- File can be loaded later (manual load feature if implemented)

**Cleanup**: `rm /tmp/conv-test.json`

**Status**: [ ] Pass [ ] Fail

---

### Test 5.5: Custom Working Directory ✓
**Feature**: Interactive Chat
**Command**:
```bash
hrisa chat --working-dir /tmp --model qwen2.5-coder:32b

# In chat: "List files in the current directory"
```
**Expected**:
- Chat session operates in /tmp directory
- File operations are relative to /tmp

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 6: Multi-Turn Tool Calling

### Test 6.1: Multiple Tool Calls in Single Response ✓
**Feature**: Multi-Turn Tool Calling
**Setup**:
```bash
mkdir -p /tmp/test-multi-turn
cd /tmp/test-multi-turn
echo "content1" > file1.txt
echo "content2" > file2.txt
```
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "Read both file1.txt and file2.txt"
```
**Expected**:
- Model makes multiple `read_file` calls
- Shows both file contents
- Handles multiple tool calls in succession

**Cleanup**: `rm -rf /tmp/test-multi-turn`

**Status**: [ ] Pass [ ] Fail

---

### Test 6.2: Tool Call → Response → Tool Call Chain ✓
**Feature**: Multi-Turn Tool Calling
**Command**:
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
hrisa chat --model qwen2.5-coder:32b
# In chat: "Find all Python files in src/, then tell me about config.py"
```
**Expected**:
- Model first uses search/list tools
- Then uses read_file on config.py
- Shows chain of tool calls
- Provides final answer

**Status**: [ ] Pass [ ] Fail

---

### Test 6.3: Tool Error Recovery ✓
**Feature**: Multi-Turn Tool Calling
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "Read the file nonexistent.txt"
```
**Expected**:
- Tool returns error (file not found)
- Model acknowledges error
- Suggests alternatives or asks for clarification
- Doesn't crash

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 7: Text-Based Tool Parsing

### Test 7.1: JSON Tool Call Detection ✓
**Feature**: Text-Based Tool Parsing
**Command**: Use model known to output JSON as text (e.g., qwen2.5-coder:32b)
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "List files in the current directory"
```
**Expected**:
- Console shows: `→ Detected text-based tool call: execute_command`
- Tool executes correctly
- Result displayed

**Status**: [ ] Pass [ ] Fail

---

### Test 7.2: Multiple Text-Based Tool Calls ✓
**Feature**: Text-Based Tool Parsing
**Command**:
```bash
mkdir -p /tmp/test-text-tools
cd /tmp/test-text-tools
echo "test" > a.txt
echo "test" > b.txt

hrisa chat --model qwen2.5-coder:32b
# In chat: "Read both a.txt and b.txt"
```
**Expected**:
- Multiple `→ Detected text-based tool call` messages
- Both files read correctly
- No errors

**Cleanup**: `rm -rf /tmp/test-text-tools`

**Status**: [ ] Pass [ ] Fail

---

### Test 7.3: Malformed JSON Handling ✓
**Feature**: Text-Based Tool Parsing
**Note**: Hard to test directly, but system should handle gracefully
**Expected Behavior**:
- Skips malformed JSON
- Shows: `→ Skipped malformed tool call`
- Continues processing
- No crashes

**Status**: [ ] Pass [ ] Fail (Observable in logs during normal use)

---

## CATEGORY 8: Simple HRISA Generation

### Test 8.1: Basic HRISA.md Creation ✓
**Feature**: Simple HRISA Generation
**Command**:
```bash
mkdir -p /tmp/test-hrisa-simple
cd /tmp/test-hrisa-simple
cat > main.py << 'EOF'
def main():
    print("Hello")
if __name__ == "__main__":
    main()
EOF

hrisa init --model qwen2.5-coder:32b --force
```
**Expected**:
- Shows "Generating HRISA.md..."
- Shows tip about --comprehensive flag
- Creates HRISA.md
- Single prompt (NO multi-step orchestration)
- Completes in reasonable time

**Verification**:
```bash
ls HRISA.md
wc -l HRISA.md  # Should have content
grep -i "project" HRISA.md  # Should mention project
```
**Cleanup**: `rm -rf /tmp/test-hrisa-simple`

**Status**: [ ] Pass [ ] Fail

---

### Test 8.2: HRISA with Existing Config ✓
**Feature**: Simple HRISA Generation
**Command**:
```bash
mkdir -p /tmp/test-hrisa-config
cd /tmp/test-hrisa-config
hrisa init --skip-hrisa --force  # Create config first
hrisa init --force  # Generate HRISA.md
```
**Expected**:
- Uses existing config
- Doesn't ask to overwrite config
- Generates HRISA.md

**Cleanup**: `rm -rf /tmp/test-hrisa-config`

**Status**: [ ] Pass [ ] Fail

---

### Test 8.3: Skip HRISA Flag ✓
**Feature**: Simple HRISA Generation
**Command**:
```bash
mkdir -p /tmp/test-skip-hrisa
cd /tmp/test-skip-hrisa
hrisa init --skip-hrisa --force
```
**Expected**:
- Creates config only
- Does NOT create HRISA.md
- Shows success message

**Verification**:
```bash
ls .hrisa/config.yaml  # Should exist
ls HRISA.md 2>&1 | grep "No such file"  # Should not exist
```
**Cleanup**: `rm -rf /tmp/test-skip-hrisa`

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 9: Comprehensive HRISA (Orchestration)

### Test 9.1: Basic Orchestration (5 Steps) ✓
**Feature**: Comprehensive HRISA Orchestration
**Command**:
```bash
mkdir -p /tmp/test-comprehensive
cd /tmp/test-comprehensive
cat > app.py << 'EOF'
import sys
def add(a, b):
    return a + b
EOF

hrisa init --comprehensive --model qwen2.5-coder:32b --force
```
**Expected**:
- Shows "Generating comprehensive HRISA.md..."
- Shows "multi-step orchestration" message
- Displays 5 orchestration steps:
  - Step 1/5: Architecture Discovery
  - Step 2/5: Component Analysis
  - Step 3/5: Feature Identification
  - Step 4/5: Workflow Understanding
  - Step 5/5: Documentation Synthesis
- Each step shows progress panel
- NO model selection panels (single model)
- Creates comprehensive HRISA.md
- Shows completion message

**Verification**:
```bash
ls HRISA.md
wc -l HRISA.md  # Should be comprehensive (many lines)
```
**Cleanup**: `rm -rf /tmp/test-comprehensive`

**Status**: [ ] Pass [ ] Fail

---

### Test 9.2: Orchestration Tool Usage ✓
**Feature**: Comprehensive HRISA Orchestration
**Command**: Run comprehensive generation and monitor output
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
hrisa init --comprehensive --model qwen2.5-coder:32b --force
```
**Expected**:
- Each step uses tools to explore codebase
- Shows tool executions (read_file, search_files, execute_command)
- Multiple tool rounds per step
- Shows "Findings" after each step

**Status**: [ ] Pass [ ] Fail

---

### Test 9.3: Orchestration Discovery Storage ✓
**Feature**: Comprehensive HRISA Orchestration
**Expected Behavior** (internal, observable through output quality):
- Each step's findings stored internally
- Step 5 (Synthesis) uses all previous discoveries
- Final HRISA.md incorporates insights from all steps
- More comprehensive than simple generation

**Status**: [ ] Pass [ ] Fail (Observable through output quality)

---

## CATEGORY 10: Agent Mode

### Test 10.1: Agent Mode Exists ✓
**Feature**: Agent Mode
**Command**: Check if agent mode is accessible
```bash
# Check if agent.py exists
ls src/hrisa_code/core/agent.py
```
**Expected**: File exists

**Status**: [ ] Pass [ ] Fail

---

### Test 10.2: Agent Mode Import ✓
**Feature**: Agent Mode
**Command**:
```bash
python3 << 'EOF'
try:
    from hrisa_code.core.agent import Agent
    print("✓ Agent module imports successfully")
except ImportError as e:
    print(f"✗ Agent import failed: {e}")
EOF
```
**Expected**: Agent class can be imported

**Status**: [ ] Pass [ ] Fail

---

### Test 10.3: Agent Mode Execution ✓
**Feature**: Agent Mode
**Note**: If agent mode has dedicated CLI entry, test it. If integrated into chat/orchestration, test through those interfaces.
**Command**: (Adapt based on your agent mode interface)
```bash
# Example if there's an --agent flag:
# hrisa chat --agent --model qwen2.5-coder:32b
```
**Expected**:
- Agent mode activates
- Shows agent-specific behavior (reflection, planning, etc.)
- Completes tasks autonomously

**Status**: [ ] Pass [ ] Fail (Requires agent mode interface)

---

## CATEGORY 11: Background Task Execution

### Test 11.1: Task Manager Exists ✓
**Feature**: Background Task Execution
**Command**:
```bash
ls src/hrisa_code/core/task_manager.py
```
**Expected**: File exists

**Status**: [ ] Pass [ ] Fail

---

### Test 11.2: Task Manager Import ✓
**Feature**: Background Task Execution
**Command**:
```bash
python3 << 'EOF'
try:
    from hrisa_code.core.task_manager import TaskManager
    print("✓ TaskManager imports successfully")
except ImportError as e:
    print(f"✗ TaskManager import failed: {e}")
EOF
```
**Expected**: TaskManager class can be imported

**Status**: [ ] Pass [ ] Fail

---

### Test 11.3: Background Command Execution ✓
**Feature**: Background Task Execution
**Command**: Start chat and run background task
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "Run 'sleep 5 && echo done' in the background"
```
**Expected**:
- Command starts in background
- Returns immediately (doesn't block)
- Can continue chatting
- Eventually shows command completion

**Status**: [ ] Pass [ ] Fail

---

### Test 11.4: Task Status Monitoring ✓
**Feature**: Background Task Execution
**Expected** (if implemented):
- Can query task status
- Can list running tasks
- Can cancel tasks
- Can get task output

**Status**: [ ] Pass [ ] Fail (Depends on implementation)

---

## CATEGORY 12: Multi-Model Orchestration

### Test 12.1: Model Catalog ✓
**Feature**: Multi-Model Orchestration
**Command**:
```bash
python3 << 'EOF'
from hrisa_code.core.model_catalog import ModelCatalog, ModelCapability
catalog = ModelCatalog()
models = catalog.list_all_models()
print(f"✓ Catalog contains {len(models)} models")
code_models = catalog.get_models_by_capability(ModelCapability.CODE_ANALYSIS)
print(f"✓ {len(code_models)} models have CODE_ANALYSIS capability")
EOF
```
**Expected**:
- Shows number of models in catalog
- Shows models by capability
- No errors

**Status**: [ ] Pass [ ] Fail

---

### Test 12.2: Model Router Selection ✓
**Feature**: Multi-Model Orchestration
**Command**:
```bash
python3 << 'EOF'
from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy, TaskType
strategy = ModelSelectionStrategy(
    available_models={"qwen2.5-coder:32b", "qwen2.5:72b"},
    default_model="qwen2.5-coder:32b"
)
router = ModelRouter(strategy=strategy)
model = router.select_model_for_task(TaskType.CODE_ANALYSIS)
print(f"✓ Selected model for CODE_ANALYSIS: {model}")
model2 = router.select_model_for_task(TaskType.DOCUMENTATION_SYNTHESIS)
print(f"✓ Selected model for DOCUMENTATION: {model2}")
EOF
```
**Expected**:
- Shows selected models
- Different tasks may select different models
- Falls back intelligently

**Status**: [ ] Pass [ ] Fail

---

### Test 12.3: Model Switching ✓
**Feature**: Multi-Model Orchestration
**Command**:
```bash
python3 << 'EOF'
from hrisa_code.core.ollama_client import OllamaClient, OllamaConfig
config = OllamaConfig(model="model1")
client = OllamaClient(config)
assert client.get_current_model() == "model1"
client.switch_model("model2")
assert client.get_current_model() == "model2"
print("✓ Model switching works")
EOF
```
**Expected**:
- Model switches successfully
- Conversation history preserved
- No errors

**Status**: [ ] Pass [ ] Fail

---

### Test 12.4: Multi-Model Orchestration (Requires Large Models) ⏳
**Feature**: Multi-Model Orchestration
**Prerequisites**:
- qwen2.5:72b
- deepseek-coder-v2:236b
- llama3.1:70b
- deepseek-r1:70b (optional)

**Command**:
```bash
mkdir -p /tmp/test-multi-model
cd /tmp/test-multi-model
cat > test.py << 'EOF'
def hello():
    print("Hello, World!")
EOF

hrisa init --comprehensive --multi-model --force
```
**Expected**:
- Shows "multi-model orchestration" message
- Shows "Found X available models"
- Before each step, shows yellow "Model Selection" panel
- Panel shows selected model and reason
- Different models used for different steps:
  - Architecture → qwen2.5:72b or similar
  - Components → deepseek-coder-v2:236b or best code model
  - Features → qwen2.5:72b or pattern model
  - Workflows → deepseek-r1:70b or reasoning model
  - Synthesis → llama3.1:70b or documentation model
- Creates comprehensive HRISA.md
- Shows completion message

**Cleanup**: `rm -rf /tmp/test-multi-model`

**Status**: [ ] Pass [ ] Fail [ ] ⏳ Pending (models not downloaded yet)

---

### Test 12.5: Multi-Model Fallback ✓
**Feature**: Multi-Model Orchestration
**Command**: Run multi-model with limited available models
```bash
# Only have qwen2.5-coder:32b available
mkdir -p /tmp/test-fallback
cd /tmp/test-fallback
hrisa init --comprehensive --multi-model --model qwen2.5-coder:32b --force
```
**Expected**:
- Attempts multi-model orchestration
- Falls back to qwen2.5-coder:32b for all steps (best available)
- Shows model selection panels explaining fallback
- Completes successfully
- No errors

**Cleanup**: `rm -rf /tmp/test-fallback`

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 13: Error Handling & Edge Cases

### Test 13.1: Invalid Model Name ✓
**Feature**: Error Handling
**Command**:
```bash
hrisa chat --model nonexistent-model
```
**Expected**:
- Shows clear error message
- Suggests running `ollama pull`
- Exits gracefully
- No crash

**Status**: [ ] Pass [ ] Fail

---

### Test 13.2: Ollama Not Running ✓
**Feature**: Error Handling
**Command**: Stop Ollama, then:
```bash
hrisa models
```
**Expected**:
- Shows connection error
- Suggests running `ollama serve`
- Exits gracefully
- No crash

**Status**: [ ] Pass [ ] Fail

---

### Test 13.3: Empty Directory HRISA Generation ✓
**Feature**: Error Handling
**Command**:
```bash
mkdir -p /tmp/test-empty
cd /tmp/test-empty
hrisa init --model qwen2.5-coder:32b --force
```
**Expected**:
- Generates HRISA.md (may be minimal)
- No crash
- Completes successfully

**Cleanup**: `rm -rf /tmp/test-empty`

**Status**: [ ] Pass [ ] Fail

---

### Test 13.4: Very Large Repository ✓
**Feature**: Error Handling
**Command**: Run on Hrisa-Code itself (medium-large project)
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
hrisa init --comprehensive --model qwen2.5-coder:32b --force
```
**Expected**:
- Completes all 5 steps
- May take longer
- No timeout errors
- No memory errors
- Creates HRISA.md

**Status**: [ ] Pass [ ] Fail

---

### Test 13.5: Special Characters in File Names ✓
**Feature**: Error Handling
**Setup**:
```bash
mkdir -p /tmp/test-special-chars
cd /tmp/test-special-chars
touch "file with spaces.txt"
touch "file-with-dashes.txt"
touch "file_with_underscores.txt"
```
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "List all files in the current directory"
```
**Expected**:
- Handles special characters correctly
- Lists all files
- No errors

**Cleanup**: `rm -rf /tmp/test-special-chars`

**Status**: [ ] Pass [ ] Fail

---

## CATEGORY 14: Output Verification & Quality

### Test 14.1: Tool Selection Appropriateness ✓
**Feature**: Output Quality - Tool Selection
**Command**: Ask for different types of tasks
```bash
hrisa chat --model qwen2.5-coder:32b

# Test 1: File reading
> "What's in the file src/hrisa_code/cli.py?"

# Test 2: Search task
> "Find all Python files that import OllamaClient"

# Test 3: Command execution
> "How many lines of code are in the src directory?"
```
**Expected Verification**:
- Test 1: Uses `read_file` tool (NOT execute_command)
- Test 2: Uses `search_files` or `grep` (NOT reading every file)
- Test 3: Uses `execute_command` with `wc -l` or similar (efficient)
- Tool choices are appropriate for the task
- No over-use of tools (e.g., not reading files unnecessarily)

**Scoring**:
- ✓ All tool choices optimal
- ⚠ Some suboptimal but functional
- ✗ Poor tool selection

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.2: Response Accuracy (File Content) ✓
**Feature**: Output Quality - Accuracy
**Setup**:
```bash
mkdir -p /tmp/test-accuracy
cd /tmp/test-accuracy
cat > numbers.txt << 'EOF'
1
2
3
4
5
EOF
```
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
> "Read numbers.txt and tell me the sum of all numbers"
```
**Expected Verification**:
- Reads file correctly
- Calculates: 1+2+3+4+5 = 15
- States answer: "15" or "The sum is 15"
- Correct reasoning shown

**Scoring**:
- ✓ Correct answer with correct reasoning
- ⚠ Correct answer but unclear reasoning
- ✗ Incorrect answer

**Cleanup**: `rm -rf /tmp/test-accuracy`

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.3: Reasoning Quality (Multi-Step Task) ✓
**Feature**: Output Quality - Reasoning
**Command**:
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
hrisa chat --model qwen2.5-coder:32b
> "How many CLI commands does Hrisa Code have? List them."
```
**Expected Verification**:
1. **Planning**: Model should plan to read cli.py
2. **Execution**: Uses read_file on src/hrisa_code/cli.py
3. **Analysis**: Identifies @app.command() decorators
4. **Result**: Lists 3 commands: chat, models, init
5. **Reasoning**: Explains how it found them

**Quality Checklist**:
- [ ] Shows clear reasoning steps
- [ ] Uses appropriate tools
- [ ] Finds correct answer (3 commands)
- [ ] Lists correct command names
- [ ] Explains methodology

**Scoring**:
- ✓ All checklist items met
- ⚠ 3-4 items met
- ✗ < 3 items met

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.4: Planning Quality (Comprehensive HRISA) ✓
**Feature**: Output Quality - Planning
**Command**:
```bash
mkdir -p /tmp/test-planning
cd /tmp/test-planning
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""Simple calculator"""

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

if __name__ == "__main__":
    print(add(5, 3))
EOF

hrisa init --comprehensive --model qwen2.5-coder:32b --force
```
**Expected Verification** - Check HRISA.md contains:

1. **Architecture Section**:
   - [ ] Identifies Python project
   - [ ] Notes main.py as entry point
   - [ ] Describes project structure

2. **Components Section**:
   - [ ] Identifies functions: add, subtract
   - [ ] Describes their purposes
   - [ ] Notes parameters and return types

3. **Features Section**:
   - [ ] Mentions calculator functionality
   - [ ] Lists operations (addition, subtraction)
   - [ ] Describes CLI usage (if applicable)

4. **Workflow Section**:
   - [ ] Explains execution flow
   - [ ] Notes if __name__ == "__main__" pattern
   - [ ] Describes example execution

5. **Quality Indicators**:
   - [ ] No hallucinated features
   - [ ] Accurate code references
   - [ ] Appropriate detail level
   - [ ] Clear organization

**Scoring**:
- ✓ 12+ items present
- ⚠ 8-11 items present
- ✗ < 8 items present

**Cleanup**: `rm -rf /tmp/test-planning`

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.5: Execution Correctness (Tool Results) ✓
**Feature**: Output Quality - Execution
**Setup**:
```bash
mkdir -p /tmp/test-execution
cd /tmp/test-execution
cat > data.json << 'EOF'
{
  "name": "test",
  "version": "1.0.0",
  "dependencies": ["pkg1", "pkg2", "pkg3"]
}
EOF
```
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
> "Read data.json and tell me how many dependencies it has"
```
**Expected Verification**:
1. **Reads file**: Uses read_file on data.json
2. **Parses correctly**: Understands JSON structure
3. **Counts accurately**: Identifies 3 dependencies
4. **States clearly**: "3 dependencies" or similar
5. **Can list them**: If asked, lists pkg1, pkg2, pkg3

**Quality Checklist**:
- [ ] Reads correct file
- [ ] Understands JSON format
- [ ] Counts correctly (3)
- [ ] Clear answer
- [ ] No fabricated information

**Scoring**:
- ✓ All items correct
- ⚠ Minor interpretation issues but correct count
- ✗ Wrong count or major errors

**Cleanup**: `rm -rf /tmp/test-execution`

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.6: Response Completeness (Multi-Part Question) ✓
**Feature**: Output Quality - Completeness
**Command**:
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
hrisa chat --model qwen2.5-coder:32b
> "Tell me about the ModelCatalog class: where it's defined, what it does, and what methods it has"
```
**Expected Verification** - Response should include:

1. **Location**:
   - [ ] File: src/hrisa_code/core/model_catalog.py
   - [ ] Shows it found this via read/search

2. **Purpose**:
   - [ ] Explains it's for managing model profiles
   - [ ] Mentions model capabilities and metadata
   - [ ] Describes use in multi-model orchestration

3. **Methods** (key ones):
   - [ ] add_profile()
   - [ ] get_profile()
   - [ ] get_models_by_capability()
   - [ ] get_best_model_for_capability()
   - [ ] list_all_models()

4. **Quality**:
   - [ ] Answers all three parts of question
   - [ ] Provides accurate information
   - [ ] Well-organized response
   - [ ] No hallucinated details

**Scoring**:
- ✓ All three parts answered correctly (8+ checkboxes)
- ⚠ 2 parts answered well (5-7 checkboxes)
- ✗ Incomplete or inaccurate (< 5 checkboxes)

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.7: Code Understanding (Pattern Recognition) ✓
**Feature**: Output Quality - Code Understanding
**Setup**:
```bash
mkdir -p /tmp/test-patterns
cd /tmp/test-patterns
cat > example.py << 'EOF'
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def do_something(self):
        print("Doing something")
EOF
```
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
> "Read example.py and tell me what design pattern it implements"
```
**Expected Verification**:
- **Identifies pattern**: Singleton pattern
- **Explains how**: Uses __new__ method, _instance class variable
- **Describes purpose**: Ensures only one instance exists
- **Shows understanding**: Can explain why this pattern is used

**Quality Checklist**:
- [ ] Correctly identifies Singleton
- [ ] Explains implementation mechanism
- [ ] Describes use case
- [ ] Shows code-level understanding

**Scoring**:
- ✓ Correctly identifies pattern with good explanation
- ⚠ Identifies pattern but weak explanation
- ✗ Wrong pattern or no understanding

**Cleanup**: `rm -rf /tmp/test-patterns`

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.8: Multi-Step Orchestration Quality ✓
**Feature**: Output Quality - Orchestration
**Command**: Run comprehensive HRISA on Hrisa-Code itself
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code
hrisa init --comprehensive --model qwen2.5-coder:32b --force
```
**Expected Verification** - Review HRISA.md for:

1. **Step 1 Quality (Architecture)**:
   - [ ] Identified all core modules (config, ollama_client, conversation, etc.)
   - [ ] Noted directory structure (src/hrisa_code/core, src/hrisa_code/tools)
   - [ ] Found key config files (pyproject.toml, Makefile)
   - [ ] Described overall organization

2. **Step 2 Quality (Components)**:
   - [ ] Analyzed OllamaClient class
   - [ ] Analyzed ConversationManager class
   - [ ] Analyzed HrisaOrchestrator class
   - [ ] Described their interactions

3. **Step 3 Quality (Features)**:
   - [ ] Found CLI commands (chat, models, init)
   - [ ] Identified tools (read_file, write_file, execute_command, search_files)
   - [ ] Noted special features (agent mode, multi-model, text-based parsing)

4. **Step 4 Quality (Workflows)**:
   - [ ] Traced CLI → Interactive → Conversation flow
   - [ ] Explained tool calling mechanism
   - [ ] Described multi-turn workflow

5. **Step 5 Quality (Synthesis)**:
   - [ ] Comprehensive documentation
   - [ ] Well-structured with clear sections
   - [ ] Accurate information (no hallucinations)
   - [ ] Appropriate detail level
   - [ ] No major omissions

**Scoring**:
- ✓ Excellent (15+ checkboxes)
- ⚠ Good (10-14 checkboxes)
- ✗ Poor (< 10 checkboxes)

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.9: Error Explanation Quality ✓
**Feature**: Output Quality - Error Handling
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
> "Read the file /path/that/does/not/exist.txt"
```
**Expected Verification** - Response should:
- [ ] Acknowledge error occurred
- [ ] Explain what went wrong (file not found)
- [ ] Be helpful (not just "error")
- [ ] Suggest alternatives if appropriate
- [ ] Remain coherent and professional

**Quality Checklist**:
- [ ] Clear error acknowledgment
- [ ] Specific explanation
- [ ] Helpful tone
- [ ] Suggests next steps
- [ ] No confusion or hallucination

**Scoring**:
- ✓ Handles error gracefully with good explanation
- ⚠ Acknowledges error but explanation unclear
- ✗ Confusing or unhelpful response

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

### Test 14.10: Context Retention Quality ✓
**Feature**: Output Quality - Memory
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b

# Message 1
> "I'm working on a calculator project in Python"

# Message 2
> "What programming language am I using?"

# Message 3
> "What kind of project did I mention?"
```
**Expected Verification**:
- Message 2 response: [ ] Correctly states "Python"
- Message 3 response: [ ] Correctly states "calculator project"
- [ ] Doesn't ask for information already provided
- [ ] References earlier context naturally
- [ ] Shows conversation continuity

**Quality Checklist**:
- [ ] Remembers programming language
- [ ] Remembers project type
- [ ] Natural conversation flow
- [ ] No repetitive questions
- [ ] Coherent across messages

**Scoring**:
- ✓ Perfect recall (all 5 items)
- ⚠ Some recall issues (3-4 items)
- ✗ Poor memory (< 3 items)

**Status**: [ ] Pass [ ] Partial [ ] Fail

---

## CATEGORY 15: Performance & Resource Usage

### Test 15.1: Memory Usage (Normal Operation) ✓
**Feature**: Performance
**Command**: Monitor memory during chat session
```bash
# In one terminal:
hrisa chat --model qwen2.5-coder:32b

# In another terminal:
ps aux | grep hrisa
# or: top -p $(pgrep -f hrisa)
```
**Expected**:
- Reasonable memory usage (< 500MB for Python process)
- No memory leaks during conversation
- Memory stable over time

**Status**: [ ] Pass [ ] Fail

---

### Test 15.2: Response Time (Simple Query) ✓
**Feature**: Performance
**Command**: Time a simple query
```bash
time hrisa models
```
**Expected**:
- Completes in < 5 seconds
- No unnecessary delays

**Status**: [ ] Pass [ ] Fail

---

### Test 15.3: Large File Handling ✓
**Feature**: Performance
**Setup**: Create large file
```bash
mkdir -p /tmp/test-large-file
cd /tmp/test-large-file
python3 -c "print('x' * 100000)" > large.txt  # 100KB file
```
**Command**:
```bash
hrisa chat --model qwen2.5-coder:32b
# In chat: "Read large.txt"
```
**Expected**:
- Handles large file (may truncate if configured)
- Shows appropriate message if truncated
- No crash or hang

**Cleanup**: `rm -rf /tmp/test-large-file`

**Status**: [ ] Pass [ ] Fail

---

## Test Summary Template

```
=== TEST RUN SUMMARY ===
Date: YYYY-MM-DD
Tester: [Name]
Version: 0.1.0

Category 1:  Basic CLI              [  /3  ] tests passed
Category 2:  Configuration          [  /4  ] tests passed
Category 3:  Ollama Integration     [  /3  ] tests passed
Category 4:  File Operations        [  /5  ] tests passed
Category 5:  Interactive Chat       [  /5  ] tests passed
Category 6:  Multi-Turn Tools       [  /3  ] tests passed
Category 7:  Text-Based Parsing     [  /3  ] tests passed
Category 8:  Simple HRISA           [  /3  ] tests passed
Category 9:  Comprehensive HRISA    [  /3  ] tests passed
Category 10: Agent Mode             [  /3  ] tests passed
Category 11: Background Tasks       [  /4  ] tests passed
Category 12: Multi-Model            [  /5  ] tests passed
Category 13: Error Handling         [  /5  ] tests passed
Category 14: Output Verification    [  /10 ] tests passed (with quality scoring)
Category 15: Performance            [  /3  ] tests passed

TOTAL: [  /61  ] tests passed
PASS RATE: ___%

OUTPUT QUALITY SCORE: [  /10 ] ✓ Pass | [  /10 ] ⚠ Partial | [  /10 ] ✗ Fail
OVERALL QUALITY: Excellent / Good / Needs Improvement

CRITICAL FAILURES: [List any]
NOTES: [Any observations]

## Quality Assessment Notes
- Tool Selection: [observations]
- Reasoning Quality: [observations]
- Accuracy: [observations]
- Completeness: [observations]
- Code Understanding: [observations]
```

---

## Automated Test Runner (Future)

To make regression testing faster, create an automated test script:

```bash
#!/bin/bash
# tests/run_all_tests.sh

# Run all automated tests
./tests/smoke_test.sh

# Run specific test categories
# TODO: Automate more tests

echo "Manual tests remain in COMPREHENSIVE_REGRESSION_TESTS.md"
```

---

## Contributing New Tests

When adding a new feature:

1. **Add to Feature Matrix** at the top
2. **Create new category** if needed
3. **Write 2-5 tests** covering:
   - Happy path
   - Error cases
   - Edge cases
4. **Update test summary template**
5. **Document expected behavior**
6. **Include setup/cleanup steps**

---

## Notes

- ⏳ = Pending (requires resources not yet available)
- ✓ = Core test (must pass)
- Tests should be runnable independently
- Each test should clean up after itself
- Tests should not depend on each other
- Update this document with each feature addition!
