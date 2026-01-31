# Phase 4 — Data Layer: Missing Repositories Implementation

## 목표

- 10 Google Sheets + Config_Local(1) Data Layer 리포지토리 정합
- Enhanced 타입 리포지토리의 역할 명확화

## 근거

- Dividend, Strategy, R_Dash 시트에 대한 리포지토리 구현 및 삭제된 시트(DI_DB, DT_Report) 제거
- 아키텍처 문서의 10+1 시트 모델(00_Architecture.md) 반영
- Data Layer의 전체적인 정합성 확보

## 작업

- [x] Repository 구현·정리
  - [x] `src/runtime/data/repositories/dividend_repository.py` (기존 존재)
  - [x] `src/runtime/data/repositories/strategy_repository.py` 구현
  - [x] `src/runtime/data/repositories/r_dash_repository.py` (기존 존재)
  - [x] DI_DB, DT_Report 시트 삭제에 따라 `di_db_repository.py`, `dt_report_repository.py` 제거
- [x] Enhanced Repository 패턴 정리
  - [x] `EnhancedPortfolioRepository` 역할 및 책임 명확화
  - [x] `EnhancedPerformanceRepository` 역할 및 책임 명확화
  - [x] Enhanced vs 일반 Repository의 구분 기준 확정
- [x] Data Layer Integration
  - [x] `RepositoryManager.register_all_base_repositories` — Position, History, T_Ledger, Dividend, Strategy, R_Dash 등록 (DI_DB/DT_Report 제외)
- [x] Repository Testing
  - [x] Strategy 리포지토리 단위 테스트 (`test_new_repositories.py`)
  - [x] Google Sheets 연동 통합 테스트 (`test_google_sheets_integration.py`)

## 완료 조건

- [x] 10+1 시트 모델에 맞는 Repository만 유지 (DI_DB/DT_Report 제거)
- [x] Enhanced Repository 패턴이 명확히 정의됨
- [x] Data Layer가 아키텍처와 일치

## 구현 정리

- **Base 등록 시트**: Position, History, T_Ledger, Dividend, Strategy, R_Dash. DI_DB/DT_Report는 삭제된 시트로 리포지토리 제거.
- **Enhanced vs Base**: `src/runtime/data/repositories/README.md` — Base = 시트 고정명 + 헤더 기반 CRUD, Enhanced = SchemaBasedRepository + 스키마 연동. 10+1 시트 대응 표.
- **단위 테스트**: `tests/runtime/data/test_new_repositories.py` — StrategyRepository 계약 검증.
- **통합 테스트**: `tests/runtime/data/test_google_sheets_integration.py` — .env 기반 Strategy get_all 및 RepositoryManager health_check.
