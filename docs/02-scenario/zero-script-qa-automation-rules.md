# Zero Script QA - Automation Rules for Claude Code

**Purpose**: Rules that Claude Code follows when monitoring QTS logs
**Status**: Phase 1 (Manual setup), Phase 2+ (Automated)
**Last Updated**: 2026-02-11

---

## Overview

These rules define how Claude Code automatically:
1. Detects issues in real-time log streams
2. Extracts relevant context
3. Documents findings
4. Suggests fixes

Rules are applied during QA monitoring sessions when user runs QTS tests.

---

## Rule Categories

### Category A: Error Detection
When Claude Code sees an ERROR in logs.

### Category B: Performance Warning
When a stage exceeds performance thresholds.

### Category C: Safety State Change
When the safety layer changes state.

### Category D: Broker Integration
When broker operations succeed/fail.

### Category E: Data Anomaly
When data looks suspicious but doesn't error.

---

## Category A: Error Detection Rules

### Rule A1: Unhandled Exception
**Trigger**: `[ERROR]` + `Traceback` OR `Exception` in logs

**Action**:
1. Extract error type (e.g., `ZeroDivisionError`, `TypeError`)
2. Extract file path and line number
3. Extract error message
4. Find code context (read file at that line)
5. Collect preceding 10 log lines (to understand what led to error)
6. Create issue document with:
   - **Title**: `[file.py:line] Error type: error_message`
   - **Severity**: CRITICAL (unhandled exception)
   - **Category**: Bug
   - **Reproduction**: "Run test with current config, error on cycle N"
   - **Code snippet**: Show file:line and surrounding 5 lines
   - **Fix suggestion**: Add try/catch or validation
   - **Root cause**: Why wasn't this error anticipated?

**Example**:
```
Trigger in log:
[ERROR] Traceback (most recent call last):
  File "src/strategy/signals.py", line 123, in calculate
    return 100 / (momentum - threshold)
ZeroDivisionError: division by zero

Generated issue:
ISSUE-A1-001: [signals.py:123] Prevent division by zero in signal calculation

Root Cause: Missing validation that (momentum - threshold) != 0
Recommended Fix: Add guard: if (momentum - threshold) == 0: return 0
```

### Rule A2: Stage Failure (Expected Failure Path)
**Trigger**: `[ERROR]` + stage name (Extract/Transform/Evaluate/Decide/Act)

**Action**:
1. Identify which ETEDA stage
2. Extract error message (e.g., "Schema validation failed")
3. Determine if error is expected (see expected failures below)
4. If expected: Document as expected failure, continue monitoring
5. If unexpected: Document as issue

**Expected Failures** (okay to skip cycle, retry next):
- Extract: Missing observer file, timeout reading data
- Transform: NULL in optional field, missing optional data
- Evaluate: Risk constraint exceeded, portfolio limit reached
- Decide: Conflicting signals (tie-break applied)
- Act: Broker timeout, order rejected, insufficient funds

**Unexpected Failures** (bugs):
- Extract: Unhandled I/O error, invalid file format
- Transform: Schema validation with no clear error message, type error
- Evaluate: Unhandled calculation error, invalid signal format
- Decide: Logic error in decision, invalid state
- Act: Unhandled broker error, order validation with bad error

**Example - Expected**:
```
Log: [WARNING] Transform: Portfolio margin 150% (required: 200%)
→ Document as "Risk check triggered" (expected behavior)
→ No issue, continue monitoring
```

**Example - Unexpected**:
```
Log: [ERROR] Transform: Schema validation failed
→ Check if error message explains what failed
→ If vague (no detail), create issue: "Add error detail to schema validation"
```

### Rule A3: Broker Error
**Trigger**: `[ERROR]` + ("broker" OR "order" OR "connection")

**Action**:
1. Extract broker name (e.g., "KIS", "Kiwoom", "Mock")
2. Extract error type:
   - Connection error (timeout, refused, unreachable)
   - Order error (rejected, validation failed, insufficient funds)
   - API error (invalid response, HTTP error)
3. Check if retry logic applied (look for "Retry" or "attempt" in logs)
4. Document issue with:
   - **Title**: `[broker_name] error_type`
   - **Severity**: CRITICAL (affects trading)
   - **Category**: Integration
   - **Error details**: Exact broker error message
   - **Retry behavior**: Did system attempt to recover?
   - **Recommendation**:
     - If connection: Check network/broker status
     - If order: Check order validation logic
     - If API: Check broker API documentation

