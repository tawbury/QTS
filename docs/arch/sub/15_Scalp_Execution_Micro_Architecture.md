# ============================================================
# QTS Scalp Execution Micro-Architecture
# ============================================================

Version: v1.0.0
Status: Architecture Specification (Final)
Author: 타우
Last Updated: 2026-01-30

문서 목적:
본 문서는 QTS의 **Scalp 실행 마이크로 아키텍처**를 정의한다.
ETEDA 파이프라인의 Act 단계를 Scalp 전략 전용으로 확장하여
6개의 세부 단계(PreCheck → OrderSplit → AsyncSend → PartialFillMonitor →
AdaptiveAdjust → EmergencyEscape)로 구성한다.
실행 로직은 전략 로직과 완전히 분리된다.

---

# **1. Overview**

## **1.1 목적**

Scalp Execution Micro-Architecture는 다음 목표를 수행한다.

1. Scalp 전략의 초고속 실행 지원
2. 대량 주문의 분할 실행 (시장 충격 최소화)
3. 부분 체결 실시간 모니터링
4. 적응적 가격 조정
5. 긴급 탈출 메커니즘
6. 실행 로직과 전략 로직의 완전 분리

---

## **1.2 범위**

포함:

- 6단계 실행 파이프라인 (PreCheck → ... → EmergencyEscape)
- 실행 상태 머신
- 브로커 레이어 통합
- Safety 연계
- 레이턴시 요구사항

제외:

- 전략 신호 생성 (Strategy Engine 참조)
- 리스크 승인 (Risk Engine 참조)
- 포지션 사이징 (Portfolio Engine 참조)
- 메인 ETEDA 파이프라인 (03_Pipeline_ETEDA_Architecture 참조)

---

## **1.3 설계 원칙**

1. **실행은 전략과 분리된다.**
   실행 로직은 "어떻게" 주문을 처리할지만 담당한다.
   "무엇을" 거래할지는 전략이 결정한다.

2. **각 단계는 실패 가능하다.**
   모든 단계는 실패 시 복구 경로가 정의되어야 한다.

3. **부분 체결은 정상이다.**
   부분 체결은 오류가 아니라 정상적인 시장 행동이다.

4. **긴급 탈출은 항상 가능해야 한다.**
   어떤 상태에서도 EmergencyEscape가 실행 가능해야 한다.

5. **P0 우선순위로 실행된다.**
   Scalp 실행 이벤트는 최고 우선순위(P0)로 처리된다.

**Execution vs Risk Authority.** Execution은 Risk 권한 하에 동작한다. Micro Risk Loop가 긴급 액션을 트리거하면 Execution은 즉시 제어를 양보해야 하며, 부분 체결 처리도 안전하게 중단해야 한다. 우선순위 규칙: **Micro Risk Loop > Execution > ETEDA**.

---

## **1.4 관련 문서**

- **Main Architecture**: [../00_Architecture.md](../00_Architecture.md)
- **ETEDA Pipeline**: [../03_Pipeline_ETEDA_Architecture.md](../03_Pipeline_ETEDA_Architecture.md)
- **Broker Integration**: [../08_Broker_Integration_Architecture.md](../08_Broker_Integration_Architecture.md)
- **Fail-Safe & Safety**: [../07_FailSafe_Architecture.md](../07_FailSafe_Architecture.md)
- **Event Priority**: [17_Event_Priority_Architecture.md](./17_Event_Priority_Architecture.md)
- **Micro Risk Loop**: [16_Micro_Risk_Loop_Architecture.md](./16_Micro_Risk_Loop_Architecture.md)
- **Caching Architecture**: [19_Caching_Architecture.md](./19_Caching_Architecture.md)

---

# **2. Execution Sub-Stage Pipeline**

## **2.1 파이프라인 개요**

```
┌─────────────────────────────────────────────────────────────────────┐
│             SCALP EXECUTION MICRO-PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ETEDA Decide Phase                                                 │
│       │                                                              │
│       │ OrderDecision (Scalp)                                       │
│       ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐  │  │
│  │  │ Stage 1 │──▶│ Stage 2 │──▶│ Stage 3 │──▶│   Stage 4   │  │  │
│  │  │PreCheck │   │OrderSplit│  │AsyncSend│   │ PartialFill │  │  │
│  │  │         │   │         │   │         │   │  Monitor    │  │  │
│  │  └─────────┘   └─────────┘   └─────────┘   └──────┬──────┘  │  │
│  │                                                    │         │  │
│  │                                    ┌───────────────┘         │  │
│  │                                    │                         │  │
│  │                                    ▼                         │  │
│  │                            ┌─────────────┐   ┌───────────┐  │  │
│  │                            │   Stage 5   │──▶│  Stage 6  │  │  │
│  │                            │ Adaptive    │   │ Emergency │  │  │
│  │                            │  Adjust     │   │  Escape   │  │  │
│  │                            └─────────────┘   └───────────┘  │  │
│  │                                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│       │                                                              │
│       ▼                                                              │
│  ExecutionResult                                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **2.2 Stage 1: PreCheck**

### **2.2.1 목적**

주문 실행 전 모든 전제 조건을 검증한다.

### **2.2.2 검증 항목**

| 항목 | 검증 내용 | 실패 시 동작 |
|------|----------|-------------|
| 포지션 유효성 | 중복 주문 방지, 포지션 상태 확인 | 주문 취소 |
| 자본 가용성 | Scalp Pool 가용 자본 확인 | 주문 축소/취소 |
| 브로커 연결 | 브로커 API 연결 상태 | 재연결 시도/취소 |
| 시장 상태 | 장중 여부, 거래 가능 여부 | 대기/취소 |
| 리스크 재확인 | 최종 리스크 한도 재확인 | 주문 조정/취소 |

### **2.2.3 PreCheck 로직**

```python
class PreCheckStage:
    def execute(self, order: OrderDecision) -> PreCheckResult:
        checks = []

        # 1. 포지션 유효성
        position_check = self.check_position_validity(order)
        checks.append(position_check)
        if not position_check.passed:
            return PreCheckResult(passed=False, reason="POSITION_INVALID")

        # 2. 자본 가용성
        capital_check = self.check_capital_availability(order)
        checks.append(capital_check)
        if not capital_check.passed:
            if capital_check.available_qty > 0:
                order.qty = capital_check.available_qty  # 축소
            else:
                return PreCheckResult(passed=False, reason="INSUFFICIENT_CAPITAL")

        # 3. 브로커 연결
        broker_check = self.check_broker_connection(order)
        checks.append(broker_check)
        if not broker_check.passed:
            if self.attempt_reconnect():
                broker_check.passed = True
            else:
                return PreCheckResult(passed=False, reason="BROKER_DISCONNECTED")

        # 4. 시장 상태
        market_check = self.check_market_status(order)
        checks.append(market_check)
        if not market_check.passed:
            return PreCheckResult(passed=False, reason="MARKET_CLOSED")

        # 5. 리스크 재확인
        risk_check = self.recheck_risk_limits(order)
        checks.append(risk_check)
        if not risk_check.passed:
            return PreCheckResult(passed=False, reason="RISK_LIMIT_EXCEEDED")

        return PreCheckResult(passed=True, order=order)
