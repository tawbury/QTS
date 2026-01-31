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
| Config 3분할 모델/머지 로직 | 🟡 | 문서·코드 일치 |
| Sheet 기반 Config 로딩 | 🟡 | `sheet_config.py`가 GoogleSheetsClient 인터페이스와 정합 |

---

## 작업 (체크리스트)

- [ ] **Config Sheet 로딩 정합성**
  - [ ] `sheet_config.py` 호출 경로를 현재 `GoogleSheetsClient` API에 맞게 수정
  - [ ] 생성자/호출부 불일치 제거
- [ ] **테스트**
  - [ ] `tests/config/` 등 Config 로딩 테스트가 현재 인터페이스와 일치하고 통과
- [ ] **문서**
  - [ ] Config 3분할/Sheet 로딩 진입점·wiring 문서화
  - [ ] Roadmap Phase 2 비고(“sheet_config–Client 불일치”) 해소

---

## 완료 조건 (Exit Criteria)

- [ ] 필수 테스트 통과 (§2.1)
- [ ] 설정 로딩 실패 시 운영 체크 문서화 (§2.2)
- [ ] 문서 SSOT 반영 (§2.3)
