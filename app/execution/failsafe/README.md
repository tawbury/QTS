# app/execution/failsafe — Fail-Safe Policies

## 구현됨

- **ConsecutiveFailureGuard**: 연속 N회 실패 시 차단. `LiveBroker`에서 사용.
  - `ConsecutiveFailurePolicy(max_failures=3)`
  - `on_success()` / `on_failure()` 호출로 상태 갱신
  - 차단 시 `ExecutionResponse(accepted=False, broker="failsafe")` 반환 → ETEDA `safety_hook.record_fail_safe("FS040", ...)` 연동

## 확장 가능

- **Timeout**: 호출 시간 초과 시 Fail-Safe (예: `submit_intent` 타임아웃)
- **Circuit Breaker**: 실패율/연속 실패에 따라 일정 시간 차단 후 재시도

정책 추가 시 `app.execution.failsafe`에 구현하고, Broker/ETEDA와 동일한 방식으로 `safety_hook.record_fail_safe(code, message, stage)` 연동 권장.
