
---

# **PART 1. QTS 개요 및 운영 철학**

## **1. QTS의 목적**

QTS(Qualitative Trading System)는 개인 투자자가  
다중 전략·다중 데이터 기반의 정교한 의사결정을  
**자동화된 구조로 실행할 수 있도록 설계된 통합 트레이딩 시스템**이다.

QTS의 근본 목적은 다음과 같다:

- 투자자의 개별 판단 한계를 시스템화하여 극복
    
- 전략의 일관성 확보
    
- 감정 개입 최소화
    
- 데이터 기반의 정량·정성 결합 의사결정
    
- 수익률뿐 아니라 **장기 생존력(리스크 관리/안정성)** 중시
    
- 자동화된 프로세스 구축을 통한 반복 업무 제거
    

QTS는 단순 자동매매가 아니라  
**투자 철학 → 데이터 기준 → 전략 엔진 → 리스크 엔진 → 실행 → 복구 시스템**  
까지 포함하는 **전체 투자 운영 체계**다.

---

## **2. QTS 운영 철학**

QTS 운영 철학은 다음 5가지 원칙을 기반으로 한다.

### **(1) Consistency – 일관성이 최고의 성과를 만든다**

인간의 판단은 하루에도 여러 번 흔들리지만  
시스템은 1년이 지나도 동일한 규칙으로 답을 낸다.

QTS는 언제나 정해진 규칙에 따라:

- 동일한 조건 → 동일한 의사결정
    
- 동일한 분석 방식 → 동일한 신호
    

을 출력하는 것을 목표로 한다.

---

### **(2) Transparency – 모든 의사결정은 기록 가능해야 한다**

QTS는 Black-box 전략이 아니다.  
어떤 조건에서 어떤 신호가 발생했는지  
**전략 엔진·리스크 엔진·실행 엔진·브로커 응답**  
모든 과정이 Audit Logging Layer에 기록된다.

이는 시스템의 신뢰성과 복구 가능성을 결정하는 핵심 요소이다.

---

### **(3) Stability – 자동매매의 핵심 경쟁력은 안정성이다**

자동매매는 “돌발 변수”와 “예외 상황”이 반드시 발생한다.

- API 지연
    
- 브로커 오류
    
- Google Sheets 구조 변경
    
- 데이터 결측치/오류
    
- 전략 계산 실패
    
- 리스크 급등
    
- Config 값 입력 오류
    

이벤트가 발생할 때 시스템이 “오류 없이 버티는지”가  
장기 성과를 좌우한다.

QTS는 아래 6개 안정성 모듈을 갖춘다:

1. Config Validation Layer
    
2. Version Tracking Layer
    
3. Audit Logging Layer
    
4. Fail-safe Decision Engine
    
5. Graceful Shutdown Module
    
6. Recovery Engine
    

이 6개 모듈은 내부적으로 다른 엔진과 동등한 비중의 핵심 구성요소다.

---

### **(4) Interpretability – 전략의 근거가 명확해야 한다**

QTS는 다음을 명확히 구분한다:

- **전략이 무엇을 근거로 매수 신호를 냈는가?**
    
- **어떤 지표가 위험 신호를 발생시켰는가?**
    
- **어떤 조건 때문에 매도를 트리거했는가?**
    

Audit Logging에 모든 근거가 남도록 설계되어 있기 때문에  
사용자는 언제든 “이 신호가 왜 발생했는지”를 검증할 수 있다.

---

### **(5) Robustness – 시장 변화에 견디는 구조**

QTS가 추구하는 시스템은 다음에 강해야 한다:

- 시장 변동성
    
- 뉴스·이슈 충격
    
- 데이터 변화
    
- 구조 변경
    
- 엔진 업데이트
    

즉, **성능이 아닌 생존성(robustness)** 을 최우선 가치로 둔다.

---

## **3. QTS 상위 구조 요약**

QTS는 다음 5개의 Layer로 구성된다.

|Layer|설명|
|---|---|
|**Data Layer**|Google Sheets 기반 Data Warehouse|
|**Schema Engine Layer**|스키마 자동생성/검증/복구|
|**Logic Layer**|전략 엔진·리스크 엔진·포트폴리오 엔진|
|**Execution Layer**|브로커 API 기반 매매 처리|
|**Stability Layer**|자동매매 안정성 보장하는 핵심 6대 모듈|

이 구조는 기존 문서의 상위 정의를 그대로 유지하면서,  
우리가 확정한 최신 설계 내용을 자연스럽게 통합한 확장 버전이다.

---

## **4. 데이터·전략·리스크·실행의 연결성**

QTS는 다음과 같은 상승형 구조로 설계되어 있다.

```
데이터 → 스키마 엔진 → 전략 엔진 → 리스크 엔진 → 실행 엔진 → 기록·검증 → 복구/안정성 엔진
```

이 흐름은 기존 문서의 기본 골격을 유지하되,  
이번 버전에 따라 안정성 모듈들이 정식으로 포함된 형태다.

---

## **5. 가치투자 기반 요소의 통합**

이번 설계에서는 **가치투자 공식 기준**이 전략 엔진 내부에 정식 통합되었다.

- 핵심 재무지표 기준 (PER, PBR, ROE 등)
    
- 지표별 정상 범위
    
- 산업별 조정
    
- 내재가치 공식(DCF/Residual/Multiple 기반)
    
- 성장률/할인율 가정
    
- 질적 요소 점수
    
- 종합 점수 기준
    
- 저평가 기준
    
- 위험조정 방식
    

이 모든 설정은 **Config Sheet**에서 관리되며,  
엔진은 Config → Schema → Repository 경유 구조로 읽는다.

---

## **6. 자동화 운영 원칙**

QTS 운영은 다음 원칙을 적용한다:

- 수동介入 최소화
    
- 파라미터 변경은 Config Sheet에서만
    
- 모든 변경은 Version Tracking
    
- 엔진 실행은 일정한 인터벌 기반
    
- 오류 발생 시 Fail-safe/Shutdown → Recovery
    
- 신호 및 매매 기록은 모두 Audit Logging
    

---

# **PART 2. 시스템 아키텍처 개요 (System Architecture Overview)**

**Version: v1.0.0**

본 파트는 QTS의 전체 기술적 구조를 설명한다.  
QTS는 단순한 자동매매 엔진이 아니라, 데이터 관리부터 전략 계산, 리스크 평가, 실행, 안정성 제어까지 하나의 통합된 구조로 설계되어 있다.

아키텍처는 크게 다섯 개의 Layer로 구성된다.

---

# **2.1 Data Layer – Google Sheets 기반 데이터 웨어하우스**

QTS의 모든 운용 데이터는 Google Sheets를 기반으로 저장된다.  
Google Sheets는 단순한 스프레드시트가 아니라, 아래 역할을 수행하는 **데이터 웨어하우스(Data Warehouse)** 로 활용된다:

- 전략 엔진의 입력 데이터
    
- 포트폴리오 상태 데이터
    
- 리스크 모니터링 데이터
    
- 트레이딩 기록
    
- 배당·현금흐름 데이터
    
- 가치평가 지표
    
- Config 파라미터 저장소
    
- Audit Logging 일부 데이터
    

각 시트는 명확한 책임을 가진 독립적 테이블로 구성된다.

---

## **2.1.1 주요 시트 구성**

### **(1) Config Sheet (SSOT – Single Source of Truth)**

QTS의 모든 설정 값은 이 시트 하나에서 관리된다.  
CATEGORY / SUB_CATEGORY / KEY / VALUE / DESCRIPTION 구조로 구성되며,  
전략, 가치투자 기준, 리스크 관리, 시스템 파라미터, 안정성 모듈 설정까지 모두 포함된다.

**구조:**

|Column|의미|
|---|---|
|A|CATEGORY|
|B|SUB_CATEGORY|
|C|KEY|
|D|VALUE|
|E|DESCRIPTION|

**추가된 신규 CATEGORY (안정성 모듈용):**

- STABILITY_CONFIG_VALIDATION
    
- STABILITY_VERSION_TRACKING
    
- STABILITY_AUDIT_LOGGING
    
- STABILITY_FAIL_SAFE
    
- STABILITY_GRACEFUL_SHUTDOWN
    
- STABILITY_RECOVERY
    

---

### **(2) Position Sheet**

현재 보유 중인 모든 포지션 상태를 유지한다.

- 종목 코드
    
- 보유 수량
    
- 평균 매입가
    
- 현재가
    
- 평가 손익
    
- 비중·노출도
    

Portfolio Engine은 이 시트를 통해 실시간 포트폴리오 상태를 파악한다.

---

### **(3) Portfolio Sheet**

전체 자산 상태를 기록하는 테이블이다.

- 총자산
    
- 현금잔고
    
- 종목별 비중
    
- 변동성
    
- 리스크 점수
    

리밸런싱·위험 판단·포지션 축소 등 핵심 로직의 기초 자료가 된다.

---

### **(4) T_Ledger (거래 원장)**

모든 실제 체결 기록이 이 시트에 저장된다.

- 체결 시간
    
- 종목
    
- 방향 (Buy/Sell)
    
- 수량
    
- 가격
    
- 슬리피지
    
- 수수료
    
- 브로커 응답
    

이는 전략 검증, 백테스트 비교, 손익 계산의 기준 데이터가 된다.

---

### **(5) R_Dash (Risk Dashboard)**

리스크 엔진의 분석 결과가 실시간으로 반영되는 시트다.

- 변동성
    
- 노출도
    
- 종목별 리스크
    
- 시장 리스크 지표(VIX 등)
    
- 내부 위험 레벨
    

---

### **(6) Dividend Sheet**

배당 기반 평가모델에서 사용되는 배당·현금흐름 데이터를 저장한다.

---

### **(7) DT_DB / History Sheet**

전략 신호 기록, 백테스트 결과, 과거 메트릭을 저장하는 시트다.

- 전략별 신호
    
- 점수
    
- 내재가치 계산 결과
    
- 리스크 레벨
    
- 전략 실행 이력
    

장기적 성능 분석에서 핵심적인 역할을 한다.

---

### **(8) Dashboard Sheet**

운영자가 실시간으로 참고하는 대시보드다.

- 핵심 신호
    
- 포트폴리오 요약
    
- 당일 P/L
    
- 거래 상태
    
- 브로커 상태
    
- 리스크 경고
    

운영 효율성을 높이는 인터페이스 역할을 한다.

---

# **2.2 Schema Engine Layer – 스키마 자동화 구조**

Schema Engine은 QTS의 유지보수성과 안정성의 핵심이며,  
Google Sheets와 엔진을 완전히 분리된 구조로 만들어주는 역할을 한다.

이 레이어는 다음 네 가지 기능을 수행한다.

---

## **2.2.1 스키마 자동 생성 (Header → schema.json)**

각 시트의 첫 행(헤더)을 읽어:

- 필드명
    
- 컬럼 인덱스
    
- 데이터 타입 추론
    
- 필수 여부
    

등을 자동 생성해 **schema.json** 파일에 저장한다.

엔진은 직접 시트를 읽지 않고  
**schema.json을 통해 구조를 해석**한다.

---

## **2.2.2 스키마 Diff 감지**

Schema Engine은 매 실행 시 이전 스키마와 비교해 변경점을 감지한다:

- 컬럼 추가
    
- 삭제
    
- 순서 변경
    
- 이름 변경
    

변경사항은 Version Tracking Layer에서 기록되며,  
문제가 발견될 경우 Config Validation Layer 또는 Fail-safe Engine을 호출한다.

---

## **2.2.3 오류 자동 복원 (Fallback Defaults)**

스키마 오류가 발견되면 다음 순서로 복원한다:

1. 오류 기록(Audit)
    
2. fallback_defaults.json 불러오기
    
3. 문제 영역의 기능 제한
    
4. 필요 시 Fail-safe 모드로 전환
    
5. 최종적으로 Graceful Shutdown 수행 가능
    

스키마 구조 변경으로 자동매매가 중단되는 일이 없도록 설계되어 있다.

---

## **2.2.4 Repository 자동 생성**

Repository Layer는  
schema.json을 기반으로 자동 생성된다.

- PositionRepository
    
- LedgerRepository
    
- RiskRepository
    
- ConfigRepository
    

이 구조 덕분에 시트 구조 변경 시  
엔진 코드를 수정할 필요가 없다.

---

# **2.3 Logic Layer – 전략·리스크·포트폴리오 엔진**

Logic Layer는 QTS의 의사결정을 담당하는 핵심 뇌에 해당한다.

세 가지 엔진으로 구성된다.

---

## **2.3.1 Strategy Engine**

전략 엔진은 다음을 계산한다:

- 기술적 지표(MA, RSI, ATR 등)
    
- 가치투자 기반 정량 지표(PER, PBR, ROE 등)
    
- 내재가치 기반 지표(DCF, Residual 등)
    
- 질적 평가 점수
    
- 가중치 기반 종합 스코어
    

전략 엔진의 출력은 다음 형태이다:

```
{
  symbol: "005930",
  buy_signal: true,
  sell_signal: false,
  score: 87,
  factors: {...}
}
```

`factors`는 Audit Logging Layer에 기록되어  
모든 결정의 근거가 재현 가능하다.

---

## **2.3.2 Risk Engine**

리스크 엔진은 포트폴리오의 생존력을 보호하는 역할을 한다.

주요 기능:

- 변동성 계산
    
- 시장 국면 분석
    
- 종목별 위험도 측정
    
- 포트폴리오 위험도 측정
    
- 매수 제한/비중 축소 트리거
    
- Fail-safe 조건 감지
    

리스크 엔진은 Strategy Engine의 신호보다 우선한다.  
즉, 매수 신호가 있어도 리스크 상태가 나쁘면 매수하지 않는다.

---

## **2.3.3 Portfolio Engine**

포트폴리오 엔진은 매매 이후의 전체 포지션 상태를 유지한다.

- 현금/자산 계산
    
- 비중 계산
    
- 최대 종목수 관리
    
- 노출도 관리
    
- 리밸런싱 수행
    

Risk Engine과 결합해  
안전한 포지션 관리가 가능하게 한다.

---

# **2.4 Execution Layer – 자동 실행 엔진**

브로커 API(KIS API)와 직접 연결되는 모듈이다.

기능:

- 주문 생성
    
- 단위가격 계산
    
- 슬리피지 반영
    
- 체결 여부 확인
    
- 재시도 처리
    
- 시간 기반 종료
    
- 오류 감지
    

특히 KIS API의 응답 불량, 재시도 제한 등  
예외 상황을 안정적으로 처리하기 위한 구조가 포함되어 있다.

---

# **2.5 Stability Layer – 자동매매 안정성 보장 핵심 구조**

이번 업데이트를 통해 QTS는 독립된 **Stability Layer**를 정식 구성 요소로 가진다.

이 Layer는 시스템이 중단되지 않도록 보호하는 최후의 방어선이다.

6개 모듈로 구성된다:

---

## **2.5.1 Config Validation Layer**

Config 값 오류를 자동 감지:

- 허용 범위 초과
    
- 음수 불가 값
    
- 필수 KEY 누락
    
- 데이터 타입 불일치
    

오류 발생 시:

- 해당 KEY 비활성화
    
- fallback 값 적용
    
- Audit 기록
    
- 필요 시 Fail-safe 호출
    

---

## **2.5.2 Version Tracking Layer**

다음의 변경 사항을 모두 기록한다:

- Config 변경
    
- Schema 변경
    
- Engine 버전 변경
    
- 중요 파라미터 수정
    

변경 시각, 변경 전/후 값, 영향 범위가 기록된다.

---

## **2.5.3 Audit Logging Layer**

모든 엔진의 판단 근거를 기록한다.

- 전략 신호
    
- 리스크 평가
    
- 포트폴리오 조정
    
- 브로커 응답
    
- 오류 기록
    

이는 디버깅과 복구뿐 아니라  
장기적 전략 개선에도 필수적이다.

---

## **2.5.4 Fail-safe Decision Engine**

위험 상황에서 자동 보호 기능을 수행한다.

트리거 예:

- 손실률 초과
    
- 오류 연속 발생
    
- 브로커 응답 지연
    
- 스키마 오류
    
- 리스크 레벨 초과
    

가능한 대응:

- 매수 중단
    
- 포지션 축소
    
- 트레이딩 전체 중단
    
- 신호 무시
    
- 시스템 보호 모드 진입
    

---

## **2.5.5 Graceful Shutdown Module**

즉시 종료가 아니라,  
안전하게 종료하기 위한 절차를 실행한다.

- 미체결 주문 취소
    
- 포지션 상태 저장
    
- 실행 중 프로세스 종료
    
- 로그 저장
    
- 브로커 연결 해제
    

---

## **2.5.6 Recovery Engine**

재가동 시 자동 복구 절차를 수행한다.

- Config 재적재
    
- Position 재검증
    
- Risk Score 재계산
    
- 전략 초기화
    
- 정상 모드 복귀 여부 판단
    

---

# **PART 3. 데이터 정의 및 관리 체계 (Data Definition & Management System)**

**Version: v1.0.0**

본 파트는 QTS가 의존하는 모든 데이터 구조를 정의하고,  
Google Sheets 기반 데이터 웨어하우스의 전체 구조와 관리 규칙을 설명한다.

QTS는 단순히 데이터를 저장하는 시스템이 아니라,  
**데이터 품질 → 스키마 구조 → 검증 → 복구 → 안정성**까지 고려한  
완성도 높은 데이터 관리 체계를 구축하는 것을 목표로 한다.

---

# **3.1 데이터 관리 철학 (Data Philosophy)**

QTS 데이터 철학은 아래 4가지 원칙을 기반으로 한다.

### **(1) Single Source of Truth (SSOT)**

모든 설정 값은 Config 시트에서만 관리되며,  
전략·리스크·가치평가·시스템 파라미터는 하나의 통합 중앙 저장소에서 읽는다.

### **(2) Schema-driven Architecture**

엔진은 시트 구조에 직접 의존하지 않고  
항상 schema.json을 통해 구조를 해석한다.

### **(3) 자동 복구 가능성 (Self-healing)**

스키마 오류, 결측치, 타입 오류 등 데이터 문제가 발생해도  
엔진은 즉시 중단되지 않고 복구 절차를 수행한다.

### **(4) 완전한 Auditability**

데이터는 변경 이력과 함께 검증 가능해야 하며,  
모든 계산 결과는 Audit Logging Layer를 통해 기록된다.

---

# **3.2 Config Sheet 정의 (QTS 핵심 데이터 구조)**

Config Sheet는 QTS의 모든 설정 값을 저장하는 핵심 데이터이며  
전략·리스크·가치투자·시스템·안정성 파라미터의 SSOT 역할을 수행한다.

구조는 다음과 같다:

|Column|설명|
|---|---|
|A: CATEGORY|설정 대분류|
|B: SUB_CATEGORY|설정 중분류|
|C: KEY|내부 엔진 파라미터 이름|
|D: VALUE|실제 값|
|E: DESCRIPTION|설명|

Config에 설정되는 주요 그룹:

---

## **3.2.1 STRATEGY_PARAMETERS**

기술적 지표, 가치지표, 내재가치 모델 등  
전략 엔진이 사용하는 모든 파라미터 포함.

예:

- PER_MIN
    
- ROE_TARGET
    
- GROWTH_RATE_BASE
    
- RSI_BUY / RSI_SELL
    
- ATR_WINDOW
    
- DCF_DISCOUNT_RATE
    

---

## **3.2.2 RISK_PARAMETERS**

리스크 엔진이 판단하는 위험 기준 설정.

예:

- MAX_POSITION_COUNT
    
- VIX_WARNING / DANGER
    
- MDD_LIMIT
    
- VOLATILITY_THRESHOLD
    

---

## **3.2.3 SYSTEM_PARAMETERS**

자동화 실행 엔진의 설정.

예:

- ENGINE_LOOP_INTERVAL
    
- BROKER_RETRY_LIMIT
    
- ORDER_SLIPPAGE_PCT
    

---

## **3.2.4 VALUE_MODEL_PARAMETERS**

가치투자 공식 구성요소:

- 정상 PER/PBR 범위
    
- ROE 목표 범위
    
- 성장률 가정
    
- 할인율 가정
    
- 안전마진 기준
    
- 내재가치 산출 기준(평균/중앙값 등)
    

---

## **3.2.5 Stability Layer Parameters (신규 정식 반영)**

이번 버전에서 새롭게 정식 도입된 안정성 파라미터 그룹.

|CATEGORY|설명|
|---|---|
|**STABILITY_CONFIG_VALIDATION**|Config 값 오류 자동 검증|
|**STABILITY_VERSION_TRACKING**|Config·Schema 변경 이력 기록|
|**STABILITY_AUDIT_LOGGING**|모든 엔진의 판단 근거 저장|
|**STABILITY_FAIL_SAFE**|위험 상황 자동 대응|
|**STABILITY_GRACEFUL_SHUTDOWN**|안전 종료 프로토콜|
|**STABILITY_RECOVERY**|재가동 시 자동 복구 절차|

※ 기존 문서 흐름을 유지하면서 이번 새 아키텍처의 핵심을 자연스럽게 완전 통합한 구조.

---

# **3.3 Position Sheet 정의**

Position Sheet는 현재 보유 종목의 상태를 관리하는 핵심 테이블이다.

주요 필드:

- symbol
    
- qty
    
- avg_price
    
- current_price
    
- pnl
    
- exposure
    
- weight
    

Portfolio Engine은 이 데이터를 기반으로  
비중 관리, 리밸런싱, 손익 계산을 수행한다.

—

# **3.4 Portfolio Sheet 정의**

투자자의 전체 자산 상태를 관리하는 데이터 테이블이다.

포함 정보:

- 총자산
    
- 가용 현금
    
- 종목별 비중
    
- 변동성 지표
    
- 위험 점수
    
- 투자 비중 설정 기준
    

Portfolio Sheet는 리스크 관리 및 전략 실행의 핵심 입력값을 제공한다.

---

# **3.5 T_Ledger 정의**

QTS 시스템의 **거래 원장(Ledger)** 이다.

포함 정보:

- 거래 시각
    
- 종목
    
- 방향 (Buy/Sell)
    
- 수량 및 가격
    
- 수수료
    
- 브로커 응답
    
- 슬리피지
    
- 거래 실패 여부
    

T_Ledger는 다음 분야에서 중추적 역할을 한다:

- 성과 분석
    
- 오류 추적
    
- 전략 개선
    
- 백테스트 검증
    

---

# **3.6 R_Dash 정의**

R_Dash는 리스크 대시보드로, 시스템의 위험 상태를 실시간 반영한다.

주요 데이터:

- 변동성 (20D, 60D)
    
- 종목별 위험 점수
    
- 시장 위험(VIX 등)
    
- 노출도
    
- 위험 등급
    
- 내부 Fail-safe 신호
    

Risk Engine은 이 데이터를 바탕으로  
매수 제한, 비중 축소, 강제 보호 모드 전환 등을 수행한다.

---

# **3.7 Dividend Sheet 정의**

배당 기반 가치 평가에 필요한 데이터 저장소다:

- 배당 지급일
    
- 배당금
    
- 배당 성장률
    
- 배당 지속성 여부
    

---

# **3.8 DT_DB / History Sheet 정의**

전략 신호, 리스크 계산 결과, 과거 데이터, 내재가치 추정치 등이 기록되는  
장기 저장소(Long-term Archive)이다.

역할:

- 전략 개선
    
- 백테스트 결과와 실제 결과 비교
    
- 장애 원인 분석
    
- 시각화 리포트 생성
    

---

# **3.9 Dashboard Sheet 정의**

운영자가 바로 확인할 수 있는 실시간 대시보드 역할을 하며:

- 현재 P/L
    
- 포트폴리오 상태
    
- 주요 신호
    
- 거래 상태
    
- 위험 레벨
    
- 브로커 연결 상태
    

를 집약적으로 보여준다.

---

# **3.10 데이터 품질 관리 규칙 (Data Quality Rules)**

기존 문서의 규칙을 유지하며,  
이번 신규 안정성 기준을 통합하여 확장한 최종 버전이다.

---

## **(1) 결측치 처리 규칙**

- 전략 필수 지표 결측 → 해당 종목 평가 제외
    
- 가치지표 결측 → 보수적 처리 또는 계산 제외
    
- 리스크 지표 결측 → Fail-safe 모드 진입 가능
    

---

## **(2) 이상치 처리 규칙**

- 비정상적 급등락 → 리스크 점수 보정
    
- 음수 불가 지표 → 즉시 오류 처리
    
- 산업/섹터 기준 밖 값 → 필터링
    

이 규칙들은 Stability Config Validation Layer와 결합하여 자동화된다.

---

## **(3) 타입 검증 규칙**

VALUE 칼럼의 타입은 다음 원칙으로 검증한다:

- 숫자여야 하는 항목은 숫자형 자동 변환
    
- 변환 실패 시 fallback 값 적용
    
- 문자열/Boolean 값 정규화
    

---

## **(4) 스키마 구조 검증 규칙**

Schema Engine이 자동으로 수행한다.

- 컬럼명 누락
    
- 순서 변경
    
- 필수 컬럼 삭제
    

