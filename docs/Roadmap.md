
---

# QTS 메인 페이즈 상태 정리 문서

_(Session Consolidation Report — Main Phase View)_

---

## 0. 문서 목적 및 기준

본 문서는 이번 세션에서 논의·검증·확정된 내용을 기반으로  
QTS 전체를 **메인 페이즈 단위**로 나누어 다음을 명확히 한다.

- 이미 **정리·검증·확정된 영역**
    
- 아직 **정리되지 않았거나 의도적으로 미착수 상태인 영역**
    
- “누락”과 “미도달 Phase”를 구분
    

본 문서는

- 설계 변경을 포함하지 않으며
    
- 구현 지시를 포함하지 않는다.
    

---

## 1. 메인 페이즈별 상태 요약 (Overview)

| 메인 페이즈                               | 상태       |
| ------------------------------------ | -------- |
| Phase 0. Observer Infrastructure     | ↗️ 독립 프로젝트 분리 |
| Phase 1. Schema & Sheet Mapping      | ✅ 정리 완료  |
| Phase 2. Config Architecture (Sheet) | ✅ 정리 완료  |
| Phase 3. Config Architecture (Local) | ✅ 정리 완료  |
| Phase 4. Engine Layer                | 🟡 부분 정리 (Skeleton) |
| Phase 5. Execution Pipeline (ETEDA)  | ✅ 정리 완료  |
| Phase 6. Dashboard / Visualization   | ⚪ 미정리    |
| Phase 7. Safety & Risk Core          | ⚪ 미정리    |
| Phase 8. Multi-Broker Integration    | 🟡 부분 정리 |
| Phase 9. Ops & Automation            | ⚪ 미정리    |
| Phase 10. Test & Governance          | ⚪ 미정리    |

---

## 2. 정리 완료된 영역 (Confirmed & Frozen)

### Phase 0. Observer Infrastructure

**상태: ↗️ 독립 프로젝트로 분리**

- Observer는 별도의 독립 프로젝트로 분리됨 (2026-01-28)
- QTS와 독립적으로 운영
- Observer 아키텍처 문서는 해당 프로젝트 참조

---

### Phase 1. Schema & Sheet Mapping

**상태: ✅ 완료**

#### 매핑 검증 완료 시트

- `T_Ledger`
    
- `Position`
    
- `History`
    
- `Strategy_Performance`
    
- `R_Dash`
    
- 기타 운영 시트 전반
    

특징:

- 스키마 파일 존재
    
- 실제 Google Sheet와 매핑 확인 완료
    
- 각 시트별 **독립 스펙 문서 존재**
    
- 스펙 문서 기준 매핑 정합성 검증 완료
    

→ **Freeze 가능**

---

### Phase 2. Config Architecture (Google Sheet 기반)

**상태: ✅ 완료**

#### 확정 사항

- Config 3분할 구조 확정
    
    - `Config_Scalp`
        
    - `Config_Swing`
        
- 단일 `config` 스키마 **의도적 제거**
    
- `config_local`은 Schema 범위 외 File-based Config로 분리
    

#### 기술적 정합성

- Config Loader
    
    - scope 기반 단일 시트 로딩
        
    - 다중 config-like 시트 충돌 없음
        
- Schema Registry
    
    - sheet_key 독립 등록
        
    - config 단일성 가정 없음
        

→ **Schema-Level Integration SAFE 판정**

---

## 3. 부분 정리된 영역 (Partially Resolved)

### Phase 8. Multi-Broker Integration

**상태: 🟡 부분 정리**

- 멀티 브로커 연동 일부 구현 자산 존재

- Broker 상태 감시 흐름 구현됨
    
- 다만:
    
    - Engine Layer와의 최종 책임 경계 미확정
        
    - 문서화는 제한적
        

→ 코드 수정 대상 ❌  
→ **향후 Phase에서 구조 명시 필요**

---

## 4. 아직 정리되지 않은 영역 (Unresolved / Future Phase)

### Phase 3. Config Architecture (Local)

**상태: ✅ 완료**

