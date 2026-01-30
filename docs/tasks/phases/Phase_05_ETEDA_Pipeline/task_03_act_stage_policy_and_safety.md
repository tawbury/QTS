# Phase 5 — ETEDA Pipeline: Act Stage Policy & Safety

## 목표

- Act 단계(주문 실행)의 정책/가드/모드(VIRTUAL/SIM/REAL)를 명확히 정의하고 코드에 반영

## 근거

- `docs/arch/03_Pipeline_ETEDA_Architecture.md`
- `docs/arch/07_FailSafe_Architecture.md`
- 코드:
  - `src/ops/decision_pipeline/execution_stub/*`

## 작업

- [ ] 실행 모드 정책 정리
  - [ ] VIRTUAL/SIM/REAL 모드 정의 및 전환 조건
- [ ] Guard/Fail-Safe 연계
  - [ ] Fail-Safe 조건과 Act 중단 규칙을 코드 레벨에서 일관화
- [ ] 코드 품질 개선(필수)
  - [ ] “stub/executor” 구현이 실제 정책과 어긋나지 않도록 정합화

## 완료 조건

- [ ] Act 단계가 정책 기반으로만 활성화된다.
- [ ] 실행 결과(ExecutionResult)가 문서 계약과 정합하다.
