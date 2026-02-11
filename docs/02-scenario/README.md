# QTS QA & Scenario Testing Documentation

This folder contains QA methodology, test scenarios, and monitoring guidelines for QTS.

## Documents

### Zero Script QA Framework

**[zero-script-qa-setup.md](zero-script-qa-setup.md)**
- Complete framework overview
- 4-phase roadmap (Assessment → Infrastructure → Monitoring → Reporting)
- Current state assessment
- Docker setup details
- Testing scenarios
- Monitoring checklist

**[zero-script-qa-quickstart.md](zero-script-qa-quickstart.md)**
- 5-minute quick start guide
- How to start testing immediately
- What to look for (green/red signals)
- Common issues and fixes
- Emergency references

**[zero-script-qa-automation-rules.md](zero-script-qa-automation-rules.md)**
- Detailed automation rules for Claude Code
- 5 rule categories (Error, Performance, Safety, Broker, Data)
- 14 specific rules with examples
- Issue report templates
- False positive prevention

**[log-analysis-toolkit.md](log-analysis-toolkit.md)**
- Understanding QTS log format
- ETEDA stage log patterns
- Common error patterns
- Manual analysis techniques
- Performance analysis
- Tools and commands reference
- Issue categorization

### Test Results

Test results from QA monitoring sessions are documented here:
- `zero-script-qa-{YYYYMMDD}-cycle{N}.md` - Per-cycle results
- `zero-script-qa-issues-{YYYYMMDD}.md` - Aggregated issues found

## Quick Start

To run your first QA monitoring session:

```bash
cd /home/tawbu/projects/QTS

# 1. Build and start
docker-compose -f docker/docker-compose.local.yml up --build

# 2. In another terminal, monitor logs
docker-compose logs -f qts-test

# 3. Let it run for 50 iterations (~1 min)

# 4. Document your findings
cp zero-script-qa-quickstart.md your-session-notes.md
# Edit with your observations

# 5. Stop
docker-compose down
```

See [zero-script-qa-quickstart.md](zero-script-qa-quickstart.md) for details.

## Understanding the Framework

### What is Zero Script QA?

Zero Script QA verifies system behavior through:
1. **Structured logging** - All events logged with context
2. **Real-time monitoring** - Claude Code analyzes logs live
3. **Manual flows** - User tests actual system behaviors
4. **Automatic detection** - AI finds patterns and issues
5. **Quick documentation** - Issues captured immediately

**Unlike traditional QA**:
- No test scripts to maintain
- No manual test case execution
- No post-test analysis delays
- Issues documented as discovered
- Root causes identified immediately

### The 4 Phases

| Phase | Status | Goal | Timeline |
|-------|--------|------|----------|
| **1: Assessment** | Current | Verify system startup, establish baseline, identify issues | This session |
| **2: Infrastructure** | Planned | Add JSON logging, Request ID propagation | Next session |
| **3: Real-time Monitoring** | Planned | Automate issue detection, live alert system | Following sessions |
| **4: Reporting** | Planned | QA metrics dashboard, trend analysis | Later sessions |

## Current Project State

### Working
- Docker Compose setup (local, test, e2e)
- Text-based logging system
- ETEDA pipeline (Extract → Transform → Evaluate → Decide → Act)
- Mock broker support
- 4 engines (Strategy, Risk, Portfolio, Performance)

### Needs Enhancement
- JSON log format (for machine parsing)
- Request ID propagation (for flow tracing)
- Performance metrics (timing per stage)
- Error categorization (structured error details)
- Recovery mechanism tracking (how system handles failures)

## Key Files

### System Configuration
- `config/default.yaml` - Default settings
- `config/.env` - Environment variables
- `docker/docker-compose.*.yml` - Docker configurations

### Source Code
- `src/monitoring/central_logger.py` - Logging system (to enhance)
- `src/runtime/main.py` - Entrypoint (add Request ID)
- `src/pipeline/loop/eteda_loop.py` - ETEDA runner
- `src/safety/` - Safety layer (monitor state changes)

### Documentation
- `docs/arch/` - Architecture documentation (13 documents)
- `docs/arch/03_ETEDA_Pipeline_Architecture.md` - ETEDA details
- `docs/arch/07_Fail_Safe_Safety_Architecture.md` - Safety details

## Monitoring Session Workflow

### Before Session
```bash
# 1. Review the quick start guide
cat zero-script-qa-quickstart.md

# 2. Plan your focus
# - System startup and stability?
# - ETEDA cycle timing?
# - Error handling?
# - Safety system?

# 3. Prepare logging file
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="/tmp/qts-qa-$TIMESTAMP.txt"
```

