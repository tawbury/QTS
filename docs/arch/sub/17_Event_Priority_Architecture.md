# ============================================================
# QTS Event Priority Architecture
# ============================================================

Version: v1.0.0
Status: Architecture Specification (Final)
Author: 타우
Last Updated: 2026-01-30

문서 목적:
본 문서는 QTS의 **이벤트 우선순위(Event Priority)** 아키텍처를 정의한다.
이벤트는 4개의 우선순위 레벨로 분류되며, 레이턴시 격리와 논블로킹 실행을
보장하여 시스템의 결정론적(Deterministic) 처리를 구현한다.

---

# **1. Overview**

## **1.1 목적**

Event Priority Architecture는 다음 목표를 수행한다.

1. 이벤트의 우선순위 기반 처리 보장
2. 레이턴시 격리(Latency Isolation) 구현
3. 논블로킹 실행(Non-blocking Execution) 보장
4. 결정론적 이벤트 처리 순서 정의
5. 시스템 과부하 시 그레이스풀 저하(Graceful Degradation) 지원

---

## **1.2 범위**

포함:

- 이벤트 우선순위 레벨 정의 (P0 ~ P3)
- 이벤트 큐 아키텍처
- 처리 규칙 및 스케줄링
- 스레드/프로세스 모델
- ETEDA 통합
- 모니터링 및 알림

제외:

- 개별 이벤트 핸들러 구현 (각 Engine 문서 참조)
- 비즈니스 로직 상세 (Pipeline 문서 참조)

---

## **1.3 설계 원칙**

1. **P0은 절대 지연되지 않는다.**
   Execution/Fill 이벤트는 즉시 처리되어야 한다.

2. **낮은 우선순위가 높은 우선순위를 차단하지 않는다.**
   UI/Logging(P3)이 Execution(P0)을 블로킹할 수 없다.

3. **이벤트 유실보다 지연이 낫다.**
   P0/P1 이벤트는 유실 없이 처리되어야 한다.

4. **레이턴시 SLA는 측정 가능해야 한다.**
   각 우선순위별 레이턴시 목표가 명확히 정의된다.

---

## **1.4 관련 문서**

- **Main Architecture**: [../00_Architecture.md](../00_Architecture.md)
- **ETEDA Pipeline**: [../03_Pipeline_ETEDA_Architecture.md](../03_Pipeline_ETEDA_Architecture.md)
- **Broker Integration**: [../08_Broker_Integration_Architecture.md](../08_Broker_Integration_Architecture.md)
- **Fail-Safe & Safety**: [../07_FailSafe_Architecture.md](../07_FailSafe_Architecture.md)
- **Micro Risk Loop**: [16_Micro_Risk_Loop_Architecture.md](./16_Micro_Risk_Loop_Architecture.md)
- **Scalp Execution**: [15_Scalp_Execution_Micro_Architecture.md](./15_Scalp_Execution_Micro_Architecture.md)

---

# **2. Priority Level Definitions**

## **2.1 우선순위 계층 개요**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EVENT PRIORITY HIERARCHY                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐                                               │
│  │      P0         │  CRITICAL - 즉시 처리                         │
│  │   Execution &   │  Target: < 10ms                               │
│  │   Fill Events   │  절대 지연 불가                               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │      P1         │  HIGH - 고우선 처리                           │
│  │   Orderbook &   │  Target: < 50ms                               │
│  │   Price Updates │  P0 완료 후 처리                              │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │      P2         │  MEDIUM - 일반 처리                           │
│  │    Strategy     │  Target: < 500ms                              │
│  │   Evaluation    │  P0/P1 완료 후 처리                           │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │      P3         │  LOW - 최선 노력(Best Effort)                 │
│  │   UI & Logging  │  Target: Best effort                          │
│  │                 │  지연/배치 허용                               │
│  └─────────────────┘                                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **2.2 P0: Execution & Fill Events (Critical)**

### **2.2.1 정의**

P0은 가장 높은 우선순위로, 주문 실행 및 체결 관련 이벤트를 처리한다.
이 이벤트들은 시스템 상태와 자산에 직접적인 영향을 미친다.

### **2.2.2 P0 이벤트 목록**

| 이벤트 | 설명 | 소스 |
|--------|------|------|
| `FILL_CONFIRMED` | 주문 체결 확인 | Broker |
| `FILL_PARTIAL` | 부분 체결 | Broker |
| `ORDER_REJECTED` | 주문 거부 | Broker |
| `ORDER_CANCELLED` | 주문 취소 | Broker |
| `POSITION_UPDATE` | 포지션 상태 변경 | System |
| `EMERGENCY_STOP` | 긴급 정지 | Safety |
| `BROKER_DISCONNECT` | 브로커 연결 끊김 | Broker |

