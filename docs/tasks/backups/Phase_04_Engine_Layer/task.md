# Phase 4: Engine Layer Implementation

- [x] **Portfolio Engine**
    - [x] **Remove Mocks**: Replace `mock_positions` and `mock_summary` with real data calls
    - [x] **Integration**: Connect `PortfolioEngine` to `PositionRepository` and `T_LedgerRepository` (via `EnhancedPortfolioRepository`)
    - [x] **Calculation Logic**: Implement `calculate_exposure()` using real asset values
    - [x] **Allocation Logic**: Implement `get_sector_allocation()` and `get_strategy_allocation()` dynamically
    - [x] **KPI Updates**: Implement `update_portfolio_kpi()` to persist calculated metrics

- [x] **Performance Engine**
    - [x] **Remove Mocks**: Replace mock performance data
    - [x] **PnL Calculation**: Implement Realized vs Unrealized PnL logic based on `History` and `Position` sheets
    - [x] **Metrics**: Implement MDD (Max Drawdown), Sharpe, Win Rate calculations
    - [x] **Reporting**: Implement methods to generate daily/weekly performance reports

- [ ] **Testing**
    - [ ] Create integration tests with real (or seeded) Sheet data
    - [ ] Verify Engine outputs against known calculation models (Excel/Manual)
