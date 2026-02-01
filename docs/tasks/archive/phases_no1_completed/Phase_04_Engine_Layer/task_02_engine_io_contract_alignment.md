# Phase 4 — Engine Layer: I/O Contract Alignment

## 목표

- Engine Input/Output Contract를 문서 기준으로 고정하고, ETEDA 단계에서 안정적으로 연결

## 근거

- `docs/arch/02_Engine_Core_Architecture.md`
- `docs/arch/04_Data_Contract_Spec.md`

## 작업

- [x] Strategy/Risk/Portfolio/Trading/Performance I/O 경계를 코드에서 확인/정리
- [x] Engine 상태 모델(FAULT 등)과 예외/에러 모델의 적용 범위 확정
- [x] 코드 품질 개선(필수)
  - [x] 엔진 생성자/메서드 시그니처와 테스트 코드 간 불일치 해소

## 완료 조건

- [x] Engine Layer 호출 규칙이 ETEDA Evaluate/Decide/Act 단계와 정합하다.
- [x] 테스트가 엔진의 “현재 인터페이스”를 기준으로 통과한다.

## 구현 정리

- **execute() I/O Contract**: `base_engine.execute()` docstring에 Input(operation 필수) / Output(success, data|error, execution_time) 명시. Strategy/Portfolio/Performance 모두 동일 규칙 적용.
- **Engine State Model**: `BaseEngine._state_kind()` 추가 — OK / WARNING(error_count≥1) / FAULT(error_count≥10). `get_status()`, `health_check()`에 `state_kind` 포함.
- **StrategyEngine.execute()**: 기존 `return {}` → Contract 정합 형태(success, data, execution_time) 반환. operation `calculate_signal` 지원.
- **PortfolioEngine 테스트**: 생성자에 position_repo, portfolio_repo, t_ledger_repo 목 주입. 결정적 픽스처만 사용.
- **UnifiedConfig**: 엔진용 단일 키 조회 `get_flat(key, default)` 추가. PortfolioEngine은 `get_flat('BASE_EQUITY'|'KILLSWITCH_STATUS')` 사용.