### **2.2.3 P0 처리 규칙**

```python
P0_RULES = {
    "max_latency_ms": 10,
    "queue_size": 100,          # 작고 bounded
    "overflow_policy": "BLOCK", # 유실 불가
    "thread_affinity": "DEDICATED",
    "preemption": True,
    "retry_on_failure": True,
    "max_retries": 3
}
```

### **2.2.4 P0 이벤트 계약**

```python
P0EventContract = {
    "event_id": "uuid",
    "event_type": "FILL_CONFIRMED",
    "priority": 0,
    "timestamp": "2026-01-30T09:30:00.123Z",
    "source": "BROKER_KIS",
    "payload": {
        "order_id": "ORD123456",
        "symbol": "005930",
        "filled_qty": 100,
        "filled_price": 75000,
        "filled_time": "2026-01-30T09:30:00.100Z"
    },
    "requires_ack": True,
    "max_process_time_ms": 10
}
```

---

## **2.3 P1: Orderbook & Price Updates (High)**

### **2.3.1 정의**

P1은 시장 데이터 이벤트로, 가격 변동 및 호가창 업데이트를 처리한다.
전략 평가와 리스크 계산에 필요한 실시간 데이터를 제공한다.

### **2.3.2 P1 이벤트 목록**

| 이벤트 | 설명 | 소스 |
|--------|------|------|
| `PRICE_TICK` | 가격 틱 업데이트 | Market Data |
| `ORDERBOOK_UPDATE` | 호가창 업데이트 | Market Data |
| `VOLUME_UPDATE` | 거래량 업데이트 | Market Data |
| `INDEX_UPDATE` | 지수 업데이트 | Market Data |
| `VIX_UPDATE` | 변동성 지수 | Market Data |

### **2.3.3 P1 처리 규칙**

```python
P1_RULES = {
    "max_latency_ms": 50,
    "queue_size": 10000,
    "overflow_policy": "DROP_OLDEST",  # 오래된 틱 드롭
    "thread_affinity": "POOL",
    "preemption": False,               # P0에 의해 선점됨
    "batching_enabled": True,          # 배치 처리 허용
    "batch_window_ms": 10
}
```

### **2.3.4 P1 이벤트 계약**

```python
P1EventContract = {
    "event_id": "uuid",
    "event_type": "PRICE_TICK",
    "priority": 1,
    "timestamp": "2026-01-30T09:30:00.200Z",
    "source": "MARKET_DATA",
    "payload": {
        "symbol": "005930",
        "price": 75100,
        "volume": 1000,
        "bid": 75000,
        "ask": 75100
    },
    "requires_ack": False,
    "can_batch": True
}
```

---

## **2.4 P2: Strategy Evaluation (Medium)**

### **2.4.1 정의**

P2는 전략 평가 이벤트로, ETEDA 파이프라인의 주요 계산 작업을 처리한다.
시장 상황에 따른 매매 신호 생성 및 평가를 담당한다.

### **2.4.2 P2 이벤트 목록**

| 이벤트 | 설명 | 소스 |
|--------|------|------|
| `ETEDA_CYCLE_START` | ETEDA 사이클 시작 | Scheduler |
| `STRATEGY_EVALUATE` | 전략 평가 트리거 | ETEDA |
| `RISK_EVALUATE` | 리스크 평가 트리거 | ETEDA |
| `PORTFOLIO_EVALUATE` | 포트폴리오 평가 | ETEDA |
| `INDICATOR_UPDATE` | 기술 지표 업데이트 | Calc Engine |
| `SIGNAL_GENERATED` | 매매 신호 생성 | Strategy |

### **2.4.3 P2 처리 규칙**

```python
P2_RULES = {
    "max_latency_ms": 500,
    "queue_size": 1000,
    "overflow_policy": "COLLAPSE",     # 같은 타입 병합
    "thread_affinity": "WORKER_POOL",
    "preemption": False,
    "batching_enabled": True,
    "batch_window_ms": 100
}
```

### **2.4.4 P2 이벤트 계약**

```python
P2EventContract = {
    "event_id": "uuid",
    "event_type": "STRATEGY_EVALUATE",
    "priority": 2,
    "timestamp": "2026-01-30T09:30:01.000Z",
    "source": "ETEDA_SCHEDULER",
    "payload": {
        "strategy_type": "SCALP",
        "symbols": ["005930", "000660"],
        "calc_data_version": "v1.2.3"
    },
    "requires_ack": False,
    "can_collapse": True
}
```

