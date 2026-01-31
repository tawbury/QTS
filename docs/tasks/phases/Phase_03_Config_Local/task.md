# Phase 3 — Config Architecture (Local) (로드맵 기준 Task)

## Roadmap 상태

| 항목 | 상태 | 비고 |
|------|------|------|
| Local Config 파일/로더 | ✅ | 구현 완료 |
| Config 머지 오케스트레이터(로컬 우선) | 🟡 | 별도 Exit Criteria 적용 가능 |

**근거:** [docs/Roadmap.md](../../../Roadmap.md)

---

## 목표

- Phase 3은 **로컬 Config** 기준으로 ✅ 유지.
- Config 머지 오케스트레이터 개선 시 선택적으로 정합성·테스트 유지.

---

## 작업 (선택)

- [ ] Config 머지(로컬 우선) 동작이 문서·테스트와 일치하는지 주기적 검증
- [ ] `config/local/config_local.json`, `src/runtime/config/local_config.py`, `config_loader.py` 변경 시 Exit Criteria §2.1·§2.3 유지

---

## 완료 조건

- 이미 ✅. 추가 Task는 “머지 쪽 🟡 해소” 시에만 정의.
