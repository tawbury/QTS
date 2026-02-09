# app/strategy/engines — Engine Layer

생성자 시그니처·ETEDA 연동·execute I/O 계약 정리.  
**근거**: [02_Engine_Core_Architecture.md](../../../../docs/arch/02_Engine_Core_Architecture.md), [04_Data_Contract_Spec.md](../../../../docs/arch/04_Data_Contract_Spec.md)

---

## 1. 생성자/진입점

| 엔진 | 생성자 | 비고 |
|------|--------|------|
| **BaseEngine** | `(config: UnifiedConfig)` | 공통: state, metrics, initialize/start/stop/execute |
| **PortfolioEngine** | `(config, position_repo, portfolio_repo, t_ledger_repo)` | ETEDARunner에서 리포지토리 주입 |
| **PerformanceEngine** | `(config, history_repo, performance_repo)` | ETEDARunner에서 리포지토리 주입 |
| **StrategyEngine** | `(config: UnifiedConfig)` | config만 주입 |
| **TradingEngine** | `(config, broker)` | BrokerEngine 주입. Act 단계에서 submit_intent |

---

## 2. ETEDA 연동

- **ETEDARunner** (`app/pipeline/eteda_runner.py`):  
  `__init__`에서 PortfolioEngine, PerformanceEngine, StrategyEngine 생성 후 Evaluate/Decide 단계에서 `execute` 호출.
- **Evaluate**: portfolio/performance/strategy `execute(operation=...)` 호출.
- **Decide**: 의사결정 입력 조합.
- **Act**: TradingEngine(브로커 주입 시) `submit_intent` → ExecutionResponse Contract.

---

## 3. Engine I/O Contract (execute)

- **입력**: `data: Dict[str, Any]` — `operation` 필드 필수. operation별 추가 필드(예: `market_data`, `position_data`, `intent`).
- **출력**: `{ "success": bool, "data"?: ..., "error"?: str, "execution_time": float }` — ETEDA Evaluate/Decide와 정합.
- **StrategyEngine**: `operation == "calculate_signal"` → `data`: market_data, position_data → `{ success, data, execution_time }`.
- **PortfolioEngine**: `get_portfolio_summary`, `get_positions`, `calculate_exposure` 등.
- **PerformanceEngine**: `calculate_performance_metrics`, `get_daily_performance`, `get_monthly_performance` 등.

---

## 4. 테스트 경로

- `tests/engines/` — BaseEngine, PortfolioEngine, PerformanceEngine, TradingEngine (Mock/NoopBroker).
- `tests/runtime/strategy/` — SimpleStrategy, StrategyMultiplexer, StrategyRegistry.
- `tests/runtime/risk/` — SimpleRiskCalculator, CalculatedRiskGate, StagedRiskGate.

기본 실행: `pytest tests/engines/ tests/runtime/strategy/ tests/runtime/risk/ -v -m "not live_sheets and not real_broker"`

---

**경로**: `app/strategy/engines/` (앱형 리팩토링 2026-02-01)