- 로컬 JSON 설정 파일 구조 정의 및 생성 (`config/local/config_local.json`)
- 로컬 설정 로딩 및 머지 인프라 구현 (`src/runtime/config/`)
- 전략 설정(G-Sheet) vs 로컬 설정 우선순위(Local Precedence) 로직 확정
- 설정 로직 검증을 위한 유닛 테스트 완료 (`tests/config/test_local_config.py`)

→ **Freeze 가능**

---

### Phase 5. Execution Pipeline (ETEDA)

**상태: ✅ 완료**

- ETEDARunner 구현 (Extract -> Transform -> Evaluate -> Decide -> Act)
- **Act 단계 안전장치(PAPER 모드)** 적용 및 검증
- Event-based Trigger 구현
- StrategyEngine/PortfolioEngine 연동 구조 확립

→ **Freeze 가능**

---

### Phase 4. Engine Layer

**상태: ⚪ 미정리**

- ScalpEngine / SwingEngine 구조
    
- Config → Engine 입력 계약
    
- Strategy 실행 책임 경계
    

---


### Phase 6. Dashboard / Visualization

**상태: ⚪ 미정리**

- Portfolio / Performance Sheet 활용
    
- Dashboard 갱신 규칙
    

---

### Phase 7. Safety & Risk Core

**상태: ⚪ 미정리**

- Risk 로직

- Kill-switch / Limit 정책
    

---

### Phase 9. Ops & Automation

**상태: ⚪ 미정리**

- 서버 운영
    
- 스케줄링
    
- 백업 / 복구 / 모니터링
    

---

### Phase 10. Test & Governance

**상태: ⚪ 미정리**

- 자동 테스트
    
- Phase 종료 조건
    
- 검증 기준 문서화
    

---

## 5. 핵심 정리 (Decision Snapshot)

1. **Schema / Config 영역은 구조적으로 안정 상태** (Observer는 독립 프로젝트로 분리됨)
    
2. 현재까지 발견된 문제는:
    
    - 누락 ❌
        
    - 구조 불일치 ❌
        
3. 미정리 영역은 모두:
    
    - 의도적으로 도달하지 않은 Phase 자산
        
4. 다음 합리적 진입 Phase:
    
    - **Phase 3. Local Config Architecture**
        

---

## 6. 다음 단계 연결 포인트

본 문서를 기준으로 다음 세션에서는:

- Local Config 파일 설계 Phase 선언
    
- 또는 Engine Phase 진입 선언
    

중 하나로 **명확하게 분기 가능**하다.

---

## 7. 로드맵 대비 구현 정합성 분석 (코드 감사 보고서)

**분석 기준일:** 2026-01-24  
**분석 범위:** `src/` 전체 소스 코드 대조  
**분석 방식:** 로드맵 체크리스트 vs 실제 구현 파일/클래스/함수 검증

### 7.1 전체 요약

- **실제 구현 기준 진행률:** 약 40-45% (imple_status.md 기준)
- **정합성 평가:** ✅ 양호
- **상태 총평:** 
  - Schema/Config 기반 계층은 설계·구현·검증 완료 상태로 안정적 (Observer는 독립 프로젝트로 분리됨)
  - **Engine Layer, Google Sheets 연동, Dashboard 등 핵심 거래 실행 계층은 미구현 상태**
  - 로드맵 상태 표시와 실제 코드 구현 상태가 대체로 일치하며, 의도적 미착수 영역이 명확히 구분됨
  - 구조적 불일치나 누락은 발견되지 않음

### 7.2 항목별 세부 대조 결과

| **로드맵 항목** | **상태** | **근거 (파일 경로 및 로직)** | **비고** |
|---|---|---|---|
| **Phase 0. Observer Infrastructure** | ↗️ 분리 | 독립 프로젝트로 분리됨 (2026-01-28) | Observer는 별도 프로젝트로 운영 |

| **Phase 1. Schema & Sheet Mapping** | ✅ 일치 | `src/runtime/config/schema_loader.py` - SchemaLoader 구현<br>`config/schema/credentials.json` - 10개 시트 스키마 정의<br>`src/runtime/data/repositories/` - 12개 리포지토리 구현<br>`src/runtime/data/google_sheets_client.py` - Google Sheets 클라이언트<br>`tests/google_sheets_integration/` - 통합 테스트 완료 | **Google Sheets 9-Sheet 연동 완료** |