발견 즉시 Version Tracking과 Fail-safe가 동작한다.

---

# **3.11 데이터 변경 이력 관리 (Version Tracking)**

Version Tracking Layer는 다음을 기록한다:

- Config 시트 변경 사항
    
- Schema 변화
    
- 엔진 버전 변경
    
- 주요 시스템 파라미터 변경
    

이 기록은 History Sheet 또는 별도 로그 파일에 저장된다.

---

# **PART 3. 데이터 정의 및 관리 체계 (Data Definition & Management System)**

본 파트는 QTS가 의존하는 모든 데이터 구조를 정의하고,  
Google Sheets 기반 데이터 웨어하우스의 전체 구조와 관리 규칙을 설명한다.

QTS는 단순히 데이터를 저장하는 시스템이 아니라,  
**데이터 품질 → 스키마 구조 → 검증 → 복구 → 안정성**까지 고려한  
완성도 높은 데이터 관리 체계를 구축하는 것을 목표로 한다.

---

# **3.1 데이터 관리 철학 (Data Philosophy)**

QTS 데이터 철학은 아래 4가지 원칙을 기반으로 한다.

### **(1) Single Source of Truth (SSOT)**

모든 설정 값은 Config 시트에서만 관리되며,  
전략·리스크·가치평가·시스템 파라미터는 하나의 통합 중앙 저장소에서 읽는다.

### **(2) Schema-driven Architecture**

엔진은 시트 구조에 직접 의존하지 않고  
항상 schema.json을 통해 구조를 해석한다.

### **(3) 자동 복구 가능성 (Self-healing)**

스키마 오류, 결측치, 타입 오류 등 데이터 문제가 발생해도  
엔진은 즉시 중단되지 않고 복구 절차를 수행한다.

### **(4) 완전한 Auditability**

데이터는 변경 이력과 함께 검증 가능해야 하며,  
모든 계산 결과는 Audit Logging Layer를 통해 기록된다.

---

# **3.2 Config Sheet 정의 (QTS 핵심 데이터 구조)**

Config Sheet는 QTS의 모든 설정 값을 저장하는 핵심 데이터이며  
전략·리스크·가치투자·시스템·안정성 파라미터의 SSOT 역할을 수행한다.

구조는 다음과 같다:

|Column|설명|
|---|---|
|A: CATEGORY|설정 대분류|
|B: SUB_CATEGORY|설정 중분류|
|C: KEY|내부 엔진 파라미터 이름|
|D: VALUE|실제 값|
|E: DESCRIPTION|설명|

Config에 설정되는 주요 그룹:

---

## **3.2.1 STRATEGY_PARAMETERS**

기술적 지표, 가치지표, 내재가치 모델 등  
전략 엔진이 사용하는 모든 파라미터 포함.

예:

- PER_MIN
    
- ROE_TARGET
    
- GROWTH_RATE_BASE
    
- RSI_BUY / RSI_SELL
    
- ATR_WINDOW
    
- DCF_DISCOUNT_RATE
    

---

## **3.2.2 RISK_PARAMETERS**

리스크 엔진이 판단하는 위험 기준 설정.

예:

- MAX_POSITION_COUNT
    
- VIX_WARNING / DANGER
    
- MDD_LIMIT
    
- VOLATILITY_THRESHOLD
    

---

## **3.2.3 SYSTEM_PARAMETERS**

자동화 실행 엔진의 설정.

예:

- ENGINE_LOOP_INTERVAL
    
- BROKER_RETRY_LIMIT
    
- ORDER_SLIPPAGE_PCT
    

---

## **3.2.4 VALUE_MODEL_PARAMETERS**

가치투자 공식 구성요소:

- 정상 PER/PBR 범위
    
- ROE 목표 범위
    
- 성장률 가정
    
- 할인율 가정
    
- 안전마진 기준
    
- 내재가치 산출 기준(평균/중앙값 등)
    

---

## **3.2.5 Stability Layer Parameters (신규 정식 반영)**

이번 버전에서 새롭게 정식 도입된 안정성 파라미터 그룹.

|CATEGORY|설명|
|---|---|
|**STABILITY_CONFIG_VALIDATION**|Config 값 오류 자동 검증|
|**STABILITY_VERSION_TRACKING**|Config·Schema 변경 이력 기록|
|**STABILITY_AUDIT_LOGGING**|모든 엔진의 판단 근거 저장|
|**STABILITY_FAIL_SAFE**|위험 상황 자동 대응|
|**STABILITY_GRACEFUL_SHUTDOWN**|안전 종료 프로토콜|
|**STABILITY_RECOVERY**|재가동 시 자동 복구 절차|

※ 기존 문서 흐름을 유지하면서 이번 새 아키텍처의 핵심을 자연스럽게 완전 통합한 구조.

---

# **3.3 Position Sheet 정의**

Position Sheet는 현재 보유 종목의 상태를 관리하는 핵심 테이블이다.

주요 필드:

- symbol
    
- qty
    
- avg_price
    
- current_price
    
- pnl
    
- exposure
    
- weight
    

Portfolio Engine은 이 데이터를 기반으로  
비중 관리, 리밸런싱, 손익 계산을 수행한다.

—

# **3.4 Portfolio Sheet 정의**

투자자의 전체 자산 상태를 관리하는 데이터 테이블이다.

포함 정보:

- 총자산
    
- 가용 현금
    
- 종목별 비중
    
- 변동성 지표
    
- 위험 점수
    
- 투자 비중 설정 기준
    

Portfolio Sheet는 리스크 관리 및 전략 실행의 핵심 입력값을 제공한다.

---

# **3.5 T_Ledger 정의**

QTS 시스템의 **거래 원장(Ledger)** 이다.

포함 정보:

- 거래 시각
    
- 종목
    
- 방향 (Buy/Sell)
    
- 수량 및 가격
    
- 수수료
    
- 브로커 응답
    
- 슬리피지
    
- 거래 실패 여부
    

T_Ledger는 다음 분야에서 중추적 역할을 한다:

- 성과 분석
    
- 오류 추적
    
- 전략 개선
    
- 백테스트 검증
    

---

# **3.6 R_Dash 정의**

R_Dash는 리스크 대시보드로, 시스템의 위험 상태를 실시간 반영한다.

주요 데이터:

- 변동성 (20D, 60D)
    
- 종목별 위험 점수
    
- 시장 위험(VIX 등)
    
- 노출도
    
- 위험 등급
    
- 내부 Fail-safe 신호
    

Risk Engine은 이 데이터를 바탕으로  
매수 제한, 비중 축소, 강제 보호 모드 전환 등을 수행한다.

---

# **3.7 Dividend Sheet 정의**

배당 기반 가치 평가에 필요한 데이터 저장소다:

- 배당 지급일
    
- 배당금
    
- 배당 성장률
    
- 배당 지속성 여부
    

---

# **3.8 DT_DB / History Sheet 정의**

전략 신호, 리스크 계산 결과, 과거 데이터, 내재가치 추정치 등이 기록되는  
장기 저장소(Long-term Archive)이다.

역할:

- 전략 개선
    
- 백테스트 결과와 실제 결과 비교
    
- 장애 원인 분석
    
- 시각화 리포트 생성
    

---

# **3.9 Dashboard Sheet 정의**

운영자가 바로 확인할 수 있는 실시간 대시보드 역할을 하며:

- 현재 P/L
    
- 포트폴리오 상태
    
- 주요 신호
    
- 거래 상태
    
- 위험 레벨
    
- 브로커 연결 상태
    

를 집약적으로 보여준다.

---

# **3.10 데이터 품질 관리 규칙 (Data Quality Rules)**

기존 문서의 규칙을 유지하며,  
이번 신규 안정성 기준을 통합하여 확장한 최종 버전이다.

---

## **(1) 결측치 처리 규칙**

- 전략 필수 지표 결측 → 해당 종목 평가 제외
    
- 가치지표 결측 → 보수적 처리 또는 계산 제외
    
- 리스크 지표 결측 → Fail-safe 모드 진입 가능
    

---

## **(2) 이상치 처리 규칙**

- 비정상적 급등락 → 리스크 점수 보정
    
- 음수 불가 지표 → 즉시 오류 처리
    
- 산업/섹터 기준 밖 값 → 필터링
    

이 규칙들은 Stability Config Validation Layer와 결합하여 자동화된다.

---

## **(3) 타입 검증 규칙**

VALUE 칼럼의 타입은 다음 원칙으로 검증한다:

- 숫자여야 하는 항목은 숫자형 자동 변환
    
- 변환 실패 시 fallback 값 적용
    
- 문자열/Boolean 값 정규화
    

---

## **(4) 스키마 구조 검증 규칙**

Schema Engine이 자동으로 수행한다.

- 컬럼명 누락
    
- 순서 변경
    
- 필수 컬럼 삭제
    

발견 즉시 Version Tracking과 Fail-safe가 동작한다.

---

# **3.11 데이터 변경 이력 관리 (Version Tracking)**

Version Tracking Layer는 다음을 기록한다:

- Config 시트 변경 사항
    
- Schema 변화
    
- 엔진 버전 변경
    
- 주요 시스템 파라미터 변경
    

이 기록은 History Sheet 또는 별도 로그 파일에 저장된다.

---

# **PART 5. 리스크 엔진 구조 및 위험 관리 체계 (Risk Engine & Risk Governance System)**

**Version: v1.0.0**

QTS의 리스크 엔진은 전체 시스템의 “생존성”을 책임지는 핵심 모듈이다.  
리스크 엔진의 목적은 수익 극대화가 아니라,  
**계좌의 장기적 생존을 보장하고 시스템 손상을 방지하는 것**에 있다.

리스크 엔진은 단순히 변동성을 계산하는 수준이 아니라,

- 계좌 노출도 관리
    
- 종목별 위험 점수 산출
    
- 시장 리스크 판단
    
- 전략 신호 필터링
    
- 자동 포지션 축소
    
- Fail-safe 및 Shutdown 연동
    
- 복구(Recovery) 협력
    

까지 포함하는 완성된 위험 관리 플랫폼이다.

---

# **5.1 리스크 엔진의 기본 원칙**

QTS 리스크 엔진은 다음 네 가지 원칙을 기반으로 설계되었다.

### **(1) Survival First – 생존이 최우선**

수익보다 중요한 것은 살아남는 것이다.  
리스크 엔진은 계좌 생존성을 최우선 목표로 한다.

### **(2) Multi-layered Risk Control – 다층적 위험 통제**

리스크는 다음 네 계층에서 독립적으로 평가된다:

1. **종목 리스크**
    
2. **포트폴리오 리스크**
    
3. **시장 리스크**
    
4. **시스템 리스크 (신규: 안정성 Layer)**
    

각 계층의 판단 결과는 전략 신호보다 우선한다.

### **(3) Proactive Protection – 선제적 위험 방어**

단순한 Stop-loss가 아니라,  
위험 신호가 일정 수준 이상 증가할 경우 **사전 차단 및 축소**를 실행한다.

### **(4) Transparent & Reproducible – 투명하고 재현 가능한 리스크 계산**

모든 위험 판단과 수식은 Audit Logging Layer에 기록되어  
사후 분석이 가능하다.

---

# **5.2 리스크 엔진 구성 요소**

리스크 엔진은 6개의 세부 모듈로 구성된다.

|모듈명|설명|
|---|---|
|**Volatility Module**|종목 및 시장 변동성 계산|
|**Exposure Module**|종목/섹터/포트폴리오 노출 비율 관리|
|**Market Risk Module**|시장 위험(VIX, KOSPI 변동성 등) 분석|
|**Drawdown Module**|계좌 낙폭(MDD) 평가 및 보호|
|**Risk Score Engine**|종합 위험 점수 산출|
|**Risk Governance Module**|리스크 판단에 따른 조치 실행 (제한/축소/중단 등)|

---

# **5.3 Volatility Module (변동성 분석)**

변동성은 리스크 엔진의 가장 기초적인 입력값이다.

### 계산 방식:

- 20일, 60일 표준편차 기반 변동성
    
- ATR 기반 변동성
    
- 종목별 변동성 증가율
    
- 시장 변동성(VIX/KOSPI/KOSDAQ)
    

### 역할:

- 변동성이 일정 기준을 넘으면 해당 종목의 매수 금지
    
- 변동성 급등 시 포지션 축소 신호
    
- 시장 변동성이 위험 수준이면 전체 매수 봉쇄
    

### Config 연동:

- 변동성 임계값은 Config Sheet에서 설정
    
- 값 오류는 Validation Layer가 자동 검증
    

---

# **5.4 Exposure Module (노출 비율 관리)**

Exposure는 계좌의 과도한 집중을 방지하는 핵심 모듈이다.

### 관리 항목:

- 종목당 최대 비중
    
- 섹터별 최대 비중
    
- 전체 시장 노출도
    
- 현금 비중 최소 기준
    

### 동작 로직:

- 비중이 상한선을 넘으면 리밸런싱 요청
    
- 과도한 포지션 집중은 자동 축소
    
- 시장 급락 시 현금 비중 강화
    

### Config에서 관리되는 값:

- MAX_POSITION_COUNT
    
- MAX_POSITION_PCT
    
- MAX_TOTAL_EXPOSURE
    

---

# **5.5 Market Risk Module (시장 위험 분석)**

시장 위험은 종목 단위보다 상위의 위험이므로 최종 의사결정을 크게 좌우한다.

### 분석 지표:

- VIX 지수
    
- KOSPI/KOSDAQ 변동성
    
- 시장 추세 전환 여부
    
- 글로벌 위험 신호(선택적 사용 가능)
    

### 역할:

- 시장 위험 증가 → 전체 매수 차단
    
- 위험 급등 → 기존 포지션 축소 지시
    

### 안정성 Layer와의 결합:

시장 데이터 자체가 비정상일 경우  
Fail-safe 모드가 자동 발동하도록 설계된다.

---

# **5.6 Drawdown Module (계좌 낙폭 관리)**

MDD(Maximum Drawdown)는 계좌 보호의 핵심이다.

### 기능:

- 계좌 낙폭 추적
    
- 일일 손실률 추적
    
- 손실률에 따른 보호 조치 결정
    

### Config 설정 예:

- MAX_DRAWDOWN
    
- DAILY_LOSS_LIMIT
    
- RECOVERY_THRESHOLD
    

### 동작 예시:

- MDD가 기준 초과 → 전체 거래 중단 + Fail-safe 호출
    
- 일일 손실 2% 도달 → 매수 금지 + 비중 축소
    

---

# **5.7 Risk Score Engine (종합 리스크 점수)**

리스크 엔진의 중심 모듈이다.

### 리스크 점수를 구성하는 요소:

- 변동성
    
- 노출도
    
- 시장 위험
    
- 낙폭
    
- 종목의 위험 신호(예: 급락)
    

리스크 점수는 0~100 점수로 변환되며,  
높을수록 위험이 큰 상태이다.

최종 점수는 다음 기준으로 분류된다:

|점수|구분|
|---|---|
|0~30|안전|
|31~50|주의|
|51~70|경고|
|71~100|위험|

---

# **5.8 Risk Governance Module (조치 실행 모듈)**

리스크 엔진의 결과를 실제 행동으로 연결하는 실행 제어 모듈이다.

### 가능한 조치:

- 매수 금지
    
- 특정 섹터 금지
    
- 비중 축소
    
- 포지션 정리
    
- 시스템 보호 모드 진입
    
- Graceful Shutdown
    
- Fail-safe 강제 발동
    

### 예시:

```
if risk_score > 70:
    trigger_fail_safe("Portfolio risk too high")
    block_all_buy_orders()
```

---

# **5.9 전략 엔진과의 연결 구조**

Risk Engine은 Strategy Engine보다 항상 우선한다.

### 구조:

1. Strategy Engine이 Buy 신호 발생
    
2. Risk Engine이 신호를 평가
    
3. 리스크가 허용 범위면 실행 엔진으로 전달
    
4. 리스크 초과면 신호 차단
    
5. 위험 심각 시 Fail-safe 호출
    

이 로직은 기존 문서의 핵심 구조를 유지한 상태에서  
안정성 Layer와 결합하여 더 견고해진 형태다.

---

# **5.10 스키마 엔진 및 안정성 Layer와의 결합**

Risk Engine은 다른 엔진보다  
Schema Engine과 Stability Layer의 영향을 크게 받는다.

### (1) R_Dash 스키마 변경을 Schema Diff가 감지

- 컬럼 삭제/추가 시 버그 예방
    
- 자동 복구 및 fallback 처리
    

### (2) Config 값 오류 시 Validation Layer가 차단

예:  
MAX_POSITION_COUNT가 음수 → 자동 수정 적용 + 경고 기록

### (3) 시스템 위험 감지 시 Fail-safe

예:  
보유 종목의 변동성 데이터가 누락 → 즉시 보수 모드로 이동

### (4) Graceful Shutdown과의 연결

리스크 폭주 시 무조건적 종료가 아니라  
안전하게 포지션을 처리 후 종료

---

# **5.11 리스크 엔진의 최종 출력 형태**

Risk Engine은 다음 형태의 결과를 반환한다:

```
{
    "portfolio_risk": 62,
    "market_risk": "WARNING",
    "exposure_status": "LIMIT_REACHED",
    "allow_buy": false,
    "force_reduce": true,
    "fail_safe_trigger": false,
    "timestamp": "2025-01-13 14:34"
}
```

이 출력은 Execution Layer가 실제 주문을 결정하는 기준이 된다.

---

# **PART 6. 포트폴리오 엔진 구조 (Portfolio Engine Architecture)**

**Version: v1.0.0**

포트폴리오 엔진(Portfolio Engine)은 QTS의 계좌 운영 심장부이며,  
전략 엔진과 리스크 엔진이 산출한 결과를 실제 포트폴리오 상태에 반영하는 핵심 시스템이다.

이 엔진의 목적은 단순히 수익을 만드는 것이 아니라,  
**안정적인 비중 관리·리스크 대응·자산 성장 구조를 유지하는 것**에 있다.

본 파트에서는 포트폴리오 엔진의 구조, 데이터 처리 방식, 리밸런싱 규칙,  
리스크와 전략 신호의 연결 방식, 시스템 안정성 요소까지 완전한 형태로 정의한다.

---

# **6.1 포트폴리오 엔진의 기본 원칙**

QTS 포트폴리오 엔진은 다음 네 가지 원칙을 기반으로 설계되어 있다.

### **(1) Exposure Discipline – 노출 비율 준수**

과도한 한 종목 집중은 장기 성과를 위협한다.  
포트폴리오 엔진은 Exposure(노출 비율)를 항상 관리한다.

### **(2) Cash as a Position – 현금도 하나의 포지션으로 취급**

현금 비중이 낮아지는 경우 리스크가 급격히 증가한다.  
전략 신호가 아무리 좋아도 현금이 일정 수준 이하로 떨어지면 매수를 제한한다.

### **(3) Risk-aligned Execution – 리스크 기반 실행**

포트폴리오 변경은 반드시 리스크 엔진의 판단과 연계되어 수행된다.

### **(4) Stable Long-term Growth – 장기 성장 중심의 균형 유지**

단기 수익률보다 장기적으로 견딜 수 있는 구조가 우선한다.  
포트폴리오 엔진은 최소 단위의 불필요한 변화를 억제한다.

---

# **6.2 포트폴리오 엔진 구성 요소**

포트폴리오 엔진은 총 6개의 모듈로 구성된다.

|모듈명|설명|
|---|---|
|**Position Loader**|현재 보유 포지션 데이터 로딩|
|**Weight Calculator**|비중·노출 비율 계산|
|**Rebalancing Engine**|리밸런싱 판단 및 실행|
|**Exposure Controller**|과도한 집중 방지|
|**Portfolio Risk Adjuster**|위험도 기반 비중 제어|
|**Portfolio State Writer**|결과를 Portfolio Sheet에 기록|

각 모듈은 독립적이며, Schema Engine과 Validation Layer를 통해  
안정적으로 데이터를 읽고 쓴다.

---

# **6.3 Position Loader (포지션 로더)**

포트폴리오 엔진은 Portfolio Sheet와 Position Sheet를 기반으로 데이터를 로드한다.

### 주요 기능:

- 포지션 정보 로딩
    
- 결측 데이터 보정
    
- 이전 실행 대비 포지션 변화 감지
    
- 스키마 기반 자동 매핑 (schema.json 사용)
    

### 안정성 Layer와의 결합:

- 스키마 불일치 발생 시 Diff Engine이 즉시 감지
    
- Validation Layer가 타입 오류 자동 정정
    
- 오류 발생 시 Fail-safe 모드에서 "읽기 전용(Read-Only Mode)"로 전환
    

---

# **6.4 Weight Calculator (비중 계산기)**

Weight Calculator는 포트폴리오 상태의 핵심 정보를 계산한다.

### 계산 항목:

- 종목별 비중(weight)
    
- 총 노출도(total exposure)
    
- 섹터별 노출도
    
- 현금 비중
    
- 위험 가중 비중
    

계산된 결과는 Portfolio Sheet에 반영된다.

---

# **6.5 Exposure Controller (노출 비율 제어)**

Exposure Controller는 계좌의 과도한 집중을 제어하는 안전장치이다.

### 동작 규칙:

- 종목당 비중이 MAX_POSITION_PCT를 초과 → 비중 축소 요청
    
- 총 노출도가 MAX_TOTAL_EXPOSURE 초과 → 매수 제한
    
- 섹터별 비중 과다 → 특정 섹터 매수 차단
    

### 모든 기준은 Config Sheet에서 관리된다.

### 안정성 요소:

- Exposure 계산 오류 시 fallback 값 적용
    
- trigger_level을 넘으면 자동 Fail-safe 연동
    

---

# **6.6 Rebalancing Engine (리밸런싱 엔진)**

리밸런싱은 포트폴리오 엔진의 핵심 기능이다.

### 리밸런싱 트리거:

- 비중 과다/과소
    
- 리스크 점수 급등
    
- 전략 점수 변화
    
- 시장 국면 변화
    
- 내부 시스템 경고
    

### 리밸런싱 목적:

- 특정 종목의 과도한 성장으로 인한 위험 제거
    
- 전체 포트폴리오의 Target Exposure 유지
    
- 장기 성장 구조 최적화
    

### 실행 방식:

- Soft Rebalancing: 작은 조정
    
- Hard Rebalancing: 비중 강제 조정
    
- Auto Rebalancing: 조건 충족 시 자동 실행
    

---

# **6.7 Portfolio Risk Adjuster (포트폴리오 위험 조정기)**

포트폴리오 엔진은 Risk Engine의 판단을 반영하여 비중을 조정한다.

### 판단 요소:

- 시장 위험 수준
    
- 포트폴리오 위험 점수
    
- 종목별 오류 발생 여부
    
- 노출도 상태
    
- 매수 차단 조건 여부
    

### 조정 방식:

- 위험 구간 → 매수 금지
    
- 경고 구간 → 매수 최소화
    
- 위험 수준 심각 → 강제 축소
    
- Fail-safe → 전체 축소/중단
    

### 안정성 Layer 통합:

- Risk Engine 경고 시 자동 Graceful Shutdown 가능
    
- Audit Logging에 모든 조정 기록
    

---

# **6.8 Portfolio State Writer (포트폴리오 상태 기록기)**

최종 계산된 포트폴리오 상태를 Portfolio Sheet에 기록한다.

### 기록 항목:

- 총자산
    
- 현금잔고
    
- 종목별 비중
    
- 변동성
    
- 리스크 점수
    
- 노출도
    

### 기록 방식:

- Schema 기반 자동 필드 매핑
    
- Validation Layer로 데이터 검증
    
- Write 실패 시 Recovery Engine이 이전 기록으로 복원
    

---

# **6.9 포트폴리오 엔진의 전체 실행 흐름**

실행 순서는 다음과 같다.

```
1) Position Loader → 데이터 로드
2) Weight Calculator → 비중 및 노출 계산
3) Risk Engine 데이터 반영
4) Exposure Controller → 노출 초과 여부 판단
5) Rebalancing Engine → 조정 필요 여부 판단
6) Portfolio Risk Adjuster → 리스크 기반 조치
7) Portfolio State Writer → 결과 기록
```

이는 기존 문서의 기본 흐름을 유지하면서,  
스키마 엔진과 안정성 Layer를 자연스럽게 통합한 형태다.

---

# **6.10 포트폴리오 엔진 안정성 요소 (Stability Integration)**

포트폴리오 엔진은 시스템 위험과 직접 연결되어 있기 때문에  
Stability Layer의 모든 요소와 연동된다.

### **(1) Config Validation Layer**

- 값 오류 → 비중 계산 차단
    
- MAX_POSITION_COUNT 음수 → 자동 수정
    

### **(2) Version Tracking Layer**

- 포트폴리오 기준 변경 이력 자동 기록
    

### **(3) Audit Logging Layer**

- 비중 조정 근거
    
- 리밸런싱 근거
    
- 리스크 기반 조정 기록
    

### **(4) Fail-safe Decision Engine**

- 노출도 폭주 → Fail-safe 강제 발동
    

### **(5) Graceful Shutdown**

