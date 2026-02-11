# Zero Script QA Setup Guide for QTS

**Status**: Phase 1 - Setup & Assessment
**Date Created**: 2026-02-11
**Last Updated**: 2026-02-11

---

## Overview

This guide establishes the Zero Script QA methodology for QTS. Zero Script QA verifies system behavior through **structured log analysis** and **real-time monitoring** without traditional test scripts.

```
Traditional QA: Write tests → Run → Check → Maintain
Zero Script QA: Instrument logs → Manual flow → AI monitors → Auto-detect issues
```

---

## Current State Assessment

### Logging Infrastructure
- **Status**: Functional, text-based
- **Location**: `src/monitoring/central_logger.py`
- **Logger Names**: `runtime.eteda`, `runtime.engine`, `runtime.broker`, `runtime.monitoring`
- **Output**: Console (DEBUG in dev) + Optional file rotation
- **Format**: Text-based with timestamp, level, logger name, message
- **Request Tracking**: None (opportunity for enhancement)

### Docker Setup
- **Local Development**: `docker/docker-compose.local.yml`
- **Test Environment**: `docker/docker-compose.test.yml`
- **E2E Testing**: `docker/docker-compose.e2e.yml`
- **Log Driver**: json-file with size limits (10MB per file, 3 backups)
- **Networking**: Bridge network for multi-container coordination

### Entry Point
```bash
python -m src.runtime.main
  --scope [scalp|swing]
  --broker [kis|kiwoom]
  --local-only              # Use mock broker
  --max-iterations 50       # Limit cycles for testing
  -v/--verbose              # DEBUG logging
```

---

## QA Monitoring Workflow

### 1. Start Test Environment

```bash
# Terminal 1: Start Docker services
cd /home/tawbu/projects/QTS
docker-compose -f docker/docker-compose.local.yml up --build

# Terminal 2: Start log monitoring (Claude Code monitors here)
docker-compose logs -f
```

### 2. Monitor Log Streams

Claude Code analyzes logs in real-time for:

#### Error Detection Pattern
```
[ERROR] in any logger
→ Immediate flag + Request ID extraction
→ Collect all related logs
→ Analyze failure point in ETEDA pipeline
→ Document in issue report
```

#### Performance Pattern (Slow Response)
```
Extract time > 100ms
Transform time > 50ms
Evaluate time > 200ms
Decide time > 100ms
Act time > 500ms
→ Flag as performance warning
→ Recommend optimization
```

#### Safety State Pattern
```
NORMAL → WARNING (guardrail triggered)
WARNING → FAIL (safety threshold exceeded)
FAIL → LOCKDOWN (kill switch activated)
→ Document state transition + timestamp
→ Analyze preceding events
→ Assess recovery behavior
```

### 3. Log Tracking by Stage

QTS ETEDA Pipeline stages to monitor:

| Stage | Handler | Success Log | Failure Log |
|-------|---------|-------------|-------------|
| **Extract** | ObserverClient | Market data loaded | File I/O error, timeout |
| **Transform** | DataCalculator | Schema validation passed | Type error, NULL handling |
| **Evaluate** | Strategy/Risk/Portfolio engines | Position calculation OK | Calculation error, constraint violation |
| **Decide** | DecisionEngine | Order decision made | Logic error, tie-breaking failed |
| **Act** | BrokerClient | Order submitted/confirmed | Broker error, connection lost |

---

## Phase 1: Assessment (CURRENT)

### Goals
1. Verify Docker Compose startup without errors
2. Capture baseline log output (10-50 iterations)
3. Document current ETEDA cycle timing
4. Identify missing error handling
5. Assess performance bottlenecks

### Manual Test Checklist

```bash
# 1. Start environment
docker-compose -f docker/docker-compose.local.yml up --build

# 2. Monitor logs (in separate terminal)
docker-compose logs -f qts-test

# 3. Verify successful startup logs
# Expected: "Started ETEDA loop", "Max iterations: 50"

# 4. Let system run for 10-20 cycles
# Monitor: Extract → Transform → Evaluate → Decide → Act

# 5. Check for errors/warnings
docker-compose logs qts-test | grep -i error
docker-compose logs qts-test | grep -i warning

# 6. Capture sample logs
docker-compose logs qts-test > /tmp/qts-baseline-logs.txt

# 7. Stop environment
docker-compose down
```

### What to Document

**File**: `docs/02-scenario/zero-script-qa-{date}-cycle1.md`