---

## **2.5 P3: UI & Logging (Low)**

### **2.5.1 정의**

P3은 가장 낮은 우선순위로, 사용자 인터페이스 업데이트와 로깅을 처리한다.
시스템의 핵심 기능에 영향을 주지 않으며, 지연이 허용된다.

### **2.5.2 P3 이벤트 목록**

| 이벤트 | 설명 | 소스 |
|--------|------|------|
| `DASHBOARD_UPDATE` | 대시보드 업데이트 | UI Engine |
| `LOG_WRITE` | 로그 기록 | Logger |
| `REPORT_GENERATE` | 리포트 생성 | Reporter |
| `NOTIFICATION_SEND` | 알림 전송 | Notifier |
| `METRIC_RECORD` | 메트릭 기록 | Monitor |

### **2.5.3 P3 처리 규칙**

```python
P3_RULES = {
    "max_latency_ms": None,            # Best effort
    "queue_size": 50000,
    "overflow_policy": "SAMPLE",       # 샘플링 (일부만 처리)
    "thread_affinity": "BACKGROUND",
    "preemption": False,
    "batching_enabled": True,
    "batch_window_ms": 1000            # 1초 배치
}
```

### **2.5.4 P3 이벤트 계약**

```python
P3EventContract = {
    "event_id": "uuid",
    "event_type": "DASHBOARD_UPDATE",
    "priority": 3,
    "timestamp": "2026-01-30T09:30:02.000Z",
    "source": "UI_ENGINE",
    "payload": {
        "dashboard_id": "R_DASH",
        "update_type": "FULL",
        "data": {...}
    },
    "requires_ack": False,
    "can_drop": True                   # 드롭 가능
}
```

---

# **3. Event Queue Architecture**

## **3.1 멀티 큐 설계**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EVENT QUEUE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    EVENT DISPATCHER                          │   │
│  └────────────────────────────┬────────────────────────────────┘   │
│                               │                                     │
│          ┌────────────────────┼────────────────────┐               │
│          │                    │                    │               │
│          ▼                    ▼                    ▼               │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐        │
│  │   P0 QUEUE    │   │   P1 QUEUE    │   │  P2/P3 QUEUE  │        │
│  │               │   │               │   │               │        │
│  │  Size: 100    │   │  Size: 10000  │   │  Size: 51000  │        │
│  │  Bounded      │   │  Ring Buffer  │   │  Unbounded    │        │
│  │  No Drop      │   │  Drop Oldest  │   │  Collapse     │        │
│  └───────┬───────┘   └───────┬───────┘   └───────┬───────┘        │
│          │                   │                   │                 │
│          ▼                   ▼                   ▼                 │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐        │
│  │ P0 HANDLER    │   │ P1 HANDLER    │   │ P2/P3 WORKERS │        │
│  │ (Dedicated)   │   │ (Pool: 2)     │   │ (Pool: 4)     │        │
│  └───────────────┘   └───────────────┘   └───────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **3.2 큐 우선순위 스케줄링**

### **3.2.1 스케줄링 알고리즘**

```python
def event_scheduler():
    while system_running:
        # P0 최우선 처리 (Strict Priority)
        while not p0_queue.empty():
            event = p0_queue.get_nowait()
            process_p0_event(event)

        # P0 비어있을 때만 P1 처리
        if p0_queue.empty() and not p1_queue.empty():
            events = p1_queue.get_batch(max_batch=100)
            process_p1_events(events)

        # P0/P1 비어있을 때만 P2/P3 처리
        if p0_queue.empty() and p1_queue.empty():
            if not p2_queue.empty():
                events = p2_queue.get_batch(max_batch=50)
                process_p2_events(events)
            elif not p3_queue.empty():
                events = p3_queue.get_batch(max_batch=100)
                process_p3_events(events)

        # 짧은 대기 (CPU 절약)
        sleep_ms(1)
```

### **3.2.2 선점(Preemption) 규칙**

```python
PREEMPTION_RULES = {
    "p0_can_preempt": ["P1", "P2", "P3"],  # P0는 모든 것을 선점
    "p1_can_preempt": ["P2", "P3"],         # P1은 P2/P3 선점
    "p2_can_preempt": ["P3"],               # P2는 P3 선점
    "p3_can_preempt": []                    # P3는 선점 불가
}
```

---

## **3.3 큐 오버플로우 처리**

### **3.3.1 오버플로우 정책**