- 포트폴리오 기록 중 오류 발생 시 안전 종료
    

### **(6) Recovery Engine**

- 포트폴리오 스냅샷 복구
    
- 비정상 상태 복원
    

---

# **6.11 포트폴리오 엔진 최종 출력 구조**

Portfolio Engine은 다음과 같은 최종 결과를 생성한다:

```
{
    "total_equity": 12500000,
    "cash_ratio": 34.1,
    "exposure": 0.66,
    "risk_level": "WARNING",
    "rebalance_required": true,
    "positions": [...],
    "timestamp": "2025-01-13 14:48"
}
```

이 출력은 다음으로 전달된다:

- Execution Layer
    
- Dashboard Sheet
    
- History Sheet
    
- Backtest Engine
    
- Stability Layer (감시 및 보호)
    

---

# **PART 7. 실행 엔진 구조 (Execution Engine Architecture)**

Execution Engine은 QTS에서 실제 거래를 수행하는 핵심 실행 모듈이다.  
전략 엔진과 리스크 엔진이 생성한 신호를 기반으로 거래 주문을 만들고,  
브로커(KIS API)와 통신하여 체결을 검증한다.

Execution Engine은 단순한 “주문 전송기”가 아니며,

- 재시도 로직
    
- 슬리피지 반영
    
- 예외 처리
    
- 브로커 장애 대응
    
- 로그 기록
    
- Fail-safe 연동
    
- Graceful Shutdown 연계
    

까지 포함하는 완전한 자동 거래 시스템이다.

---

# **7.1 실행 엔진의 설계 원칙**

Execution Engine은 다음의 명확한 기준을 기반으로 설계된다.

### **(1) Reliability – 안정성 최우선**

모든 자동매매 시스템의 약점은 “실행 불능”이며,  
이를 최소화하기 위해 안정성을 가장 중요한 요소로 둔다.

### **(2) Non-blocking – 실행 중단 금지**

주문 실패, API 타임아웃 등 모든 상황에서 엔진이 멈추지 않도록 설계한다.

### **(3) Safety Integration – 안전 모드 연동**

리스크 엔진, Fail-safe 엔진, Validation Layer와 긴밀히 연결되어  
위험 상황에서 자동으로 거래를 억제한다.

### **(4) Determinism – 일관된 실행 구조**

같은 조건이면 언제나 같은 방식으로 주문이 생성되어야 한다.

---

# **7.2 실행 엔진 구성 요소**

Execution Engine은 7개의 서브모듈로 구성된다.

|모듈명|설명|
|---|---|
|**Order Builder**|주문 생성 (수량, 가격 계산)|
|**Slippage Processor**|슬리피지 반영|
|**Broker Connector**|KIS API 연결 관리|
|**Retry & Error Handler**|실패 시 재시도 및 오류 처리|
|**Execution Validator**|주문 조건 검증|
|**Execution Logger**|실행 로그 기록|
|**Execution Governance**|Fail-safe / Shutdown / 제한 조건과 연동|

---

# **7.3 Order Builder (주문 생성기)**

Order Builder는 전략·포트폴리오·리스크 엔진 데이터를 기반으로  
실제 주문 형태를 생성한다.

### 입력:

- buy_signal / sell_signal
    
- 목표 비중
    
- 현재 비중
    
- 매수 가능한 금액
    
- 리스크 수준
    

### 출력 예:

```
{
  "symbol": "005930",
  "side": "BUY",
  "qty": 12,
  "price": 72100
}
```

### 안정성 요소:

- 비정상 수량(0 이하) 자동 차단
    
- Config Validation Layer로 가격·수량 유효성 검증
    
- 오류 발생 시 fallback 계산 적용
    

---

# **7.4 Slippage Processor (슬리피지 반영)**

슬리피지는 실제 체결가와 예상가의 차이를 뜻한다.

### 목적:

- 전략 왜곡 방지
    
- 과도한 체결 비용 방지
    
- 백테스트와 실거래의 차이를 줄임
    

### 계산 방식:

- ORDER_SLIPPAGE_PCT 적용
    
- 변동성 환경 기반 동적 조정 가능
    

### 안정성:

- 슬리피지 계산 오류 → Validation Layer가 자동 복원
    

---

# **7.5 Broker Connector (브로커 API 연결)**

브로커와 통신하는 핵심 인터페이스다.

### 기능:

- 주문 요청
    
- 응답 수신
    
- 체결 여부 확인
    
- API 토큰 갱신
    
- 타임아웃 관리
    
- 재시도 로직 호출
    

### 안정성 요소:

- 브로커 응답 지연 시 자동 재시도
    
- BROKER_RETRY_LIMIT 초과 시 Fail-safe 호출
    
- 응답 포맷 오류 → Graceful Shutdown 조건 가능
    
- 모든 응답은 Execution Logger에서 기록
    

---

# **7.6 Retry & Error Handler (재시도 / 오류 처리기)**

실거래에서는 오류가 필연적으로 발생한다.

### 오류 유형 예:

- API 연결 실패
    
- 주문 불가 (제한 / 종목 정지)
    
- 체결 지연
    
- 서버 응답 NULL
    

### 처리 방식:

1. 즉시 재시도
    
2. 재시도 간격 조정(BROKER_RETRY_INTERVAL)
    
3. 재시도 제한 초과 시 Fail-safe 호출
    
4. Audit Logging에 상세 기록 저장
    

---

# **7.7 Execution Validator (실행 검증기)**

주문 전 반드시 아래 조건을 검증한다:

- Risk Engine이 매수 허용했는가
    
- Exposure 초과 여부
    
- 현금 부족 여부
    
- Config 값 유효성 여부
    
- 포지션 수 제한 초과 여부
    

### 안정성 Layer와의 결합:

- Config Validation 문제가 있을 경우 해당 주문 차단
    
- 리스크 경고 레벨이면 매수 차단
    
- Fail-safe 상태면 모든 주문 중단
    

Execution Layer는 어떤 상황에서도  
잘못된 주문을 발생시키지 않는 구조로 설계되어 있다.

---

# **7.8 Execution Logger (실행 로그 저장기)**

실행 엔진에서 발생하는 모든 상태는  
Audit Logging Layer에 기록된다.

### 기록 항목:

- 주문 요청 전 상태
    
- 주문 생성 정보
    
- 브로커 응답
    
- 오류 상세 내용
    
- 재시도 기록
    
- 실행 결과
    

기록은 JSON 기반으로 로컬/시트/파일 등 선택된 방식으로 저장된다.

---

# **7.9 Execution Governance (실행 통제 시스템)**

_(신규: 안정성 Layer와 통합된 공식 구조)_

Execution Governance는 실행 엔진이  
잘못된 환경에서 거래하지 않도록 통제하는 보호 계층이다.

### 기능:

- Fail-safe 모드 → 자동 거래 중지
    
- Graceful Shutdown 호출 → 안전 종료
    
- Config 오류 → 주문 우선 차단
    
- 스키마 오류 → 주문 데이터 생성 차단
    
- 시장 위험 폭주 → buy-order 전면 금지
    

### 사례 예:

```
if risk_level == "DANGER":
    block_buy_orders()
if fail_safe_triggered:
    pause_all_trading()
if schema_invalid:
    halt_execution("Schema mismatch detected")
```

Execution Governance는 리스크 엔진, 안정성 Layer, 스키마 엔진과 밀접하게 연결되어  
거래 오류를 최소화하는 완전한 보호 체계를 제공한다.

---

# **7.10 실행 엔진 전체 흐름**

실행 과정은 아래 순서로 진행된다:

```
1) Strategy Engine → buy/sell 신호 전달
2) Risk Engine → 허용 여부 판단
3) Execution Validator → 주문 검증
4) Order Builder → 주문 생성
5) Slippage Processor → 가격 보정
6) Broker Connector → 주문 요청
7) Retry Handler → 오류 대응
8) Execution Logger → 기록 저장
9) Governance Module → 보호 조치 적용
```

이 구조는 기존 설계를 유지하면서  
최신 안정성 Layer와 Schema Engine을 자연스럽게 흡수한  
정식 v1.0.0 아키텍처이다.

---

# **7.11 실행 엔진 최종 출력 예시**

```
{
    "symbol": "035420",
    "side": "BUY",
    "qty": 5,
    "expected_price": 210000,
    "executed_price": 210500,
    "slippage_pct": 0.24,
    "status": "FILLED",
    "risk_evaluation": "ACCEPTED",
    "timestamp": "2025-01-13 15:02",
    "logs": {...}
}
```

이 결과는:

- T_Ledger 기록
    
- Dashboard 표시
    
- Portfolio Engine 업데이트
    
- History 저장
    
- 안정성 Layer 검증
    

등 QTS 내부의 전 계층으로 전달된다.

---

# **PART 8. Fail-safe & 운영 안정성 아키텍처 (System Stability & Fail-safe Architecture)**

Fail-safe Architecture는 QTS의 **생존성(Survivability)** 을 보장하는 핵심 시스템이며,  
전략이나 데이터가 아니라 **운영 안정성(Stability) 그 자체**를 책임지는 계층이다.

시장에서 예측 불가능한 상황이 발생해도 엔진이 멈추지 않고,  
실수·오류·데이터 문제·API 장애 발생 시 손실을 최소화하고,  
문제 지점을 정확히 기록해 이후 유지보수가 가능하도록 설계한다.

Fail-safe는 “예외 처리의 확장판”이 아니라  
**운영 안전을 독립적으로 관리하는 보호 레이어**이다.

---

# **8.1 Fail-safe 아키텍처의 역할**

Fail-safe Layer는 다음의 5가지 역할을 수행한다:

### **(1) 시스템 보호 (System Guard)**

비정상 상태 감지, 거래 중단, 모듈 비활성화 등 즉각적인 보호 기능 수행.

### **(2) 자산 보호 (Capital Protection)**

갑작스러운 시장 변동 / API 장애 / 데이터 이상치로 인한 손실을 최소화.

### **(3) 런타임 질서 유지 (Runtime Governance)**

각 엔진의 상태를 감시하며, 위험 상황에서 실행 흐름을 제어.

### **(4) 장애 발생 시 복원성 확보 (Resilience)**

Graceful Shutdown, 재기동(재부팅) 후 정상 운영으로 복원.

### **(5) 유지보수 편의성 제공 (Maintainability)**

문제 원인 기록, 재현 가능한 상태 저장.

---

# **8.2 Fail-safe 구성 레이어**

Fail-safe는 총 6개의 레이어로 구성되며,  
이는 타우가 요청했던 안정성 6대 모듈이 그대로 설계에 반영된 구조다.

|레이어|설명|
|---|---|
|**1. Fail-safe Trigger Layer**|위험 감지 후 즉시 보호 조치 실행|
|**2. Config Protection & Validation Layer**|Config 오류·이상 설정 자동 차단|
|**3. Schema Integrity Layer**|스키마 구조 오류 발생 시 전체 거래 차단|
|**4. Execution Safeguard Layer**|실행 엔진 보호, 주문 차단, 오류 확산 억제|
|**5. Graceful Shutdown Layer**|안전 종료, 재부팅 준비|
|**6. Audit Logging Layer**|모든 상태·이벤트 기록|

이 6대 Layer는 서로 독립적이면서, 동시에 상호 연계된 통합 안전 체계다.

---

# **8.3 Fail-safe Trigger Layer (위험 감지 엔진)**

Fail-safe Trigger는 리스크 엔진과 데이터 엔진에서 넘어오는  
위험 신호를 기반으로 즉시 시스템 보호 조치를 실행한다.

### 감지 항목:

- DD 위험 수준 도달
    
- 시장 변동성 급증
    
- API 반복 오류
    
- 데이터 스키마 불일치
    
- Config 값 유효성 실패
    
- 포트폴리오 손실 급증
    
- 주문 실패 반복
    

### Trigger가 발생하면:

```
fail_safe_status = "ON"
pause_all_trading()
log("Fail-safe triggered: DD Danger")
```

---

# **8.4 Config Protection & Validation Layer**

QTS는 Config를 매우 중요한 운영 자산으로 본다.  
Config 오류는 곧 잘못된 거래로 이어지기 때문에,  
Fail-safe는 Config Validation Layer를 운영한다.

### 검증 항목:

- 값의 타입(Type) 검증
    
- 범위(Range) 검증
    
- 필수 값 누락 검증
    
- 비논리적 값 조합 탐지
    
- 전략/리스크/포트폴리오 모듈과의 충돌 여부
    

### 오류 시 조치:

- Config 부분 차단
    
- 해당 전략 중지
    
- 전체 엔진 Fail-safe 모드 진입
    

### 예시:

```
if config["MAX_POSITION_PCT"] > 0.3:
    block_execution("Excess position configuration")
```

---

# **8.5 Schema Integrity Layer (스키마 무결성 보호)**

데이터 스키마는 QTS의 기반 구조이며,  
스키마가 깨지는 순간 전략·포트폴리오·리스크가 모두 오작동하게 된다.

### 스키마 무결성 점검:

- 시트 컬럼 구조 비교
    
- auto_schema.json과 시트 구조 diff
    
- 삭제·추가 컬럼 탐지
    
- 필수 컬럼 누락 여부
    
- 데이터 타입 일관성
    

### 문제 발생 시 즉시 차단:

```
if schema_diff.detect_mismatch():
    halt_execution("Schema mismatch detected")
```

### 이 Layer는 안정성 모듈 중 가장 중요한 역할을 담당한다.

---

# **8.6 Execution Safeguard Layer (실행 엔진 보호)**

Execution Layer는 매수/매도 주문을 실제로 브로커에 전달하는 계층이므로  
여기서의 오류는 즉각적인 손실로 이어질 수 있다.

Safeguard Layer는 다음을 보호한다:

- 비정상 주문 차단
    
- 동일 주문 중복 전송 방지
    
- 반복 오류 시 주문 중단
    
- API 장애 시 시스템 확산 방지
    

### 예시:

```
if retry_count >= BROKER_RETRY_LIMIT:
    pause_buy_orders()
```

---

# **8.7 Graceful Shutdown Layer**

**Graceful Shutdown**은 갑작스러운 종료를 방지하고  
정상적인 상태를 유지한 채 운영을 멈추는 종료 방식이다.

### 수행 절차:

1. 모든 주문 즉시 중단
    
2. 포트폴리오/포지션 저장
    
3. 대기 중인 작업 플러시(flush)
    
4. 로그 저장
    
5. 상태 스냅샷 저장
    
6. 엔진 종료
    

Graceful Shutdown은 장애 복구 시 복원 속도를 크게 개선한다.

---

# **8.8 Audit Logging Layer (전체 기록 시스템)**

Fail-safe는 운영 안정성 확보를 넘어  
유지보수·분석·역추적을 지원하는 전체 기록 시스템을 제공한다.

### 기록 항목:

- Fail-safe 발생
    
- Config 변경
    
- 스키마 변경
    
- 주문 실행 및 실패
    
- 리스크 경고 발동
    
- 시장 상태 경고
    
- Graceful Shutdown 실행
    

### 기록의 목적:

- 문제 상황 재현 가능
    
- 디버깅 속도 개선
    
- 전략 검증 근거 확보
    
- 운영 투명성 향상
    

---

# **8.9 운영 안정성 아키텍처의 전체 흐름**

운영 과정은 아래 순서로 실행된다:

```
1) 데이터 수집 → 스키마 검증
2) Config Validation 적용
3) 리스크 수준 감지
4) Fail-safe Trigger 조건 확인
5) Execution Safeguard로 주문 검증
6) 이상 신호 발생 → 즉시 Fail-safe 모드
7) 운영 유지 or Graceful Shutdown
8) Audit Logging 저장
9) 시스템 복구 또는 재기동
```

이 구조는 안정성·복원성·투명성을 기반으로  
QTS가 장기적으로 안정적인 자동매매 시스템으로 운영되도록 설계되어 있다.

---

# **8.10 Fail-safe 동작 예시**

### 예시 1: DD 위험

```
if dd_ratio >= KS_TRIGGER_DD:
    fail_safe_on("Drawdown limit exceeded")
```

### 예시 2: 스키마 오류

```
if schema_diff.missing_columns():
    halt_execution("Critical columns missing")
```

### 예시 3: API 장애

```
if retry_count > BROKER_RETRY_LIMIT:
    pause_all_trading()
```

---

# **PART 9. 리스크 엔진 아키텍처 (Risk Engine Architecture)**

Risk Engine은 QTS 전체 운영의 **안전장치이자 심장부**로,  
전략에서 생성된 신호가 실제 매수·매도로 이어지기 전에  
리스크 관점에서 모든 조건을 평가하는 필수 Layer이다.

리스크 엔진은 단순히 "위험 계산기"가 아니라  
**전략, 포트폴리오, 시장 환경, 변동성, 시나리오 기반 위험 통제 기능을 통합한 통합 의사결정 시스템**이다.

이 엔진이 허용하지 않으면 QTS는 어떤 조건에서도 거래하지 않는다.

---

# **9.1 리스크 엔진의 목적**

리스크 엔진은 다음의 5가지 핵심 목적을 가진다:

### **(1) 손실 방지 (Capital Preservation)**

과도한 손실, 변동성 증가, 불리한 시장 조건에 대한 방어장치.

### **(2) 포트폴리오 안정성 (Portfolio Stability)**

보유 자산의 균형 유지 및 과도한 집중을 방지.

### **(3) 전략 신호 검증 (Signal Approval)**

전략에서 발생한 buy/sell 신호가  
리스크 관점에서 허용 가능한지 최종 승인.

### **(4) 시장 환경 변화 대응 (Market Condition Adaptation)**

변동성, 시장 위험도, 업종 위험 수준을 고려해 동적으로 리스크 조정.

### **(5) 시스템 통합 (Inter-layer Coordination)**

Fail-safe, Execution Engine, Portfolio Engine과 연계해  
운영 과정 전체가 안정적으로 진행되도록 조정.

---

# **9.2 리스크 엔진의 핵심 구조**

Risk Engine은 다음 6개 모듈로 구성되며  
각 모듈은 독립적으로 작동하면서도 유기적으로 결합한다.

|모듈|설명|
|---|---|
|**1. Exposure Control**|종목·총 자산 비중 조절|
|**2. Volatility Risk Module**|변동성 기반 위험 조정|
|**3. Drawdown Risk Module**|DD 기준 기반 안전장치|
|**4. Market Regime Filter**|시장 장세 분석 후 위험 조절|
|**5. Portfolio Concentration Module**|특정 종목/업종 쏠림 방지|
|**6. Position Risk Filter**|포지션 유지/청산 조건 평가|

---

# **9.3 Exposure Control (익스포저 통제 모듈)**

포트폴리오에서 가장 중요한 요소 중 하나는  
"너무 많이 담지 않는 것"이다.

### 관리 항목:

- MAX_POSITION_PCT
    
- MAX_TOTAL_EXPOSURE
    
- MAX_POSITION_COUNT
    

### 주요 역할:

- 종목당 최대 비중 초과 차단
    
- 전체 포트폴리오 비중 초과 차단
    
- 보유 종목 수 관리
    

### 예시:

```
if position_pct > MAX_POSITION_PCT:
    reject_buy("Exposure limit exceeded")
```

---

# **9.4 Volatility Risk Module (변동성 위험 모듈)**

변동성은 직접적인 위험 지표이며,  
높은 변동성은 QTS의 거래 리스크를 크게 증가시킨다.

### 입력 데이터:

- 20일 변동성
    
- ATR
    
- 시장 지수 변동성
    
- 업종 변동성
    

### 작동 방식:

- 변동성 수준이 높으면 매수 제한
    
- 변동성이 급격히 증가하면 포지션 축소
    
- ATR 기반 주문 수량 축소 기능 포함
    

### 예시:

```
if volatility_20d > VOLATILITY_LIMIT_20D:
    block_buy()
```

---

# **9.5 Drawdown Risk Module (DD 위험 모듈)**

DD(Drawdown)는 자산 감소 폭을 의미하며,  
확대될수록 추가 매수는 큰 위험을 초래한다.

### 관리 항목:

- DD_WARNING_LEVEL
    
- DD_DANGER_LEVEL
    
- KS_TRIGGER_DD (Kill Switch Trigger)
    

### 동작:

- 경고 수준 → 매수 신호 약화
    
- 위험 수준 → 매수 차단
    
- Kill Switch 수준 → 전체 매매 즉시 정지
    

---

# **9.6 Market Regime Filter (시장 레짐 필터)**

시장은 상승·하락·변동성 확대 국면 등 여러 상태를 갖는다.

### 판단 요소:

- KOSPI/KOSDAQ 변동성
    
- 장중 시장 퍼포먼스
    
- 지수 추세 방향
    
- 업종별 상대세
    

### 효과:

- 위험 국면 → 보수적 매매
    
- 안정 국면 → 정상 매매
    
- 강세 국면 → 공격적 매매 허용(단 조건부)
    

---

# **9.7 Portfolio Concentration Module (집중도 관리)**

포트폴리오가 특정 종목·업종에 과도하게 모이면  
전략은 한 번의 시장 충격에 큰 손실을 입는다.

### 기능:

- 업종별 최대 비중 제한
    
- 종목별 상관관계 기반 비중 조정
    
- 포트폴리오 다변화 지표 활용
    

### 예:

```
if sector_exposure > SECTOR_LIMIT:
    reject_buy()
```

---

# **9.8 Position Risk Filter (포지션 위험 필터)**

각 포지션의 상태를 평가해  
청산 또는 유지 여부를 결정한다.

### 평가 요소:

- 변동성 급증
    
- 손절 기준 충족
    
- 전략 신호 반전
    
- 시장 위험 경고
    
- 업종 위험 증가
    

포지션 유지 여부는 단순히 전략 신호만으로 결정되지 않고  
**리스크·시장 위험·집중도**를 종합해 평가한다.

---

# **9.9 리스크 평가 → 전략 신호 승인 구조**

Risk Engine은 전략 엔진으로부터 받은 신호를  
아래 단계로 평가한다:

```
1) Exposure 평가
2) 변동성 평가
3) Drawdown 상태 확인
4) 시장 레짐 검토
5) 포트폴리오 집중도 검증
6) 포지션 단위 위험 점검
```

모든 조건을 통과해야 다음 메시지를 반환한다:

```
risk_result = "APPROVED"
```

하나라도 실패하면:

```
risk_result = "REJECTED"
```

---

# **9.10 리스크 엔진의 Fail-safe 연동**

Risk Engine은 Fail-safe Layer와 깊이 결합되어 있다.

### 연동 방식:

- 리스크 임계값 초과 → Fail-safe 자동 발동
    
- DD 위험 → 거래 중단
    
- 스키마/Config 오류 → 거래 차단
    
- 시장 위험 폭주 → buy 신호 전면 금지
    
- 반복 주문 실패 → Fail-safe로 전환
    

### 목적:

실수·장애·시장 이상으로 인한 급격한 손실을 방지.

---

# **9.11 리스크 엔진의 로그 기록 구조**

모든 리스크 관련 의사결정은  
Audit Logging Layer에 자동 저장된다.

### 기록 항목:

- Exposure 판단
    
- 변동성 판단
    
- 시장 상태
    
- Trigger 상황
    
- 승인·거절 사유
    

### 예시 기록:

```
{
  "risk_status": "REJECTED",
  "reason": "Volatility Danger Zone",
  "value": 0.032,
  "timestamp": "2025-01-13 14:23"
}
```

---

# **9.12 리스크 엔진 최종 흐름**

리스크 엔진의 전체적인 흐름은 다음과 같다:

```
1) 전략 신호 수신
2) 주요 위험 지표 계산
3) 시장 레짐 분석
4) 포트폴리오 구조 평가
5) 주문 가능 여부 판별
6) Fail-safe 상태 확인
7) Execution Engine으로 승인/거절 전달
```

이 구조는 QTS가 예측 불가능한 시장에서  
안정적으로 수익을 추구할 수 있도록 설계된 핵심 보호 체계이다.

---

# **PART 10. 포트폴리오 엔진 아키텍처 (Portfolio Engine Architecture)**

Portfolio Engine은 QTS의 **자산 상태를 관리하고**,  
거래 결정이 실제 포트폴리오 구조에 어떤 영향을 주는지 평가하며,  
리스크·전략·실행 엔진과 데이터를 교환하는 **핵심 상태 관리 시스템**이다.

전략이 신호를 만들고, 리스크 엔진이 승인·거절을 결정하더라도,  
실제 거래된 결과는 Portfolio Engine에서 최종적으로 반영된다.

즉, Portfolio Engine은 QTS 시스템의 **State Manager**이자  
운영 전반의 데이터 일관성을 유지하도록 설계된 핵심 모듈이다.

---

# **10.1 포트폴리오 엔진의 역할**

Portfolio Engine이 제공하는 주요 역할은 다음과 같다:

### **(1) 보유 종목·수량·평단·평가금액 관리**

실제 계좌 상태를 엔진 내부에서 정규화하여 관리.

### **(2) 거래 반영 (Fill, Partial Fill, Cancel 등)**

브로커 응답을 구조화하여 포지션 업데이트.

### **(3) 실제 리스크 지표 계산**