```markdown
# QTS QA Test Cycle 1 - Baseline Assessment

## Environment
- Date: 2026-02-11
- Command: docker-compose -f docker/docker-compose.local.yml up --build
- Duration: 10 minutes
- Iterations: 20

## Results
- Startup time: ___ seconds
- Errors encountered: ___ (list them)
- Warnings encountered: ___ (list them)
- Total cycles completed: ___
- Average cycle time: ___ ms

## Timing Analysis
- Extract stage avg: ___ ms
- Transform stage avg: ___ ms
- Evaluate stage avg: ___ ms
- Decide stage avg: ___ ms
- Act stage avg: ___ ms
- **Total cycle avg**: ___ ms

## Issues Found
### ISSUE-001: [Title]
- Location in logs: [line number or timestamp]
- Severity: CRITICAL/WARNING/INFO
- Description: [what happened]
- Related code: [file:line]
- Reproduction: [steps]
- Recommended fix: [suggestion]

## Performance Notes
- [Observations about bottlenecks]
- [Observations about error patterns]

## Next Steps
- [ ] Fix identified issues
- [ ] Re-run Phase 1 assessment
- [ ] Proceed to Phase 2 (JSON logging upgrade)
```

---

## Phase 2: Infrastructure Upgrade (PLANNED)

### Objective
Convert text logs to JSON format with Request ID propagation.

### Changes Required

#### 1. Enhance `src/monitoring/central_logger.py`
```python
# Add JSON formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        import json
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": "qts",
            "request_id": getattr(record, 'request_id', 'N/A'),
            "stage": getattr(record, 'stage', 'N/A'),  # ETEDA stage
            "message": record.getMessage(),
        }
        if hasattr(record, 'data'):
            log_record["data"] = record.data
        return json.dumps(log_record)
```

#### 2. Add Request ID to `src/runtime/main.py`
```python
import uuid

request_id = f"req_{uuid.uuid4().hex[:8]}"
# Pass to ETEDA loop and all engines
```

#### 3. Propagate through Pipeline
- Add `request_id` parameter to `run_eteda_loop()`
- Pass through each stage: Extract → Transform → Evaluate → Decide → Act
- Log each stage with Request ID

### Success Criteria
- All logs are valid JSON
- Every log line contains `request_id` field
- All ETEDA stages include `stage` field
- Startup to first Extract: logged
- Each stage: start + duration + success/failure logged

---

## Phase 3: Real-time Monitoring (PLANNED)

### Automation Rules

Claude Code will monitor logs and:

#### Rule 1: Error Detection
```
IF log.level == "ERROR" THEN
  - Extract request_id
  - Collect all logs with same request_id
  - Analyze failure point (which stage)
  - Document in issue report with:
    * Request ID
    * ETEDA stage where error occurred
    * Full error message
    * Stack trace (if available)
    * Suggested remediation
```

#### Rule 2: Performance Warning
```
IF any_stage_duration > threshold THEN
  - Extract ETEDA stage name
  - Extract duration_ms
  - Compare against baseline
  - Log as WARNING if > 2x baseline
  - Document bottleneck analysis
```

#### Rule 3: Safety State Transition
```
IF safety_state_changed THEN
  - Log state change with timestamp
  - Extract triggering condition
  - Collect preceding N logs
  - Document state machine transition
  - Check recovery mechanism
```

#### Rule 4: Broker Connection Error
```
IF broker.error or connection_lost THEN
  - Extract broker error code
  - Determine error type (timeout/auth/invalid_order/etc)
  - Extract order details (if applicable)
  - Document broker-specific error handling
  - Check fallback/retry behavior
```

---

## Phase 4: QA Reporting (PLANNED)

### Issue Documentation Template

**File**: `docs/02-scenario/zero-script-qa-issues-{date}.md`

