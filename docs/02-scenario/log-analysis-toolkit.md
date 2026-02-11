# Log Analysis Toolkit for QTS QA

**Purpose**: Reference guide for analyzing QTS logs manually and with Claude Code
**Applies to**: All QA monitoring sessions

---

## Understanding QTS Log Output

### Log Entry Format (Current)
```
2026-02-11 10:30:45,123 [INFO] runtime.eteda: Extract stage starting
```

### Components
| Part | Meaning | Example |
|------|---------|---------|
| Date/Time | When event occurred | 2026-02-11 10:30:45,123 |
| Level | Severity | [INFO], [WARNING], [ERROR], [DEBUG] |
| Logger | Which system/layer | runtime.eteda, runtime.engine, runtime.broker |
| Message | What happened | Extract stage starting |

### Future Format (Phase 2)
```json
{
  "timestamp": "2026-02-11T10:30:45.123Z",
  "level": "INFO",
  "service": "qts",
  "request_id": "req_abc12345",
  "stage": "Extract",
  "message": "Market data loaded",
  "data": {
    "symbols": 50,
    "duration_ms": 45
  }
}
```

---

## ETEDA Stage Log Patterns

### Extract Stage
Reads market data from observer or file.

**Success Indicators**:
```
Extract stage starting
Market data loaded
Asset count: N
Price data retrieved
Duration: Xms
Extract stage completed
```

**Failure Indicators**:
```
ERROR: Failed to open observer file
WARNING: Missing price data for symbol
ERROR: Timeout reading market data
ERROR: Invalid asset format
```

### Transform Stage
Calculates derived data and validates schema.

**Success Indicators**:
```
Transform stage starting
Schema validation passed
Position calculations completed
Risk metrics calculated
Duration: Xms
Transform stage completed
```

**Failure Indicators**:
```
ERROR: Schema validation failed
ERROR: NULL in required field
ERROR: Type mismatch in calculation
WARNING: Missing dividend data
ERROR: Division by zero in metric
```

### Evaluate Stage
Evaluates strategy signals and risk constraints.

**Success Indicators**:
```
Evaluate stage starting
Strategy evaluation: {signal}
Risk assessment: {status}
Portfolio check: {status}
Performance metrics updated
Duration: Xms
Evaluate stage completed
```

**Failure Indicators**:
```
ERROR: Strategy evaluation failed
ERROR: Risk constraint violated
WARNING: Portfolio margin insufficient
ERROR: Performance metric calculation error
ERROR: Conflicting signals detected
```

### Decide Stage
Makes trading decision based on evaluations.

**Success Indicators**:
```
Decide stage starting
Decision: BUY/SELL/HOLD
Quantity: N
Reason: {explanation}
Duration: Xms
Decide stage completed
```

**Failure Indicators**:
```
ERROR: Decision logic error
WARNING: Conflicting signals, skipping
ERROR: No valid decision
WARNING: Decision margin insufficient
ERROR: Portfolio locked
```

### Act Stage
Submits orders to broker.

**Success Indicators**:
```
Act stage starting
Order submission attempt
Order ID: {id}
Order status: PENDING/FILLED
Execution price: {price}
Duration: Xms
Act stage completed
```

**Failure Indicators**:
```
ERROR: Broker connection failed
ERROR: Order rejection: {reason}
WARNING: Broker timeout
ERROR: Order validation failed
ERROR: Insufficient funds
```

---

## Common Error Patterns

### Pattern 1: Extract Failure → Cycle Skip
```
[INFO] Extract stage starting
[ERROR] Failed to read observer data
[INFO] Cycle 1 skipped (extract failed)
[INFO] Cycle 2 starting...
```
**Analysis**: Expected behavior. System retries next cycle.
**Action**: If persistent, check observer integration.

### Pattern 2: Transform Validation Error
```
[INFO] Transform stage starting
[ERROR] Schema validation failed: 'price' is null
[INFO] Cycle 1 failed
```
**Analysis**: Bad data from extract stage.
**Action**: Fix data source or null handling.

### Pattern 3: Risk Constraint Violation
```
[INFO] Evaluate stage starting
[WARNING] Portfolio margin: 150% (threshold: 200%)
[INFO] Cycle 1 skipped (risk check failed)
```
**Analysis**: Safety system working as designed.
**Action**: Check risk settings or market conditions.

### Pattern 4: Broker Timeout
```
[INFO] Act stage starting
[WARNING] Broker timeout after 5000ms
[ERROR] Order submission failed
[INFO] Retrying... (attempt 2/3)
```
**Analysis**: Network/broker latency.
**Action**: Check broker connectivity or increase timeout.

