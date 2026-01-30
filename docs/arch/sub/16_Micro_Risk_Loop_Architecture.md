# ============================================================
# QTS Micro Risk Loop Architecture
# ============================================================

Version: v1.0.0
Status: Architecture Specification (Final)
Author: 타우
Last Updated: 2026-01-30

문서 목적:
본 문서는 QTS의 **마이크로 리스크 루프(Micro Risk Loop)** 아키텍처를 정의한다.
Micro Risk Loop는 메인 ETEDA 사이클과 독립적으로 100ms~1초 주기로 동작하며,
트레일링 스탑, MAE(Maximum Adverse Excursion), 보유시간, 변동성 킬스위치 등
초고속 리스크 제어를 수행한다.

---

# **1. Overview**

## **1.1 목적**

Micro Risk Loop는 다음 목표를 수행한다.

1. ETEDA 사이클(500ms~3s)보다 빠른 리스크 제어 (100ms~1s)
2. 트레일링 스탑의 실시간 조정
3. MAE 기반 손실 제한
4. 보유 시간 기반 강제 청산
5. 변동성 급등 시 자동 포지션 축소/청산
6. 메인 파이프라인 독립적 안전 계층 제공

---

## **1.2 범위**

포함:

- Micro Loop 컴포넌트 구조
- 초고속 리스크 규칙 (Trailing/MAE/Time/Volatility)
- ETEDA 독립성 아키텍처
- 긴급 액션 타입
- 상태 동기화
- Safety Layer 연계

제외:

- 메인 ETEDA 파이프라인 로직 (03_Pipeline_ETEDA_Architecture)
- Strategy Engine 신호 생성 (02_Engine_Core_Architecture)
- 자본 배분 로직 (14_Capital_Flow_Architecture)

---

## **1.3 설계 원칙**

1. **독립적 실행**
   Micro Risk Loop는 ETEDA 파이프라인과 완전히 분리되어 실행된다.

2. **최소 레이턴시**
   리스크 판단과 액션은 50ms 이내에 완료되어야 한다.

3. **P0 우선순위**
   Micro Risk Loop의 긴급 액션은 P0 이벤트로 처리된다.

4. **ETEDA 정지 권한**
   Micro Risk Loop는 위험 상황 시 ETEDA를 정지시킬 수 있다.

5. **섀도우 상태 기반**
   메인 상태와 동기화된 섀도우 상태로 동작하여 잠금 경합을 최소화한다.

**Micro Risk Loop 권한 명확화.** Micro Risk Loop는 Execution 및 ETEDA에 대해 선제적 권한을 가진다. 리스크 액션은 최종이며 재협상 대상이 아니다. 자본 프로모션 결정은 Micro Risk Loop 책임에서 명시적으로 제외된다. 긴급 상황 시 권한 모호를 제거한다.

---

## **1.4 관련 문서**

- **Main Architecture**: [../00_Architecture.md](../00_Architecture.md)
- **ETEDA Pipeline**: [../03_Pipeline_ETEDA_Architecture.md](../03_Pipeline_ETEDA_Architecture.md)
- **Fail-Safe & Safety**: [../07_FailSafe_Architecture.md](../07_FailSafe_Architecture.md)
- **Event Priority**: [17_Event_Priority_Architecture.md](./17_Event_Priority_Architecture.md)
- **Scalp Execution**: [15_Scalp_Execution_Micro_Architecture.md](./15_Scalp_Execution_Micro_Architecture.md)
- **System State**: [18_System_State_Promotion_Architecture.md](./18_System_State_Promotion_Architecture.md)

---

# **2. Micro-Loop Components**

## **2.1 컴포넌트 아키텍처**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MICRO RISK LOOP ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    MICRO LOOP CONTROLLER                     │   │
│  │                   (Loop Frequency: 100ms-1s)                 │   │
│  └────────────────────────────┬────────────────────────────────┘   │
│                               │                                     │
│         ┌─────────────────────┼─────────────────────┐              │
│         │                     │                     │              │
│         ▼                     ▼                     ▼              │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐        │
│  │  POSITION   │      │   PRICE     │      │    RISK     │        │
│  │   SHADOW    │      │    FEED     │      │    RULE     │        │
│  │  MANAGER    │      │  HANDLER    │      │  EVALUATOR  │        │
│  └──────┬──────┘      └──────┬──────┘      └──────┬──────┘        │
│         │                    │                    │                │
│         └────────────────────┴────────────────────┘                │
│                              │                                      │
│                              ▼                                      │
│                    ┌─────────────────┐                             │
│                    │     ACTION      │                             │
│                    │   DISPATCHER    │                             │
│                    └────────┬────────┘                             │
│                             │                                       │
│              ┌──────────────┼──────────────┐                       │
│              │              │              │                       │
│              ▼              ▼              ▼                       │
│      ┌───────────┐  ┌───────────┐  ┌───────────┐                  │
│      │ Emergency │  │   ETEDA   │  │  Safety   │                  │
│      │  Order    │  │  Suspend  │  │  Notify   │                  │
│      │  Channel  │  │  Signal   │  │           │                  │
│      └───────────┘  └───────────┘  └───────────┘                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **2.2 Position Shadow Manager**