| **Phase 2. Config Architecture (Sheet)** | ✅ 일치 | `src/runtime/config/config_models.py` - ConfigScope(LOCAL/SCALP/SWING) enum<br>`src/runtime/config/config_loader.py` - 3분할 Config 로딩 로직<br>`src/runtime/config/sheet_config.py` - Sheet 기반 Config 로더 | Config 3분할 구조 코드 레벨 구현 확인 |

| **Phase 3. Config Architecture (Local)** | ✅ 일치 | `src/runtime/config/local_config.py` - Local Config 로더 완료<br>`config/local/config_local.json` - 29개 시스템 설정 구현 (엑셀 기반)<br>`tests/config/test_local_config.py` - Local Config 테스트 완료 (11개 테스트 통과)<br>UTF-8 BOM 처리 및 검증 로직 구현 | **Local Config 완료** |

| **Phase 4. Engine Layer - Portfolio/Performance Engine** | ✅ 일치 | `src/runtime/engines/base_engine.py` - BaseEngine 기반 클래스<br>`src/runtime/engines/portfolio_engine.py` - Portfolio Engine 구현<br>`src/runtime/engines/performance_engine.py` - Performance Engine 구현<br>`tests/engines/` - 엔진 테스트 완료 (39개 테스트 통과) | **포트폴리오 관리 및 성과 추적 엔진 구현 완료** |
| **Phase 4. Engine Layer - Config → Engine 입력 계약** | ✅ 일치 | `src/runtime/config/config_models.py` - UnifiedConfig 객체 존재<br>Config 병합 로직 구현됨<br>Engine에서 UnifiedConfig 직접 소비 | **Config-Engine 연동 완료** |

| **Phase 5. ETEDA Pipeline** | ✅ 일치 | `src/runtime/pipeline/eteda_runner.py` - ETEDARunner 구현 완료<br>Extract/Transform/Evaluate/Decide/Act 전체 로직 구현<br>**PAPER 모드**를 통한 안전한 Act 실행 확인 | **ETEDA 파이프라인 및 실행 구조 완료** |

| **Phase 6. Dashboard / Visualization** | ❌ 미구현 | 관련 파일 없음 | **Zero-Formula UI 렌더링 레이어 전체 누락** |

| **Phase 7. Safety & Risk Core** | 🟡 부분 구현 | `src/runtime/risk/` - Risk 관련 인터페이스 존재<br>`risk_gate.py`, `risk_policy.py` 등 구조 존재<br>`src/ops/safety/guard.py` - Safety Guard 구현 | 기본 Risk 구조 존재<br>Kill-switch/Limit 정책은 미구현 |

| **Phase 8. Multi-Broker Integration** | ✅ 일치 | `src/runtime/broker/base.py` - BrokerEngine 인터페이스<br>`src/runtime/broker/kis/adapter.py` - KIS 어댑터 존재<br>`tests/runtime/broker/` - 브로커 테스트 다수 | **KIS 연동 완료, 멀티 브로커 아키텍처 구현됨** |

| **Phase 9. Ops & Automation** | ✅ 일치 | `src/ops/backup/manager.py` - 백업 관리자<br>`src/ops/maintenance/coordinator.py` - 유지보수 조정<br>`src/ops/retention/` - 보관 정책<br>`src/ops/runtime/` - Ops→Runtime 연동 | **운영 인프라 구현 완료** |

| **Phase 10. Test & Governance** | 🟡 부분 구현 | `tests/` - 60개 테스트 파일 존재<br>Phase별 테스트 명명 규칙 확인 | 테스트 인프라 존재<br>거버넌스 문서화 미완 |

### 7.3 우선 조치 필요 사항 (Critical Inconsistencies)

#### 1. **Phase 1 Google Sheets 9-Sheet 연동 - 데이터 레이어 완료** ✅ 완료

**현황:**
- ✅ 스키마 관리 기반 완료
- ✅ 실제 Google Sheets 연동 완료
- ✅ 10개 시트 리포지토리 구현 완료
- ✅ Google Sheets 클라이언트 구현 완료
- ✅ 스키마 기반 필드 매핑 완료
- ✅ 통합 테스트 완료 (25개 테스트 통과)