전략 계산용 위험이 아닌, “현재 포트폴리오 상태 기반 위험”을 계산.

### **(4) 포트폴리오 재조정(Rebalancing) 기준 정보 제공**

목표 비중과 실제 비중을 비교하여 재조정 필요 여부 판단.

### **(5) Portfolio Snapshot 생성**

백테스트·리포트·리스크 모니터링 등에 활용되는 정규화된 포트폴리오 스냅샷 생성.

### **(6) Audit Logging 기반 상태 이력 기록**

모든 변화는 구조화된 형태로 저장되어 재현성을 보장.

---

# **10.2 포트폴리오 엔진의 구성 요소**

Portfolio Engine은 아래 7개 모듈로 설계된다:

|모듈|설명|
|---|---|
|**1. Position Registry**|현재 포지션 상태 저장|
|**2. Trade Reflector**|거래 결과 반영|
|**3. Exposure Calculator**|비중 계산|
|**4. Equity & NAV Calculator**|계좌 평가금액 관리|
|**5. Rebalancing Assistant**|목표 비중 대비 조정 필요 판별|
|**6. Portfolio Snapshot Generator**|일일/실시간 스냅샷 생성|
|**7. Logging & Versioning Module**|이력 저장 및 버전 관리|

---

# **10.3 Position Registry (포지션 레지스트리)**

Position Registry는 보유 중인 모든 종목의 핵심 정보를 유지한다.

### 저장 항목:

- 종목(symbol)
    
- 보유 수량
    
- 평균 매입가
    
- 현재가
    
- 평가금액
    
- 수익률
    
- 업종 정보
    
- 진입 시점
    

### 특징:

- 스키마 기반 정규화
    
- 오류 방지 Validation Layer 적용
    
- 매수/매도 체결 시 자동 업데이트
    

---

# **10.4 Trade Reflector (거래 반영 모듈)**

브로커 응답(Filled / Partially Filled / Cancelled)을  
정규화된 포지션 데이터로 통합하는 모듈이다.

### 주요 기능:

- 매수 체결 → 수량 증가, 평균가 재계산
    
- 매도 체결 → 수량 감소, 수익률 반영
    
- Partial fill 반영
    
- 거래 취소 로그 기록
    

### 안정성 요소:

- 매수/매도 수량이 음수가 되지 않도록 자동 검증
    
- 체결 오류 발생 시 Fail-safe 전달
    

---

# **10.5 Exposure Calculator (익스포저 계산기)**

Risk Engine과도 공유되는 중요한 기능.

### 계산 항목:

- 종목 비중
    
- 업종 비중
    
- 총 노출 비중 (Total Exposure)
    
- 목표 비중 대비 차이
    

Exposure Calculator는:

- 전략 신호의 현실성 평가
    
- 리스크 승인 기준 제공
    
- 리밸런싱 판단 근거 제공
    

등 여러 엔진에 핵심 데이터를 제공한다.

---

# **10.6 Equity & NAV Calculator**

계좌의 전체 가치를 계산하는 모듈이다.

### 포함되는 항목:

- 현금 잔고
    
- 포지션 평가금액
    
- 총 계좌 평가금액(NAV)
    
- 일일 변동
    
- 누적 손익
    

### 특징:

- History 시트와 연동
    
- 리스크 엔진의 DD 계산에 필수
    
- Execution Engine의 포지션분 수량 계산에도 활용
    

---

# **10.7 Rebalancing Assistant (비중 조정 모듈)**

목표 비중이 있는 전략(예: 가치투자형 전략)을 운영할 때 필수 모듈이다.

### 기능:

- 현재 비중 vs 목표 비중 비교
    
- 차이(Deviation) 계산
    
- 조정 필요 여부 판단
    
- 리밸런싱 주문 후보군 생성
    

### 예:

```
if deviation_pct > REBALANCE_THRESHOLD:
    generate_rebalance_signal()
```

리밸런싱 로직은 전략이 한 번 설정되면 주기적으로 반복 테스트를 수행해  
장기적인 안정성을 제공한다.

---

# **10.8 Portfolio Snapshot Generator**

QTS는 모든 거래일마다 상태를 저장한다.

### 저장되는 내용:

- 보유 종목 리스트
    
- 비중
    
- NAV
    
- 수익률
    
- 변동성
    
- 전략 상태
    
- 리스크 상태
    

Snapshot은 리포트·백테스트·모니터링 등 모든 곳에서 활용되며  
분석 구조의 중추 역할을 한다.

---

# **10.9 Logging & Versioning Module**

포트폴리오의 모든 변화는  
Audit Logging Layer를 통해 저장된다.

### 기록 항목:

- 체결 정보
    
- 포지션 변화
    
- 노출 비중 변화
    
- DD 변화
    
- 리밸런싱 실행
    
- 전략 상태 변화
    

### 버전 관리 개념:

포트폴리오 상태는 단순 값이 아니라  
“시간에 따라 변화하는 기록”이며  
언제든 복원(Fork) 가능하도록 설계된다.

---

# **10.10 포트폴리오 엔진과 다른 엔진의 상호작용**

Portfolio Engine은 QTS의 모든 엔진과 연결된다.

|연동 대상|역할|
|---|---|
|**Strategy Engine**|매수/매도 목표 비중 제공|
|**Risk Engine**|승인/거절 판단에 필요한 실제 비중 제공|
|**Execution Engine**|체결 정보 전달 후 업데이트|
|**Fail-safe Engine**|시스템 위험 시 포지션 조정 또는 유지|
|**Dashboard / Report**|시각화된 포트폴리오 정보 제공|
|**Schema Engine**|포지션 데이터의 스키마 구조 보증|

---

# **10.11 포트폴리오 엔진 최종 흐름**

```
1) 초기 포트폴리오 로드
2) 전략 신호 입력
3) 리스크 엔진 승인 여부 확인
4) 주문 → 브로커 전송
5) 체결 정보 반영 (Trade Reflector)
6) 포지션·비중 업데이트
7) NAV 계산
8) Snapshot 생성
9) 로그 기록
10) 다음 사이클 실행
```

Portfolio Engine은 단순히 수량을 기록하는 수준이 아니라  
QTS 전체의 시간적 흐름을 구성하는 “중앙 상태 관리자”이다.

---

# **PART 11. 데이터 아키텍처 (Data Architecture)**

데이터 아키텍처는 QTS의 모든 엔진을 관통하는 근본 구조이며,  
전략 계산·리스크 평가·실행 엔진·보고서 생성까지  
모든 단계에서 일관성·정확성·재현성을 보장하는 핵심 계층이다.

자동매매 시스템에서 “데이터의 정확성”은 곧 “의사결정의 정확성”이며  
잘못된 데이터는 곧바로 잘못된 손실을 유발한다.

QTS의 데이터 아키텍처는 다음 원칙을 중심으로 설계된다:

- **Schema-driven architecture**
    
- **Validation-first**
    
- **Reproducibility (재현성)**
    
- **Stability (운영 안정성)**
    
- **Separation of concerns**
    

---

# **11.1 데이터 아키텍처 구성 요소**

QTS 데이터 아키텍처는 총 7개의 계층으로 구성된다:

|계층|설명|
|---|---|
|**1. Data Source Layer**|데이터의 원천 (API, 시트, DB)|
|**2. Data Ingestion Layer**|원시 데이터 수집·로드|
|**3. Schema Engine (Auto Schema System)**|스키마 자동 생성·검증|
|**4. Data Validation Layer**|이상치·결측치·타입 검증|
|**5. Data Normalization Layer**|정규화 및 구조 통일|
|**6. Feature Builder Layer**|전략·리스크 계산용 지표 생성|
|**7. Persistence & Logging Layer**|저장·이력·버전 관리|

각 계층은 독립적으로 작동하되,  
상호 연결되며 전체 데이터 흐름을 제어한다.

---

# **11.2 Data Source Layer (데이터 소스)**

QTS가 사용하는 주요 데이터 소스는 다음과 같다:

### **(1) 한국투자증권 OpenAPI**

- 실시간 가격
    
- 과거 시세
    
- 주문/체결 데이터
    
- 계좌 정보
    

### **(2) Google Sheets 기반 운영 데이터**

- Config
    
- Position
    
- Portfolio
    
- History
    
- Risk Monitor
    
- Metrics Dictionary
    

### **(3) 로컬 파일 / 백업 데이터**

- schema.json
    
- 전략 테스트 데이터
    
- 리포트 저장 파일
    

각 소스는 Schema Engine을 통해 일관된 구조로 통일된다.

---

# **11.3 Data Ingestion Layer (데이터 로드)**

Data Ingestion Layer는 원시 데이터를 수집하는 단계이다.

### 특징:

- 비동기 또는 동기화된 방식으로 로드
    
- API 실패 시 재시도
    
- 시트 읽기 오류 시 Fail-safe 전달
    
- 최소 단위별 모듈화 (시세 로더, 체결 로더 등)
    

### 예시 로직:

```
raw_price = fetch_price(symbol)
raw_config = load_sheet("Config")
raw_position = load_sheet("Position")
```

---

# **11.4 Schema Engine (스키마 자동화 엔진)**

QTS만의 독자적 아키텍처 요소이다.

Schema Engine은 다음 기능을 수행한다:

- Google Sheets의 구조를 자동 분석
    
- schema.json 자동 생성
    
- Auto Diff Engine 기반 스키마 비교
    
- 변경 사항 감지
    
- 필수 컬럼 누락 여부 파악
    
- 잘못된 타입 구조 감지
    
- 스키마 오류 시 Fail-safe 발동
    

### 개발 목적:

1. 시트 구조가 변경되더라도 엔진이 깨지지 않도록
    
2. 유지보수 비용 최소화
    
3. 스키마 기반 자동화 아키텍처 구현
    

### 예시:

```
schema_diff = compare_schema(sheet_schema, saved_schema)
if schema_diff.error:
    halt_execution("schema mismatch detected")
```

Schema Engine은 QTS의 안정성에 결정적 기여를 한다.

---

# **11.5 Data Validation Layer (데이터 검증 계층)**

Validation Layer는 원시 데이터를 아래 기준으로 자동 스크리닝한다:

### 검증 항목:

- 결측치(Missing Data)
    
- 이상치(Outliers)
    
- 타입(Type) 오류
    
- 음수/불가능한 값
    
- 비정상 변화율
    
- 수치 논리 검증 (예: PER 음수)
    

### 처리 방식:

- 자동 대체(fallback)
    
- 제거(drop)
    
- 경고(log)
    
- Fail-safe 전달(심각한 경우)
    

### 예시:

```
if price <= 0:
    raise ValidationError("Invalid price")
```

Validation Layer는 “품질이 나쁜 데이터 → 잘못된 의사결정”이라는 문제를 사전에 차단한다.

---

# **11.6 Data Normalization Layer (정규화 계층)**

QTS는 서로 다른 소스 데이터를 받더라도  
정규화된 통일 구조로 변환하여 엔진의 일관성을 유지한다.

### 정규화 작업:

- 컬럼명 일관화
    
- 날짜·시간 포맷 변환
    
- 문자열 정리
    
- 단위 통일
    
- 타입 캐스팅
    

이를 통해 전략 엔진과 리스크 엔진이  
오로지 “정확한 정규화된 데이터”만 사용하도록 강제한다.

---

# **11.7 Feature Builder Layer (전략·리스크 지표 생성)**

Feature Builder는 전략에 필요한 계산 요소를 구성한다.

### 예시 지표:

- 이동평균
    
- 변동성(표준편차)
    
- ATR
    
- 모멘텀
    
- 거래량 변화율
    
- 가치지표(PER, PBR 등)
    
- QTS 고유의 멀티팩터 점수
    

### 특징:

- 전략별 Feature Pipeline 구성
    
- 리스크 엔진과 공유
    
- 단일 종목·전시장 기반 지표 모두 지원
    

---

# **11.8 Persistence & Logging Layer (저장 및 기록)**

데이터는 두 가지 방식으로 저장한다:

### **1) Operational Store (운영 저장소)**

- Position
    
- History
    
- Risk Monitor
    
- Metrics Dictionary
    

### **2) Audit Logging Store (감사 기록 저장소)**

- 스키마 변경
    
- Config 변경
    
- 체결 로그
    
- 리스크 이벤트
    
- Fail-safe Trigger
    

### 목적:

- 문제 원인 추적
    
- 백테스트와 실전 일치성 확보
    
- 시스템 수준의 투명성 제공
    
- 재현성(Reproducibility) 향상
    

---

# **11.9 데이터 아키텍처 전체 흐름**

전체 흐름은 다음 순서로 구성된다:

```
1) Raw Data 수집 (API, 시트, 파일)
2) Schema Engine 검증
3) Validation Layer 검증
4) Normalization Layer 표준화
5) Feature Builder에서 지표 생성
6) Strategy / Risk Engine 사용
7) Execution Engine 실행
8) Portfolio Engine 반영
9) Snapshot / Logging 저장
```

이 구조는 엔진이 안정적이고 예측 가능하게 작동하도록 보장하는  
QTS의 근본적 운영 기반이다.

---

# **PART 12. 전략 엔진 아키텍처 (Strategy Engine Architecture)**

Strategy Engine은 QTS에서 **거래 신호를 생성하는 두뇌(Core Intelligence)** 역할을 수행한다.  
전략은 하나 이상 존재할 수 있으며, 각각은 독립적으로 작동하면서도  
Risk Engine, Portfolio Engine, Execution Engine과의 연동을 통해  
매매 구조화된 신호를 생산한다.

전략 엔진은 단순히 “사는 조건이 되면 매수” 같은 규칙 기반이 아니라  
데이터 기반·멀티팩터 기반·가치 기반·기술 기반 등  
여러 성격의 조건을 조합한 구조로 확장될 수 있도록 설계되어 있다.

QTS는 **전략의 독립성, 확장성, 재현성, 안정성**을 최우선 원칙으로 한다.

---

# **12.1 전략 엔진의 설계 원칙**

전략 엔진은 다음 원칙을 기반으로 설계된다:

### **(1) Isolation – 전략 독립성 보장**

각 전략은 고유한 로직·파라미터·Feature Pipeline을 가지며  
다른 전략의 결과에 영향을 받지 않는다.

### **(2) Reproducibility – 재현 가능한 신호 생성**

같은 입력 데이터를 주면 항상 동일한 결과가 출력되도록 설계한다.

### **(3) Feature-driven Architecture**

전략의 계산은 Feature Builder Layer에서 생성된 지표 기반으로 이루어지며,  
지표 계산과 전략 로직을 분리해 유지보수성을 높인다.

### **(4) Stability & Validation**

전략 신호는 리스크 엔진을 선행적으로 통과해야 하며,  
데이터 오류·스키마 누락·Validation 실패 시 신호를 생성하지 않는다.

### **(5) Extensibility – 확장성**

새로운 전략을 추가할 때 기존 엔진을 수정할 필요가 없도록 설계된다.

---

# **12.2 전략 엔진 구성 요소**

전략 엔진은 다음 7개 서브모듈로 구성된다:

|모듈|설명|
|---|---|
|**1. Strategy Registry**|전략 목록 및 메타 정보 등록|
|**2. Parameter Loader**|전략별 파라미터 로드|
|**3. Feature Pipeline Manager**|지표 입력 관리|
|**4. Signal Generator**|매수/매도 신호 생성|
|**5. Signal Validator**|신호 유효성 검사|
|**6. Multi-Strategy Combiner**|복수 전략 통합|
|**7. Strategy Logging Module**|신호 기록|

이 구조를 통해 QTS는 전략을 플러그인처럼 빠르게 생성·수정·확장할 수 있다.

---

# **12.3 Strategy Registry (전략 등록 시스템)**

Strategy Registry는 시스템이 실행되는 동안  
어떤 전략들이 활성화되어 있는지 관리한다.

### 등록 정보:

- 전략명
    
- 전략 타입 (기술/가치/모멘텀/멀티팩터 등)
    
- 사용 지표 목록
    
- 파라미터 목록
    
- 활성 여부
    
- 전략 우선순위
    

Registry 구조는 다음과 같은 모습이다:

```
{
  "strategies": {
    "GoldenCross": { ... },
    "RSI_Reversal": { ... },
    "ValueFactor": { ... }
  }
}
```

---

# **12.4 Parameter Loader (전략 파라미터 로더)**

전략 파라미터는 Config 시트 또는 YAML 기반에서 로드된다.

### 예:

- GC_FAST_MA
    
- GC_SLOW_MA
    
- RSI_BUY
    
- RSI_SELL
    
- Value 기준 (PER, PBR 임계값 등)
    
- Multi-factor 가중치
    

### 특징:

- Validation Layer를 통과해야 파라미터로 인정
    
- 파라미터 누락 시 fallback 적용
    
- 잘못된 값은 Fail-safe로 전달
    

---

# **12.5 Feature Pipeline Manager**

전략이 사용하는 모든 지표는  
Feature Builder Layer에서 계산된 값을 입력받는다.

### 입력 Feature 예시:

- 가격 기반: MA, 볼린저밴드, ATR
    
- 모멘텀 기반: ROC, RSI
    
- 가치 기반: PER, PBR, ROE
    
- 리스크 기반: 변동성, DD 상태
    
- 시장 기반: KOSPI 레짐, 업종 상대강도
    

Feature Pipeline은 전략마다 독립적으로 구성된다.

---

# **12.6 Signal Generator (신호 생성기)**

전략의 핵심 단계이다.  
Signal Generator는 지표의 관계·조건을 기반으로  
매수/매도 신호를 생성한다.

### 신호 출력 형태:

```
{
  "symbol": "005930",
  "signal": "BUY",
  "confidence": 0.82,
  "parameters": {...}
}
```

### 신호 유형:

- **Binary Signal** (매수/매도/중립)
    
- **Weighted Signal** (신뢰도 기반 점수)
    
- **Directional Signal** (롱/숏 가능 구조)
    

신호 생성 단계에서 전략 고유의 알고리즘이 실행된다.

---

# **12.7 Signal Validator (신호 검증기)**

전략 신호는 리스크 엔진으로 넘어가기 전에  
Signal Validator가 1차 검증한다.

### 검증 항목:

- 데이터 오류 여부
    
- 스키마 이상 여부
    
- 결측치 포함 여부
    
- 논리적 충돌 여부
    
- 가격/거래량 부족 여부
    
- 최근 Fail-safe 여부
    

### 오류 예:

```
if confidence < MIN_CONFIDENCE:
    reject_signal("Low confidence")
```

Signal Validator는 “잘못된 신호가 리스크 엔진으로 넘어가는 것을 방지”한다.

---

# **12.8 Multi-Strategy Combiner**

QTS는 복수 전략을 동시에 운용할 수 있다.  
Combiner는 각 전략이 생성한 신호를 정규화하여 하나의 통합 신호로 만든다.

### 통합 방식 예시:

- **Equal Weight**
    
- **Confidence Weight**
    
- **Performance Weighting**
    
- **Risk-adjusted Weighting**
    

### 예시:

```
final_signal = weighted_average(strategy_signals)
```

---

# **12.9 Strategy Logging Module (전략 로그 저장기)**

전략의 모든 판단 과정은  
Audit Logging Layer를 통해 저장된다.

### 기록 항목:

- 전략명
    
- 입력 지표
    
- 신호 결과
    
- confidence
    
- 파라미터 값
    
- 신호 생성 이유
    

### 목적:

- 전략 성능 분석
    
- 백테스트 일관성 검증
    
- 의사결정 과정 재현성 확보
    

---

# **12.10 전략 엔진 전체 흐름**

전략 엔진은 아래 순서로 작동한다:

```
1) Feature Pipeline 로드
2) 전략별 파라미터 로드
3) 전략별 신호 생성
4) Signal Validator 검증
5) Multi-Strategy Combiner로 통합 신호 생성
6) Risk Engine으로 전송
7) Logging 저장
```

전략 엔진은 QTS 전체 아키텍처에서  
“의사결정을 하는 두뇌”이며,  
나머지 엔진들은 전략의 신호가  
안전하고 정확한 방식으로 실행되도록 돕는다.

---

# **PART 13. 가치 투자(Valuation) 아키텍처**

QTS의 가치 평가(Value Engine)는 단순한 투자 기준을 넘어서  
**정량적 지표 + 정성 분석 요소 + 위험 조정 요소**를 통합하여  
종목의 “실질적 가치”를 평가하는 독립 아키텍처이다.

전략 엔진과 달리 Value Engine은  
**본질 가치(Inner Value)** 와  
**저평가 여부(Undervaluation)** 를 정량화해  
전략의 초기 종목 선정, 필터링, 랭킹 산출에 활용된다.

가치투자 모듈은 다음의 3가지 특성을 가진다:

1. **정확성(Accuracy)**
    
2. **안전성(Safety Through Validation)**
    
3. **일관성(Reproducibility)**
    

---

# **13.1 가치투자 모듈의 목적**

Value Engine의 핵심 목적은 다음과 같다:

### **(1) 상장 기업의 내재가치를 정량적으로 계산**

DCF, 상대가치, Residual Income Model 등을 지원.

### **(2) 재무지표 기반 멀티팩터 스코어 산출**

PER, PBR, ROE, 매출 성장률, 영업이익률, 부채비율 등.

### **(3) 질적 요소 점수화(Qualitative Scoring)**

경영진, 브랜드, 경쟁력, 리스크, 성장성 등.

### **(4) 저평가 여부 판별 및 매수 조건 생성**

안전마진(MOS) 기반 규칙.

### **(5) 전략 엔진과 통합하여 종목 Universe 생성**

전략의 신호 출력을 뒷받침하는 기초 데이터 제공.

---

# **13.2 가치투자 아키텍처 구성 요소**

가치투자 엔진은 크게 **정량(Quant)** + **정성(Qualitative)** + **통합(Integration)** 구조로 이루어진다.

|모듈|설명|
|---|---|
|**1. Financial Metrics Processor**|재무지표 수집·계산|
|**2. Factor Normalization Engine**|지표 정규화 및 등급화|
|**3. Intrinsic Value Calculator**|내재가치 모델(DCF, 상대가치 등)|
|**4. Qualitative Factor Scorer**|경영·브랜드·산업의 질적 평가|
|**5. MOS Calculator**|안전마진 계산|
|**6. Valuation Ranker**|전체 점수 기반 랭킹|
|**7. Validation Layer**|데이터·모델 오류 검증|
|**8. Value Logging Module**|계산 근거 기록|

---

# **13.3 Financial Metrics Processor (재무 지표 처리기)**

기업의 주요 재무 데이터를 입력받아 핵심 지표를 산출한다.

### 입력:

- 재무제표(매출, 영업이익, 순이익, 부채, 자본 등)
    
- 시장 데이터(PER, PBR, 시가총액 등)
    
- 성장률 데이터
    

### 지표 계산 예:

- PER
    
- PBR
    
- PSR
    
- ROE / ROA
    
- FCF
    
- 매출·영업이익 성장률
    
- 부채비율
    

### Validation:

모든 지표는 Validation Layer로 검증되며,  
결측치/비논리적 값(PER 음수 등) 감지 시 자동 보정 또는 제외한다.

---

# **13.4 Factor Normalization Engine (정규화 엔진)**

서로 다른 단위·범위의 지표를  
일관된 스케일로 변환해 비교 가능하게 만든다.

### 기술 요소:

- Z-score
    
- Min-Max Scaling
    
- Quantile Ranking
    
- Sector-relative Standardization(동종 업종 대비 평가)
    

### 목적:

- PER 5와 ROE 15%를 동일 스케일로 비교
    
- 성장주·가치주의 지표 차이를 통일
    

정규화는 멀티팩터 스코어링의 기반이 된다.

---

# **13.5 Intrinsic Value Calculator (내재가치 계산기)**

내재가치는 기업의 실질 가치를 나타내며  
본 엔진은 아래 모델들을 지원한다.

### **(1) DCF (Discounted Cash Flow)**

- FCF 추정
    
- WACC 기반 할인
    
- Terminal Value 계산
    

### **(2) Relative Valuation (상대가치)**

- PER·PBR·PSR 밴드
    
- 업종 내 상대 평가
    

### **(3) Residual Income Model (잔여이익 모델)**

- ROE와 자본 비용 간 차이를 이용한 가치 평가
    

### 결과 예:

```
intrinsic_value = 82,000원
current_price = 61,000원
mos = 25.6%
```

---

# **13.6 Qualitative Factor Scorer (질적 평가 모듈)**

정성적 요소를 점수화하여 Value Score에 포함한다.

### 평가 항목 예시:

- 브랜드 가치
    
- 경영진 신뢰도
    
- 산업 경쟁구조(진입장벽, 과점 등)
    
- 기술력 / 제품 경쟁력
    
- 재무 건전성
    
- 장기 성장성
    

### 점수 범위:

0~5점 또는 가중치 포함식  
(QTS에서는 가중치 적용이 기본값)

### 목적:

재무상 저평가나 고평가가 아닌  
기업 “본질 경쟁력”을 판단해 왜곡 방지.

---

# **13.7 MOS (Margin of Safety) Calculator**

안전마진은 가치투자의 핵심 원칙이다.

### 계산 공식:

```
MOS = (Intrinsic Value – Current Price) / Intrinsic Value
```

### 활용 방식:

- MOS ≥ 30% → 가치 기반 매수 후보
    
- 10% ≤ MOS < 30% → 관심 종목
    
- MOS < 0% → 과대평가
    

수치는 Config에서 조정 가능하다.

---

# **13.8 Valuation Ranker (랭킹 시스템)**

정량 + 정성 + 내재가치를 모두 통합해  
종목의 최종 투자 매력도를 산출한다.

### 최종 점수:

```
Value Score = 
  (정량 지표 가중치 점수) +
  (정성 지표 가중치 점수) +
  (내재가치 점수) +
  (MOS 점수) -
  (위험 점수)
```

### 출력 예:

```
A등급: 강력 매수 후보
B등급: 매수 가능
C등급: 중립
D등급: 주의
F등급: 매수 금지
```

---

# **13.9 Validation Layer**

Value Engine은 숫자 계산 특성상  
데이터 오류에 매우 민감하다.

Validation Layer는 다음을 검증한다:

- PER 음수 여부
    
- FCF 음수일 때 DCF 모델 사용 제한
    
- 업종 데이터 부족 여부
    
- 지표 스케일링 오류
    
- 값 누락 여부
    

오류가 감지되면:

- 계산 제외
    
- 대체값 적용
    
- Fail-safe 조건 전달
    

---

# **13.10 Value Logging Module**

모든 가치 계산 결과는  
Audit Logging Layer에 구조화된 형태로 저장된다.

### 기록 항목:

- 사용 데이터
    
- 계산 방식
    
- 모델 종류
    
- 가정값(할인율, 성장률)
    
- 정량·정성 점수
    
- MOS
    
- 최종 등급
    

### 목적:

- 가치 평가의 재현성 확보
    
- 전략 검증
    
- 장기적 업데이트 기반 구축
    

---

# **13.11 가치투자 엔진 전체 흐름**

```
1) 재무 데이터 로드
2) Financial Metrics Processor 계산
3) 정규화(Scaling)
4) Intrinsic Value 모델 실행
5) 질적 평가 점수 반영
6) MOS 계산
7) Value Score 산출
8) 등급 분류
9) 로그 저장
10) 전략/리스크 엔진으로 전달
```

QTS의 가치투자 엔진은  
단순한 스크리너가 아니라  
**정량·정성·위험·내재가치가 모두 통합된 전문적 가치 평가 시스템**이다.

---

# **PART 14. 백테스트 아키텍처 (Backtest & Simulation Architecture)**

Backtest Engine은 QTS의 전략·가치평가·리스크 모델을  
과거 데이터에 적용하여 성능을 검증하는 핵심 시스템이다.

백테스트의 질은 전략의 신뢰성과 직결되며,  
QTS는 실거래 환경과 최대한 동일한 구조의  
**Realistic Backtesting Framework** 를 지향한다.

백테스트는 단순히 “수익률 계산”이 아니라  
전략의 강점·약점·리스크 구조를 정밀 분석하고  
실전에서 발생 가능한 상황을 시뮬레이션하는 과정이다.

---

# **14.1 백테스트 시스템의 목표**

QTS Backtest Engine의 핵심 목표는 다음과 같다:

### **(1) 전략의 일관성 검증**

과거 다양한 시장 국면에서 전략이 일관된 수익 구조를 보이는지 평가.

### **(2) 리스크 기반 평가**

수익률뿐만 아니라 변동성, DD, Sharpe, MDD까지 종합적으로 분석.

### **(3) 실전 환경 유사성 확보**

슬리피지, 거래 비용, 체결 지연 등을 모두 고려한 현실적 백테스트.

### **(4) 가치 기반 전략 검증**

Value Score 기반 전략도 과거 시장에서 통했는지 확인.

### **(5) 전략 미세 튜닝 근거 확보**

가중치 조정, 파라미터 변경에 대한 논리적 근거 제공.

---

# **14.2 백테스트 아키텍처 구성 요소**

Backtest Engine은 다음 9개 모듈로 구성된다:

|모듈|설명|
|---|---|
|**1. Data Loader**|과거 데이터 로딩|
|**2. Preprocessing Engine**|정규화, 결측치 처리|
|**3. Simulation Clock**|일자별·시간별 시뮬레이션|
|**4. Strategy Simulator**|전략 신호 재현|
|**5. Risk Simulator**|리스크 기준 적용|
|**6. Execution Simulator**|주문·체결 시뮬레이션|
|**7. Portfolio Simulator**|포트폴리오 업데이트|
|**8. Performance Analyzer**|성능 지표 분석|
|**9. Backtest Logging Module**|결과 기록|

각 모듈은 실거래 엔진에서 사용하는 로직과  
동일한 구조를 그대로 적용하도록 설계된다.

---

# **14.3 Data Loader (데이터 로더)**

과거 데이터를 아래 기준으로 로드한다:

### 로드 범위:

- 일봉, 분봉, 체결 기반 데이터
    
- 재무 데이터
    
- 가치투자 지표
    
- 업종 데이터
    
- 시장 레짐 데이터
    

### 기능:

- CSV / API / DB 등 다양한 소스 지원
    
- 스키마 검증 후 정규화
    
- 구간별 누락 데이터 자동 처리
    

---

# **14.4 Preprocessing Engine (전처리)**

전략·리스크·가치 기반 모델이  
실전과 동일한 입력값을 받도록 구성한다.

### 작업 내용:

- 결측치 처리
    
- 이상치 교정
    
- 정규화
    
- 날짜/시간 정렬
    
- Feature Builder 적용
    

### 목적:

실거래 구조와 동일한 환경을 만들어  
전략 로직이 왜곡되지 않도록 보장.

---

# **14.5 Simulation Clock (시뮬레이션 시계)**

시뮬레이션은 다양한 시간 단위를 지원한다:

- 일봉 단위 (일별 신호 발생)
    
- 분봉 단위 (세밀한 테스트 가능)
    
- 틱 기반(Level 2 데이터는 선택적)
    

### 기능:

- 특정 기간 선택
    
- 특정 섹터/종목만 선택
    
- 시장 위기 구간만 테스트 가능
    

---

# **14.6 Strategy Simulator**

실전 Strategy Engine과 동일한 로직을 그대로 사용한다.

### 과정:

1. Feature Pipeline 생성
    
2. 전략 신호 생성
    
3. Signal Validator 통과
    
4. Multi-strategy Combiner 적용
    

### 목적:

실전 전략과 동일한 결과가 나오도록 재현성을 보장.

---

# **14.7 Risk Simulator**

Risk Engine의 모든 규칙이 동일하게 적용된다:

- Exposure 제한
    
- 변동성 기준
    
- DD 기준
    
- 시장 레짐 필터
    
- 포트폴리오 집중도
    
- Fail-safe 조건
    

Risk Simulator는 전략 신호의 품질을 평가하며  
실전과 동일한 필터 역할을 수행한다.

---

# **14.8 Execution Simulator**

QTS Execution Engine의 동작을 백테스트에서도 재현한다.

### 시뮬레이션 포함 요소:

- 슬리피지
    
- 체결 지연
    
- 거래 비용
    
- 재시도 로직
    
- 주문 필터
    

### 목적:

“백테스트는 좋았는데 실전은 다르네”라는 오류를 원천적으로 차단.

---

# **14.9 Portfolio Simulator**

Portfolio Engine의 실제 동작을 그대로 반영한다.

### 기능:

- 포지션 업데이트
    
- 비중 계산
    
- NAV 계산
    
- Snapshot 생성
    

### 특징:

실전 포트폴리오 엔진과 동일한 스키마 구조 유지.

---

# **14.10 Performance Analyzer (성과 분석기)**

Backtest Engine의 최종 출력은 “성과 분석”이다.

### 평가 지표:

- CAGR
    
- MDD
    
- Sharpe Ratio
    
- Win Rate
    
- Volatility
    
- Calmar Ratio
    
- Profit Factor
    
- Rolling Return
    
- Drawdown 기간 분석
    

### 가치 기반 분석 추가:

- Value Score 상위 종목만 포함 시 성과
    
- MOS 높은 종목군의 성과
    
- 저평가 구간 진입 후 수익률
    

QTS에서는 수익률만으로 전략을 평가하지 않고  
리스크 대비 성과를 중심으로 평가한다.

---

# **14.11 Backtest Logging Module**

모든 백테스트 결과는  
구조화된 로그 파일(JSON 등)로 저장된다.

### 기록 항목:

- 전략 파라미터
    
- 리스크 기준
    
- Value Score 기반 필터
    
- 주문·체결 내역
    
- 포트폴리오 변화
    
- 성과 지표
    
- 이벤트(DD 위험, Fail-safe 발생 등)
    

### 목적:

- 백테스트의 재현성 보장
    
- 전략 최적화 근거 확보
    
- 향후 강화학습·AI 기반 모델에 활용 가능
    

---

# **14.12 백테스트 전체 흐름**

```
1) 데이터 로드
2) 전처리 및 정규화
3) Feature Builder 계산
4) 전략 신호 생성
5) Risk Simulator 필터링
6) Execution Simulator 주문·체결 시뮬레이션
7) Portfolio Simulator 포지션 생성
8) Snapshot 저장
9) 성과 분석
10) 로그 저장
```

이 전체 과정은 실전 엔진과 최대한 동일한 구조로 설계되어  
백테스트 결과가 실전 성능을 정확히 반영하도록 한다.

---

# **PART 15. 리포트 & 대시보드 아키텍처 (Reporting & Dashboard Architecture)**

리포트 및 대시보드 시스템은 QTS의 모든 엔진(전략·가치·리스크·포트폴리오·실행·백테스트)의  
결과물을 **시각화·요약·구조화하여 사용자에게 전달하는 모듈**이다.

QTS는 단순한 데이터를 나열하는 방식이 아니라,  
실시간 상태와 의사결정 가능 정보를 제공하는  
**인터랙티브 운영 통제 시스템(Operation Control System)** 을 목표로 한다.

리포트 & 대시보드는 다음의 목적을 가진다:

- 전략 성능·리스크·포트폴리오 상태를 즉시 파악
    
- Fail-safe·경고·이벤트를 실시간 모니터링
    
- 거래 히스토리 및 스냅샷 기반 추세 분석
    
- 자동화 시스템 운영의 투명성 강화
    

---

# **15.1 리포트 & 대시보드의 역할**

보고·시각화 시스템은 다음 6가지 역할을 수행한다:

### **(1) 의사결정 보조 (Decision Support)**

수익률, DD, 노출 비중 등 핵심 지표를 한눈에 제공.

### **(2) 리스크 모니터링 (Risk Awareness)**

시장 위험, 변동성, 포트폴리오 집중도 실시간 확인.

### **(3) 전략 상태 추적 (Strategy Intelligence)**

전략별 신호·성과·실패 원인 추적 가능.

### **(4) Fail-safe 및 운영 이벤트 기록**

이상 상황 감지 및 즉시 피드백.

### **(5) 거래 분석 (Execution Analytics)**

체결 성공률, 슬리피지 패턴, 주문 충실도 확인.

### **(6) 가치 기반 종목 분석 (Valuation Insights)**

Value Score, MOS, 등급 기반 투자 판단 제공.

---

# **15.2 대시보드 아키텍처 구성 요소**

리포트 및 대시보드는 총 8개 모듈로 구성된다:

|모듈|설명|
|---|---|
|**1. Summary Dashboard**|모든 핵심 지표 요약|
|**2. Portfolio Dashboard**|비중, 종목 상태, 수익률|
|**3. Risk Dashboard**|변동성, DD, 시장 레짐|
|**4. Strategy Dashboard**|전략 신호·성과 추적|
|**5. Execution Dashboard**|주문·체결 분석|
|**6. Valuation Dashboard**|가치평가 점수·등급 분석|
|**7. History & Snapshot Viewer**|일별 스냅샷 조회|
|**8. Event & Fail-safe Monitor**|경고·이벤트 실시간 표시|

이 8개 모듈은 QTS의 모든 엔진이 생산하는 정보를  
사용자에게 구조화된 형태로 제공한다.

---

# **15.3 Summary Dashboard**

전체 시스템 상태를 한눈에 보여주는 요약 대시보드.

### 주요 제공 항목:

- 누적 수익률
    
- 일일 수익률
    
- 총 자산(NAV)
    
- 현재 노출 비중
    
- 전략별 신호 요약
    
- 리스크 상태(정상/경고/위험)
    
- Fail-safe 상태
    
- 시장 레짐 상태
    

Summary Dashboard는  
“아침에 시스템 켜고 가장 먼저 확인하는 기본 화면”에 해당한다.

---

# **15.4 Portfolio Dashboard**

Portfolio Engine의 상태를 시각적으로 표현한다.

### 제공 항목:

- 종목별 비중
    
- 업종별 비중
    
- 수익률 / 평가금액
    
- 매수·매도 히스토리
    
- 보유 기간
    
- 익절/손절 구간 표시
    

### 시각화 요소:

- 원형 차트 (비중)
    
- 바 차트 (수익률)
    
- 라인 차트 (NAV 변화)
    

---

# **15.5 Risk Dashboard**

리스크 엔진이 계산한 모든 위험 지표를 보여준다.

### 포함 정보:

- 변동성(20D)
    
- DD 상태
    
- 시장 레짐 (강세/약세/변동성 확대 구간)
    
- Exposure
    
- 업종 쏠림도
    
- Kill Switch 임계 수준
    

### 목적:

리스크 요인을 빠르게 파악하고  
전략 실행의 안정성을 고려한 판단 가능.

---

# **15.6 Strategy Dashboard**

각 전략의 성능과 신호를 분석한다.

### 제공 정보:

- 전략별 신호 로그
    
- 신호 발생 빈도
    
- 장세별 성과
    
- 전략별 Sharpe / CAGR
    
- 전략 파라미터 상태
    
- 전략 실패·거절 사유 (리스크 엔진이 거절한 이력 포함)
    

이 화면은 전략의 효율성과 정확도를 장기적으로 분석하는 데 활용된다.

---

# **15.7 Execution Dashboard**

Execution Engine의 주문·체결 품질을 분석한다.

### 제공 정보:

- 주문 성공률
    
- 슬리피지 평균
    
- 체결까지 걸린 시간
    
- 주문 재시도 횟수
    
- Fail-safe 호출 원인
    
- API 응답 패턴 (속도/오류)
    

이 모듈은 자동매매 시스템의 “운영 품질”을 개선하는 데 핵심적이다.

---

# **15.8 Valuation Dashboard**

Value Engine의 출력(정량·정성·내재가치·MOS)을 시각화한다.

### 포함 요소:

- Value Score 상위 10
    
- MOS 기반 저평가 랭킹
    
- 등급 분포(A~F)
    
- 정성 점수 분석
    
- 가치/가격 괴리율
    

### 목적:

- 어떤 종목이 “근본적으로 좋은 기업인지”
    
- “가격이 싸게 형성되었는지”  
    한눈에 판단할 수 있는 구조 제공.
    

---

# **15.9 History & Snapshot Viewer**

Portfolio Engine과 Backtest Engine이 생성한 Snapshot을 조회하는 모듈.

### 기능:

- 날짜별 포트폴리오 상태 조회
    
- NAV 변화 추적
    
- 리스크 수준 변화
    
- 매매 이벤트 조회
    
- 종목별 수익률 히스토리
    

기록 중심(Log-Centric) 시스템을 위해  
QTS는 모든 데이터를 누적 저장한다.

---

# **15.10 Event & Fail-safe Monitor**

Fail-safe Engine과 리스크 엔진에서 발생한 모든 이벤트를  
실시간으로 모니터링하는 모듈이다.

### 제공 정보:

- Fail-safe 발동 기록
    
- DD 경고/위험
    
- 스키마 변경 탐지
    
- Config 오류
    
- Broker API 장애
    
- 포트폴리오 위험 구조 변화
    

Fail-safe Monitor는  
“시스템이 정상적으로 작동하고 있는가?”  
를 판단하는 가장 중요한 지표이다.

---

# **15.11 리포트 생성 구조 (Reporting Engine)**

QTS는 자동 리포트 생성 기능을 제공한다.

### 생성 가능한 리포트:

- 일간 리포트 (Daily Report)
    
- 주간 요약 리포트
    
- 전략별 성능 리포트
    
- 리스크 분석 리포트
    
- 가치 기반 종목 분석 리포트
    

### 리포트 구성:

- 핵심지표 요약
    
- 수익률 및 성과
    
- 위험지표
    
- 매수·매도 이벤트
    
- 전략 성능
    
- 향후 모니터링 포인트
    

리포트는 PDF, Markdown, JSON 등 다양한 포맷을 지원한다.

---

# **15.12 리포트 & 대시보드 전체 흐름**

```
1) 모든 엔진에서 실시간 데이터 수집
2) Summary Metrics 계산
3) Portfolio / Risk / Strategy / Execution / Value 데이터 업데이트
4) Snapshot 저장
5) Dashboard 시각화
6) Report Generator에서 출력물 생성
7) 이벤트 및 Fail-safe 모니터링
```

---

# **PART 16. 운영 관리 체계 (Operations Management System)**

운영 관리 체계는 QTS의 지속적 운용을 가능하게 하는  
**모니터링, 유지보수, 업데이트, 품질보증(Ops-QA)** 을 총괄하는 시스템이다.

QTS가 단순 전략 엔진이나 포트폴리오 툴 수준에 머무르지 않고  
**운영 가능한 자동매매 시스템**이 되기 위해서는  
운영 관리 체계의 확립이 필수적이다.

본 시스템은 다음과 같은 목적을 가진다:

- 운영 중 발생하는 모든 이벤트를 감지·기록
    
- 리스크 및 Fail-safe Layer와 통합된 안정성 관리
    
- Config/Schema 변경의 추적 및 버전 관리
    
- 로그 기반 품질관리 및 오류 재현 가능성 확보
    
- 시스템 업데이트 주기 및 가이드라인 확립
    
- 백테스트/리포트/전략/가치 평가 엔진과의 일관성 유지
    

운영 관리 체계는 QTS 전체를 감싸는 “운영형 안정화 구조”다.

---

# **16.1 운영 관리 체계의 6대 역할**

운영 체계는 다음 6개 핵심 역할로 구성된다.

### **1) 모니터링 (Monitoring)**

- 실시간 전략 신호
    
- 포트폴리오 비중 변화
    
- 체결 결과
    
- API 응답 상태
    
- 리스크 지표
    
- 이벤트 및 Fail-safe 신호
    

### **2) 로그 수집 및 아카이빙 (Logging & Archiving)**

- 모든 엔진의 입력·출력·이벤트 저장
    
- Config/Schema 변경 기록
    
- 전략 오류·실패 로그
    
- 실행 속도·성능 데이터
    

### **3) 품질 보증 (Ops-QA)**

- 오류 재현성 확보
    
- 전략 결과 검증
    
- 비정상 신호 필터링
    
- 리스크 거절 이벤트 검사
    

### **4) 업데이트/배포 관리 (Update & Release Management)**

- Config 버전 관리
    
- Schema 버전 관리
    
- 전략 파라미터 버전 기록
    
- 리포트 구조 버전 관리
    

### **5) 유지보수 가이드 (Maintenance Guidelines)**

- 일일 점검 루틴
    
- 주간 리밸런싱 업무
    
- 월간 시스템 점검
    
- 연간 전략 업데이트
    

### **6) 복구/비상 대응 체계 (Recovery & Emergency Response)**

- Fail-safe 후 재가동 절차
    
- API 장애 대응 프로토콜
    
- 긴급 정지(Kill Switch) 후 복구 절차
    
- 데이터 손상 대비 백업/복구 체계
    

---

# **16.2 운영 보고 체계 (Operations Reporting Layer)**

운영 관리 체계는 제3의 보고 계층을 가진다.

### 운영 보고의 3대 종류:

#### **1) Daily Ops Report (일간 운영 리포트)**

- 오늘 발생한 전략 신호 요약
    
- 체결·미체결 분석
    
- 리스크 지표 변화
    
- Fail-safe 이벤트 로그
    
- 포트폴리오 변동 현황
    

#### **2) Weekly Ops Review (주간 운영 리뷰)**

- 전략별 수익률
    
- 포트폴리오 Performance
    
- 리스크 누적 상태
    
- 슬리피지·체결 품질
    
- 이탈 이벤트(Outliers)
    

#### **3) Monthly Ops QA Review (월간 품질 점검)**

- API 응답 성능
    
- 리스크 거절 이벤트 합산
    
- Config/Schema 변경 이력
    
- 전략 성능 비교
    
- 가치 엔진 점수 변화
    
- 백업·로그 무결성 검사
    

---

# **16.3 일일 운영 점검 루틴 (Daily Ops Checklist)**

QTS 운영자는 매일 다음을 점검해야 한다.

1. **API 정상 연결 여부**
    
2. **Price Feed 정상 갱신 여부**
    
3. **전략별 오류 여부**
    
4. **리스크 엔진 경고/위험 발생 여부**
    
5. **Fail-safe 발동 여부**
    
6. **거래 거절, 주문 실패율 증가 여부**
    
7. **포트폴리오 변동률 급등/급락 여부**
    
8. **로그 파일 정상 저장 여부**
    
9. **스냅샷 저장 여부 확인**
    
10. **Config 값 변경 여부 자동 감지 확인**
    

---

# **16.4 주간 운영 점검 루틴 (Weekly Ops Checklist)**

1. 전략 성능 비교 (CAGR, MDD, Hit Ratio)
    
2. 포트폴리오 집중도 점검
    
3. 변동성 변화 패턴
    
4. 종목별 리스크 기여도
    
5. 주문 성공률 및 슬리피지
    
6. 백업 파일 무결성 체크
    
7. Value Engine 결과 변화(점수 재산정 필요 여부)
    

---

# **16.5 월간 운영 점검 루틴 (Monthly Ops Checklist)**

1. 전략 가중치 조정 필요 여부
    
2. 리밸런싱 정책 유지/변경
    
3. Kill Switch 발생 여부 및 사유 재검토
    
4. Config / Schema 변경 이력 리뷰
    
5. 로그 파일 압축·보관
    
6. API 응답 지연 패턴 분석
    
7. Portfolio Engine 재성능 테스트
    
8. 시장 레짐 변화 영향 분석
    

---

# **16.6 운영 리스크 관리 체계 (Operational Risk Management)**

운영 관리 체계에는 별도로  
**시스템 리스크**를 감지하기 위한 Layer가 존재한다.

### 감지할 운영 리스크 종류:

- API 응답 불능
    
- 속도 저하
    
- 가격 이상치 도착
    
- 체결 데이터 불일치
    
- Config 변경 오류
    
- Schema mismatch
    
- DB 쓰기 실패
    
- 로그 파일 손상
    
- 메모리 누수
    
- 무한루프 감지
    

### 자동 대응 시나리오:

|상황|시스템 대응|필요 시 운영자 행동|
|---|---|---|
|API 지연|재시도 → Fail-safe 발동|브로커 변경 또는 시간 제한 조정|
|가격 이상치|해당 tick 무시|데이터 소스 재확인|
|Config 오류|기본값 fallback|Config 검토 후 수정|
|Schema mismatch|자동 복원 시도|스키마 버전 수동 교정|
|메모리 증가|엔진 자동 재시작|필요 시 서버 리소스 확장|

---

# **16.7 Config / Schema 변경 관리 체계**

운영 단계에서는 Config와 Schema 변경이 필수적으로 발생한다.  
QTS는 이를 안정적으로 감당하기 위해 “Versioned Change Management” 체계를 갖춘다.

### 관리 원칙:

#### **1) 모든 변경은 기록(Log) 필수**

- 변경 전/후 KEY, VALUE 기록
    
- 변경자 / 변경 시간 기록
    

#### **2) 스키마 변경은 항상 버전 증가**

- schema_version = X.Y.Z 구조 유지
    
- 구조 변경은 Major
    
- 필드 추가는 Minor
    
- 주석/설명 변경은 Patch
    

#### **3) Config 변경은 자동 알림**

- Real-time diff 감지
    
- 위험 영역 변경 시 경고
    
- fallback 값 존재해야 함
    

#### **4) 자동 오염 방지(Fallback / Validation)**

- 잘못된 값 입력 시 엔진 자동 거절
    
- Validation 규칙 통합
    
- Critical field는 fail-safe trigger 가능
    

---

# **16.8 백업 및 데이터 아카이빙 정책**

QTS는 기록 기반 아키텍처이므로 데이터 보존 정책이 중요하다.

|항목|보존 기간|비고|
|---|---|---|
|Daily Snapshot|1년|NAV/포트/리스크|
|전략 신호 로그|2년|재현성 확보|
|거래 로그|5년|세무 추적 가능|
|Config 변경 로그|영구|레거시 추적|
|Schema 변경 로그|영구|시스템 무결성|
|리포트 파일|3년|PDF/Markdown|

---

# **16.9 운영 실패 시 대응 절차 (Incident Response Protocol)**

### Step 1. 문제 탐지

Fail-safe 또는 Warning 발생

### Step 2. 자동 초기 진단

- 원인 추정
    
- 오류 유형 분류
    
