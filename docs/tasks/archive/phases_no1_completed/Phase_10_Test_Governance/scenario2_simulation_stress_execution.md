# Task 10 - Scenario 2: Simulation-based Snapshot Load Stress Testing
# Progressive Load Testing with Contract-Compliant Snapshot Injection

## 1. Derived Sub-Task List for Scenario 2

### 1.1 Simulation Strategy Development
- Design contract-compliant ObservationSnapshot schema
- Create simulation data generator that respects Observer contracts
- Implement safe snapshot injection method without modifying Observer core
- Validate simulation data integrity and schema compliance

### 1.2 Progressive Load Configuration
- Define load levels: 5, 10, 25, 50 snapshots/second
- Set duration for each load level (3 minutes each)
- Configure Observer for stress testing with appropriate settings
- Prepare monitoring infrastructure for each load level

### 1.3 Execution Infrastructure Setup
- Deploy Observer with stress-test configuration
- Set up system resource monitoring
- Create snapshot generation and injection pipeline
- Establish metrics collection and logging

### 1.4 Load Test Execution
- Execute progressive load levels sequentially
- Monitor system behavior during each level
- Collect performance metrics and resource usage
- Record Observer behavior under stress

### 1.5 Analysis and Validation
- Analyze performance degradation patterns
- Identify system limits and failure points
- Validate Observer contract compliance under load
- Document stress test results and boundaries

## 2. Simulation Strategy (Contract-Compliant)

### 2.1 Snapshot Schema Compliance
Based on Observer_Architecture.md, Observer receives ObservationSnapshot structures with:
- **meta**: run_id, timestamp, source
- **market_data**: symbol, price, volume, timestamp
- **system_state**: status, memory_usage

### 2.2 Injection Method
**Assumption**: Observer accepts snapshots via standard input (JSON lines) without core modification
**Strategy**: Use pipe-based injection with schema-compliant JSON snapshots
**Contract Compliance**: No Observer core modification, respects existing data contracts

### 2.3 Simulation Data Characteristics
- **Realistic Market Data**: Varying prices, volumes, timestamps
- **System State Variation**: Memory usage fluctuations, status changes
- **Run ID Uniqueness**: Each snapshot has unique run_id for tracking
- **Timestamp Accuracy**: UTC timestamps with proper timezone handling

## 3. Load Profile

### 3.1 Progressive Load Levels
| Level | Snapshots/Second | Duration | Total Snapshots | Purpose |
|-------|------------------|----------|----------------|---------|
| 1 | 5 | 3 min | 900 | Light load validation |
| 2 | 10 | 3 min | 1800 | Moderate load testing |
| 3 | 25 | 3 min | 4500 | High load stress |
| 4 | 50 | 3 min | 9000 | Extreme stress testing |

### 3.2 Total Test Duration
- **Setup**: 5 minutes
- **Load Testing**: 12 minutes (4 levels × 3 minutes)
- **Cooldown**: 5 minutes
- **Total**: 22 minutes

### 3.3 Configuration for Stress Testing
```json
{
  "hybrid_trigger": {
    "enabled": true,
    "tick_source": "simulation",
    "min_interval_ms": 20.0,
    "max_interval_ms": 200.0
  },
  "buffer": {
    "flush_interval_ms": 500.0,
    "max_buffer_size": 50000,
    "enable_buffering": true
  },
  "rotation": {
    "enabled": true,
    "window_ms": 600000,
    "max_files": 20
  },
  "performance": {
    "enabled": true,
    "metrics_history_size": 10000
  }
}
```

## 4. Server Commands (Copy-Paste Ready)