### **2.2.1 역할**

메인 시스템의 포지션 상태를 미러링하여 Micro Loop에서 잠금 없이 접근 가능하게 한다.

### **2.2.2 섀도우 상태 구조**

```python
PositionShadow = {
    "symbol": "005930",
    "qty": 100,
    "avg_price": 75000,
    "current_price": 75500,
    "unrealized_pnl": 50000,
    "unrealized_pnl_pct": 0.0067,

    # Micro Risk 전용 필드
    "entry_time": "2026-01-30T09:30:00Z",
    "time_in_trade_sec": 1800,
    "highest_price_since_entry": 76000,  # 트레일링용
    "lowest_price_since_entry": 74800,
    "mae_pct": -0.0027,                   # MAE 추적
    "mfe_pct": 0.0133,                    # MFE 추적

    # 상태
    "trailing_stop_active": True,
    "trailing_stop_price": 75200,
    "last_sync_time": "2026-01-30T10:00:00.100Z"
}
```

### **2.2.3 동기화 규칙**

```python
SYNC_CONFIG = {
    "sync_frequency_ms": 100,           # 100ms 마다 동기화
    "max_sync_delay_ms": 500,           # 500ms 이상 지연 시 경고
    "stale_threshold_ms": 1000,         # 1초 이상 지연 시 위험

    "sync_fields": [
        "qty", "avg_price", "current_price",
        "unrealized_pnl", "unrealized_pnl_pct"
    ],

    "local_fields": [
        "time_in_trade_sec", "highest_price_since_entry",
        "lowest_price_since_entry", "mae_pct", "mfe_pct",
        "trailing_stop_active", "trailing_stop_price"
    ]
}

def sync_position_shadow():
    main_positions = get_main_positions()  # Non-blocking read

    for symbol, main_pos in main_positions.items():
        shadow = position_shadows[symbol]

        # 메인 필드 동기화
        for field in SYNC_CONFIG["sync_fields"]:
            shadow[field] = main_pos[field]

        # 로컬 필드 업데이트
        shadow.time_in_trade_sec = calculate_time_in_trade(shadow)
        shadow.update_extremes(main_pos.current_price)
        shadow.last_sync_time = now()
```

---

## **2.3 Price Feed Handler**

### **2.3.1 역할**

실시간 가격 피드를 수신하여 Micro Loop에 전달한다.

### **2.3.2 가격 피드 구조**

```python
PriceFeed = {
    "symbol": "005930",
    "price": 75500,
    "bid": 75400,
    "ask": 75500,
    "volume": 1000,
    "timestamp": "2026-01-30T10:00:00.050Z",
    "source": "BROKER_KIS"
}
```

### **2.3.3 가격 버퍼 관리**

```python
class PriceFeedHandler:
    def __init__(self):
        self.price_buffer = {}  # symbol -> deque
        self.buffer_size = 100  # 최근 100틱 유지

    def on_price_tick(self, feed: PriceFeed):
        symbol = feed.symbol

        if symbol not in self.price_buffer:
            self.price_buffer[symbol] = deque(maxlen=self.buffer_size)

        self.price_buffer[symbol].append(feed)

        # 포지션 섀도우 업데이트
        if symbol in position_shadows:
            shadow = position_shadows[symbol]
            shadow.current_price = feed.price
            shadow.update_pnl()
            shadow.update_extremes(feed.price)

    def is_price_stale(self, symbol, threshold_ms=500):
        if symbol not in self.price_buffer:
            return True

        last_tick = self.price_buffer[symbol][-1]
        age_ms = (now() - last_tick.timestamp).total_milliseconds()
        return age_ms > threshold_ms
```

### **2.3.4 가격 이상 감지**

```python
def detect_price_anomaly(symbol, new_price):
    """가격 급변 감지"""
    if symbol not in self.price_buffer or len(self.price_buffer[symbol]) < 2:
        return False

    prev_price = self.price_buffer[symbol][-1].price
    change_pct = abs((new_price - prev_price) / prev_price)

    # 1틱 사이에 5% 이상 변동은 이상
    if change_pct > 0.05:
        log_warning(f"Price anomaly detected: {symbol} {change_pct:.2%}")
        return True

    return False
```

---

## **2.4 Risk Rule Evaluator**

### **2.4.1 역할**

리스크 규칙을 평가하여 액션 필요 여부를 결정한다.

### **2.4.2 평가 순서**

규칙은 우선순위 순서로 평가되며, 먼저 트리거된 규칙이 실행된다.

```
1. Volatility Kill-Switch (최우선)
2. MAE Breach
3. Time-in-Trade Timeout
4. Trailing Stop Hit
```

### **2.4.3 평가 로직**

