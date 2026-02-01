# NG-0: E2E Testing & Stabilization

## 목표

현재 구현된 Phase 1~10의 통합 테스트 및 프로덕션 준비

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-0 Section
- [Phase Exit Criteria](../../finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md)
- 코드: `tests/`, `src/runtime/`, `src/ops/`

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| E2E 시나리오 테스트 | ETEDA 전체 흐름 (Extract→Act) 통합 검증 | ✅ |
| 성능 벤치마크 | 각 단계별 레이턴시 측정 및 병목 식별 | ✅ |
| 실 환경 스모크 테스트 | Google Sheets + KIS Mock API 연동 | 🟡 |
| 버그 수정 | 발견된 이슈 해결 및 안정화 | ✅ |

---

## 체크리스트

### 1. E2E 시나리오 테스트

- [x] ETEDA 파이프라인 전체 흐름 테스트
  - [x] Extract: Google Sheets 데이터 추출 검증
  - [x] Transform: 데이터 정규화 검증
  - [x] Evaluate: 신호 평가 로직 검증
  - [x] Decide: 주문 결정 로직 검증
  - [x] Act: 주문 실행 검증 (Mock Broker)
- [x] 시나리오 10회 연속 성공 달성
- [x] 에러 복구 시나리오 테스트

### 2. 성능 벤치마크

- [x] 각 ETEDA 단계별 레이턴시 측정
  - [x] Extract: 목표 < 500ms
  - [x] Transform: 목표 < 100ms
  - [x] Evaluate: 목표 < 200ms
  - [x] Decide: 목표 < 100ms
  - [x] Act: 목표 < 500ms (Mock)
- [x] 전체 ETEDA 사이클 < 3초 (Mock 기준)
- [ ] 병목 지점 식별 및 문서화 (실 환경 Google Sheets 기준은 live_sheets 마커 테스트)

### 3. 실 환경 스모크 테스트

- [ ] Google Sheets 실제 스프레드시트 연동 테스트 (live_sheets 마커)
- [x] KIS Mock API 연동 테스트
- [x] 설정 로딩 (Local + Sheet) 검증
- [x] Safety/Guard 시스템 동작 검증

### 4. 버그 수정

- [x] 테스트 중 발견된 버그 목록화 (StrategyEngine price float 처리)
- [x] 우선순위별 버그 수정
- [x] 회귀 테스트 통과 확인

---

## 완료 조건 (Exit Criteria)

- [x] `pytest tests/ -v -m "not live_sheets and not real_broker"` 전체 통과
- [x] E2E 시나리오 10회 연속 성공
- [x] 평균 ETEDA 사이클 < 3초 (Mock 기준; Google Sheets는 live_sheets 테스트)
- [x] Critical/High 버그 0건

---

## 의존성

- **선행 조건**: 없음 (첫 번째 Phase)
- **후행 Phase**: NG-1, NG-3 (병렬 시작 가능)

---

## 예상 기간

1주

---

## 관련 문서

- [Test Suite Structure](../../finished/phases_no1/Phase_10_Test_Governance/Test_Suite_Structure_and_Execution.md)
- [Phase Exit Criteria](../../finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md)
- [scenario1_baseline_execution.md](../../finished/phases_no1/Phase_10_Test_Governance/scenario1_baseline_execution.md)
- [scenario2_simulation_stress_execution.md](../../finished/phases_no1/Phase_10_Test_Governance/scenario2_simulation_stress_execution.md)
- **E2E 테스트**: `tests/runtime/integration/test_eteda_e2e.py`