### 4.1 Environment Setup
```bash
# Set standalone mode
export QTS_OBSERVER_STANDALONE=1

# Create working directory
mkdir -p /tmp/observer_scenario2
cd /tmp/observer_scenario2

# Create stress test configuration
cat > stress_config.json << 'EOF'
{
  "hybrid_trigger": {
    "enabled": true,
    "tick_source": "simulation",
    "min_interval_ms": 20.0,
    "max_interval_ms": 200.0
  },
  "buffer": {
    "flush_interval_ms": 500.0,
    "max_buffer_size": 50000,
    "enable_buffering": true
  },
  "rotation": {
    "enabled": true,
    "window_ms": 600000,
    "max_files": 20
  },
  "performance": {
    "enabled": true,
    "metrics_history_size": 10000
  }
}
EOF

# Create enhanced system monitoring
cat > monitor_system_enhanced.sh << 'EOF'
#!/bin/bash
echo "Timestamp,CPU%,Memory%,Disk%,Network_Recv_MB,Network_Sent_MB,Observer_PID,Observer_CPU%,Observer_Memory_MB"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # System metrics
    cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    memory=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
    disk=$(df -h . | awk 'NR==2{print $5}' | cut -d'%' -f1)
    
    # Network metrics
    net_recv=$(cat /proc/net/dev | grep eth0 | awk '{print $2}')
    net_sent=$(cat /proc/net/dev | grep eth0 | awk '{print $10}')
    net_recv_mb=$(echo "scale=2; $net_recv / 1048576" | bc)
    net_sent_mb=$(echo "scale=2; $net_sent / 1048576" | bc)
    
    # Observer process metrics
    observer_pid=$(pgrep -f observer.py | head -1)
    if [ -n "$observer_pid" ]; then
        observer_cpu=$(ps -p $observer_pid -o %cpu --no-headers)
        observer_memory=$(ps -p $observer_pid -o rss --no-headers)
        observer_memory_mb=$(echo "scale=1; $observer_memory / 1024" | bc)
    else
        observer_cpu="N/A"
        observer_memory_mb="N/A"
    fi
    
    echo "$timestamp,$cpu,$memory,$disk,$net_recv_mb,$net_sent_mb,$observer_pid,$observer_cpu,$observer_memory_mb"
    sleep 2
done
EOF

chmod +x monitor_system_enhanced.sh
```

### 4.2 Contract-Compliant Snapshot Generator
```bash
# Create advanced snapshot generator
cat > generate_stress_snapshots.py << 'EOF'
#!/usr/bin/env python3
import json
import time
import sys
import random
from datetime import datetime, timezone

class SnapshotGenerator:
    def __init__(self, base_price=100.0):
        self.base_price = base_price
        self.snapshot_count = 0
        self.start_time = time.time()
    
    def generate_observation_snapshot(self, run_id):
        """Generate contract-compliant ObservationSnapshot"""
        # Vary price realistically
        price_change = random.uniform(-0.5, 0.5)
        current_price = self.base_price + price_change
        
        # Vary volume
        volume = random.randint(100, 10000)
        
        # Vary system state
        memory_usage = random.uniform(30.0, 80.0)
        status = "running" if memory_usage < 70.0 else "high_memory"
        
        snapshot = {
            "meta": {
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "stress_test_simulation"
            },
            "market_data": {
                "symbol": "STRESS_TEST",
                "price": round(current_price, 2),
                "volume": volume,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "system_state": {
                "status": status,
                "memory_usage": round(memory_usage, 1)
            }
        }
        
        return snapshot
    
    def generate_snapshots_at_rate(self, snapshots_per_second, duration_seconds):
        """Generate snapshots at specified rate for duration"""
        interval = 1.0 / snapshots_per_second
        end_time = time.time() + duration_seconds
        
        snapshots_generated = 0
        
        while time.time() < end_time:
            run_id = f"stress_{self.snapshot_count}"
            snapshot = self.generate_observation_snapshot(run_id)
            
            print(json.dumps(snapshot))
            
            self.snapshot_count += 1
            snapshots_generated += 1
            
            # Precise timing
            elapsed = time.time() - (self.start_time + snapshots_generated * interval)
            if elapsed < 0:
                time.sleep(-elapsed)
        
        return snapshots_generated

def main():
    if len(sys.argv) != 3:
        print("Usage: generate_stress_snapshots.py <snapshots_per_second> <duration_seconds>", file=sys.stderr)
        sys.exit(1)
    
    snapshots_per_second = int(sys.argv[1])
    duration = int(sys.argv[2])
    
    generator = SnapshotGenerator()
    
    print(f"Starting stress test: {snapshots_per_second} snapshots/sec for {duration} seconds", file=sys.stderr)
    
    snapshots_generated = generator.generate_snapshots_at_rate(snapshots_per_second, duration)
    
    print(f"Generated {snapshots_generated} snapshots", file=sys.stderr)

if __name__ == "__main__":
    main()
EOF

chmod +x generate_stress_snapshots.py
```

