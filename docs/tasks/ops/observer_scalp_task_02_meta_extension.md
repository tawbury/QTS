# Task 02: Extended Meta Fields Implementation

## Purpose
Add extended meta fields (E2) to ObservationSnapshot to support high-frequency scalping requirements while maintaining additive-only field changes.

## Scope
**Included:**
- Add iteration_id field to Meta section
- Add timestamp_ms field to Meta section  
- Add loop_interval_ms field to Meta section
- Add latency_ms field to Meta section
- Add tick_source field to Meta section
- Add buffer_depth field to Meta section
- Add flush_reason field to Meta section
- Ensure all new fields are additive (no existing field modifications)

**Excluded:**
- Removal or modification of existing meta fields
- Changes to snapshot core structure
- Decision logic based on new fields
- Strategy coupling through new fields

## Architectural Constraints
From Observer_Scalp_Extension.md:
- Must use additive field approach only (no existing field changes)
- Observer-Core structure must be preserved
- Existing data compatibility must be maintained
- Phase 2 JSONL data must remain usable in Phase 3~5

From Observer_Integration_Guide.md:
- Snapshot remains the minimum observation unit
- Observer → Snapshot → Decision Pipeline flow unchanged
- No decision logic in Observer

## Expected Changes
- Extend Meta dataclass in snapshot.py with new fields
- Update snapshot creation logic to populate new fields
- Add field population for both loop and tick-triggered snapshots
- Ensure backward compatibility with existing snapshot consumers
- Add validation for new field formats and ranges

## Non-Goals
- No interpretation or decision logic based on new fields
- No filtering based on new field values
- No changes to existing field definitions
- No strategy-specific metadata

## Validation Checklist
- [ ] All new meta fields are added without modifying existing ones
- [ ] iteration_id increments correctly for each snapshot
- [ ] timestamp_ms provides millisecond precision
- [ ] loop_interval_ms reflects actual loop timing
- [ ] latency_ms measures collection delay accurately
- [ ] tick_source identifies data source correctly
- [ ] buffer_depth indicates queue state
- [ ] flush_reason captures flush trigger
- [ ] Existing snapshot consumers remain functional
- [ ] Backward compatibility maintained for old data
- [ ] New fields populated for both loop and tick snapshots
- [ ] No decision logic added to Observer
