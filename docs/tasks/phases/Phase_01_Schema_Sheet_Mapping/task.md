# Phase 1 — Schema & Sheet Mapping (로드맵 기준 Task)

## 목표

- 데이터 레이어/리포지토리/매니저/Runner 간 **인터페이스 정합성 확보**
- Google Sheets 클라이언트·시트 리포지토리·스키마 로더의 **생성자 시그니처/호출 경로**를 실제 코드와 문서에 맞게 정합화
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 1, Section 3 (다음 우선순위)
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.1
- 코드: `src/runtime/data/google_sheets_client.py`, `src/runtime/data/repositories/`, `src/runtime/config/schema_loader.py`, `src/runtime/schema/`
- 아키텍처: `docs/arch/01_Schema_Auto_Architecture.md`, `docs/arch/04_Data_Contract_Spec.md`, `docs/arch/sub/18_Data_Layer_Architecture.md`

---

## Roadmap Section 2 — Phase 1 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| Google Sheets 클라이언트 모듈 | 🟡 | 호출부/매니저와 시그니처 정합 |
| 시트 리포지토리(포지션/레저/히스토리 등) | 🟡 | 동일 Range/Headers/Row 규칙, health_check 등 |
| 스키마 로더/레지스트리 | 🟡 | 문서·코드 일치 |

---

## 작업 (체크리스트)

- [ ] **인터페이스 정합성**
  - [ ] `GoogleSheetsClient`와 호출부/매니저 생성자 시그니처 통일 또는 adapter 문서화
  - [ ] Repository가 동일한 “Range/Headers/Row Mapping” 규칙을 따르는지 검증
  - [ ] 실패 시 예외/에러 반환 규칙 문서화
- [ ] **테스트**
  - [ ] `tests/google_sheets_integration/`, `tests/runtime/data/` 해당 테스트가 현재 인터페이스와 일치하고 CI 통과
  - [ ] Contract/스키마 검증 테스트 포함 (필요 시)
- [ ] **문서**
  - [ ] 해당 Phase 아키텍처/스펙 문서가 현재 구현과 일치
  - [ ] 진입점/wiring(호출 경로, 생성자 주입) 문서 또는 README 정리

---

## 완료 조건 (Exit Criteria)

- [ ] 필수 테스트 통과 (Phase 10 Exit Criteria §2.1)
- [ ] 해당 Phase 운영 체크 문서화(실 시트 연동 시) (§2.2)
- [ ] 문서 SSOT 반영 (§2.3)
- [ ] Roadmap Phase 1 비고(“생성자 시그니처 불일치”) 해소
