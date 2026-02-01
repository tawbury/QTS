# NG-7: System State Promotion

## 목표

운영 상태 기반 동적 자본 배분 시스템 구현

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-7 Section
- [docs/arch/sub/18_System_State_Promotion_Architecture.md](../../../arch/sub/18_System_State_Promotion_Architecture.md)
- 코드: `src/runtime/state/` (신규 생성)

---

## 아키텍처 요약

```python
# 운영 상태
AGGRESSIVE  → Scalp 60-80%, Swing 15-30%, Portfolio 5-10%
BALANCED    → Scalp 30-50%, Swing 30-40%, Portfolio 20-30%
DEFENSIVE   → Scalp 5-15%, Swing 15-25%, Portfolio 60-80%

# 상태 전이 조건
AGGRESSIVE → BALANCED: DD > 5%, VIX > 25, 연속 손실 > 5회
BALANCED → DEFENSIVE: DD > 10%, VIX > 30, Safety WARNING/FAIL
DEFENSIVE → BALANCED: DD < 5%, VIX < 20, 연속 수익 >= 3일 (최소 5일 유지)
```

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| OperatingState | 3가지 운영 상태 정의 | 🟡 |
| StateTransition | 상태 전이 조건 및 로직 | 🟡 |
| AllocationPolicy | 상태별 자본 배분 정책 | 🟡 |
| Safety 연계 | Safety State와 연동 | 🟡 |

---

## 체크리스트

### 1. Operating State 정의

- [ ] `src/runtime/state/operating.py` 생성
- [ ] OperatingState Enum
  ```python
  class OperatingState(Enum):
      AGGRESSIVE = "aggressive"
      BALANCED = "balanced"
      DEFENSIVE = "defensive"
  ```
- [ ] 각 상태별 특성 정의
  ```python
  STATE_CONFIG = {
      AGGRESSIVE: {
          "scalp_range": (0.60, 0.80),
          "swing_range": (0.15, 0.30),
          "portfolio_range": (0.05, 0.10),
          "risk_tolerance": "high",
      },
      BALANCED: {
          "scalp_range": (0.30, 0.50),
          "swing_range": (0.30, 0.40),
          "portfolio_range": (0.20, 0.30),
          "risk_tolerance": "medium",
      },
      DEFENSIVE: {
          "scalp_range": (0.05, 0.15),
          "swing_range": (0.15, 0.25),
          "portfolio_range": (0.60, 0.80),
          "risk_tolerance": "low",
      },
  }
  ```

### 2. State Transition 구현

- [ ] `src/runtime/state/transition.py` 생성
- [ ] 전이 조건 구현
  ```python
  class StateTransitionRule:
      def evaluate(self, current: OperatingState, metrics: SystemMetrics) -> Optional[OperatingState]:
          # AGGRESSIVE → BALANCED
          if current == AGGRESSIVE:
              if metrics.drawdown > 0.05 or metrics.vix > 25 or metrics.consecutive_losses > 5:
                  return BALANCED

          # BALANCED → DEFENSIVE
          if current == BALANCED:
              if metrics.drawdown > 0.10 or metrics.vix > 30 or metrics.safety_state in [WARNING, FAIL]:
                  return DEFENSIVE

          # DEFENSIVE → BALANCED
          if current == DEFENSIVE:
              if (metrics.drawdown < 0.05 and metrics.vix < 20 and
                  metrics.consecutive_wins >= 3 and metrics.days_in_state >= 5):
                  return BALANCED
  ```
- [ ] 전이 이력 기록
- [ ] 전이 알림 (P2 이벤트)

### 3. Allocation Policy

- [ ] `src/runtime/state/allocation.py` 생성
- [ ] 상태별 배분 정책
  ```python
  class AllocationPolicy:
      def get_allocation(self, state: OperatingState) -> AllocationRatios:
          config = STATE_CONFIG[state]
          return AllocationRatios(
              scalp=config["scalp_range"],
              swing=config["swing_range"],
              portfolio=config["portfolio_range"],
          )
  ```
- [ ] 일일 최대 조정 제한: 5%
- [ ] 점진적 배분 조정 (급격한 변동 방지)

### 4. Safety State 연계

- [ ] Safety State와 Operating State 연동
  ```python
  # Safety State → Operating State 영향
  SafetyState.NORMAL    → 영향 없음
  SafetyState.WARNING   → BALANCED 유지 또는 DEFENSIVE 전이
  SafetyState.LOCKDOWN  → 강제 DEFENSIVE
  SafetyState.FAIL      → 강제 DEFENSIVE + 신규 배분 중단
  ```
- [ ] 양방향 연동:
  - Safety → Operating: 위험 상황 시 방어적 전환
  - Operating → Safety: 상태 정보 공유

### 5. Metrics 수집

- [ ] SystemMetrics 데이터 클래스
  ```python
  @dataclass
  class SystemMetrics:
      drawdown: float            # 현재 손실률
      vix: float                 # 변동성 지수
      consecutive_losses: int    # 연속 손실 횟수
      consecutive_wins: int      # 연속 수익 횟수
      days_in_state: int         # 현재 상태 유지 일수
      safety_state: SafetyState  # 안전 상태
  ```
- [ ] 메트릭 수집 주기: 1분
- [ ] 상태 평가 주기: 1시간

### 6. Capital Engine 연동

- [ ] CapitalEngine (NG-5)과 통합
- [ ] 상태 변경 시 리밸런싱 트리거
- [ ] 배분 비율 동적 적용

### 7. 테스트

- [ ] 단위 테스트: OperatingState, TransitionRule
- [ ] 통합 테스트: State + Capital Engine
- [ ] 시나리오 테스트: 전이 시나리오 검증
- [ ] Safety 연동 테스트

---

## 구현 범위

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| OperatingState | `src/runtime/state/operating.py` | 상태 정의 |
| StateTransition | `src/runtime/state/transition.py` | 전이 로직 |
| AllocationPolicy | `src/runtime/state/allocation.py` | 배분 정책 |
| SystemMetrics | `src/runtime/state/metrics.py` | 메트릭 수집 |

---

## 완료 조건 (Exit Criteria)

- [ ] 3가지 운영 상태 구현
- [ ] 상태 전이 조건 자동 평가
- [ ] Safety State 연계 동작
- [ ] 일일 최대 5% 조정 제한
- [ ] Capital Engine 연동

---

## 의존성

- **선행 Phase**: NG-5 (Capital Flow Engine) ⚠️ 순환 의존성 주의
- **후행 Phase**: 없음
- **연동**: Safety Layer (Phase 7 레거시), Capital Engine (NG-5)

---

## 예상 기간

2주

---

## 관련 문서

- [18_System_State_Promotion_Architecture.md](../../../arch/sub/18_System_State_Promotion_Architecture.md)
- [14_Capital_Flow_Architecture.md](../../../arch/sub/14_Capital_Flow_Architecture.md)
- [07_Safety_Architecture.md](../../../arch/07_Safety_Architecture.md) (레거시)
