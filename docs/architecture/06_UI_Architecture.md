아래는 **6번 문서: QTS_UI_Architecture.md**  
**완성본(v1.0.0)** 이다.

QTS UI는 단순한 대시보드가 아니라  
**ETEDA Pipeline·Engine Layer·Performance Layer의 상태를 실시간 반영하는 운영 핵심 시스템**이므로  
설계 원칙, 렌더링 규칙, 안정성 원칙을 모두 포함한 “정식 아키텍처 문서” 형태로 완성했다.

---

# ============================================================

# QTS UI Architecture

# ============================================================

Version: v1.0.0  
Status: Architecture Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
QTS 시스템의 UI Layer 전체 구조를 정의한다.  
UI Layer는 운영자에게 계좌 상태·리스크·신호·성과를 직관적으로 제공하며,  
ETEDA Pipeline과 Engine 동작의 상태를 정확히 투명하게 보여주는 역할을 수행한다.

본 문서는 **Zero-Formula UI**, **Contract-Driven Rendering**,  
**안전성 중심 UI**라는 세 가지 원칙을 기반으로 작성되었다.

---

# **1. Overview**

## **1.1 목적**

UI Architecture의 목적은 다음과 같다.

1. 실시간 자동매매 시스템에서 필수적인 운영 지표를 시각적으로 제공
    
2. ETEDA Pipeline의 상태와 오류를 실시간 전달
    
3. Zero-Formula 구조로 시트 오류 가능성을 제거
    
4. UI Contract 기반으로 렌더링 구조를 고정
    
5. 운영자 실수를 원천 차단하는 안전 구조 제공
    

---

## **1.2 범위**

포함 범위:

- QTS UI Layer 아키텍처
    
- Zero Formula UI 구조
    
- UI Contract 구조 및 렌더링
    
- Dashboard Block Architecture
    
- Google Sheets 기반 UI 설계
    
- UI 상태/오류 처리 규칙
    

제외:

- UX 세부 디자인
    
- 상세 색상/폰트 스타일 가이드
    

---

## **1.3 UI Layer의 역할**

UI는 다음 기능을 수행한다.

- 계좌 현황 즉시 파악
    
- 신호/매매 결과 실시간 확인
    
- 리스크 상태 및 Fail-Safe 감지
    
- Performance 결과 시각화
    
- ETEDA 사이클 모니터링
    
- ETEDA 실패 시 즉각적인 피드백 제공
    

---

## **1.4 ETEDA·Engine Layer와의 관계**

ETEDA Pipeline의 각 단계는 UI Contract를 갱신한다.

```
Transform  → 계좌/종목 계산값 업데이트  
Evaluate   → 엔진 신호/승인 상태 UI 반영  
Decide     → 최종 매매 여부 표시  
Act        → ExecutionResult 및 T_Ledger UI 반영  
Performance→ PnL/MDD/CAGR 등 UI 반영
```

UI는 **결과만 표시**하며,  
ETEDA/Engine 내부 로직을 직접 참조하지 않는다.

---

## **1.5 Zero Formula UI 원칙 개요**

Zero Formula UI란:

- Google Sheets 내 수식을 완전히 제거
    
- 모든 값은 UI Contract가 직접 전달
    
- 시트는 단순 표시(Rendering) 기능만 수행
    

이를 통해:

- 시트 오류 제거
    
- 유지보수 비용 절감
    
- 자동매매 안정성 극대화
    

---

# **2. QTS UI Layer 구조**

UI Layer는 3가지 구성요소로 나뉜다.

## **2.1 UI Contract 기반 렌더링**

UI는 ETEDA Pipeline 종료 시 생성되는  
**UI Contract**만을 기반으로 업데이트된다.

Contract → Render  
이 흐름이 UI의 절대 원칙이다.

---

## **2.2 Raw/Calc 데이터를 UI에 직접 연결하지 않는 이유**

직접 연결하면:

- 시트 구조 변화 시 오류 발생
    
- ETEDA와 UI의 동기화 깨짐
    
- 안정성 저하 위험 증가
    

UI는 반드시 Contract 데이터를 통해서만 표시한다.

---

## **2.3 UI Rendering Flow**

