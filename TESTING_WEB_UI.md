# Testing the Web UI - Quick Start Guide

Follow these steps to test the new web UI functionality.

## Prerequisites Check

Before starting, make sure you have:
- ✅ Python 3.10+ installed
- ✅ Ollama installed and running
- ✅ At least one Ollama model available
- ✅ Hrisa Code repository cloned

## Step 1: Install Web Dependencies

```bash
cd /Users/peng/Documents/mse/private/Hrisa-Code

# Install with web dependencies
pip install -e ".[web]"
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- WebSockets (real-time communication)

## Step 2: Run Validation Script

```bash
# Make sure Ollama is running first
ollama serve  # In a separate terminal

# Run the validation script
python3 test_web_ui.py
```

Expected output:
```
============================================================
Hrisa Code Web UI - Quick Validation
============================================================
Testing imports...
  ✓ WebAgentManager imports successfully
  ✓ FastAPI app imports successfully

Testing static files...
  ✓ index.html exists
  ✓ styles.css exists
  ✓ app.js exists

Testing dependencies...
  ✓ fastapi installed (FastAPI web framework)
  ✓ uvicorn installed (ASGI server)
  ✓ websockets installed (WebSocket support)

Testing Ollama connection...
  ✓ Ollama is running with N model(s)

============================================================
Summary:
============================================================
  Imports: ✓ PASS
  Static Files: ✓ PASS
  Dependencies: ✓ PASS
  Ollama: ✓ PASS
============================================================

✓ All tests passed! Ready to start the web UI.
```

## Step 3: Start the Web UI Server

```bash
# Start the server
hrisa web

# Or with custom port
hrisa web --port 3000

# Or with auto-reload for development
hrisa web --reload
```

You should see:
```
══════════════════════════════════════════════════
  Hrisa Code Web UI

  Starting server on http://0.0.0.0:8000

  Features:
    • Create and manage multiple agents
    • Real-time progress tracking
    • Automatic stuck detection
    • Send instructions to agents
    • View agent outputs and messages

  Press Ctrl+C to stop
══════════════════════════════════════════════════

Opening web UI at: http://0.0.0.0:8000
API documentation: http://0.0.0.0:8000/docs

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Open the Web UI

Open your browser to:
- **Main UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

You should see:
- Dark-themed dashboard
- "Create New Agent" button
- System statistics (all showing 0)
- Connection status showing "Connected" (green dot)

## Step 5: Create Your First Agent

### Test 1: Simple Documentation Task

1. Click "➕ Create New Agent" button
2. Enter this task:
   ```
   List all Python files in the current directory and create a simple report
   ```
3. Leave other fields empty (uses defaults)
4. Click "Create & Start"

**Expected Behavior:**
- Modal closes
- New agent card appears in the main area
- Status shows "running" (blue badge)
- Progress bar starts filling
- You see live updates without page refresh

### Test 2: More Complex Task

1. Create another agent with:
   ```
   Analyze the src/hrisa_code/web/ directory and summarize:
   - Number of Python files
   - Total lines of code
   - Main components (server, agent_manager, etc.)
   - Key features implemented
   ```
2. Watch it run alongside the first agent

**Expected Behavior:**
- Both agents run concurrently
- Dashboard shows 2 running agents
- Each has its own progress bar
- Updates happen in real-time

## Step 6: Test Agent Details

1. Click on any agent card
2. Detail panel slides in from the right

**Expected to See:**
- Agent ID
- Current status
- Model being used
- Working directory
- Progress metrics (steps, tool calls, etc.)
- Message history (scrollable)
- Action buttons (Send Instruction, Cancel, Delete)

## Step 7: Test Stuck Detection

### Manually Trigger Stuck State

To test stuck detection, create an agent with an unclear task:

1. Create new agent:
   ```
   Find the non-existent file called impossible.txt and tell me what it says
   ```
2. Agent will try to find the file
3. After ~2 minutes of no progress, status changes to "stuck" (orange badge)
4. You should see a notification (browser console)

**Expected Behavior:**
- Status badge changes from blue (running) to orange (stuck)
- Stuck reason appears in detail panel
- System statistics update (stuck count increases)

## Step 8: Test User Intervention

With the stuck agent selected:

1. Click "💬 Send Instruction" button
2. Enter:
   ```
   The file doesn't exist. Instead, list all files in the current directory
   ```
3. Click "Send"

**Expected Behavior:**
- Instruction modal closes
- New message appears in message history
- Agent status changes back to "running"
- Agent continues with new instruction
- Eventually completes successfully

## Step 9: Test Filtering

Use the sidebar filters:

1. Uncheck "Running"
   - Running agents disappear from list
2. Check "Completed"
   - Completed agents appear
3. Check "Stuck"
   - Stuck agents appear

## Step 10: Test WebSocket Updates

