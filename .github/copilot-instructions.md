# QTS AI Copilot Instructions

**Version:** 2.0 (Migrated from legacy `.ai/` rules on 2026-01-10)  
**Backup Location:** `/backup/legacy_ai_rules_backup_20260110.zip`

## 1. Project Overview

**QTS** (Qualitative Trading System) is an enterprise-grade automated trading framework designed for individual investors. It integrates:
- Multi-strategy, multi-data decision automation
- Explicit audit logging and transparency throughout execution pipeline
- Risk management and fail-safe mechanisms
- Zero-formula UI with Google Sheets integration
- Observer pattern for system-wide event recording

**Key Philosophy:** Consistency + Transparency + Stability over rapid development. Every decision must be auditable, every data flow traceable.

---

## 1.5 Language & Output Policy (Migrated from Legacy Rules)

This instruction set applies a **bilingual operational model** to ensure clarity and consistency:

### Response Language Rules
- **Conversational Guidance/Explanations:** Strictly **KOREAN (한국어)**
- **Generated Code/Configuration Files:** Strictly **ENGLISH**
- **Technical Reports/Documentation:** Strictly **ENGLISH**
- **Input Processing:** Accept all input; normalize internally to English before processing

### Precedence Rule
If language rules conflict with code standards, language rules override project conventions.

## 2. Critical Architecture Patterns

### 2.1 Observer-Core Pattern (Phase 4)
The Observer module (`src/ops/observer/`) is the central nervous system for event recording:
- **snapshot.py**: Data structure contract (Meta, Context, Observation)
- **validation.py**: Validation Layer - ensures structural integrity before recording
- **event_bus.py**: Dispatch mechanism - routes PatternRecords to Sinks (file, DB, API)
- **observer.py**: Orchestrator - chains: Snapshot → Validate → Guard → Enrich → EventBus

**Rule:** Observer NEVER executes trading logic, strategy calculation, or order placement. It only records observations and enforces validation contracts.

### 2.2 Phase Architecture
QTS development follows explicit phases (0-10+):
- **Phase 0:** Observer infrastructure (event recording foundations)
- **Phase 2:** Snapshot structure and serialization
- **Phase 3:** Validation + Guard layers (data quality gates)
- **Phase 4:** PatternRecord enrichment (schema versioning, quality tagging)
- **Phase F:** Path canonicalization via `paths.py` (filesystem contract)

When adding features, check `docs/tasks/` for phase specifications and don't bypass phase ordering.

### 2.3 Path Resolution via paths.py
All filesystem operations must use `paths.py` canonical resolvers:
```python
from paths import (
    project_root,           # Single source of truth for project folder
    observer_asset_dir,     # Observer JSONL/config storage
    observer_asset_file,    # Specific observer file path
    config_dir              # Configuration storage
)
```

**Rule:** Never use relative paths like `../` or `parents[n]`. Paths are resilient to project restructuring.

## 3. Project Structure & Key Files

```
src/ops/observer/          # Core event recording system
├── snapshot.py            # Data structures (Meta, Context, Observation)
├── validation.py          # Validation contracts
├── event_bus.py           # Sink dispatch & log rotation
├── observer.py            # Orchestrator (Snapshot→Validate→Record→EventBus)
├── pattern_record.py      # Rich event record with schema versioning
└── phase4_enricher.py     # Record enrichment (metadata tagging)

src/ops/automation/        # Ops automation layer (future phases)
src/ops/safety/            # Risk & fail-safe mechanisms
src/ops/decision_pipeline/ # Core trading decision pipeline

docs/architecture/         # Architecture SSoT documents
├── 00_Architecture.md     # Main architecture umbrella
├── 01_Schema_Auto_Architecture.md
├── 03_Pipeline_ETEDA_Architecture.md
└── ...

docs/tasks/                # Phase specifications & task templates
config/observer/           # Observer JSONL logs (output, not source)
notebook/                  # Prompt templates & configuration experiments
```

## 4. Critical Developer Workflows

