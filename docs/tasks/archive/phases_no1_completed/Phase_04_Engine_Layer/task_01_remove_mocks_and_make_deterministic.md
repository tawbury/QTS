# Phase 4 — Engine Layer: Remove Mocks & Make Deterministic

## 목표

- 엔진 계층에서 Mock/Random 기반 결과를 제거하고 실제 데이터 기반으로 동작하도록 정리

## 근거

- `docs/arch/02_Engine_Core_Architecture.md`
- 코드:
  - `src/runtime/engines/performance_engine.py`
  - `src/runtime/engines/portfolio_engine.py`

## 작업

- [x] 코드 품질 개선(필수)
  - [x] `PerformanceEngine`의 mock 생성 경로(`_generate_mock_*`) 제거 또는 테스트 전용으로 격리
  - [x] 랜덤/seed 기반 결과가 런타임 결과에 섞이지 않도록 방지
- [x] 실제 데이터 경로 강화
  - [x] History/Performance repository 기반 KPI 산출 흐름 점검

## 완료 조건

- [x] 런타임 엔진 결과가 “실제 데이터 기반”으로만 생성된다.
- [x] Mock 로직은 테스트 전용 경로로만 존재한다(또는 제거).
