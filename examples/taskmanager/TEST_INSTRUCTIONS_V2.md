# Q3 2025 Real Project Test - UPDATED INSTRUCTIONS

**Version:** 2.0 (Post-UX Fixes)
**Date:** 2026-01-01
**Changes:** Added Plan Mode confirmation, improved mode clarity

---

## CRITICAL: What Went Wrong in V1

In the first test, you accidentally ended up in **Agent Mode** instead of **Plan Mode** because:
1. You pressed SHIFT+TAB 4 times (cycled: normal → agent → plan → normal → agent)
2. Mode indicator wasn't clear enough
3. No confirmation prevented accidental activation

**Result:** 2 hours wasted, v0.2.0 improvements not tested.

---

## NEW SAFETY FEATURES ✓

**Plan Mode now requires confirmation:**
- Shows explanation of what Plan Mode does
- Asks "Enter Plan Mode? (y/n)"
- Shows large banner: "YOU ARE NOW IN PLAN MODE"
- Bottom toolbar always shows current mode

**You cannot accidentally activate Plan Mode anymore!**

---

## Prerequisites

1. **Clean the previous test directory:**
```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples
rm -rf taskmanager
mkdir -p taskmanager/src/taskmanager taskmanager/tests taskmanager/docs
cd taskmanager
```

2. **Create fresh project files:**
```bash
# Copy these from parent taskmanager folder
cp ../../../examples/taskmanager/pyproject.toml .
cp ../../../examples/taskmanager/.gitignore .
cp ../../../examples/taskmanager/METRICS.md .
git init
git add .
git commit -m "Initial setup"
```

---

## Step-by-Step Instructions

### STEP 1: Start Hrisa Chat

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
hrisa chat
```

**You will see:**
- ASCII art banner
- Configuration panel showing "Mode: normal"
- Command prompt: `>`

---

### STEP 2: Enter Plan Mode (WITH CONFIRMATION)

**Type exactly:** `/agent`

**Then press ENTER**

**What happens:**
1. Shows "► Agent Mode" panel
2. Explains agent mode capabilities

**Type again:** `/agent`

**Then press ENTER**

**NOW IMPORTANT - You will see:**

```
╭──────────────── Plan Mode Activation ────────────────╮
│                                                       │
│  ⚠ Entering Plan Mode                                │
│                                                       │
│  Plan Mode generates a multi-step execution plan...  │
│                                                       │
│  The system will:                                     │
│    1. Analyze task complexity                         │
│    2. Generate 4-15 step execution plan               │
│    3. Execute each step with visual progress          │
│    4. Use previous step results...                    │
│                                                       │
╰───────────────────────────────────────────────────────╯

Enter Plan Mode? (y/n): _
```

**Type:** `y` **and press ENTER**

**You will then see:**

```
╭──────────── ✓ Plan Mode Active ────────────────╮
│                                                 │
│  YOU ARE NOW IN PLAN MODE                       │
│                                                 │
│  Your next task will be planned and executed... │
│                                                 │
╰─────────────────────────────────────────────────╯
```

**VERIFY:** Look at the bottom of your terminal. You should see:
```
Mode: plan
```

**If you don't see the Plan Mode confirmation prompt, you're still in Agent Mode. Type `/agent` again.**

---

### STEP 3: Start Metrics Tracking

**BEFORE giving the task**, open a new terminal window and prepare to track metrics:

```bash
# In new terminal
cd /Users/peng/Documents/mse/private/Hrisa-Code/examples/taskmanager
# Keep METRICS.md open in editor for real-time updates
```

**Start a timer or note the current time.**

---

### STEP 4: Give the Task

**Copy and paste this EXACT task:**

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

**Press ENTER**

---

### STEP 5: Watch and Record

**What you should see:**

**Phase 1: Complexity Analysis (2-5 seconds)**
```
★ Task Complexity: COMPLEX (14 steps)
```

**Record in METRICS.md:**
- Time when task given: ___
- Complexity detected: SIMPLE/MODERATE/COMPLEX
- Expected steps: ___

**Phase 2: Plan Generation (5-10 seconds)**

You should see a table like:
```
┏━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ #   ┃ Step                        ┃ Type           ┃ Dependencies ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 1   │ Explore...                  │ exploration    │ none         │
│ 2   │ Design data model...        │ design         │ 1            │
│ 3   │ Implement Task class...     │ implementation │ 2            │
│ 4   │ Implement database layer... │ implementation │ 2            │
│ ...and so on...                                                    │
└─────┴─────────────────────────────┴────────────────┴──────────────┘
```

**GOOD SIGNS (means it's working):**
- ✓ 10-15 steps generated
- ✓ Steps are SPECIFIC (mention files, classes, features)
- ✓ Multiple step types (exploration, design, implementation, testing, documentation)
- ✓ Clear dependencies

**BAD SIGNS (means it fell back to heuristic):**
- ✗ Only 4 generic steps
- ✗ Steps are vague ("Implement the solution")
- ✗ All steps are same type

**Record in METRICS.md:**
- Number of steps: ___
- Steps per phase:
  - Exploration: ___
  - Design: ___
  - Implementation: ___
  - Testing: ___
  - Documentation: ___
- Plan quality (1-5): ___

**Phase 3: Step Execution (variable time)**

For EACH step, watch for:

```
► Step 1/10 (0% complete)
   [Step description]
   Type: exploration

