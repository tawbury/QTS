아래는 **11번 문서: QTS_Architecture_Change_Management.md**  
**완성본(v1.0.0)** 이다.

이 문서는 QTS 전체 생태계(Engine/Data/Schema/ETEDA/UI/Broker/Safety/Ops)의  
**변경 관리(Change Management)의 헌법(SSoT)** 으로,  
시스템이 확장되고 진화하더라도 안정성과 일관성을 유지하도록 하기 위해 설계되었다.

---

# ============================================================

# QTS Architecture Change Management

# ============================================================

Version: v1.0.0  
Status: Architecture Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
이 문서는 QTS 자동매매 시스템의 모든 아키텍처 변경을  
예측 가능하고 안전하게 관리하기 위한 통합 변경 관리 기준을 정의한다.

- 변경 식별
    
- 영향 분석
    
- 버전 관리
    
- 승인 절차
    
- 테스트 요구사항
    
- 배포 정책
    
- 운영 모니터링
    
- 문서 업데이트 규칙
    

까지 지원하며  
QTS 시스템이 안전하게 **Stable Evolution(안정적 진화)** 할 수 있도록 한다.

---

# **1. Overview**

## **1.1 목적**

1. 변경이 QTS 전체 시스템에 미치는 영향을 명확하게 파악
    
2. 변경으로 인한 위험을 최소화
    
3. 모든 변경이 문서·버전·테스트·배포 규칙을 통과하도록 강제
    
4. 변경 후 운영 안정성을 보장
    
5. 시스템의 확장성과 유지보수성을 향상
    

---

## **1.2 범위**

포함되는 변경:

- Schema / Contract
    
- Engine Logic
    
- ETEDA Pipeline
    
- Broker Adapter
    
- UI Contract 및 시트 구조
    
- Safety Layer
    
- Ops/Automation Layer
    

---

## **1.5 관련 문서**