| 큐 | 정책 | 설명 |
|-----|------|------|
| P0 | BLOCK | 생산자 차단, 이벤트 유실 불가 |
| P1 | DROP_OLDEST | 가장 오래된 이벤트 드롭 |
| P2 | COLLAPSE | 같은 타입 이벤트 병합 |
| P3 | SAMPLE | 샘플링 (N개 중 1개만 처리) |

### **3.3.2 오버플로우 처리 로직**

```python
def handle_queue_overflow(queue, event, policy):
    if policy == "BLOCK":
        # 공간이 생길 때까지 대기
        while queue.full():
            sleep_ms(1)
        queue.put(event)

    elif policy == "DROP_OLDEST":
        if queue.full():
            dropped = queue.get_nowait()
            log_dropped_event(dropped, reason="OVERFLOW")
        queue.put(event)

    elif policy == "COLLAPSE":
        existing = find_collapsible_event(queue, event)
        if existing:
            merge_events(existing, event)
        else:
            queue.put(event)

    elif policy == "SAMPLE":
        if random() < SAMPLE_RATE:
            queue.put(event)
        else:
            log_sampled_event(event)
```

---

## **3.4 백프레셔(Backpressure) 메커니즘**

```python
BACKPRESSURE_CONFIG = {
    "p1_warning_threshold": 0.70,   # 70% 차면 경고
    "p1_critical_threshold": 0.90,  # 90% 차면 위험
    "p2_warning_threshold": 0.80,
    "p2_critical_threshold": 0.95,

    "actions": {
        "WARNING": "INCREASE_BATCH_SIZE",
        "CRITICAL": "PAUSE_LOW_PRIORITY"
    }
}

def check_backpressure():
    for queue_id, queue in queues.items():
        fill_ratio = queue.size() / queue.capacity()

        if fill_ratio > BACKPRESSURE_CONFIG[f"{queue_id}_critical_threshold"]:
            trigger_backpressure(queue_id, "CRITICAL")
        elif fill_ratio > BACKPRESSURE_CONFIG[f"{queue_id}_warning_threshold"]:
            trigger_backpressure(queue_id, "WARNING")
```

---

# **4. Event Processing Rules**

## **4.1 P0 선점 규칙**

P0 이벤트가 도착하면:

1. 현재 P1/P2/P3 처리를 즉시 중단 (체크포인트 저장)
2. P0 이벤트 처리
3. P0 큐가 빌 때까지 계속
4. 중단된 처리 재개

```python
def p0_interrupt_handler(event):
    # 현재 작업 상태 저장
    checkpoint = save_current_work()

    # P0 즉시 처리
    result = process_p0_event(event)

    # 결과 즉시 적용
    apply_p0_result(result)

    # 이전 작업 재개
    resume_from_checkpoint(checkpoint)
```

---

## **4.2 레이턴시 격리 보장**

### **4.2.1 격리 규칙**

```python
LATENCY_ISOLATION_RULES = {
    # P0/P1은 P2/P3와 별도 스레드
    "thread_isolation": True,

    # P0은 전용 스레드 (다른 작업 없음)
    "p0_dedicated_thread": True,

    # P3는 P0/P1/P2와 완전 분리된 프로세스 가능
    "p3_separate_process": True,

    # 메모리 버퍼 분리
    "memory_isolation": True
}
```

### **4.2.2 격리 검증**

```python
def verify_latency_isolation():
    # P0 레이턴시 검증
    p0_latencies = measure_p0_latencies(duration_sec=60)
    p0_p99 = percentile(p0_latencies, 99)

    if p0_p99 > 10:  # 10ms 초과
        raise IsolationViolation(
            f"P0 p99 latency {p0_p99}ms exceeds 10ms target"
        )

    # P1 레이턴시 검증
    p1_latencies = measure_p1_latencies(duration_sec=60)
    p1_p99 = percentile(p1_latencies, 99)

    if p1_p99 > 50:  # 50ms 초과
        log_warning(f"P1 p99 latency {p1_p99}ms exceeds 50ms target")
```

---

## **4.3 논블로킹 보장**

P3가 P0/P1을 블로킹할 수 없음을 보장:

```python
class NonBlockingGuarantee:
    """P3가 P0/P1을 블로킹하지 않도록 보장"""

    def __init__(self):
        # P3는 별도 스레드 풀에서 실행
        self.p3_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="P3_"
        )

        # P3 작업 타임아웃
        self.p3_timeout_ms = 5000

    def process_p3_event(self, event):
        future = self.p3_executor.submit(
            self._process_p3_internal, event
        )

        try:
            # 타임아웃 적용 (5초)
            future.result(timeout=self.p3_timeout_ms / 1000)
        except TimeoutError:
            # 타임아웃 시 취소
            future.cancel()
            log_warning(f"P3 event {event.event_id} timed out")
```

