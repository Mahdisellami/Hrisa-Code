# Q3 2025 Real Project Test V3 - Instructions

**Date:** 2026-01-01
**Version:** V3 (Third Attempt with All Fixes)
**Objective:** Validate v0.2.0 Plan Mode improvements + critical fixes from V1/V2

---

## What's Different in V3?

### ✅ Fixed from V1
- Plan Mode confirmation modal (no more mode confusion)
- Async prompt compatibility
- Better file structure

### ✅ NEW Fixes in V3
1. **Config Loading Fixed** - deepseek-r1:70b will actually load now
2. **CLI/CRUD Heuristic Added** - Specific 10-15 step plan for CLI tools
3. **Enhanced Step Prompts** - Explicit "NO PLACEHOLDERS" instructions
4. **Code Quality Validation** - Syntax/import/type hint checks on write

---

## Pre-Test Verification

### 1. Verify Model Configuration
```bash
cat ~/.config/hrisa-code/config.yaml
```

**Expected output:**
```yaml
model:
  name: "deepseek-r1:70b"
  temperature: 0.7

ollama:
  host: "http://localhost:11434"

tools:
  enabled: true
```

**✓ If correct:** Proceed
**✗ If wrong/missing:** Run:
```bash
mkdir -p ~/.config/hrisa-code
cat > ~/.config/hrisa-code/config.yaml << 'EOF'
model:
  name: "deepseek-r1:70b"
  temperature: 0.7

ollama:
  host: "http://localhost:11434"

tools:
  enabled: true
EOF
```

### 2. Verify Ollama Running
```bash
ollama list | grep deepseek-r1
```

**Expected:** Should show `deepseek-r1:70b`
**✗ If missing:** Run `ollama pull deepseek-r1:70b`