**Example**:
```
Log:
[WARNING] Broker KIS: Connection timeout (5000ms)
[INFO] Retrying... (attempt 2/3)
[WARNING] Broker KIS: Order rejected (ERR-200: Insufficient funds)

Generated issue:
ISSUE-A3-001: [KIS Broker] Insufficient funds error

Root Cause: Portfolio cash position calculation incorrect
Recommended Fix: Verify position calculation before order submission
Prevention: Add cash balance check before creating order
```

---

## Category B: Performance Warning Rules

### Rule B1: Stage Exceeds Threshold
**Trigger**: Stage duration > threshold for that stage

**Thresholds**:
```
Extract:   > 100ms    (read I/O intensive)
Transform: > 50ms     (calculation intensive)
Evaluate:  > 200ms    (engine computation intensive)
Decide:    > 100ms    (logic intensive)
Act:       > 500ms    (network dependent)
```

**Action**:
1. Extract stage name and duration
2. Calculate how much over threshold (e.g., "150ms vs 100ms = 50% over")
3. Check if this is consistent (sample 5 recent cycles)
4. If consistent: Create performance issue
5. If intermittent: Create warning note
6. Document with:
   - **Title**: `[stage] Performance: Xms (threshold: Yms)`
   - **Severity**: WARNING (system still functional)
   - **Category**: Performance
   - **Data**:
     - Average duration over last N cycles
     - Worst duration
     - Baseline (first successful cycle)
   - **Suspected cause**:
     - Extract slow: File I/O, data volume
     - Transform slow: Validation logic, calculation
     - Evaluate slow: Engine logic, database query
     - Decide slow: Decision algorithm complexity
     - Act slow: Network latency, broker API
   - **Recommendation**:
     - Profile the stage
     - Look for unnecessary operations
     - Consider caching or parallelization

**Example**:
```
Log (multiple cycles):
Cycle 1: Extract 95ms
Cycle 2: Extract 150ms
Cycle 3: Extract 140ms
Cycle 4: Extract 155ms
Cycle 5: Extract 148ms

Generated issue:
ISSUE-B1-001: Extract stage consistently slow (avg 148ms vs threshold 100ms)

Root Cause: Suspect large file size or slow I/O
Recommendation:
1. Check observer file size
2. Profile file read performance
3. Consider splitting data or caching
```

### Rule B2: Total Cycle Time Exceeds Budget
**Trigger**: Sum of all stages > 1000ms

**Action**:
1. Extract cycle duration
2. Identify which stage is worst offender
3. Create warning if consistent
4. Document timeline showing all stage durations
5. Prioritize fixing slowest stage

**Example**:
```
Cycle 15: Total 1200ms
  Extract: 120ms
  Transform: 50ms
  Evaluate: 450ms  ← Slowest
  Decide: 80ms
  Act: 500ms

Recommendation: Investigate Evaluate stage
```

---

## Category C: Safety State Change Rules

### Rule C1: State Transition
**Trigger**: Log contains state change (NORMAL → WARNING → FAIL → LOCKDOWN)

**Action**:
1. Extract old state and new state
2. Extract reason/trigger for state change
3. Log timestamp and cycle number
4. Check what follows state change:
   - After WARNING: System should skip/hold
   - After FAIL: System should stop taking orders
   - After LOCKDOWN: System should stop entirely
5. Document state machine progress:
   - **Title**: `Safety state: NORMAL → WARNING` (or other transition)
   - **Severity**: INFO/WARNING (depends on state)
   - **Trigger**: What caused transition?
   - **Behavior**: What did system do after?
   - **Recovery**: How did system recover (if at all)?

**Example**:
```
Log:
[INFO] Safety state: NORMAL → WARNING
[INFO] Trigger: Portfolio margin 150% (threshold: 200%)
[INFO] Decision suppressed: No orders will be placed
[INFO] Monitoring margin recovery...
Cycle 20:
[INFO] Safety state: WARNING → NORMAL
[INFO] Reason: Portfolio margin recovered to 220%
[INFO] Order placement resumed

Generated note:
Safety system test successful:
- Triggered properly on margin violation
- Suppressed orders as expected
- Recovered when condition cleared
Status: PASS
```

