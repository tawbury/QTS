# Phase 6 — UI/Dashboard: Renderers & R_Dash Writer

## 목표

- UI Rendering Unit(Renderer)을 정의하고, 필요 시 `R_Dash` 시트를 업데이트하는 Writer 경로를 확정

## 근거

- `docs/arch/06_UI_Architecture.md`
- 코드:
  - `src/runtime/data/repositories/r_dash_repository.py`

## 작업

- [ ] Rendering Unit 설계
  - [ ] account/portfolio/performance/risk/pipeline status 단위 renderer 정의
- [ ] R_Dash 업데이트 정책
  - [ ] 언제(ETEDA 사이클 종료) 어떤 데이터로 갱신할지 규칙 확정
- [ ] 코드 품질 개선(필수)
  - [ ] UI 갱신이 ETEDA 실행을 방해하지 않도록 비동기/격리 규칙 반영

## 완료 조건

- [ ] UI 렌더링이 ETEDA와 분리되어 있으며, R_Dash 업데이트 규칙이 고정되어 있다.
