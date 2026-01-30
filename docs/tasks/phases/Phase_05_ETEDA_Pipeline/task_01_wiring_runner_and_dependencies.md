# Phase 5 — ETEDA Pipeline: Wiring (Runner & Dependencies)

## 목표

- `ETEDARunner`와 Engine/Repository 의존성 주입 경로를 정합화

## 근거

- `docs/arch/03_Pipeline_ETEDA_Architecture.md`
- 코드:
  - `src/runtime/pipeline/eteda_runner.py`
  - `src/runtime/data/repository_manager.py`

## 작업

- [ ] Runner 의존성 주입 규칙 확정
  - [ ] 스프레드시트 ID/시트명/리포지토리 생성 책임 분리
- [ ] 코드 품질 개선(필수)
  - [ ] Runner 내부에서 “임시 생성/매직 값”을 제거하고 Config 계약으로 통일

## 완료 조건

- [ ] Runner가 명확한 입력(snapshot) + Config + Repository/Engine wiring으로 1회 실행 가능하다.
