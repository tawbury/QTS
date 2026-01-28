# Phase 4: Engine Layer Implementation

- [ ] **Portfolio Engine**
    - [ ] **Remove Mocks**: Replace `mock_positions` and `mock_summary` with real data calls
    - [ ] **Integration**: Connect `PortfolioEngine` to `PositionRepository` and `T_LedgerRepository` (via `EnhancedPortfolioRepository`?)
    - [ ] **Calculation Logic**: Implement `calculate_exposure()` using real asset values
    - [ ] **Allocation Logic**: Implement `get_sector_allocation()` and `get_strategy_allocation()` dynamically
    - [ ] **KPI Updates**: Implement `update_portfolio_kpi()` to persist calculated metrics

- [ ] **Performance Engine**
    - [ ] **Remove Mocks**: Replace mock performance data
    - [ ] **PnL Calculation**: Implement Realized vs Unrealized PnL logic based on `History` and `Position` sheets
    - [ ] **Metrics**: Implement MDD (Max Drawdown), CAGR, Win Rate calculations
    - [ ] **Reporting**: Implement methods to generate daily/weekly performance reports

- [ ] **Testing**
    - [ ] Create integration tests with real (or seeded) Sheet data
    - [ ] Verify Engine outputs against known calculation models (Excel/Manual)
