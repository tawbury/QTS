
---

# QTS Config Sub-Architecture Spec (Draft)

문서명: `QTS_Config_Sub_Architecture.md`  
상태: Draft (Anchor 후보)  
목적: Config 분리 및 전략별(Swing / Scalp) 운영을 위한 **Sub-Architecture 기준** 확정

상위 문서 : [[00QTS_Architecture]]
하위 문서 : [[G_S_Portfolio]], [[G_S_Perfomance]], [[G_S_R_Dash]], [[G_S_Dividend]], [[G_S_T_Ledger]], [[G_S_History]], [[G_S_Strategy]], [[G_S_Position]], [[Config_분리·운영_Spec_Doc]], [[Local_Bootstrap_Config]]


---

## 0. 문서 성격 및 적용 범위

### 0.1 문서 목적

본 문서는 QTS에서 Config를 **전략 운영(Swing/Scalp) 및 리스크 안전성** 관점으로 분리·적용하기 위한 서브 아키텍처 기준을 정의한다.

### 0.2 적용 범위

- Config 저장소(구글 시트) 분리 구조 정의
    
- Unified Config 해석/우선순위/충돌 규칙 정의
    
- 전략별 Engine 분리(ScalpEngine / SwingEngine) 반영
    
- 전략 Sheet의 “필수 KEY **목록**”이 아니라 “필수 KEY **범위**(최소 논리 구성)” 정의
    

### 0.3 명시적 제외

- 개별 KEY의 값 튜닝/최적화
    
- 전략 성과 개선 논의
    
- 메인 아키텍처 변경
    
- 실제 코드 구현/리팩토링
    
- 개별 KEY 이름을 확정하는 작업(Phase 확장 또는 구현 단계에서 수행)
    

---

## 1. 핵심 원칙 (Anchor)

1. **Sheet가 곧 스코프다.**  
    전략 스코프는 KEY 네임스페이스가 아니라 **Google Sheet 단위로 물리 분리**한다.
    
2. **엔진은 Config 소스를 알 필요가 없다.**  
    엔진은 “Local/Scalp/Swing이 어디에 저장되어 있는지”가 아니라 **Unified Config**를 입력으로 받는다.
    
3. **Local은 보호 영역이다.**  
    `Config_Local`은 전략에 의해 override 되지 않는다.  
    (전략별 시트가 Local을 덮어쓰는 것을 금지)
    
    - 운영 원칙: **운영 책임자만 수정 가능**
    - 제한 사항: **전략 튜닝 세션에서는 수정 금지**
    
4. **공용 KEY는 공유가 아니라 복제다.**  
    “Swing/Scalp 공용”은 단일 저장이 아니라 **각 전략 시트에 동일 KEY를 각각 보유(복제)**하는 것을 의미한다.
    
5. **리스크는 구조로 예방한다.**  
    로그/이력보다 “실수 자체가 일어나기 어렵게” 설계한다.
    

---

## 2. Config 저장 구조 (Google Sheet 3분리)

### 2.1 최종 구성 (확정)

|Sheet|역할|스코프|변경 성격|
|---|---|---|---|
|`Config_Local`|System / Global|전략 불변(전역)|낮음(거의 고정)|
|`Config_Scalp`|Strategy Tunable|Scalp 전용|높음(튜닝)|
|`Config_Swing`|Strategy Tunable|Swing 전용|높음(튜닝)|

> 기존 단일 `Config` 시트 운영은 종료한다.

### 2.2 컬럼 구조

- CATEGORY / SUB_CATEGORY는 **사람(운영자) 관리 목적**으로 유지한다.
    
- 프로그램은 **KEY**를 유일 식별자로 사용한다.
    
- TAG(DANGER/STABLE/TUNABLE)는 리스크 인지 및 운영 가이드 목적으로 사용한다.  
    (집행/강제 여부는 구현 단계에서 별도 결정)
    

권장 컬럼(현행 호환):

- `CATEGORY | SUB_CATEGORY | KEY | VALUE | DESCRIPTION | TAG`
    

---

## 3. Unified Config Resolution Flow

### 3.1 정의

전략 실행 시, Unified Config는 아래 순서로 구성된다.

```
Unified_Config(strategy) =
    Load(Config_Local)
  + Load(Config_{Strategy})   # Config_Scalp or Config_Swing
  + Load(Secrets)             # .env / env var
```

### 3.2 우선순위 규칙

1. `Secrets` 최우선
    
2. `Config_Local`은 보호 영역이며, 전략 시트가 이를 override 하지 못한다.
    
3. 전략 시트는 전략 내부에서만 유효하다. (Scalp ↔ Swing 교차 영향 없음)
    

### 3.3 충돌 규칙 (핵심)

- 동일 KEY가 `Config_Local`과 `Config_{Strategy}`에 동시에 존재할 경우:
    
    - **Config_Local 승**
        
    - 전략 시트 값은 무시된다.
        
- 동일 KEY가 `Config_Scalp`와 `Config_Swing`에 모두 존재할 수 있다:
    
    - 이는 정상이며 “공용(복제)” 정책의 결과다.
        
    - 두 값이 달라도 무방하며, 엔진은 자신의 전략 시트 값만 사용한다.
        

### 3.4 누락 규칙

- 전략 실행 시 필요한 KEY가 전략 시트에 없더라도:
    
    - Local에 존재하면 Local 값을 사용 가능(단, Local 보호 정책과 충돌하지 않는 범위에서)
        
    - Local에도 없으면 Validation 실패 대상
        

---

## 4. 전략 Sheet 필수 KEY 범위 (최소 논리 구성)

> 본 섹션은 KEY “목록”이 아니라, 각 전략 시트가 전략 엔진을 구동하기 위해 충족해야 하는 **최소 논리 범위**를 정의한다.