```

### **2.2.4 PreCheck 계약**

```python
PreCheckResult = {
    "passed": True,
    "order": OrderDecision,
    "checks": [
        {"name": "POSITION", "passed": True},
        {"name": "CAPITAL", "passed": True, "available_qty": 100},
        {"name": "BROKER", "passed": True},
        {"name": "MARKET", "passed": True},
        {"name": "RISK", "passed": True}
    ],
    "timestamp": "2026-01-30T09:30:00.010Z"
}
```

---

## **2.3 Stage 2: OrderSplit**

### **2.3.1 목적**

대량 주문을 작은 단위로 분할하여 시장 충격을 최소화한다.

### **2.3.2 분할 전략**

| 전략 | 설명 | 사용 조건 |
|------|------|----------|
| VWAP 분할 | 거래량 가중 평균가 추종 | 대량 주문, 유동성 충분 |
| TWAP 분할 | 시간 균등 분할 | 시간 제약 있는 주문 |
| Iceberg 분할 | 호가창에 일부만 노출 | 시장 영향 최소화 |
| Single | 분할 없이 단일 주문 | 소량 주문 |

### **2.3.3 분할 알고리즘**

```python
class OrderSplitStage:
    def execute(self, order: OrderDecision, config: SplitConfig) -> SplitResult:
        total_qty = order.qty
        symbol = order.symbol

        # 분할 필요 여부 판단
        if total_qty <= config.min_split_qty:
            return SplitResult(
                strategy="SINGLE",
                splits=[SplitOrder(qty=total_qty, price=order.price)]
            )

        # 분할 전략 선택
        strategy = self.select_split_strategy(order, config)

        if strategy == "VWAP":
            splits = self.vwap_split(order, config)
        elif strategy == "TWAP":
            splits = self.twap_split(order, config)
        elif strategy == "ICEBERG":
            splits = self.iceberg_split(order, config)
        else:
            splits = [SplitOrder(qty=total_qty, price=order.price)]

        return SplitResult(strategy=strategy, splits=splits)

    def vwap_split(self, order, config) -> List[SplitOrder]:
        """VWAP 기반 분할"""
        total_qty = order.qty
        volume_profile = get_intraday_volume_profile(order.symbol)

        splits = []
        remaining = total_qty

        for bucket in volume_profile.buckets:
            if remaining <= 0:
                break

            # 해당 시간대 거래량 비중에 따라 분할
            bucket_qty = int(total_qty * bucket.volume_pct)
            bucket_qty = min(bucket_qty, remaining)

            if bucket_qty > 0:
                splits.append(SplitOrder(
                    qty=bucket_qty,
                    price=None,  # 시장가 또는 적응적 가격
                    scheduled_time=bucket.time,
                    max_wait_ms=bucket.duration_ms
                ))
                remaining -= bucket_qty

        return splits
```

### **2.3.4 SplitOrder 계약**

```python
SplitOrder = {
    "split_id": "uuid",
    "parent_order_id": "parent_uuid",
    "sequence": 1,                    # 1, 2, 3...
    "qty": 50,
    "price": 75000,                   # None = 시장가
    "price_type": "LIMIT",            # MARKET / LIMIT
    "scheduled_time": "2026-01-30T09:30:30Z",
    "max_wait_ms": 5000,              # 최대 대기 시간
    "status": "PENDING"               # PENDING / SENT / FILLED / CANCELLED
}
```

---

## **2.4 Stage 3: AsyncSend**

### **2.4.1 목적**

분할된 주문을 비동기로 브로커에 전송한다.

### **2.4.2 비동기 전송 모델**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ASYNC SEND MODEL                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Split Orders                                                       │
│      │                                                              │
│      ├──▶ [Order 1] ──▶ ┌─────────┐ ──▶ Broker API ──▶ ACK        │
│      │                  │ Async   │                                │
│      ├──▶ [Order 2] ──▶ │ Queue   │ ──▶ Broker API ──▶ ACK        │
│      │                  │         │                                │
│      └──▶ [Order 3] ──▶ └─────────┘ ──▶ Broker API ──▶ ACK        │
│                                                                      │
│  ACK = Order Acknowledged (주문 접수)                               │
│  → 체결(Fill)은 Stage 4에서 모니터링                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### **2.4.3 전송 로직**

```python
class AsyncSendStage:
    def __init__(self, broker_adapter):
        self.broker = broker_adapter
        self.pending_orders = {}
        self.retry_config = RetryConfig(max_retries=3, backoff_ms=100)

    async def execute(self, splits: List[SplitOrder]) -> SendResult:
        tasks = []

        for split in splits:
            task = asyncio.create_task(self.send_single(split))
            tasks.append(task)

        # 모든 전송 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return SendResult(
            sent_count=sum(1 for r in results if r.success),
            failed_count=sum(1 for r in results if not r.success),
            orders=results
        )

    async def send_single(self, split: SplitOrder) -> SingleSendResult:
        for attempt in range(self.retry_config.max_retries):
            try:
                # 브로커에 주문 전송
                ack = await self.broker.send_order_async(
                    symbol=split.symbol,
                    side=split.side,
                    qty=split.qty,
                    price=split.price,
                    order_type=split.price_type
                )

                if ack.accepted:
                    split.status = "SENT"
                    split.broker_order_id = ack.order_id
                    self.pending_orders[ack.order_id] = split
                    return SingleSendResult(success=True, order_id=ack.order_id)

                else:
                    log_warning(f"Order rejected: {ack.reject_reason}")

            except Exception as e:
                log_error(f"Send failed attempt {attempt+1}: {e}")
                await asyncio.sleep(self.retry_config.backoff_ms / 1000)

        split.status = "FAILED"
        return SingleSendResult(success=False, error="MAX_RETRIES_EXCEEDED")
