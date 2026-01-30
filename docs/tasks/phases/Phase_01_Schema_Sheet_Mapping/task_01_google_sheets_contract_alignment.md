# Phase 1 — Schema & Sheet Mapping

## 목표

- Schema/Repository/Google Sheets Client 경로를 실제 코드 기준으로 정합화
- Sheet I/O Contract(필드/헤더/타입)와 Repository CRUD 경계를 고정

## 근거

- `docs/Roadmap.md`
- `docs/arch/01_Schema_Auto_Architecture.md`
- `docs/arch/04_Data_Contract_Spec.md`
- 코드:
  - `src/runtime/data/google_sheets_client.py`
  - `src/runtime/data/repositories/base_repository.py`
  - `src/runtime/data/repository_manager.py`

## 작업

- [ ] `GoogleSheetsClient` 사용 계약 정리
  - [ ] 인증/스프레드시트/워크시트 접근 API를 “단일 진입점”으로 확정
  - [ ] 예외 타입(인증/레이트리밋/검증)에 대한 호출자 처리 기준을 문서화
- [ ] Repository 공통 계약 고정
  - [ ] `BaseSheetRepository`의 CRUD/헤더/캐시 동작을 문서 기준과 맞추기
  - [ ] 헤더 누락/컬럼 변경 시 Fail-Safe 수준 정의(에러 vs 자동 복구)
- [ ] 코드 품질 개선(필수)
  - [ ] Repository/Client 층에서 임시 로직/중복 변환 로직 제거(정합화 후)

## 완료 조건

- [ ] Repository가 동일한 “Range/Headers/Row Mapping” 규칙을 따른다.
- [ ] 실패 시 예외/에러 반환 규칙이 문서화되어 있다.
