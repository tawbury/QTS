# Phase 4 — Engine Tests & Benchmarks

## 목표

- 엔진 계산의 정확성과 회귀 안정성을 테스트(및 필요 시 벤치마크)로 고정

## 근거

- `docs/arch/10_Testability_Architecture.md`
- 테스트:
  - `tests/engines/`

## 작업

- [x] 엔진 단위 테스트 보강
  - [x] 경계값(0/음수/결측/NaN) 케이스 추가
  - [x] 결정론적 입력 대비 결정론적 출력 보장
- [x] 코드 품질 개선(필수)
  - [x] 테스트가 “Mock 의존”이 아니라 “계약 검증” 중심이 되도록 정리

## 완료 조건

- [x] 엔진 핵심 KPI 산출이 회귀 테스트로 고정된다.

## 구현 정리

- **PerformanceEngine**: `TestPerformanceEngineKpiBoundaryAndRegression` 추가 — 경계(빈/0/전부 양수·음수), 결정론적 회귀(total_return/MDD/profit_factor/max_consecutive_losses 고정 입력→고정 값), 계약(PerformanceMetrics 필드·타입·mdd≥0, 0≤win_rate≤1, NaN 아님).
- **PortfolioEngine**: `TestPortfolioEngineBoundaryAndContract` 추가 — 경계(빈 포지션→holdings_count 0, exposure 0, allocation {}), 계약(Summary/Position 필드·타입·exposure/cash_ratio 0~1, allocation 합 ≈1).
- 테스트 모듈 docstring: “계약 검증 중심, Mock 호출 수 비의존” 명시.
