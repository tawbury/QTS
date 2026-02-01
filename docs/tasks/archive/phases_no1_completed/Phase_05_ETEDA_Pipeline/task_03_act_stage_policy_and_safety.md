# Phase 5 — ETEDA Pipeline: Act Stage Policy & Safety

## 목표

- Act 단계(주문 실행)의 정책/가드/모드(VIRTUAL/SIM/REAL)를 명확히 정의하고 코드에 반영

## 근거

- `docs/arch/03_Pipeline_ETEDA_Architecture.md`
- `docs/arch/07_FailSafe_Architecture.md`
- 코드:
  - `src/ops/decision_pipeline/execution_stub/*`

## 작업

- [x] 실행 모드 정책 정리
  - [x] VIRTUAL/SIM/REAL 모드 정의 및 전환 조건
- [x] Guard/Fail-Safe 연계
  - [x] Fail-Safe 조건과 Act 중단 규칙을 코드 레벨에서 일관화
- [x] 코드 품질 개선(필수)
  - [x] "stub/executor" 구현이 실제 정책과 어긋나지 않도록 정합화

## 완료 조건

- [x] Act 단계가 정책 기반으로만 활성화된다.
- [x] 실행 결과(ExecutionResult)가 문서 계약과 정합하다.

## 구현 요약

- **정책 문서**: `docs/tasks/phases/Phase_05_ETEDA_Pipeline/act_stage_policy.md` — VIRTUAL/SIM/REAL 정의, 전환 조건(Config+Guard), Guard/Fail-Safe 연계, ExecutionResult 계약 및 Ledger 계약 참조.
- **실행 모드**: `src/ops/decision_pipeline/execution_stub/execution_mode.py` — 모드 주석 및 정책 문서 참조 추가.
- **Guard 일관화**: SimExecutor가 apply_execution_guards 사용하도록 변경; Guard 코드(G_EXE_*) 통일. VirtualExecutor는 기존대로 Guard 사용.
- **Act 정책 게이트**: `src/runtime/pipeline/eteda_runner.py` — _act 진입 전 trading_enabled/KILLSWITCH_STATUS/PIPELINE_PAUSED/safe_mode 검사로 정책 기반 활성화.
- **ExecutionResult 계약**: `src/ops/decision_pipeline/execution_stub/execution_result.py` — 모듈 독스트링에 Act 정책 결과 계약 및 Ledger 계약(04_Data_Contract_Spec §6) 참조.