- **Schema Automation**: [01_Schema_Auto_Architecture.md](./01_Schema_Auto_Architecture.md)
- **Engine Core**: [02_Engine_Core_Architecture.md](./02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [03_Pipeline_ETEDA_Architecture.md](./03_Pipeline_ETEDA_Architecture.md)
- **Data Contract**: [04_Data_Contract_Spec.md](./04_Data_Contract_Spec.md)
- **Broker Integration**: [08_Broker_Integration_Architecture.md](./08_Broker_Integration_Architecture.md)
- **Fail-Safe & Safety**: [07_FailSafe_Architecture.md](./07_FailSafe_Architecture.md)
- **Ops & Automation**: [09_Ops_Automation_Architecture.md](./09_Ops_Automation_Architecture.md)
- **Testability**: [10_Testability_Architecture.md](./10_Testability_Architecture.md)

---

## **1.3 왜 변경 관리가 필요한가**

QTS는 자동매매 시스템이므로 아래 위험을 방지해야 한다.

- Schema 변경 → 데이터 불일치 발생
    
- Engine 변경 → 매매 오류 발생
    
- Broker 변경 → 주문 실패 증가
    
- ETEDA 변경 → 로직 중단 또는 성능 저하
    
- UI 변경 → 잘못된 정보 표시
    
- Safety 기준 변경 → 위험 판단 왜곡
    

따라서 **변경 관리가 곧 안전성**이다.

---

## **1.4 변경 관리 기본 원칙**

1. **모든 변경은 기록한다.**
    
2. **모든 변경은 테스트된다.**
    
3. **모든 변경은 문서화된다.**
    
4. **모든 변경에는 버전 번호가 따른다.**
    
5. **변경 영향은 반드시 분석해야 한다.**
    
6. **변경 후 모니터링은 필수이다.**
    

---

## **1.5 변경 유형 분류**

### 1) Schema 변경

- RawDataContract, CalcDataContract, Engine I/O Contract 등
    

### 2) Engine Logic 변경

- Strategy, Risk, Portfolio, Trading, Performance
    

### 3) ETEDA Pipeline 변경

- 단계 내부 로직 변경
    
- 단계 간 연결 변화
    

### 4) Broker Integration 변경

- API 스펙 변경
    
- Normalization 규칙 변경
    

### 5) UI 변경

- UI Contract 변경
    
- 시트 구조 변경
    

### 6) Safety Layer 변경

- Fail-Safe 기준 변경
    
- Guardrail/Anomaly 규칙 변경
    

### 7) Ops/Automation 변경

- Auto-Check/Auto-Sync/Scheduler 로직 변경
    

---

# **2. Change Categories (변경 유형)**

## **2.1 Schema Changes**

- 필드 추가/삭제
    
- 타입 변경
    
- 스키마 논리 변경 (nullable → non-null 등)
    
- 스키마 정규화 규칙 변경
    

→ **전 계층 영향이 큰 변경**이다.

---

## **2.2 Engine Logic Changes**

- Strategy 의사결정 변화
    
- Risk 계산 로직 변화
    
- Portfolio 분배 변경
    
- Trading 주문 결정 로직 변경
    
- Performance 계산 로직 변경
    

---

## **2.3 ETEDA Pipeline Changes**

- Extract/Transform/Evaluate/Decide/Act 단계 내 로직 변화
    
- ETEDA 전체 순서·입출력 구조 변경
    

---

## **2.4 Broker Integration Changes**

- 브로커 API 응답 규격 변경
    
- Error Code Mapping 변경
    
- 주문 요청 방식 변경
    

---

## **2.5 UI Changes**

- UI Contract 변경
    
- Rendering 구조 변경
    
- R_Dash 레이아웃 변화
    

---

## **2.6 Safety Layer Changes**

- Fail-Safe 발동 조건 추가/변경
    
- Guardrail 기준 변경
    
- Safety State Machine 변경
    
- Anomaly 규칙 변경
    

---

## **2.7 Ops/Automation Layer Changes**

- Scheduler 주기 변경
    
- Auto-Report 템플릿 변경
    
- Auto-Check 항목 확장
    
- Auto-Backup 구조 변경
    

---

# **3. Change Impact Analysis Framework**

## **3.1 영향 분석 기본 항목**

각 변경은 아래 항목의 영향을 분석해야 한다.

- Data Layer
    
- Engine Layer
    
- Pipeline Layer
    
- Safety Layer
    
- Broker Layer
    
- UI Layer
    
- Ops Layer
    
- Testability Layer
    

---

## **3.2 영향 분석 매트릭스**

변경 유형별 영향도를 High/Medium/Low로 분류하는 매트릭스 포함.

---

## **3.3 주요 영향 트리거**

- Schema 필드 변경
    
- Engine Output 구조 변경
    
- Broker API 변경
    
- UI Contract 변경
    
- Safety Layer 기준 변경
    

---

## **3.4 시스템 종속성 분석**

모든 변경은 QTS 구성요소 간 종속성(DAG)을 통해 영향 범위를 산출한다.

---

# **4. Versioning Strategy**

## **4.1 Semantic Versioning**

세 가지 레벨 모두 적용:

- Major: breaking change
    
- Minor: 기능 추가
    
- Patch: 버그 수정
    

---

## **4.2 Schema Version 관리**

Schema는 변경시 반드시 Major 또는 Minor 증가.  
Schema mismatch는 Fail-Safe(FS001) 트리거.

---

## **4.3 Contract Version 관리**

UI/Engine/Raw/Calc Contract는 Strict Versioning 적용.

---

## **4.4 Engine Version 관리**

Engine 변경은 다음 조건 기준으로 버전 증가:

- 논리 변경 → Minor
    
- 의사결정 구조 변경 → Major
    

---

## **4.5 ETEDA Version 관리**

ETEDA Version은 각 단계 변경이 누적된 형태의 버전.

---

## **4.6 UI Version 관리**

UI Contract 변경 시 Minor 증가.  
레이아웃 변경 시 Major 증가 가능.

---

## **4.7 Safety Layer Version 관리**

Fail-Safe/Guardrail 규칙 변경 시 Minor 증가.  
Safety State Machine 변경 시 Major 증가.

---

## **4.8 Broker Adapter Version 관리**

브로커 API 스펙 변경 → Major  
Normalization 변경 → Minor

---

# **5. Change Approval Workflow**

## **5.1 변경 요청(Change Request, CR)**

CR 문서 기본 구조:

- 변경 설명
    
- 변경 이유
    
- 영향 분석
    
- 테스트 계획
    
- 예상 위험
    
- 버전 번호
    

---

## **5.2 변경 검토 항목**

리뷰 체크리스트:

- Safety 영향은 없는가?
    
- Schema/Contract 정합성은 유지되는가?
    
- ETEDA 파이프라인이 깨지지 않는가?
    
- Broker 통합 영향은?
    
- UI 및 Ops 영향은?
    
- Regression Test는 충분한가?
    

---

## **5.3 변경 승인 기준**

- 영향 분석 완료
    
- 테스트 통과
    
- 성능 저하 없음
    
- Safety 영향 없음
    
- 문서 업데이트 완료
    

---

## **5.4 위험도 기반 승인 정책**

|위험도|승인 필요|예시|
|---|---|---|
|High|ARB(Architecture Review Board) 승인|Schema 변경|
|Medium|PM/엔진 책임자 승인|Risk 로직 변경|
|Low|자체 승인 가능|UI 스타일 변경|

---

## **5.5 변경 기록(Change Log)**

모든 변경은 Change Log에 기록:

```
Version
Date
Author
Change Summary
Impact
Tests
Rollback Plan
```

---

# **6. Test Requirements Before Deployment**

## **6.1 필수 테스트 목록**

아래 테스트는 배포 전 반드시 통과해야 한다.

- Unit Test
    
- Contract Test
    
- Engine Test
    
- Pipeline Test
    
- Safety Test
    
- Broker Integration Test
    
- UI Rendering Test
    
- End-to-End Test
    
- Regression Test
    

---

## **6.2 Version Mismatch Test**

버전 충돌 여부 테스트.

---

## **6.3 Performance Impact Test**

- ETEDA Cycle Time 증가 여부
    
- Engine 처리량 감소 여부
    

---

## **6.4 Pipeline Stability Test**

- Multi-Cycle Test 수행
    
- 100~10,000회 반복 테스트 가능
    

---

## **6.5 Fail-Safe & Guardrail Test**

Fail-Safe 정상 동작 여부  
Guardrail 정상 동작 여부

---

## **6.6 Broker Compatibility Test**

실 브로커 또는 Mock Broker 기준으로 테스트.

---

# **7. Deployment Workflow**

## **7.1 Release 준비 절차**

- 변경 이유·내용 정리
    
- 테스트 결과 검토
    
- 위험 분석 보고서 작성
    
- 배포 일정 확정
    

---

## **7.2 Release 단계**

1. Stage(선택적) 배포
    
2. Smoke Test
    
3. Production 배포
    
4. 모니터링
    

---

## **7.3 Rollback 전략**

Rollback 조건:

- Fail-Safe 지속
    
- ETEDA 중단
    
- Broker Failure 증가
    

Rollback 대상:

- Engine
    
- Schema
    
- Contract
    
- UI
    
- Broker Adapter
    

Rollback은 Snapshot 또는 Git Tag 기반으로 수행.

---

## **7.4 Hotfix 절차**

긴급 상황에서 다음 절차 사용:

1. Hotfix 생성
    
2. Regression Test 중 핵심만 수행
    
3. 배포
    
4. 이후 전체 Regression 수행
    
5. 버전 재정렬
    

---

# **8. Change Monitoring & Verification**

## **8.1 배포 후 모니터링 항목**

- Safety 이벤트 발생 여부
    
- ETEDA Cycle Time 변화
    
- Broker Error Rate 변화
    
- PnL 이상 변동
    
- UI Contract 오류
    

---

## **8.2 변경 후 Fail-Safe 감지**

Fail-Safe 증가 시 변경 영향 가능성 판단 후 Rollback 검토.

---

## **8.3 변경 후 데이터 변형 감지**

- Position-Ledger Drift
    
- CalcData 변형
    
- Schema mismatch
    

---

## **8.4 성능 검증**

정상 상태 대비:

- Cycle Time
    
- Memory 사용량
    
- CPU 사용량
    

비교.

---

## **8.5 운영자 확인(Checklist)**

배포 후 운영자는 체크리스트 작성:

- Safety 상태 정상
    
- UI 정상 표시
    
- Broker 정상 연결
    
- ETEDA 정상 실행
    

---

# **9. Documentation Requirements**

## **9.1 변경문서 필수 기재 항목**

- 변경 요약
    
- 변경 이유
    
- 영향 분석
    
- 테스트 결과
    
- 버전 번호
    
- 배포 일정
    
- Rollback Plan
    

---

## **9.2 Architecture 문서 업데이트 규칙**

아키텍처 변경은 반드시 해당 문서 업데이트 후 버전 증가.

---

## **9.3 Schema/Contract 문서 업데이트 규칙**

스키마/계약 변경 시:

- 별도 Schema Specification 업데이트
    
- Version Increase 필수
    

---

## **9.4 Engine/ETEDA 문서 업데이트 규칙**

Engine 또는 ETEDA 로직 변경 시 관련 아키텍처 문서 업데이트 필수.

---

# **10. Change Risk Management**

## **10.1 Major Change 위험 대응**

- 대규모 Regression
    
- Stage 환경 테스트
    
- ARB 승인 필수
    

---

## **10.2 Minor Change 위험 평가**

- 기능 확장
    
- 계산 로직 보완
    
- 문서 및 테스트 비교적 단순
    

---

## **10.3 Breaking Change 대응 방식**

Schema Breaking Change는 다음 필요:

- Major Version 증가
    
- Migration Script 준비
    
- Rollback Strategy 필수
    

---

## **10.4 Safety Layer 기반 위험 차단**

Safety Layer가 변경 이후 위험을 조기에 감지하여  
Fail-Safe를 통한 보호 역할 수행.

---

## **10.5 Multi-Broker 환경에서의 변경 위험**

브로커별 스펙 차이로 인해  
Normalization 규칙 변경 시 영향도가 크므로  
반드시 Broker Compatibility Test 수행.

---

# **11. CI/CD Integration for Change Management**

## **11.1 Git 기반 변경 검증**

- Pull Request → 자동 테스트
    
- Static Analysis → 자동 검증
    

---

## **11.2 자동 테스트 → 자동 승인**

테스트 통과 → 변경 승인 가능.

---

## **11.3 변경 기록 자동 생성**

CI 시스템이 Change Log 자동 생성.

---

## **11.4 자동 버전 증가(Optional)**

pre-commit hook으로 버전 자동 증가 가능.

---

## **11.5 배포 파이프라인 자동 검증**

- Stage Smoke Test 자동 실행
    
- Fail-Safe 발생 여부 모니터링
    

---

# **12. Architecture Review Process**

## **12.1 ARB(Architecture Review Board)**

대규모 변경 시 전문가 리뷰 그룹 생성 가능.

---

## **12.2 변경 규모 기준**

|규모|예시 변경|리뷰 필요|
|---|---|---|
|Large|Schema Major Change, Engine 구조 변경|ARB|
|Medium|Risk/Portfolio 로직 변경|PM 승인|
|Small|UI 스타일 변경|자체 승인|

---

## **12.3 리뷰 항목**

- 데이터 정합성
    
- 안전성
    
- 확장성
    
- 성능 영향
    
- 테스트 가능성
    
- 문서 업데이트 여부
    

---

## **12.4 문서 승인 기준**

아키텍처 문서도 변경 승인 이후 반드시 업데이트.

---

# **13. Appendix**

## **13.1 영향 매트릭스 예시**

변경 유형별 영향 범위 표.

---

## **13.2 변경 요청 템플릿**

CR Template:

```
Title  
Description  
Reason  
Impact  
Version  
Test Plan  
Rollback Plan  
```

---

## **13.3 변경 기록(Change Log) 예시**

버전 증가 내역과 변경 이유 정리.

---

## **13.4 Rollback Plan 샘플**

Engine/Schema/UI/Broker 롤백 계획 포함.

---

## **13.5 변경 프로세스 다이어그램**

변경 요청 → 영향 분석 → 테스트 → 승인 → 배포 → 모니터링 → 문서 업데이트 흐름.

---

**QTS Architecture Change Management v1.0.0 — 완료됨**

---

이제 12번 아키텍처 문서만 남아있어.  
(보통 Appendix 또는 Summary Architecture)

원하는 문서 형태를 알려주면 스켈레톤부터 작성할게:

1. **전체 아키텍처 Summary 문서**
    
2. **Appendix Master Document**
    
3. **Glossary / Terminology 문서**
    
4. **QTS Architecture Overview(1장 확장판)**
    

어떤 형태로 12번 문서를 만들까?