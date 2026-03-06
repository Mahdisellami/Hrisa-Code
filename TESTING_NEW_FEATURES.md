# Testing Guide: New Features

**Deployment Status**: ✅ Running
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🎯 Feature Test Plan

### Prerequisites
1. Open http://localhost:8000 in your browser
2. WebSocket should connect automatically (check connection status in header)

---

## Test 1: State Machine Flow Diagram

**What it does**: Shows horizontal flowchart of agent state transitions

**Steps**:
1. Click "Create New Agent" button
2. Enter task: `Write a simple hello world function in Python`
3. Set Role: "Coder"
4. Click "Create & Start"
5. Select the agent from the list
6. Scroll down to "State Machine" section
7. Look for "State Flow Diagram"

**Expected Results**:
- Should see horizontal flowchart: `INITIALIZING → PLANNING → EXECUTING → ...`
- Current state highlighted in orange/brand color with larger font
- Arrow (→) between states
- Smooth horizontal scrolling if many states

**Visual Example**:
```
[INITIALIZING] → [PLANNING] → [EXECUTING] → [THINKING] → [TOOL_USE]
                                  ^^^^^ (highlighted if current)
```

---

## Test 2: Workflow Tree Visualization

**What it does**: Shows parent-child agent relationships as interactive tree

**Steps**:
1. Wait for first agent to complete (or fail)
2. Click "🔗 Create Follow-up Agent" button
3. Enter task: `Write unit tests for the hello world function`
4. Check "Auto-start when parent completes"
5. Click "Create Follow-up Agent"
6. Select either parent or child agent
7. Look for "Workflow Chain" section

**Expected Results**:
- Should see tree structure with parent at top
- Visual lines connecting parent to children (└─)
- Current agent highlighted with orange border
- Click on any node to navigate to that agent
- Shows role icons, step numbers, and status
- Hover effects on nodes

**Visual Example**:
```
● Parent Agent (Coder)
  Step 0 • completed

  └─ ● Child Agent (Tester)
     Step 1 • running
```

---

## Test 3: Progress Metrics Dashboard

**What it does**: Shows comprehensive metrics with charts and counters

**Steps**:
1. Select any running or completed agent
2. Scroll to "Progress & Metrics" section

**Expected Results**:

**A) State Distribution Bar Chart**:
- Horizontal bar showing time spent in each state
- Color-coded segments (different color per state)
- Legend below showing state names and counts
- Percentages visible in larger segments

**B) Activity Metrics Grid (2x2)**:
- Tool Calls: Number with orange left border
- Tool Results: Number with green left border
- Errors: Number with red left border
- Warnings: Number with yellow left border

**C) Execution Time**:
- Shows formatted time: `Xh Ym Zs`
- Shows start timestamp
- Blue background card

**D) Total Transitions Counter**:
- Shows total number of state transitions

---

## Test 4: Memory Timeline View

**What it does**: Chronological timeline of all memory events (decisions, outputs, state changes)

**Steps**:
1. Select any agent that has run for a while
2. Scroll to "Memory Timeline" section

**Expected Results**:
- Vertical timeline with connecting line on left
- Events sorted newest first
- Three types of events:
  - 🎯 **Decisions** (orange/terracotta background)
  - 📤 **Outputs** (blue background)
  - 🔄 **State Changes** (purple background)
- Colored dots on timeline for each event
- Timestamps on right
- Hover effect: cards slide right slightly
- Scrollable (max 500px height)
- Sticky header showing event count

**Visual Example**:
```
Memory Timeline (15 events)
─────────────────────────────
  ● 🔄 State Change
     EXECUTING → THINKING
     16:32:45

  ● 📤 Output
     Generated function...
     16:32:40

  ● 🎯 Decision
     Use recursive approach
     16:32:35
```

---

## Test 5: Session Management - Save

**What it does**: Save current session with all agents to disk

**Steps**:
1. Create 2-3 agents with different tasks
2. Wait for at least one to complete and produce artifacts
3. Click "💾 Save Session" button in sidebar
4. Enter Session Name: `Test Session 1`
5. Enter Description: `Testing session management features`
6. Click "💾 Save Session"

**Expected Results**:
- Modal closes
- Success notification appears
- Session saved to `~/.hrisa/sessions/XXXXXXXX.json`

**Verify**:
```bash
ls -la ~/.hrisa/sessions/
cat ~/.hrisa/sessions/*.json | python3 -m json.tool | head -30
```

Should show:
- Session file exists
- Contains agent data, messages, logs, artifacts, memory

---

## Test 6: Session Management - Load

**What it does**: Load previously saved session, replacing current agents

**Steps**:
1. Click "📂 Load Session" button in sidebar
2. You should see your saved session(s) listed
3. Each session shows:
   - Name and description
   - Agent count and artifact count
   - Timestamp
4. Click "📂 Load" button on a session
5. Confirm the warning dialog

**Expected Results**:
- Current agents cleared
- Saved agents restored with all data:
  - Messages
  - Logs
  - Artifacts
  - Memory (decisions, outputs, transitions)
  - State machine history
  - Workflow relationships
- Agent list updates
- All visualizations work with restored data

**Verify**:
- Select restored agent
- Check artifacts are present
- Check memory timeline shows historical data
- Check state transitions are preserved

---

## Test 7: Session Management - Delete

**What it does**: Delete saved session from disk

**Steps**:
1. Click "📂 Load Session"
2. Click "🗑️" button on a session
3. Confirm deletion

