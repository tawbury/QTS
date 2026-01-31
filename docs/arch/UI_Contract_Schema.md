# UI Contract Schema (Pipeline 종료 시 생성)

**Version:** 1.0.0  
**Status:** 고정 스키마 (SSoT)  
**관련:** [04_Data_Contract_Spec.md](./04_Data_Contract_Spec.md) §7, [06_UI_Architecture.md](./06_UI_Architecture.md), [11_Architecture_Change_Management.md](./11_Architecture_Change_Management.md) §4.6

## 목적

- Pipeline(ETEDA) **종료 시 한 번만** 생성되는 UI용 계약 구조를 고정한다.
- UI는 Raw/Calc를 직접 읽지 않고 **이 Contract만**으로 R_Dash를 렌더링한다(Zero-Formula 원칙).
- Contract 생성은 **단일 빌더/팩토리**에서만 수행하며, 산발적 생성/변경을 금지한다.

---

## 1. 버전 정책

| 변경 유형 | 버전 bump | 비고 |
|-----------|-----------|------|
| 필드 삭제 / 의미 변경 | **Major** | 호환 깨짐 |
| 필드 추가 / 선택 필드 변경 | **Minor** | 11_Architecture_Change_Management §4.6 |
| 오타·문구·주석 | **Patch** | 04_Data_Contract_Spec §8.2 |

- Contract 버전은 `meta.contract_version`에 `"MAJOR.MINOR.PATCH"` 문자열로 기록한다.
- 렌더링 측에서 기대 버전과 불일치 시 **UI 업데이트 중단** (06_UI_Architecture §10.1, §10.4).

---

## 2. 스키마 개요

UI Contract는 **한 개의 루트 객체**이며, 다음 블록으로 구성된다.

| 블록 | 필수 여부 | 설명 |
|------|-----------|------|
| `account` | 필수 | 계좌 요약 |
| `symbols` | 필수 | 종목별 상세 (배열) |
| `performance` | 선택 | 성과 지표 |
| `risk` | 선택 | 리스크 현황 |
| `pipeline_status` | 필수 | ETEDA 상태 |
| `meta` | 필수 | 버전·타임스탬프 |

---

## 3. 필드 정의

### 3.1 `account` (Account-Level)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `total_equity` | number | ✓ | 계좌 평가금 |
| `daily_pnl` | number | ✓ | 일 손익 |
| `realized_pnl` | number | ○ | 실현 손익 |
| `unrealized_pnl` | number | ○ | 미실현 손익 |
| `exposure_pct` | number (0~1) | ○ | 전체 노출 비율 |

**Validation:** `total_equity` ≤ 0 → 경고; `daily_pnl` NaN → 오류.

### 3.2 `symbols` (Symbol-Level, 배열)

각 요소:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `symbol` | string | ✓ | 종목 코드 |
| `price` | number | ○ | 현재가 |
| `qty` | number | ○ | 보유 수량 |
| `exposure_value` | number | ○ | 노출 금액 |
| `unrealized_pnl` | number | ○ | 미실현 손익 |
| `strategy_signal` | string | ○ | 전략 신호 |
| `risk_approved` | bool | ○ | 리스크 승인 여부 |
| `final_qty` | number | ○ | 최종 수량 |

**Validation:** `symbol` 목록이 비어 있으면 빈 배열 `[]`로 두며, 필수 블록 자체는 존재해야 함.

### 3.3 `performance`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `daily_pnl_curve` | array of number | ○ | 일별 PnL 곡선 |
| `mdd` | number | ○ | MDD |
| `cagr` | number | ○ | CAGR |
| `win_rate` | number | ○ | 승률 |
| `strategy_performance_table` | array / object | ○ | 전략별 성과 |

### 3.4 `risk`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `exposure_limit_pct` | number | ○ | 노출 한도 비율 |
| `current_exposure_pct` | number | ○ | 현재 노출 비율 |
| `risk_warnings` | array of string | ○ | 리스크 경고 목록 |
| `rejected_signals` | array | ○ | 거부된 신호 목록 |

### 3.5 `pipeline_status`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `pipeline_state` | string | ✓ | IDLE / RUNNING / SAFE / FAIL / LOCKDOWN |
| `last_cycle_duration` | number (sec) | ○ | 마지막 사이클 소요 시간 |
| `last_error_code` | string | ○ | 마지막 오류 코드 |
| `cycle_timestamp` | string (ISO8601) | ○ | 마지막 사이클 시각 |

**Validation:** `pipeline_state` None/누락 → 오류(UI 업데이트 중단).

### 3.6 `meta`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `contract_version` | string | ✓ | "MAJOR.MINOR.PATCH" (예: "1.0.0") |
| `schema_version` | string | ○ | 데이터 스키마 버전 |
| `qts_version` | string | ○ | QTS 애플리케이션 버전 |
| `broker_connected` | bool | ○ | 브로커 연결 여부 |
| `timestamp` | string (ISO8601) | ✓ | Contract 생성 시각 |

---

## 4. 생성 시점과 단일 빌더

- **생성 시점:** ETEDA 한 사이클 종료 후, **한 번만** 생성한다.
- **생성 주체:** `UIContractBuilder`(또는 동일 규약의 단일 팩토리). 다른 모듈에서 UI Contract 구조를 직접 만들거나 수정하지 않는다.
- **소비:** Render Engine(UI Update Function)이 이 Contract만 사용해 R_Dash를 갱신한다.

---

## 5. 변경 이력

| 버전 | 변경 내용 |
|------|-----------|
| 1.0.0 | 최초 고정: 필드/버전 정책 정의, 단일 빌더 원칙 명시 |