---

## **4.4 이벤트 배치 처리 규칙**

```python
BATCHING_RULES = {
    "p1": {
        "enabled": True,
        "max_batch_size": 100,
        "max_batch_window_ms": 10,
        "batch_by": "event_type"
    },
    "p2": {
        "enabled": True,
        "max_batch_size": 50,
        "max_batch_window_ms": 100,
        "batch_by": "symbol"
    },
    "p3": {
        "enabled": True,
        "max_batch_size": 100,
        "max_batch_window_ms": 1000,
        "batch_by": "event_type"
    }
}

def batch_events(queue, rules):
    batch = []
    start_time = now()

    while len(batch) < rules.max_batch_size:
        elapsed = now() - start_time
        if elapsed > rules.max_batch_window_ms:
            break

        try:
            event = queue.get(timeout=rules.max_batch_window_ms - elapsed)
            batch.append(event)
        except Empty:
            break

    return batch
```

---

# **5. Thread/Process Model**

## **5.1 스레드 아키텍처**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     THREAD ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  MAIN PROCESS                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │
│  │  │ P0 HANDLER  │  │ P1 HANDLER  │  │   P2 WORKER POOL    │  │   │
│  │  │ (Dedicated) │  │ (Pool: 2)   │  │   (Workers: 4)      │  │   │
│  │  │             │  │             │  │                     │  │   │
│  │  │ Affinity:   │  │ Affinity:   │  │   Worker-1          │  │   │
│  │  │ CPU Core 0  │  │ CPU Core 1  │  │   Worker-2          │  │   │
│  │  │             │  │             │  │   Worker-3          │  │   │
│  │  │ Priority:   │  │ Priority:   │  │   Worker-4          │  │   │
│  │  │ REALTIME    │  │ HIGH        │  │                     │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │   │
│  │                                                              │   │
│  │  ┌─────────────────────────────────────────────────────────┐│   │
│  │  │                    SCHEDULER THREAD                      ││   │
│  │  │   Queue Monitor | Backpressure Control | Health Check    ││   │
│  │  └─────────────────────────────────────────────────────────┘│   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  BACKGROUND PROCESS (Optional - P3 isolated)                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────┐│   │
│  │  │                   P3 WORKER POOL                         ││   │
│  │  │   UI Worker | Log Worker | Report Worker                 ││   │
│  │  └─────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **5.2 P0 전용 핸들러 스레드**

```python
class P0Handler(Thread):
    """P0 이벤트 전용 핸들러 - 최고 우선순위"""

    def __init__(self, queue):
        super().__init__(daemon=False)
        self.queue = queue
        self.running = True

        # CPU 코어 고정
        self.cpu_affinity = 0

        # 스레드 우선순위 최대
        self.priority = THREAD_PRIORITY_REALTIME

    def run(self):
        set_cpu_affinity(self.cpu_affinity)
        set_thread_priority(self.priority)

        while self.running:
            try:
                event = self.queue.get(timeout=0.001)  # 1ms 타임아웃
                self._process(event)
            except Empty:
                continue

    def _process(self, event):
        start = time_ns()

        try:
            handler = get_handler(event.event_type)
            result = handler.handle(event)
            self._apply_result(result)
        finally:
            elapsed_ms = (time_ns() - start) / 1_000_000
            record_latency("P0", elapsed_ms)

            if elapsed_ms > 10:
                log_warning(f"P0 latency exceeded: {elapsed_ms}ms")
```

---

## **5.3 P1 핸들러 스레드 풀**

```python
class P1HandlerPool:
    """P1 이벤트 핸들러 풀"""

    def __init__(self, queue, pool_size=2):
        self.queue = queue
        self.pool = ThreadPoolExecutor(
            max_workers=pool_size,
            thread_name_prefix="P1_Handler_"
        )

    def start(self):
        for i in range(self.pool._max_workers):
            self.pool.submit(self._worker_loop, i)

    def _worker_loop(self, worker_id):
        set_thread_priority(THREAD_PRIORITY_HIGH)

        while True:
            # 배치 수집
            batch = collect_batch(self.queue, max_size=100, timeout_ms=10)

            if batch:
                self._process_batch(batch)

    def _process_batch(self, batch):
        start = time_ns()

        for event in batch:
            handler = get_handler(event.event_type)
            handler.handle(event)

        elapsed_ms = (time_ns() - start) / 1_000_000
        record_batch_latency("P1", len(batch), elapsed_ms)
```