### During Session
```bash
# 1. Start monitoring
docker-compose logs -f qts-test | tee $LOG_FILE

# 2. Observe for 5-10 minutes (50+ cycles)

# 3. Note anything unusual:
# - Errors (timestamps)
# - Slow stages (which ones, how slow)
# - Unexpected behavior

# 4. Stop when done
# Ctrl+C to stop monitoring
```

### After Session
```bash
# 1. Review log file
# - Count errors: grep ERROR $LOG_FILE | wc -l
# - Find slowest stage: grep Duration $LOG_FILE | sort

# 2. Create result document
# - Copy template from zero-script-qa-quickstart.md
# - Fill in your observations
# - Save as zero-script-qa-{date}-cycle{N}.md

# 3. Document any issues found
# - Use templates from zero-script-qa-automation-rules.md
# - Create one issue file per major finding
# - Include error details and suggestions

# 4. Commit results
git add docs/02-scenario/zero-script-qa-*.md
git commit -m "QA: Test run {date} - findings documented"
```

## Common Analysis Tasks

### Find All Errors
```bash
docker-compose logs qts-test 2>&1 | grep ERROR
```

### Performance Analysis
```bash
# Extract timing data
docker-compose logs qts-test 2>&1 | grep -i "duration\|time"

# Average extract time
docker-compose logs qts-test 2>&1 | grep Extract | grep Duration | \
  awk '{print $NF}' | sed 's/ms//' | \
  awk '{sum+=$1; count++} END {print "Avg: " sum/count "ms"}'
```

### Track Progress
```bash
# How many cycles completed?
docker-compose logs qts-test 2>&1 | grep Iteration | tail -1

# Are errors increasing or stable?
docker-compose logs qts-test 2>&1 | grep ERROR | wc -l
```

See [log-analysis-toolkit.md](log-analysis-toolkit.md) for more techniques.

## Issue Severity Levels

| Severity | Meaning | Example | Action |
|----------|---------|---------|--------|
| **CRITICAL** | System cannot continue | Unhandled exception | Stop & investigate |
| **WARNING** | System continues but degraded | Slow performance, graceful error | Document & continue |
| **INFO** | Normal operation with notes | Expected failure handled | Monitor patterns |

## Success Metrics

After Phase 1 (Assessment):
- [ ] System starts without errors
- [ ] Completes 50+ ETEDA cycles
- [ ] All 5 stages execute per cycle
- [ ] Average cycle time < 1000ms
- [ ] Error recovery working
- [ ] Safety system operational

## Next Steps

1. **Run Phase 1 assessment** (today)
   - Use [zero-script-qa-quickstart.md](zero-script-qa-quickstart.md)
   - Document baseline performance
   - Identify top 3 blocking issues

2. **Plan Phase 2** (next session)
   - Review Phase 2 in [zero-script-qa-setup.md](zero-script-qa-setup.md)
   - Design JSON logging enhancement
   - Plan Request ID propagation

3. **Enhance logging** (following sessions)
   - Modify `src/monitoring/central_logger.py`
   - Update `src/runtime/main.py`
   - Add ETEDA stage tracking

4. **Enable automation** (later)
   - Implement detection rules from [zero-script-qa-automation-rules.md](zero-script-qa-automation-rules.md)
   - Set up live monitoring in Claude Code
   - Create automated issue reports

## References

### Internal Documentation
- `CLAUDE.md` - Project context and conventions
- `docs/arch/00_Main_Architecture.md` - System overview
- `docs/arch/03_ETEDA_Pipeline_Architecture.md` - ETEDA details
- `README.md` - Project getting started

### External Resources
- Zero Script QA skill: `/home/tawbu/projects/QTS/.claude/skills/zero-script-qa/`
- Agent memory: `/home/tawbu/projects/QTS/.claude/agent-memory/bkit-qa-monitor/`

## Questions?

Review the appropriate guide:
- **Getting started?** → [zero-script-qa-quickstart.md](zero-script-qa-quickstart.md)
- **Understanding framework?** → [zero-script-qa-setup.md](zero-script-qa-setup.md)
- **Analyzing logs?** → [log-analysis-toolkit.md](log-analysis-toolkit.md)
- **Setting up automation?** → [zero-script-qa-automation-rules.md](zero-script-qa-automation-rules.md)

---

**Last Updated**: 2026-02-11
**Framework Version**: 1.0 (Phase 1)
**Maintainer**: Claude Code (Zero Script QA)
