"""
Mock Snapshot Source for local-only mode.

실제 Observer나 Market Data Provider 없이
테스트용 가격 데이터를 생성합니다.
--local-only 모드에서 파이프라인 전체 흐름을 테스트할 수 있습니다.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Dict, List, Optional


class MockSnapshotSource:
    """
    Mock Snapshot Source

    테스트용 스냅샷 데이터를 생성합니다.
    실제 시장 데이터 없이 ETEDA 파이프라인을 테스트할 수 있습니다.
    """

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        base_prices: Optional[Dict[str, float]] = None,
        volatility: float = 0.001,
        max_iterations: int = 10,
    ):
        """
        MockSnapshotSource 초기화

        Args:
            symbols: 테스트할 종목 코드 리스트 (기본: ["005930"])
            base_prices: 종목별 기준 가격 (기본: 삼성전자 70000원)
            volatility: 가격 변동성 (기본: 0.1%)
            max_iterations: 최대 반복 횟수 (0이면 무제한)
        """
        self._symbols = symbols or ["005930"]  # 삼성전자
        self._base_prices = base_prices or {"005930": 70000.0}
        self._volatility = volatility
        self._max_iterations = max_iterations
        self._current_iteration = 0
        self._current_symbol_idx = 0

        # 현재 가격 상태 (시뮬레이션용)
        self._current_prices: Dict[str, float] = {
            sym: self._base_prices.get(sym, 50000.0) for sym in self._symbols
        }

        self._logger = logging.getLogger(__name__)
        self._logger.info(
            f"MockSnapshotSource initialized (symbols={self._symbols}, "
            f"max_iterations={max_iterations})"
        )

    def __call__(self) -> Dict[str, Any]:
        """
        다음 스냅샷 데이터 생성.

        Returns:
            Dict[str, Any]: ETEDA 파이프라인이 기대하는 스냅샷 구조
        """
        self._current_iteration += 1

        # 현재 종목 선택 (라운드 로빈)
        symbol = self._symbols[self._current_symbol_idx]
        self._current_symbol_idx = (self._current_symbol_idx + 1) % len(self._symbols)

        # 가격 변동 시뮬레이션
        old_price = self._current_prices[symbol]
        change = old_price * random.uniform(-self._volatility, self._volatility)
        new_price = max(100.0, old_price + change)  # 최소 100원
        self._current_prices[symbol] = new_price

        # 볼륨 시뮬레이션
        base_volume = random.randint(10000, 100000)

        timestamp_ms = int(time.time() * 1000)

        snapshot = {
            "trigger": "mock",
            "meta": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_ms": timestamp_ms,
                "iteration": self._current_iteration,
                "source": "MockSnapshotSource",
            },
            "context": {
                "symbol": symbol,
                "market": "KOSPI",
            },
            "observation": {
                "inputs": {
                    "price": {
                        "open": old_price,
                        "high": max(old_price, new_price) * 1.001,
                        "low": min(old_price, new_price) * 0.999,
                        "close": new_price,
                        "prev_close": old_price,
                    },
                    "volume": base_volume,
                },
            },
        }

        self._logger.debug(
            f"[MockSnapshot] iteration={self._current_iteration}, "
            f"symbol={symbol}, price={new_price:.2f}"
        )

        return snapshot

    def is_exhausted(self) -> bool:
        """최대 반복 횟수 도달 여부"""
        if self._max_iterations <= 0:
            return False
        return self._current_iteration >= self._max_iterations

    def reset(self) -> None:
        """상태 초기화"""
        self._current_iteration = 0
        self._current_symbol_idx = 0
        self._current_prices = {
            sym: self._base_prices.get(sym, 50000.0) for sym in self._symbols
        }
        self._logger.debug("[MockSnapshotSource] Reset")

    @property
    def iteration_count(self) -> int:
        """현재 반복 횟수"""
        return self._current_iteration


def create_mock_should_stop(
    snapshot_source: MockSnapshotSource,
    max_iterations: int = 10,
) -> callable:
    """
    MockSnapshotSource와 연동되는 should_stop 함수 생성.

    Args:
        snapshot_source: MockSnapshotSource 인스턴스
        max_iterations: 최대 반복 횟수

    Returns:
        should_stop 콜백 함수
    """
    def should_stop() -> bool:
        return snapshot_source.iteration_count >= max_iterations

    return should_stop