### 4.3 Observer Startup and Monitoring
```bash
# Create log directory
mkdir -p logs

# Start enhanced system monitoring
./monitor_system_enhanced.sh > logs/system_metrics_scenario2.csv &
MONITOR_PID=$!
echo "System monitoring started (PID: $MONITOR_PID)"

# Start Observer with stress configuration
cd /opt/qts_observer

# Copy stress config to Observer location
cp /tmp/observer_scenario2/stress_config.json config/

# Start Observer
python observer.py > /tmp/observer_scenario2/logs/observer_stress.log 2>&1 &
OBSERVER_PID=$!
echo "Observer started (PID: $OBSERVER_PID)"

# Wait for Observer initialization
sleep 15

# Verify Observer is running
if ps -p $OBSERVER_PID > /dev/null; then
    echo "Observer is running successfully"
else
    echo "Observer failed to start"
    exit 1
fi

# Return to test directory
cd /tmp/observer_scenario2
```

### 4.4 Progressive Load Test Execution
```bash
# Create stress test runner
cat > run_progressive_stress_test.sh << 'EOF'
#!/bin/bash

echo "=== Scenario 2: Progressive Stress Test ==="
echo "Starting at: $(date)"

# Load levels: snapshots_per_second duration_seconds
declare -a load_levels=(
    "5 180"   # Level 1: 5 snapshots/sec for 3 minutes
    "10 180"  # Level 2: 10 snapshots/sec for 3 minutes
    "25 180"  # Level 3: 25 snapshots/sec for 3 minutes
    "50 180"  # Level 4: 50 snapshots/sec for 3 minutes
)

level_num=1
total_snapshots=0

for level in "${load_levels[@]}"; do
    read -r rate duration <<< "$level"
    
    echo ""
    echo "=== Load Level $level_num: $rate snapshots/sec for $duration seconds ==="
    echo "Start time: $(date)"
    
    # Start snapshot generation
    ./generate_stress_snapshots.py $rate $duration | python observer.py > logs/level${level_num}_processing.log 2>&1 &
    load_pid=$!
    
    # Monitor during this level
    level_start=$(date +%s)
    while [ $(($(date +%s) - level_start)) -lt $duration ]; do
        # Check if Observer is still running
        if ! ps -p $OBSERVER_PID > /dev/null; then
            echo "ERROR: Observer crashed during level $level_num"
            kill $load_pid 2>/dev/null
            exit 1
        fi
        
        # Check system resources
        cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        memory=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
        
        if (( $(echo "$cpu > 90" | bc -l) )); then
            echo "WARNING: High CPU usage: $cpu%"
        fi
        
        if (( $(echo "$memory > 85" | bc -l) )); then
            echo "WARNING: High memory usage: $memory%"
        fi
        
        sleep 10
    done
    
    # Wait for load generation to complete
    wait $load_pid
    
    # Calculate snapshots for this level
    level_snapshots=$((rate * duration))
    total_snapshots=$((total_snapshots + level_snapshots))
    
    echo "Level $level_num completed: $level_snapshots snapshots"
    echo "Total so far: $total_snapshots snapshots"
    
    # Brief cooldown between levels
    if [ $level_num -lt 4 ]; then
        echo "Cooldown: 30 seconds"
        sleep 30
    fi
    
    level_num=$((level_num + 1))
done

echo ""
echo "=== All Load Levels Completed ==="
echo "Total snapshots generated: $total_snapshots"
echo "End time: $(date)"
EOF

chmod +x run_progressive_stress_test.sh

# Execute the progressive stress test
./run_progressive_stress_test.sh
```

