"""
자본 배분기.

근거: docs/arch/sub/14_Capital_Flow_Architecture.md §3
- OperatingState 기반 목표 배분 비율 계산
- Config_Local 오버라이드 지원 (ALLOCATION_OVERRIDE_ENABLED)
- 제약 조건 (min_pct, max_pct, min_amount) 적용
- 합계 100% 정규화
"""
from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal

from src.capital.contracts import (
    POOL_CONSTRAINTS,
    PoolId,
)
from src.state.contracts import STATE_PROPERTIES, OperatingState

_LOG = logging.getLogger(__name__)

_STATE_PREFIX_MAP = {
    OperatingState.AGGRESSIVE: "AGGRESSIVE",
    OperatingState.BALANCED: "BALANCED",
    OperatingState.DEFENSIVE: "DEFENSIVE",
}


def _mid(range_: tuple[float, float]) -> Decimal:
    """범위의 중간값."""
    return Decimal(str((range_[0] + range_[1]) / 2))


def _get_config_allocation(
    operating_state: OperatingState,
    config_overrides: dict[str, str],
) -> dict[PoolId, Decimal] | None:
    """Config_Local에서 OperatingState별 배분 비율 추출.

    3개 키 모두 있어야 유효, 부분 설정이면 None 반환 (fallback).
    """
    prefix = _STATE_PREFIX_MAP[operating_state]
    keys = {
        PoolId.SCALP: f"{prefix}_SCALP_PCT",
        PoolId.SWING: f"{prefix}_SWING_PCT",
        PoolId.PORTFOLIO: f"{prefix}_PORTFOLIO_PCT",
    }
    result: dict[PoolId, Decimal] = {}
    for pool_id, key in keys.items():
        value = config_overrides.get(key)
        if value is not None:
            try:
                result[pool_id] = Decimal(value)
            except Exception:
                return None
    if len(result) == 3:
        return result
    return None


def calculate_target_allocation(
    operating_state: OperatingState,
    total_equity: Decimal,
    config_overrides: dict[str, str] | None = None,
) -> dict[PoolId, Decimal]:
    """
    OperatingState 기반 목표 배분 비율 계산.

    config_overrides에 ALLOCATION_OVERRIDE_ENABLED=="1"이면
    Config_Local의 상태별 비율을 우선 사용하고, 실패 시 STATE_PROPERTIES
    중간값으로 fallback한다. 합계가 1.0이 되도록 정규화한다.
    """
    props = STATE_PROPERTIES[operating_state]

    # Config_Local 오버라이드 시도
    if (
        config_overrides
        and config_overrides.get("ALLOCATION_OVERRIDE_ENABLED") == "1"
    ):
        override_raw = _get_config_allocation(operating_state, config_overrides)
        if override_raw is not None:
            raw = override_raw
        else:
            _LOG.warning(
                "Config_Local 배분 비율 조회 실패, STATE_PROPERTIES fallback 사용: %s",
                operating_state.value,
            )
            raw = {
                PoolId.SCALP: _mid(props.scalp_allocation_range),
                PoolId.SWING: _mid(props.swing_allocation_range),
                PoolId.PORTFOLIO: _mid(props.portfolio_allocation_range),
            }
    else:
        raw = {
            PoolId.SCALP: _mid(props.scalp_allocation_range),
            PoolId.SWING: _mid(props.swing_allocation_range),
            PoolId.PORTFOLIO: _mid(props.portfolio_allocation_range),
        }

    # 제약 조건 적용
    for pool_id, constraints in POOL_CONSTRAINTS.items():
        pct = raw[pool_id]
        pct = max(pct, constraints.min_pct)
        pct = min(pct, constraints.max_pct)
        raw[pool_id] = pct

    # 합계 경고: 정규화 전 0.9~1.1 범위 밖이면 WARNING
    raw_total = sum(raw.values())
    if raw_total < Decimal("0.9") or raw_total > Decimal("1.1"):
        _LOG.warning(
            "배분 비율 합계가 정상 범위(0.9~1.1) 밖: %s (state=%s)",
            raw_total,
            operating_state.value,
        )

    # 정규화 (합계 = 1.0)
    total = sum(raw.values())
    if total == 0:
        equal = Decimal("1") / Decimal("3")
        return {pid: equal for pid in PoolId}

    result: dict[PoolId, Decimal] = {}
    for pool_id in PoolId:
        normalized = (raw[pool_id] / total).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        result[pool_id] = normalized

    # 반올림 오차 보정: SCALP에 나머지 할당
    diff = Decimal("1.0000") - sum(result.values())
    result[PoolId.SCALP] += diff

    return result


def calculate_target_amounts(
    allocation: dict[PoolId, Decimal],
    total_equity: Decimal,
) -> dict[PoolId, Decimal]:
    """배분 비율 → 금액 변환."""
    amounts: dict[PoolId, Decimal] = {}
    for pool_id, pct in allocation.items():
        amount = (total_equity * pct).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        amounts[pool_id] = amount
    return amounts


def check_drift(
    current_pcts: dict[PoolId, Decimal],
    target_pcts: dict[PoolId, Decimal],
    threshold: Decimal = Decimal("0.10"),
) -> dict[PoolId, Decimal]:
    """
    드리프트 계산. 임계값 초과 풀 반환.

    Returns: {PoolId: drift_amount} (threshold 초과분만)
    """
    drifts: dict[PoolId, Decimal] = {}
    for pool_id in PoolId:
        current = current_pcts.get(pool_id, Decimal("0"))
        target = target_pcts.get(pool_id, Decimal("0"))
        drift = abs(current - target)
        if drift > threshold:
            drifts[pool_id] = drift
    return drifts