### Rule C2: Kill Switch Activation
**Trigger**: Log contains "LOCKDOWN" or "kill switch" OR "trading disabled"

**Action**:
1. Extract activation reason
2. Extract timestamp and cycle
3. **CRITICAL**: This is a safety feature - activation is good!
4. Document as successful safety trigger:
   - **Event**: Kill switch activated
   - **When**: Timestamp, cycle number
   - **Reason**: What triggered it?
   - **System status**: Are logs clean after (no more orders)?
5. Verify:
   - No orders placed after activation
   - System remains operational (for monitoring/recovery)
   - Error recovery not triggered (kill switch is intentional)

**Example**:
```
Log:
[WARNING] Portfolio constraint severe: Margin 80% (minimum 100%)
[ERROR] Cannot place order during FAIL state
[ERROR] Kill switch activated: Trading disabled
[INFO] System locked down. Manual intervention required.

Generated documentation:
Kill Switch Test Passed:
✓ Activated on critical constraint violation
✓ Prevented order placement
✓ System remains operational for monitoring
✓ Clear message for operator

Operator action needed: Check portfolio and manually approve reset
```

---

## Category D: Broker Integration Rules

### Rule D1: Order Lifecycle Tracking
**Trigger**: Log contains order-related events

**Action**:
1. Extract Request ID (or assign one if missing)
2. Track order through states: SUBMITTED → PENDING → FILLED/REJECTED
3. Record timing at each state
4. Verify all state transitions logged
5. Document as successful operation or identify gaps

**Complete Order Lifecycle**:
```
[INFO] Act stage starting
[INFO] Creating order: BUY 100 @ limit price
[INFO] Order validation: PASS
[INFO] Submitting to broker...
[INFO] Order submitted: ID=12345, status=PENDING
[INFO] Awaiting broker confirmation...
[INFO] Order filled: ID=12345, price=100.50
[INFO] Ledger entry created
[INFO] Act stage completed: 450ms
```

**Incomplete Order Lifecycle** (issue):
```
[INFO] Act stage starting
[INFO] Creating order: BUY 100
[INFO] Submitting to broker...
[ERROR] Order submission failed (no detail)
→ Issue: Missing error detail, hard to debug
```

### Rule D2: Order Rejection Analysis
**Trigger**: Log contains "rejected" or "validation failed" for order

**Action**:
1. Extract rejection reason (if available)
2. Extract order details (symbol, quantity, price)
3. Determine if rejection is expected or unexpected
4. Document with:
   - **Title**: `Order rejected: reason`
   - **Order details**: What was being traded?
   - **Rejection reason**: Why did broker reject?
   - **Expected?**: Should this order have been rejected?
   - **Prevention**: How to prevent in future?

**Expected Rejections**:
- Insufficient funds (portfolio check failed)
- Invalid symbol (typo in symbol)
- Limit price invalid (price outside valid range)

