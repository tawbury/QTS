# Act Stage I/O Contract (Phase 5 — ExecutionIntent Integration)

근거: `docs/arch/03_Pipeline_ETEDA_Architecture.md`, `docs/arch/04_Data_Contract_Spec.md`, `src/runtime/execution/models/intent.py`, `src/runtime/execution/models/response.py`

## 1. Act Input (Decide → Act)

- **소스**: Decide 단계 출력(decision dict).
- **필수 필드**: `action` (BUY/SELL/NONE), `symbol`, `approved`.
- **선택 필드**: `qty`, `final_qty`, `reason`, 기타 메타데이터.
- **규칙**: `action == "HOLD"` 또는 `approved == False`이면 Act에서 실행 없이 skip.

## 2. ExecutionIntent (Act → Broker)

- **생성 시점**: Act 단계에서 broker 주입 시, policy 통과 후.
- **필드**: `intent_id` (UUID), `symbol`, `side` (BUY/SELL), `quantity`, `intent_type` (MARKET/LIMIT/NOOP), `metadata`.
- **매핑**: decision.action → side, decision.qty 또는 decision.final_qty → quantity.

## 3. Act Output (ExecutionResponse Contract as dict)

- **broker 주입 시**: ExecutionResponse를 dict로 반환.
  - `status`: "executed" | "rejected" | "error" | "skipped"
  - `intent_id`, `accepted`, `broker`, `message`, `timestamp`, `mode` (PAPER/LIVE).
- **broker 미주입 시**: `status`, `mode`, `details` (기존 호환).

## 4. Error Handling

- **submit_intent 예외**: catch 후 `status: "error"`, `error: str(e)` 반환. 파이프라인은 결과만 기록하고, 상위 루프/정책에서 재시도·Fail-Safe 결정.
- **Fail-Safe**: LiveBroker 내 ConsecutiveFailureGuard 연동 — 연속 실패 시 `accepted=False`, `broker="failsafe"`, `message="blocked: consecutive failures exceeded"` 반환. ETEDA는 해당 결과를 그대로 act_result로 전달.

## 5. Retry 정책

- **Act 단계**: 자동 재시도 없음. 일시 오류는 Broker/Adapter 내부 재시도에 위임.
- **재시도 필요 시**: 상위 루프(ETEDA loop) 또는 스케줄러에서 다음 사이클에 재실행.
