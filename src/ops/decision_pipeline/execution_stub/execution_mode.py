"""
Act stage execution mode (VIRTUAL / SIM / REAL).

정책: docs/tasks/phases/Phase_05_ETEDA_Pipeline/act_stage_policy.md
- VIRTUAL: 검증만, 부작용 없음.
- SIM: 시뮬/페이퍼 실행 (런타임 PAPER 대응).
- REAL: 실거래 (런타임 LIVE 대응).
"""

from __future__ import annotations

from enum import Enum


class ExecutionMode(str, Enum):
    """Virtual → SIM → REAL 단계 확장용 모드. 전환은 Config + Guard 통과 시에만."""

    VIRTUAL = "VIRTUAL"
    SIM = "SIM"
    REAL = "REAL"
