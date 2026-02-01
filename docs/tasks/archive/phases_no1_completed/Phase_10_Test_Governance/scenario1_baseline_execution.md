# Task 10 - Scenario 1: Baseline Operation Validation
# Duration: 5 minutes, Load: 1 snapshot/second, Mode: Standalone

## Step-by-Step Execution Commands

### 1. Environment Setup
```bash
# Set standalone mode
export QTS_OBSERVER_STANDALONE=1

# Create working directory
mkdir -p /tmp/observer_scenario1
cd /tmp/observer_scenario1

# Create baseline configuration
cat > baseline_config.json << 'EOF'
{
  "hybrid_trigger": {
    "enabled": false
  },
  "buffer": {
    "flush_interval_ms": 1000.0,
    "max_buffer_size": 10000,
    "enable_buffering": true
  },
  "rotation": {
    "enabled": false
  },
  "performance": {
    "enabled": true,
    "metrics_history_size": 1000
  }
}
EOF

# Create system monitoring script
cat > monitor_system.sh << 'EOF'
#!/bin/bash
while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S'),CPU,$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1),Memory,$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}'),Disk,$(df -h . | awk 'NR==2{print $5}' | cut -d'%' -f1)"
    sleep 5
done
EOF

chmod +x monitor_system.sh

# Create snapshot generator (1 snapshot/second)
cat > generate_baseline_snapshots.py << 'EOF'
#!/usr/bin/env python3
import json
import time
import sys
from datetime import datetime

from shared.timezone_utils import now_kst

def generate_snapshot(run_id, price=100.0):
    return {
        "meta": {
            "run_id": run_id,
            "timestamp": now_kst().isoformat(),
            "source": "baseline_test"
        },
        "market_data": {
            "symbol": "TEST",
            "price": price,
            "volume": 1000,
            "timestamp": now_kst().isoformat()
        },
        "system_state": {
            "status": "running",
            "memory_usage": 50.0
        }
    }

def main():
    snapshot_count = 0
    start_time = time.time()
    duration = 300  # 5 minutes
    
    while time.time() - start_time < duration:
        snapshot = generate_snapshot(f"baseline_{snapshot_count}")
        print(json.dumps(snapshot))
        snapshot_count += 1
        time.sleep(1.0)  # 1 snapshot per second
    
    print(f"Generated {snapshot_count} snapshots", file=sys.stderr)

if __name__ == "__main__":
    main()
EOF

chmod +x generate_baseline_snapshots.py
```

### 2. Start Monitoring
```bash
# Start system monitoring in background
./monitor_system.sh > system_metrics.csv &
MONITOR_PID=$!
echo "System monitoring started (PID: $MONITOR_PID)"

# Create Observer log directory
mkdir -p logs
```

### 3. Start Observer with Baseline Configuration
```bash
# Start Observer (assuming Observer is deployed to /opt/qts_observer)
cd /opt/qts_observer

# Start Observer with baseline configuration
python observer.py > /tmp/observer_scenario1/logs/observer_baseline.log 2>&1 &
OBSERVER_PID=$!
echo "Observer started (PID: $OBSERVER_PID)"

# Wait for Observer to initialize
sleep 10

# Verify Observer is running
if ps -p $OBSERVER_PID > /dev/null; then
    echo "Observer is running successfully"
else
    echo "Observer failed to start"
    exit 1
fi
```

### 4. Start Load Generation
```bash
# Start snapshot generation
cd /tmp/observer_scenario1
./generate_baseline_snapshots.py | python observer.py > logs/baseline_processing.log 2>&1 &
LOAD_PID=$!
echo "Load generation started (PID: $LOAD_PID)"

# Record start time
echo "Scenario 1 started at: $(date)"
START_TIME=$(date +%s)
```

### 5. Monitor During 5-Minute Run
```bash
# Create real-time monitoring script
cat > monitor_scenario1.sh << 'EOF'
#!/bin/bash
echo "=== Scenario 1 Monitoring ==="
echo "Time,Observer_PID,CPU%,Memory%,Disk%,Buffer_Depth,Processing_Latency_ms"

for i in {1..60}; do  # Check every 5 seconds for 5 minutes
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # System metrics
    cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    memory=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
    disk=$(df -h /tmp | awk 'NR==2{print $5}' | cut -d'%' -f1)
    
    # Observer metrics (from logs if available)
    buffer_depth="N/A"
    latency="N/A"
    
    echo "$timestamp,$OBSERVER_PID,$cpu,$memory,$disk,$buffer_depth,$latency"
    sleep 5
done
EOF

chmod +x monitor_scenario1.sh

# Run monitoring
./monitor_scenario1.sh > scenario1_monitoring.csv &
MONITOR_SCENARIO_PID=$!
```

### 6. Wait for Completion
```bash
# Wait for 5 minutes
echo "Running Scenario 1 for 5 minutes..."
sleep 300

# Stop all processes
echo "Stopping processes..."
kill $LOAD_PID 2>/dev/null
kill $MONITOR_SCENARIO_PID 2>/dev/null
kill $MONITOR_PID 2>/dev/null

# Gracefully stop Observer
kill $OBSERVER_PID 2>/dev/null
sleep 5

# Force stop if needed
kill -9 $OBSERVER_PID 2>/dev/null

echo "Scenario 1 completed at: $(date)"
```