```

### **2.4.4 전송 실패 처리**

```python
def handle_send_failure(split: SplitOrder, error: str):
    """전송 실패 처리"""

    if error == "BROKER_DISCONNECTED":
        # 재연결 후 재시도
        if reconnect_broker():
            return retry_send(split)

    elif error == "INSUFFICIENT_BALANCE":
        # 자본 부족 - 전체 실행 중단
        trigger_guardrail("GR061", "Insufficient balance during send")
        return cancel_remaining_splits()

    elif error == "SYMBOL_NOT_FOUND":
        # 잘못된 종목 - Fail-Safe
        trigger_fail_safe("FS091", f"Invalid symbol: {split.symbol}")
        return abort_execution()

    else:
        # 기타 오류 - 로그 후 계속
        log_error(f"Send failure: {error}")
        return skip_split(split)
```

---

## **2.5 Stage 4: PartialFillMonitor**

### **2.5.1 목적**

전송된 주문의 체결 상태를 실시간으로 모니터링한다.

### **2.5.2 체결 상태 모델**

```
전송된 주문 수량: 100주

┌─────────────────────────────────────────────────────────────────────┐
│  시간 ──▶                                                           │
│                                                                      │
│  ├────────┼────────┼────────┼────────┼────────┤                    │
│  │ 10주   │ 30주   │ 20주   │ 25주   │ 15주   │                    │
│  │ 체결   │ 체결   │ 체결   │ 체결   │ 체결   │                    │
│  ├────────┼────────┼────────┼────────┼────────┤                    │
│  t=0     t=1s     t=2s     t=3s     t=4s                           │
│                                                                      │
│  누적 체결: 10 → 40 → 60 → 85 → 100 (완료)                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### **2.5.3 모니터링 로직**

```python
class PartialFillMonitorStage:
    def __init__(self, config):
        self.config = config
        self.fill_buffer = {}  # order_id -> List[Fill]

    async def execute(self, sent_orders: List[SplitOrder]) -> MonitorResult:
        total_qty = sum(o.qty for o in sent_orders)
        filled_qty = 0
        start_time = now()

        while filled_qty < total_qty:
            # 타임아웃 체크
            elapsed = (now() - start_time).total_seconds() * 1000
            if elapsed > self.config.timeout_ms:
                return MonitorResult(
                    status="TIMEOUT",
                    filled_qty=filled_qty,
                    remaining_qty=total_qty - filled_qty
                )

            # 체결 이벤트 대기
            fill_event = await self.wait_for_fill(timeout_ms=100)

            if fill_event:
                # 체결 집계
                self.aggregate_fill(fill_event)
                filled_qty = self.get_total_filled_qty()

                # 진행률 로그
                progress = filled_qty / total_qty * 100
                log_info(f"Fill progress: {filled_qty}/{total_qty} ({progress:.1f}%)")

        return MonitorResult(
            status="COMPLETE",
            filled_qty=filled_qty,
            fills=self.get_all_fills()
        )

    def aggregate_fill(self, fill_event):
        """체결 이벤트 집계"""
        order_id = fill_event.order_id

        if order_id not in self.fill_buffer:
            self.fill_buffer[order_id] = []

        self.fill_buffer[order_id].append(Fill(
            qty=fill_event.filled_qty,
            price=fill_event.filled_price,
            timestamp=fill_event.timestamp
        ))
```

### **2.5.4 타임아웃 처리**

```python
def handle_fill_timeout(result: MonitorResult):
    """체결 타임아웃 처리"""

    remaining = result.remaining_qty

    if remaining > 0:
        # 미체결 수량이 있음
        log_warning(f"Fill timeout: {remaining} shares unfilled")

        if result.filled_qty > 0:
            # 부분 체결 - 미체결 분은 취소
            cancel_unfilled_orders()
            return result.with_status("PARTIAL")
        else:
            # 전혀 체결 안됨 - Stage 5로 이동
            return result.with_status("NEEDS_ADJUSTMENT")
```

---

## **2.6 Stage 5: AdaptiveAdjust**

### **2.6.1 목적**

미체결 수량에 대해 가격을 조정하여 체결을 유도한다.

### **2.6.2 조정 전략**

| 전략 | 설명 | 조건 |
|------|------|------|
| 가격 개선 | 제한가를 시장가 방향으로 조정 | 부분 체결, 시간 여유 |
| 시장가 전환 | 제한가 → 시장가 | 긴급 체결 필요 |
| 수량 조정 | 미체결 수량 감소 | 자본 제약 |
| 대기 | 현재 가격 유지 | 가격 회복 기대 |

### **2.6.3 조정 로직**