### Pattern 5: Unhandled Exception
```
[ERROR] Traceback (most recent call last):
  File "src/strategy/engine.py", line 45, in evaluate
    signal = self.calculate_signal()
  File "src/strategy/signals.py", line 123, in calculate_signal
    return 100 / (self.momentum - self.threshold)
ZeroDivisionError: division by zero
[ERROR] Evaluate stage failed
```
**Analysis**: Bug in code - missing error handling.
**Action**: Add validation before division.

---

## Manual Analysis Techniques

### 1. Extract Error Logs
```bash
# All errors
docker-compose logs qts-test 2>&1 | grep ERROR

# Errors from specific stage
docker-compose logs qts-test 2>&1 | grep -E "Extract|ERROR" | head -20

# Errors with context (5 lines before/after)
docker-compose logs qts-test 2>&1 | grep -B5 -A5 ERROR
```

### 2. Extract Timing Data
```bash
# Find all stage completion messages with duration
docker-compose logs qts-test 2>&1 | grep -i "duration\|completed"

# Extract and sort by duration
docker-compose logs qts-test 2>&1 | grep -i "duration" | sort -t: -k3 -n

# Calculate average (bash)
docker-compose logs qts-test 2>&1 | grep "Extract" | grep "Duration" | \
  awk '{print $NF}' | sed 's/ms//' | \
  awk '{sum+=$1; count++} END {print "Avg: " sum/count "ms"}'
```

### 3. Track Iteration Progress
```bash
# Count completed cycles
docker-compose logs qts-test 2>&1 | grep "Iteration" | wc -l

# Show iteration status
docker-compose logs qts-test 2>&1 | grep "Iteration" | tail -10

# Find where iteration stopped
docker-compose logs qts-test 2>&1 | grep -A5 "Iteration.*started" | tail -30
```

### 4. Identify Failure Points
```bash
# Find first error
docker-compose logs qts-test 2>&1 | grep -m1 ERROR

# Count errors by type
docker-compose logs qts-test 2>&1 | grep ERROR | cut -d: -f2- | sort | uniq -c

# Find error patterns
docker-compose logs qts-test 2>&1 | grep ERROR | \
  awk -F: '{print $3}' | sort | uniq -c | sort -rn
```

### 5. Analyze Safety State
```bash
# All safety-related events
docker-compose logs qts-test 2>&1 | grep -i "safety\|state\|warning\|fail"

# State transitions
docker-compose logs qts-test 2>&1 | grep -i "state:" | head -20

# Guard rail triggers
docker-compose logs qts-test 2>&1 | grep -i "guard\|trigger\|threshold"
```

---

## Performance Analysis

### Baseline Metrics (Expected)
```
Extract:   < 100ms    (read files/observer data)
Transform: < 50ms     (schema validation, calculations)
Evaluate:  < 200ms    (engine computations)
Decide:    < 100ms    (decision logic)
Act:       < 500ms    (broker communication)
---
Total:     < 950ms per cycle
```

### Slow Performance Investigation
```bash
# Step 1: Identify slowest stage
docker-compose logs qts-test 2>&1 | grep -E "Extract|Transform|Evaluate|Decide|Act" | \
  grep "Duration" | sort -t: -k3 -rn | head -10

# Step 2: Sample logs around slow stage
# If Extract is slow:
docker-compose logs qts-test 2>&1 | grep -B3 -A3 "Extract.*Duration.*ms"

# Step 3: Check for errors/warnings in slow cycles
# Add context (20 lines before/after)
docker-compose logs qts-test 2>&1 | grep -B20 -A20 "Duration.*5000"

# Step 4: Check system resources during test
# (In separate terminal)
docker stats qts-test
```

### Bottleneck Identification
```
If Extract is slow:
  → Check observer file I/O
  → Check file system performance
  → Check data volume (too many symbols?)

If Transform is slow:
  → Check schema validation logic
  → Check calculation complexity
  → Look for N^2 operations

If Evaluate is slow:
  → Check engine logic (strategy/risk/portfolio)
  → Check signal calculation complexity
  → Look for database queries without cache

If Decide is slow:
  → Check decision logic
  → Check tie-breaking algorithm
  → Look for iterative searches

If Act is slow:
  → Check broker latency (network)
  → Check broker API response time
  → Check order validation logic
```

---

## Issue Categorization

### By Severity

**CRITICAL** - System cannot continue
```
[ERROR] Unhandled exception in main loop
[ERROR] Broker disconnected with no fallback
[ERROR] Safety lockdown triggered
```
→ Stop testing, investigate immediately

**WARNING** - System continues but degraded
```
[WARNING] Portfolio margin low
[WARNING] Broker timeout, retrying
[WARNING] Missing data for symbol X
```
→ Document and continue testing

**INFO** - Normal operation
```
[INFO] Cycle completed successfully
[INFO] Order placed: BUY 100 shares
```
→ Monitor patterns but no immediate action