---

## **5.4 P2/P3 워커 풀**

```python
class P2P3WorkerPool:
    """P2/P3 이벤트 워커 풀"""

    def __init__(self, p2_queue, p3_queue, pool_size=4):
        self.p2_queue = p2_queue
        self.p3_queue = p3_queue
        self.pool = ThreadPoolExecutor(
            max_workers=pool_size,
            thread_name_prefix="P2P3_Worker_"
        )

    def start(self):
        for i in range(self.pool._max_workers):
            self.pool.submit(self._worker_loop, i)

    def _worker_loop(self, worker_id):
        set_thread_priority(THREAD_PRIORITY_NORMAL)

        while True:
            # P2 우선 처리
            p2_batch = collect_batch(self.p2_queue, max_size=50, timeout_ms=100)
            if p2_batch:
                self._process_p2_batch(p2_batch)
                continue

            # P2 비어있으면 P3 처리
            p3_batch = collect_batch(self.p3_queue, max_size=100, timeout_ms=1000)
            if p3_batch:
                self._process_p3_batch(p3_batch)
```

---

## **5.5 리소스 할당 가이드라인**

```python
RESOURCE_ALLOCATION = {
    "cpu_cores": {
        "p0_handler": 1,        # 1개 코어 전용
        "p1_handlers": 1,       # 1개 코어 공유
        "p2_p3_workers": 2,     # 2개 코어 공유
        "scheduler": 0.5        # 0.5 코어 (공유)
    },

    "memory_mb": {
        "p0_queue": 10,
        "p1_queue": 100,
        "p2_queue": 200,
        "p3_queue": 500,
        "handlers": 256
    },

    "thread_count": {
        "p0_handler": 1,
        "p1_handlers": 2,
        "p2_p3_workers": 4,
        "scheduler": 1
    }
}
```

---

# **6. ETEDA Integration**

## **6.1 파이프라인 이벤트 소스**

ETEDA 파이프라인에서 발생하는 이벤트:

| 단계 | 이벤트 | 우선순위 |
|------|--------|----------|
| Extract | `EXTRACT_COMPLETE` | P2 |
| Transform | `TRANSFORM_COMPLETE` | P2 |
| Evaluate | `STRATEGY_SIGNAL` | P2 |
| Decide | `ORDER_DECISION` | P2 |
| Act | `ORDER_SENT` | P0 |
| Act | `FILL_RECEIVED` | P0 |
| Performance | `PERF_UPDATE` | P3 |

---

## **6.2 이벤트 기반 Act 단계**

Act 단계는 이벤트 기반으로 동작:

```python
def act_phase(order_decision):
    # 주문 전송 (P0 이벤트 생성)
    order_sent_event = P0Event(
        event_type="ORDER_SENT",
        payload=order_decision
    )
    dispatch_event(order_sent_event)

    # 체결 대기 (P0 이벤트 수신)
    fill_event = await_fill_event(timeout_ms=5000)

    if fill_event:
        return ExecutionResult(
            status="FILLED",
            fill_data=fill_event.payload
        )
    else:
        return ExecutionResult(status="TIMEOUT")
```

---

## **6.3 Micro Risk Loop과의 이벤트 조율**

```
┌─────────────────────────────────────────────────────────────────────┐
│               EVENT COORDINATION WITH MICRO RISK LOOP               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  P0 Queue                                                           │
│      │                                                              │
│      ├──▶ [FILL_CONFIRMED] ──▶ Position Update ──▶ Micro Risk Loop │
│      │                                                              │
│      ├──▶ [PRICE_TICK] ──▶ Micro Risk Loop (병렬)                  │
│      │                                                              │
│      └──▶ [EMERGENCY_STOP] ──▶ ETEDA Suspend + Micro Risk          │
│                                                                      │
│  Micro Risk Loop                                                    │
│      │                                                              │
│      ├──▶ [TRAILING_STOP_HIT] ──▶ P0 Queue (긴급 청산)             │
│      │                                                              │
│      └──▶ [ETEDA_SUSPEND] ──▶ ETEDA Scheduler                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

# **7. Monitoring & Alerting**

## **7.1 큐 깊이 모니터링**

```python
QUEUE_MONITORING = {
    "check_interval_ms": 100,

    "alerts": {
        "p0_queue_depth": {
            "warning": 50,
            "critical": 80
        },
        "p1_queue_depth": {
            "warning": 7000,
            "critical": 9000
        },
        "p2_queue_depth": {
            "warning": 800,
            "critical": 950
        }
    }
}

