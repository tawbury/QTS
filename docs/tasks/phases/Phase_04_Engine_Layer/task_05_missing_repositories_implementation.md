# Phase 4 — Data Layer: Missing Repositories Implementation

## 목표

- 9-Sheet Data Layer의 누락된 리포지토리 구현
- Enhanced 타입 리포지토리의 역할 명확화

## 근거

- DI_DB, Dividend, DT_Report, Strategy, R_Dash 시트에 대한 리포지토리 부재
- 아키텍처 문서의 9-Sheet 모델 완성 필요
- Data Layer의 전체적인 정합성 확보

## 작업

- [x] 누락된 Repository 구현
  - [x] `src/runtime/data/repositories/di_db_repository.py` 구현
  - [x] `src/runtime/data/repositories/dividend_repository.py` 구현 (기존 존재)
  - [x] `src/runtime/data/repositories/dt_report_repository.py` 구현
  - [x] `src/runtime/data/repositories/strategy_repository.py` 구현
  - [x] `src/runtime/data/repositories/r_dash_repository.py` 구현 (기존 존재)
- [x] Enhanced Repository 패턴 정리
  - [x] `EnhancedPortfolioRepository` 역할 및 책임 명확화
  - [x] `EnhancedPerformanceRepository` 역할 및 책임 명확화
  - [x] Enhanced vs 일반 Repository의 구분 기준 확정
- [ ] Data Layer Integration
  - [ ] 모든 Repository가 Schema Automation Engine과 연동되도록 수정
  - [ ] Repository 간 데이터 정합성 검증 로직 강화
- [x] Repository Testing
  - [x] 각 Repository 단위 테스트 구현
  - [ ] Google Sheets 연동 통합 테스트

## 완료 조건

- [x] 9-Sheet 모든 시트에 대한 Repository가 구현됨
- [x] Enhanced Repository 패턴이 명확히 정의됨
- [ ] Data Layer가 완전히 통합됨

## 구현 정리

- **누락 리포지토리**: `DI_DBRepository`(DI_DB, symbol 기준 CRUD), `DT_ReportRepository`(DT_Report, Date 기준 CRUD), `StrategyRepository`(Strategy 파라미터, param_name/value/description, param_name 기준 CRUD) 추가. Dividend, R_Dash는 기존 구현 유지.
- **Enhanced vs Base**: `src/runtime/data/repositories/README.md`에 구분 기준 정리 — Base = 시트 고정명 + 헤더 기반 CRUD, Enhanced = SchemaBasedRepository + 스키마 연동 + KPI/블록 업데이트. 9-Sheet 대응 표 추가.
- **단위 테스트**: `tests/runtime/data/test_new_repositories.py` — DI_DB/DT_Report/Strategy 리포지토리 목 클라이언트 기반 get_all(빈 리스트)/get_by_id(미존재 시 None) 계약 검증.