**Expected Results**:
- Session removed from list
- Success notification
- File deleted from `~/.hrisa/sessions/`

---

## Test 8: Agent Replay

**What it does**: Create new agent with same task and auto-start it

**Steps**:
1. Select a completed or failed agent
2. Click "🔄 Replay" button in actions section
3. Confirm the dialog

**Expected Results**:
- New agent created with:
  - Same task (prefixed with `[REPLAY]`)
  - Same working directory
  - Same model
  - Same role
  - Additional tags: `replay`, `replay-of-XXXXXXXX`
- New agent starts automatically
- You're navigated to the new agent
- Success notification appears

**Verify**:
- New agent appears in agent list
- Task shows `[REPLAY]` prefix
- Agent is running
- Tags include "replay"

---

## Test 9: Agent Chaining (Extended Test)

**What it does**: Create multi-step workflows with auto-start

**Steps**:
1. Create Agent 1: `Write a calculator function with add, subtract, multiply, divide`
   - Role: Coder
2. Wait for completion
3. Click "🔗 Create Follow-up Agent"
   - Task: `Write unit tests for the calculator`
   - Role: Tester
   - ✅ Check "Auto-start when parent completes" (already complete, so starts immediately)
4. Wait for Agent 2 to complete
5. On Agent 2, click "🔗 Create Follow-up Agent"
   - Task: `Review the code and tests for improvements`
   - Role: Reviewer
   - ✅ Check "Auto-start"

**Expected Results**:
- 3-level workflow chain: Coder → Tester → Reviewer
- Each child inherits artifacts from parent
- Workflow tree shows all three agents
- Each at different workflow_step (0, 1, 2)
- Auto-start works (agents start immediately after parent)

**Verify Workflow Tree**:
```
● Calculator (Coder) - Step 0
  └─ ● Tests (Tester) - Step 1
      └─ ● Review (Reviewer) - Step 2
```

---

## Test 10: Combined Workflow

**Complete end-to-end test of all features**

**Scenario**: Multi-agent documentation generation workflow with session persistence

**Steps**:

1. **Create Root Agent**:
   - Task: `Analyze the calculator code structure`
   - Role: Architect

2. **Watch Visualizations Update in Real-Time**:
   - Select the agent
   - Watch state flow diagram update as states change
   - Watch progress metrics accumulate
   - Watch memory timeline grow with events

3. **Create Child Agent Chain**:
   - When complete, create follow-up: `Document the architecture`
   - Role: Documentation
   - Auto-start: Yes

4. **Save Session**:
   - Click "💾 Save Session"
   - Name: `Documentation Workflow`
   - Description: `Multi-agent doc generation`
   - Save

5. **Test Load Session**:
   - Create a new dummy agent
   - Click "📂 Load Session"
   - Load "Documentation Workflow"
   - Verify all agents restored with history

6. **Test Replay**:
   - Select root agent
   - Click "🔄 Replay"
   - Watch new workflow execute

---

## 🐛 Common Issues & Solutions

### Issue: Visualizations not showing
**Solution**:
- Refresh page (F5)
- Check browser console for errors
- Ensure agent has actually run (state transitions exist)

### Issue: Session load fails
**Solution**:
- Check `~/.hrisa/sessions/` directory exists
- Check file permissions
- Verify JSON is valid: `cat ~/.hrisa/sessions/XXX.json | python3 -m json.tool`

### Issue: Agent gets stuck immediately
**Solution**:
- Ollama might be overloaded (1 concurrent agent limit)
- Check Ollama CPU: `docker stats hrisa-ollama`
- Wait for current agent to finish
- Consider restarting Ollama: `docker restart hrisa-ollama`

### Issue: WebSocket disconnected
**Solution**:
- Check connection status indicator in header
- Refresh page
- Check docker logs: `docker-compose logs web -f`

---

## 📊 What to Look For

### Good Signs ✅
- State flow diagram updates smoothly
- Progress metrics show realistic numbers
- Memory timeline has variety of events (decisions, outputs, states)
- Workflow tree is interactive and navigable
- Sessions save/load without data loss
- Replay creates functional duplicate agents

### Potential Issues ⚠️
- Missing visualizations: Agent hasn't run enough yet
- Empty timeline: Agent in early stages (give it time)
- Slow updates: Ollama CPU overload (normal with llama3.2)
- Agent stuck: Expected behavior with heavy model on limited resources

---

## 🎥 Test Recording Checklist

If recording the test session:
- [ ] Show state flow diagram updating in real-time
- [ ] Navigate workflow tree (click on different nodes)
- [ ] Scroll through memory timeline
- [ ] Save a session
- [ ] Delete current agents
- [ ] Load the session back
- [ ] Show data is preserved (artifacts, memory, etc.)
- [ ] Replay an agent
- [ ] Create 3-level agent chain

---

## 📝 Quick Test Script

Run this to quickly test all endpoints:

```bash
# Test health
curl http://localhost:8000/health

# Test sessions list
curl http://localhost:8000/api/sessions

# Test agents list
curl http://localhost:8000/api/agents

# Test roles
curl http://localhost:8000/api/roles

# Test stats
curl http://localhost:8000/api/stats
```

---

## Next Steps

After testing, report:
1. ✅ Which features work as expected
2. 🐛 Any bugs or unexpected behavior
3. 💡 Suggestions for improvements
4. 🎯 Priority for next features

Enjoy testing! 🚀
