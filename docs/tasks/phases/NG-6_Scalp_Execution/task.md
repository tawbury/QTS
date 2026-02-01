# NG-6: Scalp Execution Micro-Pipeline

## 목표

6단계 마이크로 실행 파이프라인 구현 (전체 실행 < 100ms, 체결 대기 제외)

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-6 Section
- [docs/arch/sub/15_Scalp_Execution_Micro_Architecture.md](../../../arch/sub/15_Scalp_Execution_Micro_Architecture.md)
- 코드: `src/runtime/execution/stages/` (신규 생성)

---

## 아키텍처 요약

```
PreCheck (< 5ms)
    ↓
OrderSplit (VWAP/TWAP/Iceberg)
    ↓
AsyncSend (< 10ms)
    ↓
PartialFillMonitor (< 60s)
    ↓
AdaptiveAdjust (< 5ms, 최대 3회)
    ↓
EmergencyEscape (< 5ms)
```

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| PreCheckStage | 사전 검증 (리스크, 잔고, 시장 상태) | 🟡 |
| OrderSplitStage | 주문 분할 (VWAP/TWAP/Iceberg) | 🟡 |
| AsyncSendStage | 비동기 주문 전송 | 🟡 |
| PartialFillMonitor | 부분 체결 모니터링 | 🟡 |
| AdaptiveAdjust | 적응형 조정 (최대 3회) | 🟡 |
| EmergencyEscape | 긴급 탈출 | 🟡 |

---

## 체크리스트

### 1. PreCheck Stage

- [ ] `src/runtime/execution/stages/precheck.py` 생성
- [ ] PreCheckStage 구현
  ```python
  class PreCheckStage:
      def check(self, intent: ExecutionIntent) -> PreCheckResult:
          # 1. 리스크 게이트 검증
          # 2. 잔고/증거금 확인
          # 3. 시장 상태 확인 (장 운영 시간)
          # 4. 호가 스프레드 검증
  ```
- [ ] 레이턴시 < 5ms
- [ ] 실패 시 즉시 중단

### 2. OrderSplit Stage

- [ ] `src/runtime/execution/stages/split.py` 생성
- [ ] 주문 분할 알고리즘 구현
  ```python
  class OrderSplitStrategy(Enum):
      SINGLE = "single"    # 단일 주문
      VWAP = "vwap"        # 거래량 가중 평균
      TWAP = "twap"        # 시간 가중 평균
      ICEBERG = "iceberg"  # 아이스버그
  ```
- [ ] 분할 기준: 주문 규모, 유동성
- [ ] 최대 분할 수: 10개

### 3. AsyncSend Stage

- [ ] `src/runtime/execution/stages/send.py` 생성
- [ ] 비동기 주문 전송
  ```python
  class AsyncSendStage:
      async def send(self, orders: List[Order]) -> List[OrderId]:
          # 1. 주문 직렬화
          # 2. 브로커 API 호출 (비동기)
          # 3. 주문 ID 수신
  ```
- [ ] 레이턴시 < 10ms
- [ ] 병렬 전송 지원

### 4. PartialFill Monitor

- [ ] `src/runtime/execution/stages/monitor.py` 생성
- [ ] 부분 체결 모니터링
  ```python
  class PartialFillMonitor:
      def monitor(self, order_ids: List[OrderId], timeout: int = 60) -> FillStatus:
          # 1. 체결 상태 폴링/웹소켓
          # 2. 부분 체결 집계
          # 3. 타임아웃 처리
  ```
- [ ] 체결률 추적 (0% ~ 100%)
- [ ] 타임아웃: 60초 (설정 가능)

### 5. AdaptiveAdjust Stage

- [ ] `src/runtime/execution/stages/adjust.py` 생성
- [ ] 적응형 조정 구현
  ```python
  class AdaptiveAdjustStage:
      MAX_ADJUSTMENTS = 3

      def adjust(self, order: Order, fill_status: FillStatus) -> AdjustedOrder:
          # 1. 미체결 수량 확인
          # 2. 가격 조정 (스프레드 기반)
          # 3. 재주문 생성
  ```
- [ ] 최대 3회 조정
- [ ] 레이턴시 < 5ms/회
- [ ] 가격 조정 한도: 0.5%

### 6. EmergencyEscape Stage

- [ ] `src/runtime/execution/stages/escape.py` 생성
- [ ] 긴급 탈출 구현
  ```python
  class EmergencyEscapeStage:
      def escape(self, order: Order) -> EscapeResult:
          # 1. 미체결 주문 취소
          # 2. 시장가 청산 (옵션)
          # 3. P0 이벤트 발송
  ```
- [ ] 레이턴시 < 5ms
- [ ] MicroRiskLoop 트리거 연동

### 7. 파이프라인 통합

- [ ] `src/runtime/execution/micro_pipeline.py` 생성
- [ ] 6단계 순차 실행
- [ ] 각 단계 레이턴시 측정
- [ ] 전체 레이턴시 < 100ms (체결 대기 제외)

### 8. 테스트

- [ ] 단위 테스트: 각 Stage
- [ ] 통합 테스트: 전체 파이프라인
- [ ] 성능 테스트: 레이턴시 목표 달성
- [ ] 시뮬레이션: Slippage < 0.5%

---

## 구현 범위

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| PreCheckStage | `src/runtime/execution/stages/precheck.py` | 사전 검증 |
| OrderSplitStage | `src/runtime/execution/stages/split.py` | 주문 분할 |
| AsyncSendStage | `src/runtime/execution/stages/send.py` | 비동기 전송 |
| FillMonitor | `src/runtime/execution/stages/monitor.py` | 체결 모니터 |
| AdaptiveAdjust | `src/runtime/execution/stages/adjust.py` | 적응형 조정 |
| EmergencyEscape | `src/runtime/execution/stages/escape.py` | 긴급 탈출 |
| MicroPipeline | `src/runtime/execution/micro_pipeline.py` | 파이프라인 통합 |

---

## 완료 조건 (Exit Criteria)

- [ ] 전체 실행 < 100ms (체결 대기 제외)
- [ ] 각 단계 레이턴시 목표 달성
- [ ] Slippage < 0.5% (시뮬레이션)
- [ ] 긴급 탈출 동작 검증 (MicroRiskLoop 연동)

---

## 의존성

- **선행 Phase**: NG-1 (Event Priority), NG-4 (Caching)
- **후행 Phase**: NG-8 (Feedback Loop)
- **연동**: MicroRiskLoop (NG-2), Event System (NG-1)

---

## 예상 기간

3주

---

## 관련 문서

- [15_Scalp_Execution_Micro_Architecture.md](../../../arch/sub/15_Scalp_Execution_Micro_Architecture.md)
- [16_Micro_Risk_Loop_Architecture.md](../../../arch/sub/16_Micro_Risk_Loop_Architecture.md)
- [17_Event_Priority_Architecture.md](../../../arch/sub/17_Event_Priority_Architecture.md)
