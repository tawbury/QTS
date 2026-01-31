# Fail-Safe / Lockdown 운영 체크 (Phase 7 §2.2)

Fail-Safe·Lockdown 상태 머신 및 복구 절차. **근거**: Phase 10 Exit Criteria §2.2, [docs/arch/07_FailSafe_Architecture.md](../../../arch/07_FailSafe_Architecture.md) §6

---

## 1. 상태 및 전이 요약

| 상태 | 의미 | 거래 허용 | 전이(입력) |
|------|------|-----------|------------|
| **NORMAL** | 정상 | ✓ | anomaly → WARNING; fail_safe → FAIL |
| **WARNING** | 이상 징후 | ✓ | anomaly/guardrail 유지; fail_safe → FAIL |
| **FAIL** | Fail-Safe 1회 | ✗ | fail_safe 2회 연속 → LOCKDOWN; recovery → NORMAL |
| **LOCKDOWN** | Fail-Safe 2회 연속 | ✗ | recovery(operator_approved=True) → NORMAL |

- **Lockdown 진입**: FAIL 상태에서 `apply_fail_safe` 2회 연속 시 자동 LOCKDOWN (Arch §6.4).
- **복구**: FAIL → NORMAL은 `request_recovery()` 호출. LOCKDOWN → NORMAL은 **운영자 승인(operator_approved=True)** 필요.

---

## 2. 복구 절차 (운영)

1. **FAIL 상태 복구**  
   - 원인 확인: `last_fail_safe_code`, Guard/코드 테이블(ops/safety/codes.py) 참조.  
   - 원인 제거 후 `SafetyLayer.request_recovery(operator_approved=False)` 또는 `SafetyStateManager.request_recovery(operator_approved=False)` 호출 → NORMAL 전이.

2. **LOCKDOWN 상태 복구 (operator_approved 플로우)**  
   - LOCKDOWN은 **운영자 승인 없이 복구 불가**.  
   - 운영 절차: 원인 확인 → 조치 완료 → **운영자 승인** 후 `request_recovery(operator_approved=True)` 호출.  
   - 호출 경로: `SafetyLayer.request_recovery(operator_approved=True)` (ETEDARunner에 주입된 safety_hook에서 layer.state_manager 접근 가능).

3. **Kill Switch**  
   - `SafetyLayer.kill_switch = True` 이면 `should_run()` False → 파이프라인 1회 실행 스킵.  
   - 해제: `kill_switch = False` 후 재시작.

4. **롤백/영향 범위**  
   - Safety 상태는 **파이프라인 실행 제어**만 수행. 데이터 롤백은 별도(Config/시트/브로커 정책).  
   - FAIL/LOCKDOWN 시 Act(주문 실행) 미수행; 이전 주문 취소는 브로커 Phase 정책.

---

## 3. ETEDA 연동

- **run_once 시작 시**: `safety_hook.should_run()` False면 `status=skipped, reason=safety` 반환.  
- **Act 단계 Broker Fail-Safe 시**: `record_fail_safe("FS040", message, "act")` 호출 → 상태 전이 + 알림.  
- **테스트**: `tests/ops/safety/` — 상태 전이, Lockdown·recovery(operator_approved), Guard·Codes.
