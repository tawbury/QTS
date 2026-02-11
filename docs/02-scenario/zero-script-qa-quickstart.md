# Zero Script QA - Quick Start Guide

**For**: Running first QA monitoring session on QTS
**Time Required**: 20-30 minutes
**Prerequisites**: Docker, Docker Compose, basic bash knowledge

---

## 5-Minute Setup

### Step 1: Navigate to Project
```bash
cd /home/tawbu/projects/QTS
```

### Step 2: Prepare Docker Network (first time only)
```bash
docker network create qts-bridge || true
```

### Step 3: Build Docker Image
```bash
docker-compose -f docker/docker-compose.local.yml build
```

### Step 4: Start Services (Terminal 1)
```bash
docker-compose -f docker/docker-compose.local.yml up
```

You should see:
```
qts-test | [INFO] Started ETEDA loop
qts-test | [INFO] Iteration 1/50
qts-test | Extract stage starting...
...
```

### Step 5: Monitor Logs (Terminal 2)
```bash
# In a new terminal
docker-compose logs -f qts-test
```

---

## What to Look For

### Green Signals (System Working)
```
✓ "Started ETEDA loop"
✓ "Iteration N/50" (increasing)
✓ "Extract stage" completed in <100ms
✓ "Transform stage" completed in <50ms
✓ "Evaluate stage" completed in <200ms
✓ "Decide stage" completed in <100ms
✓ "Act stage" completed in <500ms
✓ "Cycle completed" or "Order placed"
```

### Red Signals (Issues to Report)
```
✗ [ERROR] anywhere in logs
✗ Stuck on single iteration (not progressing)
✗ Stage duration > thresholds above
✗ "Broker error" or "Connection timeout"
✗ "Safety trigger" or "State: FAIL"
✗ Unhandled exception
```

---

## Basic Analysis

### Quick Filters

```bash
# See only errors
docker-compose logs qts-test | grep -i error

# See only warnings
docker-compose logs qts-test | grep -i warning

# See only ETEDA stage logs
docker-compose logs qts-test | grep -i "stage\|cycle"

# Count iterations
docker-compose logs qts-test | grep "Iteration" | wc -l

# Find slowest stage
docker-compose logs qts-test | grep "duration\|time" | sort
```

### Performance Baseline

Run the system for 50 iterations and observe:

```
Extract:   10-50ms average
Transform:  5-30ms average
Evaluate:  50-150ms average
Decide:    20-80ms average
Act:      100-400ms average
---
Total:    200-700ms per cycle
```

If your numbers are significantly higher, capture logs for analysis:
```bash
docker-compose logs qts-test > /tmp/slow-logs.txt
```

---

## Documentation Template

After running a test session, create a file:
`docs/02-scenario/qa-run-{YYYYMMDD}-{N}.md`

```markdown
# QA Run - {Date}

**Duration**: Start time → End time
**Iterations Completed**: X/50
**Status**: PASS / PARTIAL / FAIL

## What Happened
[Brief summary of test run]

## Key Observations
- Extract time: ___ms avg
- Transform time: ___ms avg
- Evaluate time: ___ms avg
- Decide time: ___ms avg
- Act time: ___ms avg

## Issues Found
[If any errors appeared, list them here with timestamps]

### Issue-1: [Title]
```
[Paste relevant log lines]
```
Root cause: [Your analysis]
Fix needed: [Recommendation]

## Next Steps
- [ ] [Action item 1]
- [ ] [Action item 2]
```

---

## Common Issues & Quick Fixes

### "Container won't start"
```bash
# Check what's wrong
docker-compose logs qts-test

# Common causes:
# 1. Port conflict
docker ps | grep qts

# 2. Image build failed
docker-compose build --no-cache

# 3. Volume issues
docker volume ls
docker volume prune
```

### "Logs not appearing"
```bash
# Verify container is running
docker ps | grep qts

# Check logs directly
docker exec qts-test tail -f logs/qts.log

# Or stream from compose
docker-compose logs -f --tail 50
```

