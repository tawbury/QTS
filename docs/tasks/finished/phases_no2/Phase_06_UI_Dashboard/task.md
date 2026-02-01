# Phase 6 — Dashboard / Visualization (로드맵 기준 Task)

## 목표

- **Dashboard(Zero-Formula UI) 구현 범위 확정 및 최소 렌더링 경로 정의**
- R_Dash 리포지토리와 Zero-Formula UI 렌더러/계약 빌더 경로를 문서·코드에서 명확히 하고 테스트 추가
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 6, Section 3 (다음 우선순위)
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.2
- 코드: `src/runtime/data/repositories/r_dash_repository.py`
- 아키텍처: [docs/arch/06_UI_Architecture.md](../../../arch/06_UI_Architecture.md), [docs/arch/UI_Contract_Schema.md](../../../arch/UI_Contract_Schema.md)

---

## Roadmap Section 2 — Phase 6 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| R_Dash 리포지토리 | ✅ | wiring·테스트 정합 (src/runtime/ui/README.md, tests/contracts·tests/runtime/ui) |
| Zero-Formula UI 렌더링/계약 빌더 | ✅ | 전용 경로 정의·최소 구현 (contract_builder, contract_schema, renderers/, r_dash_writer, zero_formula_base) |

---

## Wiring 요약 (현행)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| R_Dash 리포지토리 | `R_DashRepository(client, spreadsheet_id)` | BaseSheetRepository. 시트명 "R_Dash". RepositoryManager 등록 |
| UI Contract 빌더 | `UIContractBuilder.build(account, symbols, pipeline_status, performance=None, risk=None, meta_overrides=None)` | 단일 진입점. account·pipeline_status·symbols 필수. 스키마: `docs/arch/UI_Contract_Schema.md` |
| Contract 스키마/버전 | `contract_schema.UIContractVersion`, `get_expected_contract_version()` | 버전 불일치 시 R_DashWriter가 갱신 중단 (06 §10.1) |
| Zero-Formula 렌더러 | `renderers/`: `render_account_summary`, `render_symbol_detail`, `render_risk_monitor`, `render_performance`, `render_pipeline_status`, `render_meta_block` | Contract 블록 → `List[List[Any]]` (값만, 수식 없음). `zero_formula_base.BlockRenderer` 프로토콜 |
| R_Dash Writer | `R_DashWriter(client)` → `write(contract)` / `schedule_write(contract)` | Contract 버전 검사 후 각 블록별 렌더러 호출 → 시트 범위 갱신. ETEDA 블록 방지: `schedule_write` 권장 |
| 셀 영역 | R_DASH_ACCOUNT, R_DASH_SYMBOLS, R_DASH_RISK, R_DASH_PERFORMANCE, R_DASH_PIPELINE, R_DASH_META | `r_dash_writer.py` 상수. 06_UI_Architecture §8.1 |

---

## 미결 사항

| 미결 항목 | 진행 단계 | 비고 |
|-----------|-----------|------|
| Zero-Formula 최소 구현 범위 문서 확정 | ✅ 완료 | 전용 경로: contract_builder, contract_schema, renderers/, r_dash_writer, zero_formula_base. src/runtime/ui/README.md |
| R_Dash·렌더러 wiring·테스트 정합 | ✅ 완료 | R_DashRepository·R_DashWriter·렌더러 경로 명확. tests/contracts·tests/runtime/ui |
| UI Contract/렌더러 테스트 | ✅ 완료 | Contract 버전·필수 필드(tests/contracts). 렌더러 입출력·UIContractBuilder(tests/runtime/ui/test_ui_renderers.py) |
| UI 실패 시 매매 중단 아님 정책 | ✅ 완료 | [UI_실패_정책.md](./UI_실패_정책.md) — 04 §7.4·06 §10 반영 |
| Dashboard 진입점·렌더링 경로 문서화 | ✅ 완료 | src/runtime/ui/README.md, 본 task Wiring 요약 |
| Roadmap Phase 6 비고 해소 | ✅ 완료 | 전용 렌더러/계약 빌더 경로 확정. Exit Criteria §2.1·§2.2·§2.3 충족 |

---

## 작업 (체크리스트)

- [x] **구현 범위 확정**
  - [x] Zero-Formula UI 렌더러·계약 빌더 “최소 구현 범위” 문서 확정 (src/runtime/ui/README.md)
  - [x] 전용 경로 명확: contract_builder, contract_schema, renderers/, r_dash_writer, zero_formula_base
- [x] **테스트**
  - [x] UI Contract/렌더러 테스트 추가·인터페이스 일치 (tests/contracts TestUIContract, tests/runtime/ui/test_ui_renderers.py)
  - [x] UI 실패 시 매매 중단 아님 정책 문서화 (§2.2) — [UI_실패_정책.md](./UI_실패_정책.md)
- [x] **문서**
  - [x] Dashboard 진입점·렌더링 경로·UI Contract 스키마 문서화 (ui/README.md, 06_UI_Architecture, UI_Contract_Schema)
  - [x] Roadmap Phase 6 비고(“전용 렌더러/계약 빌더 미확정”) 해소

---

## 완료 조건 (Exit Criteria)

- [x] 필수 테스트 통과 (§2.1) — `pytest tests/contracts/ tests/runtime/ui/ -v`
- [x] 운영 체크(UI 실패 시 정책) (§2.2) — [UI_실패_정책.md](./UI_실패_정책.md)
- [x] 문서 SSOT 반영 (§2.3) — 06_UI_Architecture, UI_Contract_Schema, ui/README.md