```python
class AdaptiveAdjustStage:
    def execute(self, unfilled_orders: List[SplitOrder], market_data) -> AdjustResult:
        adjustments = []

        for order in unfilled_orders:
            # 조정 전략 결정
            strategy = self.select_adjustment_strategy(order, market_data)

            if strategy == "PRICE_IMPROVE":
                new_price = self.calculate_improved_price(order, market_data)
                adjustment = self.modify_order_price(order, new_price)

            elif strategy == "CONVERT_MARKET":
                adjustment = self.convert_to_market_order(order)

            elif strategy == "REDUCE_QTY":
                new_qty = self.calculate_reduced_qty(order)
                adjustment = self.modify_order_qty(order, new_qty)

            elif strategy == "WAIT":
                adjustment = AdjustAction(action="WAIT", order=order)

            adjustments.append(adjustment)

        return AdjustResult(adjustments=adjustments)

    def calculate_improved_price(self, order, market_data):
        """가격 개선 계산"""
        current_price = order.price
        best_ask = market_data.best_ask
        best_bid = market_data.best_bid

        if order.side == "BUY":
            # 매수: 가격 상향 조정 (최대 best_ask까지)
            improved = min(
                current_price * (1 + self.config.price_improve_pct),
                best_ask
            )
        else:
            # 매도: 가격 하향 조정 (최소 best_bid까지)
            improved = max(
                current_price * (1 - self.config.price_improve_pct),
                best_bid
            )

        return improved
```

### **2.6.4 슬리피지 허용 범위**

```python
SlippageConfig = {
    "max_slippage_pct": 0.005,        # 최대 0.5% 슬리피지 허용
    "price_improve_step_pct": 0.001,  # 0.1%씩 가격 조정
    "max_adjustment_rounds": 3,        # 최대 3회 조정
    "adjust_interval_ms": 1000         # 1초마다 재평가
}
```

---

## **2.7 Stage 6: EmergencyEscape**

### **2.7.1 목적**

긴급 상황 시 모든 미체결 주문을 취소하고 포지션을 즉시 청산한다.

### **2.7.2 트리거 조건**

| 조건 | 동작 |
|------|------|
| 손실 임계값 초과 | 즉시 시장가 청산 |
| 시간 제한 초과 | 미체결 취소 + 시장가 청산 |
| 브로커 연결 불안정 | 미체결 취소 |
| Safety FAIL 상태 | 전량 청산 |
| 수동 트리거 | 즉시 탈출 |

### **2.7.3 탈출 로직**

```python
class EmergencyEscapeStage:
    def execute(self, context: ExecutionContext, reason: str) -> EscapeResult:
        log_warning(f"Emergency escape triggered: {reason}")

        # 1. 모든 미체결 주문 취소
        cancelled = self.cancel_all_pending_orders(context)

        # 2. 보유 포지션 즉시 청산
        if context.has_position():
            liquidation = self.execute_market_liquidation(context)
        else:
            liquidation = None

        # 3. Safety 통보
        self.notify_safety(
            code="FS092",
            message=f"Emergency escape: {reason}",
            context=context
        )

        # 4. ETEDA 일시 정지 (선택적)
        if reason in ["SAFETY_FAIL", "BROKER_DISCONNECT"]:
            self.request_eteda_suspend()

        return EscapeResult(
            cancelled_orders=cancelled,
            liquidation=liquidation,
            reason=reason,
            timestamp=now()
        )

    def execute_market_liquidation(self, context):
        """시장가 즉시 청산"""
        position = context.current_position

        order = EmergencyOrder(
            symbol=position.symbol,
            side="SELL" if position.qty > 0 else "BUY",
            qty=abs(position.qty),
            order_type="MARKET",
            reason="EMERGENCY_ESCAPE"
        )

        # P0 이벤트로 전송
        dispatch_p0_event(P0Event(
            event_type="EMERGENCY_ORDER",
            payload=order
        ))

        return order
```

### **2.7.4 탈출 결과 계약**

```python
EscapeResult = {
    "success": True,
    "reason": "TIME_LIMIT_EXCEEDED",
    "cancelled_orders": [
        {"order_id": "uuid1", "status": "CANCELLED"},
        {"order_id": "uuid2", "status": "CANCELLED"}
    ],
    "liquidation": {
        "order_id": "uuid3",
        "qty": 100,
        "side": "SELL",
        "status": "FILLED",
        "filled_price": 74800
    },
    "total_loss": -20000,
    "timestamp": "2026-01-30T09:35:00Z"
}
```

---

# **3. Execution State Machine**

## **3.1 상태 정의**

```python
ExecutionState = Enum(
    "INIT",           # 초기 상태
    "PRECHECK",       # PreCheck 진행 중
    "SPLITTING",      # OrderSplit 진행 중
    "SENDING",        # AsyncSend 진행 중
    "MONITORING",     # PartialFillMonitor 진행 중
    "ADJUSTING",      # AdaptiveAdjust 진행 중
    "ESCAPING",       # EmergencyEscape 진행 중
    "COMPLETE",       # 정상 완료
    "ESCAPED",        # 긴급 탈출 완료
    "FAILED"          # 실패
)
```

---

## **3.2 상태 전이 다이어그램**