- 회복 가능 여부 판단
    

### Step 3. 자동 대응 실행

- 재시도
    
- fallback 값 사용
    
- 엔진 분리 재시작
    

### Step 4. 운영자 알림

- Slack/Webhook/Email
    

### Step 5. 문제 해결

- Config/Schema 수정
    
- API 교체 또는 대기
    

### Step 6. 사후 분석 리포트 생성

- 재발 방지 대책 기록
    
- 변경 관리 체계 반영
    

---

# **PART 17. 리포팅 시스템 (Reporting System Architecture)**

QTS Reporting System은 운영, 전략 점검, 가치평가, 백테스트 결과 등을  
구조화된 형태로 자동 생성하는 종합 리포트 엔진이다.

리포트 엔진은 QTS 전체 운영의 “가시성(Observability)”을 구축하고  
전략의 개선, 리스크 통제, 가치평가 업데이트에 활용되는 핵심 인프라다.

QTS의 리포팅은 크게 다음의 목적을 가진다:

1. 전략 및 포트폴리오의 **현재 상태 진단**
    
2. 리스크 변화 모니터링
    
3. 자동매매 엔진의 **품질 유지 관리(QA)**
    
4. 가치 기반 투자 기준 업데이트
    
5. 오류 재현 및 원인 분석
    
6. 백테스트 비교 분석 및 최적화
    

리포트는 단순 요약 문서가 아니라  
**QTS 의사결정의 근거**가 되는 정량·정성 혼합 데이터 분석 체계이다.

---

# **17.1 리포트 엔진의 5대 구성 요소**

리포트 엔진은 다음 5개의 모듈로 구성된다:

|모듈|역할|
|---|---|
|**1. Reporting Data Collector**|각 엔진에서 필요한 데이터 수집|
|**2. Metrics Formatter**|분석 지표 계산 및 구조화|
|**3. Visualization Layer (옵션)**|차트·테이블 자동 생성|
|**4. Report Compiler**|Markdown/PDF 형태로 컴파일|
|**5. Delivery Module**|Slack/Webhook/Email 전달|

각 모듈은 독립적으로 동작하지만  
조합되어 Daily·Weekly·Monthly 리포트를 생성한다.

---

# **17.2 리포트 종류 (Report Types)**

QTS는 총 6종의 리포트를 자동 생성하도록 설계한다:

## **1) Daily Market & Ops Report (일간 시장·운영 리포트)**

운영 단계에서 가장 많이 참조되는 리포트.

### 포함 내용:

- 시장 지표 요약 (KOSPI/KOSDAQ/섹터 흐름)
    
- 변동성 지표(VIX, 시장 변동성 등)
    
- 포트폴리오 NAV 및 일간 수익률
    
- 오늘의 전략 신호 요약
    
- 체결률·슬리피지 기록
    
- 리스크 경고/Fail-safe 이벤트
    
- 종목별 리스크 기여도 변화
    
- Significant Events (비정상 급등락 등)
    

---

## **2) Weekly Strategy & Portfolio Report (주간 전략·포트폴리오 리포트)**

주간 단위 전략 검증과 구조 점검을 위한 리포트.

### 포함 내용:

- 전략별 주간 수익률
    
- MDD 변화
    
- 포트폴리오 비중 구조 변화
    
- Value Score 기반 종목군 성과
    
- 리스크 엔진 거절 이벤트 요약
    
- 체결 품질 분석(Spread, Slippage)
    
- 전략 상호 비교 (Multi-strategy Flow)
    

---

## **3) Monthly System QA Report (월간 시스템 품질 점검 리포트)**

QTS 유지보수 핵심 문서.

### 포함 내용:

- API 응답 성공/실패 로그
    
- 브로커 지연 시간
    
- 엔진 오류 로그
    
- Config/Schema 변경 이력
    
- Fail-safe 발동 내역
    
- 로깅 시스템 정상 여부
    
- Value Engine 재평가 보고
    
- 시장 레짐 변화 분석
    

---

## **4) Value Investment Report (가치평가 리포트)**

QTS 가치투자 모듈에서 자동 생성.

### 포함 내용:

- 내재가치 점수(Value Score) 정렬
    
- Safety Margin Top 리스트
    
- 저평가 후보군 변화
    
- 재무 트렌드(ROE/성장률/부채비율)
    
- 질적 점수(브랜드, 경쟁력 등)
    
- 최종 종합투자등급(A/B/C/D/F) 변화
    
- 신규 매수·보유·매도 추천군
    

---

## **5) Strategy Performance Report (전략 성능 분석 리포트)**

백테스트/실전 데이터 모두 반영.

### 포함 내용:

- CAGR / MDD / PF / Sharpe
    
- Rolling Return 분석
    
- Drawdown 기간·빈도
    
- 거래 횟수 및 히트 비율
    
- 전략별 Risk-adjusted Score
    
- 시장국면별 전략 성과 비교
    

---

## **6) Backtest Comparison Report (백테스트 비교 리포트)**

전략 버전 간 비교를 위한 전문 분석 리포트.

### 포함 내용:

- 버전별 성능 차이
    
- 파라미터 변경 효과 분석
    
- 리스크 기여도 변화
    
- Value Score 기반 전략 성과 변화
    
- 최종 채택 전략 도출
    

---

# **17.3 리포트 생성 프로세스**

```
1) Raw Data 수집  
2) 지표 정제 및 Score 계산  
3) 리스크 필터 통과 여부 반영  
4) 전략/포트폴리오 상태 분석  
5) 테이블/차트 자동 생성  
6) Markdown → PDF 변환  
7) Slack/Email/Webhook 전달  
```

각 단계는 개별 엔진에서 발생한 로그와  
리스크·스키마·전략 데이터를 통합하여 분석한다.

---

# **17.4 리포트 템플릿 구조 (Report Template Structure)**

리포트는 Markdown 형식의 템플릿 구조로 생성되며  
아래 항목이 기본 Skeleton이다.

```
# {{REPORT_TITLE}}
Generated: {{DATE}}

## 1. Overview
- Summary of Market / Strategy / Portfolio

## 2. Portfolio Performance
- NAV / Return / Volatility / MDD

## 3. Strategy Signals
- Buy / Sell / Hold Activity
- Valid / Invalid Signal Ratio

## 4. Risk Analysis
- Exposure
- Volatility
- Fail-safe Events
- Warning/Danger Level Count

## 5. Value Analysis (옵션)
- Value Score
- Intrinsic Value Gap
- MoS Candidates

## 6. Event Logs
- 주요 시스템/시장 이벤트

## 7. Appendix
- Raw tables
- Parameter list
- Schema/Config info
```

---

# **17.5 보고 자동화 아키텍처**

리포트 자동화는 다음 구조를 따른다:

### **1) Trigger Layer**

- Daily → Market open 전 또는 마감 후 자동 실행
    
- Weekly → 금요일 마감 후
    
- Monthly → 매월 첫 거래일 오전
    

### **2) Pipeline Layer**

- Data Collector
    
- Metrics Calculator
    
- Table/Chart Generator
    
- Report Compiler
    

### **3) Export Layer**

- Markdown
    
- PDF
    
- HTML(선택)
    

### **4) Delivery Layer**

- Slack
    
- Email
    
- Discord
    
- Local 저장
    

---

# **17.6 리포트 품질 기준 (Report Quality Standards)**

QTS 리포트는 다음 기준을 충족해야 한다:

1. **재현성** – 같은 조건이면 동일한 결과 산출
    
2. **추적 가능성** – 모든 지표는 원본 로그 참조 가능
    
3. **구조화** – 템플릿 기반, 항목 고정
    
4. **신뢰성** – 결측치·이상치 제거 후 정제된 데이터 사용
    
5. **투명성** – 파라미터, 가정값 모두 리포트에 표기 가능
    
6. **대조 가능성** – 버전 간 리포트 비교 용이
    

---

# **17.7 리포트와 Fail-safe/Logging 시스템 연동**

리포팅 엔진은 단순 보고 기능뿐 아니라  
시스템 안정성 모듈과 깊게 통합되어 있다.

### 자동 포함되는 항목:

- Fail-safe 발생 로그
    
- Kill-switch 발동 여부
    
- Risk Reject 이벤트
    
- Config 변경 감지
    
- Schema mismatch 발생 여부
    
- API 지연 및 Timeouts 로그
    

> 리포트는 단순 성과 분석이 아닌 **시스템 상태의 전반적 진단 문서** 역할을 수행한다.

---

# **17.8 향후 확장성**

QTS 리포팅 시스템은 다음 기능까지 확장 가능하도록 설계돼 있다:

- AI 기반 요약(Executive Summary Generator)
    
- PDF 자동 배포
    
- Slack 인터랙티브 리포트
    
- Voice Summary(요약 음성 제공)
    
- 브라우저 기반 Dashboard
    

---

# **PART 18. 백테스트 기반 최적화 (Backtest Optimization Framework)**

QTS에서 전략은 한 번 개발하면 끝나는 것이 아니라  
주기적으로 백테스트를 통해 검증·미세조정·재평가해야 한다.

이 과정은 단순한 성과 비교가 아니라  
**전략의 생명주기를 관리하는 핵심 운영 프로세스**이며  
QTS의 품질 유지(QA)와 직결된다.

최적화 프레임워크는 다음의 질문에 답하기 위해 존재한다:

- 전략이 지금 시장에서도 여전히 유효한가?
    
- 어떤 파라미터가 성과에 가장 큰 영향을 주는가?
    
- 어떤 지표는 유지하고 어떤 지표는 제거해야 하는가?
    
- Value Engine·Strategy Engine·Risk Engine 사이의 균형은 적절한가?
    
- 현재 전략 버전이 과최적화된 것은 아닌가?
    

이를 체계적으로 수행하기 위해 QTS는  
전략 최적화를 **3단계·8요소 Framework**로 정의한다.

---

# **18.1 최적화 3단계 구조 (Three-Stage Optimization Process)**

최적화는 아래 3단계로 구성된다.

---

## **Stage 1. Sensitivity Analysis (민감도 분석)**

전략 파라미터가 성과에 어떤 영향을 미치는지 정량적으로 분석한다.

### 목적:

- 핵심 영향을 주는 변수 식별
    
- 불필요한 파라미터 제거
    
- 구조적 불안정 구간(성능 급락 지점) 확인
    

### 분석 요소:

- Fast MA / Slow MA 변화에 따른 성과
    
- Value Score 가중치 변화
    
- MOS 기준 변화 영향
    
- 리스크 제한값 변화 영향
    
- 거래 비용 변화에 따른 민감도
    

---

## **Stage 2. Parameter Optimization (파라미터 최적화)**

민감도 분석을 기반으로 실제 파라미터 후보군을 선정하고  
백테스트로 최적 조합을 결정한다.

### 고려 요소:

- 성과 지표(CAGR, MDD, Sharpe, PF)
    
- 거래 횟수 및 슬리피지 증가 여부
    
- 캠브리지 룰(CAGR/MDD)이 균형을 이루는 지점
    
- Value Engine 점수 안정성
    
- 리스크 엔진과의 충돌 최소화
    

### 산출물:

- 최적 파라미터 세트(parameter_set_vX.X.X.json)
    
- 근거 요약 리포트
    
- 성능 비교 그래프
    

---

## **Stage 3. Robustness Verification (견고성 검증)**

최적화된 파라미터가 **특정 구간에만 맞춰진 과최적화(overfitting)**가 아닌지,  
다른 환경에서도 일관되게 작동하는지 검증한다.

### 검증 방식:

1. Out-of-sample Test
    

- 최적화에 사용되지 않은 기간으로 검증
    

2. Walk-forward Test
    

- 기간 분할 기반 반복 검증
    

3. Market Regime Stress Test
    

- 상승 장세
    
- 급락 장세
    
- 변동성 장세
    
- 횡보 장세
    

4. Random Subsampling
    

- 랜덤 구간 선택 테스트
    

### 목표:

전략의 “환경 의존성”을 줄이고  
진짜 실전에서도 재현 가능한 구조 확보.

---

# **18.2 최적화 8요소 (Eight Optimization Elements)**

QTS는 최적화 시 아래 **8가지 구조 요소**를 기준으로 분석 및 조정한다.

---

## **1) 성과(Performance)**

- CAGR
    
- Rolling Return
    
- Hit Ratio
    
- Profit Factor
    

---

## **2) 리스크(Risk)**

- MDD
    
- Volatility
    
- Exposure
    
- DD 발생 빈도
    

---

## **3) 일관성(Consistency)**

- 월별 수익 분포
    
- 승률 패턴
    
- 전략 로직의 단순성 유지
    

---

## **4) 체결 품질(Execution Quality)**

- 슬리피지
    
- 체결률
    
- 주문 실패율
    
- 브로커 응답 지연
    

---

## **5) 비용 구조(Cost Structure)**

- 거래 비용 증가에 따른 민감도
    
- 회전율 증가 리스크
    
- 스프레드 비용 반영
    

---

## **6) 가치 기반 요소(Value Factors)**

- MOS 기준 변화 영향
    
- Value Score 정렬 결과 변동성
    
- 재무 트렌드 지속성 분석
    

---

## **7) 시장 레짐 적합도(Market Regime Fit)**

- 특정 국면에서의 과도한 성능 집중 여부
    
- 방향성 전략/역추세 전략 간 균형
    
- 리스크 엔진과 상충되는 구간 식별
    

---

## **8) 전략 구조 안정성(Structural Stability)**

- 파라미터 변화에 따라 극단적 변동이 있는지
    
- 전략의 베이스 로직은 유지되는지
    
- overfitting 패턴 제거
    

---

# **18.3 최적화 프로세스 자동화**

QTS는 최적화를 자동화할 수 있도록 아래 레이어 구조를 갖는다.

### **1) Optimization Task Manager**

- 최적화 작업 스케줄링
    
- Parameter grid 자동 생성
    
- 테스트 우선순위 관리
    

### **2) Batch Backtester**

- 여러 파라미터 조합을 병렬 백테스트
    
- 성능 요약표 자동 생성
    

### **3) Optimization Report Generator**

- 최적 후보군 정렬
    
- 민감도 차트 생성
    
- 전략 버전 비교 리포트 자동 생성
    

### **4) Parameter Validator**

- 실전 사용 가능 여부 검증
    
- 리스크 기준 충족 여부 확인
    

---

# **18.4 전략 버전 관리 (Strategy Versioning System)**

최적화의 결과는 반드시 버전 관리로 추적된다.

버전 규칙은 다음과 같다:

### **Major (X.0.0)**

전략 구조 변경 발생 시

- 예: Value Score 계산식 변경
    
- 예: 전략 신호 생성 로직 일부 수정
    

### **Minor (0.X.0)**

파라미터 변경

- 예: Fast MA 20→15
    
- 예: MOS 기준 30%→25%
    

### **Patch (0.0.X)**

반응성 개선·버그 수정

- 예: 체결 오류 처리 개선
    
- 예: 슬리피지 모델 개선
    

각 버전은 아래 파일로 저장한다:

- strategy_config_vX.X.X.json
    
- parameter_set_vX.X.X.json
    
- optimization_report_vX.X.X.md
    

---

# **18.5 최적화 후 전략 채택(Selection)**

최적화 과정에서 도출된 결과는 무조건 채택되는 것이 아니라  
다음 기준을 모두 충족해야 한다.

### 필수 채택 조건:

1. Out-of-sample에서도 성능 유지
    
2. 리스크 기준(Exposure/MDD) 충족
    
3. 시장 국면 분포가 균형적
    
4. 체결 품질 악화 없음
    
5. Value Score 기반 전략과 충돌 없음
    
6. 리포팅 시스템의 QA 기준 충족
    

### 선택적 조건:

- 단순화된 파라미터 구조
    
- 연산량 감소
    
- 유지보수 용이성
    

---

# **18.6 최적화 주기 (Optimization Cycle)**

최적화는 아래 주기로 수행한다:

### **단기 (Monthly)**

- 파라미터 확인
    
- 민감도 변화 분석
    
- 설계 오류 탐지
    

### **중기 (Quarterly)**

- 전략 성능 재평가
    
- Value Score 정렬 안정성 점검
    
- 리스크 구조 변화 분석
    

### **장기 (Yearly)**

- 전략 구조 재검토
    
- 시장 구조 변화 대응
    
- 신호 로직 개선 여부 판단
    

---

# **18.7 Value Engine 기반 최적화 연동**

QTS는 전통적인 기술 전략만 최적화하는 것이 아니라  
**가치 기반 전략 최적화**도 지원한다.

최적화 대상:

- Value Score 가중치
    
- 내재가치 공식 파라미터
    
- Safety Margin 기준
    
- 질적 평가 점수 가중치
    
- 성장률 가정 변화 영향
    

검증 요소:

- 모멘텀·가치 결합 전략의 Robustness
    
- 성장률 가정 민감도
    
- ROE/PBR 비선형 효과
    
- Value Score 상위 종목군의 consistency
    

---

# **18.8 최적화 결과 리포팅 체계**

최적화 완료 후 자동 생성되는 문서:

1. Optimization Summary
    
2. Parameter Comparison Table
    
3. Sensitivity Maps
    
4. Robustness Charts
    
5. Backtest Result Tables
    
6. 최종 채택 여부 및 사유
    

이 문서는 **PART 17의 리포팅 엔진**과 동일한 템플릿 아키텍처를 사용한다.

---

# **PART 19. 종합 등급화 시스템 (Grading System Architecture)**

QTS의 등급화 시스템은  
재무 지표, 가치평가, 전략 신호, 리스크 지표를 통합하여  
각 종목에 대해 **행동(Action) 기반 의사결정 등급**을 부여하는 구조이다.

이 등급화 시스템은 단순한 점수의 합산이 아니라  
QTS의 모든 엔진이 산출한 결과를 하나의 의사결정 모델로 통합하는  
**최종 Decision Layer**이다.

등급화는 다음 질문에 답한다:

- 지금 이 종목을 **매수해야 하는가?**
    
- 지금 이 종목을 **보유해야 하는가?**
    
- 지금 이 종목을 **매도해야 하는가?**
    
- 지금 이 종목은 **관망**해야 하는가?
    
- 이 종목은 **투자 금지**해야 하는가?
    

---

# **19.1 등급화 시스템의 목적**

등급화 시스템의 목적은 크게 4가지다:

### **1) 비정형 데이터를 정량화**

경영진, 경쟁력, 브랜드 가치 같은 정성 요소도  
점수화하여 투자 판단에 통합한다.

### **2) 전략·가치·리스크의 균형적 통합**

Value Score만 보거나  
Momentum/기술적 신호만 보거나  
리스크만 보는 것은 편향을 만든다.

등급화 시스템은 이 3요소의 균형을 자동 조정한다.

### **3) 실전 매수/매도 행동(Action)으로 연결**

단순히 “좋다/나쁘다”가 아니라  
“무엇을 해야 하는가?”로 구체화한다.

### **4) 전략 자동화와 운영 안정성 확보**

QTS의 자동매매 엔진이  
등급을 기반으로 포트폴리오를 업데이트하도록 설계된다.

---

# **19.2 등급 시스템의 구조**

QTS의 등급 시스템은 다음 3층 구조다:

```
1) 점수화 Score Layer  
2) 가중치 Weight Layer  
3) 의사결정 Decision Layer (A/B/C/D/F)
```

이 구조는 전략·가치 모두 확장 가능하도록 설계됐다.

---

# **19.3 Score Layer (점수화 레이어)**

점수화는 다음 4개 Score로 구성된다:

---

## **1) Value Score (가치 점수)**

구성 요소:

- 내재가치 대비 할인율(MoS)
    
- PBR 정상범위 점수
    
- PER 정상범위 점수
    
- ROE 품질 점수
    
- 재무 구조 안정성
    
- 성장성 점수
    
- 질적 평가 점수(경영진·브랜드·네트워크)
    

출력 범위: **0~100점**

---

## **2) Momentum Score (모멘텀·전략 점수)**

구성 요소:

- Trend 방향성
    
- MA 구조
    
- 기술적 지표(모멘텀·밴드·RSI·MACD 등)
    
- 시그널 신뢰도
    
- Multi-strategy 합성 점수
    

출력 범위: **0~100점**

---

## **3) Risk Score (리스크 점수)**

구성 요소:

- 변동성
    
- Exposure
    
- DD Risk
    
- 종목 위험 기여도
    
- 레짐 위험도(시장 국면 위험)
    

출력 범위: **0~100점**  
점수가 낮을수록 안전함(리스크 점수는 반전 스케일링 적용 가능)

---

## **4) Portfolio Fit Score (포트폴리오 적합도)**

구성 요소:

- 섹터 분산 기여도
    
- 종목 상관도
    
- 기존 포트folio 위험 대비 기여도
    
- 보유 종목과의 균형성
    

출력 범위: **0~100점**

---

# **19.4 Weight Layer (가중치 레이어)**

종합 등급은 단순 합산이 아니라  
다음 가중치 기반 Weighting으로 계산한다:

```
Final Score =
  Value Score * w_value +
  Momentum Score * w_momentum +
  Risk Score * w_risk +
  Portfolio Fit * w_portfit
```

기본 가중치 예시(v1 기준):

|Score|Weight|
|---|---|
|Value Score|0.40|
|Momentum Score|0.25|
|Risk Score|0.20|
|Portfolio Fit Score|0.15|

가중치는 시장 상황에 따라 변경될 수 있으며  
Config 시트에서 versioned 관리가 가능하다.

---

# **19.5 Decision Layer (A/B/C/D/F 등급)**

최종 등급은 다음과 같이 5단계로 구분한다.

---

## **A등급 — 강력 매수(Buy Strong)**

조건:

- Final Score ≥ 80
    
- Value Score ≥ 70
    
- Risk Score ≥ 50
    
- 포트폴리오 분산 기여도 양호
    

행동:

- 신규 매수 즉시 허용
    
- 목표 비중까지 강화(Scale In)
    

---

## **B등급 — 매수(Buy)**

조건:

- Final Score ≥ 65
    
- Value Score ≥ 55
    
- Risk Score ≥ 40
    

행동:

- 부분 매수 가능
    
- 급등 구간에서는 모니터링 후 분할 매수
    

---

## **C등급 — 보유(Hold)**

조건:

- Final Score ≥ 50
    
- Value Score ≥ 40
    

행동:

- 매수는 금지
    
- 기존 보유분은 유지
    
- 리스크 상승 여부 모니터링
    

---

## **D등급 — 매도 경고(Reduce/Sell)**

조건:

- Final Score < 50
    
- Risk Score 낮음(위험 증가)
    
- Value Score 약화
    

행동:

- 점진적 비중 축소
    
- 포트폴리오 리스크 재정렬
    

---

## **F등급 — 매도(Sell / Ban)**

조건:

- Final Score < 35
    
- 리스크 임계치 초과
    
- Value Score 심각한 악화
    
- 질적 평가 F항목 포함(부도 위험 등)
    

행동:

- 즉시 매도
    
- 투자 금지 리스트(Banned List)에 등록 가능
    

---

# **19.6 Multi-Decision Matrix (다중 조건 의사결정 매트릭스)**

최종 등급은 Score 하나가 아니라  
아래 Matrix를 기반으로 의사결정을 내린다.

|Value|Momentum|Risk|Final|Action|
|---|---|---|---|---|
|High|High|Stable|A|강한 매수|
|High|Low|Stable|B|모아가기|
|Low|High|High Risk|C|제한적 보유|
|High|Low|High Risk|D|절반 축소|
|Low|Low|High Risk|F|전량 매도|

이 매트릭스는 Config 시트에서 확장 가능하다.

---

# **19.7 등급화 시스템과 QTS 엔진 연동**

등급화 시스템은 단순 분석 도구가 아니라  
QTS 전체 엔진의 최종 의사결정 레이어다.

### **연동 방식:**

1. Value Engine → Value Score 전달
    
2. Strategy Engine → Momentum Score 전달
    
3. Risk Engine → Risk Score 전달
    
4. Portfolio Engine → Fit Score 전달
    
5. Grading Engine → Final Grade 산출
    
6. Execution Engine → Grade 기반 매수·매도 실행
    

---

# **19.8 등급 기반 자동 트레이딩 로직**

등급에 따른 자동 매수/매도 트리거:

|Grade|자동 실행|
|---|---|
|A|목표 비중까지 즉시 매수|
|B|분할 매수|
|C|보유 유지|
|D|부분 매도(25~50%)|
|F|전량 매도|

Fail-safe 연동 조건:

- 리스크 급등 시 A/B라도 매수 금지
    
- 시장 레짐 위험 시 매도 우선
    
- 금지 업종/종목은 무조건 F 처리
    

---

# **19.9 등급 버전 관리 및 로깅**

모든 등급 변경은 기록된다:

- 등급 변경 사유
    
- Value/Momentum/Risk Score 변화
    
- 변경 시간
    
- Config/Schema 버전
    

ex)

```
2025-01-10 10:32  
Ticker: AAPL  
Grade: B → A  
Reason: Value Score +12 상승, MoS 확대
```

---

# **19.10 향후 확장성**

향후 등급 시스템은 다음 기능으로 확장 가능하다:

- AI 기반 등급 보정 모델
    
- 강화학습 기반 비중 조절
    
- 섹터별 다른 등급 기준
    
- 시장 국면별 등급 가중치 자동 전환
    
- 전략별 등급 기준 자동 학습
    

---

# **PART 20. 백테스트 범위 설정 (Backtest Range & Scenario Design)**

백테스트는 전략 검증의 출발점이며,  
전략의 생존력·일관성·리스크 구조를 평가하는 핵심 과정이다.

QTS에서는 백테스트를 단순 기간 테스트가 아닌  
**복합적 환경 분석 도구**로 정의한다.

즉, 전략이 다양한 환경에서도 살아남는지 검증하는 것이 목적이다.

따라서 “일반 범위 설정”과 “극한 상황 시나리오”를 모두 포함해야 한다.

---

# **20.1 백테스트 범위 설계의 핵심 원칙**

QTS의 백테스트 범위는 아래 세 가지 원칙을 따른다:

### **1) Data-Complete (데이터 완전성)**

누락·오염 데이터가 없는 기간을 우선 선정  
→ 데이터 품질 보장

### **2) Market-Diverse (시장 다양성)**

상승/하락/횡보/초고변동성 등  
시장의 다양한 국면을 반드시 포함  
→ 전략의 환경 적응성 검증

### **3) Stress-Included (스트레스 국면 포함)**

극한 상황에서도 전략이 붕괴되지 않는지 검증  
→ 전략의 생존력 확인

---

# **20.2 기본 백테스트 기간 설정**

QTS는 최소 3개의 기간을 사용해 백테스트를 수행한다.

---

## **1) Long-term Range (10년 이상)**

목적:

- 전략의 구조적 안정성 검증
    
- Value/Momentum 통합 전략의 장기적 성과 평가
    
- 시장 구조 변화에도 견딜 수 있는지 확인
    

적용 기간 예시:

- 2013–현재
    
- 글로벌 금융 이벤트 포함
    

---

## **2) Mid-term Range (5년)**

목적:

- 최근 시장 구조에 대한 적합성 검증
    
- 금리 사이클 변동 반영
    

적용 기간 예시:

- 2018–현재
    

---

## **3) Short-term Range (2년)**

목적:

- 최신 시장 데이터 기반 실전 성능 예상
    
- 전략 버전 업데이트 후 즉각적 검증
    

적용 기간 예시:

- 최근 24개월
    

---

# **20.3 시장 국면 기반 범위 구성 (Market Regime Coverage)**

백테스트 범위에는 반드시 시장의 주요 국면이 포함되어야 한다.

다음 시장 구조(Regime)를 포함한 기간 지정이 필수:

|Regime|설명|
|---|---|
|Bull Market|장기 상승 국면|
|Bear Market|장기 하락 국면|
|Sideways|박스권 장기 횡보|
|High Volatility|급격한 변동성 증가|
|Low Volatility|안정적 변동성 구간|
|Crisis Event|금융위기·팬데믹 등|

예:

- 2020 COVID 폭락 및 회복
    
- 2022 금리 급등 구간
    
- 2018 미중 무역전쟁 변동성 증가
    

---

# **20.4 백테스트 시뮬레이션 조건**

백테스트는 단순한 가격 데이터 시뮬레이션이 아니라  
실거래와 동일한 조건을 적용해야 한다.

필수 적용 조건:

### **1) 거래 비용 포함**

- 수수료
    
- 스프레드
    
- 세금
    

### **2) 슬리피지 반영**

- 최소 고정 슬리피지
    
- 변동성 기반 슬리피지
    

### **3) 체결 조건 실거래 기반**

- 지정가 체결 실패 반영
    
- Best-Bid/Ask 기반 시뮬레이션
    
- 체결 지연 시간 포함
    

### **4) 리스크 엔진 적용**

- Exposure 제한
    
- DD 경고/차단 레벨
    
- 시장 레짐 기반 매수 금지 조건
    

### **5) 포트폴리오 구조 반영**

- 보유 종목 수 제한
    
- 비중 조절 규칙
    
- 재매수/재평가 시점
    

---

# **20.5 가치투자 백테스트 범위**

QTS Value Engine 백테스트는 가격 기반 전략과 다르다.  
아래 조건이 반드시 포함되어야 한다.

### **1) 재무 데이터 시차(Time Lag) 반영**

실제 발표일 이후에만 데이터 사용  
→ 미래 데이터 누수 방지

### **2) 재무 데이터 품질 필터**

- 결측치 제거
    
- 이상치 보정
    
- 재무구조 급변 기업 별도 표시
    

### **3) Value Score 기반 필터**

- Top 20%
    
- Bottom 20%
    
- Score band별 수익률 비교
    

### **4) MOS 기반 전략 검증**

- MOS ≥ 30% 기준군
    
- MOS < 30% 대비 성과 차이
    

### **5) 질적 평가 요소 적용 여부**

경영진/브랜드/경쟁력 점수 포함 vs 미포함 비교

---

# **20.6 전략 결합 테스트 (Hybrid Strategy Test)**

QTS는 Value + Momentum + Risk 기반 하이브리드 전략을 지원한다.

따라서 백테스트는 다음 조합을 반드시 테스트해야 한다:

|조합|설명|
|---|---|
|Value only|전통적 가치 전략|
|Momentum only|가격 기반 전략|
|Value + Momentum|하이브리드|
|Value + Momentum + Risk|QTS 표준 전략|
|Value + Momentum + Risk + Portfolio Fit|완전형|

---

# **20.7 스트레스 테스트 (Stress Test)**

극단적 상황에서도 전략이 붕괴되지 않는지 테스트해야 한다.

### 적용 시나리오 예시:

---

## **1) Price Shock Scenario**

- 하루 -10% 갭다운
    
- 연속 3일 급락
    
- 단일 섹터 폭락
    

---

## **2) Volatility Explosion**

- 20일 변동성 4배 증가
    
- VIX 급등 구간 포함
    

---

## **3) Liquidity Crash**

- 거래량 70% 감소
    
- 스프레드 확대
    
- 체결 실패 비율 증가
    

---

## **4) Risk-Regime Lock**

- 시장 위험 레짐에서 매수 금지
    
- 포트폴리오 리밸런싱 차단
    

---

## **5) Fail-safe Trigger Test**

- DD 위험 구간 진입
    
- API 지연 연속 발생  
    → 전략 자동 중지 여부 검증
    

---

# **20.8 백테스트 결과 저장 구조**

모든 백테스트 결과는 아래 구조로 저장된다:

```
/backtests/
    /v1.0.0/
        backtest_summary.json
        performance_table.csv
        drawdown_chart.png
        rolling_return.png
        value_score_distribution.png
        stress_test_report.md
        parameter_snapshot.json
        config_version.txt
        schema_version.txt
```

이 구조는 재현성·추적성·비교 가능성을 보장한다.

---

# **20.9 백테스트 성공 기준 (Success Criteria)**

전략이 다음 조건을 충족해야 채택 가능하다:

### **핵심 Success 조건**

- CAGR > 시장 벤치마크
    
- MDD ≤ 전략의 목표 리스크 수준
    
- Sharpe ≥ 0.8
    
- Rolling Return 안정성
    
- 시장 레짐 변화에도 성능 유지
    

### **가치 기반 Success 조건**

- Value Score 상위 구간과의 일관성
    
- MOS 확대 구간에서 초과수익 존재
    
- 질적 평가 반영 시 성과 개선
    

### **리스크 기반 Success 조건**

- DD 이벤트 분산
    
- 종목 위험 기여도 적정
    
- Exposure 유지
    

---

# **20.10 백테스트 기준과 운영 프로세스 통합**

백테스트는 PART 21에서 다룰  
**최종 실전 전략 채택 프로세스**와 연결된다:

- Backtest → Performance Analysis
    
- Performance → Optimization
    
- Optimization → Strategy Selection
    
- Selection → Trading Engine 적용
    

---

# **PART 21. 백테스트 실행 및 성능 검증 (Backtest Execution & Performance Validation)**

백테스트 실행 및 성능 검증은  
전략이 실전에서 살아남을 수 있는지를 평가하는  
QTS 전체 아키텍처의 중추적인 단계다.

정확한 백테스트는 전략의 설계, 가치평가, 리스크 구조, 시장 적응성을  
모두 반영해야 하며,  
QTS는 단순한 수익률 계산이 아니라  
“전략의 실전 생존력”을 검증하는 데 초점을 둔다.

---

# **21.1 백테스트 실행 프로세스 개요**

QTS의 Backtest Engine은 아래 순서로 실행된다:

```
1) Historical Data Load
2) Data Preprocessing & Cleaning
3) Feature Builder 적용
4) Strategy Signal Generation
5) Risk Filter & Exposure Validation
6) Execution Simulation (Slippage, Fill Rate)
7) Portfolio Update & NAV Calculation
8) Snapshot 저장
9) Performance Analyzer 수행
10) 결과 Export & Logging
```

이 모든 과정은 실전 거래 엔진의 구조를 그대로 모사하도록 설계된다.

---

# **21.2 시뮬레이션 환경 재현 (Realism)**

QTS는 실전과 동일한 환경을 재현하기 위해 다음 기능을 포함한다:

### **1) 실시간 체결 논리 반영**

- 지정가·시장가 체결 방식
    
- Best Bid/Ask 기반 Fill 논리
    
- 체결 실패율 반영
    
- 재시도 로직 고려
    

### **2) 슬리피지 모델**

- 고정 슬리피지
    
- 변동성 기반 가변 슬리피지
    
- 거래량 부족 시 체결 시간 지연
    

### **3) 거래 비용 반영**

- 매수·매도별 수수료
    
- 시장별/업종별 비용 차이
    
- 세금 포함
    

### **4) 리스크 엔진과 동기화**

- Risk Reject 이벤트
    
- DD 기반 매수 금지
    
- 노출(Exposure) 제한
    
- 시장 위험 레짐 감지
    

### **5) 포트폴리오 구조 유지**

- 비중 조절 규칙
    
- 재진입 지연(Cooldown)
    
- 보유 종목 수 관리
    

---

# **21.3 성능 분석 주요 지표**

QTS Performance Analyzer는  
전략 성능을 아래 기준으로 평가한다.

## **1) Return Metrics**

- CAGR
    
- Total Return
    
- Monthly Return
    
- Rolling Return (12M, 36M)
    
- Up-Capture / Down-Capture
    

---

## **2) Risk Metrics**

- Max Drawdown(MDD)
    
- Volatility(σ)
    
- Value at Risk(VaR)
    
- Conditional VaR
    
- Drawdown Recovery Time
    
- Exposure Stability
    

---

## **3) Risk-adjusted Metrics**

- Sharpe Ratio
    
- Sortino Ratio
    
- Calmar Ratio
    
- Omega Ratio
    

---

## **4) Trade Quality Metrics**

- Win Rate
    
- Profit Factor
    
- Avg Win / Avg Loss
    
- Payoff Ratio
    
- Holding Period Distribution
    

---

## **5) Execution Metrics**

- Slippage per trade
    
- Fill Rate
    
- Failed Order Ratio
    
- Execution Delay
    

---

## **6) Value Engine Metrics**

- Value Score Group 성과 비교
    
- MOS ≥ 기준군 vs. 미충족군 성과
    
- 질적 평가 반영 여부에 따른 성과 차이
    

---

# **21.4 성능 해석(Interpretation) 기준**

전략의 백테스트 성능을 해석할 때  
QTS는 다음 기준을 적용한다:

---

## **1) Consistency (일관성)**

- 월별 수익률이 일정한 패턴을 유지하는가
    
- 특정 몇 달만 수익이 나고 나머지는 불안정한가
    
- Rolling Return이 지속적으로 양호한가
    

---

## **2) Drawdown Behavior**

- MDD가 너무 크지 않은가
    
- DD가 길게 지속되지는 않는가
    
- DD가 특정 시장국면에서만 발생하는가
    

---

## **3) Risk-adjusted Quality**

Sharpe, Sortino, Calmar이  
전략의 “진짜 품질”을 보여주는 지표다.

Sharpe > 0.8  
Calmar > 0.5  
정도면 우수한 전략으로 판단한다.

---

## **4) Trade Robustness**

- 승률이 약해도 Payoff Ratio가 높으면 우수
    
- 거래 횟수 과도 증가(과거 데이터 과적합 신호)
    
- 슬리피지 증가 시 성능 급락 여부 확인
    

---

## **5) Sensitivity & Stability**

- 파라미터 조금만 바뀌어도 성능이 급락하는지
    
- Value Score 가중치 변화에 민감한지
    
- Risk Engine 조정에 과도하게 반응하는지
    

---

# **21.5 백테스트 실패 조건**

다음 조건이 발생하면 전략은 “Fail” 처리되며  
최적화 또는 구조 재검토가 필요하다.

- Rolling Return이 특정 구간에서 지속적 음수
    
- MDD가 전략 기준 초과
    
- Exposure 규칙 반복 위반
    
- 매수 금지 조건 위반
    
- 슬리피지 모델 적용 시 성능 붕괴
    
- Value Score 상위군 성과와 연동 실패
    
- 시장 레짐 변화에 따라 성능 극단적으로 변함
    
- 수익의 50% 이상이 단 몇 개 이벤트에 집중됨
    
- 과최적화로 판단되는 경우
    

---

# **21.6 백테스트 결과 저장 및 버전 관리**

백테스트 결과는 다음 파일 구조로 저장된다:

```
/backtests/
    /strategy_v1.0.0/
        performance.json
        trade_log.csv
        metrics_summary.md
        rolling_return.png
        drawdown_chart.png
        sensitivity_map.json
        execution_quality.csv
        config_version.txt
        schema_version.txt
```

모든 백테스트는 **Config / Schema / Engine 버전**과 함께 저장되어  
재현성을 100% 보장한다.

---

# **21.7 백테스트 결과 리포트 자동 생성**

PART 17의 Reporting System과 통합하여  
다음 문서가 자동 생성된다:

- Daily Backtest Digest (옵션)
    
- Strategy Backtest Report
    
- Value-Momentum 비교 리포트
    
- Stress Test Report
    
- Rolling Return Stability Report
    
- Execution Quality Summary
    

리포트는 Markdown 기반이며 PDF/HTML로 변환 가능하다.

---

# **21.8 백테스트 검증 이후의 흐름**

백테스트가 완료되면 전략은 다음 단계로 넘어간다:

```
Backtest → Optimization → Strategy Selection → Strategy Versioning → Trading Engine 적용
```

이 흐름은 다음 PART 22 및 PART 23과 연결된다.

---

# **PART 22. 공식 수정 및 미세튜닝 (Formula Refinement & Micro-Optimization)**

PART 22는 QTS에서 전략·가치·리스크 공식을  
**백테스트-분석 결과에 따라 미세 조정하는 절차**를 정의한다.

미세튜닝은 단순히 숫자를 바꾸는 작업이 아니라:

- 왜 조정하는지
    
- 조정 근거가 무엇인지
    
- 조정에 따른 효과가 무엇인지
    
- 리스크는 어떻게 달라지는지
    

이 모든 것을 체계적으로 검증하는 과정이다.

---

# **22.1 공식 미세튜닝의 목적**

공식 수정이 필요한 이유는 다음과 같다:

### **1) 시장 구조 변화 반영**

금리, 변동성, 기업 재무 구조는 시간이 지나면 변한다.

### **2) 전략의 민감도 조절**

특정 지표에 대한 반응이 과한지/약한지 조정한다.

### **3) 리스크 구조 개선**

DD 구간이 특정 시점에 집중되면 원인을 재분석해야 한다.

### **4) Value Engine의 현실성 강화**

성장률, 할인율, MOS 기준이 실제 시장 상황과 맞는지 재평가한다.

### **5) 포트폴리오 균형 확보**

종목 간 위험 기여도가 균형적인지 확인한다.

---

# **22.2 미세튜닝 프로세스 개요**

QTS 공식 수정은 아래 5단계 프로세스로 수행된다:

```
1) Performance Diagnosis (성과 진단)
2) Weakness Identification (약점 식별)
3) Formula Adjustment (공식 조정)
4) Re-testing & Validation (재검증)
5) Versioning & Deployment (버전 관리 및 배포)
```

---

# **22.3 Step 1: Performance Diagnosis (성과 진단)**

백테스트 및 실전 데이터를 기반으로  
다음 항목을 우선 진단한다.

### **1) Value Engine 진단**

- 성장률 가정이 과도한가?
    
- 할인율이 시장보다 높은가?
    
- MoS 기준이 너무 보수적/느슨한가?
    
- 질적 평가 점수가 과도하게 영향을 주는가?
    

### **2) Strategy Engine 진단**

- 매수·매도 신호가 과도하게 빈번한가?
    
- 추세 대응이 지나치게 늦거나 빠른가?
    
- 특정 지표가 성능의 대부분을 결정하는가?
    

### **3) Risk Engine 진단**

- DD가 특정 시점에 집중되는가?
    
- Exposure 상한이 너무 낮거나 높은가?
    
- 레짐 필터가 지나치게 엄격한가?
    

### **4) Portfolio Engine 진단**

- 비중 과집중 문제는 없는가?
    
- 손절 또는 익절 기준이 시장 상황과 맞는가?
    

---

# **22.4 Step 2: Weakness Identification (약점 식별)**

약점 분석은 다음 관점에서 수행된다:

## **1) 구조적 약점 (Structural Weakness)**

- 공식 자체가 시장 구조와 안 맞음
    
- 지표의 민감도 비정상적
    

예:  
MA 기반 전략이 횡보장에서 반복 손절 → 구조적 약점

---

## **2) 환경 의존적 약점 (Environment-Dependent Weakness)**

- 특정 시장 국면에서만 성능 급락
    

예:  
금리 급등기에서 가치 전략의 MoS 기준이 과하게 보수적

---

## **3) 최적화 왜곡 (Overfitting Symptoms)**

- 특정 파라미터가 실제 설명력이 낮는데 성능 향상에만 기여
    
- 시계열 랜덤 구간에서 성능 급락
    

---

## **4) 리스크-보상 불균형 (Risk-Reward Imbalance)**

- CAGR은 높지만 DD가 지나치게 깊음
    
- Sharpe는 양호하지만 PF가 낮음
    

---

# **22.5 Step 3: Formula Adjustment (공식 조정)**

약점을 정확히 식별하면  
아래 방식으로 공식을 조정한다.

---

## **1) Value Engine 공식을 조정할 때**

### 조정 가능한 요소:

- Terminal Growth Rate
    
- Discount Rate
    
- MoS 기준
    
- ROE/FCF 가중치
    
- 부채비율 Penalty
    
- 질적 점수 가중치
    

### 예시:

MoS 기준 30% → 25% (완화)  
할인율 11% → 10% (시장 금리 반영)

---

## **2) Strategy Engine 공식을 조정할 때**

### 조정 가능 요소:

- MA 길이
    
- RSI 구간
    
- 밴드 폭
    
- 추세 강도 필터
    
- 진입·청산 조건
    
- 신호 무효화 조건
    

### 예시:

Fast MA 20 → 15  
RSI Buy 30 → 25

---

## **3) Risk Engine 공식을 조정할 때**

### 조정 가능 요소:

- Exposure 상한
    
- 변동성 경고 레벨
    
- DD Warning/Danger
    
- Market Regime 필터 조건
    

예:  
DD 위험 기준 5% → 4% (보수적 강화)

---

## **4) Portfolio Engine 공식을 조정할 때**

### 조정 가능 요소:

- 종목당 최대 비중
    
- 최소 비중
    
- Rebalancing 주기
    
- 부분 익절 규칙
    

---

# **22.6 Step 4: Re-testing & Validation (재검증)**

공식을 수정하면 반드시 아래 검증을 수행한다.

### **1) Full Backtest 재실행**

모든 구간과 레짐에서 성능 변화 비교

### **2) 민감도(Sensitivity) 재분석**

조정한 파라미터가 과도하게 영향을 주지 않는지 확인

### **3) Stress Test 재검증**

극단 상황에서 전략 붕괴 여부 확인

### **4) 실전 체결 모델 적용**

슬리피지·거래 비용 반영하여 실전 성능 예측

### **5) Value Engine과 충돌 여부 점검**

가치 전략과 기술 전략이 상충하지 않도록 조정

---

# **22.7 Step 5: Versioning & Deployment (버전 관리 및 배포)**

최종 확인을 거친 공식 수정은  
다음 규칙에 따라 버전이 기록된다.

---

## **버전 관리 규칙**

### Major (X.0.0)

- 공식 구조 자체 변경
    
- Value Score 구성 변경
    
- Momentum Logic 일부 교체
    

### Minor (0.X.0)

- 파라미터 레벨 조정
    
- MoS 기준 변화
    
- Risk threshold 변경
    

### Patch (0.0.X)

- 예외 처리 강화
    
- 슬리피지 공식 개선
    
- 체결 오류 처리 강화
    

---

## **배포 절차**

```
1) 변경 내용 정리 (Changelog 생성)
2) 수정된 공식/파라미터를 Config로 반영
3) Schema 영향 여부 검증
4) 엔진 적용 전 Dry-run 수행
5) 실전 적용
6) Logging Layer에 기록
7) Reporting 엔진이 자동으로 반영
```

---

# **22.8 공식 미세튜닝의 성공 기준**

다음 조건을 충족해야 최종 채택된다:

- 성능 개선 또는 변동성 감소
    
- DD 안정화
    
- Rolling Return 개선
    
- Value Score 변화와 일관성
    
- Risk Engine과 충돌 없음
    
- Overfitting 증상 완화
    
- 복잡도 증가 없이 단순성 유지
    

---

# **22.9 공식 미세튜닝 실패 조건**

다음 중 하나라도 발생하면 재조정이 필요하다:

- 특정 시장 구간에서 성능 급락
    
- DD 증가
    
- 리스크 관리 규칙 위반
    
- 체결 품질 악화
    
- Value Engine과 충돌
    
- 불안정한 민감도 결과
    

---

# **PART 23. 가치투자 기준 v1.0 문서화 (Value Investing Standard v1.0)**

본 문서는 QTS에서 사용되는  
**가치투자(Value Investing) 의사결정 기준의 공식 버전(v1.0)**을 정의한다.

이 기준은 아래 6개 구성 요소로 이루어진다:

1. 투자 철학
    
2. 데이터 기준
    
3. 핵심 재무/가치 지표
    
4. 내재가치 평가 모델
    
5. 질적 평가(Qualitative Scoring)
    
6. 매수/보유/매도 기준 및 행동 규칙
    

이 문서는 QTS Value Engine의 최상위 표준 문서로 활용되며,  
향후 모든 업데이트는 **v1.1, v2.0** 등 버전으로 관리된다.

---

# **23.1 가치투자 철학(Value Philosophy)**

QTS 가치투자의 핵심 철학은 다음 네 가지다.

### **1) “가치(Value)는 결국 가격(Price)을 이긴다.”**

단기적으로 시장은 비효율적일 수 있으나  
장기적으로 가격은 내재가치에 회귀한다.

### **2) “안전마진(Margin of Safety)은 필수이다.”**

내재가치 대비 충분한 할인율이 확보된 종목만 매수한다.

### **3) “질적 가치(Qualitative Value)는 정량보다 우선한다.”**

브랜드, 경영진 능력, 네트워크, 사업 경쟁력 등  
정성 요소는 장기 Return의 핵심 요인이다.

### **4) “가치와 모멘텀의 결합은 더 강력하다.”**

가치가 좋은 종목이라도  
수급/추세가 하락 중이면 진입 타이밍을 조절해야 한다.  
따라서 QTS는 Value + Momentum 하이브리드 구조를 채택한다.

---

# **23.2 데이터 기준 (Data Standards)**

가치 평가에 사용되는 데이터는 아래 조건을 충족해야 한다:

### **1) 재무 데이터 기준**

- 최소 최근 **5년치 재무제표**
    
- 발표일 기준 시차(Time Lag) 반영
    
- 결측치 제거 또는 대체 기준 명확화
    
- 이상치(Outlier) Winsorizing 또는 제거
    
- IFRS 기반 데이터 우선 사용
    

### **2) 가격/시장 데이터 기준**

- 일봉 기준 필수
    
- 시가총액, 거래량 포함
    
- 섹터/업종 코드 정규화
    

### **3) 데이터 품질 기준**

- 동일 회계항목 간 Naming 일관성
    
- 분기·연간 재무제표 병합 규칙 유지
    
- 재무 데이터 Update Log 기록
    

### **4) 재무 안정성 필터**

- 감사의견 ‘한정/부적정/의견거절’ 기업 제외
    
- 상장폐지 위험군 제외
    

---

# **23.3 핵심 재무/가치 지표 (Core Value Metrics)**

QTS Value Engine은 다음 지표를 기준으로 Score를 계산한다.

---

## **A. 수익성 지표 (Profitability)**

|지표|기준|
|---|---|
|ROE|10% 이상 가점 / 5% 이하 감점|
|ROA|업종 평균 이상 가점|
|영업이익률|10% 이상 가점|
|순이익률|안정성 판단|

---

## **B. 성장성 지표 (Growth)**