### 4.5 Post-Test Cleanup and Analysis
```bash
# Stop monitoring
kill $MONITOR_PID 2>/dev/null

# Stop Observer gracefully
kill $OBSERVER_PID 2>/dev/null
sleep 10

# Force stop if needed
kill -9 $OBSERVER_PID 2>/dev/null

echo "Scenario 2 completed at: $(date)"

# Generate quick analysis
cat > analyze_scenario2.sh << 'EOF'
#!/bin/bash
echo "=== Scenario 2 Analysis ==="

# Count total snapshots processed
processed=$(grep -c "PatternRecord dispatched" /tmp/observer_scenario2/logs/observer_stress.log)
echo "Snapshots processed: $processed"

# Count errors
errors=$(grep -c "ERROR\|CRITICAL" /tmp/observer_scenario2/logs/observer_stress.log)
echo "Error count: $errors"

# Peak system resources
peak_cpu=$(awk -F',' 'NR>1 && $2>max {max=$2} END {print max}' logs/system_metrics_scenario2.csv)
peak_memory=$(awk -F',' 'NR>1 && $3>max {max=$3} END {print max}' logs/system_metrics_scenario2.csv)
echo "Peak CPU: ${peak_cpu}%"
echo "Peak Memory: ${peak_memory}%"

# Observer peak resources
peak_observer_cpu=$(awk -F',' 'NR>1 && $8>max && $8!="N/A" {max=$8} END {print max}' logs/system_metrics_scenario2.csv)
peak_observer_memory=$(awk -F',' 'NR>1 && $9>max && $9!="N/A" {max=$9} END {print max}' logs/system_metrics_scenario2.csv)
echo "Peak Observer CPU: ${peak_observer_cpu}%"
echo "Peak Observer Memory: ${peak_observer_memory}MB"

# Output file analysis
if [ -f "/opt/qts_observer/config/observer/observer.jsonl" ]; then
    output_lines=$(wc -l < /opt/qts_observer/config/observer/observer.jsonl)
    echo "Output file lines: $output_lines"
fi

echo "=== Analysis Complete ==="
EOF

chmod +x analyze_scenario2.sh
./analyze_scenario2.sh
```

## 5. Metrics and How to Read Them

### 5.1 Performance Metrics
- **Processing Latency**: Time from snapshot receipt to PatternRecord dispatch
- **Throughput**: Snapshots processed per second
- **Buffer Depth**: Current number of records in buffer
- **Flush Frequency**: How often buffer flushes occur
- **Error Rate**: Number of errors per 1000 snapshots

### 5.2 System Resource Metrics
- **CPU Utilization**: Total system CPU percentage
- **Memory Usage**: System memory usage percentage
- **Disk I/O**: Disk read/write operations
- **Network I/O**: Network receive/transmit rates
- **Observer Process CPU/Memory**: Per-process resource usage

### 5.3 Application Behavior Metrics
- **Event Queue Depth**: Number of pending events
- **Log Rotation Events**: Number of log rotations performed
- **Configuration Validation**: Configuration loading status
- **Snapshot Validation Rate**: Percentage of snapshots passing validation

### 5.4 Reading the Metrics
```bash
# Real-time monitoring
tail -f logs/system_metrics_scenario2.csv

# Observer log monitoring
tail -f logs/observer_stress.log | grep -E "(PatternRecord dispatched|ERROR|WARNING)"

# Performance metrics extraction
grep "snapshot_processing" logs/observer_stress.log | tail -10

# Buffer depth monitoring
grep "buffer_depth" logs/observer_stress.log | tail -10
```