Keep the browser tab open and watch for:
- Real-time progress bar updates
- Status badge changes without refresh
- Message count updates
- Last activity timestamp updates
- Connection status (should stay "Connected")

## Step 11: Test API Directly

Open a new terminal:

```bash
# Get system stats
curl http://localhost:8000/api/stats

# List all agents
curl http://localhost:8000/api/agents

# Get specific agent
curl http://localhost:8000/api/agents/{AGENT_ID}
```

Or use the interactive API docs:
- Open http://localhost:8000/docs
- Try the "GET /api/stats" endpoint
- Try the "GET /api/agents" endpoint

## Step 12: Test Multiple Browsers

1. Open http://localhost:8000 in Chrome
2. Open http://localhost:8000 in another browser (Firefox/Safari)
3. Create agent in one browser
4. Watch it appear in real-time in the other browser

**Expected Behavior:**
- Both browsers show the same agents
- Updates broadcast to all connected clients
- Both can send instructions to agents

## Step 13: Test Cancel and Delete

1. Create a new agent with a long-running task
2. While it's running, click the agent to open details
3. Click "⏹️ Cancel" button
4. Confirm the cancellation

**Expected Behavior:**
- Agent status changes to "cancelled"
- Progress stops
- Agent card updates

Then:
1. Click "🗑️ Delete" button
2. Confirm deletion

**Expected Behavior:**
- Agent disappears from list
- Detail panel closes
- System stats update

## Troubleshooting

### Server Won't Start

**Error: "Address already in use"**
```bash
# Find what's using port 8000
lsof -i :8000

# Use different port
hrisa web --port 3000
```

### Can't Import FastAPI

**Error: "No module named 'fastapi'"**
```bash
# Install web dependencies
pip install -e ".[web]"

# Or manually
pip install fastapi uvicorn[standard] websockets
```

### WebSocket Won't Connect

**Status shows "Disconnected"**
1. Check browser console (F12) for errors
2. Refresh the page
3. Restart the server
4. Try different browser

### Ollama Not Found

**Error in agent execution**
```bash
# Start Ollama
ollama serve

# Check it's running
ollama list
```

### Static Files Not Loading

**Blank page or broken UI**
```bash
# Verify files exist
ls src/hrisa_code/web/static/

# Should show: index.html, styles.css, app.js

# Reinstall
pip install -e ".[web]"
```

## Test Checklist

Use this checklist to ensure everything works:

- [ ] Server starts without errors
- [ ] Web UI loads in browser
- [ ] Can create new agent
- [ ] Agent starts running
- [ ] Real-time progress updates work
- [ ] Can view agent details
- [ ] Can see message history
- [ ] Stuck detection works (after 2 min)
- [ ] Can send instruction to stuck agent
- [ ] Agent resumes after instruction
- [ ] Can cancel running agent
- [ ] Can delete agent
- [ ] Filters work (show/hide by status)
- [ ] Multiple agents run concurrently
- [ ] Multiple browsers sync in real-time
- [ ] API docs accessible (/docs)
- [ ] API endpoints respond correctly
- [ ] Connection status shows "Connected"
- [ ] System statistics update correctly

## Next Steps After Testing

If all tests pass:

1. **Use it for real work**:
   - Generate documentation for your projects
   - Refactor code with agent assistance
   - Run multiple analysis tasks

2. **Report issues**:
   - Note any bugs or unexpected behavior
   - Suggest improvements
   - Document edge cases

3. **Experiment**:
   - Try different task types
   - Test with different models
   - Push the concurrent agent limit

4. **Deploy** (Future):
   - We'll set up Vercel/Render deployment
   - Add authentication for multi-user
   - Add persistence for agent history

## Performance Expectations

**Normal Behavior:**
- Agent creation: < 1 second
- WebSocket updates: < 100ms
- API responses: < 500ms
- UI rendering: < 200ms

**If Slower:**
- Check Ollama model size (32B is slower than 7B)
- Check system resources (RAM, CPU)
- Reduce concurrent agents (from 5 to 2-3)

## Known Limitations

Currently:
- ❌ No persistence (agents lost on restart)
- ❌ No authentication (single user)
- ❌ No agent history export
- ❌ No agent templates
- ✅ Works locally only
- ✅ Max 5 concurrent agents

## Success Criteria

The web UI is working correctly if:
1. ✅ You can create and run agents
2. ✅ Progress updates in real-time
3. ✅ Stuck agents are detected
4. ✅ You can send instructions
5. ✅ Multiple agents work simultaneously
6. ✅ No errors in browser console
7. ✅ No errors in server logs

## Getting Help

If you encounter issues:
1. Check server terminal for errors
2. Check browser console (F12) for errors
3. Review `docs/WEB_UI.md` for detailed docs
4. Check the validation script output
5. Ensure Ollama is running with a model

---

**Happy Testing!** 🚀

Once you've verified everything works, you can start using the web UI for real tasks and provide feedback for improvements.