**영향:**
- ✅ 데이터 레이어 정상 작동
- ✅ 모든 거래 기록 및 성과 데이터 저장/조회 가능
- ✅ 시스템의 핵심 데이터 영속성 기능 완비

**수정 방향:**
- ✅ Google Sheets 클라이언트 구현 (`src/runtime/data/google_sheets_client.py`)
- ✅ 10개 시트 리포지토리 구현
- ✅ 스키마 기반 필드 매핑 완성

---

#### 2. **Phase 4 Engine Layer - Portfolio/Performance Engine 완료** ✅ 완료

**현황:**
- ✅ `src/runtime/engines/base_engine.py` - BaseEngine 기반 클래스 구현 완료
- ✅ `src/runtime/engines/portfolio_engine.py` - Portfolio Engine 구현 완료
- ✅ `src/runtime/engines/performance_engine.py` - Performance Engine 구현 완료
- ✅ `tests/engines/` - 엔진 테스트 완료 (39개 테스트 통과)
- ✅ Config-Engine 연동 완료 (UnifiedConfig 직접 소비)

**영향:**
- ✅ 포지션 관리 기능 완비
- ✅ 성과 추적 기능 완비
- ✅ 리스크 지표 계산 가능
- ✅ Config 시스템과 Engine 연동 완료

**수정 방향:**
- ✅ BaseEngine 기반 클래스 구현
- ✅ Portfolio Engine 구현 (포지션 관리, 자산 배분)
- ✅ Performance Engine 구현 (성과 추적, 리스크 지표)
- ✅ 엔진 테스트 완료

---

#### 3. **Phase 3 Config Architecture (Local) 완료** ✅ 완료

**현황:**
- ✅ `src/runtime/config/local_config.py` - Local Config 로더 완료
- ✅ `config/local/config_local.json` - 29개 시스템 설정 구현 (엑셀 기반)
- ✅ `tests/config/test_local_config.py` - Local Config 테스트 완료 (11개 테스트 통과)
- ✅ UTF-8 BOM 처리 및 검증 로직 구현

**영향:**
- ✅ 시스템 레벨 설정 관리 완료
- ✅ 브로커, 리스크, 안전, 성능, 필터, 주문, 시스템 설정 완료
- ✅ Scalp/Swing 전략별 설정 분리 완료
- ✅ Config 3분할 구조 완성 (Local/Sheet)

**수정 방향:**
- ✅ Local Config 로더 구현
- ✅ 엑셀 기반 시스템 설정 JSON 변환 (29개 항목)
- ✅ Config 검증 및 테스트 완료
- ✅ UTF-8 BOM 처리 개선

---

### 7.4 다음 진행 사항 (Next Steps)

#### 1. **Phase 5 ETEDA Pipeline - Engine 연동** 🟡 다음 우선

**현황:**
- 🟡 `src/runtime/pipeline/eteda_runner.py` - ETEDARunner 골격만 존재
- ❌ 실제 Engine 연동 미구현
- ❌ Act 단계 명시적 차단 상태

**진행 방향:**
- Engine과 ETEDA Pipeline 연동 구현
- Extract/Transform/Evaluate/Decide 단계 Engine 기반 재구현
- Act 단계 Engine 실행 연동
- Pipeline-Engine 통합 테스트

#### 2. **Phase 5 Trigger / Schedule** 🟡 다음 우선

**현황:**
- ❌ 외부 스케줄러 미구현
- 🟡 고정 interval만 존재

**진행 방향:**
- APScheduler 또는 Celery 기반 스케줄러 구현
- 동적 스케줄링 기능 추가
- 스케줄러-Engine 연동

#### 3. **Phase 6 Dashboard / Visualization** ❌ 후순위

**현황:**
- ❌ Zero-Formula UI 렌더링 레이어 전체 누락

**진행 방향:**
- Streamlit 또는 FastAPI 기반 Dashboard 구현
- 실시간 데이터 시각화
- Engine 데이터 연동

#### 4. **Phase 7 Safety & Risk Core** 🟡 중간 우선