## 6. Pass/Fail Criteria

### 6.1 PASS Criteria (All must be met)
1. **System Stability**: Observer runs through all load levels without crashing
2. **Progressive Performance**: Throughput scales with load (within limits)
3. **Resource Limits**: CPU < 80%, Memory < 85% at all load levels
4. **Error Rate**: < 0.1% error rate across all levels
5. **Data Integrity**: All generated snapshots processed and written to output
6. **Graceful Degradation**: Performance degrades predictably, not catastrophically
7. **Recovery**: System returns to baseline after test completion

### 6.2 FAIL Criteria (Any one triggers failure)
1. **Process Failure**: Observer crashes during any load level
2. **Resource Exhaustion**: CPU > 90% or Memory > 95% sustained
3. **High Error Rate**: > 1% error rate at any load level
4. **Data Loss**: > 5% of snapshots not processed or corrupted
5. **Catastrophic Degradation**: Sudden performance collapse
6. **Contract Violation**: Observer modifies snapshots or introduces decision logic
7. **Ungraceful Shutdown**: Observer does not stop cleanly

### 6.3 Performance Thresholds by Load Level
| Load Level | Expected Throughput | Max Acceptable Latency | Max CPU | Max Memory |
|------------|-------------------|----------------------|---------|------------|
| 5 snap/sec | 4.8-5.0 snap/sec | < 50ms | < 40% | < 60% |
| 10 snap/sec | 9.5-10.0 snap/sec | < 75ms | < 60% | < 70% |
| 25 snap/sec | 23-25 snap/sec | < 150ms | < 75% | < 80% |
| 50 snap/sec | 45-50 snap/sec | < 300ms | < 80% | < 85% |

## 7. Early Warning Signals vs Fail Signals

### 7.1 Early Warning Signals (Monitor Closely)
- CPU usage 70-80% sustained
- Memory usage 75-85% sustained
- Processing latency increasing trend
- Buffer depth growing trend
- Occasional validation failures

### 7.2 Fail Signals (Immediate Action Required)
- CPU usage > 90% sustained
- Memory usage > 95% sustained
- Processing latency > 500ms
- Error rate > 1%
- Observer process crashes
- Data corruption or loss

### 7.3 Monitoring Commands During Test
```bash
# Check Observer status
ps -p $OBSERVER_PID && echo "Observer running" || echo "Observer crashed"

# Check system resources
top -bn1 | head -5

# Check error rate
echo "Recent errors:" && tail -100 logs/observer_stress.log | grep -c "ERROR"

# Check processing rate
echo "Recent processing rate:" && tail -100 logs/observer_stress.log | grep -c "PatternRecord dispatched"
```

## 8. Expected Results for Successful Scenario 2

### 8.1 Total Volume
- **Total Snapshots**: 16,200 (900 + 1800 + 4500 + 9000)
- **Test Duration**: 22 minutes total
- **Output File Size**: ~10-20MB depending on buffer settings

### 8.2 Performance Profile
- **Level 1 (5 snap/sec)**: < 40ms latency, < 30% CPU
- **Level 2 (10 snap/sec)**: < 75ms latency, < 50% CPU  
- **Level 3 (25 snap/sec)**: < 150ms latency, < 70% CPU
- **Level 4 (50 snap/sec)**: < 300ms latency, < 80% CPU

### 8.3 Resource Usage
- **Peak System CPU**: < 80%
- **Peak System Memory**: < 85%
- **Peak Observer Memory**: < 500MB
- **Disk Usage**: Predictable based on volume

### 8.4 Behavior Validation
- **No Contract Violations**: Observer remains judgment-free data producer
- **No Decision Logic**: No strategy or execution logic introduced
- **Data Integrity**: All snapshots processed correctly
- **Graceful Degradation**: Performance scales predictably with load