### 4.1 공통 필수 범위

전략 시트에는 아래 범주 중 **최소 2개 이상**이 존재해야 한다.

- Entry Rule (진입 조건 파라미터)
    
- Exit Rule (청산 조건 파라미터)
    
- Risk Control (전략 레벨 리스크 제어)
    
- Position / Allocation (포지션 수·비중·랭킹/선별)
    

> 최소 범위를 만족하지 못하면 “불완전 전략 Config”로 간주한다.

### 4.2 `Config_Scalp` 필수 범위

`Config_Scalp`는 단기·고회전 실행을 전제로 한다.

필수 포함:

- Entry/Signal 계열(기술적 지표/신호)
    
- Exit Rule 계열(손절/익절/시간 기반 중 1개 이상)
    
- Risk Control(전략 레벨: 단건 손실 제한 또는 변동성 제한 중 1개 이상)
    
- Position 제약(최대 포지션 수 또는 단건 비중 제한)
    

### 4.3 `Config_Swing` 필수 범위

`Config_Swing`는 중장기·저회전 실행을 전제로 한다.

필수 포함:

- Screening / Market Filter (시장·섹터·종목 필터)
    
- Valuation / Fundamental / Quality 중 **최소 1개 이상**
    
- Risk Monitoring(DD/변동성 경계 등) 또는 Portfolio Rule(편입 수/비중/랭킹) 중 **최소 1개 이상**
    

---

## 5. Engine Layer 보완 (전략별 2엔진)

### 5.1 기존 대비 변경점(상태 선언)

- 기존 구조: 단일 Trading Engine에서 전략이 Config로만 분기되는 형태였을 가능성이 높음.
    
- 현재 구조(본 문서 기준): **전략별 엔진 2개로 분리**한다.
    
    - `ScalpEngine`
        
    - `SwingEngine`
        

### 5.2 엔진-시트 1:1 대응

- ScalpEngine은 `Config_Local + Config_Scalp (+ Secrets)`를 입력으로 받는다.
    
- SwingEngine은 `Config_Local + Config_Swing (+ Secrets)`를 입력으로 받는다.
    

개념 구조:

```
Trading Layer
├─ ScalpEngine  <- Unified_Config(Scalp)
└─ SwingEngine  <- Unified_Config(Swing)
```

### 5.3 책임 경계

- 전략 판단/주문 실행: 각 전략 엔진
    
- Hard Risk / Kill Switch / Fail-safe 정책: Local(System) 영역에서 정의(전략 override 불가)
    
- Validation: 엔진 시작 시 수행(정책/강제 수준은 구현 단계에서 확정)
    

### 5.4 동시 실행 전제(명시)

- 본 아키텍처는 “단일 전략 실행 컨텍스트”를 기준으로 정의한다.
    
- 동시 실행(Scalp+Swing)은 **멀티 프로세스/인스턴스**로 처리하는 것을 전제로 하며, 본 문서 범위에서는 동시성 운영 정책을 정의하지 않는다.
    

---

## 6. 운영 규칙 요약

### 6.1 운영자 워크플로우

- 전역/안전 정책 조정: `Config_Local`만 수정
    
- Scalp 튜닝: `Config_Scalp`만 수정
    
- Swing 튜닝: `Config_Swing`만 수정
    
- 비밀정보: `.env / 환경변수`만 수정(시트/깃에 저장 금지)
    

### 6.2 “공용(복제)” 운영 가이드

- 공용으로 보이는 KEY는 두 시트에 동일 KEY로 존재 가능
    
- 초기에는 값을 동일하게 맞춰도 되나, 운영 중 독립 튜닝을 허용한다.
    
- 공용 KEY를 단일 시트로 합치는 시도는 스코프 혼선 리스크가 있으므로 본 아키텍처에서 채택하지 않는다.
    

---

## 7. Validation & Fail-safe (정책 수준 선언)

- Validation 실패 시:
    
    - 신규 주문 차단 또는 엔진 중단/안전 모드 진입을 기본으로 한다.
        
- 강제 청산 등 고위험 액션은:
    
    - 별도 Phase/정책 문서에서 다룬다(본 문서 범위 외).
        

---

## 8. 보류 항목 (의도적으로 지금 확정하지 않는 것)

- 전략 시트의 개별 KEY “필수 목록” 확정
    
- KEY 간 의존성(예: A가 있으면 B 필수)
    
- 타입/범위 스키마 강제 수준
    
- Config versioning/승인 워크플로우 상세
    

> 위 항목은 구현 단계 또는 Phase 확장에서 확정한다.

---

## 9. 구현 세션 진입 체크리스트 (요약)

-  `Config_Local / Config_Scalp / Config_Swing` 시트가 존재한다.
    
-  Local 보호(전략 override 금지) 규칙이 코드/검증 로직에 반영될 수 있다.
    
-  공용 KEY는 공유가 아니라 복제라는 원칙을 팀/문서가 동일하게 이해한다.
    
-  전략별 엔진(ScalpEngine/SwingEngine)이 Unified Config 입력을 기준으로 동작하도록 설계된다.
    
-  Validation 실패 시 기본 동작(주문 차단/중단)이 합의되어 있다.
    

---

## Appendix A. 용어

- **Local**: 전략과 무관한 전역(System) Config
    
- **Strategy Sheet**: 전략 전용 튜닝 Config(`Config_Scalp`, `Config_Swing`)
    
- **공용(복제)**: 동일 KEY가 각 전략 시트에 각각 존재(공유 저장 아님)
    
- **Unified Config**: 로딩/머지 결과로서 엔진이 소비하는 단일 Config 객체
    

---

첨부 문서 : [[QTS_Config_Architecture_Delta_Memo]]