## Observation Checklist During 5-Minute Run

### Every 30 Seconds (Check these items):
- [ ] Observer process is still running (`ps -p $OBSERVER_PID`)
- [ ] CPU usage < 50%
- [ ] Memory usage < 70%
- [ ] Disk usage < 80%
- [ ] No error messages in observer log
- [ ] Snapshots being processed (check log activity)
- [ ] Buffer operations occurring (flush messages in log)

### Every Minute (Record these metrics):
- [ ] CPU utilization percentage
- [ ] Memory usage percentage
- [ ] Disk space usage
- [ ] Number of snapshots processed (from log count)
- [ ] Buffer depth (if visible in logs)
- [ ] Processing latency (if visible in logs)

### At 2.5 Minutes (Mid-point check):
- [ ] System stability confirmed
- [ ] No performance degradation
- [ ] Log file size reasonable (< 10MB)
- [ ] No memory leaks (memory usage stable)

### At 5 Minutes (Final check):
- [ ] All snapshots processed successfully
- [ ] Observer shuts down gracefully
- [ ] All data flushed to disk
- [ ] No data corruption or loss

## Normal Operation Indicators

### System Metrics (NORMAL Range):
- **CPU Usage**: < 50%
- **Memory Usage**: < 70%
- **Disk Usage**: < 80%
- **Network I/O**: Minimal (baseline only)

### Application Metrics (NORMAL Range):
- **Processing Latency**: < 100ms
- **Buffer Depth**: < 100 records
- **Flush Interval**: ~1000ms (as configured)
- **Error Rate**: 0 errors/minute
- **Snapshot Processing**: ~60 snapshots/minute

### Log Messages (NORMAL Indicators):
- "Observer started successfully"
- "PatternRecord dispatched" messages
- "Flush completed" messages
- No ERROR or CRITICAL level messages
- Performance metrics being recorded

## Early Warning Signals

### System Level Warnings:
- **CPU Usage**: 50-70% (monitor closely)
- **Memory Usage**: 70-85% (approaching limit)
- **Disk Usage**: 80-90% (running out of space)
- **Process Status**: Observer process using high CPU

### Application Level Warnings:
- **Processing Latency**: 100-200ms (degrading performance)
- **Buffer Depth**: 100-500 records (backlog building)
- **Error Messages**: Any ERROR level messages
- **Missed Flushes**: Flush intervals > 2000ms

### Log Pattern Warnings:
- "Snapshot validation failed" messages
- "Snapshot guard blocked" messages
- "Buffer size exceeded" warnings
- Performance degradation messages

## Pass/Fail Criteria

### PASS Criteria (All must be met):
1. **System Stability**: Observer runs for full 5 minutes without crashing
2. **Resource Usage**: CPU < 50%, Memory < 70%, Disk < 80% throughout
3. **Processing Performance**: All ~300 snapshots processed successfully
4. **Latency**: Average processing latency < 100ms
5. **Error Rate**: Zero error messages in logs
6. **Graceful Shutdown**: Observer stops cleanly with data flushed
7. **Data Integrity**: All snapshots written to output file correctly

### FAIL Criteria (Any one triggers failure):
1. **Process Failure**: Observer crashes or hangs during test
2. **Resource Exhaustion**: CPU > 80% or Memory > 90% sustained
3. **Processing Failure**: > 5% of snapshots fail to process
4. **High Latency**: Average processing latency > 200ms
5. **Error Rate**: > 1 error per minute in logs
6. **Data Loss**: Snapshots not written to output or corrupted
7. **Shutdown Failure**: Observer does not stop gracefully

### Validation Commands (Post-Test):
```bash
# Check Observer exit status
echo "Observer exit code: $?"

# Count processed snapshots
echo "Snapshots processed: $(grep -c "PatternRecord dispatched" /tmp/observer_scenario1/logs/observer_baseline.log)"

# Check for errors
echo "Error count: $(grep -c "ERROR\|CRITICAL" /tmp/observer_scenario1/logs/observer_baseline.log)"

# Check output file size
echo "Output file size: $(wc -l < /opt/qts_observer/config/observer/observer.jsonl) lines"

# Verify system metrics
echo "Peak CPU: $(awk -F',' 'NR>1 && $3>max {max=$3} END {print max}' system_metrics.csv)"
echo "Peak Memory: $(awk -F',' 'NR>1 && $5>max {max=$5} END {print max}' system_metrics.csv)"
```

## Expected Results for Successful Scenario 1

- **Total Snapshots**: ~300 (60 per minute × 5 minutes)
- **Average CPU**: < 30%
- **Average Memory**: < 50%
- **Processing Latency**: < 50ms average
- **Buffer Depth**: < 50 records
- **Error Count**: 0
- **Output Lines**: ~300 lines in observer.jsonl
- **Log File Size**: < 5MB
