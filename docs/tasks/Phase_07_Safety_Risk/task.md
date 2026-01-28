# Phase 7: Safety & Risk Core

- [ ] **Risk Policy Implementation**
    - [ ] Implement `KillSwitch` logic (Global & Strategy-level)
    - [ ] Implement `ExposureLimit` checks
    - [ ] Implement `LossLimit` checks (Daily Max Loss)

- [ ] **Guard System**
    - [ ] Integrate Risk Gates into `ETEDARunner` (Decide Phase)
    - [ ] Implement `ObserverGuard` for real-time market anomaly detection (e.g., Flash Crash)

- [ ] **Recovery & Fail-safe**
    - [ ] Implement "Lockdown Mode" (Cease all trading)
    - [ ] Implement "Liquidate All" emergency procedure
    - [ ] Implement auto-recovery from API failures