★ Task Complexity: SIMPLE (2 steps)
⠇ Executing step 1: [description]
```

**Record for EACH step in METRICS.md:**
- Step number: ___
- Tool calls made: ___
- Validation errors: ___
- Approval prompts: ___
- Time spent: ___ minutes

**IMPORTANT: Approve write operations**
- When asked to approve file writes, choose "Always" (press 'a')
- This speeds up the test
- We'll review code quality at the end

**Watch for:**
- Does Step 2 reference Step 1 results? (context passing)
- Are tool parameters correct on first try? (parameter validation)
- Are steps making progress or repeating work? (redundancy)

---

### STEP 6: When Execution Completes

**You will see:**
```
╭────────────── ► Complete ──────────────╮
│ ✓ Plan Completed Successfully          │
│                                        │
│ All 10 steps executed.                 │
│                                        │
│ Task finished.                         │
╰────────────────────────────────────────╯
```

**Record end time in METRICS.md**

---

### STEP 7: Evaluate Code Quality

**Run quality checks:**

```bash
# Check syntax
python3 -m py_compile src/taskmanager/*.py

# Count lines
find src/taskmanager -name "*.py" -exec wc -l {} + | tail -1

# Check for placeholder code
grep -r "Implementation to be added" src/
grep -r "# TODO" src/

# Check for syntax errors
grep -r "{{" src/taskmanager/

# List all files created
find src/taskmanager -name "*.py" -ls
find tests/ -name "*.py" -ls

# Check if type hints present
grep -c "def.*->" src/taskmanager/*.py
```

**Record in METRICS.md:**
- Total files created: ___
- Total lines of code: ___
- Placeholder lines: ___
- Syntax errors found: ___
- Files with type hints: ___ / ___

---

### STEP 8: Run Tests

**Install dependencies and run tests:**

```bash
# Install in venv
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src/taskmanager --cov-report=term
```

**Record in METRICS.md:**
- Tests written: ___
- Tests passing (first run): ___ / ___ (__%)
- Code coverage: ___%

---

### STEP 9: Manual Feature Check

**Test each feature manually:**

```bash
# Try CLI commands
python -m taskmanager add "Test task" --description "Testing" --priority 1
python -m taskmanager list
python -m taskmanager show 1
python -m taskmanager complete 1
python -m taskmanager delete 1

# Try search (if implemented)
python -m taskmanager search "test"
python -m taskmanager filter --status completed

# Try export (if implemented)
python -m taskmanager export json output.json
python -m taskmanager export csv output.csv
python -m taskmanager export markdown output.md
```

**Record in METRICS.md:**

| Feature | Implemented | Working |
|---------|-------------|---------|
| add command | Y/N | Y/N |
| list command | Y/N | Y/N |
| show command | Y/N | Y/N |
| edit command | Y/N | Y/N |
| complete command | Y/N | Y/N |
| delete command | Y/N | Y/N |
| Search/filter | Y/N | Y/N |
| Export JSON | Y/N | Y/N |
| Export CSV | Y/N | Y/N |
| Export Markdown | Y/N | Y/N |
| Type hints | Y/N | N/A |
| Tests passing | Y/N | N/A |

---

### STEP 10: Calculate Success Rating

**Based on completed features and quality:**

**⭐ Minimum Success:**
- 50%+ code by Hrisa
- 70%+ tests passing
- Project functional

**⭐⭐ Good Success:**
- 70%+ code by Hrisa
- 85%+ tests passing
- Minimal manual intervention

**⭐⭐⭐ Excellent Success:**
- 85%+ code by Hrisa
- 95%+ tests passing
- Production quality

**Record in METRICS.md:**
- Success rating: ⭐ / ⭐⭐ / ⭐⭐⭐
- Justification: ___

---

## Expected Timeline

- **Complexity analysis:** 2-5 seconds
- **Plan generation:** 5-10 seconds
- **Step 1 (Exploration):** 2-5 minutes
- **Step 2 (Design):** 1-3 minutes
- **Steps 3-7 (Implementation):** 5-15 minutes each
- **Step 8-9 (Testing):** 10-20 minutes
- **Step 10 (Documentation):** 5-10 minutes

**Total expected:** 1-2 hours for full implementation

---

## Troubleshooting

### "I pressed /agent but didn't see confirmation prompt"

You're probably in Normal Mode. Type `/agent` once more to reach Agent Mode, then once more for Plan Mode confirmation.

### "I accidentally pressed 'n' on the confirmation"

No problem! You're still in your current mode. Type `/agent` twice more to get back to Plan Mode confirmation.

### "Bottom toolbar doesn't show 'plan'"

You're not in Plan Mode. Start over: type `/agent` until you see the confirmation prompt, then confirm with 'y'.

### "Plan has only 4 generic steps"

This means LLM plan generation failed and it fell back to heuristic. This is OK - it's data we need! But note it in METRICS.md as a failure case.

### "Code has syntax errors"

This is a bug we're tracking. Note all syntax errors in METRICS.md. This helps us improve validation.

### "Tests are failing"

Record which tests fail and why. This is valuable data for improving code generation quality.

---

## Success Criteria Reminder

**We're testing:**
1. ✓ Does Plan Mode generate better plans than Agent Mode?
2. ✓ Does step context passing reduce redundancy?
3. ✓ Do parameter checklists reduce validation errors?
4. ✓ Does code meet quality requirements (type hints, no syntax errors)?
5. ✓ Can Hrisa build a working multi-feature project?

**Good result:** 70%+ of features working, 85%+ tests passing, minimal manual fixes

**Great result:** 85%+ of features working, 95%+ tests passing, production quality

---

## After Test Completion

1. **Fill out METRICS.md completely**
2. **Save full transcript** (if possible)
3. **Run evaluation:**
   ```bash
   # Count successes and failures
   grep "✓" METRICS.md | wc -l
   grep "✗" METRICS.md | wc -l
   ```

4. **Document lessons learned** in METRICS.md

5. **Share results** - we'll analyze and plan Q4 2025 improvements!

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────┐
│  ENTERING PLAN MODE (DO THIS FIRST)             │
├──────────────────────────────────────────────────┤
│  1. hrisa chat                                   │
│  2. Type: /agent    (press ENTER)                │
│  3. Type: /agent    (press ENTER)                │
│  4. See confirmation prompt                      │
│  5. Type: y         (press ENTER)                │
│  6. See "YOU ARE NOW IN PLAN MODE"               │
│  7. Verify bottom shows: Mode: plan              │
│  8. Paste task and press ENTER                   │
└──────────────────────────────────────────────────┘
```

---

**Ready to test? Follow these instructions exactly!**

**Good luck! 🚀**