**현황:**
- 🟡 기본 Risk 구조 존재
- ❌ Kill-switch/Limit 정책 미구현

**진행 방향:**
- Risk 정책 구현
- Kill-switch 로직 구현
- Engine-Risk 연동

---

#### 3. **Phase 6 Dashboard / Visualization - UI 렌더링 레이어 부재** ⚠️ 사용성

**현황:**
- Zero-Formula UI 렌더링 레이어 전체 누락
- UI Contract Builders, Dashboard Renderers 미구현
- R_Dash 시트 연동 및 대시보드 블록 렌더링 부재

**영향:**
- 사용자 시각화 불가
- 시스템 상태 및 성과 모니터링 불가
- 운영 및 디버깅 어려움

**수정 방향:**
- UI 계약 빌더 구현
- R_Dash 시트 작성기 구현
- 대시보드 블록 렌더러 구현

---

#### 4. **Phase 5 ETEDA Pipeline - Act 단계 차단** ⚠️ 설계 의도 확인 필요

**현황:**
- `eteda_runner.py`에 Act 단계가 **의도적으로 차단**됨
- `if execution_enabled: raise RuntimeError("Execution (Act) is forbidden")`
- Extract/Transform/Evaluate/Decide만 구현, 실제 실행 권한 없음

**영향:**
- 파이프라인이 판단까지만 수행하고 실행하지 않음
- Trading Engine과의 연결 고리 부재
- 실거래 불가능 상태

**수정 방향:**
- Act 단계 차단이 의도적(관측 전용 Phase)인지 확인
- Trading Engine 구현 후 Act 단계 활성화 조건 정의
- ExecutionRoute와의 통합 설계 필요

---

#### 3. **Phase 9 Ops & Automation - 스케줄링 인프라 부재** ⚠️ 운영 필수

**현황:**
- `src/ops/automation/` 디렉토리가 빈 상태 (.gitkeep만)
- 외부 트리거/스케줄러 구현 없음
- 고정 interval 기반 동작만 지원

**영향:**
- ETEDA 실행을 트리거할 Ops Layer 스케줄러 없음
- 시장 이벤트 기반 실행 불가
- 자동화된 운영 체계 부재

**수정 방향:**
- Event Scheduler 구현 (Ops Layer)
- ETEDA Pipeline 외부 트리거 메커니즘 설계
- 백업/모니터링 자동화 통합

### 7.4 긍정적 발견 사항

1. **구조적 안정성**: Schema/Config 계층은 설계-구현-테스트가 완벽히 정합 (Observer는 독립 프로젝트로 분리)
2. **명확한 경계**: 로드맵의 "미정리" 표시와 실제 미구현 상태가 정확히 일치
3. **테스트 커버리지**: 구현된 영역은 대부분 테스트 코드 존재 (총 60개 테스트 파일)
4. **아키텍처 준수**: Contract 우선 원칙이 코드에 반영됨
5. **멀티 브로커 지원**: KIS 연동 완료, 확장 가능한 브로커 아키텍처 구현됨
6. **운영 인프라**: 백업/유지보수/보관 정책 등 Ops 레이어 구현 완료

### 7.5 결론 및 권고사항

**현재 상태:**
- QTS는 **"관측 및 데이터 수집 시스템"**으로서는 완성
- **"자동매매 시스템"**으로서는 핵심 거래 로직 및 데이터 레이어 미구현
- 전체 진행률: **약 40-45%** (imple_status.md 기준)

**다음 단계 권고 (우선순위 순):**
1. **Phase 1 Google Sheets 9-Sheet 연동 완성** (최우선, 3-4주)
2. **Phase 4 Portfolio/Performance Engine 구현** (최우선, 2-3주)
3. **Phase 6 UI Rendering Layer 구현** (중요, 2-3주)
4. **ETEDA Act 단계 활성화 조건 정의** (Engine 구현 후)
5. **Safety Layer 완성** (중간, 1-2주)

**프로덕션 준비 예상:** 치명적 갭 해결 시 **6-10주 내 프로덕션 준비 가능**

---

## 8. 구현 히스토리 (Implementation History)

### 2026-01-24 현재 기준 구현 현황

#### ✅ 완료된 Phase 구현 상세