**Unexpected Rejections**:
- "Order format invalid" (code generated bad order)
- "Permission denied" (auth token expired)
- Vague error message (can't debug)

---

## Category E: Data Anomaly Rules

### Rule E1: Missing or NULL Data
**Trigger**: Log contains "null", "missing", "empty" for required field

**Action**:
1. Identify which field is missing
2. Identify where missing (which ETEDA stage discovered it)
3. Determine if gracefully handled
4. Document as:
   - **Data issue**: Missing X field
   - **Impact**: Does it block progress?
   - **Handled**: Yes/No (is there fallback?)
   - **Prevention**: How to ensure data completeness?

**Example**:
```
Log:
[WARNING] Transform: Missing dividend data for symbol XYZ
[INFO] Using cached dividend data from yesterday
[INFO] Transform completed

Analysis: Handled gracefully
✓ System detected missing data
✓ Fallback strategy applied
✓ Warning logged
Status: PASS (expected behavior)
```

### Rule E2: Data Inconsistency
**Trigger**: Log contains conflicting data or validation warnings

**Action**:
1. Extract conflicting values
2. Identify source and cause
3. Check if system reconciled it
4. Document as data quality issue

**Example**:
```
Log:
[WARNING] Position count mismatch: expected=50, actual=49
[INFO] Investigating... Found stale cache entry
[INFO] Cache invalidated, position recalculated
[INFO] Reconciliation complete

Analysis: Issue detected and fixed automatically
Status: PASS (but log cache invalidation issue for monitoring)
```

---

## Rule Application Priority

### High Priority (Check First)
1. Unhandled exceptions (Category A1)
2. Kill switch activation (Category C2)
3. Broker connection errors (Category A3)
4. Order rejections (Category D2)

### Medium Priority (Check Next)
1. Unexpected stage failures (Category A2)
2. Performance warnings (Category B)
3. State transitions (Category C1)

### Low Priority (Monitor)
1. Expected failures (handled gracefully)
2. Data anomalies (handled)
3. Consistent behavior (baseline)

---

## False Positive Prevention

### Expected and Harmless Events (Don't Flag)

**Expected Failures**:
```
[WARNING] Extract: Observer file not found, using mock data
→ Normal in local-only mode

[WARNING] Risk: Portfolio margin low, skipping order
→ Safety system working correctly

[WARNING] Broker: Timeout on first attempt, retrying
→ Transient network issue being handled
```

**Transient Issues** (Don't flag if recovered):
```
[WARNING] Connection lost, reconnecting...
[INFO] Connection restored
→ System recovered automatically, all good
```

**Informational Messages** (Not issues):
```
[INFO] Cycle 1/50 started
[INFO] Order placed: BUY 100
[INFO] Position updated
→ These are normal operation logs
```

---

## Issue Report Templates

### For Unhandled Errors
```markdown
ISSUE-{ID}: {Error type} in {module}

**Trigger**: [Exact log message]
**When**: Cycle {N}, {timestamp}
**Where**: {file.py:line_number}

**Error Details**:
```
[Paste full error message from logs]
```

**Root Cause**: [Your analysis]

**Code**:
```
[Paste code from file at error location]
```

**Fix**: [Describe fix]
```

### For Performance Issues
```markdown
ISSUE-{ID}: {Stage} Performance - {duration}ms vs {threshold}ms

**Data**:
- Avg: {X}ms
- Worst: {Y}ms
- Threshold: {Z}ms
- Samples: {N} cycles

**Suspected Cause**: [Your analysis]

**Recommendation**:
1. [Investigation step 1]
2. [Investigation step 2]
3. [Fix suggestion]
```

### For Safety/Integration Issues
```markdown
ISSUE-{ID}: {Category} - {Title}

**What**: [What happened]
**When**: [Timestamp/cycle]
**Impact**: [Does it block trading?]
**Handled**: [Did system recover?]
**Expected**: [Should this happen?]

**Details**: [Full context from logs]

**Next Steps**:
- [ ] Verify reproducibility
- [ ] Implement fix
- [ ] Test recovery
```

---

## Claude Code Monitoring Session

When Claude Code is actively monitoring logs:

1. **Startup**: Greet user, confirm monitoring is active
2. **Every 30 seconds**: Sample logs, check for new issues
3. **On issue detection**: Document immediately (don't wait for end of test)
4. **On performance warning**: Suggest if user wants to continue or investigate
5. **On completion**: Summarize findings

---

## Questions for Users During Monitoring

Ask user to provide context:
```
When I detect: "Portfolio margin low"
I ask: "Is this expected given market conditions, or new issue?"

When I detect: "Slow stage"
I ask: "Was this stage fast in previous runs?"

When I detect: "Broker error"
I ask: "Is broker known to be down, or is this a system issue?"
```

---

## Success Indicators

Good QA monitoring finds:
- Reproducible bugs (unhandled exceptions)
- Performance regressions (stage got slower)
- Integration issues (broker failures)
- Data quality issues (missing fields)
- Safety system effectiveness (did it protect?)

Excellent QA monitoring also:
- Suggests root causes
- Proposes code locations to investigate
- Provides code samples
- Suggests test strategies to verify fixes
- Tracks patterns across multiple test cycles

---

## Continuous Improvement

After each QA session:
1. Review accuracy of rule application
2. Note false positives (rules that triggered incorrectly)
3. Note false negatives (real issues that weren't caught)
4. Update rules to improve accuracy
5. Add new rules for new issue types discovered

---

Happy monitoring!
