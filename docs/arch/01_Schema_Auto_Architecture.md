아래는 **1번 문서: QTS_Schema_Auto_Architecture.md**의  
**정식 완성본(v1.0.0)** 이다.

본 문서는 단순 설명 수준이 아닌,  
**실제 구현 시 바로 기준 문서로 사용할 수 있는 Depth**로 작성했다.  
본문은 “정답지 수준”의 기술 명세 형태로 구성되어 있다.

---

# ============================================================

# QTS Schema Automation Architecture

# ============================================================

Version: v1.0.0  
Status: Technical Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
QTS 시스템의 근간이 되는 **Schema Automation Engine**의 구조·역할·알고리즘·변경 감지·오류 처리·테스트 규칙을  
정식 기술 명세서로 정의한다.  
본 문서는 Data Layer와 Engine Layer가 안정적으로 연결되기 위한  
표준(Source of Truth) 문서이다.

---

# **1. Overview**

## **1.1 목적**

QTS는 Google Sheets 기반의 9개 시트를 사용한다.  
그러나 시트는 언제든지 사람이 직접 수정하거나 구조가 바뀔 수 있는 환경이다.

Schema Automation Engine의 목적은:

- 시트 구조 변경을 자동으로 감지하고
    
- 엔진/파이프라인의 수정 없이
    
- 자동으로 매핑을 재생성하여
    
- QTS를 **Schema-Driven Architecture** 기반으로 운영하는 것이다.
    

즉, 컬럼 이동·추가·삭제가 발생해도  
**시스템 전체가 안정적으로 작동하도록 보장하는 핵심 엔진**이다.

---

## **1.2 범위**

본 문서가 다루는 범위:

- 시트 구조 분석 알고리즘
    
- Schema JSON 생성 규칙
    
- 필드 매핑 원리
    
- Contract Builder 동작 방식
    
- Schema Version 관리 규칙
    
- 오류 처리 구조
    
- 테스트 및 유지보수 프로세스
    

본 문서는 엔진 구현, 전략 구현은 다루지 않는다.  
(해당 내용은 [Engine Core Architecture](./02_Engine_Core_Architecture.md) 문서 참고)

---

## **1.4 관련 문서**