```
┌─────────────────────────────────────────────────────────────────────┐
│                  EXECUTION STATE MACHINE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────┐                                                         │
│  │  INIT  │                                                         │
│  └───┬────┘                                                         │
│      │ OrderDecision received                                       │
│      ▼                                                               │
│  ┌────────────┐                                                     │
│  │  PRECHECK  │───────────────────────────────────┐                │
│  └─────┬──────┘ failed                            │                │
│        │ passed                                   ▼                │
│        ▼                                     ┌────────┐            │
│  ┌────────────┐                              │ FAILED │            │
│  │ SPLITTING  │                              └────────┘            │
│  └─────┬──────┘                                   ▲                │
│        │                                          │                │
│        ▼                                          │                │
│  ┌────────────┐                                   │                │
│  │  SENDING   │───────────────────────────────────┤                │
│  └─────┬──────┘ all failed                        │                │
│        │ some sent                                │                │
│        ▼                                          │                │
│  ┌────────────┐                                   │                │
│  │ MONITORING │───────────────────────────────────┤                │
│  └─────┬──────┘ timeout + 0 filled                │                │
│        │                                          │                │
│   ┌────┴────┐                                     │                │
│   │         │                                     │                │
│   ▼         ▼                                     │                │
│ filled   unfilled                                 │                │
│   │         │                                     │                │
│   │         ▼                                     │                │
│   │    ┌────────────┐                             │                │
│   │    │ ADJUSTING  │─────────────────────────────┤                │
│   │    └─────┬──────┘ max adjustments             │                │
│   │          │                                    │                │
│   │    ┌─────┴─────┐                              │                │
│   │    │           │                              │                │
│   │    ▼           ▼                              │                │
│   │  adjusted    still unfilled                   │                │
│   │    │           │                              │                │
│   │    │           ▼                              │                │
│   │    │      ┌────────────┐                      │                │
│   │    │      │  ESCAPING  │──────────────────────┘                │
│   │    │      └─────┬──────┘                                       │
│   │    │            │                                              │
│   │    │            ▼                                              │
│   │    │       ┌─────────┐                                         │
│   │    │       │ ESCAPED │                                         │
│   │    │       └─────────┘                                         │
│   │    │                                                           │
│   └────┴───────────▶ ┌──────────┐                                  │
│                      │ COMPLETE │                                  │
│                      └──────────┘                                  │
│                                                                      │
│  * 모든 상태에서 ESCAPING으로 즉시 전이 가능 (Emergency 트리거)    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **3.3 상태 전이 규칙**

```python
STATE_TRANSITIONS = {
    "INIT": ["PRECHECK"],
    "PRECHECK": ["SPLITTING", "FAILED", "ESCAPING"],
    "SPLITTING": ["SENDING", "FAILED", "ESCAPING"],
    "SENDING": ["MONITORING", "FAILED", "ESCAPING"],
    "MONITORING": ["COMPLETE", "ADJUSTING", "ESCAPING"],
    "ADJUSTING": ["MONITORING", "ESCAPING"],
    "ESCAPING": ["ESCAPED"],
    "COMPLETE": [],  # 종료 상태
    "ESCAPED": [],   # 종료 상태
    "FAILED": []     # 종료 상태
}

def can_transition(current: ExecutionState, target: ExecutionState) -> bool:
    # Emergency Escape는 항상 가능
    if target == ExecutionState.ESCAPING:
        return current not in [ExecutionState.COMPLETE, ExecutionState.ESCAPED, ExecutionState.FAILED]

    return target.value in STATE_TRANSITIONS.get(current.value, [])
```

---

## **3.4 타임아웃 처리**

```python
STAGE_TIMEOUTS = {
    "PRECHECK": 5000,      # 5초
    "SPLITTING": 1000,     # 1초
    "SENDING": 10000,      # 10초
    "MONITORING": 60000,   # 60초
    "ADJUSTING": 30000,    # 30초
    "ESCAPING": 30000      # 30초
}

def handle_stage_timeout(state: ExecutionState, context: ExecutionContext):
    timeout_ms = STAGE_TIMEOUTS[state.value]

    if context.stage_elapsed_ms() > timeout_ms:
        log_warning(f"Stage {state.value} timeout after {timeout_ms}ms")

        if state == ExecutionState.MONITORING:
            # 모니터링 타임아웃 → 조정 시도
            return transition_to(ExecutionState.ADJUSTING)

        elif state == ExecutionState.ADJUSTING:
            # 조정 타임아웃 → 긴급 탈출
            return transition_to(ExecutionState.ESCAPING)

        else:
            # 기타 타임아웃 → 실패
            return transition_to(ExecutionState.FAILED)
```

---

## **3.5 롤백 절차**

```python
def rollback_execution(context: ExecutionContext, reason: str):
    """실행 롤백 - 미체결 취소, 체결분 유지"""

    # 1. 미체결 주문 취소
    for order in context.pending_orders:
        if order.status == "SENT":
            cancel_order(order)

    # 2. 체결된 내용 기록
    for fill in context.fills:
        record_fill_to_ledger(fill)

    # 3. 상태 정리
    context.status = "ROLLED_BACK"
    context.rollback_reason = reason

    log_info(f"Execution rolled back: {reason}")
```

---

# **4. Broker Layer Integration**

## **4.1 비동기 주문 인터페이스**

```python
class AsyncBrokerInterface(ABC):
    @abstractmethod
    async def send_order_async(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: float,
        order_type: str
    ) -> OrderAck:
        """비동기 주문 전송"""
        pass

    @abstractmethod
    async def modify_order_async(
        self,
        order_id: str,
        new_price: float = None,
        new_qty: int = None
    ) -> ModifyAck:
        """비동기 주문 수정"""
        pass

    @abstractmethod
    async def cancel_order_async(self, order_id: str) -> CancelAck:
        """비동기 주문 취소"""
        pass

    @abstractmethod
    def subscribe_fills(self, callback: Callable[[FillEvent], None]):
        """체결 이벤트 구독"""
        pass
```

---

## **4.2 부분 체결 콜백 계약**

```python
FillEvent = {
    "event_id": "uuid",
    "order_id": "broker_order_id",
    "symbol": "005930",
    "side": "BUY",
    "filled_qty": 50,
    "filled_price": 75100,
    "cumulative_qty": 75,      # 누적 체결 수량
    "remaining_qty": 25,       # 잔여 수량
    "fee": 375,
    "timestamp": "2026-01-30T09:30:15.500Z"
}
```

---

## **4.3 주문 상태 폴링 vs 푸시**

```python
FILL_NOTIFICATION_MODE = {
    "mode": "PUSH",            # PUSH (권장) 또는 POLL

    "push_config": {
        "websocket_enabled": True,
        "callback_timeout_ms": 100
    },

    "poll_config": {
        "poll_interval_ms": 100,
        "max_poll_duration_ms": 60000
    }
}
```

---

## **4.4 멀티 브로커 페일오버**

```python
class MultiBrokerFailover:
    def __init__(self, primary: BrokerAdapter, secondary: BrokerAdapter):
        self.primary = primary
        self.secondary = secondary
        self.active = primary

    async def send_order_with_failover(self, order):
        try:
            return await self.active.send_order_async(order)
        except BrokerConnectionError:
            log_warning("Primary broker failed, switching to secondary")
            self.active = self.secondary
            return await self.active.send_order_async(order)
