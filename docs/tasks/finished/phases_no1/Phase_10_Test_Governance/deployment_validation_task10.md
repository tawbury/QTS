# Task 10: Deployment Validation & Stress Testing Execution Plan

## 1. Derived Sub-Task List

### 1.1 Environment Preparation
- Verify server environment meets requirements
- Deploy Observer Scalp Extension to server
- Configure monitoring and logging infrastructure
- Set up Azure credit usage monitoring

### 1.2 Baseline Validation
- Confirm Observer starts successfully with default configuration
- Validate basic snapshot processing functionality
- Verify performance metrics collection works
- Test configuration loading and validation

### 1.3 Load Testing Scenarios
- Light load test (baseline performance)
- Medium load test (sustained operation)
- Heavy load test (stress conditions)
- Extreme load test (failure boundaries)

### 1.4 Feature-Specific Testing
- Hybrid trigger mechanism validation
- Buffer and flush operations under load
- Log rotation during high-frequency operations
- Performance monitoring under stress

### 1.5 Resource Monitoring
- CPU utilization monitoring
- Memory usage tracking
- Disk I/O and storage monitoring
- Network bandwidth utilization

### 1.6 Azure Cost Observability
- Credit usage monitoring setup
- Cost metrics collection
- Resource consumption analysis
- Cost optimization validation

---

## 2. Stress Test Scenarios

### 2.1 Scenario 1: Baseline Operation (5 minutes)
**Purpose:** Establish baseline performance metrics
**Configuration:** Default settings, performance monitoring enabled
**Load:** 1 snapshot per second
**Duration:** 300 seconds

### 2.2 Scenario 2: Sustained Medium Load (15 minutes)
**Purpose:** Validate sustained operation under moderate load
**Configuration:** Hybrid trigger enabled, buffering enabled
**Load:** 10 snapshots per second
**Duration:** 900 seconds

### 2.3 Scenario 3: High-Frequency Stress (10 minutes)
**Purpose:** Test system under high-frequency conditions
**Configuration:** Hybrid trigger enabled, aggressive buffering
**Load:** 50 snapshots per second
**Duration:** 600 seconds

### 2.4 Scenario 4: Extreme Load (5 minutes)
**Purpose:** Identify failure boundaries and system limits
**Configuration:** Maximum performance settings
**Load:** 100+ snapshots per second
**Duration:** 300 seconds

### 2.5 Scenario 5: Resource Exhaustion (10 minutes)
**Purpose:** Validate graceful degradation under resource constraints
**Configuration:** Limited memory/disk environment
**Load:** Progressive load increase
**Duration:** 600 seconds

---

## 3. Server Commands

### 3.1 Environment Setup Commands

```bash
# Set standalone mode
export QTS_OBSERVER_STANDALONE=1

# Create deployment directory
mkdir -p /opt/qts_observer
cd /opt/qts_observer

# Copy required files (from previous deployment analysis)
cp -r src/ .
cp observer.py .
cp -r docs/ .

# Create log directory
mkdir -p logs
mkdir -p data
mkdir -p config

# Set permissions
chmod +x observer.py
```

### 3.2 Monitoring Setup Commands

```bash
# Install monitoring tools
apt-get update
apt-get install -y htop iotop nethogs

# Create monitoring script
cat > monitor_system.sh << 'EOF'
#!/bin/bash
echo "=== System Monitoring ==="
echo "Timestamp: $(date)"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)"
echo "Memory: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
echo "Disk: $(df -h / | awk 'NR==2{print $5}')"
echo "Network: $(cat /proc/net/dev | grep eth0 | awk '{print $2+$10}')"
echo "Observer Process: $(ps aux | grep observer.py | grep -v grep | wc -l)"
echo "========================"
EOF

chmod +x monitor_system.sh
```

### 3.3 Configuration Files

```bash
# Create stress test configuration
cat > config/stress_test_config.json << 'EOF'
{
  "hybrid_trigger": {
    "enabled": true,
    "tick_source": "simulation",
    "min_interval_ms": 10.0,
    "max_interval_ms": 100.0
  },
  "buffer": {
    "flush_interval_ms": 500.0,
    "max_buffer_size": 50000,
    "enable_buffering": true
  },
  "rotation": {
    "enabled": true,
    "window_ms": 300000,
    "max_files": 10
  },
  "performance": {
    "enabled": true,
    "metrics_history_size": 10000
  }
}
EOF

# Create baseline configuration
cat > config/baseline_config.json << 'EOF'
{
  "hybrid_trigger": {
    "enabled": false
  },
  "buffer": {
    "flush_interval_ms": 1000.0,
    "max_buffer_size": 10000,
    "enable_buffering": true
  },
  "performance": {
    "enabled": true,
    "metrics_history_size": 1000
  }
}
EOF
```

