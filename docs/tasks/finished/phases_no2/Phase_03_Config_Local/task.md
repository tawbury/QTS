# Phase 3 — Config Architecture (Local) (로드맵 기준 Task)

## Roadmap 상태

| 항목 | 상태 | 비고 |
|------|------|------|
| Local Config 파일/로더 | ✅ | 구현 완료 |
| Config 머지 오케스트레이터(로컬 우선) | 🟡 | 별도 Exit Criteria 적용 가능 |

**근거:** [docs/Roadmap.md](../../../Roadmap.md), [Phase Exit Criteria](../../../tasks/finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §2 (Phase 3: `tests/config/`, 로컬 설정만, 13_Config_3분할)

---

## 목표

- Phase 3은 **로컬 Config** 기준으로 ✅ 유지.
- Config 머지 오케스트레이터 개선 시 선택적으로 정합성·테스트 유지.

---

## Wiring 요약 (현행)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| Config_Local 로딩 | `local_config.load_local_config(project_root)` | 경로: `project_root / config/local/config_local.json`. JSON 배열, ConfigEntry 파싱. 파일 없음/파싱 오류 시 ok=False |
| 로컬 전용 Unified | `config_loader.load_local_only_config(project_root)` | Local만 로드 → config_map·metadata → ConfigMergeResult |
| 머지(로컬 우선) | `config_loader.load_unified_config(project_root, scope)` | Local 로드 → Sheet(SCALP/SWING) 로드 → `_merge_configs`(Local 우선, 충돌 키 기록). SSOT: `docs/arch/13_Config_3분할_Architecture.md` |

---

## 미결 사항

| 미결 항목 | 상태 | 비고 |
|-----------|------|------|
| Local Config 파일/로더 | ✅ 완료 | 구현·테스트 존재 (`tests/config/test_local_config.py`) |
| Config 머지(로컬 우선) | 🟡 선택 검증 | Phase 2에서 `_merge_configs`·13_Config_3분할 정합 검증. 머지 개선 시에만 별도 진행 |
| 변경 시 Exit Criteria 유지 | ✅ 문서화 | 아래 “유지보수 시 유의사항” 반영. 변경 시 `pytest tests/config/`·13_Config_3분할 정합 유지 |

Phase 3은 **로컬 Config 기준으로 ✅ 유지**. 위 “선택” 항목은 머지 쪽 🟡 해소 또는 유지보수 시에만 진행.

---

## 작업 (선택)

- [x] Config 머지(로컬 우선) 동작이 문서·테스트와 일치하는지 검증 — Phase 2에서 config_loader·13_Config §3.3 정합 완료
- [x] `config/local/config_local.json`, `src/runtime/config/local_config.py`, `config_loader.py` 변경 시 Exit Criteria §2.1·§2.3 유지 — 유지보수 시 유의사항으로 정리

**유지보수 시 유의사항:** 위 경로/모듈 변경 시 `pytest tests/config/ -v` 통과·`docs/arch/13_Config_3분할_Architecture.md`와 동작 일치 유지 (§2.1 필수 테스트, §2.3 문서 SSOT).

---

## 완료 조건 (Phase 10 Exit Criteria 기준)

- [x] 필수 테스트 통과 (§2.1) — `tests/config/` 존재·통과 (`pytest tests/config/ -v`, Local·Sheet Mock 포함)
- [x] 해당 Phase 운영 체크 (§2.2) — 로컬 설정만 해당. 파일 없음/JSON 오류 시 `ok=False` 반환·문서화됨 (local_config docstring, test_local_config)
- [x] 문서 SSOT 반영 (§2.3) — Wiring 요약·13_Config_3분할·config_constants 경로 일치

Phase 3은 **로컬 Config 기준으로 ✅**. 추가 Task는 “머지 쪽 🟡 해소” 시에만 정의.