```
UI Contract 생성
    ↓
Render Engine(UI Update Function)
    ↓
Sheets의 R_Dash 업데이트
```

ETEDA 사이클 종료마다 자동 실행된다.

---

## **2.4 Rendering Unit 설계**

각 UI 영역은 독립적인 Rendering Unit으로 구성된다.

예:

- account_summary_renderer()
    
- risk_monitor_renderer()
    
- performance_renderer()
    
- pipeline_status_renderer()
    

---

## **2.5 UI Layer와 Data Layer 분리 규칙**

- UI는 절대 RawData/CalcData를 직접 읽지 않는다.
    
- Contract만을 사용하여 화면을 갱신한다.
    
- Contract 변경 = UI 변경 신호
    

---

# **3. Core UI Blocks (Dashboard Architecture)**

UI는 6개의 Core Block으로 설계된다.

---

## **3.1 Account Summary Block**

포함 정보:

- Total Equity
    
- Daily PnL
    
- Exposure Summary
    
- Unrealized / Realized PnL
    
- Cash Flow Summary
    

계좌 상태를 한눈에 파악하는 핵심 영역이다.

---

## **3.2 Symbol Detail Block**

각 종목의 상세 정보 제공:

- 현재가
    
- 보유 수량
    
- 평가손익
    
- 노출 비중
    
- 전략 신호 및 confidence
    
- 허용 수량 (Risk Engine 출력)
    

---

## **3.3 Risk Monitor Block**

리스크 관련 실시간 데이터 표시:

- 현재 Exposure vs Limit
    
- Daily Loss Limit
    
- Rejected Signals
    
- Risk Warnings
    

리스크 초과 시 시각적 경고 강조.

---

## **3.4 Performance Block**

성과 지표 표시:

- Daily PnL Curve
    
- MDD
    
- CAGR
    
- 전략별 성과 비교
    
- 누적 수익률 곡선
    

Performance Engine의 출력을 기반으로 업데이트된다.

---

## **3.5 Pipeline Status Block**

ETEDA 상태 표시:

- IDLE / RUNNING / SAFE / FAIL / LOCKDOWN
    
- Last Cycle Time
    
- Cycle Duration
    
- Recent Error Codes
    

이 영역은 운영 안정성에 가장 중요하다.

---

## **3.6 Meta Block**

시스템 메타데이터:

- QTS Version
    
- Schema Version
    
- Contract Version
    
- Broker 연결 상태
    
- Server Clock / Pipeline Clock
    

---

# **4. Zero Formula UI Architecture**

## **4.1 개념 정의**

Zero Formula = 시트 내 모든 계산식 제거  
Sheet는 단순히 Render된 값을 보여주는 UI View 역할만 담당한다.

---

## **4.2 Zero Formula의 필요성**

자동매매 시스템에서 시트 오류는 다음 문제를 일으킨다.

- ETEDA 파이프라인 중단
    
- 잘못된 신호 표시
    
- 운영자 오판 가능성
    
- 시트 가독성 파괴
    

Zero Formula는 이러한 위험을 원천적으로 제거한다.

---

## **4.3 ETEDA 종료 시점 업데이트 방식**

ETEDA 한 사이클 종료 후:

1. CalcDataContract, PerformanceOutput 등 집계
    
2. UI Contract 생성
    
3. UI Rendering Function 실행
    
4. R_Dash 시트 갱신
    

---

## **4.4 UI Contract 필드 구성 원칙**

- UI에 필요한 정보만 최소한으로 포함
    
- Raw/Calc 정보 중 UI가 직접 사용하지 않는 필드 제외
    
- 상태/경고/에러 코드는 명확하게 분리
    
- 필드명은 항상 snake_case
    

---

## **4.5 Sheet 오류를 원천 차단하는 구조**

- 수식 제거
    
- 병합 셀 최소화
    
- 숨김/필터/정렬 동작 제거
    
- 모든 데이터는 Python에서 덮어쓰기 방식으로 관리
    

---

## **4.6 UI 업데이트 트리거**

- ETEDA 종료
    
- 안전모드(SAFE) 변경
    
- Fail-Safe 발생
    
- 사용자 요청
    

---

# **5. UI Contract Specification**

