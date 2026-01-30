# Data Layer Repositories

10 Google Sheets + Config_Local(1) Data Layer 리포지토리 구현. docs/arch/00_Architecture.md 및 04_Data_Contract_Spec.md 기준.

## Base vs Enhanced 구분

| 구분 | BaseSheetRepository 계열 | Enhanced (SchemaBasedRepository) 계열 |
|------|--------------------------|--------------------------------------|
| **역할** | 시트 고정 이름 + 헤더 기반 CRUD | 스키마 파일 기반 필드 매핑 + KPI/블록 업데이트 |
| **시트 구조** | `get_headers()`로 동적 읽기, `required_fields`로 검증 | Schema Automation Engine 연동, `sheet_key`로 시트/블록 결정 |
| **용도** | Position, History, Dividend, Strategy, R_Dash 등 Raw 데이터 시트 | Portfolio, Performance 등 대시보드/KPI 시트 |
| **예시** | PositionRepository, HistoryRepository, StrategyRepository | EnhancedPortfolioRepository, EnhancedPerformanceRepository |

- **Enhanced**: 스키마 로더 + `project_root` 필요, `update_kpi_summary` / `update_kpi_overview` 등 KPI 전용 메서드 제공. CRUD는 대시보드용으로 빈 구현 가능.
- **Base**: `client` + `spreadsheet_id` + `sheet_name`만으로 동작. 모든 CRUD를 시트 행 단위로 구현.

## 10+1 시트 대응 (Google 10 + 로컬 1)

| 시트 | 리포지토리 | 비고 |
|------|------------|------|
| Position | PositionRepository | Base |
| History | HistoryRepository | Base |
| T_Ledger | T_LedgerRepository | Base |
| Portfolio | EnhancedPortfolioRepository | Enhanced |
| Performance | EnhancedPerformanceRepository | Enhanced |
| Config_Scalp / Config_Swing | ConfigScalpRepository, ConfigSwingRepository | Base |
| Dividend | DividendRepository | Base |
| Strategy (파라미터) | StrategyRepository | Base |
| Strategy (성과) | StrategyPerformanceRepository | Base |
| R_Dash | R_DashRepository | Base |
| Config_Local | 로컬 설정 (별도) | 로컬 1개 시트 |