def monitor_queues():
    for queue_id, queue in queues.items():
        depth = queue.qsize()
        thresholds = QUEUE_MONITORING["alerts"][f"{queue_id}_queue_depth"]

        if depth > thresholds["critical"]:
            trigger_alert(f"CRITICAL: {queue_id} depth {depth}")
        elif depth > thresholds["warning"]:
            trigger_alert(f"WARNING: {queue_id} depth {depth}")
```

---

## **7.2 레이턴시 추적**

```python
class LatencyTracker:
    def __init__(self):
        self.histograms = {
            "P0": Histogram(),
            "P1": Histogram(),
            "P2": Histogram(),
            "P3": Histogram()
        }

    def record(self, priority, latency_ms):
        self.histograms[priority].record(latency_ms)

    def get_percentiles(self, priority):
        h = self.histograms[priority]
        return {
            "p50": h.percentile(50),
            "p95": h.percentile(95),
            "p99": h.percentile(99),
            "max": h.max()
        }

    def check_sla_violations(self):
        violations = []

        if self.get_percentiles("P0")["p99"] > 10:
            violations.append("P0 p99 > 10ms")

        if self.get_percentiles("P1")["p99"] > 50:
            violations.append("P1 p99 > 50ms")

        return violations
```

---

## **7.3 오버플로우 알림**

```python
def overflow_alert_handler(queue_id, event, reason):
    alert = {
        "type": "QUEUE_OVERFLOW",
        "queue": queue_id,
        "event_type": event.event_type,
        "reason": reason,
        "timestamp": now(),
        "queue_size": queues[queue_id].qsize()
    }

    if queue_id == "P0":
        # P0 오버플로우는 심각한 상황
        trigger_fail_safe("FS095", f"P0 queue overflow: {reason}")
    else:
        log_warning(alert)
        increment_metric(f"{queue_id}_overflow_count")
```

---

## **7.4 대시보드 통합**

R_Dash에 표시되는 이벤트 상태:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EVENT SYSTEM STATUS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Queue Status:                                                      │
│  ┌──────────┬─────────┬─────────┬─────────┐                        │
│  │ Priority │  Depth  │ Max     │ Status  │                        │
│  ├──────────┼─────────┼─────────┼─────────┤                        │
│  │ P0       │  12     │ 100     │ OK      │                        │
│  │ P1       │  3,421  │ 10,000  │ OK      │                        │
│  │ P2       │  523    │ 1,000   │ OK      │                        │
│  │ P3       │  15,234 │ 50,000  │ OK      │                        │
│  └──────────┴─────────┴─────────┴─────────┘                        │
│                                                                      │
│  Latency (p99):                                                     │
│  P0: 8ms  │  P1: 42ms  │  P2: 380ms  │  P3: 2,100ms               │
│                                                                      │
│  Events/sec: P0: 150 | P1: 5,200 | P2: 320 | P3: 1,800             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

# **8. Failure Handling**

## **8.1 큐 실패 복구**

```python
def handle_queue_failure(queue_id, error):
    if queue_id == "P0":
        # P0 큐 실패는 치명적
        trigger_fail_safe(
            code="FS096",
            message=f"P0 queue failure: {error}"
        )
        suspend_trading()

    elif queue_id == "P1":
        # P1 큐 재생성 시도
        try:
            queues["P1"] = recreate_queue("P1", P1_RULES)
            log_warning(f"P1 queue recreated after failure: {error}")
        except Exception:
            trigger_fail_safe("FS097", "P1 queue recreation failed")

    else:
        # P2/P3는 재시작으로 복구
        queues[queue_id] = recreate_queue(queue_id)
        log_info(f"{queue_id} queue recreated")
```

---

## **8.2 핸들러 실패 복구**

```python
def handle_handler_failure(handler_id, error, event):
    # 이벤트 재처리 큐에 추가
    if event.retry_count < event.max_retries:
        event.retry_count += 1
        requeue_event(event)
        log_warning(f"Handler {handler_id} failed, retry {event.retry_count}")
    else:
        # 재시도 초과
        log_error(f"Handler {handler_id} failed permanently: {error}")
        dead_letter_queue.put(event)

        if event.priority == "P0":
            trigger_fail_safe("FS098", "P0 handler permanent failure")
```

---

## **8.3 시스템 저하 모드 (Degradation)**

```python
DEGRADATION_LEVELS = {
    "LEVEL_0": "NORMAL",           # 정상 운영
    "LEVEL_1": "P3_PAUSED",        # P3 일시 중지
    "LEVEL_2": "P2_P3_PAUSED",     # P2/P3 일시 중지
    "LEVEL_3": "CRITICAL_ONLY"     # P0만 처리
}