- **Data Contract**: [04_Data_Contract_Spec.md](./04_Data_Contract_Spec.md)
- **Engine Core**: [02_Engine_Core_Architecture.md](./02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [03_Pipeline_ETEDA_Architecture.md](./03_Pipeline_ETEDA_Architecture.md)
- **Architecture Summary**: [12_Architecture_Summary.md](./12_Architecture_Summary.md)

---

## **1.3 Schema-Driven Architecture 철학**

핵심 철학은 다음 두 문장으로 요약된다:

1. **데이터 구조는 언제든지 바뀔 수 있다.**
    
2. **하지만 시스템은 절대 깨지면 안 된다.**
    

따라서 QTS가 지향하는 구조는:

- 시트 구조 → Schema Engine → Contract → Engine
    
- Engine은 시트 구조를 직접 참조하지 않는다.
    
- Contract를 통해서만 데이터를 전달받는다.
    

이를 통해 구조 변경을 통제하고 시스템 안정성을 확보한다.

---

## **1.4 기존 좌표 기반(하드코딩) 방식의 문제점**

일반적인 자동매매 시스템은:

- “A열 = 종목명”, “B열 = 수량”  
    처럼 좌표에 의존한다.
    

그러나 이 방식은 다음 문제를 만든다:

- 컬럼 이동 = 엔진 파손
    
- 컬럼 추가 = 인덱스 오류
    
- 시트 구조가 사람에 의해 쉽게 망가짐
    
- 시트와 코드가 강하게 결합되어 유지보수 불가
    

QTS는 이 문제를 자동화로 해결한다.

---

# **2. Schema Automation Engine 구성요소**

## **2.1 Sheet Inspector**

시트의 전체 구조를 스캔하는 모듈

- 헤더 행 탐색
    
- 컬럼 이름 추출
    
- 데이터 범위 자동 탐색
    
- 병합된 셀 감지
    

출력: `RawSheetStructure`

---

## **2.2 Column/Row Scanner**

컬럼별 실제 Storage Index를 파악

- 컬럼 이동 여부 감지
    
- 숨김 컬럼 포함 여부 판단
    
- 유효 데이터 시작점 결정(row_start)
    

출력: `ColumnProfile`, `RowProfile`

---

## **2.3 Field Mapper**

Schema Engine의 핵심 모듈.  
전략·엔진에서 요구하는 필드를 실제 컬럼에 자동 매핑한다.

예:

```
필요 필드: symbol, qty, avg_price
시트 컬럼: 종목명, 보유수량, 평균단가
```

자동 매핑 규칙:

1. exact match
    
2. partial match
    
3. synonyms match
    
4. fallback match (경고)
    

출력: `FieldMap`

---

## **2.4 Schema Validator**

스키마 완료 후 유효성 검사 수행:

- 필수 필드 존재 여부
    
- 타입 유효성 검사(Int, Float, String)
    
- 중복 컬럼 체크
    
- 잘못된 포맷 감지
    

문제가 있으면 Contract 생성 중단 및 Error Report 생성

---

## **2.5 Contract Builder**

최종 스키마를 기반으로  
RawDataContract와 CalcDataContract를 생성한다.

출력 예:

```
RawDataContract.Position.qty = sheet['B']
RawDataContract.Strategy.param1 = sheet['F']
```

---

## **2.6 Schema Version Manager**

Schema 변경을 버전으로 관리한다.

- 구조 변경 발생 → schema_version 증가
    
- Engine/Contract 테스트 실행
    
- 변경 이력 기록
    

schema_version은 ETEDA Pipeline의 필수 Input이다.

---

# **3. Schema 구조 및 JSON 정의**

## **3.1 schema_version 규칙**

버전 형태:  
`major.minor`

예:  
`3.6`

증가 규칙:

- 컬럼 이동 → minor 증가
    
- 컬럼 추가 → minor 증가
    
- 컬럼 삭제 → major 증가
    
- 시트 구조 대규모 변경 → major 증가
    

---

## **3.2 sheets 객체 구조**

예시:

```
{
 "schema_version": "3.6",
 "sheets": {
    "Position": {
       "sheet_name": "Position",
       "row_start": 2,
       "columns": {
          "symbol": "A",
          "qty": "B",
          "avg_price": "C",
          "market": "D"
       }
    }
 }
}
```

---

## **3.3 column 매핑 규칙**

- 컬럼은 A~Z 또는 AA~AZ 로 자동 변환
    
- 숨김 컬럼도 매핑 대상
    
- 병합된 셀은 무시하고 실제 좌표만 사용
    
- 매핑 실패 시 오류 기록 후 Fail-Safe 트리거 가능
    

---

## **3.4 row_start / data_range 정책**

row_start = 실제 데이터가 시작되는 첫 행  
일반적으로 2행(A2) 사용  
병합된 셀 또는 빈 행은 자동 스킵

---

## **3.5 필수 필드와 선택 필드**

예: Position 시트

필수:

- symbol
    
- qty
    
- avg_price
    

선택:

- exposure_value
    
- pnl
    

선택 필드 누락은 허용되지만 Contract에서 빈 값 처리.

---

# **4. 필드 매핑 알고리즘**

## **4.1 컬럼 이동 자동 감지**

기존 schema와 현재 시트를 비교하여  
Header Text 기반으로 컬럼 이동 여부 탐지.

```
if old_column_header != new_column_header:
    remap_field()
```

---

## **4.2 컬럼 추가/삭제 대응**

컬럼 추가 → 필드 검색 후 매핑  
컬럼 삭제 → 필드 없으면 오류 발생 및 Fail-Safe

---

## **4.3 시트 구조 변경 시 재매핑 로직**

```
1) Hash 생성
2) 이전 Hash와 비교
3) 차이 → diff_report 생성
4) FieldMapper 재실행
5) schema_version 증가
```

---

## **4.4 누락 필드 탐지 및 오류 처리**

필수 필드 누락 예:

```
MissingRequiredFieldError: qty not found in Position
```

Fail-Safe로 전환할 수 있다.

---

## **4.5 시트별 우선순위 규칙**

시트별 매핑 중요도:

1. Position
    
2. T_Ledger
    
3. DI_DB
    
4. Strategy
    
5. Config
    
6. Others (Report, R_Dash)
    

---

# **5. Data Contract 생성 규칙**

## **5.1 RawData Contract 생성**

Schema 구조 기반으로 시트 → Raw 모델 생성  
타입 변환 및 공백값 처리 수행

예:

```
Raw.Position.qty = int(sheet['B'])
```

---

## **5.2 CalcData Contract 연결 방식**

RawDataContract를 기반으로  
계산 데이터(CalcData)를 생성해 Contract에 포함한다.

예:

```
Calc.Position.exposure_value = Raw.qty * price
```

CalcData는 Engine과 UI 양쪽에서 참조 가능.

---

## **5.3 UI Contract 매핑 규칙**

UI Contract는 R_Dash 시트를 업데이트하기 위한 구조.

예:

```
UI.equity = Calc.total_equity
UI.daily_pnl = Calc.daily_pnl
```

필요한 값만 전달하는 최소화된 구조를 사용.

---

## **5.4 Contract Versioning**

계약서(Contract)의 필드 구조가 바뀌면  
contract_version이 증가한다.

Raw/Calc/UI Contract 모두 포함.

---

## **5.5 Contract 무결성 검사**

- 필수 필드 검사
    
- Null/NaN 검사
    
- 타입 일관성 검사
    
- cross-field validation (예: qty < 0 금지)
    

---

# **6. 시트 구조 변화 대응(Change Detection)**

## **6.1 Hash 기반 구조 탐지**

각 시트의 헤더와 필드 형태로 Hash 생성

```
hash = sha256(",".join(headers))
```

---

## **6.2 Schema Diff 알고리즘**

과거 Hash와 비교하여  
변경 컬럼·삭제 컬럼·추가 컬럼을 탐지한다.

---

## **6.3 구조 변화 시 자동 재빌드**

1. diff 감지
    
2. FieldMapper 재실행
    
3. Schema JSON 재생성
    
4. Schema Version 증가
    
5. Contract 재생성
    
6. Engine Integration Test 수행
    
7. 결과 문제 없으면 반영
    

---

## **6.4 ETEDA 파이프라인과 연동**

Extract 단계에서 Schema Version을 검증한다.

```
if schema_version != expected_version:
    trigger_fail_safe()
```

---

## **6.5 Fail-Safe Trigger 조건**

- 필수 컬럼 삭제
    
- 컬럼명 중복
    
- Raw 데이터 타입 오류
    
- Contract 생성 실패
    
- Schema Version Mismatch
    

---

# **7. 오류 처리(Error Handling)**

## **7.1 Missing Column Error**

필수 컬럼 누락 시 즉시 중단.

## **7.2 Invalid Data Error**

숫자 필드에 문자열 등 부적절 데이터 발생 시 발생.

## **7.3 Schema Version Mismatch**

시스템 예상 버전과 JSON 버전 불일치 시 Fail-Safe 적용.

## **7.4 Contract Build Failure**

계약서 생성 실패 시 전체 파이프라인 중단.

## **7.5 재시도 및 롤백 전략**

- 시트 재스캔
    
- 기존 Schema 사용하여 일시적 운영
    
- 구조 수정 후 다시 빌드
    

---

# **8. 테스트 전략(Testability)**

## **8.1 Schema Integrity Test**

시트 구조 변경 시 자동 실행.

## **8.2 Contract Consistency Test**

필드 타입, Null 여부, 계산 일관성 체크.

## **8.3 End-to-End Schema Build Test**

Raw → Schema → Contract → Engine 연결 테스트.

## **8.4 Scenario 기반 시트 변경 테스트**

- 컬럼 이동
    
- 컬럼 삭제
    
- 컬럼 추가
    
- 헤더 이름 변경
    

---

# **9. 운영(Operation) 규칙**

## **9.1 Schema 파일 저장 경로**

```
/config/schema/schema.json
```

## **9.2 자동 업데이트 스케줄**

```
every 1 min:
    check_sheet_structure_change()
```

## **9.3 백업 및 버전 관리 정책**

```
/backup/schema/schema_2025-12-12.json
```

## **9.4 구조 변경 알림**

Slack/Telegram/Email 등으로 실시간 전송.

---

# **10. Appendix**

## **10.1 Schema JSON 샘플**

(본문 예시 참조)

## **10.2 필드 매핑 예시**

symbol → “종목명”, qty → “보유수량”

## **10.3 오류 코드 목록**

FS001 ~ FS020 등 Fail-Safe 코드 통합

## **10.4 Contract 샘플**

Raw/Calc/UI Contract 샘플 포함

---
