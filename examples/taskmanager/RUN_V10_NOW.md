# V10 Test - Execute Now (Interactive Required)

**Date:** 2026-01-27
**Status:** ✅ Ready - All Prerequisites Verified
**Duration:** 3-4 hours (requires your presence)

---

## ✅ Pre-Flight Complete

### Environment Status
- ✅ V9 artifacts cleaned
- ✅ Python 3.11.9 ready
- ✅ Ollama running (15 models available)
- ✅ Required models: qwen2.5-coder:32b, qwen2.5:72b
- ✅ CLAUDE.md updated with critical requirements
- ✅ Git ready
- ✅ PDF libraries available

### Files Ready
- ✅ `CLEAN_V10.sh` - Executed successfully
- ✅ `RUN_TEST.sh` - Ready to execute
- ✅ `TASK_TO_PASTE.txt` - Task ready to paste
- ✅ `V10_PREP.md` - Monitoring guide available

---

## 🚀 Execute V10 Test Now

### Step 1: Open Terminal
You need to run the test in your terminal (not through me).

### Step 2: Navigate to Test Directory
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
```

### Step 3: Start the Test
```bash
./RUN_TEST.sh
```

**You'll see:**
```
================================================
  Q3 2025 Real Project Test V2 - Setup
================================================

Step 1: Cleaning previous test artifacts...
✓ Cleaned

Step 2: Verifying Hrisa config...
...

================================================
  READY TO START TEST!
================================================

Next steps:

1. In a SECOND TERMINAL, start model download:
   ollama pull deepseek-r1:14b

2. In THIS TERMINAL, press ENTER to start Hrisa...
```

### Step 4: Press ENTER
When prompted, press ENTER to start hrisa chat.

### Step 5: Wait for Hrisa to Start
You'll see the Hrisa banner and configuration info:
```
  ██╗  ██╗██████╗ ██╗███████╗ █████╗
  ...
  Local AI Coding Assistant

Configuration
  Model: qwen2.5:72b
  Directory: taskmanager/
  ...
