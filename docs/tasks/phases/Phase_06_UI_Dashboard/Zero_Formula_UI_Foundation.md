# Zero-Formula UI Foundation

**관련:** task_04_zero_formula_ui_foundation.md, docs/arch/06_UI_Architecture.md §4, UI_Contract_Schema.md

---

## 1. UI Layer 기본 구조

### 1.1 위치

- **UI Layer 경로:** `src/runtime/ui/` (단일 UI 레이어 진입점)
- `src/ui/` 는 사용하지 않으며, 런타임 UI는 모두 `src/runtime/ui/` 에 둔다.

### 1.2 폴더 구조

```
src/runtime/ui/
├── __init__.py           # UIContractBuilder, R_DashWriter, BlockRenderer 노출
├── contract_schema.py    # UI Contract 버전·TypedDict
├── contract_builder.py   # UIContractBuilder (단일 빌더)
├── r_dash_writer.py     # R_Dash 시트 갱신 Writer
├── zero_formula_base.py  # BlockRenderer Protocol (Zero-Formula 계약)
├── r_dash/               # R_Dash 컴포넌트 네임스페이스
│   └── __init__.py       # Writer + Renderers re-export
└── renderers/            # 블록별 렌더러 (Contract → 행 데이터)
    ├── account_summary.py
    ├── symbol_detail.py
    ├── risk_monitor.py
    ├── performance.py
    ├── pipeline_status.py
    ├── meta_block.py
    └── _display.py        # None/NaN → "-"/"ERR"
```

### 1.3 Zero-Formula 기본 클래스

- **`BlockRenderer`** (Protocol, `zero_formula_base.py`):
  - 입력: UI Contract 블록(dict)만 사용. Raw/Calc 직접 접근 금지.
  - 출력: `List[List[Any]]` — 셀에 쓸 **값만**. 수식/참조 없음.
- 모든 `render_*` 함수는 이 프로토콜을 만족한다.

---

## 2. R_Dash 컴포넌트 기반

### 2.1 모듈 구조

- **`src/runtime/ui/r_dash/`**: R_Dash 전용 진입점
  - `R_DashWriter`, `R_DASH_*` 범위 상수, `render_*` 함수 re-export
  - 사용 예: `from src.runtime.ui.r_dash import R_DashWriter, render_account_summary`

### 2.2 Data Contract 기반 시각화 인터페이스

- **입력:** UI Contract (docs/arch/UI_Contract_Schema.md)
- **출력:** R_Dash 셀 영역별 행 데이터 (값만)
- **갱신:** `R_DashWriter.write(contract)` 또는 `schedule_write(contract)` (비동기 격리)

---

## 3. Dashboard Block Architecture

| 블록 | 06 §3 | 렌더러 | R_Dash 영역 |
|------|-------|--------|-------------|
| Account Summary | §3.1 | `render_account_summary` | A1:E10 |
| Symbol Detail | §3.2 | `render_symbol_detail` | A12:H40 |
| Risk Monitor | §3.4 | `render_risk_monitor` | F1:I20 |
| Performance | §3.3 | `render_performance` | J1:N20 |
| Pipeline Status | §3.5 | `render_pipeline_status` | F25:I33 |
| Meta | §3.6 | `render_meta_block` | J25:N33 |

### 3.1 실시간 데이터 업데이트 채널

- **트리거:** ETEDA 사이클 종료 시 (R_Dash_Update_Policy.md)
- **흐름:** UI Contract 생성(UIContractBuilder) → R_DashWriter.write(contract) 또는 schedule_write(contract)
- **격리:** UI 갱신은 비동기로 실행하여 ETEDA를 블록하지 않음

---

## 4. UI Contract 정의

- **Engine → UI 데이터 전송 Contract:** docs/arch/UI_Contract_Schema.md
- **생성:** UIContractBuilder.build(...) 단일 진입점
- **소비:** R_DashWriter + Renderers만 사용

---

## 5. Zero-Formula 원칙 준수 확인

- [x] UI는 Raw/Calc를 직접 읽지 않고 **UI Contract만** 사용한다.
- [x] 시트에 **수식을 넣지 않는다** — Renderer 출력은 값만(List[List[Any]])이다.
- [x] Contract 생성은 **UIContractBuilder** 한 곳에서만 수행한다.
- [x] R_Dash 갱신은 **R_DashWriter** 한 경로로만 수행한다.
- [x] None/NaN 표시는 **"-"/"ERR"** 로 고정(renderers/_display.py).
