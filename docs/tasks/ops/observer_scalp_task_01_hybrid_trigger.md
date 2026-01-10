# Task 01: Hybrid Trigger Implementation

## Purpose
Implement hybrid trigger model (A3) that combines default fixed loop execution with additional snapshot generation on tick events.

## Scope
**Included:**
- Hybrid trigger mechanism combining loop-based and tick-based triggers
- Fixed interval loop execution (existing behavior preserved)
- Additional snapshot generation on tick events
- Tick-triggered snapshots as supplemental to loop snapshots (not replacement)

**Excluded:**
- Decision logic modifications
- Strategy coupling
- Execution pipeline changes
- Snapshot suppression or filtering

## Architectural Constraints
From Observer_Scalp_Extension.md:
- Observer-Core structure must be preserved (Observer → PatternRecord → EventBus → Sink)
- Observer must remain a pure data producer (no decision logic)
- Existing data compatibility must be maintained (additive field changes only)
- Observer responsibility boundaries must not change

From Observer_Integration_Guide.md:
- Observer → Snapshot → Decision Pipeline flow must be maintained
- EventBus-based decoupled event delivery must be preserved
- execution_stub-based non-execution structure must remain

## Expected Changes
- Modify ObserverRunner to support hybrid trigger mode
- Add tick event listener that generates additional snapshots
- Ensure tick-triggered snapshots are supplemental to loop snapshots
- Maintain existing fixed loop as primary trigger mechanism
- Add configuration for hybrid mode enable/disable

## Non-Goals
- Tick-triggered snapshots must NOT replace loop snapshots
- No filtering or suppression of any snapshots
- No changes to Decision Pipeline
- No strategy-specific logic in Observer
- No execution awareness in trigger logic

## Validation Checklist
- [ ] Fixed loop execution continues to work as before
- [ ] Tick events generate additional snapshots without disrupting loop
- [ ] Both trigger types produce identical snapshot structures
- [ ] No decision logic is added to Observer
- [ ] All snapshots (loop and tick) are logged (full density B1)
- [ ] Observer responsibility boundaries remain unchanged
- [ ] Existing tests continue to pass
- [ ] New tests verify hybrid trigger behavior
- [ ] Configuration controls hybrid mode enable/disable
