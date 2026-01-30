# Phase 7 — Safety/Risk: Safety State Machine & Lockdown

## 목표

- Safety 상태(NORMAL/WARNING/FAIL/LOCKDOWN)를 상태 머신으로 고정하고, Lockdown 절차를 명확히 한다.

## 근거

- `docs/arch/07_FailSafe_Architecture.md`

## 작업

- [ ] Safety State Manager 구현 범위 확정
  - [ ] 상태 전이 조건/이벤트 정의
- [ ] Lockdown/Recovery 절차 정의
  - [ ] 자동 복구 vs 운영자 개입 기준
- [ ] 코드 품질 개선(필수)
  - [ ] 상태 전이가 “암묵적 플래그”로 존재하지 않도록 명시화

## 완료 조건

- [ ] Lockdown 진입/해제 조건이 문서/코드 모두에서 일치한다.
