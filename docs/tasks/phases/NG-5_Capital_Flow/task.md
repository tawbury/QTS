# NG-5: Capital Flow Engine

## 목표

3-Track 자본 전략 및 풀 기반 자본 관리 시스템 구현

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-5 Section
- [docs/arch/sub/14_Capital_Flow_Architecture.md](../../../arch/sub/14_Capital_Flow_Architecture.md)
- 코드: `src/runtime/capital/`, `src/runtime/engines/capital_engine.py` (신규 생성)

---

## 아키텍처 요약

```python
# 3-Track Strategy
SCALP     → 현금흐름 창출, 고빈도
SWING     → 복리 성장, 중빈도
PORTFOLIO → 자산 보존, 저빈도

# Promotion 조건
Scalp → Swing: 누적 수익 > 100만원, Sharpe > 1.5, 승률 > 55%
Swing → Portfolio: 누적 수익 > 500만원, Sharpe > 1.2
```

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| CapitalPool | 풀 상태 관리 (SCALP/SWING/PORTFOLIO) | 🟡 |
| CapitalEngine | 자본 배분 엔진 (6번째 엔진) | 🟡 |
| PromotionRule | 프로모션/디모션 규칙 | 🟡 |
| RebalancePolicy | 리밸런싱 정책 | 🟡 |

---

## 체크리스트

### 1. Capital Pool 구현

- [ ] `src/runtime/capital/pool.py` 생성
- [ ] CapitalPool 클래스
  ```python
  class CapitalPoolType(Enum):
      SCALP = "scalp"
      SWING = "swing"
      PORTFOLIO = "portfolio"

  class CapitalPool:
      pool_type: CapitalPoolType
      allocated_amount: Decimal
      used_amount: Decimal
      available_amount: Decimal
      state: PoolState  # ACTIVE, PAUSED, LOCKED
  ```
- [ ] 풀 상태 관리 (ACTIVE, PAUSED, LOCKED)
- [ ] 풀 간 자본 이동 기록

### 2. Capital Engine 구현

- [ ] `src/runtime/engines/capital_engine.py` 생성
- [ ] CapitalEngine 클래스 (6번째 엔진)
  ```python
  class CapitalEngine:
      def allocate(self, request: AllocationRequest) -> AllocationResult: ...
      def deallocate(self, position_id: str) -> bool: ...
      def rebalance(self) -> RebalanceResult: ...
      def get_pool_status(self) -> Dict[CapitalPoolType, PoolStatus]: ...
  ```
- [ ] 배분 요청 처리
- [ ] 풀 잔액 추적
- [ ] ETEDA 파이프라인 통합

### 3. Promotion/Demotion 규칙

- [ ] `src/runtime/capital/promotion.py` 생성
- [ ] Promotion 규칙 구현
  ```python
  # Scalp → Swing 조건
  - 누적 수익 > 100만원
  - Sharpe Ratio > 1.5
  - 승률 > 55%
  - 최소 거래 횟수 > 100회

  # Swing → Portfolio 조건
  - 누적 수익 > 500만원
  - Sharpe Ratio > 1.2
  - 최소 보유 기간 > 30일
  ```
- [ ] Demotion 규칙 구현
  ```python
  # Portfolio → Swing 조건
  - 3개월 연속 손실
  - Sharpe < 0.5

  # Swing → Scalp 조건
  - 1개월 연속 손실
  - 최대 손실 > 10%
  ```
- [ ] 자동 Promotion/Demotion 평가

### 4. Rebalance Policy

- [ ] `src/runtime/capital/rebalance.py` 생성
- [ ] 리밸런싱 정책 구현
  ```python
  class RebalancePolicy:
      # 일일 최대 조정: 전체 자본의 5%
      MAX_DAILY_ADJUSTMENT_RATIO = 0.05

      # 최소 리밸런싱 임계값: 2%
      MIN_REBALANCE_THRESHOLD = 0.02
  ```
- [ ] 트리거 조건: 주간 또는 상태 변경 시
- [ ] 점진적 리밸런싱 (급격한 변동 방지)

### 5. Safety 연동

- [ ] FS080-FS089 Fail-Safe 코드 추가
  ```python
  FS080 = "Capital Pool 잔액 부족"
  FS081 = "Promotion 조건 미충족"
  FS082 = "강제 Demotion 트리거"
  FS083 = "리밸런싱 한도 초과"
  ```
- [ ] GR050-GR059 Guardrail 코드 추가
  ```python
  GR050 = "일일 배분 한도 경고"
  GR051 = "풀 사용률 90% 초과"
  GR052 = "Scalp 풀 고갈 임박"
  ```

### 6. 테스트

- [ ] 단위 테스트: CapitalPool, PromotionRule
- [ ] 통합 테스트: CapitalEngine ETEDA 연동
- [ ] 시나리오 테스트: Promotion/Demotion 플로우
- [ ] 스트레스 테스트: 고빈도 배분 요청

---

## 구현 범위

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| CapitalPool | `src/runtime/capital/pool.py` | 풀 상태 관리 |
| CapitalEngine | `src/runtime/engines/capital_engine.py` | 배분 엔진 |
| PromotionRule | `src/runtime/capital/promotion.py` | 프로모션 규칙 |
| RebalancePolicy | `src/runtime/capital/rebalance.py` | 리밸런싱 |
| Safety Codes | `src/ops/safety/codes.py` | FS080-089, GR050-059 추가 |

---

## 완료 조건 (Exit Criteria)

- [ ] Capital Engine ETEDA 통합
- [ ] Promotion/Demotion 규칙 동작 검증
- [ ] FS080-FS089 Fail-Safe 연동
- [ ] GR050-GR059 Guardrail 연동
- [ ] 리밸런싱 정책 동작 검증

---

## 의존성

- **선행 Phase**: NG-3 (Data Layer), NG-7 (System State) ⚠️ 순환 의존성 주의
- **후행 Phase**: 없음 (NG-7과 상호 의존)
- **관련 엔진**: TradingEngine, PortfolioEngine, PerformanceEngine, StrategyEngine

---

## 예상 기간

2주

---

## 관련 문서

- [14_Capital_Flow_Architecture.md](../../../arch/sub/14_Capital_Flow_Architecture.md)
- [18_System_State_Promotion_Architecture.md](../../../arch/sub/18_System_State_Promotion_Architecture.md)