```markdown
# QTS QA Issues Report

**Test Period**: {date start} to {date end}
**Total Cycles**: {number}
**Pass Rate**: {percentage}%
**Issues Found**: {count}

## Summary
- Critical: {count}
- Warning: {count}
- Info: {count}

## Issues by Severity

### CRITICAL

#### ISSUE-001: [Title]
**Request ID**: req_abc12345
**ETEDA Stage**: {Extract|Transform|Evaluate|Decide|Act}
**Timestamp**: 2026-02-11 10:30:45.123Z
**Error Message**:
```
{full error text from logs}
```

**Analysis**:
- Root cause: [analysis]
- Affected component: [file path]
- Impact: [what fails]

**Reproduction Steps**:
1. Start system with --local-only
2. [step 2]
3. [step 3]
4. Observe: [error]

**Recommended Fix**:
- Modify: `src/path/to/file.py:line_number`
- Change: [describe fix]
- Test: [how to verify fix]

---

### WARNING

#### ISSUE-002: [Title]
...

---

## Summary Statistics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Cycle Success Rate | __% | >95% | ✓/✗ |
| Avg Extract Time | ___ms | <100ms | ✓/✗ |
| Avg Transform Time | ___ms | <50ms | ✓/✗ |
| Avg Evaluate Time | ___ms | <200ms | ✓/✗ |
| Avg Decide Time | ___ms | <100ms | ✓/✗ |
| Avg Act Time | ___ms | <500ms | ✓/✗ |
| Error Recovery Rate | __% | >95% | ✓/✗ |

## Recommendations
- [action item 1]
- [action item 2]
```

---

## Docker Commands Reference

### Startup
```bash
# Build and start
docker-compose -f docker/docker-compose.local.yml up --build

# Start in background
docker-compose -f docker/docker-compose.local.yml up -d --build

# View services status
docker-compose ps
```

### Logging
```bash
# Stream all logs
docker-compose logs -f

# Stream specific service
docker-compose logs -f qts-test

# Last N lines
docker-compose logs --tail 100 qts-test

# Since time
docker-compose logs --since 5m qts-test

# Save to file
docker-compose logs > logs-$(date +%Y%m%d_%H%M%S).txt
```

### Cleanup
```bash
# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all
```

### Debugging
```bash
# Shell into container
docker exec -it qts-test bash

# Check logs from inside
docker exec qts-test tail -f logs/qts.log

# Check environment variables
docker exec qts-test env | grep QTS
```

---

## Testing Scenarios

### Scenario 1: Happy Path (All stages succeed)
```bash
# Expected behavior:
# Extract → Transform → Evaluate → Decide → Act → Success
# All stages should log without errors
# Cycle time < 2000ms
```

### Scenario 2: Extract Failure (Bad market data)
```bash
# Expected behavior:
# Extract fails → Cycle skipped → System continues
# Error should be logged with context
# Next cycle should retry
```

### Scenario 3: Decision Conflict (Multiple signals)
```bash
# Expected behavior:
# Evaluate produces conflicting signals
# Decide applies tie-breaking logic
# Single decision produced → Act executes
```

### Scenario 4: Broker Timeout
```bash
# Expected behavior:
# Act → Broker call timeout
# Retry logic activated
# Error logged with duration
# System continues
```

### Scenario 5: Safety Trigger (Risk limit exceeded)
```bash
# Expected behavior:
# Evaluate → Risk constraint violation
# Safety layer triggers → State: WARNING
# Decide blocked → No order
# Next cycle: Risk re-evaluated
```

---

## Monitoring Checklist

- [ ] Docker Compose starts without errors
- [ ] QTS container healthcheck passes
- [ ] First ETEDA cycle completes successfully
- [ ] All 5 stages (Extract/Transform/Evaluate/Decide/Act) logged
- [ ] No unhandled exceptions in logs
- [ ] Cycle time is within expected range
- [ ] Safety system is operational (can trigger WARNING/FAIL/LOCKDOWN)
- [ ] Broker connection established (mock or real)
- [ ] Log output is parseable and structured
- [ ] All errors include sufficient context for root cause analysis

---

## Next Steps

1. **Immediate** (This session):
   - Run Phase 1 baseline assessment
   - Document findings in `zero-script-qa-{date}-cycle1.md`
   - Identify top 3 issues blocking Phase 2

2. **Short-term** (Next session):
   - Plan Phase 2 JSON logging upgrade
   - Implement Request ID propagation
   - Add ETEDA stage tracking to logs

3. **Medium-term** (Following sessions):
   - Implement real-time monitoring automation
   - Create issue detection rules
   - Set up automated QA reporting

4. **Long-term**:
   - Integrate with GitHub Actions for CI/CD QA
   - Add performance benchmarking
   - Create QA metrics dashboard

---

## Questions?

Refer to:
- QTS Architecture: `/home/tawbu/projects/QTS/docs/arch/`
- Logging System: `/home/tawbu/projects/QTS/src/monitoring/`
- ETEDA Pipeline: `/home/tawbu/projects/QTS/src/pipeline/`
- Safety Layer: `/home/tawbu/projects/QTS/src/safety/`
