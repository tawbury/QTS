# NG-8: Feedback Loop

## 목표

실행 품질 기반 전략 개선 피드백 시스템 구현

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-8 Section
- [docs/arch/sub/20_Feedback_Loop_Architecture.md](../../../arch/sub/20_Feedback_Loop_Architecture.md)
- 코드: `src/runtime/feedback/` (신규 생성)

---

## 아키텍처 요약

```python
FeedbackData:
  - total_slippage_bps: float        # 총 슬리피지 (bps)
  - avg_fill_latency_ms: float       # 평균 체결 레이턴시
  - partial_fill_ratio: float        # 부분 체결 비율
  - execution_quality_score: float   # 실행 품질 점수 (0.0-1.0)
  - market_impact_bps: float         # 시장 충격 (bps)
```

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| FeedbackAggregator | 실행 데이터 수집 및 집계 | 🟡 |
| SlippageCalculator | 슬리피지 계산 | 🟡 |
| QualityScorer | 실행 품질 점수 산출 | 🟡 |
| StrategyFeedback | Strategy Engine 피드백 연동 | 🟡 |

---

## 체크리스트

### 1. FeedbackData 정의

- [ ] `src/runtime/feedback/models.py` 생성
- [ ] FeedbackData 데이터 클래스
  ```python
  @dataclass
  class FeedbackData:
      execution_id: str
      symbol: str
      strategy_id: str
      strategy_type: str  # SCALP, SWING, PORTFOLIO

      # 슬리피지 메트릭
      expected_price: Decimal
      actual_price: Decimal
      slippage_bps: float

      # 레이턴시 메트릭
      order_sent_at: datetime
      first_fill_at: datetime
      complete_fill_at: datetime
      fill_latency_ms: float

      # 체결 메트릭
      requested_qty: int
      filled_qty: int
      partial_fill_ratio: float

      # 시장 영향
      pre_order_spread_bps: float
      post_order_spread_bps: float
      market_impact_bps: float

      # 품질 점수
      execution_quality_score: float  # 0.0 ~ 1.0

      timestamp: datetime
  ```

### 2. FeedbackAggregator 구현

- [ ] `src/runtime/feedback/aggregator.py` 생성
- [ ] 실시간 데이터 수집
  ```python
  class FeedbackAggregator:
      def record_execution(self, execution: ExecutionResponse) -> None: ...
      def get_recent_stats(self, window: timedelta) -> AggregatedStats: ...
      def get_strategy_stats(self, strategy_id: str) -> StrategyStats: ...
  ```
- [ ] 윈도우 기반 집계 (1시간, 1일, 1주)
- [ ] 전략별/종목별 분류

### 3. SlippageCalculator 구현

- [ ] `src/runtime/feedback/slippage.py` 생성
- [ ] 슬리피지 계산
  ```python
  class SlippageCalculator:
      def calculate(self, expected: Decimal, actual: Decimal, side: str) -> float:
          # BUY: (actual - expected) / expected * 10000  # bps
          # SELL: (expected - actual) / expected * 10000  # bps
  ```
- [ ] 방향별 슬리피지 (BUY/SELL)
- [ ] 시장가 vs 지정가 구분

### 4. QualityScorer 구현

- [ ] `src/runtime/feedback/quality.py` 생성
- [ ] 실행 품질 점수 산출
  ```python
  class QualityScorer:
      WEIGHTS = {
          "slippage": 0.40,        # 40%
          "latency": 0.25,         # 25%
          "fill_rate": 0.20,       # 20%
          "market_impact": 0.15,   # 15%
      }

      def score(self, data: FeedbackData) -> float:
          # 0.0 (매우 나쁨) ~ 1.0 (최상)
          slippage_score = self._score_slippage(data.slippage_bps)
          latency_score = self._score_latency(data.fill_latency_ms)
          fill_score = self._score_fill_rate(data.partial_fill_ratio)
          impact_score = self._score_market_impact(data.market_impact_bps)

          return (
              slippage_score * 0.40 +
              latency_score * 0.25 +
              fill_score * 0.20 +
              impact_score * 0.15
          )
  ```
- [ ] 점수 기준:
  - 슬리피지 < 5bps → 1.0, > 50bps → 0.0
  - 레이턴시 < 100ms → 1.0, > 1000ms → 0.0
  - 체결률 100% → 1.0, < 50% → 0.0
  - 시장 충격 < 2bps → 1.0, > 20bps → 0.0

### 5. Strategy Feedback 연동

- [ ] `src/runtime/feedback/strategy.py` 생성
- [ ] Strategy Engine 피드백 인터페이스
  ```python
  class StrategyFeedback:
      def send_feedback(self, strategy_id: str, feedback: FeedbackSummary) -> None:
          # Strategy Engine에 피드백 전달
          # - 평균 슬리피지
          # - 평균 품질 점수
          # - 권장 조정 사항
  ```
- [ ] 피드백 기반 보정 입력
  - 슬리피지 보정: 예상 가격 조정
  - 수량 보정: 체결률 기반 조정
- [ ] 피드백 주기: 1시간

### 6. 데이터 저장

- [ ] TimescaleDB 저장 연동 (NG-3)
- [ ] 보존 기간: 180일
- [ ] 테이블: `feedback_data` (hypertable)
- [ ] 집계 뷰: `hourly_feedback_stats`, `daily_feedback_stats`

### 7. 테스트

- [ ] 단위 테스트: SlippageCalculator, QualityScorer
- [ ] 통합 테스트: Aggregator + TimescaleDB
- [ ] 시나리오 테스트: 피드백 → 전략 보정 플로우

---

## 구현 범위

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| FeedbackData | `src/runtime/feedback/models.py` | 데이터 모델 |
| FeedbackAggregator | `src/runtime/feedback/aggregator.py` | 데이터 수집 |
| SlippageCalculator | `src/runtime/feedback/slippage.py` | 슬리피지 계산 |
| QualityScorer | `src/runtime/feedback/quality.py` | 품질 점수 |
| StrategyFeedback | `src/runtime/feedback/strategy.py` | 전략 연동 |

---

## 완료 조건 (Exit Criteria)

- [ ] 실행 품질 메트릭 수집 구현
- [ ] TimescaleDB 저장 (180일 보존)
- [ ] Strategy Engine 피드백 연동 (보정 입력)
- [ ] 품질 점수 정확도 검증

---

## 의존성

- **선행 Phase**: NG-3 (Data Layer), NG-6 (Scalp Execution)
- **후행 Phase**: 없음 (최종 Phase)
- **연동**: Strategy Engine, TimescaleDB

---

## 예상 기간

2주

---

## 관련 문서

- [20_Feedback_Loop_Architecture.md](../../../arch/sub/20_Feedback_Loop_Architecture.md)
- [18_Data_Layer_Architecture.md](../../../arch/sub/18_Data_Layer_Architecture.md)
- [15_Scalp_Execution_Micro_Architecture.md](../../../arch/sub/15_Scalp_Execution_Micro_Architecture.md)