```

---

# **5. Safety Integration**

## **5.1 Emergency Escape Triggers (FS090-FS099)**

| 코드 | 조건 | 동작 |
|------|------|------|
| FS090 | 전송 실패 (전체) | 실행 중단 |
| FS091 | 잘못된 종목 | 실행 중단, 조사 필요 |
| FS092 | Emergency Escape 실행 | 로그 및 알림 |
| FS093 | 체결 타임아웃 | 미체결 취소 |
| FS094 | 슬리피지 초과 | 조정 또는 중단 |
| FS095 | P0 큐 오버플로우 | 실행 일시 정지 |

---

## **5.2 Execution Guardrails (GR060-GR069)**

| 코드 | 조건 | 동작 |
|------|------|------|
| GR060 | 분할 주문 과다 | 분할 수 제한 |
| GR061 | 잔고 부족 | 수량 축소 |
| GR062 | 일일 거래 한도 | 추가 거래 차단 |
| GR063 | 슬리피지 경고 | 가격 조정 제한 |
| GR064 | 체결 지연 | 경고 로그 |

---

## **5.3 Micro Risk Loop 핸드오프**

```python
def handoff_to_micro_risk_loop(position):
    """체결 완료 후 Micro Risk Loop에 포지션 전달"""

    # 포지션 섀도우 생성
    shadow = PositionShadow(
        symbol=position.symbol,
        qty=position.qty,
        avg_price=position.avg_price,
        entry_time=now()
    )

    # Micro Risk Loop에 등록
    micro_risk_loop.register_position(shadow)

    # 트레일링 스탑 조건 확인
    if should_activate_trailing(position):
        shadow.trailing_stop_active = True
        shadow.trailing_stop_price = calculate_initial_stop(position)

    log_info(f"Position handed off to Micro Risk: {position.symbol}")
```

---

# **6. Latency Requirements**

## **6.1 단계별 목표 레이턴시**

| 단계 | 목표 p50 | 목표 p99 | 최대 |
|------|----------|----------|------|
| PreCheck | 2ms | 5ms | 10ms |
| OrderSplit | 1ms | 3ms | 5ms |
| AsyncSend | 10ms | 20ms | 50ms |
| PartialFillMonitor | - | - | 60s (전체) |
| AdaptiveAdjust | 5ms | 10ms | 20ms |
| EmergencyEscape | 5ms | 15ms | 30ms |

---

## **6.2 네트워크 레이턴시 예산**

```python
NETWORK_LATENCY_BUDGET = {
    "broker_api_call_ms": 20,        # 브로커 API 왕복
    "fill_notification_ms": 50,      # 체결 알림 수신
    "order_modification_ms": 30,     # 주문 수정

    "total_execution_target_ms": 100  # 전체 실행 목표 (체결 대기 제외)
}
```

---

## **6.3 모니터링 및 알림**

```python
def monitor_execution_latency(stage: str, latency_ms: float):
    record_latency(f"scalp_exec_{stage}", latency_ms)

    thresholds = LATENCY_THRESHOLDS[stage]

    if latency_ms > thresholds["critical"]:
        trigger_alert(f"CRITICAL: {stage} latency {latency_ms}ms")
    elif latency_ms > thresholds["warning"]:
        log_warning(f"{stage} latency elevated: {latency_ms}ms")
```

---

# **7. Testability**

## **7.1 단계별 단위 테스트**

```python
class TestPreCheckStage:
    def test_passes_when_all_valid(self):
        order = valid_order()
        result = PreCheckStage().execute(order)
        assert result.passed == True

    def test_fails_on_insufficient_capital(self):
        order = order_exceeding_capital()
        result = PreCheckStage().execute(order)
        assert result.passed == False
        assert result.reason == "INSUFFICIENT_CAPITAL"

class TestOrderSplitStage:
    def test_vwap_split_creates_multiple_orders(self):
        order = large_order(qty=1000)
        result = OrderSplitStage().execute(order, VWAPConfig())
        assert len(result.splits) > 1
        assert sum(s.qty for s in result.splits) == 1000
```

---

## **7.2 Mock 브로커 통합 테스트**

```python
class TestAsyncSendWithMock:
    def test_successful_send(self):
        mock_broker = MockBrokerAdapter(response=OrderAck(accepted=True))
        stage = AsyncSendStage(mock_broker)

        splits = [SplitOrder(qty=100, price=75000)]
        result = asyncio.run(stage.execute(splits))

        assert result.sent_count == 1
        assert result.failed_count == 0

    def test_retry_on_failure(self):
        mock_broker = MockBrokerAdapter(
            responses=[
                BrokerError("TIMEOUT"),
                BrokerError("TIMEOUT"),
                OrderAck(accepted=True)
            ]
        )
        stage = AsyncSendStage(mock_broker)

        result = asyncio.run(stage.execute([SplitOrder(qty=100)]))
        assert result.sent_count == 1
        assert mock_broker.call_count == 3
```

---

## **7.3 레이턴시 스트레스 테스트**

```python
class TestLatencyUnderLoad:
    def test_precheck_latency_under_load(self):
        latencies = []

        for i in range(1000):
            start = time_ns()
            PreCheckStage().execute(random_order())
            latencies.append((time_ns() - start) / 1_000_000)

        p99 = percentile(latencies, 99)
        assert p99 < 5, f"PreCheck p99 latency {p99}ms exceeds 5ms"
