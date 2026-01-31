# UI 실패 시 매매 중단 아님 정책 (Phase 6 §2.2)

Dashboard(Zero-Formula UI) 갱신 실패는 **매매(ETEDA Act) 중단 사유가 아니다**.  
**근거**: Phase 10 Exit Criteria §2.2, [docs/arch/04_Data_Contract_Spec.md](../../../arch/04_Data_Contract_Spec.md) §7.4, [06_UI_Architecture.md](../../../arch/06_UI_Architecture.md) §10

---

## 1. 정책

- **UI 갱신 실패**(R_Dash 시트 쓰기 오류, Contract 버전 불일치, 네트워크/인증 오류 등)가 발생해도:
  - **ETEDA 파이프라인(Evaluate/Decide/Act)** 은 계속 진행한다.
  - **Broker 주문 실행(Act)** 은 UI 성공/실패와 무관하게 동작한다.
- UI는 **표시 전용**이며, 매매 결정 경로(Strategy → Risk → Portfolio → Trading → Broker)와 분리된다.

---

## 2. 구현 반영

- **R_DashWriter**: `write(contract)` 실패 시 예외를 raise하지만, 호출부(ETEDA 종료 후 `schedule_write` 등)에서 **await하지 않고 태스크로 격리** 실행하거나, 예외를 catch하여 로깅만 하고 파이프라인 결과에는 반영하지 않는다.
- **schedule_write**: ETEDA를 블록하지 않도록 `asyncio.create_task(writer.write(contract))` 로 격리 실행 권장 (06 §4.3, §8.1).

---

## 3. 운영 시 유의사항

- R_Dash 시트 갱신이 반복 실패하면 **모니터링/알림**으로 처리하고, 원인(시트 권한, 네트워크, Contract 스키마 변경 등)을 점검한다.
- **매매 중단**은 Safety/Kill Switch(Phase 7), Broker Fail-Safe(Phase 8) 등 별도 정책에 따른다.