```python
class RiskRuleEvaluator:
    def __init__(self, config):
        self.config = config
        self.rules = [
            VolatilityKillSwitchRule(config.volatility),
            MAERule(config.mae),
            TimeInTradeRule(config.time_in_trade),
            TrailingStopRule(config.trailing_stop)
        ]

    def evaluate(self, shadow: PositionShadow, market_data: MarketData):
        """모든 규칙 평가, 트리거된 액션 반환"""
        actions = []

        for rule in self.rules:
            action = rule.evaluate(shadow, market_data)
            if action:
                actions.append(action)

                # 단락 평가: Kill-Switch 또는 Full Exit 시 다른 규칙 스킵
                if action.type in ["KILL_SWITCH", "FULL_EXIT"]:
                    break

        return actions
```

---

## **2.5 Action Dispatcher**

### **2.5.1 역할**

평가 결과에 따른 액션을 실행한다.

### **2.5.2 액션 타입**

```python
MicroRiskAction = {
    "action_id": "uuid",
    "action_type": "TRAILING_STOP_ADJUST",  # 아래 참조
    "symbol": "005930",
    "payload": {...},
    "timestamp": "2026-01-30T10:00:00.100Z",
    "priority": "P0"
}

ACTION_TYPES = [
    "TRAILING_STOP_ADJUST",  # 트레일링 스탑 가격 조정
    "PARTIAL_EXIT",          # 부분 청산
    "FULL_EXIT",             # 전량 청산
    "POSITION_FREEZE",       # 신규 진입 차단
    "ETEDA_SUSPEND",         # ETEDA 일시 정지
    "KILL_SWITCH"            # 모든 포지션 청산
]
```

### **2.5.3 디스패치 로직**

```python
class ActionDispatcher:
    def __init__(self, broker_channel, eteda_controller, safety_notifier):
        self.broker_channel = broker_channel      # 긴급 주문 채널
        self.eteda_controller = eteda_controller  # ETEDA 제어
        self.safety_notifier = safety_notifier    # Safety 알림

    def dispatch(self, action: MicroRiskAction):
        if action.action_type == "TRAILING_STOP_ADJUST":
            self._adjust_trailing_stop(action)

        elif action.action_type == "PARTIAL_EXIT":
            self._execute_partial_exit(action)

        elif action.action_type == "FULL_EXIT":
            self._execute_full_exit(action)

        elif action.action_type == "POSITION_FREEZE":
            self._freeze_position(action)

        elif action.action_type == "ETEDA_SUSPEND":
            self._suspend_eteda(action)

        elif action.action_type == "KILL_SWITCH":
            self._execute_kill_switch(action)

    def _execute_full_exit(self, action):
        """긴급 전량 청산"""
        emergency_order = EmergencyOrder(
            symbol=action.symbol,
            side="SELL",
            qty=action.payload["qty"],
            order_type="MARKET",
            reason=action.payload["reason"]
        )

        # P0 이벤트로 전송
        event = P0Event(
            event_type="EMERGENCY_ORDER",
            payload=emergency_order
        )
        dispatch_p0_event(event)

        # Safety 통보
        self.safety_notifier.notify(
            code="FS102",
            message=f"Micro Risk triggered full exit: {action.symbol}"
        )
```

---

# **3. Risk Rules (Ultra-Fast)**

## **3.1 Trailing Stop Control**

### **3.1.1 개념**

트레일링 스탑은 수익이 발생한 포지션에서 일정 비율의 이익을 보호하는 동적 손절이다.

```
가격
  │
  │     ◆ 고점 (Highest Since Entry)
  │    /│
  │   / │  ← Trail Distance
  │  /  ▼
  │ /  ═══════════════════  트레일링 스탑 라인
  │/
  ├─────────────────────────────── 시간
```

### **3.1.2 활성화 조건**

```python
TrailingStopConfig = {
    "activation_profit_pct": 0.01,    # 1% 수익 발생 시 활성화
    "trail_distance_pct": 0.005,      # 고점 대비 0.5% 아래에 스탑
    "min_trail_distance": 500,        # 최소 500원
    "adjustment_frequency_ms": 100,   # 100ms마다 조정
    "ratchet_only": True              # 스탑은 위로만 이동 (하향 불가)
}

def should_activate_trailing_stop(shadow: PositionShadow, config):
    return (
        shadow.unrealized_pnl_pct >= config.activation_profit_pct and
        not shadow.trailing_stop_active
    )
```

### **3.1.3 스탑 가격 계산**

```python
def calculate_trailing_stop_price(shadow: PositionShadow, config):
    highest = shadow.highest_price_since_entry

    # 고점 대비 trail_distance 아래
    stop_price = highest * (1 - config.trail_distance_pct)

    # 최소 거리 보장
    min_stop = highest - config.min_trail_distance
    stop_price = max(stop_price, min_stop)

    # 래칫: 기존 스탑보다 높아야만 업데이트
    if config.ratchet_only and shadow.trailing_stop_price:
        stop_price = max(stop_price, shadow.trailing_stop_price)

    return stop_price
```