```

---

# **8. Redis Caching Integration**

## **8.1 Caching Requirements for Low-Latency Execution**

Scalp Execution은 레이턴시 목표 100ms (체결 제외) 달성을 위해 Redis 캐싱 계층이 필수적이다.

**현재 문제:**
- Google Sheets API 조회: 150-300ms
- PreCheck 단계 데이터 조회 시간 초과
- 목표 레이턴시 달성 불가

**해결 방안:**
- Redis In-Memory Cache
- Write-Through / Read-Through 전략
- TTL 기반 자동 무효화

---

## **8.2 Scalp Execution에서 필요한 캐시 데이터**

| Data Type | Cache Key | TTL | PreCheck 단계 사용 |
|-----------|-----------|-----|-------------------|
| 실시간 호가 | `price:{symbol}` | 50-100ms | ✓ |
| 포지션 정보 | `pos:{symbol}` | 1s | ✓ |
| 리스크 한도 | `risk:account` | 5s | ✓ |
| 주문 상태 | `ord:{order_id}` | 60s | Stage 4 |
| 호가창 스냅샷 | `book:{symbol}` | 50ms | Stage 5 |
| 전략 파라미터 | `strat:{id}` | 60s | - |

---

## **8.3 PreCheck Stage Cache Integration**

PreCheck 단계에서 Redis 캐시 활용:

```python
class PreCheckStage:
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache

    def execute(self, order: OrderDecision) -> PreCheckResult:
        # 1. Position Check (Redis 우선)
        position = self.cache.get_position(order.symbol)
        if not position:
            position = self.db.get_position(order.symbol)
            self.cache.set_position(order.symbol, position, ttl=1)

        # 2. Risk Limits Check (Redis 우선)
        risk_status = self.cache.get_risk_status()
        if not risk_status:
            risk_status = self.db.get_risk_status()
            self.cache.set_risk_status(risk_status, ttl=5)

        # 3. Price Check (Redis 필수 - 실시간)
        price = self.cache.get_price(order.symbol)
        if not price or price.is_stale(threshold_ms=100):
            raise PriceDataStaleError("Price data too old")

        # Perform checks...
        return PreCheckResult(passed=True, order=order)
```

---

## **8.4 Cache Data Structures**

```python
# Price Cache (Hash)
redis.hset("price:005930", mapping={
    "bid": "75000",
    "ask": "75100",
    "last": "75050",
    "volume": "1234567",
    "timestamp": "1706700000000"  # Unix timestamp ms
})
redis.expire("price:005930", 0.1)  # 100ms TTL

# Position Cache (Hash)
redis.hset("pos:005930", mapping={
    "qty": "100",
    "avg_price": "74500",
    "unrealized_pnl": "55000",
    "exposure_pct": "0.05"
})
redis.expire("pos:005930", 1)  # 1s TTL

# Risk Cache (Hash)
redis.hset("risk:account", mapping={
    "exposure_used": "0.45",
    "daily_pnl": "125000",
    "trade_count": "15",
    "remaining_limit": "0.55"
})
redis.expire("risk:account", 5)  # 5s TTL

# Orderbook Cache (Sorted Set)
redis.zadd("book:005930:bid", {
    "75000": 1000,  # price: volume
    "74900": 2500,
    "74800": 5000,
})
redis.zadd("book:005930:ask", {
    "75100": 800,
    "75200": 1500,
})
redis.expire("book:005930:bid", 0.05)  # 50ms TTL
```

---

## **8.5 Cache Update Strategies**

### **Write-Through (포지션, 주문 상태)**

주문 체결 시 DB와 캐시 동시 업데이트:

```python
async def update_position_on_fill(fill: Fill):
    # 1. DB 업데이트
    position = await db.update_position(fill)

    # 2. Cache 업데이트 (Write-Through)
    await redis.hset(
        f"pos:{fill.symbol}",
        mapping=position.to_cache_dict()
    )
    await redis.expire(f"pos:{fill.symbol}", 1)
```

### **Read-Through (리스크 한도, 전략 파라미터)**

캐시 미스 시 DB 조회 후 캐시 채움:

```python
async def get_risk_limits() -> RiskLimits:
    # 1. Try cache
    cached = await redis.hgetall("risk:account")
    if cached:
        return RiskLimits.from_cache(cached)

    # 2. Cache miss - fetch from DB
    limits = await db.get_risk_limits()

    # 3. Populate cache
    await redis.hset("risk:account", mapping=limits.to_cache_dict())
    await redis.expire("risk:account", 5)

    return limits
```

### **Real-Time Push (실시간 호가)**

WebSocket 또는 Market Data Feed → Redis:

```python
async def on_market_data(tick: TickData):
    """시장 데이터 수신 시 즉시 캐시 업데이트"""
    await redis.hset(f"price:{tick.symbol}", mapping={
        "bid": str(tick.bid),
        "ask": str(tick.ask),
        "last": str(tick.last),
        "volume": str(tick.volume),
        "timestamp": str(int(tick.timestamp.timestamp() * 1000))
    })
    await redis.expire(f"price:{tick.symbol}", 0.1)
```

---

## **8.6 Latency Improvement Estimates**

| Operation | Before (Sheets) | After (Redis) | Improvement |
|-----------|-----------------|---------------|-------------|
| Price Lookup | 150-300ms | 0.5-1ms | 99.7% |
| Position Check | 200-400ms | 0.3-0.8ms | 99.8% |
| Risk Validation | 250-500ms | 0.5-1.5ms | 99.7% |
| **Total PreCheck** | **600-1200ms** | **2-5ms** | **99.5%** |

**목표 달성:**
- PreCheck p99 목표: 5ms ✓
- 전체 실행 목표: 100ms ✓

---

## **8.7 Cache Failure Handling**

Redis 장애 시 Fallback 전략:

```python
class CacheAwarePreCheck:
    def execute(self, order: OrderDecision) -> PreCheckResult:
        try:
            # Redis 우선
            return self.execute_with_cache(order)
        except RedisConnectionError:
            log_warning("Redis unavailable, falling back to DB")
            return self.execute_with_db(order)
        except CacheStaleDataError:
            log_warning("Cache data stale, refreshing from DB")
            self.refresh_cache()
            return self.execute_with_db(order)