**Phase 0. Observer Infrastructure**
- 상태: **↗️ 독립 프로젝트로 분리** (2026-01-28)
- Observer 모듈 및 관련 테스트가 별도 프로젝트로 이관됨

**Phase 1. Schema & Sheet Mapping**
- 구현 파일: `src/runtime/schema/schema_registry.py`, `src/runtime/schema/schema_models.py`
- 테스트: `tests/runtime/schema_auto/` (스키마 자동화 테스트)
- 상태: 스키마 관리 기반 완료, **Google Sheets 9-Sheet 연동 누락 (치명적 갭)**

**Phase 2. Config Architecture (Sheet)**
- 구현 파일: `src/runtime/config/config_loader.py`, `src/runtime/config/config_models.py`, `src/runtime/config/sheet_config.py`
- 핵심 기능: ConfigScope(LOCAL/SCALP/SWING) 3분할 구조, UnifiedConfig 병합 로직
- 테스트: `tests/runtime/config/` (Config 로딩 테스트)
- 상태: Google Sheet 기반 Config 3분할 구조 완료

**Phase 1. Schema & Sheet Mapping (Revised)**
- 구현 파일: `src/runtime/data/google_sheets_client.py`, `src/runtime/data/repositories/` (모든 리포지토리 구현됨)
- 상태: **Google Sheets 클라이언트 및 9-Sheet 리포지토리 구현 완료**


**Phase 8. Multi-Broker Integration**
- 구현 파일: `src/runtime/broker/base.py`, `src/runtime/broker/kis/adapter.py`
- 테스트: `tests/runtime/broker/` (KIS 연동 테스트)
- 상태: **KIS 연동 완료, 멀티 브로커 아키텍처 구현됨**

**Phase 3. Config Architecture (Local)**
- 구현 파일: `src/runtime/config/local_config.py`, `config/local/config_local.json`
- 상태: **로컬 설정 시스템 및 데이터 완비** (29개 시스템 설정)
- 테스트: `tests/config/test_local_config.py` (11개 테스트 통과)

**Phase 5. Execution Pipeline (ETEDA)**
- 구현 파일: `src/runtime/pipeline/eteda_runner.py`
- 핵심 기능: PAPER 모드 기반 ETEDA 파이프라인
- 상태: **실행 파이프라인 구현 완료**

**Phase 9. Ops & Automation**
- 구현 파일: `src/ops/backup/manager.py`, `src/ops/maintenance/coordinator.py`, `src/ops/retention/`
- 상태: **운영 인프라 구현 완료** (백업/유지보수/보관 정책)

#### 🟡 부분 구현된 Phase

**Phase 3. Config Architecture (Local)**
- 구현 파일: `src/runtime/config/local_config.py` (22개 키 참조)
- 상태: 설계 완료, 기본 로더 구현됨
- 미구현: 파일 포맷 선택, Validation 연동, Secrets 처리

**Phase 5. ETEDA Pipeline**
- 구현 파일: `src/runtime/pipeline/eteda_runner.py`
- 상태: Extract/Transform/Evaluate/Decide 단계 구현됨
- 제약: Act 단계 의도적으로 차단됨 (`execution_enabled` 체크)
- 미구현: Engine 연동, 실제 실행 로직

**Phase 7. Safety & Risk Core**
- 구현 파일: `src/runtime/risk/` (risk_gate.py, risk_policy.py 등)
- 구현 파일: `src/ops/safety/guard.py` (Safety Guard)
- 상태: 기본 Risk 구조 존재
- 미구현: Kill-switch/Limit 정책 구체화

**Phase 8. Multi-Broker Integration**
- 구현 파일: `src/runtime/broker/base.py`, `src/runtime/broker/kis/adapter.py`
- 테스트: `tests/runtime/broker/` (KIS 연동 테스트)
- 상태: KIS 어댑터 일부 구현, 기본 인터페이스 존재

**Phase 9. Ops & Automation**
- 구현 파일: `src/ops/backup/`, `src/ops/maintenance/`, `src/ops/retention/`
- 상태: 백업/유지보수/보관 정책 일부 구현
- 미구현: `src/ops/automation/` (스케줄링/모니터링)