|지표|기준|
|---|---|
|매출 성장률|5년 평균 > 5% 가점|
|EPS 성장률|일관적 증가 시 가점|
|FCF 성장률|플러스로 전환 시 가점|

---

## **C. 안정성 지표 (Stability)**

|지표|기준|
|---|---|
|부채비율|150% 이상 감점|
|유동비율|100% 미만 감점|
|이자보상배율|3배 이하 감점|

---

## **D. 밸류에이션 지표 (Valuation)**

|지표|기준|
|---|---|
|PER|업종 평균 대비 70% 이하 가점|
|PBR|1.0 이하 가점 / 0.3 이하 금지|
|PSR|업종 구조에 따라 보조지표|
|EV/EBITDA|8 이하 가점|

---

## **E. 현금흐름 지표 (Cash Flow)**

|지표|기준|
|---|---|
|FCF|최근 3년 연속 플러스 가점|
|CFO > 순이익|영업이익의 질 판단|
|CapEx 안정성|변동성 낮을수록 가점|

---

# **23.4 내재가치 평가 모델 (Intrinsic Value Model)**

QTS v1.0은 아래 3개의 내재가치 모델을 지원하며  
최종 Value Score는 이들의 가중 평균 또는 합성 형태로 구성된다.

---

## **1) DCF(Discounted Cash Flow)**

### 구성:

- FCF Forecast (3~5년)
    
- Terminal Growth
    
- Discount Rate (WACC 또는 기준가중)
    

### 입력 가정 예시:

- 성장률: 3~7%
    
- 할인율: 9~11%
    
- Terminal Growth: 1~2%
    
- 안전마진 기준: 최소 20~30%
    

---

## **2) Residual Income Model (RIM)**

### 구성:

- 자기자본
    
- 기대수익률
    
- 초과수익(Earnings – Required Return)
    

특히 ROE 기반 기업 평가에서 강력함.

---

## **3) 상대가치(Relative Valuation)**

### 구성:

- PER Band
    
- PBR Band
    
- EV/EBITDA Band
    

시장의 “정상 밴드” 대비 현재 위치로  
저평가 여부 판단.

---

# **23.5 Value Score 계산 구조**

Value Score는 다음 구성 요소의 가중 합산으로 계산한다:

```
Value Score = 
  Profitability * 0.25 +
  Growth * 0.20 +
  Stability * 0.15 +
  Cashflow * 0.15 +
  Valuation * 0.15 +
  Intrinsic Value Gap * 0.10
```

각 항목은 **0~100 점**으로 정규화된다.

---

# **23.6 질적 평가(Qualitative Scoring)**

정량적 지표가 포착하지 못하는 기업의 기업가치 요소를  
정성적 Score로 평가한다.

### 평가 항목 (각 0~5점)

|항목|설명|
|---|---|
|경영진 역량|리더십, 실행력|
|브랜드 가치|시장 인지도, 충성도|
|경쟁우위|비용우위/기술우위/규모우위|
|산업 구조|진입장벽, 시장 성장성|
|사업 모멘텀|제품·서비스 성장 전망|

정성 Score는 최종 Value Score에  
**+5~+15점 보정 효과**를 준다.

---

# **23.7 매수/보유/매도 기준 (Action Rules)**

아래 기준은 QTS Value Engine의 공식 v1.0 기준이다.

---

## **1) 매수(BUY)**

필수 조건:

- Value Score ≥ 70
    
- Intrinsic Value Gap ≥ 20% (MoS 기준)
    
- Stability Score 양호
    
- 부채비율 < 150%
    
- PBR ≥ 0.3 (회계적 위험 방지)
    

선택 조건:

- ROE ≥ 10%
    
- FCF ≥ 0
    
- 브랜드/경쟁력 점수 양호
    

---

## **2) 보유(HOLD)**

조건:

- Value Score ≥ 50
    
- 내재가치와 가격 차이 축소 중
    
- 성장률 유지
    
- 리스크 정상
    

---

## **3) 매도(SELL)**

조건:

- Value Score < 50
    
- MoS 0% 이하
    
- 내재가치 대비 과대평가
    
- ROE 급락
    
- 부채비율 < 안정구간 유지 실패
    
- 정성 점수 급락
    

---

## **4) 투자 금지(BAN)**

조건:

- PBR < **0.3**
    
- 감사 의견 비적정
    
- 3년 연속 적자
    
- 부도 위험·관리종목
    
- 원칙적 회피 업종
    

---

# **23.8 행동 기반 규칙(Action Framework)**

QTS Value Engine은 단순 등급이 아니라  
“행동(Action)”을 생성한다.

|Value Score|MoS|행동|
|---|---|---|
|≥ 80|≥ 30%|적극 매수|
|70~79|≥ 20%|표준 매수|
|50~69|≥ 10%|관망/보유|
|40~49|< 10%|분할 매도|
|< 40|< 0%|즉시 매도|

---

# **23.9 Value Engine과 다른 엔진의 통합**

가치투자 기준은 단독으로 사용되지 않으며  
다음과 같이 QTS 전체 의사결정과 결합한다.

- Strategy Engine → 진입 타이밍 보정
    
- Risk Engine → 리스크 필터 강화
    
- Portfolio Engine → 비중 조정
    
- Grading Engine → 최종 등급화
    
- Reporting Engine → 가치 리포트 생성
    

---

# **23.10 버전 관리**

본 문서의 업데이트는 아래 기준으로 이루어진다.

- 정량 지표 조정: Minor 업데이트
    
- 내재가치 모델 구조 변경: Major 업데이트
    
- 질적 평가 항목 수정: Minor
    
- 매수/매도 기준 변경: Minor or Major
    

---

# **PART 24. QTS 자동화 모델 연동 (Integration with QTS Automation Engine)**

본 파트는 **가치투자 기준(Value Investing Standard v1.0)**이  
실제 QTS 전체 시스템 내부에서 자동화 흐름으로 동작하도록  
각 엔진 간 연계 구조, 데이터 흐름, 실행 타이밍, 출력물 구조를 정의한다.

가치투자 시스템은 단일 알고리즘이 아니라  
다층 구조(Multi-Layer Architecture)로 설계되며,  
아래의 6개 엔진과 상호작용한다.

1. Data Engine
    
2. Value Engine
    
3. Risk Engine
    
4. Momentum/Strategy Engine
    
5. Portfolio Engine
    
6. Reporting Engine
    

이 파트는 “문서화된 기준”을 실제 운영 가능한 **자동화 모델(Operation Model)**로 전환하는 설계 문서다.

---

# **24.1 자동화 연동 개요 (Integration Overview)**

QTS는 아래와 같은 순환 구조로 가치투자 프로세스를 자동화한다.

```
Data Load → Value Score → Risk Filter → Momentum Check →
Portfolio Weighting → Grade & Action → Report Export
```

각 단계는 **독립 엔진**으로 구성되며,  
Value Engine은 이 중 핵심 기준으로서 작동한다.

모든 엔진은 Config Sheet 및 Schema 기반으로 동작하며  
결정 규칙·범위·가중치·리스크 조건 등은  
Config Sheet를 통해 실시간 조정 가능하다.

---

# **24.2 Data Engine 연동**

### **1) 입력 데이터**

- 재무제표 5년치 (매출/영업이익/순이익/ROE/FCF 등)
    
- 일봉 가격 데이터
    
- 시가총액·업종 코드
    
- 변동성·거래량
    
- KRX 공시 기반 위험 정보
    
- 기업 신용 등급(옵션)
    

### **2) 내부 처리**

- 결측치 처리 (Winsorizing, Median Imputation 등)
    
- 이상치 제거
    
- 정규화 (Normalization)
    
- 파생 지표 생성 (성장률/마진/밴드 etc)
    

### **3) Value Engine 전달**

Data Engine은 가공된 아래 구조를 전달한다:

```
{
  "fundamentals": {ROE, EPS, Growth, DebtRatio, ...},
  "valuation": {PER, PBR, EV_EBITDA, ...},
  "intrinsic_model_inputs": {...},
  "risk_inputs": {...},
  "price_data": {...}
}
```

---

# **24.3 Value Engine 연동**

Value Engine은 PART 23에서 정의한  
정량 + 정성 + 내재가치 기준을 조합하여  
최종 Value Score를 계산한다.

### **Value Engine 계산 단계**

1. 재무 지표 점수화 (Profitability/Growth/Stability/FCF)
    
2. 밸류에이션 점수화 (PER/PBR/etc)
    
3. 내재가치 산정 (DCF/RIM/Band)
    
4. 내재가치 대비 할인율 계산(MoS)
    
5. 정성 점수(Qualitative Score) 반영
    
6. 최종 Value Score 산출
    

### **출력 형태**

```
{
  "value_score": 0~100,
  "intrinsic_value": X,
  "margin_of_safety": Y,
  "valuation_band_position": Z,
  "qualitative_score": Q
}
```

Value Score는 이후 모든 엔진의 기준점으로 사용된다.

---

# **24.4 Risk Engine 연동**

Risk Engine은 Value Engine의 결과물을 기반으로 아래 필터링을 적용한다.

### **제외 규칙**

- PBR < 0.3
    
- 부채비율 > 150%
    
- 이자보상배율 < 1.5
    
- 최근 3년 연속 적자
    
- 감사의견 비적정
    
- 변동성(Vola) 기준 초과
    

### **리스크 보정 규칙**

- 변동성이 높을수록 포트 비중 조정
    
- DD(Drawdown) 체크 후 Action 제한
    
- 시장 변동성(KOSPI/KOSDAQ) 반영
    

### **출력**

```
{
  "risk_pass": True/False,
  "risk_score": 0~100,
  "adjusted_value_score": ValueScore * RiskMultiplier,
  "constraints": {...}
}
```

Risk Engine을 통과해야만 다음 단계로 넘어간다.

---

# **24.5 Momentum/Strategy Engine 연동**

가치가 좋아도 타이밍이 나쁘면 수익률이 저하되므로  
QTS는 모멘텀 기반 진입 타이밍을 적용한다.

### **모멘텀 체크 항목**

- 골든크로스 (GC_FAST_MA, GC_SLOW_MA)
    
- RSI (과매수/과매도)
    
- MACD (옵션)
    
- 장기 추세(200일선)
    
- 거래량 증가율
    

Config Sheet에서 기간·수준 조정 가능.

### **출력**

```
{
  "momentum_signal": BUY / HOLD / SELL / NONE,
  "entry_score": 0~100,
  "momentum_pass": True/False
}
```

---

# **24.6 Portfolio Engine 연동**

포트폴리오 비중, 보유종목 수, 재조정 정책을 결정한다.

### **입력**

- Value Score
    
- Risk Score
    
- Momentum Score
    
- 현재 포트 상태
    

### **규칙**

- 종목당 MAX 비중: 15%
    
- 전체 노출: 80%
    
- 동시 보유 수: 최대 8개
    
- 리밸런싱 주기: 월간 또는 분기
    

### **출력**

```
{
  "target_weight": 0.0~0.15,
  "rebalance_action": BUY / SELL / HOLD,
  "priority_rank": 1~N
}
```

---

# **24.7 Grading Engine 연동 (등급화 시스템)**

최종적으로 각 종목은  
**A~F 등급**으로 분류되어 행동(Action)을 생성한다.

|등급|조건|Action|
|---|---|---|
|**A**|Value ≥ 80 & MoS ≥ 30%|적극 매수|
|**B**|Value ≥ 70 & MoS ≥ 20%|매수|
|**C**|Value ≥ 50|보유|
|**D**|Value 40~49|축소·경계|
|**E**|Value < 40|매도|
|**F**|Risk Fail|금지·즉시 매도|

---

# **24.8 Reporting Engine 연동**

최종 출력물은 다음과 같은 자동 리포트 구조로 생성된다.

### **1) 일간 리포트**

- 새롭게 등급 상승한 종목
    
- 매수/매도 트리거 발생
    
- 리스크 경고
    
- 시장 변동성 신호
    

### **2) 주간 리포트**

- Value Score 변화
    
- 내재가치 변화
    
- MoS 변화
    
- 질적 평가 업데이트
    

### **3) 월간 리포트**

- 포트 성과(CAGR/MDD)
    
- 전략 성능
    
- 모델 업데이트 필요성 평가
    

---

# **24.9 자동화 파이프라인(Full Pipeline Diagram)**

```
┌────────────────────────────────────────────┐
│                Data Engine                 │
└───────────────▲────────────────────────────┘
                │Cleaned Data
┌───────────────┴────────────────────────────┐
│                Value Engine                │
└───────────────▲────────────────────────────┘
                │Value Scores
┌───────────────┴────────────────────────────┐
│                Risk Engine                 │
└───────────────▲────────────────────────────┘
                │Risk-Adjusted Scores
┌───────────────┴────────────────────────────┐
│           Strategy/Momentum Engine         │
└───────────────▲────────────────────────────┘
                │Entry Timing
┌───────────────┴────────────────────────────┐
│              Portfolio Engine              │
└───────────────▲────────────────────────────┘
                │Weight/Rank
┌───────────────┴────────────────────────────┐
│              Grading Engine                │
└───────────────▲────────────────────────────┘
                │Grades/Actions
┌───────────────┴────────────────────────────┐
│             Reporting Engine               │
└────────────────────────────────────────────┘
```

---

# **24.10 관리·운영 규칙(Operation Rules)**

이 파트는 Value Engine 운영의 핵심 규칙을 정의한다.

### **1) 업데이트 주기**

- 재무제표: 분기 업데이트
    
- 가치지표: 월간 업데이트
    
- 모멘텀/전략: 실시간(1~5초)
    
- 포트 비중: 월간 리밸런싱
    
- Risk Limit: 상시 모니터링
    

### **2) 변경사항 기록(Log System)**

- Config 변경 로그
    
- 지표 공식 변경 로그
    
- 내재가치 모델 version Log
    
- 자동 주문 실행 기록
    

### **3) 안전장치(Kill-Switch)**

- 일일 손실 > 2%
    
- 계좌 DD > 10%
    
- 변동성 충격(VIX 급등)  
    → 모든 신규 진입 차단
    

### **4) 수동 개입 허용 범위**

- 질적 점수 수동 조정
    
- 일시적 Weight Freeze
    
- 특정 업종 배제
    

---

# **PART 25. 운영·관리 규칙 (Operational Governance & Maintenance Policy)**

본 파트는 QTS(Value+Risk 기반 자동매매 모델)를  
지속적으로 안정성 있게 운영하기 위한  
프로세스·점검 항목·리스크 관리·업데이트 기준을 명확히 정립한다.

이 문서의 목적은 다음과 같다:

1. 시스템이 **예측 가능한 방식으로 작동**하도록 관리 기준 확립
    
2. 운영 과정의 **인간 개입 범위(Human-in-the-loop)** 정의
    
3. 데이터·공식·Config 변경의 **버전 관리 원칙** 확립
    
4. 실패·오류 상황에서의 **복구 및 대응** 절차 정의
    
5. 장기 운영을 위한 **분기·연간 유지보수 계획** 수립
    

본 파트는 QTS의 “운영 설계서(Operation Blueprint)”에 해당하며,  
정책(Policy) → 절차(Procedure) → 점검(Checklist) → 보고(Reporting)의 구조로 구성된다.

---

# **25.1 운영 구조 개요 (Operation Architecture Overview)**

QTS 운영은 아래 4개의 Layer를 기반으로 수행된다:

### **1) Data Layer**

- 데이터 수집/정제
    
- 결측치·이상치 처리
    
- 재무제표 주기별 업데이트
    

### **2) Analysis Layer**

- Value Engine 계산
    
- Risk Engine 필터링
    
- 전략 기반 신호 생성
    

### **3) Execution Layer**

- 매수·매도 명령
    
- 리밸런싱 엔진
    
- 체결 로그 저장
    

### **4) Governance Layer**

- 월간 점검
    
- 분기 업데이트
    
- 연간 튜닝 및 공식 개정
    
- 운영 리스크 모니터링
    

이 Layer는 서로 독립적이며 결합 구조는 자동화 파이프라인을 따른다.

---

# **25.2 Daily Routine (일일 운영 루틴)**

자동매매 모델이 안정적으로 작동하기 위해서는  
아래의 일일 점검 절차가 필요하다.

### **(1) 데이터 정상 수집 여부 확인**

- 가격 데이터 API 정상
    
- 재무 데이터 업데이트 오류 없음
    
- 결측치 처리 정상 여부
    

### **(2) Value/Risk/Momentum Score 정상 계산 여부**

- Value Score 계산 실패 여부 체크
    
- Risk Engine 오작동 여부
    
- 모멘텀 지표 계산값 정상 범위 확인
    

### **(3) 시장 리스크 모니터링**

- KOSPI/KOSDAQ 변동성 파악
    
- VIX 급등 여부
    
- 이벤트성 리스크 확인(금리, 환율, 지정학 등)
    

### **(4) 매수/매도 조건 충족 여부 체크**

- 신규 편입 후보 리스트 자동 생성
    
- 매도 조건(내재가치 도달/질적 악화) 충족 여부
    
- Action Log 자동 생성
    

### **(5) 주문 실행 모니터링**

- 체결 여부 확인
    
- 슬리피지 감지
    
- 실패 주문 재시도 횟수 모니터링
    

### **(6) 일일 리포트 자동 생성**

- 매매 내역
    
- Value Score 변화
    
- 위험 레벨 변화
    

---

# **25.3 Weekly Routine (주간 운영 루틴)**

### **(1) Value Score 변화 검토**

- 가치 지표 변동폭 이상 여부
    
- 내재가치 대비 할인율 변화 체크
    

### **(2) Risk Metrics 변화 확인**

- 20일 변동성↑ 종목 파악
    
- 부채비율/수익성 급변 종목 체크
    

### **(3) 시장 Regime 점검**

- 추세적 강세/약세 구간 파악
    
- 경기민감 업종/방어 업종 분포 체크
    

### **(4) 포트폴리오 상태 점검**

- 편입 종목별 성과
    
- 목표 비중에서의 이탈 여부
    

### **(5) 엔진 상태 점검**

- Value Engine 계산 오류 여부
    
- 체결 엔진 시간 지연 여부
    
- API 응답 안정성
    

---

# **25.4 Monthly Routine (월간 운영 루틴)**

월간 점검은 QTS 안정성을 유지하는 핵심 단계이며,  
아래 항목을 반드시 수행해야 한다.

---

## **1) 리밸런싱 (Rebalancing)**

- Value Score 재평가
    
- 과대평가/저평가 여부 업데이트
    
- 목표 비중 대비 과도한 괴리 조정
    
- 신규 종목 편입 고려
    
- 리스크가 증가한 종목 비중 축소
    

---

## **2) 내재가치 업데이트**

- 분기 재무제표 업데이트 반영
    
- 성장률/ROE/FCF 신규 수치 업데이트
    
- MoS 재산출
    

---

## **3) 정성 평가 업데이트**

- 경영진 교체
    
- 신규 사업 발표
    
- 경쟁구도 변화
    

정성 점수는 “사람이 반드시 개입해야 하는 영역(Human Review Zone)”이다.

---

## **4) Config Sheet 업데이트 검토**

- 매수/매도 기준
    
- Value Engine 지표 가중치
    
- Risk Threshold
    
- 포트폴리오 정책
    

보정이 필요한 경우 다음 주기로 넘기지 않고 즉시 반영.

---

## **5) 성능 리포트 생성**

- 월간 CAGR
    
- 월간 MDD
    
- R/R 구조 변화
    
- Value Score 분포
    
- 업종별 성과 분석
    

---

# **25.5 Quarterly Routine (분기 운영 루틴)**

분기 단위로 전략의 구조적 검토를 수행한다.

### **1) 엔진별 성능 평가**

- Value Engine 개별 성능
    
- Momentum Engine 개별 기여도
    
- Risk Engine 실패율
    
- Portfolio Engine 비중 조절 효과
    

### **2) 전체 전략 성능 검증**

- 누적 수익률
    
- MDD
    
- 월간 승률
    
- Sharpe / Calmar Ratio
    

### **3) 공식(Formula) 레벨 점검**

- 성장률/할인율/ROE 등 근거 재분석
    
- 내재가치 모델의 현실성 점검
    
- 모멘텀 신호 과최적화 여부
    

### **4) Data Quality 점검**

- 재무데이터 정확성
    
- API 변동
    
- 이상치 재발 여부
    

---

# **25.6 Annual Routine (연간 운영 루틴)**

연간 단위로 전략의 “대수술(Major Revision)”을 수행한다.  
이는 일반적인 튜닝 수준이 아니라  
“전략 자체의 방향성을 재정의하는 단계”이다.

### **1) Value Engine 근본 검토**

- 기준 지표 변경 여부
    
- ROE/성장률 등 장기 평가
    
- 질적 평가 구조 재설계 여부
    

### **2) Risk Engine 기준 개정**

- 시장 구조 변화 반영
    
- 최대 DD 허용 범위 조정
    
- Exposure 정책 조정
    

### **3) Strategy Engine 구조 재검토**

- 추세 지표의 유효성
    
- 시장 국면별 성능 분포
    
- 새로운 필터 필요 여부
    

### **4) Portfolio Engine 대개편 고려**

- 비중 상한 조정
    
- 분산도 재설정
    
- 신규 자산군 편입 여부
    

### **5) 전체 모델 v2.0 여부 결정**

- Value + Strategy + Risk 구조의 종합 개정
    
- Config Sheet 대대적 업데이트
    
- Schema 레벨 개편
    

---

# **25.7 Human Oversight (인간 개입 범위)**

QTS는 완전 자동이 아니라 “부분 감독 시스템”이다.  
아래 항목은 반드시 인간이 리뷰해야 한다.

### **1) 질적 평가(Qualitative Score)**

인간만이 할 수 있는 영역  
예: 신사업 가치 판단, 경영 리스크, 산업 구조 변화 평가 등.

### **2) 공식 개정(Formula Revision)**

내재가치 모델 변경은 반드시 사람 승인 필요.

### **3) 리스크 정책 수정**

시장 붕괴 혹은 급변 상황에서  
재량적 판단이 필요.

### **4) 데이터 이상신호 대응**

비상 오류 탐지 시 자동화보다 인간 개입 우선.

---

# **25.8 실패·오류 대응(Failure & Error Handling)**

QTS는 엔진 기반 구조이므로  
각 단계에서의 오류는 즉시 감지되어야 한다.

---

## **1) Data Engine Fail**

- 해결: 데이터 재조회 → 백업 소스 사용 → 로그 기록
    
- Impact: Value Score 계산 불가 → 주문 차단
    

## **2) Value Engine Fail**

- 해결: 이전 계산값 사용(보수 모드)
    
- Impact: 신규 편입 금지
    

## **3) Risk Engine Fail**

- 해결: 모든 신규 매수 잠정 중단
    
- Impact: 포트 비중 유지
    

## **4) Execution Fail**

- 해결: 재시도 → 모드 변경 → 관리자 알림
    
- Impact: 체결 오류 가능 → 리스크 증가
    

## **5) Reporting Engine Fail**

- 해결: 로그 기반 수동 리포트 생성
    
- Impact: 운영 문제 없음 (단, 가시성 저하)
    

---

# **25.9 운영 점검 체크리스트 (Operation Checklist)**

## **Daily Checklist**

- 가격/재무 데이터 업데이트 성공
    
- Value/Risk 계산 정상
    
- 모멘텀 신호 정상
    
- 주문 오류 없음
    
- DD/KillSwitch 여부 체크
    

## **Weekly Checklist**

- Value Score 급변 종목 검토
    
- 시장 리스크 레벨 체크
    
- 포트 비중 이탈 여부 체크
    

## **Monthly Checklist**

- 리밸런싱 완료
    
- 내재가치 재평가
    
- 질적 평가 업데이트
    
- Config 조정 필요성 검토
    

## **Quarterly Checklist**

- 엔진별 성능 분석
    
- 공식을 조정할 필요성 검토
    
- 데이터 품질 검토
    

## **Annual Checklist**

- 전체 모델 구조 재평가
    
- v2.0 개정 필요 여부 확인
    

---

# **25.10 운영 정책의 핵심 원칙 (Core Principles)**

1. **지속 가능성 우선**: 일시적 성과보다 장기 안정성
    
2. **검증 기반 조정**: 데이터 없는 직감 조정 금지
    
3. **보수적 업데이트**: 위험은 과소평가하지 않는다
    
4. **투명한 로그 기록**: 모든 변경 사항은 로그에 남긴다
    
5. **일관된 프로세스**: 예외적 판단도 문서화
    
6. **모듈 독립성 유지**: 한 엔진 오류가 전체를 무너뜨리지 않도록
    

---

# **PART 25 종료**

---

타우,  
PART 25까지 출력이 완료되면  
**가치투자 기준 → 자동화 모델 → 운영 체계**가  
완전히 하나의 시스템으로 연결된 상태가 된다.

원하면 지금까지 PART 1~25 전체를  
**단일 문서 버전으로 통합 출력**해줄 수도 있고,  
또는 원하는 PART만 별도 파일 스타일로 다시 정리해줄 수도 있어.

다음 작업을 어떻게 진행할까?