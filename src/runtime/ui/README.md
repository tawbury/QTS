# Dashboard (Zero-Formula UI) — 진입점 및 렌더링 경로 (Phase 6)

UI Contract 빌더·렌더러·R_Dash Writer 경로 정리. **근거**: [docs/arch/06_UI_Architecture.md](../../../docs/arch/06_UI_Architecture.md), [UI_Contract_Schema.md](../../../docs/arch/UI_Contract_Schema.md)

---

## 1. 진입점·Wiring

| 컴포넌트 | 경로 | 진입점 | 비고 |
|----------|------|--------|------|
| **UI Contract 빌더** | `contract_builder.py` | `UIContractBuilder.build(account, symbols, pipeline_status, performance=None, risk=None, meta_overrides=None)` | account·pipeline_status·symbols 필수. 단일 진입점. |
| **Contract 스키마/버전** | `contract_schema.py` | `UIContractVersion`, `get_expected_contract_version()` | 버전 불일치 시 R_DashWriter 갱신 중단 (06 §10.1) |
| **Zero-Formula 렌더러** | `renderers/` | `render_account_summary`, `render_symbol_detail`, `render_risk_monitor`, `render_performance`, `render_pipeline_status`, `render_meta_block` | Contract 블록 → `List[List[Any]]` (값만, 수식 없음) |
| **R_Dash Writer** | `r_dash_writer.py` | `R_DashWriter(client)` → `write(contract)` / `schedule_write(contract)` | Contract 버전 검사 후 블록별 렌더러 호출 → 시트 범위 갱신. ETEDA 블록 방지: `schedule_write` 권장 |
| **R_Dash 리포지토리** | `../data/repositories/r_dash_repository.py` | `R_DashRepository(client, spreadsheet_id)`. 시트명 "R_Dash". RepositoryManager 등록 | BaseSheetRepository |

---

## 2. 셀 영역 (R_Dash 시트)

| 상수 | 범위 | 비고 |
|------|------|------|
| R_DASH_ACCOUNT | R_Dash!A1:E10 | 계좌 요약 |
| R_DASH_SYMBOLS | R_Dash!A12:H40 | 종목 상세 |
| R_DASH_RISK | R_Dash!F1:I20 | 리스크 모니터 |
| R_DASH_PERFORMANCE | R_Dash!J1:N20 | 성과 요약 |
| R_DASH_PIPELINE | R_Dash!F25:I33 | 파이프라인 상태 |
| R_DASH_META | R_Dash!J25:N33 | 메타 |

---

## 3. 테스트 경로

- `tests/contracts/test_contract_validation.py` — UI Contract 루트/메타 필수 키·버전 일치.
- `tests/runtime/ui/test_ui_renderers.py` — 렌더러 입출력(List[List[Any]]), UIContractBuilder 필수 필드·출력 구조.

기본 실행: `pytest tests/contracts/ tests/runtime/ui/ -v`

---

## 4. UI 실패 시 정책

UI 갱신 실패는 **매매 중단 사유가 아님**. [Phase_06_UI_Dashboard/UI_실패_정책.md](../../../docs/tasks/phases/Phase_06_UI_Dashboard/UI_실패_정책.md) (§2.2)