### **3.1.4 트리거 조건**

```python
class TrailingStopRule:
    def evaluate(self, shadow: PositionShadow, market_data):
        if not shadow.trailing_stop_active:
            return None

        if shadow.current_price <= shadow.trailing_stop_price:
            return MicroRiskAction(
                action_type="FULL_EXIT",
                symbol=shadow.symbol,
                payload={
                    "qty": shadow.qty,
                    "reason": "TRAILING_STOP_HIT",
                    "stop_price": shadow.trailing_stop_price,
                    "current_price": shadow.current_price
                }
            )

        # 스탑 가격 조정 필요 여부
        new_stop = calculate_trailing_stop_price(shadow, self.config)
        if new_stop > shadow.trailing_stop_price:
            return MicroRiskAction(
                action_type="TRAILING_STOP_ADJUST",
                symbol=shadow.symbol,
                payload={
                    "old_stop": shadow.trailing_stop_price,
                    "new_stop": new_stop
                }
            )

        return None
```

---

## **3.2 MAE (Maximum Adverse Excursion) Control**

### **3.2.1 개념**

MAE는 진입 후 최대 불리 이동을 측정하여 손실을 제한한다.

```
가격
  │
  ├───◆ 진입 가격
  │   │
  │   │  ← MAE = 진입가 - 최저가
  │   │
  │   ▼
  ├───◆ 최저가 (Lowest Since Entry)
  │
  └─────────────────────────────── 시간
```

### **3.2.2 MAE 설정**

```python
MAEConfig = {
    "position_mae_threshold_pct": 0.02,   # 포지션당 2% MAE 허용
    "account_mae_threshold_pct": 0.05,    # 계좌 전체 5% MAE 허용
    "mae_action": "FULL_EXIT",            # MAE 초과 시 전량 청산
    "partial_exit_at_pct": 0.015,         # 1.5% MAE 시 50% 부분 청산
    "partial_exit_ratio": 0.50
}
```

### **3.2.3 MAE 계산**

```python
def calculate_mae(shadow: PositionShadow):
    """MAE 계산 (%)"""
    if shadow.qty > 0:  # Long 포지션
        mae_pct = (shadow.lowest_price_since_entry - shadow.avg_price) / shadow.avg_price
    else:  # Short 포지션
        mae_pct = (shadow.avg_price - shadow.highest_price_since_entry) / shadow.avg_price

    return mae_pct  # 음수 값 (손실)
```

### **3.2.4 MAE 규칙 평가**

```python
class MAERule:
    def evaluate(self, shadow: PositionShadow, market_data):
        mae_pct = shadow.mae_pct

        # 임계값 초과 시 전량 청산
        if abs(mae_pct) >= self.config.position_mae_threshold_pct:
            return MicroRiskAction(
                action_type="FULL_EXIT",
                symbol=shadow.symbol,
                payload={
                    "qty": shadow.qty,
                    "reason": "MAE_THRESHOLD_EXCEEDED",
                    "mae_pct": mae_pct,
                    "threshold": self.config.position_mae_threshold_pct
                }
            )

        # 부분 청산 임계값
        if abs(mae_pct) >= self.config.partial_exit_at_pct:
            partial_qty = int(shadow.qty * self.config.partial_exit_ratio)
            return MicroRiskAction(
                action_type="PARTIAL_EXIT",
                symbol=shadow.symbol,
                payload={
                    "qty": partial_qty,
                    "reason": "MAE_PARTIAL_THRESHOLD",
                    "mae_pct": mae_pct
                }
            )

        return None
```

---

## **3.3 Time-in-Trade Monitor**

### **3.3.1 개념**

포지션 보유 시간이 최대 허용 시간을 초과하면 강제 청산한다.

### **3.3.2 시간 설정**

```python
TimeInTradeConfig = {
    "scalp_max_time_sec": 3600,          # Scalp: 최대 1시간
    "swing_max_time_sec": 604800,        # Swing: 최대 7일
    "portfolio_max_time_sec": None,      # Portfolio: 제한 없음

    "warning_at_pct": 0.80,              # 80% 도달 시 경고
    "extension_conditions": {            # 연장 조건
        "profitable": True,              # 수익 중이면 연장
        "extension_time_sec": 1800       # 30분 연장
    }
}
```

### **3.3.3 시간 규칙 평가**

```python
class TimeInTradeRule:
    def evaluate(self, shadow: PositionShadow, market_data):
        strategy = shadow.strategy  # SCALP / SWING / PORTFOLIO
        max_time = self.config.get_max_time(strategy)

        if max_time is None:
            return None

        time_in_trade = shadow.time_in_trade_sec

        # 연장 조건 확인
        if self.can_extend(shadow):
            max_time += self.config.extension_conditions["extension_time_sec"]

        # 시간 초과
        if time_in_trade >= max_time:
            return MicroRiskAction(
                action_type="FULL_EXIT",
                symbol=shadow.symbol,
                payload={
                    "qty": shadow.qty,
                    "reason": "TIME_IN_TRADE_EXCEEDED",
                    "time_in_trade_sec": time_in_trade,
                    "max_time_sec": max_time
                }
            )

        # 경고
        if time_in_trade >= max_time * self.config.warning_at_pct:
            log_warning(
                f"Time warning: {shadow.symbol} at {time_in_trade}s / {max_time}s"
            )

        return None

    def can_extend(self, shadow):
        """연장 조건 확인"""
        if self.config.extension_conditions["profitable"]:
            return shadow.unrealized_pnl > 0
        return False
```

