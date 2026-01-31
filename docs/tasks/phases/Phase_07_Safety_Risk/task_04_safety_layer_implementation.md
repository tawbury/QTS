# Phase 7 — Safety Risk: Safety Layer Implementation

## 목표

- Safety Layer 실제 구현 완성
- ConsecutiveFailureGuard를 포함한 Fail-Safe 기능 강화

## 근거

- task_01~03에서 `guard.py`, `state.py`, `notifier.py` 구현 완료
- `src/runtime/execution/failsafe/consecutive_failure_guard.py` 구현됨
- docs/arch/07_FailSafe_Architecture.md

## 작업

- [x] Safety Guard 구현
  - [x] `src/ops/safety/guard.py` 실제 로직 구현 (task_01)
  - [x] Kill Switch, Safe Mode, 자동 복구 로직 추가 (SafetyLayer)
  - [x] ConsecutiveFailureGuard와의 연동 (ETEDA _act에서 broker=="failsafe" 시 record_fail_safe)
- [x] Fail-Safe Layer 강화
  - [x] `src/runtime/execution/failsafe/` ConsecutiveFailureGuard 사용, README로 Timeout/Circuit Breaker 확장 안내
- [x] Safety State Machine 설계
  - [x] NORMAL → WARNING → FAIL → LOCKDOWN 상태 전이 (task_02)
  - [x] 자동 복구: request_recovery(operator_approved), LOCKDOWN은 운영자 승인 필요
- [x] Safety Integration
  - [x] ETEDA Pipeline과 Safety Layer 연동 (PipelineSafetyHook, safety_hook 주입)
  - [x] Broker Layer Fail-Safe와의 통합 (LiveBroker 차단 시 FS040 기록)

## 구현 요약

| 자산 | 위치 | 설명 |
|------|------|------|
| PipelineSafetyHook | `src/runtime/pipeline/safety_hook.py` | should_run(), record_fail_safe(), pipeline_state() — runtime은 ops 미참조 |
| SafetyLayer | `src/ops/safety/layer.py` | Kill Switch, Safe Mode, Notifier, request_recovery, PipelineSafetyHook 구현 |
| ETEDA 연동 | `src/runtime/pipeline/eteda_runner.py` | safety_hook 주입; run_once 시작 시 should_run(), Act 단계 broker=="failsafe" 시 record_fail_safe("FS040") |
| Broker Fail-Safe | `LiveBroker` + ConsecutiveFailureGuard | 차단 시 broker="failsafe" 반환 → ETEDA가 safety_hook.record_fail_safe 호출 |
| failsafe 확장 | `src/runtime/execution/failsafe/README.md` | ConsecutiveFailureGuard 문서, Timeout/Circuit Breaker 확장 안내 |

### 사용 예 (호출부)

```python
from ops.safety import SafetyLayer, NoOpNotifier, InMemoryNotifier
from runtime.pipeline.eteda_runner import ETEDARunner

safety = SafetyLayer(notifier=InMemoryNotifier(), kill_switch=False)
runner = ETEDARunner(config, broker=broker, safety_hook=safety)
result = await runner.run_once(snapshot)  # safety.should_run() 확인, FS040 시 record_fail_safe
# 복구: safety.request_recovery(operator_approved=True)
```

## 완료 조건

- [x] Safety Layer가 실제로 동작함
- [x] Kill Switch 및 Safe Mode가 구현됨 (SafetyLayer.kill_switch, safe_mode; ETEDA _act에서 safe_mode 스킵)
- [x] 자동 복구 기능이 동작함 (request_recovery)