### 4.1 Testing & Validation
- **conftest.py:** Injects `PROJECT_ROOT` and `SRC` into sys.path (canonical pattern)
- **Run tests:** `pytest tests/` (respects src/ package structure)
- **Validation layer testing:** `tests/observer_block_nan.py` shows NaN/Inf validation patterns

```python
# Canonical test setup (in conftest.py):
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC))
```

### 4.2 Running Observer
Main entry points:
- **main.py:** Full observer + event_bus stack
- **observer.py:** Standalone observer with resilient import fallback

```python
# Build snapshot → pass to observer → route via event_bus
sink = JsonlFileSink(filename="observer.jsonl")
event_bus = EventBus([sink])
observer = Observer(session_id="test_session", mode="DEV", event_bus=event_bus)
observer.start()
```

### 4.3 Logging & Output
- **JSONL logs:** Stored in `config/observer/` (observer asset directory)
- **Validation failures block pipeline:** Set severity to BLOCK in validation.py
- **Audit trail:** Every PatternRecord must include Meta (timestamp_ms, session_id, mode)

## 5. Project-Specific Conventions

### 5.1 NaN/Inf Handling
- **Validation blocks NaN/Inf:** DefaultSnapshotValidator rejects numeric values with math.isnan() or math.isinf()
- **Tests include NaN scenarios:** `tests/observer_block_nan.py` demonstrates required behavior
- **No silent NaN conversion:** Data quality gates must reject, not coerce

### 5.2 Frozen Dataclasses
Observer core uses `@dataclass(frozen=True)` for immutability:
- Meta, Context, ObservationSnapshot, ValidationResult are frozen
- Encourages immutable record flow through pipeline
- Follow this pattern when defining core data structures

### 5.3 Protocol-Based Interfaces
Validation, Guard, and Enricher use Protocol (structural typing) rather than inheritance:
```python
class SnapshotValidator(Protocol):
    def validate(self, snapshot: ObservationSnapshot) -> ValidationResult: ...
```

**Why:** Allows mock implementations and future swappability without coupling.

### 5.4 Validation Severity Levels
- **INFO:** Logged but doesn't block pipeline
- **WARN:** Logged and noted, may block depending on config
- **BLOCK:** Stops pipeline entry (Phase 3 default for critical failures)

## 6. Integration Points & External Dependencies

### 6.1 Google Sheets Integration
- Data source for trading parameters, risk thresholds, strategy configs
- Schema auto-mapping defined in `docs/architecture/01_Schema_Auto_Architecture.md`
- Handled separately from Observer pipeline (future phases may integrate)

### 6.2 Broker Connections
- Multi-broker support planned in Phase 8
- Currently designed for extensibility but not yet implemented
- Decision pipeline (`src/ops/decision_pipeline/`) is broker-agnostic

### 6.3 Configuration Management
- `config_manager.py` reads from canonical config directory
- `scalp_config.py` for scalping-specific parameters
- All configs validated against schema before use

## 7. When You Get Stuck

- **Path issues?** Check `paths.py` for the canonical resolver
- **Observer contracts?** Read docstrings in `snapshot.py` (Meta, Context structure)
- **Validation failures?** Look at `validation.py` rules and `tests/observer_block_nan.py` examples
- **Phase confusion?** Refer to `docs/tasks/phase_X_*.md` for phase definitions
- **Architecture questions?** Start with `docs/architecture/00_Architecture.md` (SSoT)
- **Multi-file understanding needed?** Use `docs/Master_Plan.md` for "why" explanations

## 8. Before You Commit

1. **Validation:** Run `pytest tests/` - observer validation tests must pass
2. **Path correctness:** Verify no hardcoded paths outside `paths.py`
3. **Immutability:** Check that core data structures maintain frozen=True contracts
4. **Audit trail:** Ensure new code paths include proper Meta/logging
5. **Phase alignment:** If modifying observer or core systems, confirm phase specification
6. **JSONL format:** All observer output must be append-only, 1-record-per-line