---

## **3.4 Volatility Kill-Switch**

### **3.4.1 개념**

시장 변동성이 급등하면 포지션을 축소하거나 전량 청산한다.

### **3.4.2 변동성 설정**

```python
VolatilityKillSwitchConfig = {
    "vix_warning_level": 25,             # VIX 25 이상: 경고
    "vix_critical_level": 30,            # VIX 30 이상: 위험
    "vix_kill_level": 40,                # VIX 40 이상: 킬스위치

    "realized_vol_warning": 0.03,        # 일중 변동성 3%: 경고
    "realized_vol_critical": 0.05,       # 일중 변동성 5%: 위험
    "realized_vol_kill": 0.08,           # 일중 변동성 8%: 킬스위치

    "actions": {
        "WARNING": "LOG_ONLY",
        "CRITICAL": "REDUCE_50",         # 포지션 50% 축소
        "KILL": "FULL_EXIT_ALL"          # 전량 청산
    }
}
```

### **3.4.3 변동성 규칙 평가**

```python
class VolatilityKillSwitchRule:
    def evaluate(self, shadow: PositionShadow, market_data):
        vix = market_data.vix
        realized_vol = market_data.realized_volatility

        # Kill 레벨
        if vix >= self.config.vix_kill_level or realized_vol >= self.config.realized_vol_kill:
            return MicroRiskAction(
                action_type="KILL_SWITCH",
                symbol="ALL",
                payload={
                    "reason": "VOLATILITY_KILL_SWITCH",
                    "vix": vix,
                    "realized_vol": realized_vol
                }
            )

        # Critical 레벨
        if vix >= self.config.vix_critical_level or realized_vol >= self.config.realized_vol_critical:
            return MicroRiskAction(
                action_type="PARTIAL_EXIT",
                symbol=shadow.symbol,
                payload={
                    "qty": int(shadow.qty * 0.50),
                    "reason": "VOLATILITY_CRITICAL",
                    "vix": vix
                }
            )

        # Warning 레벨
        if vix >= self.config.vix_warning_level:
            log_warning(f"Volatility warning: VIX={vix}")

        return None
```

---

# **4. Independence from Main ETEDA**

## **4.1 분리된 이벤트 루프**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PARALLEL EXECUTION MODEL                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    MAIN ETEDA LOOP                           │   │
│  │     Extract → Transform → Evaluate → Decide → Act            │   │
│  │                  (Cycle: 500ms - 3s)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                               ║                                     │
│                    ═══════════╬═══════════  (병렬, 독립)           │
│                               ║                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  MICRO RISK LOOP                             │   │
│  │      Sync → Evaluate → Act (if needed) → Sleep               │   │
│  │                  (Cycle: 100ms - 1s)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  공유 자원:                                                         │
│  - Position Shadow (read-only by Micro Loop)                       │
│  - Price Feed (shared subscription)                                │
│  - Emergency Order Channel (P0 queue)                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **4.2 논블로킹 아키텍처**

```python
class MicroRiskLoop:
    """ETEDA와 독립적으로 실행되는 Micro Risk Loop"""

    def __init__(self, config):
        self.config = config
        self.running = False

        # 논블로킹 컴포넌트
        self.position_shadow = PositionShadowManager()
        self.price_handler = PriceFeedHandler()
        self.rule_evaluator = RiskRuleEvaluator(config)
        self.action_dispatcher = ActionDispatcher()

    def start(self):
        self.running = True
        self.loop_thread = Thread(target=self._run_loop, daemon=True)
        self.loop_thread.start()

    def _run_loop(self):
        while self.running:
            loop_start = time_ns()

            try:
                # 1. 상태 동기화 (논블로킹)
                self.position_shadow.sync()

                # 2. 시장 데이터 수집
                market_data = self.price_handler.get_latest()

                # 3. 각 포지션에 대해 규칙 평가
                for symbol, shadow in self.position_shadow.items():
                    actions = self.rule_evaluator.evaluate(shadow, market_data)

                    # 4. 액션 실행
                    for action in actions:
                        self.action_dispatcher.dispatch(action)

            except Exception as e:
                log_error(f"Micro loop error: {e}")
                self._handle_loop_error(e)

            # 5. 슬립 (목표 주기 유지)
            elapsed_ms = (time_ns() - loop_start) / 1_000_000
            sleep_ms = max(0, self.config.loop_interval_ms - elapsed_ms)
            sleep(sleep_ms / 1000)
```

