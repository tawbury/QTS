# Phase 10 — Test/Governance: Test Suite Structure

## 목표

- 테스트 계층(Unit/Engine/Contract/Integration/E2E)을 문서 기준으로 정리하고 실행 가능하게 유지

## 근거

- `docs/arch/10_Testability_Architecture.md`
- 테스트 폴더: `tests/`

## 작업

- [x] 테스트 계층별 경로/규칙을 문서로 고정
- [x] flaky test/환경 의존 테스트 분리 정책 수립
- [x] 코드 품질 개선(필수)
  - [x] 테스트가 실제 코드 인터페이스와 어긋난 부분 제거 (검증 완료: `RetentionPolicy` 별칭·`ExecutionMode` 사용처 일치)

## 완료 조건

- [x] 테스트 실행 절차가 단일 문서로 정리되어 있다.

## 산출물

- **[Test_Suite_Structure_and_Execution.md](./Test_Suite_Structure_and_Execution.md)** — 테스트 계층 경로·규칙, flaky/환경 의존 분리 정책, 실행 절차 단일 문서.
