# Phase 1 — Repository Coverage & Integration Tests

## 목표

- 9-Sheet(또는 운영 대상 Sheet) 리포지토리의 기능 커버리지와 안정성을 테스트로 고정

## 근거

- `docs/arch/10_Testability_Architecture.md`
- `docs/tasks/backups/google_sheets_integration/*`
- 테스트:
  - `tests/google_sheets_integration/`
  - `tests/runtime/data/test_google_sheets_client.py`

## 작업

- [ ] 통합 테스트 범위 확정
  - [ ] 필수 시트(T_Ledger/Position/History/Strategy_Performance/R_Dash/Config_*)별 최소 시나리오 정의
- [ ] 테스트 데이터/환경 분리
  - [ ] 실 스프레드시트 기반 테스트 vs Mock 기반 테스트 경계 명확화
  - [ ] CI 환경에서 민감정보(서비스 계정 키) 취급 규칙 확정
- [ ] 코드 품질 개선(필수)
  - [ ] 테스트가 “코드 실제 인터페이스”와 불일치하는 부분 제거(시그니처/경로/클래스명)

## 완료 조건

- [ ] 리포지토리별 최소 CRUD + 핵심 쿼리 시나리오가 통과한다.
- [ ] 실패 시 원인(인증/네트워크/스키마 불일치)이 로그/리포트로 분리된다.
