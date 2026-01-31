# Phase 5 — ETEDA Pipeline: Trigger & Loop Control

## 목표

- 파이프라인을 실행 루프/스케줄러와 안전하게 연결(ETEDA 원칙을 위반하지 않도록)

## 근거

- `docs/arch/03_Pipeline_ETEDA_Architecture.md`

## 작업

- [x] 실행 루프 정책 확정
  - [x] interval 기반 vs event 기반 트리거의 우선순위/병행 규칙
  - [x] 루프 중단/재시작/에러 백오프 규칙
- [x] 코드 품질 개선(필수)
  - [x] 루프/트리거 코드가 ETEDA 단계 책임을 침범하지 않도록 정리

## 완료 조건

- [x] 반복 실행 중 장애가 발생해도 안전하게 중단/복구할 수 있다.

## 구현 요약

- **정책**: `src/runtime/execution_loop/eteda_loop_policy.py`
  - 트리거: interval 우선(Config `INTERVAL_MS`). event는 스냅샷 소스로 주입 가능. run_once 중복 실행 금지(한 사이클 1회).
  - 중단: Config `PIPELINE_PAUSED` 또는 외부 `should_stop` → 루프 탈출. 재시작 = 새 루프 실행.
  - 에러 백오프: run_once 예외 시 `ERROR_BACKOFF_MS` 대기 후 재시도, `ERROR_BACKOFF_MAX_RETRIES` 초과 시 루프 중단.
- **루프**: `src/runtime/execution_loop/eteda_loop.py` — `run_eteda_loop(runner, config, ...)` async. 루프 내부는 `runner.run_once(snapshot)` 호출만 수행(Extract/Transform/Evaluate/Decide/Act는 Runner에만 존재).
- **테스트**: `tests/runtime/execution_loop/test_eteda_loop.py` — 정책 from_config, should_stop, 연속 예외 시 안전 중단 검증.
