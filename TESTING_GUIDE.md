# Quick Testing Guide

## What We Fixed

1. **Hanging Issue**: Plan mode was trying to generate plans for simple tasks like "List files", which is slow with large models. Now SIMPLE tasks skip planning and execute directly.

2. **SHIFT+TAB**: Added keyboard binding so SHIFT+TAB cycles modes (just like /agent command).

## Quick Test (2 minutes)

```bash
hrisa chat
```

**Test 1: Mode Cycling**
```
/agent
```
Should show: "► Agent Mode" (cyan panel)

```
/agent
```
Should show: "► Plan Mode" (magenta panel)

Try pressing **SHIFT+TAB** - should also cycle modes with inline feedback: "► Switched to Agent Mode"

**Test 2: Simple Task in Plan Mode**
```
/agent
/agent
```
(Now in plan mode)

```
List all Python files in the src directory
```

Expected behavior:
- Shows: "Analyzing task complexity..."
- Shows: "Task is SIMPLE - using direct execution instead of planning"
- Executes immediately without generating a plan
- No more hanging!

**Test 3: Moderate Task in Plan Mode**
```
/agent
/agent
```
(Now in plan mode)

```
Find all TODO comments in the codebase and summarize them
```

Expected behavior:
- Shows animated spinner: "⠋ Analyzing task complexity..."
- Shows animated spinner: "⠙ Task complexity: MODERATE - generating execution plan..."
- Generates and displays a plan table
- Shows animated spinner for each step: "⠹ Executing step 1..."
- Executes steps with progress tracking

## What to Try

### Safe Tests (Won't Modify Files)
- "List all Python files in src/"
- "Count functions in src/hrisa_code/core/config.py"
- "Show me the git status"
- "Find all TODO comments"

### Moderate Tests (Read-Only Analysis)
- "Analyze the architecture of the ConversationManager class"
- "Find all functions that use the ollama_client"
- "Summarize what tools are available in file_operations.py"

## Expected Behavior

### SIMPLE Tasks
```
> List files
Analyzing task complexity...
Task is SIMPLE - using direct execution instead of planning

[executes immediately with agent mode]
```

### MODERATE/COMPLEX Tasks
```
> Add error logging to all functions
⠋ Analyzing task complexity...
⠙ Task complexity: MODERATE - generating execution plan...

    📋 Execution Plan: Add error logging
┏━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ # ┃ Step        ┃ Type      ┃ Dependencies ┃
┡━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 1 │ Explore...  │ exploration│ none        │
│ 2 │ Design...   │ design     │ 1           │
│ 3 │ Implement...│ implementation│ 2         │
└───┴─────────────┴───────────┴──────────────┘

► Step 1/3 (0% complete)
...
```

## Keyboard Shortcuts

- **SHIFT+TAB**: Cycle modes (normal → agent → plan → normal)
- **Ctrl+D**: Exit
- **Ctrl+C**: Interrupt (if something hangs)

## If Something Goes Wrong

**Hung on a task:**
- Press Ctrl+C to interrupt
- Type `/agent` to cycle back to normal mode
- Try a simpler task first

**SHIFT+TAB doesn't work:**
- Just use `/agent` command instead (works identically)
- SHIFT+TAB binding is terminal-dependent

**Mode not changing:**
- Type `/help` to see current mode
- Use `/agent` to cycle explicitly

## Success Criteria

✅ Mode cycling works (/agent command)
✅ SHIFT+TAB cycles modes (may be terminal-dependent)
✅ SIMPLE tasks execute immediately without hanging
✅ MODERATE tasks generate plans
✅ Visual feedback shows what's happening
✅ Tasks complete successfully

Enjoy testing!
