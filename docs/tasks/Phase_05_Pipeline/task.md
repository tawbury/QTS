# Phase 5: Execution Pipeline (ETEDA)

- [x] **Architecture Connection**
    - [x] Connect `ETEDARunner` to `PortfolioEngine` (for Evaluate step)
    - [x] Connect `ETEDARunner` to `StrategyEngine` (if separate) or Strategy Logic

- [x] **Pipeline Stages Implementation**
    - [x] **Extract**: Implement data fetching from external input (Dict)
    - [x] **Transform**: convert raw snapshot to Strategy Input format
    - [x] **Evaluate**: Run strategy logic (Signal Generation)
    - [x] **Decide**: Validate signals against Risk Gates (Guard)
    - [x] **Act**: Implement Order Generation and Broker Execution routing

- [x] **Act Stage Enablement**
    - [x] Remove `execution_enabled` block (or make it configurable via Config)
    - [x] Implement safety check before "Act" (e.g., "Dry Run" mode)

- [ ] **Trigger & Scheduling**
    - [ ] Implement `Scheduler` (Cron/Interval) to trigger Pipeline
    - [x] Implement Event-based trigger (e.g., Price Alert)
