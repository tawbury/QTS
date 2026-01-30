아래는 **5번 문서: QTS_Dividend_DB_Architecture.md**  
**완성본(v1.0.0)** 이다.

QTS에서 배당 처리는 단순 금액 반영이 아니라  
**계좌 Equity, 성과 지표, 리스크 지표, 포트폴리오 수급 구조까지 영향을 주는 핵심 요소**이기 때문에  
본 문서는 실전 퀀트 시스템 수준의 엄밀함으로 설계되었다.

---

# ============================================================

# QTS Dividend DB Architecture

# ============================================================

Version: v1.0.0  
Status: Architecture & Data Spec (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
QTS 시스템 내 배당 데이터를 안정적으로 관리하기 위해  
**Local JSON DB + Git 버전 관리 구조**를 기반으로 한 Dividend DB의  
스키마, 저장 구조, ETEDA Pipeline 연동, Performance Engine 반영 규칙,  
오류 처리와 테스트 전략을 정의한다.

---

# **1. Overview**

## **1.1 목적**

Dividend DB의 목적:

1. **배당을 성과 지표(PnL/MDD/CAGR) 계산에 정확하게 반영**
    
2. **배당 현금 흐름을 포트폴리오·계좌 Equity에 반영**
    
3. **배당 데이터를 Local/Git DB로 안정적 보관 및 버전 관리**
    
4. ETEDA, Performance Engine 등과의 데이터 불일치 방지
    
5. 회귀 테스트(backtesting)에서 동일한 배당 효과 재현
    

---

## **1.2 범위**

포함:

- Dividend DB 스키마 정의
    
- 배당 데이터 저장/갱신/정규화 규칙
    
- ETEDA Transform 및 Performance Engine 반영 규칙
    
- Git 기반 이력 관리
    
- Validation & Error 정책
    

제외:

- 개별 추천 전략
    
- 브로커별 정산 방식 차이(단 정규화 규칙은 포함)
    

---

## **1.6 관련 문서**

- **Data Contract**: [04_Data_Contract_Spec.md](./04_Data_Contract_Spec.md)
- **Engine Core**: [02_Engine_Core_Architecture.md](./02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [03_Pipeline_ETEDA_Architecture.md](./03_Pipeline_ETEDA_Architecture.md)
- **Config 3분할**: [13_Config_3분할_Architecture.md](./13_Config_3분할_Architecture.md)

---

## **1.3 Dividend DB의 역할**

1. **현금 흐름(Cash Flow) 직접 반영**
    
2. **계좌 Equity Curve 상승 요소**
    
3. **전략 성과 측정 시 누락되면 오차 발생**
    
4. 배당 재투자 전략의 입력값
    
5. 백테스트 재현성 보장을 위한 기준 데이터
    

---

## **1.4 기존 단순 시트 기반 배당 관리의 한계**

- 배당 이벤트가 누락되기 쉬움
    
- Record Date / Pay Date 간 시차 고려 불가
    
- 여러 종목의 배당 데이터를 통합적으로 관리 불가
    
- 시트 병합/순서 삭제 등으로 데이터 안정성 취약
    
- 백테스트에서 배당 재현이 어렵고 성과 왜곡 발생
    

---

## **1.5 QTS Dividend DB 설계 원칙**

1. **불변성 확보:** 과거 배당 데이터는 Git DB로 고정
    
2. **정확성:** Record Date, Ex-Date, Pay Date 구분
    
3. **표준화:** JSON 구조를 단일 스키마로 관리
    
4. **연동성:** ETEDA → Transform → Performance까지 일관 처리
    
5. **자동성:** Transform 단계에서 자동 배당 계산 가능
    

---

# **2. Dividend DB 전체 구조**

## **2.1 Local Dividend DB (JSON)**

경로:

```
/data/dividend/dividend.json
```

특징:

- 로컬 환경에서 빠르게 접근 가능
    
- Transform 및 Performance에서 즉시 사용
    
- 스키마 Version 포함
    

---

## **2.2 Git-Tracked Dividend DB**

경로 예시:

```
/git/dividend/YYYY/dividend_2024.json
```

특징:

- 과거 배당 데이터 영구 보존
    
- 변경 이력 추적 가능
    
- 백테스트/회귀 테스트에서 버전 고정 가능
    

---

## **2.3 Sheets 기반 배당 시트와의 관계**

- 실제 운영은 JSON 기반
    
- 시트는 단순 참고 수준 또는 입력 창구로 제한
    
- ETEDA는 시트를 배당 원천으로 사용하지 않음
    

---

## **2.4 ETEDA Pipeline 연결 지점**

- Extract 단계: Dividend DB 로딩
    
- Transform 단계: 배당 계산 적용 (계좌 현금 증가 등)
    
- Evaluate·Decide 단계: 영향 없음
    
- Act 단계: 영향 없음
    

---

## **2.5 Performance Engine 연결 지점**

- 배당은 **일별 realized PnL**로 처리
    
- Performance Engine은 Pay Date 기준으로 반영
    
- 전략 성과에는 포함되지만 매매 신호에는 영향 없음
    

---

# **3. Dividend DB 스키마 정의**

## **3.1 기본 스키마**

```json
{
  "dividend_schema_version": "1.0.0",
  "dividends": [
    {
      "symbol": "AAPL",
      "ex_date": "2024-02-10",
      "record_date": "2024-02-12",
      "pay_date": "2024-02-28",
      "amount": 0.24,
      "currency": "USD",
      "source": "manual",
      "meta": {}
    }
  ]
}
```

---

## **3.2 필드 정의**

|필드|설명|필수|
|---|---|---|
|symbol|종목|Yes|
|ex_date|배당락일|Yes|
|record_date|기준일|Yes|
|pay_date|지급일|Yes|
|amount|주당 배당금|Yes|
|currency|USD/KRW 등|Yes|
|source|데이터 출처|No|
|meta|확장 필드|No|

---

## **3.3 Key/Index 설계**

Primary Key:

```
(symbol, record_date)
```

해외주식의 경우:

```
(symbol, record_date, currency)
```

---

## **3.4 JSON 구조 예시(복수 종목)**

```json
{
  "dividends": [
    { "symbol": "TSLA", "record_date": "...", "amount": 0.0 },
    { "symbol": "AAPL", "record_date": "...", "amount": 0.24 }
  ]
}
```

---

## **3.5 스키마 Version 관리**

규칙:

- 필드 삭제 → Major 증가
    
- 필드 추가 → Minor 증가
    
- 구조 변경 → Major 증가
    

---

# **4. 데이터 수집 및 갱신 플로우**

## **4.1 입력 경로**

1. 운영자 수동 입력
    
2. API 제공처(선택)
    
3. 증권사 배당 입금 내역 기반 역산(고급 옵션)
    

---

## **4.2 수집 → 검증 → 저장 파이프라인**

1. Raw 입력 값 수집
    
2. Validation (필수 필드 확인)
    
3. 중복 체크
    
4. JSON 저장
    
5. Git Commit
    

---

## **4.3 중복 데이터 처리 규칙**

중복 기준:

- symbol + record_date
    

중복 발생 시:

- amount가 다르면 Warning
    
- source가 다르면 meta에 병합 기록
    

---

## **4.4 과거 데이터 보정 규칙**

정정 공시 발생 시:

- Git Branch로 새로운 버전 생성
    
- 기존 데이터는 history 폴더로 이동 또는 날짜 태깅
    

---

## **4.5 Git Commit/Push 주기**

- 신규 데이터 발생 즉시 commit
    
- 월간 단위 snapshot 생성 가능
    

---

# **5. ETEDA·엔진과의 연동 설계**

## **5.1 Transform 단계에서의 Dividend 처리**

Transform 단계에서:

```
dividend_amount = amount * qty
equity += dividend_amount
realized_pnl += dividend_amount
```

Pay Date 기준으로 처리한다.  
ExDate 기준이 아닌 이유: 실제 현금 유입이 Pay Date에 발생하기 때문이다.

---

## **5.2 Performance Engine 반영 규칙**

배당은 Performance Engine에서:

- `daily_pnl`에 포함
    
- `realized_pnl` 증가
    
- `dividend_income` 별도 항목 생성
    
- 전략 성과에도 포함(단, 매매 신호에는 영향 없음)
    

---

## **5.3 Portfolio Engine 인식**

기본 포트폴리오 엔진은 배당을 사용하지 않는다.  
단, 확장 옵션:

- 배당금 자동 재투자 전략의 입력 데이터로 사용 가능
    

---

## **5.4 Risk Engine과의 관계**

일반적으로 영향 없음.  
예외:

- 배당 지급 직후 Equity 변동으로 계좌 비중이 변함 → Risk 지표 재계산 필요
    

---

# **6. Local DB & Git DB 동기화 아키텍처**

## **6.1 Local DB 파일 구조**

```
/data/dividend/dividend.json
/data/dividend/history/2024/dividend_2024.json
```

---

## **6.2 Git Repo 내 구조**

```
/git/dividend/YYYY/dividend_YYYY.json
/git/dividend/schema.json
```

---

## **6.3 동기화 단계**

1. Local DB → Git Load
    
2. Git Pull
    
3. Merge
    
4. Push
    

---

## **6.4 충돌 처리 규칙**

symbol + record_date 기준으로 충돌 판단:

- amount 상이 → merge 후 둘 중 하나 선택
    
- meta 상이 → 병합
    

---

## **6.5 백업 및 롤백 전략**

Git Tag 또는 Branch를 사용:

```
v2024.01-dividend-snapshot
```

---

# **7. Validation & Consistency Rules**

## **7.1 필수 필드 Validation**

- symbol
    
- record_date
    
- pay_date
    
- amount
    

---

## **7.2 날짜/금액 유효성**

- 날짜는 ISO 포맷
    
- amount >= 0
    

---

## **7.3 symbol 정합성**

Dividend DB의 symbol은 DI_DB·Position의 symbol 목록과 일치해야 한다.

---

## **7.4 중복 레코드 처리**

- 동일 record_date 중복 → Warning
    
- 금액 불일치 → Error
    

---

## **7.5 Dividend DB vs 계좌 입금 내역 Consistency**

옵션:

- 실제 계좌 배당 입금 내역과 비교하여 Consistency Report 생성 가능
    

---

# **8. 오류 처리 및 Fail-Safe 연계**

## **8.1 Dividend DB 로딩 실패**

- Pipeline 중단
    
- Fail-Safe FS040 발생
    
- 운영자 알림 발송
    

---

## **8.2 데이터 불일치 발생 시**

예: Position에는 종목이 있는데 Dividend DB에는 없는 경우

- Warning으로 처리
    
- Performance Engine에서 해당 종목 배당 없음으로 간주
    

---

## **8.3 치명적 오류 조건**

- Dividend JSON 구조 오류
    
- 필수 필드 누락
    
- schema_version 불일치
    

---

## **8.4 오류 로그/알림**

모든 오류는 다음에 기록:

- ETEDA 로그
    
- Ops Dashboard
    
- Slack/Telegram 알림
    

---

## **8.5 배당 계산 오류에 대한 방어 전략**

- 계산 불능 시 dividend_amount = 0 처리
    
- Error Level은 Warning으로 강등
    
- 성과 지표는 배당 제외 값으로 계산
    

---

# **9. 테스트 전략 (Testability)**

## **9.1 스키마 테스트**

- 필드 형식 검사
    
- 중복 검사
    
- JSON 구조 정합성
    

---

## **9.2 샘플 배당 시나리오 테스트**

예:

- 배당금이 Pay Date에 Equity 증가를 반영하는지
    
- 여러 종목 배당 동시 지급 시 누락 없는지
    

---

## **9.3 성과 지표 연계 테스트**

- 배당 반영된 PnL이 정상인지
    
- MDD/CAGR 재계산 값이 일관성 있는지
    

---

## **9.4 Git 동기화 테스트**

- Pull → 충돌 → Merge → Push 시 정상 작동하는지
    

---

## **9.5 Mock Dividend DB 기반 Backtest**

Backtest 실행 시,  
특정 기간의 실제 배당 데이터를 Mock DB에 주입해 재현성 확인 가능.

---

# **10. Appendix**

## **10.1 Dividend JSON 샘플**

```json
{
  "symbol": "AAPL",
  "record_date": "2024-02-12",
  "pay_date": "2024-02-28",
  "amount": 0.24
}
```

---

## **10.2 배당 이벤트 타임라인**

```
Ex-Date → Record Date → Pay Date
```

---

## **10.3 용어 정리**

- **정기 배당**
    
- **특별 배당**
    
- **배당락일(Ex-Date)**
    
- **기준일(Record Date)**
    

---

## **10.4 예외 케이스**

- 해외주식 환전 이슈
    
- Special Dividend
    
- Reverse Split 후 배당 데이터 보정
    

---

## **10.5 향후 확장 아이디어**

- 세금(원천징수) 반영
    
- currency conversion 자동화
    
- 배당 재투자 전략 공식 적용
    

---

**QTS Dividend DB Architecture v1.0.0 — 완료됨**

---

다음 문서로 넘어갈 준비 완료.

### 다음 진행 옵션

1. **6번 문서 스켈레톤 생성 (QTS_UI_Architecture.md)**
    
2. 방금 작성한 5번 문서 보완
    
3. 전체 흐름 검수
    

어떻게 이어갈까?