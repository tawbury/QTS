# Phase 7 — Safety/Risk: Tests & Alerting

## 목표

- Fail-Safe/Guardrail/Anomaly 조건을 테스트 가능하게 만들고, 운영자 알림(최소 수준)을 정의한다.

## 근거

- `docs/arch/10_Testability_Architecture.md`
- `docs/arch/07_FailSafe_Architecture.md`

## 작업

- [x] Safety Layer 테스트 시나리오 정의
  - [x] 데이터 손상/브로커 오류/리스크 초과/시스템 자원 이슈
- [x] 알림(Notifier) 최소 규격 정의
- [x] 코드 품질 개선(필수)
  - [x] 테스트 가능한 구조(순수 함수/의존성 주입)를 우선 적용

## 구현 요약

### Safety Layer 테스트 시나리오 (자동 테스트)

| 시나리오 | 코드 | 테스트 위치 |
|----------|------|-------------|
| 데이터 손상(스키마 불일치) | FS001 | test_safety_guard.py / TestExtractSafety |
| 데이터 손상(RawData 누락) | FS010 | test_safety_guard.py / TestExtractSafety |
| Transform NaN/Inf | FS020 | test_safety_guard.py / TestTransformSafety |
| 리스크 계산 오류 | FS030 | test_safety_guard.py / TestEvaluateSafety |
| 브로커/실행 오류 | FS040 | test_safety_guard.py / TestActSafety |
| Equity <= 0 | FS050 | test_safety_guard.py / TestTransformSafety |
| Position-Ledger 불일치 | FS070 | test_safety_guard.py / TestTransformSafety |
| Guardrail(GR030/GR040, G_EXE_*) | GR* | test_safety_guard.py / TestDecideSafety |
| 상태 전이 / Lockdown | NORMAL→FAIL→LOCKDOWN, Recovery | test_safety_state.py |
| 코드 테이블 / 메시지 | FS/GR/AN, message_for, codes_by_stage | test_safety_codes.py |

테스트 디렉터리: `tests/ops/safety/` (test_safety_codes.py, test_safety_guard.py, test_safety_state.py, test_safety_notifier.py). 실행: `PYTHONPATH=src pytest tests/ops/safety/ -v`.

### 알림(Notifier) 최소 규격 (Arch §9.1, §9.3)

| 항목 | 위치 | 설명 |
|------|------|------|
| Safety 이벤트 구조 | `src/ops/safety/notifier.py` | `SafetyEvent`: timestamp, safety_code, level, message, pipeline_state, meta (§9.1) |
| 메시지 템플릿 | `default_message_template(event)` | Fail-Safe 알림용 표준 메시지 (§9.3) |
| Notifier 프로토콜 | `SafetyNotifier` (Protocol) | `notify(event: SafetyEvent) -> None` — 의존성 주입용 |
| 기본 구현체 | `NoOpNotifier`, `InMemoryNotifier` | 기본값/테스트용; Slack/Telegram/Email은 동일 규격으로 구현 가능 |

### 테스트 가능 구조

- Guard 체크: 순수 함수 (`check_extract_safety`, `check_transform_safety` 등) — 부작용 없음.
- State: `SafetyStateManager` — 명시적 이벤트로 전이, 테스트에서 상태 재현 용이.
- Notifier: `SafetyNotifier` 프로토콜로 주입 — 테스트 시 `InMemoryNotifier` 사용.

## 완료 조건

- [x] 대표 Fail-Safe 조건이 자동 테스트로 재현된다.