---

## **4.3 메인 사이클 대비 우선순위**

```python
PRIORITY_MODEL = {
    # Micro Risk Loop 액션은 P0 우선순위
    "micro_risk_actions": "P0",

    # ETEDA 일반 이벤트는 P2
    "eteda_events": "P2",

    # Micro Loop는 ETEDA를 선점할 수 있음
    "can_preempt_eteda": True,

    # Micro Loop는 ETEDA를 정지시킬 수 있음
    "can_suspend_eteda": True
}
```

---

## **4.4 ETEDA 정지 권한**

```python
def suspend_eteda(reason: str, duration_ms: int = None):
    """ETEDA 파이프라인 일시 정지"""

    # 정지 신호 전송
    eteda_controller.suspend(
        reason=reason,
        source="MICRO_RISK_LOOP",
        duration_ms=duration_ms
    )

    # Safety 통보
    safety_notifier.notify(
        code="FS103",
        message=f"ETEDA suspended by Micro Risk: {reason}"
    )

    log_warning(f"ETEDA suspended: {reason}")
```

---

# **5. Actions & Effects**

## **5.1 Trailing Stop Adjustment**

```python
def adjust_trailing_stop(action):
    shadow = position_shadows[action.symbol]

    old_stop = shadow.trailing_stop_price
    new_stop = action.payload["new_stop"]

    shadow.trailing_stop_price = new_stop

    log_info(
        f"Trailing stop adjusted: {action.symbol} "
        f"{old_stop} → {new_stop}"
    )
```

---

## **5.2 Partial Exit**

```python
def execute_partial_exit(action):
    """부분 청산 실행"""
    order = EmergencyOrder(
        symbol=action.symbol,
        side="SELL",
        qty=action.payload["qty"],
        order_type="MARKET",
        reason=action.payload["reason"]
    )

    # P0 긴급 주문 채널로 전송
    dispatch_p0_event(P0Event(
        event_type="EMERGENCY_ORDER",
        payload=order
    ))

    # 섀도우 업데이트 (실제 체결 전 임시)
    shadow = position_shadows[action.symbol]
    shadow.qty -= action.payload["qty"]
```

---

## **5.3 Full Exit**

```python
def execute_full_exit(action):
    """전량 청산 실행"""
    shadow = position_shadows[action.symbol]

    order = EmergencyOrder(
        symbol=action.symbol,
        side="SELL",
        qty=shadow.qty,
        order_type="MARKET",
        reason=action.payload["reason"]
    )

    dispatch_p0_event(P0Event(
        event_type="EMERGENCY_ORDER",
        payload=order
    ))

    # 트레일링 스탑 비활성화
    shadow.trailing_stop_active = False

    log_warning(
        f"Full exit triggered: {action.symbol}, "
        f"reason={action.payload['reason']}"
    )
```

---

## **5.4 Position Freeze**

```python
def freeze_position(action):
    """신규 진입 차단"""
    symbol = action.symbol

    # 신규 진입 차단 플래그 설정
    entry_blocker.block(symbol, reason=action.payload["reason"])

    # ETEDA에 통보
    eteda_controller.notify_freeze(symbol)

    log_warning(f"Position frozen: {symbol}")
```

---

## **5.5 ETEDA Suspension**

```python
def suspend_eteda_from_micro_risk(action):
    """Micro Risk에서 ETEDA 정지"""

    duration_ms = action.payload.get("duration_ms", 60000)  # 기본 1분

    eteda_controller.suspend(
        reason=action.payload["reason"],
        source="MICRO_RISK_LOOP",
        duration_ms=duration_ms
    )

    safety_notifier.notify(
        code="FS103",
        message=f"ETEDA suspended: {action.payload['reason']}"
    )
```

---

# **6. State Synchronization**

## **6.1 Position Shadow vs Main Position**

| 구분 | Main Position | Position Shadow |
|------|---------------|-----------------|
| 소유권 | ETEDA Pipeline | Micro Risk Loop |
| 업데이트 주체 | Act Phase (체결 후) | Sync (100ms 주기) |
| 잠금 | 필요 (Write Lock) | 불필요 (Read-only Copy) |
| 지연 | 없음 | 최대 100ms |
| 용도 | 실제 거래 기록 | 리스크 평가 |

---

## **6.2 동기화 타이밍**

```python
SYNC_TIMING = {
    "regular_sync_ms": 100,          # 정기 동기화: 100ms
    "on_fill_sync": True,            # 체결 시 즉시 동기화
    "on_position_change_sync": True, # 포지션 변경 시 즉시 동기화
}

def on_fill_event(fill):
    """체결 이벤트 시 즉시 동기화"""
    symbol = fill.symbol

    # 메인 포지션에서 최신 데이터 가져오기
    main_pos = get_main_position(symbol)

    # 섀도우 즉시 업데이트
    shadow = position_shadows[symbol]
    shadow.sync_from_main(main_pos)
    shadow.last_sync_time = now()
```

---

## **6.3 충돌 해결 규칙**