### "System hangs on first cycle"
```bash
# Check for blocking I/O
docker exec qts-test ps aux | grep python

# Check logs for specific error
docker-compose logs qts-test | grep -E "ERROR|timeout|blocked"

# If stuck, force restart
docker-compose restart
```

### "Errors about missing Observer data"
```bash
# This is expected in local-only mode
# The system should handle it gracefully

# Check that it falls back to mock data
docker-compose logs qts-test | grep -i "mock\|fallback"

# If not, it's a bug to document
```

---

## Stopping the System

### Graceful Shutdown
```bash
# Ctrl+C in the terminal where you ran `up`
# Wait for it to finish current iteration
```

### Force Shutdown (if needed)
```bash
docker-compose down
```

### Cleanup Everything
```bash
docker-compose down -v        # Remove volumes
docker-compose down --rmi all # Remove images
docker volume prune           # Clean unused volumes
```

---

## Record Your Findings

### When You See an Error
1. Note the timestamp
2. Copy the error message
3. Identify which ETEDA stage it's in
4. Check logs before the error for context
5. Create an issue document (see template above)

### When You See Slow Performance
1. Identify which stage is slow
2. Note the duration in milliseconds
3. Run multiple cycles to confirm it's consistent
4. Capture full logs: `docker-compose logs qts-test > /tmp/slow.txt`
5. Create a performance issue document

### When System Behaves Unexpectedly
1. Save the full logs
2. Note exact steps to reproduce
3. Check safety layer state (Normal/Warning/Fail/Lockdown)
4. Document observations
5. Create investigation document

---

## Save Your Logs

```bash
# Save full session
docker-compose logs qts-test > /tmp/qts-session-$(date +%s).txt

# Or with timestamp in filename
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker-compose logs qts-test > /tmp/qts-$TIMESTAMP.txt

# Or with explicit description
docker-compose logs qts-test > /tmp/qts-perf-issue-cycle1.txt
```

These logs are crucial for debugging. Keep them together with your issue report.

---

## What Happens Next?

After you run this quick start:

1. **If all green** ✓
   - System is working well!
   - Proceed to Phase 2 (logging upgrades)
   - Run longer test cycles (500+ iterations)

2. **If some issues** ⚠️
   - Document them clearly
   - Attempt basic fixes
   - Re-run to verify fix
   - Record results

3. **If many issues** ✗
   - Save all logs
   - Escalate to development team
   - Plan Phase 2 infrastructure work

---

## Tips for Better QA

### 1. Run Multiple Sessions
- Different times of day
- Different iteration counts
- Different configurations (if available)

### 2. Establish Baselines
- First successful run = baseline performance
- Compare subsequent runs against this baseline
- Flag if worse by >10%

### 3. Test Edge Cases
- What happens after 100 cycles?
- What happens if market data is missing?
- What happens if broker connection drops?

### 4. Document Everything
- Not just failures, but successes too
- Establish patterns
- Create runbook for common issues

### 5. Automate When Possible
- Save logs to consistent location
- Use grep filters for analysis
- Create dashboards from metrics

---

## Emergency Contacts

If you encounter:

**Critical Error** (system crashes):
- Check logs in `/tmp/qts-*.txt`
- Note stack trace
- Check `docs/arch/` for relevant architecture

**Performance Issue** (slow beyond reasonable):
- Save logs with timestamp
- Identify bottleneck stage
- Check for resource constraints (CPU/Memory/Disk)

**Broker Connection Issue**:
- Verify mock broker is configured
- Check network connectivity
- Review broker adapter code in `src/provider/`

**Safety System Trigger**:
- Check logs for `safety_state` changes
- Identify what triggered the warning/fail
- Review `src/safety/` for guardrail logic

---

## Remember

**Zero Script QA** is about:
- Reading logs carefully
- Understanding system behavior from output
- Detecting patterns
- Documenting findings

You don't need to write code to run QA. You just need to:
1. Start the system
2. Monitor the logs
3. Record what you see
4. Report your findings

Good QA creates visibility. Good logs enable good QA.

---

Happy testing! 🚀