```

**Fallback 규칙:**
- Redis 불가 시 DB 직접 조회 (레이턴시 희생)
- 일시적 장애로 간주, 주문 실행은 계속
- 반복 장애 시 Guardrail 트리거

상세 Fallback 전략은 [19_Caching_Architecture.md](./19_Caching_Architecture.md) 참조.

---

# **9. Appendix**

## **9.1 Execution State Diagram (상세)**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                         ┌──────────┐                                     │
│                         │   INIT   │                                     │
│                         └────┬─────┘                                     │
│                              │                                           │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        PRECHECK                                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │  │
│  │  │Position │→│ Capital │→│ Broker  │→│ Market  │→│  Risk   │     │  │
│  │  │  Check  │ │  Check  │ │  Check  │ │  Check  │ │  Check  │     │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│                    ┌─────────┴─────────┐                                │
│                    │                   │                                │
│                  passed              failed                              │
│                    │                   │                                │
│                    ▼                   ▼                                │
│  ┌─────────────────────────┐    ┌──────────┐                           │
│  │       SPLITTING         │    │  FAILED  │                           │
│  │  Select Strategy        │    └──────────┘                           │
│  │  VWAP/TWAP/Iceberg     │                                            │
│  └───────────┬─────────────┘                                            │
│              │                                                          │
│              ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        SENDING (Async)                           │   │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                                │   │
│  │  │ O1  │ │ O2  │ │ O3  │ │ ... │ → Broker API                   │   │
│  │  └─────┘ └─────┘ └─────┘ └─────┘                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│              │                                                          │
│              ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       MONITORING                                 │   │
│  │                                                                  │   │
│  │  Wait for Fills ──▶ Aggregate ──▶ Check Progress                │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│              │                                                          │
│    ┌─────────┴─────────┐                                               │
│    │                   │                                               │
│  100% filled      < 100% filled                                        │
│    │                   │                                               │
│    │                   ▼                                               │
│    │    ┌─────────────────────────────────────────────────────┐       │
│    │    │                   ADJUSTING                          │       │
│    │    │                                                      │       │
│    │    │  Price Improve ──▶ Modify Order ──▶ Re-monitor      │       │
│    │    │                                                      │       │
│    │    └──────────────────────────────────────────────────────┘       │
│    │                   │                                               │
│    │         ┌─────────┴─────────┐                                    │
│    │         │                   │                                    │
│    │       filled          still unfilled                             │
│    │         │                   │                                    │
│    │         │                   ▼                                    │
│    │         │    ┌─────────────────────────────────────────┐        │
│    │         │    │              ESCAPING                    │        │
│    │         │    │                                          │        │
│    │         │    │  Cancel Unfilled ──▶ Market Liquidate    │        │
│    │         │    │                                          │        │
│    │         │    └──────────────────────────────────────────┘        │
│    │         │                   │                                    │
│    │         │                   ▼                                    │
│    │         │             ┌──────────┐                               │
│    │         │             │ ESCAPED  │                               │
│    │         │             └──────────┘                               │
│    │         │                                                        │
│    └─────────┴──────────────────▶ ┌──────────┐                       │
│                                   │ COMPLETE │                       │
│                                   └──────────┘                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## **8.2 Order Split Algorithm Pseudocode**

```python
def vwap_split_algorithm(order: Order, config: VWAPConfig) -> List[SplitOrder]:
    """
    VWAP(Volume Weighted Average Price) 기반 주문 분할

    원리:
    - 일중 거래량 프로파일에 따라 주문을 분할
    - 거래량이 많은 시간대에 더 많이 실행
    - 시장 충격 최소화
    """

    total_qty = order.qty
    symbol = order.symbol

    # 1. 일중 거래량 프로파일 로드
    volume_profile = load_intraday_volume_profile(symbol)
    # 예: [{"time": "09:00", "volume_pct": 0.08}, {"time": "09:30", "volume_pct": 0.12}, ...]

    # 2. 현재 시간부터 마감까지의 버킷 선택
    remaining_buckets = [b for b in volume_profile if b.time >= current_time()]

    # 3. 남은 거래량 비중 정규화
    total_remaining_pct = sum(b.volume_pct for b in remaining_buckets)
    for b in remaining_buckets:
        b.normalized_pct = b.volume_pct / total_remaining_pct

    # 4. 각 버킷에 수량 할당
    splits = []
    allocated = 0

    for i, bucket in enumerate(remaining_buckets):
        if i == len(remaining_buckets) - 1:
            # 마지막 버킷: 남은 전부
            bucket_qty = total_qty - allocated
        else:
            bucket_qty = int(total_qty * bucket.normalized_pct)

        if bucket_qty > 0:
            splits.append(SplitOrder(
                qty=bucket_qty,
                scheduled_time=bucket.time,
                price=None,  # 시장가 또는 적응적
                max_participation_rate=config.max_participation_rate
            ))
            allocated += bucket_qty

    return splits
```

---

## **8.3 Example: 1000-share VWAP Split**

```
시나리오:
- 종목: 005930 (삼성전자)
- 총 수량: 1,000주
- 현재 시간: 10:00
- 마감: 15:30

일중 거래량 프로파일 (정규화 후):
┌────────┬──────────┬──────────┐
│  시간  │ 거래량%  │ 할당 수량│
├────────┼──────────┼──────────┤
│ 10:00  │   15%    │   150주  │
│ 10:30  │   12%    │   120주  │
│ 11:00  │   10%    │   100주  │
│ 11:30  │    8%    │    80주  │
│ 13:00  │    8%    │    80주  │
│ 13:30  │   10%    │   100주  │
│ 14:00  │   12%    │   120주  │
│ 14:30  │   15%    │   150주  │
│ 15:00  │   10%    │   100주  │
└────────┴──────────┴──────────┘
                     ─────────
                     1,000주 합계

생성된 Split Orders:
[
  SplitOrder(qty=150, scheduled_time="10:00", max_wait_ms=30000),
  SplitOrder(qty=120, scheduled_time="10:30", max_wait_ms=30000),
  SplitOrder(qty=100, scheduled_time="11:00", max_wait_ms=30000),
  ...
]

실행 결과:
- 평균 체결가: 75,150원 (VWAP 근사)
- 시장 충격: 최소화
- 총 체결 수량: 1,000주
- 총 소요 시간: ~5.5시간
```

---

**QTS Scalp Execution Micro-Architecture v1.0.0 — 완료됨**