def enter_degradation_mode(level):
    if level == "LEVEL_1":
        pause_p3_processing()
        log_warning("Degradation: P3 paused")

    elif level == "LEVEL_2":
        pause_p3_processing()
        pause_p2_processing()
        log_warning("Degradation: P2/P3 paused")

    elif level == "LEVEL_3":
        pause_all_except_p0()
        log_critical("Degradation: P0 only mode")
        trigger_guardrail("GR090", "System in critical-only mode")
```

---

# **9. Testability**

## **9.1 우선순위 스케줄링 테스트**

```python
class TestPriorityScheduling:
    def test_p0_preempts_p2(self):
        # P2 이벤트 처리 중 P0 도착
        start_p2_processing()
        inject_p0_event()

        # P0이 먼저 처리되어야 함
        assert get_last_processed_priority() == "P0"

    def test_p0_never_dropped(self):
        # P0 큐 가득 채우기
        for i in range(100):
            inject_p0_event()

        # 추가 P0 이벤트는 블로킹
        start = time()
        inject_p0_event()  # 이게 블로킹되어야 함
        elapsed = time() - start

        assert elapsed > 0.001  # 최소 1ms 대기
```

---

## **9.2 레이턴시 격리 테스트**

```python
class TestLatencyIsolation:
    def test_p3_does_not_block_p0(self):
        # 느린 P3 핸들러
        register_slow_p3_handler(delay_ms=5000)

        # P0 이벤트 주입
        inject_p0_event()
        latency = measure_p0_latency()

        # P0 레이턴시가 P3에 영향받지 않아야 함
        assert latency < 10  # 10ms 이내

    def test_p0_latency_under_load(self):
        # 부하 상황 생성
        flood_p2_events(count=10000)
        flood_p3_events(count=50000)

        # P0 레이턴시 측정
        latencies = []
        for i in range(100):
            inject_p0_event()
            latencies.append(measure_p0_latency())

        assert max(latencies) < 15  # 최대 15ms
        assert percentile(latencies, 99) < 10
```

---

# **10. Appendix**

## **10.1 Event Type Catalog**

| Event Type | Priority | Source | Description |
|------------|----------|--------|-------------|
| `FILL_CONFIRMED` | P0 | Broker | 주문 체결 확인 |
| `FILL_PARTIAL` | P0 | Broker | 부분 체결 |
| `ORDER_REJECTED` | P0 | Broker | 주문 거부 |
| `POSITION_UPDATE` | P0 | System | 포지션 변경 |
| `EMERGENCY_STOP` | P0 | Safety | 긴급 정지 |
| `PRICE_TICK` | P1 | Market | 가격 틱 |
| `ORDERBOOK_UPDATE` | P1 | Market | 호가 업데이트 |
| `VIX_UPDATE` | P1 | Market | 변동성 지수 |
| `ETEDA_CYCLE_START` | P2 | Scheduler | ETEDA 시작 |
| `STRATEGY_SIGNAL` | P2 | Strategy | 매매 신호 |
| `DASHBOARD_UPDATE` | P3 | UI | 대시보드 갱신 |
| `LOG_WRITE` | P3 | Logger | 로그 기록 |

---

## **10.2 Queue Configuration**

```python
QUEUE_CONFIG = {
    "P0": {
        "type": "BoundedQueue",
        "capacity": 100,
        "overflow_policy": "BLOCK",
        "implementation": "ArrayBlockingQueue"
    },
    "P1": {
        "type": "RingBuffer",
        "capacity": 10000,
        "overflow_policy": "DROP_OLDEST",
        "implementation": "CircularBuffer"
    },
    "P2": {
        "type": "PriorityQueue",
        "capacity": 1000,
        "overflow_policy": "COLLAPSE",
        "implementation": "HeapQueue"
    },
    "P3": {
        "type": "UnboundedQueue",
        "max_capacity": 50000,
        "overflow_policy": "SAMPLE",
        "sample_rate": 0.1,
        "implementation": "LinkedQueue"
    }
}
```

---

## **10.3 Latency SLA Table**

| Priority | Target p50 | Target p95 | Target p99 | Max |
|----------|------------|------------|------------|-----|
| P0 | 2ms | 5ms | 10ms | 20ms |
| P1 | 10ms | 30ms | 50ms | 100ms |
| P2 | 100ms | 300ms | 500ms | 1000ms |
| P3 | - | - | - | Best effort |

---

**QTS Event Priority Architecture v1.0.0 — 완료됨**
