# Phase 3: Config Architecture (Local)

- [x] **Implementation Preparation**
    - [x] Choose file format for Local Config (JSON vs YAML vs Excel)
    - [x] Define file structure for `config_local`

- [x] **Core Implementation**
    - [x] Implement `LocalConfigLoader` in `src/runtime/config/`
    - [x] Implement loading logic for Secrets/Env variables
    - [x] Implement logic to merge Local Config with Default Config
    - [x] Implement "Override" logic (Sheet Config vs Local Config priority)

- [x] **Validation & Safety**
    - [x] Add validation schema for Local Config keys
    - [x] Implement parsing for "Recommended Defaults" defined in Design Phase
    - [x] Add unit tests for invalid config files

- [x] **Integration**
    - [x] Integrate `LocalConfigLoader` into `UnifiedConfig` initialization
    - [x] Verify that `UnifiedConfig` correctly reflects Local settings