### By Frequency

**Intermittent** (happens sometimes)
```
→ Likely network issue or race condition
→ Test multiple times to reproduce
→ Check logs for triggering condition
```

**Consistent** (happens every time)
```
→ Reproducible issue
→ Easier to debug
→ Include in issue report with exact steps
```

**Cascading** (one error triggers others)
```
[ERROR] Extract failed
[ERROR] Transform skipped (no data)
[ERROR] Evaluate failed (incomplete data)
[ERROR] No decision made
→ Fix root cause (extract), others should resolve
```

---

## Creating Issue Reports

### Minimal Issue Report
```
ISSUE: [One-line title]

Timestamp: 2026-02-11 10:30:45
Cycle: 15/50
Stage: Extract
Severity: WARNING

Error Message:
[Paste exact error from logs]

Quick Repro:
1. Run test with current config
2. Wait for cycle 15
3. Observe error

Next Steps:
[ ] Investigate root cause
[ ] Determine if reproducible
[ ] Implement fix
```

### Detailed Issue Report
```
ISSUE-001: [Title]

SUMMARY
-------
What: [description]
When: [timestamp, which cycle]
Where: [which ETEDA stage, which file]
Severity: [CRITICAL/WARNING/INFO]

REPRODUCTION
------------
Steps:
1. Start system with command: [exact command]
2. Run for N cycles: [number]
3. Observe: [what happens]

Expected: [what should happen]
Actual: [what actually happened]

ROOT CAUSE ANALYSIS
-------------------
Logs showing issue:
[Paste 5-10 relevant log lines with context]

Hypothesis: [your analysis of what went wrong]

Code location: [file:line_number]
```
[Paste relevant code snippet]
```

RECOMMENDED FIX
---------------
File: [path/to/file.py]
Change: [describe the fix]
Test plan: [how to verify fix works]

PREVENTION
----------
[What should be done to prevent this in future]
```

---

## Tools and Commands Cheatsheet

### Quick Diagnostics
```bash
# Is system running?
docker ps | grep qts

# Are there errors?
docker-compose logs qts-test 2>&1 | grep -c ERROR

# Performance summary
docker-compose logs qts-test 2>&1 | grep Duration | \
  awk '{sum+=$NF; count++} END {print count " iterations, avg " sum/count}'

# Get sample of last 50 log lines
docker-compose logs --tail 50 qts-test

# Save logs to file
docker-compose logs qts-test > /tmp/qts-$(date +%s).txt
```

### Advanced Filtering
```bash
# Show specific error type
docker-compose logs qts-test 2>&1 | grep "ERROR.*timeout"

# Show lines between timestamps
docker-compose logs qts-test 2>&1 | sed -n '/10:30:00/,/10:31:00/p'

# Count occurrences by stage
for stage in Extract Transform Evaluate Decide Act; do
  echo "$stage: $(docker-compose logs qts-test 2>&1 | grep -c $stage)"
done

# Create timeline of events
docker-compose logs qts-test 2>&1 | \
  grep -E "ERROR|WARNING|completed|Iteration" | \
  awk '{print $1, $2, $NF}' > /tmp/timeline.txt
```

### For Claude Code Analysis
Save logs in structured format for analysis:
```bash
# JSON lines format (if Phase 2 complete)
docker-compose logs qts-test 2>&1 | grep "^{" > /tmp/qts-logs.jsonl

# Or CSV format
docker-compose logs qts-test 2>&1 | \
  awk -F'[][]' '{print $1, $2, $3}' > /tmp/qts-logs.csv
```

---

## Reference: ETEDA Pipeline Flow

```
START
  ↓
[EXTRACT] - Read market data
  ↓ success ↓ error
  ↓         → SKIP & RETRY
  ↓
[TRANSFORM] - Validate & calculate
  ↓ success ↓ error
  ↓         → SKIP & RETRY
  ↓
[EVALUATE] - Check strategy & risk
  ↓ success ↓ constraint violation
  ↓         → SKIP & CONTINUE
  ↓
[DECIDE] - Make trading decision
  ↓ BUY/SELL ↓ HOLD
  ↓           → END CYCLE
  ↓
[ACT] - Submit order
  ↓ success ↓ error
  ↓         → RETRY
  ↓
[COMPLETE] - Log result
  ↓
NEXT CYCLE
```

---

## Further Reading

- **Architecture Details**: `docs/arch/03_ETEDA_Pipeline_Architecture.md`
- **Engine Layer**: `docs/arch/02_Engine_Core_Architecture.md`
- **Safety System**: `docs/arch/07_Fail_Safe_Safety_Architecture.md`
- **Logging System**: `src/monitoring/central_logger.py`
- **Runtime Entry**: `src/runtime/main.py`

---

Happy analyzing!