UI Contract의 전체 구조는 QTS_Data_Contract_Spec에 정의되어 있다.  
여기서는 UI 측면에서 중요한 구조만 요약한다.

---

## **5.1 Account-Level Fields**

|필드|설명|
|---|---|
|total_equity|계좌 평가금|
|daily_pnl|일 손익|
|realized_pnl|실현 손익|
|unrealized_pnl|미실현 손익|
|exposure_pct|전체 노출 비율|

---

## **5.2 Symbol-Level Fields**

- symbol
    
- price
    
- qty
    
- exposure_value
    
- unrealized_pnl
    
- strategy_signal
    
- risk_approved
    
- final_qty
    

---

## **5.3 Performance Fields**

- daily_pnl_curve
    
- mdd
    
- cagr
    
- win_rate
    
- strategy_performance_table
    

---

## **5.4 Risk Fields**

- exposure_limit_pct
    
- current_exposure_pct
    
- risk_warnings
    
- rejected_signals
    

---

## **5.5 Pipeline Status Fields**

- pipeline_state (RUNNING / FAIL / LOCKDOWN 등)
    
- last_cycle_duration
    
- last_error_code
    
- cycle_timestamp
    

---

## **5.6 Meta Fields**

- qts_version
    
- schema_version
    
- contract_version
    
- broker_connected
    
- timestamp
    

---

# **6. ETEDA Pipeline과 UI의 통합 구조**

## **6.1 ETEDA 종료 시 마다 UI Contract 갱신**

ETEDA 실행 흐름:

```
Transform → CalcData
Evaluate → Engine Output
Decide → OrderDecision
Act → ExecutionResult
Performance → 계좌/성과 갱신
UI Update → UI Contract 생성 후 R_Dash 렌더링
```

---

## **6.2 Evaluate/Decide 데이터 UI 반영 규칙**

- signal, approved, final_qty 등 표시
    
- 전략 충돌 또는 리스크 거부는 강조 표시
    

---

## **6.3 Transform 단계 값의 UI 표시**

- total_equity
    
- exposure_pct
    
- price, qty, exposure_value
    

---

## **6.4 Performance Engine 출력값 렌더링**

- PnL 그래프(시트 기반 선형 저장)
    
- 누적 수익률
    
- 전략 성과 테이블 업데이트
    

---

## **6.5 Pipeline 오류 상태 표시 규칙**

- FAIL: 빨간색 강조
    
- SAFE: 노란색 강조
    
- LOCKDOWN: 전체 UI Freeze
    
- Warning: 오렌지 강조
    

---

# **7. UI Rendering Rules**

## **7.1 렌더링 주기**

- 기본: ETEDA Pipeline 실행 시마다
    
- 옵션: 운영자 수동 Refresh
    

---

## **7.2 Null/Error 표시 규칙**

- None → "-"
    
- NaN → "ERR"
    
- 오류 발생 시 로그와 UI에 경고 표시
    

---

## **7.3 색상 규칙**

- PnL +값: 파란색
    
- PnL -값: 빨간색
    
- 승인/성공: 녹색
    
- 거부/실패: 붉은색
    
- Warning: 주황색
    

---

## **7.4 Warning/Fail 표시 규칙**

- Warning: 조용하지만 눈에 띄는 색
    
- Fail-Safe: UI 전체 강한 강조
    
- Lockdown: 주요 버튼/셀 비활성화
    

---

## **7.5 Display Freeze 조건**

다음 조건에서는 UI 데이터 업데이트 금지:

- Pipeline FAIL
    
- Lockdown 상태
    
- UI Contract Validation 실패
    

---

# **8. Google Sheets 기반 UI**

## **8.1 R_Dash 구조**

주요 영역:

- 계좌 요약 (A1:D10)
    
- 주요 종목 상세 (A12:D40)
    
- 리스크 모니터 (F1:H20)
    
- Performance 요약 (J1:M20)
    
- Pipeline Status (F25:H33)
    
- Meta Block (J25:M33)
    

정확한 셀 좌표는 별도 시트 스펙에서 정의한다.

---

## **8.2 Position Summary UI**

Rendering Unit:

- symbol
    
- qty
    
- exposure
    
- pnl
    

정렬/필터 금지.

---

## **8.3 Symbol Detail UI**

