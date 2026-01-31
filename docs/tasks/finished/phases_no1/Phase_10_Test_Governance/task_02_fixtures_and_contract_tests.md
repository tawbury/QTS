# Phase 10 — Test/Governance: Fixtures & Contract Tests

## 목표

- Raw/Calc/Engine/UI Contract의 구조를 fixture 기반으로 검증하여 회귀를 방지

## 근거

- `docs/arch/10_Testability_Architecture.md`

## 작업

- [x] fixture 형식/버전 정책 정의
- [x] Contract validation 테스트 추가
- [x] 코드 품질 개선(필수)
  - [x] Contract 변경이 있을 때 테스트가 즉시 깨지도록(조기 감지) 설계

## 완료 조건

- [x] Contract 회귀가 자동으로 감지된다.

## 산출물

- **[Fixtures_and_Contract_Policy.md](./Fixtures_and_Contract_Policy.md)** — Fixture 형식/버전 정책, Contract validation 테스트 설계(조기 감지).
- **tests/fixtures/contracts.py** — Contract 검증용 최소 유효 fixture 상수.
- **tests/contracts/test_contract_validation.py** — ExecutionIntent/ExecutionResponse/OrderDecision/ExecutionHint/UI Contract 구조 검증 테스트(8개).
