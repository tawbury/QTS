# Task 04: Time-based Log Rotation Implementation

## Purpose
Implement time-based log rotation (D2) to split logs by time windows, preventing single growing file issues while maintaining full density logging.

## Scope
**Included:**
- Time-based log file rotation at configured intervals
- Automatic file creation for new time windows
- Seamless transition between log files
- File naming convention based on time windows
- Single growing file prohibition enforcement

**Excluded:**
- Size-based log rotation
- Snapshot filtering or suppression during rotation
- Changes to log content or format
- Decision logic in rotation timing

## Architectural Constraints
From Observer_Scalp_Extension.md:
- Append-only logging policy must be maintained
- Observer-Core structure must be preserved
- Performance optimizations must not change Observer responsibilities

From Observer_Integration_Guide.md:
- EventBus-based delivery must be preserved
- No decision logic in Observer
- Snapshot → Decision Pipeline flow unchanged

## Expected Changes
- Modify JsonlFileSink to support time-based rotation
- Add configurable rotation interval parameter
- Implement automatic file creation at rotation boundaries
- Update file naming to include time window identifiers
- Ensure no data loss during file transitions
- Add rotation event logging

## Non-Goals
- No size-based rotation triggers
- No filtering of snapshots during rotation
- No changes to JSONL format or encoding
- No decision logic based on file state

## Validation Checklist
- [ ] Log files rotate at configured time intervals
- [ ] New log files are created automatically
- [ ] No snapshots are lost during rotation transitions
- [ ] File naming convention reflects time windows clearly
- [ ] Single growing file is properly prevented
- [ ] Append-only policy is maintained across files
- [ ] Existing log reading capabilities remain functional
- [ ] Configuration controls rotation interval
- [ ] Rotation events are logged appropriately
- [ ] Memory usage does not increase due to rotation
- [ ] Concurrent access to rotating files is handled correctly
- [ ] Full density logging (B1) is preserved
