# Docker Deployment - Testing Guide

**Date**: 2026-03-04  
**Status**: ✅ Deployment Complete - Ready for Testing

## Deployment Status

✅ **ALL SERVICES RUNNING**
- **Ollama**: Healthy on port 11434
- **Web UI**: Healthy on port 8000  
- **Verification**: Passed (entrypoint checks completed)
- **PDF Libraries**: Installed and working

## Quick Access

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama API**: http://localhost:11434

---

## Phase 1: Verify Deployment ✅ (DONE)

These have already been confirmed working:

- [x] Docker services running
- [x] Ollama service healthy
- [x] Web UI service healthy
- [x] Verification checks passed
- [x] PDF libraries available

---

## Phase 2: Test Web UI (START HERE)

### Test 1: Access Web UI

Open your browser to:
**http://localhost:8000**

Or use command:
```bash
open http://localhost:8000
```

**Expected**: Clean web interface with "Create New Agent" button

**Result**: ✅ PASS / ❌ FAIL

---

### Test 2: Pull a Model First

Before creating agents, pull a model (takes 5-10 minutes):

```bash
docker exec hrisa-ollama ollama pull qwen2.5-coder:7b
```

**Or pull both recommended models**:
```bash
./deploy.sh pull-models
```

Wait for completion, then verify:
```bash
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

You should see the model(s) listed.

---

### Test 3: Create Your First Agent

1. In the Web UI, click "Create New Agent"
2. Enter task: **"List all Python files in the current directory"**
3. Click "Create & Start"

**Expected**:
- Agent appears in list
- Status changes: initializing → running → completed
- Real-time output appears
- Agent completes successfully

**Result**: ✅ PASS / ❌ FAIL

---

### Test 4: Test Real-Time Updates

While an agent runs:
- Watch the status update automatically
- See output appear in real-time
- No need to refresh the page

**Expected**: Live updates via WebSocket

**Result**: ✅ PASS / ❌ FAIL

---

## Phase 3: Test API Endpoints

### Test 5: Check Service Stats

```bash
curl -s http://localhost:8000/api/stats | python3 -m json.tool
```

**Expected Output**:
```json
{
    "total_agents": 0,
    "running_agents": 0,
    "stuck_agents": 0,
    "completed_agents": 0,
    "failed_agents": 0,
    "cancelled_agents": 0
}
```

---

### Test 6: Create Agent via API

```bash
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{"task": "Calculate 2 + 2", "model": "qwen2.5-coder:7b"}'
```

**Expected**: JSON response with agent ID and status

---

## Phase 4: Verification Testing

### Test 7: Check Startup Verification

```bash
docker-compose logs web | grep -A 15 "Hrisa Code - Docker Startup"
```

**Expected Output**:
```
========================================
  Hrisa Code - Docker Startup
========================================

[1/3] Waiting for Ollama service...
✓ Ollama service is ready

[2/3] Checking for required models...
✓ All required models are available

[3/3] Running pre-flight checks...
✓ Verification passed

========================================
  Hrisa Code Ready!
========================================
```

---

### Test 8: Run Verification Service

```bash
./deploy.sh verify
```

**Expected**: Table showing all checks passed with ✓ marks

---

### Test 9: Verify PDF Support

```bash
docker exec hrisa-web python3 -c "import pypdf; print('✓ PDF support available')"
```

**Expected Output**: `✓ PDF support available`

---

## Troubleshooting

### Web UI Won't Load

1. Check service status:
   ```bash
   docker-compose ps
   ```
   Both should show "Up" and "healthy"

2. Check logs:
   ```bash
   docker-compose logs web --tail=50
   ```

3. Restart services:
   ```bash
   ./deploy.sh restart
   ```

---

### Models Won't Pull

1. Check internet connection
2. Check disk space: `df -h` (need 20+ GB free)
3. Check Ollama logs: `docker-compose logs ollama`

---

### Agents Fail to Execute

1. Verify model is pulled:
   ```bash
   docker exec hrisa-ollama ollama list
   ```

2. Check Ollama connectivity:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. View agent output in Web UI for error details

---

## Useful Commands

```bash
# Check status
./deploy.sh status

# View logs
./deploy.sh logs

# Check system
./deploy.sh check

# Pull models
./deploy.sh pull-models

# Restart services
./deploy.sh restart

# Stop services
./deploy.sh stop
```

---

## Success Criteria

Deployment is **SUCCESSFUL** if:

✅ **Critical**:
- [ ] Web UI loads in browser
- [ ] Can pull models successfully
- [ ] Can create and run agents
- [ ] Agents complete tasks

✅ **Important**:
- [ ] Verification passes on startup
- [ ] PDF libraries available
- [ ] Real-time updates work

---

## Next Steps

### After Successful Testing

1. **Pull more models** (optional):
   ```bash
   docker exec hrisa-ollama ollama pull deepseek-coder:6.7b
   docker exec hrisa-ollama ollama pull codellama:34b
   ```

2. **Configure for your needs**:
   - Edit docker-compose.yml environment variables
   - Set AUTO_PULL_MODELS=true for convenience
   - Adjust resource limits

3. **Use regularly**:
   - `./deploy.sh start` to start
   - `./deploy.sh stop` to stop
   - `./deploy.sh backup` to backup data

---

## Test Results

**Date Tested**: 2026-03-04
**Tested By**: Automated Deployment Test
**Overall Result**: ⏳ IN PROGRESS

### Test Summary
- [x] Test 1: Web UI Access - ✅ PASS (http://localhost:8000 accessible)
- [⏳] Test 2: Pull Model - IN PROGRESS (43% complete, ~21 min remaining)
- [ ] Test 3: Create Agent - PENDING (waiting for model)
- [ ] Test 4: Real-Time Updates - PENDING (waiting for model)
- [x] Test 5: API Stats - ✅ PASS (API responding correctly)
- [ ] Test 6: API Create Agent - PENDING (waiting for model)
- [x] Test 7: Startup Verification - ✅ PASS (all checks passed)
- [x] Test 8: Verification Service - ✅ PASS (services healthy)
- [x] Test 9: PDF Support - ✅ PASS (pypdf available)

**Notes**:
- All services deployed successfully and healthy
- Web UI JavaScript bug fixed (app.js:99)
- Model llama3.2:latest downloading at 903 KB/s
- Tests 3-4 and 6 will proceed automatically when model completes
- Monitoring script running to detect completion

### Current Status
```
Services:  ✅ All Healthy
Web UI:    ✅ http://localhost:8000
API:       ✅ http://localhost:8000/docs
Ollama:    ✅ http://localhost:11434
Model:     ⏳ 43% (870 MB/2.0 GB, ~21 min remaining)
```

---

**Ready to start coding with AI!** 🚀

For detailed documentation, see:
- `DOCKER_VERIFICATION.md` - Verification system details
- `DOCKER_DEPLOYMENT.md` - Complete deployment guide
- `DOCKER_QUICKSTART.md` - Quick reference