```

### Step 6: Check Mode
Look at the prompt. You should see either:
- `[plan] >` - Plan mode (correct)
- `>` - Normal mode (press SHIFT+TAB twice to enter plan mode)

**If in normal mode, press SHIFT+TAB twice to enter plan mode.**

### Step 7: Paste the Task
Copy and paste this EXACT text:

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

### Step 8: Press ENTER
After pasting, press ENTER to submit the task.

---

## 🔍 Critical Monitoring Points

### Watch for Step 4: Database Layer Implementation

**CRITICAL SUCCESS INDICATOR:**
```
╭──────────────────────── ► Tool Call ────────────────────────╮
│ Tool: write_file                                            │
│ Arguments: {                                                │
│   "file_path": "db.py",         ← ✅ CORRECT!              │
│   "content": "..."                                          │
│ }                                                           │
╰─────────────────────────────────────────────────────────────╯
```

**FAILURE INDICATOR (V9 mistake):**
```
│   "file_path": "taskmanager/models.py",  ← ❌ WRONG!       │
```

**What to Do:**
- ✅ If you see `db.py` → Great! Continue monitoring
- ❌ If you see `taskmanager/models.py` or `database.py` → Note it but let test continue (framework should retry)

### Watch for Step 5: CLI Implementation

**CRITICAL SUCCESS INDICATOR:**
Look for import verification BEFORE writing cli.py:
```
╭──────────────────────── ► Tool Call ────────────────────────╮
│ Tool: find_files                                            │
│ Arguments: {                                                │
│   "pattern": "db.py"                                        │
│ }                                                           │
╰─────────────────────────────────────────────────────────────╯
╭──────────────────────── [OK] Tool Result ───────────────────╮
│ db.py                                     ← ✅ Verified!    │
╰─────────────────────────────────────────────────────────────╯
```

Then check imports in cli.py:
```python
from db import Task, get_session        ← ✅ CORRECT!
```

**FAILURE INDICATOR (V9 mistake):**
```python
from taskmanager.db import ...          ← ❌ WRONG (file doesn't exist)
```

### Watch for Syntax Errors

**SUCCESS INDICATOR:**
```
╭──────────────── [OK] Tool Result (File written) ────────────╮
│ Successfully wrote to db.py                                 │
╰─────────────────────────────────────────────────────────────╯
```

**FAILURE INDICATOR (V9 mistake):**
```
╭──────────────── [ERROR] Tool Result ─────────────────────────╮
│ SYNTAX ERROR - File not written:                            │
│ Syntax error at line 3: invalid syntax                      │
│                                                              │
│ Please fix the syntax error and try again.                  │
╰──────────────────────────────────────────────────────────────╯
```

### Watch for Loop Detection

**SUCCESS INDICATOR:**
Model changes strategy after warning:
```
[SYSTEM WARNING] You've called 'read_file' 2 times with identical parameters.
```
Then model does something different (not the same call again).

**FAILURE INDICATOR (V9 mistake):**
```
[SYSTEM WARNING] ...
[SYSTEM WARNING] ...
[SYSTEM INTERVENTION] Loop detected: 'read_file' called 3 times...
[SYSTEM INTERVENTION] You have reached the maximum number of tool rounds (12).
```

---

## ⏱️ What to Expect

### Timeline
- **Step 1 (Review):** ~1-2 minutes
- **Step 2 (Design data model):** ~2-3 minutes
- **Step 3 (Design CLI):** ~3-5 minutes
- **Step 4 (Implement database):** ~5-15 minutes (CRITICAL STEP)
- **Step 5 (Implement add command):** ~5-10 minutes (CRITICAL STEP)
- **Steps 6-11 (Other commands):** ~30-60 minutes total
- **Step 12-13 (Tests):** ~20-30 minutes
- **Step 14 (Documentation):** ~5-10 minutes

**Total:** ~2-4 hours

### Approval Prompts
When you see file write operations, you'll be prompted:
```
╭────────────────── File Write Operation ──────────────────────╮
│                                                              │
│  Create new file: db.py                                      │
│  ...                                                         │
╰──────────────────────────────────────────────────────────────╯

Options:
  y - Yes: Approve this operation
  n - No: Deny this operation
  a - Always: Approve this type (for this session)
  v - Never: Never approve this type (for this session)

? Select your choice:
```

**Recommended:** Press `a` (Always) for the first write operation to avoid constant prompts.

---

## 📊 V10 Success Criteria

Track these as test progresses:

| Check | Target | How to Verify |
|-------|--------|---------------|
| db.py created | ✅ Yes | Look for `write_file` with `"file_path": "db.py"` |
| cli.py created | ✅ Yes | Look for `write_file` with `"file_path": "cli.py"` |
| Correct imports | ✅ Yes | cli.py imports `from db import ...` |
| Zero syntax errors | ✅ Yes | No `SYNTAX ERROR - File not written` messages |
| Loop detections | ≤2 | Count `[SYSTEM INTERVENTION] Loop detected` messages |
| Steps completed | ≥11/14 | Watch the `► Step X/14 (Y% complete)` progress |
| Commands implemented | ≥4/6 | Count `def add`, `def list`, etc. in cli.py |

---

## 🎯 After Test Completes

### Immediate Validation

When test finishes (or stops), run these commands:

#### 1. Check Files Created
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager

echo "=== Files Created ==="
ls -la *.py 2>/dev/null || echo "No Python files at root"
ls -la taskmanager/*.py 2>/dev/null || echo "No files in taskmanager/"
```

#### 2. Verify db.py
```bash
if [ -f "db.py" ]; then
    echo "✅ db.py exists"
    python3 -m py_compile db.py && echo "✅ Valid syntax" || echo "❌ Syntax error"
else
    echo "❌ db.py NOT FOUND"
fi
```

#### 3. Verify cli.py
```bash
if [ -f "cli.py" ]; then
    echo "✅ cli.py exists"
    python3 -m py_compile cli.py && echo "✅ Valid syntax" || echo "❌ Syntax error"
    echo ""
    echo "Commands implemented:"
    grep -E "^def (add|list|show|edit|delete|search|export|complete)" cli.py
else
    echo "❌ cli.py NOT FOUND"
fi
```

#### 4. Test Imports
```bash
if [ -f "db.py" ] && [ -f "cli.py" ]; then
    python3 << 'EOF'
try:
    from db import Task, get_session
    print("✅ Imports work correctly")
except ImportError as e:
    print(f"❌ Import error: {e}")
EOF
fi
```

---

## 📝 Taking Notes During Test

Keep track of these observations:

**File Creation (Step 4):**
- [ ] File created: ______________ (expected: db.py)
- [ ] Location: ______________ (expected: root)
- [ ] Contains models: Yes / No
- [ ] Contains session: Yes / No

**Import Validation (Step 5):**
- [ ] Model verified db.py exists before importing: Yes / No
- [ ] Imports correct: `from db import ...` Yes / No
- [ ] Import errors: Yes / No

**Syntax Errors:**
- [ ] Total syntax errors: ______
- [ ] If any, on line: ______

**Loop Detections:**
- [ ] Total loop warnings: ______
- [ ] Hit 12-round limit: Yes / No / How many times: ______

**Final Results:**
- [ ] Steps completed: ____/14
- [ ] Commands working: ____/6
- [ ] Tests created: Yes / No
- [ ] Overall impression: A / B / C / D / F

---

## ⚠️ If Things Go Wrong

### If db.py Not Created (Step 4 fails again)
1. **Don't stop the test** - let it continue
2. Note the failure
3. After test completes, we'll implement **Path B** (simplify pyproject.toml)

### If Loops Start Happening
1. **Don't intervene** - let framework handle it
2. Note which tools are looping
3. System should warn and eventually stop the step

### If Test Stops Early
1. Note how many steps completed
2. Run the validation commands above
3. Report results back to me for analysis

---

## 🎬 Ready to Start!

**You have everything you need:**
- ✅ Clean environment
- ✅ All dependencies verified
- ✅ Critical fixes applied to CLAUDE.md
- ✅ Monitoring guide prepared
- ✅ Validation commands ready

**To execute:**
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
./RUN_TEST.sh
```

**Then:**
1. Press ENTER when prompted
2. Enter plan mode if needed (SHIFT+TAB twice)
3. Paste the task
4. Monitor according to guide above
5. Run validation after completion

**Good luck with V10! 🚀**

---

## 📞 After Test

When test completes, come back and let me know:
1. How many steps completed (X/14)
2. Was db.py created at root? (Yes/No)
3. Were there syntax errors? (Yes/No/How many)
4. Did loops occur? (Yes/No/How many)
5. Overall grade you'd give (A/B/C/D/F)

I'll analyze the results and prepare next steps (V11 if needed, or declare success!).
