"""
운영 상태 관리 시스템.

근거: docs/arch/sub/18_System_State_Promotion_Architecture.md
- AGGRESSIVE / BALANCED / DEFENSIVE 3가지 운영 상태
- Safety State(NORMAL/WARNING/FAIL/LOCKDOWN)와 직교적 관계
- 상태별 자본 배분, 리스크 허용치, 엔진 활성화 제어
- 상태 영속성: JSON 파일 저장/복구, JSONL 전환 이력
- 포트폴리오 리밸런싱 엔진
"""

from src.state.contracts import (
    ManualOverride,
    OperatingState,
    OperatingStateSnapshot,
    StateProperties,
    STATE_PROPERTIES,
    TransitionMetrics,
)
from src.state.config import StateConfig
from src.state.operating_state import OperatingStateManager, TransitionResult
from src.state.rebalancing import (
    RebalancingConfig,
    RebalancingEngine,
    RebalancingOrder,
)
from src.state.transition import (
    TransitionRule,
    find_applicable_rule,
)

__all__ = [
    # contracts
    "ManualOverride",
    "OperatingState",
    "OperatingStateSnapshot",
    "StateProperties",
    "STATE_PROPERTIES",
    "TransitionMetrics",
    # config
    "StateConfig",
    # operating_state
    "OperatingStateManager",
    "TransitionResult",
    # rebalancing
    "RebalancingConfig",
    "RebalancingEngine",
    "RebalancingOrder",
    # transition
    "TransitionRule",
    "find_applicable_rule",
]
