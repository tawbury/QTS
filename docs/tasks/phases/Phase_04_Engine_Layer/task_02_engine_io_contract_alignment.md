# Phase 4 — Engine Layer: I/O Contract Alignment

## 목표

- Engine Input/Output Contract를 문서 기준으로 고정하고, ETEDA 단계에서 안정적으로 연결

## 근거

- `docs/arch/02_Engine_Core_Architecture.md`
- `docs/arch/04_Data_Contract_Spec.md`

## 작업

- [ ] Strategy/Risk/Portfolio/Trading/Performance I/O 경계를 코드에서 확인/정리
- [ ] Engine 상태 모델(FAULT 등)과 예외/에러 모델의 적용 범위 확정
- [ ] 코드 품질 개선(필수)
  - [ ] 엔진 생성자/메서드 시그니처와 테스트 코드 간 불일치 해소

## 완료 조건

- [ ] Engine Layer 호출 규칙이 ETEDA Evaluate/Decide/Act 단계와 정합하다.
- [ ] 테스트가 엔진의 “현재 인터페이스”를 기준으로 통과한다.
