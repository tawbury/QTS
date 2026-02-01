# Phase 2 — Config Architecture (Sheet) (로드맵 기준 Task)

## 목표

- **Config Sheet 로딩 경로**를 현재 `GoogleSheetsClient` 인터페이스에 맞게 정리
- Config 3분할 모델/머지 로직과 Sheet 기반 Config 로딩의 wiring 일치
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 2, Section 3 (다음 우선순위)
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.1
- 코드: `src/runtime/config/config_loader.py`, `src/runtime/config/config_models.py`, `src/runtime/config/sheet_config.py`

---

## Roadmap Section 2 — Phase 2 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| Config 3분할 모델/머지 로직 | ✅ | 문서·코드 일치 (13_Config_3분할 §3.3 = config_loader._merge_configs, Local 우선) |
| Sheet 기반 Config 로딩 | ✅ | `sheet_config.py`가 GoogleSheetsClient 인터페이스와 정합 (client=None/env 생성, client 주입 지원) |

---

## Wiring 요약 (현행)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| Config 3분할 | `config_loader.load_unified_config(project_root, scope)` | Local 로드 → Sheet 로드 → 머지(Local 우선). SSOT: `docs/arch/13_Config_3분할_Architecture.md` |
| Sheet Config 로딩 | `sheet_config.load_sheet_config(project_root, scope, client=None)` | client 없으면 env 기반 `GoogleSheetsClient()` 생성·인증. client 주입 시 해당 인스턴스 사용(Phase 1 시그니처 정합) |
| Config 모델 | `ConfigEntry`, `ConfigLoadResult`, `ConfigMergeResult`, `UnifiedConfig` | `config_models.py`. 엔진은 UnifiedConfig만 수신 |

---

## 미결 사항

| 미결 항목 | 진행 단계 | 비고 |
|-----------|-----------|------|
| sheet_config–Client 정합 | ✅ 완료 | `load_sheet_config(..., client=None)`. 호출부에서 클라이언트 주입 가능 |
| Config 3분할 문서·코드 일치 | ✅ 완료 | 13_Config_3분할 §3.3 = config_loader._merge_configs (Local 우선, conflicts 목록) |
| tests/config/ Sheet 로딩 테스트 | ✅ 완료 | test_sheet_config.py 추가 (Mock client, invalid scope, client 주입, validate) |
| Config 로딩 실패 시 운영 체크 문서화 | ✅ 완료 | [Config_Sheet_운영_체크.md](./Config_Sheet_운영_체크.md) — 404/인증/파싱 시나리오·대응 |
| Roadmap Phase 2 비고 해소 | ✅ 완료 | 시그니처·테스트·운영 체크 문서 반영 |

---

## 작업 (체크리스트)

- [x] **Config Sheet 로딩 정합성**
  - [x] `sheet_config.py` 호출 경로를 현재 `GoogleSheetsClient` API에 맞게 수정 (client=None/env 생성, client 주입)
  - [x] 생성자/호출부 불일치 제거 (Phase 1 Contract·data/README와 정합)
- [x] **테스트**
  - [x] `tests/config/` Config 로딩 테스트가 현재 인터페이스와 일치하고 통과 (test_local_config + test_sheet_config)
- [x] **문서**
  - [x] Config 3분할/Sheet 로딩 진입점·wiring 문서화 (본 task Wiring 요약, 13_Config_3분할, Config_Sheet_운영_체크)
  - [x] Roadmap Phase 2 비고(“sheet_config–Client 불일치”) 해소

---

## 완료 조건 (Exit Criteria)

- [x] 필수 테스트 통과 (§2.1) — `pytest tests/config/ -v`
- [x] 설정 로딩 실패 시 운영 체크 문서화 (§2.2) — [Config_Sheet_운영_체크.md](./Config_Sheet_운영_체크.md)
- [x] 문서 SSOT 반영 (§2.3) — 13_Config_3분할, config_loader·sheet_config 코드와 일치