```python
def resolve_sync_conflict(shadow, main_pos):
    """동기화 충돌 해결"""

    # qty 불일치: 메인이 우선
    if shadow.qty != main_pos.qty:
        log_warning(f"Qty mismatch: shadow={shadow.qty}, main={main_pos.qty}")
        shadow.qty = main_pos.qty

    # 가격 불일치: 메인이 우선
    if shadow.avg_price != main_pos.avg_price:
        shadow.avg_price = main_pos.avg_price

    # 로컬 필드는 유지 (extremes, trailing stop 등)
    # 이들은 Micro Loop에서만 업데이트됨
```

---

# **7. Safety Integration**

## **7.1 Micro-loop Fail-Safe (FS100-FS109)**

| 코드 | 조건 | 동작 |
|------|------|------|
| FS100 | Micro Loop 크래시 | Loop 재시작, ETEDA 정지 |
| FS101 | 동기화 지연 > 1초 | 경고, 강제 동기화 |
| FS102 | 긴급 청산 실행 | 로그 및 Safety 통보 |
| FS103 | ETEDA 정지 요청 | Safety 통보 |
| FS104 | Kill Switch 발동 | 전량 청산, LOCKDOWN |
| FS105 | 가격 피드 중단 | 경고, 최종 가격 사용 |

---

## **7.2 Micro-loop Guardrails (GR070-GR079)**

| 코드 | 조건 | 동작 |
|------|------|------|
| GR070 | 트레일링 스탑 과다 조정 | 조정 빈도 제한 |
| GR071 | MAE 임계값 근접 | 경고 로그 |
| GR072 | 보유 시간 경고 | 경고 로그 |
| GR073 | 변동성 상승 | 경고, 포지션 축소 권고 |
| GR074 | 긴급 주문 실패 | 재시도, 실패 시 FS 에스컬레이션 |

---

## **7.3 System State로 에스컬레이션**

```python
def escalate_to_system_state(reason: str, severity: str):
    """System State(DEFENSIVE)로 에스컬레이션"""

    if severity == "CRITICAL":
        # 즉시 DEFENSIVE 전환 요청
        system_state_manager.request_transition(
            target_state="DEFENSIVE",
            reason=reason,
            source="MICRO_RISK_LOOP",
            force=True
        )

        safety_notifier.notify(
            code="FS104",
            message=f"Micro Risk escalation to DEFENSIVE: {reason}"
        )
```

---

## **7.4 LOCKDOWN 에스컬레이션**

```python
def escalate_to_lockdown(reason: str):
    """Kill Switch → LOCKDOWN 에스컬레이션"""

    # 1. 모든 포지션 청산
    for symbol, shadow in position_shadows.items():
        if shadow.qty != 0:
            execute_full_exit(MicroRiskAction(
                action_type="FULL_EXIT",
                symbol=symbol,
                payload={"qty": shadow.qty, "reason": reason}
            ))

    # 2. ETEDA 정지
    eteda_controller.suspend(reason=reason, duration_ms=None)  # 무기한

    # 3. LOCKDOWN 요청
    safety_state_manager.enter_lockdown(
        reason=reason,
        source="MICRO_RISK_LOOP"
    )

    # 4. 알림
    safety_notifier.notify_critical(
        code="FS104",
        message=f"LOCKDOWN triggered by Micro Risk: {reason}"
    )
```

---

# **8. Performance Requirements**

## **8.1 Loop Frequency**

```python
LOOP_FREQUENCY_CONFIG = {
    "target_interval_ms": 100,       # 목표: 100ms
    "max_interval_ms": 1000,         # 최대: 1초
    "min_interval_ms": 50,           # 최소: 50ms

    "adaptive_interval": True,       # 부하에 따라 조정
    "increase_on_load": True         # 부하 높으면 간격 증가
}
```

---

## **8.2 Maximum Latency**

| 구간 | 목표 레이턴시 | 최대 레이턴시 |
|------|--------------|--------------|
| 동기화 | 5ms | 20ms |
| 규칙 평가 | 10ms | 30ms |
| 액션 디스패치 | 5ms | 20ms |
| **전체 루프** | **20ms** | **50ms** |

---

## **8.3 리소스 제한**

```python
RESOURCE_LIMITS = {
    "cpu_core": 0.5,                 # 0.5 코어 사용
    "memory_mb": 128,                # 128MB 메모리
    "thread_count": 1,               # 단일 스레드
    "max_positions_monitored": 100   # 최대 100 포지션
}
```

---

# **9. Testability**

## **9.1 규칙 평가 테스트**

```python
class TestRiskRules:
    def test_trailing_stop_activation(self):
        shadow = PositionShadow(
            avg_price=100,
            current_price=102,
            unrealized_pnl_pct=0.02
        )

        rule = TrailingStopRule(TrailingStopConfig(activation_profit_pct=0.01))
        assert rule.should_activate(shadow) == True

    def test_mae_trigger(self):
        shadow = PositionShadow(
            avg_price=100,
            lowest_price_since_entry=97,
            mae_pct=-0.03
        )

        rule = MAERule(MAEConfig(position_mae_threshold_pct=0.02))
        action = rule.evaluate(shadow, None)
        assert action.action_type == "FULL_EXIT"
```

