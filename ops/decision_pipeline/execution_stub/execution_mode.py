"""
Act stage execution mode (VIRTUAL / SIM / REAL).

DEPRECATED: 이 파일은 호환성을 위해 유지됩니다.
실제 구현은 runtime.config.execution_mode.PipelineMode로 이동했습니다.

Migration:
    # Before
    from ops.decision_pipeline.execution_stub.execution_mode import ExecutionMode

    # After
    from runtime.config.execution_mode import PipelineMode
    # 또는
    from runtime.config.execution_mode import ExecutionMode  # alias (= TradingMode)

정책: docs/tasks/phases/Phase_05_ETEDA_Pipeline/act_stage_policy.md
- VIRTUAL: 검증만, 부작용 없음.
- SIM: 시뮬/페이퍼 실행 (런타임 PAPER 대응).
- REAL: 실거래 (런타임 LIVE 대응).
"""
from __future__ import annotations

# Re-export from canonical location
from runtime.config.execution_mode import (
    PipelineMode,
    pipeline_to_trading_mode,
)

# Backward compatibility: ExecutionMode = PipelineMode for ops
ExecutionMode = PipelineMode

__all__ = ["ExecutionMode", "PipelineMode", "pipeline_to_trading_mode"]
