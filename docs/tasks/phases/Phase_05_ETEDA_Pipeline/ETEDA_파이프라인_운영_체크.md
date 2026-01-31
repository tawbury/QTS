# ETEDA 파이프라인 실패/복구 운영 체크 (Phase 5 §2.2)

파이프라인 실패 시나리오와 대응·복구 절차. **근거**: Phase 10 Exit Criteria §2.2, [docs/arch/03_Pipeline_ETEDA_Architecture.md](../../../arch/03_Pipeline_ETEDA_Architecture.md)

---

## 1. 실패 시나리오 및 동작

| 시나리오 | 발생 위치 | 동작 | 호출자 확인 |
|----------|-----------|------|-------------|
| **run_once 예외** | run_eteda_loop 내 run_once() | ERROR_BACKOFF_MS 만큼 대기 후 재시도. ERROR_BACKOFF_MAX_RETRIES 초과 시 루프 중단 | Config: ERROR_BACKOFF_MS, ERROR_BACKOFF_MAX_RETRIES |
| **safety_hook.should_run() False** | run_once 시작 시 | 즉시 반환. status="skipped", reason="safety" | Safety Hook·Kill Switch 설정 |
| **no_market_data** | Extract 단계 | status="skipped", reason="no_market_data" | 스냅샷/트리거 공급 확인 |
| **PIPELINE_PAUSED truthy** | run_eteda_loop 시작·주기 | should_stop() True → run_once 호출 없이 루프 탈출 | Config PIPELINE_PAUSED=1 또는 pipeline_paused=true |
| **Broker 연속 실패** | LiveBroker submit_intent | ConsecutiveFailureGuard 차단 시 blocked. ExecutionResponse(accepted=False, broker="failsafe") | max_consecutive_failures 정책 |

---

## 2. 복구 절차 (운영)

1. **루프 중단(연속 예외)**  
   - 로그에서 run_once 예외 원인 확인.  
   - Config_Local/Sheet, 리포지토리·시트 접근, 네트워크 순으로 점검.  
   - 수정 후 **새 루프 인스턴스** 실행(재시작 = 새 run_eteda_loop 호출).

2. **PIPELINE_PAUSED로 일시 정지**  
   - PIPELINE_PAUSED=0 또는 pipeline_paused=false 로 변경 후 루프 재시작.

3. **Safety Hook 차단**  
   - Phase 7 Fail-Safe·Kill Switch 정책에 따라 pipeline_state 확인.  
   - 운영 정책에 맞게 should_run() 조건 해제 후 재시작.

4. **Broker Fail-Safe(blocked)**  
   - LiveBroker ConsecutiveFailureGuard 차단 시 adapter 연속 실패 원인 점검.  
   - 수정 후 **새 LiveBroker 인스턴스** 또는 guard 리셋 후 재시도.

5. **롤백/영향 범위**  
   - 파이프라인은 **단일 실행 단위**; 롤백은 “설정/Config 되돌리기 + 루프 재시작”.  
   - 실거래(Act)는 Broker Phase 정책에 따름.

---

## 3. Health check·모니터링

- Runner 단독 헬스체크는 엔진·리포지토리 health_check 조합.  
- run_eteda_loop 반환값(또는 로그)으로 status/skipped/error 확인.  
- 실거래 연동 시: Phase 8 Broker 운영 체크·real_broker 마커 정책 참조.