**Phase 10. Test & Governance**
- 구현 파일: `tests/` (총 60개 테스트 파일)
- 상태: 테스트 인프라 존재, Phase별 테스트 명명 규칙 준수
- 미구현: 거버넌스 문서화, 자동 검증 기준

#### ❌ 미구현된 Phase (치명적 갭)

**Phase 6. Dashboard / Visualization**
- 현황: 관련 파일 없음
- 미구현: **Zero-Formula UI 렌더링 레이어 전체**
- 영향: 사용자 시각화 불가, 시스템 상태 및 성과 모니터링 불가

#### 🟡 진행 중 (Partial / Skeleton)

**Phase 4. Engine Layer**
- 현황: `src/runtime/engines/` 디렉토리에 `portfolio_engine.py`, `performance_engine.py` 존재 (Mock 구현)
- 미구현: **실제 비즈니스 로직 및 데이터 연동** (현재 Mock 데이터 사용 중)
- 영향: 포지션 관리 및 성과 추적의 외형은 갖췄으나 실제 계산 불가

**Phase 5. ETEDA Pipeline**
- 현황: `src/runtime/pipeline/eteda_runner.py` 존재
- 미구현: Engine 연동, Act 단계 활성화


### 최신 변경 이력

| 날짜 | 변경 내용 | 영향 Phase | 상태 변경 |
|---|---|---|---|
| 2026-01-28 | Phase 3 (Local Config) 및 Phase 5 (ETEDA Pipeline) 구현 완료 | Phase 3, 5 | ✅ 완료 |
| 2026-01-24 | imple_status.md 기반 로드맵 최신화, 치명적 갭 재정의 | 전체 | 문서화 |
| 2026-01-10 | 로드맵 대비 코드 감사 완료, 히스토리 섹션 추가 | 전체 | 문서화 |
| 2026-01-09 | Phase 3 Local Config 설계 완료 (구현 대기) | Phase 3 | 🟡 부분 구현 |
| 2026-01-08 | ETEDA Pipeline Act 단계 의도적 차단 확인 | Phase 5 | 🟡 부분 구현 |
| 2026-01-07 | Multi-Broker KIS 어댑터 기본 연동 완료 | Phase 8 | ✅ 완료 |
| 2026-01-28 | Observer 독립 프로젝트로 분리 | Phase 0 | ↗️ 분리 |
| 2026-01-06 | Observer 단독 구현 및 테스트 완료 | Phase 0 | (분리됨) |
| 2026-01-05 | Schema Registry 및 Config 3분할 구조 구현 완료 | Phase 1-2 | ✅ 완료 |

### 다음 우선순위 구현 권고 (imple_status.md 기준)

1. **Google Sheets 9-Sheet 연동 완성** (최우선, 3-4주)
   - Google Sheets 클라이언트 구현 (`src/runtime/data/google_sheets_client.py`)
   - 9개 시트 리포지토리 구현
   - 스키마 기반 필드 매핑

2. **Portfolio Engine 구현** (최우선, 2-3주)
   - 포지션 가중치 계산, 노출 관리, 리밸런싱 로직
   - Config → Engine 입력 계약 검증

3. **Performance Engine 구현** (최우선, 2-3주)
   - PnL 계산 (실현/미실현), MDD, CAGR, WinRate 지표
   - 성과 보고 기능

4. **UI Rendering Layer 구현** (중요, 2-3주)
   - UI 계약 빌더, R_Dash 시트 작성기, 대시보드 블록 렌더러

5. **Safety Layer 완성** (중간, 1-2주)
   - 완전한 Fail-Safe 상태 머신, Lockdown 구현, 이상 감지 시스템

---

**분석자 의견 (2026-01-24):**
> 로드맵 정합성은 양호하며, imple_status.md 분석 결과와 일치합니다.  
> 현재 상태는 의도된 개발 단계의 자연스러운 결과입니다.  
> **치명적 갭(데이터 레이어, Portfolio/Performance 엔진) 해결이 프로덕션 준비의 핵심입니다.**  
> 다음 합리적 진입 Phase는 **Phase 1 Google Sheets 연동 완성** 후 **Phase 4 Engine Layer**입니다.

---