### 3.4 Test Execution Commands

```bash
# Create test runner script
cat > run_stress_test.sh << 'EOF'
#!/bin/bash

TEST_TYPE=$1
DURATION=$2
CONFIG_FILE=$3

echo "Starting stress test: $TEST_TYPE"
echo "Duration: $DURATION seconds"
echo "Config: $CONFIG_FILE"

# Start monitoring in background
./monitor_system.sh > logs/system_monitor_$(date +%Y%m%d_%H%M%S).log &
MONITOR_PID=$!

# Start Observer with test configuration
python observer.py --config $CONFIG_FILE > logs/observer_$(date +%Y%m%d_%H%M%S).log 2>&1 &
OBSERVER_PID=$!

echo "Observer PID: $OBSERVER_PID"
echo "Monitor PID: $MONITOR_PID"

# Run for specified duration
sleep $DURATION

# Stop processes
kill $OBSERVER_PID
kill $MONITOR_PID

echo "Stress test completed"
EOF

chmod +x run_stress_test.sh
```

### 3.5 Load Generation Commands

```bash
# Create load generator
cat > generate_load.py << 'EOF'
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
            "source": "stress_test"
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
    if len(sys.argv) != 3:
        print("Usage: generate_load.py <snapshots_per_second> <duration_seconds>")
        sys.exit(1)
    
    snapshots_per_second = int(sys.argv[1])
    duration = int(sys.argv[2])
    
    interval = 1.0 / snapshots_per_second
    end_time = time.time() + duration
    
    snapshot_count = 0
    
    while time.time() < end_time:
        snapshot = generate_snapshot(f"stress_{snapshot_count}")
        print(json.dumps(snapshot))
        snapshot_count += 1
        time.sleep(interval)
    
    print(f"Generated {snapshot_count} snapshots", file=sys.stderr)

if __name__ == "__main__":
    main()
EOF

chmod +x generate_load.py
```

---

## 4. Metrics to Observe

### 4.1 Performance Metrics
- **Snapshot Processing Latency**: Time from receipt to dispatch
- **Buffer Depth**: Number of records in buffer at any time
- **Flush Duration**: Time taken for buffer flush operations
- **Records Processed**: Total count of snapshots processed
- **Records Blocked**: Count of snapshots rejected by validation/guard

### 4.2 System Metrics
- **CPU Utilization**: Percentage CPU usage by Observer process
- **Memory Usage**: RSS memory consumption
- **Disk I/O**: Read/write operations per second
- **Network I/O**: Network bandwidth utilization
- **File Descriptors**: Number of open file handles

### 4.3 Application Metrics
- **Event Queue Depth**: Number of pending events in EventBus
- **Log File Size**: Growth rate of observer.jsonl
- **Rotation Events**: Number of log rotations performed
- **Configuration Reloads**: Count of configuration changes (should be 0)

### 4.4 Azure Cost Metrics
- **Compute Credits**: Azure compute credits consumed
- **Storage Costs**: Storage usage charges
- **Network Costs**: Data transfer costs
- **Total Cost**: Cumulative cost during testing

---

## 5. Validation Checklist

### 5.1 Pre-Test Validation
- [ ] Server environment meets minimum requirements
- [ ] Observer starts successfully with default configuration
- [ ] Basic snapshot processing works correctly
- [ ] Performance metrics are being collected
- [ ] Log files are being created and written
- [ ] Configuration loading and validation works

### 5.2 During Test Validation
- [ ] Observer process remains stable under load
- [ ] Memory usage remains within expected bounds
- [ ] CPU utilization does not exceed 90% sustained
- [ ] Disk space usage is predictable and manageable
- [ ] No error messages in application logs
- [ ] Performance metrics show expected patterns

### 5.3 Post-Test Validation
- [ ] Observer shuts down gracefully
- [ ] All data is properly flushed to disk
- [ ] Log rotation worked correctly (if enabled)
- [ ] Performance metrics are complete and consistent
- [ ] No data corruption or loss occurred
- [ ] System returns to baseline state after test

### 5.4 Feature-Specific Validation
- [ ] Hybrid trigger mechanism works correctly
- [ ] Buffer and flush operations perform as expected
- [ ] Log rotation functions during high-frequency operations
- [ ] Performance monitoring remains accurate under load
- [ ] Configuration changes are applied correctly
- [ ] No decision logic is introduced during deployment