### 3. Clean Test Directory
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
rm -f *.py tasks.db
rm -rf tests/*.py
rm -rf .hrisa/conversation_*.json
```

**✓ Verify clean:**
```bash
ls -la
```
Should show only:
- Documentation files (*.md, *.txt, *.sh)
- Config files (.gitignore, pyproject.toml)
- Empty directories (docs/, src/, tests/)

---

## Test Execution

### Step 1: Start Hrisa
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
hrisa chat
```

**Expected banner:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Hrisa - Local AI Coding Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│  Configuration                                    │
│    Model: deepseek-r1:70b                         │  ← VERIFY THIS!
│    ...                                            │
```

**⚠️ CRITICAL CHECK:** Model MUST be `deepseek-r1:70b`
**✗ If wrong:** Exit (`/exit`) and fix config

### Step 2: Enter Plan Mode (With Confirmation)
Type:
```
/agent
```

**First time:** Switches to Agent Mode
**Expected:**
```
► Switched to Agent Mode
```

Type again:
```
/agent
```

**Second time:** Shows Plan Mode confirmation modal
**Expected:**
```
╭─ Plan Mode Activation ─────────────────────────╮
│ ⚠ Entering Plan Mode                           │
│                                                 │
│ Plan Mode generates a multi-step execution     │
│ plan before executing...                       │
│                                                 │
│ The system will:                               │
│   1. Analyze task complexity                   │
│   2. Generate 4-15 step execution plan         │
│   3. Execute each step with visual progress    │
│   4. Use previous step results to avoid        │
│      redundancy                                │
╰─────────────────────────────────────────────────╯

Enter Plan Mode? (y/n): _
```

Type:
```
y
```

**Expected large confirmation banner:**
```
╭─ ✓ Plan Mode Active ───────────────────────────╮
│ YOU ARE NOW IN PLAN MODE                       │
│                                                 │
│ Your next task will be planned and executed    │
│ step-by-step.                                  │
│ Watch the bottom toolbar for persistent mode   │
│ indicator.                                     │
╰─────────────────────────────────────────────────╯
```

**✓ Verify bottom toolbar shows:** `[plan]`

### Step 3: Paste Task (Critical - Do NOT modify)
```
Implement a CLI task manager with the following features:
- Task CRUD operations (add, list, show, edit, complete, delete)
- SQLite persistence with data model (id, title, description, priority, status, tags, created_at, updated_at, due_date, completed_at)
- Search and filtering capabilities (by status, priority, tags, text search)
- Export to JSON, CSV, and Markdown formats
- Full test coverage with pytest (unit tests + integration tests)
- Type hints on ALL functions and methods
- Comprehensive docstrings
Use Typer for CLI and follow Python best practices.
```

Press ENTER and let it run.

---

## What to Watch For

### Phase 1: Plan Generation (First 30 seconds)

**✅ GOOD SIGNS:**
```
Analyzing task complexity...
Complexity: COMPLEX

Generating execution plan...
[Shows 10-15 steps in a table]
```

**Key indicators of success:**
- Plan has 10-15 steps (NOT just 4)
- Each implementation step mentions specific feature (add, list, edit, etc.)
- No "WARNING: LLM generated poor quality plan" message
- Steps include: exploration → design (2 steps) → implementation (6-7 steps) → testing (2 steps) → docs

**❌ BAD SIGNS:**
```
WARNING:root:LLM generated poor quality plan (1 steps for COMPLEX task), falling back to heuristic
```
→ This means CLI/CRUD heuristic didn't trigger or LLM still failing

### Phase 2: Exploration (Step 1)

**Expected:**
- Searches for existing files
- Reads requirements
- Reports: "No existing implementation, starting fresh"

**Time:** ~1-2 minutes

### Phase 3: Design (Steps 2-3)

**Expected:**
- Step 2: Designs data model (should mention ALL fields from requirements)
- Step 3: Designs CLI structure (should list all commands)

**Time:** ~2-3 minutes

**⚠️ WATCH:** These steps should produce detailed designs, not just "thinking"

### Phase 4: Implementation (Steps 4-11)

**CRITICAL - Watch for these:**

**✅ GOOD SIGNS:**
- Each step writes WORKING code (not `pass`)
- `write_file` tool shows CODE QUALITY WARNINGS if type hints missing
- Functions have actual logic (database operations, not stubs)
- Multiple files created: models.py, cli.py, main.py

**❌ BAD SIGNS:**
```python
def add(title: str):
    # Add a task
    pass  # ← RED FLAG!
```
→ If you see this, the enhanced prompts didn't work

**✅ WHAT YOU SHOULD SEE:**
```python
def add(title: str, description: str = "", priority: int = 1) -> None:
    """Add a new task."""
    session = Session()
    task = Task(title=title, description=description, priority=priority)
    session.add(task)
    session.commit()
    print(f"Task '{title}' added successfully!")
```

**Time per step:** ~3-5 minutes
**Total implementation time:** ~30-40 minutes

### Phase 5: Testing (Steps 12-13)

**Expected:**
- Writes unit tests
- Writes integration tests
- Runs `pytest` to verify

**Time:** ~5-10 minutes

### Phase 6: Documentation (Step 14)

**Expected:**
- Adds docstrings
- Adds type hints (if missing)
- Final quality pass

**Time:** ~3-5 minutes

---

## Success Criteria

### Minimum Success (⭐ - 50%)
- [ ] Plan Mode activated successfully
- [ ] deepseek-r1:70b used (check banner)
- [ ] 10+ step plan generated (specific, not generic)
- [ ] All files created without syntax errors
- [ ] At least 50% of functions have working implementations (not `pass`)
- [ ] Data model has correct field types
- [ ] At least 3 out of 6 CRUD operations work

### Good Success (⭐⭐ - 75%)
- [ ] All Minimum criteria
- [ ] 80%+ of functions fully implemented
- [ ] All CRUD operations working
- [ ] Search OR export working
- [ ] 50%+ tests passing
- [ ] Type hints on most functions

### Excellent Success (⭐⭐⭐ - 95%)
- [ ] All Good criteria
- [ ] 95%+ of features working
- [ ] Both search AND export working
- [ ] 80%+ tests passing
- [ ] Type hints on ALL functions
- [ ] Comprehensive docstrings
- [ ] No placeholder code anywhere

---

## Post-Test Evaluation

### 1. Verify Model Was Used
```bash
grep "Model:" ~/.hrisa/conversation_*.json | tail -1
```
Should show: `deepseek-r1:70b`

### 2. Check Generated Files
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
ls -la *.py
wc -l *.py tests/*.py
```

**Expected:**
- `main.py` (entry point)
- `cli.py` (Typer commands)
- `models.py` (SQLAlchemy model)
- `tests/test_*.py` (test files)
- **Total:** 300-500 lines of code

### 3. Check for Placeholder Code
```bash
grep -n "pass$" *.py cli.py
```

**Expected:** 0 results (no placeholder implementations)
**✗ If found:** Count how many `pass` statements exist

### 4. Run Syntax Check
```bash
python3 -m py_compile *.py
```

**Expected:** No output (all files compile)
**✗ If errors:** Note which files have syntax errors

### 5. Run Tests
```bash
pytest -v
```

**Expected:** At least 50% passing (for ⭐), 80% for ⭐⭐⭐

### 6. Test Basic Functionality
```bash
# Test add command
python main.py add "Test task" "Test description" --priority 1

# Test list command
python main.py list

# Test show command
python main.py show 1
```

**Expected:** Commands work and show output (not errors)

---

## Comparison Checklist (V3 vs V2)

| Metric | V2 Result | V3 Target | V3 Actual |
|--------|-----------|-----------|-----------|
| **Model Used** | qwen2.5:72b | deepseek-r1:70b | _____ |
| **Plan Steps** | 4 generic | 10-15 specific | _____ |
| **LLM Plan Failure** | Yes (1-step) | No | _____ |
| **Placeholder Code** | 43% (6/6 functions) | 0% | _____% |
| **Working Features** | 0% | 80%+ | _____% |
| **Tests Passing** | 0/6 (0%) | 4/6+ (70%+) | _____% |
| **Type Hints** | Missing | All functions | _____ |
| **Status Field Type** | Boolean (wrong) | String/Enum (correct) | _____ |
| **Total LOC** | 139 | 300-500 | _____ |

---

## Troubleshooting

### Problem: Model still shows qwen2.5:72b
**Fix:**
```bash
# Verify config location
cat ~/.config/hrisa-code/config.yaml

# If file doesn't exist, create it:
mkdir -p ~/.config/hrisa-code
cat > ~/.config/hrisa-code/config.yaml << 'EOF'
model:
  name: "deepseek-r1:70b"
  temperature: 0.7

ollama:
  host: "http://localhost:11434"

tools:
  enabled: true
EOF
```

### Problem: Still getting 4-step generic plan
**Check:** Look for this in logs:
```
WARNING:root:LLM generated poor quality plan
```

**Possible causes:**
1. CLI/CRUD heuristic pattern didn't trigger (check task keywords)
2. deepseek-r1:70b still generating poor plans
3. Code changes not reloaded

**Fix:**
```bash
# Reinstall Hrisa with latest changes
cd /Users/peng/Documents/mse/private/Hrisa-Code
pip install -e .

# Verify dynamic_planner.py has new pattern
grep -n "CLI tool with CRUD" src/hrisa_code/core/planning/dynamic_planner.py
```
Should show line 251.

### Problem: Still getting placeholder code
**Check:** Look for write_file results showing:
```
Successfully wrote to cli.py

CODE QUALITY WARNINGS:
Type hint warnings:
  - Function 'add' missing return type hint
```

**If NO warnings shown:** Code quality validator may not be integrated.

**Fix:**
```bash
# Verify file_operations.py has validator import
grep -n "CodeQualityValidator" src/hrisa_code/core/tools/file_operations.py
```
Should show import at top.

---

## Quick Reference Card

**Model Check:**
```bash
cat ~/.config/hrisa-code/config.yaml | grep name
```
→ Should show: `deepseek-r1:70b`

**Clean Directory:**
```bash
rm -f *.py tasks.db && rm -rf tests/*.py .hrisa/conversation_*.json
```

**Enter Plan Mode:**
1. `/agent` (first time → Agent Mode)
2. `/agent` (second time → shows confirmation)
3. Type `y` (confirms Plan Mode)
4. Check toolbar shows `[plan]`

**Start Test:**
Paste task from TASK_TO_PASTE.txt and press ENTER

**Monitor Progress:**
- Watch for 10-15 step plan (not 4)
- Watch for working code (not `pass`)
- Watch for CODE QUALITY WARNINGS

**After Test:**
```bash
python3 -m py_compile *.py  # Check syntax
grep "pass$" *.py           # Check placeholders
pytest -v                   # Run tests
```

---

## Expected Timeline

| Phase | Duration | What to Watch |
|-------|----------|---------------|
| Plan Generation | 30 sec - 2 min | 10-15 step plan appears |
| Step 1 (Explore) | 1-2 min | Searches files |
| Steps 2-3 (Design) | 2-3 min | Designs model + CLI |
| Steps 4-11 (Implement) | 30-40 min | Writes working code |
| Steps 12-13 (Test) | 5-10 min | Writes and runs tests |
| Step 14 (Docs) | 3-5 min | Adds docstrings |
| **TOTAL** | **45-60 min** | Full implementation |

---

## What Makes V3 Different?

### 1. Config Loading Fixed
- V2: Config at `~/.hrisa/` (wrong location)
- V3: Config at `~/.config/hrisa-code/` (correct)
- **Result:** deepseek-r1:70b actually loads

### 2. CLI/CRUD Heuristic Added
- V2: Generic "implement" → 4 vague steps
- V3: CLI/CRUD pattern → 10-15 specific steps
- **Result:** Clear feature-by-feature breakdown

### 3. Enhanced Step Prompts
- V2: "Implement the solution" (too vague)
- V3: "Implement FULL functionality, NOT placeholders" (explicit)
- **Result:** LLM generates working code

### 4. Code Quality Validation
- V2: No validation, syntax errors slipped through
- V3: Validates syntax, imports, type hints on write
- **Result:** Immediate feedback on code quality

---

## Next Steps After Test

1. **Capture full transcript** (copy from terminal)
2. **Run evaluation checklist** (see Post-Test Evaluation section)
3. **Fill out comparison table** (V3 vs V2 metrics)
4. **Create TEST_EVALUATION_V3.md** with:
   - Executive summary
   - Plan quality analysis
   - Code quality analysis
   - Feature completeness
   - Comparison to V1/V2
   - Lessons learned
   - Recommendations

---

**Good luck with V3!** 🚀

This test will validate if:
- deepseek-r1:70b generates better plans than qwen2.5:72b
- CLI/CRUD heuristic improves plan specificity
- Enhanced prompts prevent placeholder code
- Code quality validator catches issues early

**Expected outcome:** ⭐⭐ (75%+) or ⭐⭐⭐ (95%+) success!

---

**Date:** 2026-01-01
**Prepared by:** Claude Sonnet 4.5
**Ready for execution:** YES ✅