---

## **9.2 통합 테스트**

```python
class TestMicroRiskLoop:
    def test_loop_independence_from_eteda(self):
        # ETEDA 일시 정지
        eteda.pause()

        # Micro Risk Loop 계속 동작 확인
        micro_loop.inject_test_position()
        micro_loop.inject_price_update(price=95)  # MAE 트리거

        # 긴급 청산 실행 확인
        assert emergency_order_queue.has_order()

    def test_eteda_suspension(self):
        # Kill Switch 조건 시뮬레이션
        market_data = MarketData(vix=45)

        action = rule_evaluator.evaluate(test_shadow, market_data)
        action_dispatcher.dispatch(action)

        assert eteda_controller.is_suspended() == True
```

---

# **10. Appendix**

## **10.1 Micro-Loop State Diagram**

```
┌─────────────────────────────────────────────────────────────────────┐
│                  MICRO RISK LOOP STATE MACHINE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐                                                   │
│  │   IDLE      │◀──────────────────────────────────────┐           │
│  │             │                                        │           │
│  └──────┬──────┘                                        │           │
│         │ start()                                       │           │
│         ▼                                               │           │
│  ┌─────────────┐                                        │           │
│  │   SYNCING   │                                        │           │
│  │             │                                        │           │
│  └──────┬──────┘                                        │           │
│         │ sync complete                                 │           │
│         ▼                                               │           │
│  ┌─────────────┐                                        │           │
│  │  EVALUATING │                                        │           │
│  │             │                                        │           │
│  └──────┬──────┘                                        │           │
│         │                                               │           │
│    ┌────┴────┐                                          │           │
│    │         │                                          │           │
│    ▼         ▼                                          │           │
│  ┌─────┐  ┌─────────┐                                   │           │
│  │ NO  │  │ ACTION  │                                   │           │
│  │ACTION│  │ NEEDED │                                   │           │
│  └──┬──┘  └────┬────┘                                   │           │
│     │          │                                        │           │
│     │          ▼                                        │           │
│     │    ┌─────────────┐                                │           │
│     │    │ DISPATCHING │                                │           │
│     │    │             │                                │           │
│     │    └──────┬──────┘                                │           │
│     │           │                                       │           │
│     └─────┬─────┘                                       │           │
│           │                                             │           │
│           ▼                                             │           │
│     ┌─────────────┐                                     │           │
│     │  SLEEPING   │─────────────────────────────────────┘           │
│     │  (interval) │                                                  │
│     └─────────────┘                                                  │
│                                                                      │
│  ERROR PATH:                                                        │
│     Any State ──▶ ERROR ──▶ RECOVERY ──▶ IDLE or SHUTDOWN          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **10.2 Risk Rule Evaluation Pseudocode**

```python
def micro_risk_loop_cycle():
    """Single cycle of Micro Risk Loop"""

    # 1. Sync position shadows
    for symbol in tracked_symbols:
        main_pos = get_main_position_nonblocking(symbol)
        shadow = position_shadows[symbol]
        shadow.sync(main_pos)

    # 2. Get market data
    market_data = price_handler.get_latest_market_data()

    # 3. Evaluate rules for each position
    for symbol, shadow in position_shadows.items():
        # Skip if no position
        if shadow.qty == 0:
            continue

        # Evaluate rules in priority order
        actions = []

        # 3.1 Volatility Kill-Switch (highest priority)
        vol_action = volatility_rule.evaluate(shadow, market_data)
        if vol_action and vol_action.type == "KILL_SWITCH":
            dispatch(vol_action)
            continue  # Skip other rules

        # 3.2 MAE Rule
        mae_action = mae_rule.evaluate(shadow, market_data)
        if mae_action:
            dispatch(mae_action)
            continue

        # 3.3 Time-in-Trade Rule
        time_action = time_rule.evaluate(shadow, market_data)
        if time_action:
            dispatch(time_action)
            continue

        # 3.4 Trailing Stop Rule
        trailing_action = trailing_rule.evaluate(shadow, market_data)
        if trailing_action:
            dispatch(trailing_action)

    # 4. Sleep until next cycle
    sleep_until_next_cycle()
```

---

## **10.3 Latency Benchmark Targets**

```python
LATENCY_BENCHMARKS = {
    "sync_p50_ms": 2,
    "sync_p99_ms": 10,

    "evaluate_p50_ms": 5,
    "evaluate_p99_ms": 20,

    "dispatch_p50_ms": 2,
    "dispatch_p99_ms": 10,

    "total_cycle_p50_ms": 10,
    "total_cycle_p99_ms": 40,
    "total_cycle_max_ms": 50
}
```

---

**QTS Micro Risk Loop Architecture v1.0.0 — 완료됨**