### 5.5 Azure Cost Validation
- [ ] Azure credit usage is monitored and logged
- [ ] Cost observability metrics are captured
- [ ] Resource consumption is within expected limits
- [ ] Cost patterns match load patterns
- [ ] No unexpected cost spikes occur

---

## 6. Risk Zones and Failure Signals

### 6.1 Stable Operating Zone
- CPU utilization < 70%
- Memory usage < 80% of available
- Disk I/O < 80% of capacity
- Processing latency < 100ms
- No error messages in logs
- Buffer depth < 50% of max size

### 6.2 Risk Zone
- CPU utilization 70-90%
- Memory usage 80-90% of available
- Disk I/O 80-95% of capacity
- Processing latency 100-500ms
- Occasional error messages
- Buffer depth 50-80% of max size

### 6.3 Hard Failure Signals
- CPU utilization > 90% sustained
- Memory usage > 90% of available
- Disk I/O > 95% of capacity
- Processing latency > 500ms
- Frequent error messages
- Buffer depth > 80% of max size
- Process crashes or hangs
- Data corruption or loss

---

## 7. Test Execution Order

### 7.1 Phase 1: Environment Setup (15 minutes)
1. Set up server environment
2. Deploy Observer Scalp Extension
3. Configure monitoring tools
4. Verify basic functionality

### 7.2 Phase 2: Baseline Testing (10 minutes)
1. Run baseline configuration test
2. Collect baseline metrics
3. Verify system stability
4. Document baseline performance

### 7.3 Phase 3: Progressive Load Testing (45 minutes)
1. Run light load test (5 min)
2. Run medium load test (15 min)
3. Run high-frequency test (10 min)
4. Run extreme load test (5 min)
5. Run resource exhaustion test (10 min)

### 7.4 Phase 4: Analysis and Reporting (20 minutes)
1. Collect all metrics and logs
2. Analyze performance patterns
3. Identify system limits
4. Document findings and recommendations

---

## 8. Azure Credit Monitoring Setup

### 8.1 Azure CLI Commands
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"

# Create cost management script
cat > monitor_azure_cost.sh << 'EOF'
#!/bin/bash
echo "=== Azure Cost Monitoring ==="
echo "Timestamp: $(date)"
echo "Current Cost: $(az consumption usage list --query "[?contains(name, 'Microsoft.Compute')].cost" -o tsv | awk '{sum+=$1} END {print sum}')"
echo "Compute Credits Used: $(az consumption usage list --query "[?contains(name, 'Microsoft.Compute')].quantity" -o tsv | awk '{sum+=$1} END {print sum}')"
echo "==========================="
EOF

chmod +x monitor_azure_cost.sh
```

### 8.2 Cost Tracking Commands
```bash
# Start cost monitoring
./monitor_azure_cost.sh > logs/azure_cost_$(date +%Y%m%d_%H%M%S).log &

# Monitor during tests
watch -n 60 './monitor_azure_cost.sh'
```

---

## 9. Emergency Procedures

### 9.1 System Recovery Commands
```bash
# Stop Observer gracefully
pkill -f observer.py

# Force stop if needed
kill -9 $(pgrep -f observer.py)

# Clear temporary files
rm -rf /tmp/observer_*
rm -rf logs/temp_*

# Restart with safe configuration
python observer.py --config config/baseline_config.json
```

### 9.2 Resource Cleanup Commands
```bash
# Clean up old log files
find logs/ -name "*.log" -mtime +7 -delete

# Clean up old data files
find data/ -name "*.jsonl" -mtime +7 -delete

# Clear system cache
sync && echo 3 > /proc/sys/vm/drop_caches
```

---

## 10. Success Criteria

### 10.1 Functional Success
- Observer runs successfully in standalone mode
- All configuration options work as documented
- Performance metrics are collected accurately
- System remains stable under all test scenarios

### 10.2 Performance Success
- Baseline latency < 50ms
- Sustained load processing < 100ms latency
- No memory leaks during extended operation
- Graceful degradation under resource constraints

### 10.3 Cost Success
- Azure credit usage is predictable
- Cost patterns correlate with load patterns
- No unexpected cost spikes
- Cost monitoring provides actionable insights

### 10.4 Operational Success
- All validation checklist items completed
- Risk zones clearly identified
- Failure signals documented
- Emergency procedures tested and validated