- 종목별 상세 노출
    
- 전략 신호 강조
    
- 리스크 거부 표시
    

---

## **8.4 Risk Monitor UI**

- Exposure Limit 대비 현황
    
- Risk 경고 테이블
    
- Rejected Signals 표시 영역
    

---

## **8.5 Engine Result UI**

- 전략 신호 / 리스크 승인 / 포트폴리오 수량
    
- 최근 매매 상태
    

---

## **8.6 Performance UI**

- 일별 손익
    
- 누적 손익
    
- 지표(MDD, CAGR 등)
    

---

## **8.7 Pipeline Status UI**

- RUNNING/SAFE/FAIL 여부
    
- Error Code
    
- Cycle Time
    

---

## **8.8 Color/Conditional Formatting 규칙**

- Conditional Formatting은 최소화
    
- UI Contract 값 기반으로 색상 지정
    
- 시트 내부 계산식 사용 금지
    

---

## **8.9 숨김 처리 규칙**

- Danger Tag 기반 숨김 행/열
    
- Contract에 hidden=True인 경우 해당 행/열 자동 숨김
    

---

# **9. 향후 확장 가능한 UI Architecture**

## **9.1 웹 UI 확장(React 기반)**

- WebSocket 기반 실시간 스트리밍
    
- 모바일 및 대형 대시보드 확장 가능
    

---

## **9.2 모바일 UI**

- 간소화된 성과·리스크 표시
    
- 매매 신호 요약
    

---

## **9.3 멀티 계좌 UI**

- 계좌별 Performance 병렬 표시
    
- Exposure/Summary 통합
    

---

## **9.4 브로커 실시간 데이터 UI**

- 실시간 체결 정보
    
- 잔고 변동 추적
    

---

## **9.5 스트리밍 기반 UI**

- 초당 데이터 업데이트
    
- 고성능 렌더링 엔진 필요
    

---

# **10. 오류 처리 & 안전 장치**

## **10.1 UI Contract Validation**

다음 필드가 누락되면 UI 업데이트 중단:

- total_equity
    
- pipeline_state
    
- symbol 목록
    

---

## **10.2 잘못된 값 표시 방지**

- 음수 Equity → Error
    
- NaN PnL → Error
    
- exposure_pct > 1 → Warning
    

---

## **10.3 Pipeline Fail 표시**

- 전체 UI 붉은색 경고 표시
    
- Lockdown 상태에서 모든 렌더링 비활성화
    

---

## **10.4 UI Freeze 조건**

다음 중 하나 발생 시:

- Fail-Safe
    
- Lockdown
    
- Contract Version mismatch
    

---

## **10.5 UI 업데이트 오류 발생 시 대응**

- 오류 로그 기록
    
- UI 상태 유지
    
- 운영자에게 경고 송출
    

---

# **11. 테스트 전략**

## **11.1 UI Contract 단위 테스트**

- 필수 필드 유효성 테스트
    
- 잘못된 값 검출
    

---

## **11.2 UI 렌더링 테스트**

- 정상 렌더링
    
- 오류 상태 렌더링
    
- Safe Mode 렌더링
    

---

## **11.3 Pipeline 상태 변화 테스트**

각 상태의 UI 표현이 정확한지 검증.

---

## **11.4 Performance 데이터 렌더링 회귀 테스트**

PnL/MDD/CAGR 그래프의 일관성 확인.

---

## **11.5 Mock UI Contract 기반 테스트**

테스트 환경에서도 UI 동작 재현 가능.

---

# **12. Appendix**

## **12.1 UI Contract → R_Dash 매핑 표**

UI Contract의 각 필드가  
R_Dash 어떤 셀에 매핑되는지 정리.

---

## **12.2 UI 와이어프레임 예시**

개념적 레이아웃 설명.

---

## **12.3 Condition Formatting 규칙**

색상 규칙 테이블.

---

## **12.4 향후 확장 UI 다이어그램**

웹/모바일 확장 구조 제시.

---

**QTS UI Architecture v1.0.0 — 완료됨**

---

다음 문서로 넘어갈까?

### 7번 문서 스켈레톤 생성:

**QTS_FailSafe_Architecture.md**  
(또는 Safety Layer Architecture)

진행할까?